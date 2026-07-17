import {
  debounce,
  escapeHtml,
  humanize,
  loadTables,
  mountSiteChrome,
  normalizeSearch,
  PERIOD_ORDER,
  periodLabel,
  periodValues,
  recordUrl,
  renderError,
} from "./core.js?v=20260716-3";

mountSiteChrome("map");

const listTarget = document.querySelector("#place-list");
const countTarget = document.querySelector("#place-count");
const totalTarget = document.querySelector("#map-total");
const search = document.querySelector("#place-search");
const selectionKicker = document.querySelector("#place-selection-kicker");
const selectionTitle = document.querySelector("#place-selection-title");
const selectionMeta = document.querySelector("#place-selection-meta");
const selectionNote = document.querySelector("#place-selection-note");
const selectionLink = document.querySelector("#place-selection-link");
const toggleJourney = document.querySelector("#toggle-journey");
const layerStatus = document.querySelector("#map-layer-status");
const layerStatusLabel = document.querySelector("#map-layer-status-label");
const layerStatusDetail = document.querySelector("#map-layer-status-detail");

let map;
let markerLayer;
let historicalBasemap;
let referenceBasemap;
let historicalBasemapAvailable = true;
let selectedId = null;
const markerById = new Map();

const HISTORICAL_FULL_ZOOM = 3;
const REFERENCE_FULL_ZOOM = 5;
const HISTORICAL_ATTRIBUTION = '<a href="https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~363901~90131510%3AThe-world-on-Mercator-s-projection-" target="_blank" rel="noopener">Edward Stanford Ltd., 1926</a> · David Rumsey Map Collection';
const REFERENCE_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors';
const STANFORD_MAP_BOUNDS = [[-70.1, -195.5], [84.5, 183.2]];

function historicalOpacity(zoom) {
  if (zoom <= HISTORICAL_FULL_ZOOM) return 1;
  if (zoom >= REFERENCE_FULL_ZOOM) return 0;
  return (REFERENCE_FULL_ZOOM - zoom) / (REFERENCE_FULL_ZOOM - HISTORICAL_FULL_ZOOM);
}

function updateAttribution(showHistorical, showReference) {
  if (!map?.attributionControl) return;
  map.attributionControl.removeAttribution(HISTORICAL_ATTRIBUTION);
  map.attributionControl.removeAttribution(REFERENCE_ATTRIBUTION);
  if (showHistorical) map.attributionControl.addAttribution(HISTORICAL_ATTRIBUTION);
  if (showReference) map.attributionControl.addAttribution(REFERENCE_ATTRIBUTION);
}

function updateBasemap(zoom = map?.getZoom()) {
  if (!map || !Number.isFinite(zoom) || !referenceBasemap) return;

  const historical = historicalBasemapAvailable ? historicalOpacity(zoom) : 0;
  const reference = 1 - historical;
  historicalBasemap?.setOpacity(historical);
  referenceBasemap.setOpacity(reference);
  updateAttribution(historical > 0.02, reference > 0.02);

  if (!layerStatus || !layerStatusLabel || !layerStatusDetail) return;
  if (historical >= 0.75) {
    layerStatus.dataset.mode = "historical";
    layerStatusLabel.textContent = "Historical map · 1926";
    layerStatusDetail.textContent = "Edward Stanford Ltd.";
  } else if (historical > 0.02) {
    layerStatus.dataset.mode = "transition";
    layerStatusLabel.textContent = "Historical map + geographic reference";
    layerStatusDetail.textContent = "The reference layer appears as you zoom in";
  } else {
    layerStatus.dataset.mode = "reference";
    layerStatusLabel.textContent = "Present-day geographic reference";
    layerStatusDetail.textContent = "Zoom out to return to the 1926 map";
  }
}

function normalizedPeriod(place) {
  return periodValues(place)[0] || "";
}

function eventCount(place) {
  return (place.timelineEventIds || []).length;
}

