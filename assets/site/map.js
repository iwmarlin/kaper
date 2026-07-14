import {
  debounce,
  escapeHtml,
  humanize,
  loadTables,
  mountSiteChrome,
  normalizeSearch,
  recordUrl,
  renderError,
} from "./core.js";

mountSiteChrome("map");

const listTarget = document.querySelector("#place-list");
const countTarget = document.querySelector("#place-count");
const search = document.querySelector("#place-search");
const country = document.querySelector("#place-country");
let map;
let markerLayer;
const markerById = new Map();

try {
  const { places } = await loadTables(["places"]);
  const publicPlaces = places;
  for (const value of [...new Set(publicPlaces.map((place) => place.country).filter(Boolean))].sort()) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    country.append(option);
  }

  if (window.L) {
    map = window.L.map("research-map", { scrollWheelZoom: false, zoomControl: true });
    window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);
    markerLayer = window.L.layerGroup().addTo(map);
  } else {
    document.querySelector("#research-map").innerHTML = `<div class="map-fallback"><div><h2>Interactive map unavailable</h2><p>Use the complete searchable place list alongside the map.</p></div></div>`;
  }

  function selectPlace(place) {
    document.querySelectorAll("#place-list button").forEach((button) => {
      button.setAttribute("aria-current", String(button.dataset.id === place.id));
    });
    const marker = markerById.get(place.id);
    if (map && marker) {
      map.flyTo([place.latitude, place.longitude], Math.max(map.getZoom(), 10), { duration: 0.7 });
      marker.openPopup();
    }
  }

  function render() {
    const query = normalizeSearch(search.value.trim());
    const filtered = publicPlaces
      .filter((place) => (
        (!country.value || place.country === country.value)
        && (!query || normalizeSearch([place.displayName, place.city, place.region, place.country, place.placeType].filter(Boolean).join(" ")).includes(query))
      ))
      .sort((a, b) => String(a.country).localeCompare(String(b.country)) || String(a.displayName).localeCompare(String(b.displayName)));
    countTarget.textContent = `${filtered.length} ${filtered.length === 1 ? "place" : "places"}`;
    listTarget.innerHTML = filtered.map((place) => `
      <li><button type="button" data-id="${escapeHtml(place.id)}" aria-current="false">
        <strong>${escapeHtml(place.displayName)}</strong>
        <span>${escapeHtml([place.city, place.country].filter(Boolean).join(", "))} · ${escapeHtml(humanize(place.placeType))} · ${(place.timelineEventIds || []).length} events${Number.isFinite(place.latitude) && Number.isFinite(place.longitude) ? "" : " · not mapped"}</span>
      </button></li>`).join("");

    markerById.clear();
    markerLayer?.clearLayers();
    const bounds = [];
    for (const place of filtered) {
      if (!map || !Number.isFinite(place.latitude) || !Number.isFinite(place.longitude)) continue;
      const marker = window.L.circleMarker([place.latitude, place.longitude], {
        radius: 7,
        weight: 2,
        color: "#fffdf8",
        fillColor: "#a64228",
        fillOpacity: 0.92,
      }).bindPopup(`
        <h3>${escapeHtml(place.displayName)}</h3>
        <p>${escapeHtml([place.city, place.country].filter(Boolean).join(", "))}</p>
        <p>${(place.timelineEventIds || []).length} linked events</p>
        <a href="${recordUrl("place", place.id)}">View place record</a>`);
      marker.addTo(markerLayer);
      markerById.set(place.id, marker);
      bounds.push([place.latitude, place.longitude]);
    }
    if (map && bounds.length) map.fitBounds(bounds, { padding: [28, 28], maxZoom: 11 });
    listTarget.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        const place = filtered.find((item) => item.id === button.dataset.id);
        if (place) selectPlace(place);
      });
    });
  }

  search.addEventListener("input", debounce(render));
  country.addEventListener("change", render);
  render();
} catch (error) {
  countTarget.textContent = "Places unavailable";
  renderError(listTarget, error);
}
