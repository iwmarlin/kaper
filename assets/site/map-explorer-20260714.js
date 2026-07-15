import {
  debounce,
  escapeHtml,
  humanize,
  loadTables,
  mountSiteChrome,
  normalizeSearch,
  recordUrl,
  renderError,
} from "./core.js?v=20260715-6";

mountSiteChrome("map");

const listTarget = document.querySelector("#place-list");
const countTarget = document.querySelector("#place-count");
const totalTarget = document.querySelector("#map-total");
const search = document.querySelector("#place-search");
const period = document.querySelector("#place-period");
const selectionKicker = document.querySelector("#place-selection-kicker");
const selectionTitle = document.querySelector("#place-selection-title");
const selectionMeta = document.querySelector("#place-selection-meta");
const selectionLink = document.querySelector("#place-selection-link");

const periodOrder = ["warsaw", "european", "transnational", "hollywood"];
let map;
let markerLayer;
let selectedId = null;
const markerById = new Map();

function normalizedPeriod(place) {
  return String(place.period || place.periodKey || "")
    .toLowerCase()
    .replaceAll(" ", "_");
}

function eventCount(place) {
  return (place.timelineEventIds || []).length;
}

function markerIcon(place, selected = false) {
  const periodKey = normalizedPeriod(place);
  const size = Math.min(24, 14 + Math.sqrt(Math.max(eventCount(place), 1)) * 2.2);
  return window.L.divIcon({
    className: "map-place-icon-shell",
    html: `<span class="map-place-marker map-place-marker--${escapeHtml(periodKey)}${selected ? " is-selected" : ""}" style="--marker-size:${size}px" aria-hidden="true"></span>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
  });
}

function resetSelection() {
  if (selectedId) {
    const previous = markerById.get(selectedId);
    const previousPlace = previous?.options?.placeRecord;
    if (previous && previousPlace) {
      previous.setIcon(markerIcon(previousPlace));
      previous.setZIndexOffset(0);
    }
  }
  selectedId = null;
  selectionKicker.textContent = "Explore the map";
  selectionTitle.textContent = "Select a place";
  selectionMeta.textContent = "Choose a marker or a place from the list to see its role in the archive.";
  selectionLink.hidden = true;
}

function selectPlace(place, { moveMap = true } = {}) {
  if (selectedId && selectedId !== place.id) {
    const previous = markerById.get(selectedId);
    const previousPlace = previous?.options?.placeRecord;
    if (previous && previousPlace) {
      previous.setIcon(markerIcon(previousPlace));
      previous.setZIndexOffset(0);
    }
  }

  selectedId = place.id;
  document.querySelectorAll("#place-list button").forEach((button) => {
    button.setAttribute("aria-current", String(button.dataset.id === place.id));
  });

  selectionKicker.textContent = humanize(place.placeType || "Documented place");
  selectionTitle.textContent = place.displayName;
  const location = [place.city, place.country].filter(Boolean).join(", ");
  const linkedEvents = eventCount(place);
  selectionMeta.textContent = `${location}${location ? " · " : ""}${linkedEvents} linked ${linkedEvents === 1 ? "event" : "events"}.`;
  selectionLink.href = recordUrl("place", place.id);
  selectionLink.hidden = false;

  const marker = markerById.get(place.id);
  if (marker) {
    marker.setIcon(markerIcon(place, true));
    marker.setZIndexOffset(1000);
    if (map && moveMap) {
      if (markerLayer?.zoomToShowLayer) {
        markerLayer.zoomToShowLayer(marker, () => {
          marker.setIcon(markerIcon(place, true));
          marker.setZIndexOffset(1000);
          marker.openTooltip();
        });
      } else {
        const zoom = place.placeType === "city" ? 8 : place.placeType === "district" ? 11 : 13;
        map.flyTo([place.latitude, place.longitude], Math.max(map.getZoom(), zoom), { duration: 0.65 });
        marker.openTooltip();
      }
    }
  }
}

try {
  const { places } = await loadTables(["places"]);
  const publicPlaces = places;
  totalTarget.textContent = String(publicPlaces.length);

  const periods = [...new Set(publicPlaces.map(normalizedPeriod).filter(Boolean))]
    .sort((a, b) => periodOrder.indexOf(a) - periodOrder.indexOf(b));
  for (const value of periods) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = humanize(value);
    period.append(option);
  }

  if (window.L) {
    map = window.L.map("research-map", {
      scrollWheelZoom: false,
      zoomControl: true,
      preferCanvas: true,
    });
    window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    markerLayer = window.L.markerClusterGroup
      ? window.L.markerClusterGroup({
          showCoverageOnHover: false,
          maxClusterRadius: 48,
          spiderfyOnMaxZoom: true,
          iconCreateFunction(cluster) {
            const count = cluster.getChildCount();
            return window.L.divIcon({
              className: "map-cluster-shell",
              html: `<span class="map-cluster" aria-label="${count} nearby places">${count}</span>`,
              iconSize: [44, 44],
              iconAnchor: [22, 22],
            });
          },
        }).addTo(map)
      : window.L.layerGroup().addTo(map);
  } else {
    document.querySelector("#research-map").innerHTML = `<div class="map-fallback"><div><h2>Interactive map unavailable</h2><p>Use the complete searchable place list alongside the map.</p></div></div>`;
  }

  function render() {
    const query = normalizeSearch(search.value.trim());
    const filtered = publicPlaces
      .filter((place) => (
        (!period.value || normalizedPeriod(place) === period.value)
        && (!query || normalizeSearch([
          place.displayName,
          place.city,
          place.region,
          place.country,
          place.placeType,
        ].filter(Boolean).join(" ")).includes(query))
      ))
      .sort((a, b) => (
        eventCount(b) - eventCount(a)
        || periodOrder.indexOf(normalizedPeriod(a)) - periodOrder.indexOf(normalizedPeriod(b))
        || String(a.displayName).localeCompare(String(b.displayName))
      ));

    countTarget.textContent = String(filtered.length);
    listTarget.innerHTML = filtered.length
      ? filtered.map((place) => {
          const linkedEvents = eventCount(place);
          return `
            <li>
              <button type="button" data-id="${escapeHtml(place.id)}" aria-current="false">
                <span class="place-list__main">
                  <strong>${escapeHtml(place.displayName)}</strong>
                  <small>${escapeHtml([place.city, place.country].filter(Boolean).join(", "))} · ${escapeHtml(humanize(place.placeType))}</small>
                </span>
                <span class="place-list__count" aria-label="${linkedEvents} linked ${linkedEvents === 1 ? "event" : "events"}">${linkedEvents}</span>
              </button>
            </li>`;
        }).join("")
      : `<li class="place-list__empty">No places match these filters.</li>`;

    if (selectedId && !filtered.some((place) => place.id === selectedId)) resetSelection();

    markerById.clear();
    markerLayer?.clearLayers();
    const bounds = [];
    for (const place of filtered) {
      if (!map || !Number.isFinite(place.latitude) || !Number.isFinite(place.longitude)) continue;
      const marker = window.L.marker([place.latitude, place.longitude], {
        icon: markerIcon(place, place.id === selectedId),
        keyboard: true,
        title: place.displayName,
        alt: place.displayName,
        placeRecord: place,
      });
      marker.bindTooltip(place.displayName, { direction: "top", offset: [0, -14], opacity: 0.96 });
      marker.on("click", () => selectPlace(place, { moveMap: false }));
      marker.addTo(markerLayer);
      markerById.set(place.id, marker);
      bounds.push([place.latitude, place.longitude]);
    }

    if (map && bounds.length) {
      if (bounds.length === 1) map.setView(bounds[0], 11);
      else map.fitBounds(bounds, { padding: [42, 42], maxZoom: filtered.length > 8 ? 5 : 10 });
    }

    listTarget.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        const place = filtered.find((item) => item.id === button.dataset.id);
        if (place) selectPlace(place);
      });
    });
  }

  search.addEventListener("input", debounce(render));
  period.addEventListener("change", render);
  render();
} catch (error) {
  countTarget.textContent = "—";
  renderError(listTarget, error);
}