function markerIcon(place, selected = false) {
  const periodKey = periodValues(place).join("_") || normalizedPeriod(place);
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
  if (selectionNote) {
    selectionNote.textContent = "";
    selectionNote.hidden = true;
  }
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
  const careerPeriods = periodValues(place).map(periodLabel).join(" · ");
  const linkedEvents = eventCount(place);
  selectionMeta.textContent = [location, careerPeriods, `${linkedEvents} linked ${linkedEvents === 1 ? "event" : "events"}`]
    .filter(Boolean)
    .join(" · ");
  if (selectionNote) {
    if (place.publicNote) {
      selectionNote.textContent = place.publicNote;
      selectionNote.hidden = false;
    } else {
      selectionNote.textContent = "";
      selectionNote.hidden = true;
    }
  }
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

  if (window.L) {
    map = window.L.map("research-map", {
      scrollWheelZoom: false,
      zoomControl: true,
      preferCanvas: true,
    });
    referenceBasemap = window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      opacity: 0,
    }).addTo(map);

    map.createPane("historicalBasemap");
    const historicalPane = map.getPane("historicalBasemap");
    historicalPane.classList.add("historical-basemap-pane");
    historicalPane.style.zIndex = "250";
    historicalPane.style.pointerEvents = "none";
    historicalBasemap = window.L.imageOverlay(
      "assets/images/maps/world-1926-stanford-mercator.jpg",
      STANFORD_MAP_BOUNDS,
      {
        pane: "historicalBasemap",
        opacity: 1,
        alt: "Edward Stanford's 1926 political world map in Mercator projection",
      },
    ).addTo(map);
    historicalBasemap.on("error", () => {
      historicalBasemapAvailable = false;
      updateBasemap(map.getZoom());
    });
    map.on("zoomanim", (event) => updateBasemap(event.zoom));
    map.on("zoomend", () => updateBasemap(map.getZoom()));

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

  // Canonical migration route: Warsaw → Berlin → Vienna → Paris → Le Havre → Pier 57 (NY) → Los Angeles
  const JOURNEY_IDS = ["PL001", "PL002", "PL030", "PL003", "PL026", "PL025", "PL004"];
  let journeyPoints = [];
  let routeLayer = null;
  let routeVisible = true;
  if (map && window.L) {
    journeyPoints = JOURNEY_IDS
      .map((id) => publicPlaces.find((place) => place.id === id))
      .filter((place) => place && Number.isFinite(place.latitude) && Number.isFinite(place.longitude))
      .map((place) => [place.latitude, place.longitude]);
    if (journeyPoints.length > 1) {
      routeLayer = window.L.polyline(journeyPoints, {
        color: "#8a5a2b",
        weight: 2.5,
        opacity: 0.85,
        dashArray: "1 7",
        lineCap: "round",
        lineJoin: "round",
        interactive: false,
      });
    }
  }

  function applyRoute() {
    if (!toggleJourney) return;
    if (!routeLayer || !map) {
      toggleJourney.hidden = true;
      return;
    }
    if (routeVisible) routeLayer.addTo(map);
    else map.removeLayer(routeLayer);
    toggleJourney.setAttribute("aria-pressed", String(routeVisible));
    toggleJourney.textContent = routeVisible ? "Hide route" : "Show route";
  }

  if (toggleJourney) {
    toggleJourney.addEventListener("click", () => {
      routeVisible = !routeVisible;
      applyRoute();
    });
  }
  applyRoute();

  // The opening view presents the complete migration route on the historical map.
  let firstView = true;

  function render() {
    const query = normalizeSearch(search.value.trim());
    const filtered = publicPlaces
      .filter((place) => (
        !query || normalizeSearch([
          place.displayName,
          place.city,
          place.region,
          place.country,
          place.placeType,
        ].filter(Boolean).join(" ")).includes(query)
      ))
      .sort((a, b) => (
        eventCount(b) - eventCount(a)
        || PERIOD_ORDER.indexOf(normalizedPeriod(a)) - PERIOD_ORDER.indexOf(normalizedPeriod(b))
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
                  <small>${escapeHtml([place.city, place.country].filter(Boolean).join(", "))} · ${escapeHtml(humanize(place.placeType))} · ${escapeHtml(periodValues(place).map((value) => periodLabel(value).replace(" · ", " ")).join(" / "))}</small>
                </span>
                <span class="place-list__count" aria-label="${linkedEvents} linked ${linkedEvents === 1 ? "event" : "events"}">${linkedEvents}</span>
              </button>
            </li>`;
        }).join("")
      : `<li class="place-list__empty">No places match your search.</li>`;

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
      if (firstView && !query && journeyPoints.length > 1) {
        map.fitBounds(journeyPoints, { padding: [48, 48], maxZoom: HISTORICAL_FULL_ZOOM });
      } else if (bounds.length === 1) {
        map.setView(bounds[0], 11);
      } else {
        map.fitBounds(bounds, { padding: [42, 42], maxZoom: filtered.length > 8 ? 5 : 10 });
      }
      updateBasemap(map.getZoom());
      firstView = false;
    }

    listTarget.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        const place = filtered.find((item) => item.id === button.dataset.id);
        if (place) selectPlace(place);
      });
    });
  }

  search.addEventListener("input", debounce(render));
  render();
} catch (error) {
  countTarget.textContent = "—";
  renderError(listTarget, error);
}
