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
} from "./core.js?v=5d483e810a";

mountSiteChrome("map");

const listTarget = document.querySelector("#place-list");
const countTarget = document.querySelector("#place-count");
const totalTarget = document.querySelector("#map-total");
const search = document.querySelector("#place-search");
const selectionPanel = document.querySelector("#place-selection");
const selectionKicker = document.querySelector("#place-selection-kicker");
const selectionTitle = document.querySelector("#place-selection-title");
const selectionMeta = document.querySelector("#place-selection-meta");
const selectionFacts = document.querySelector("#place-selection-facts");
const selectionPrecision = document.querySelector("#place-selection-precision");
const selectionPeriods = document.querySelector("#place-selection-periods");
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

const PRECISION_META = Object.freeze({
  address_level: {
    label: "Address-level coordinates",
    shortLabel: "Address level",
    markerClass: "point",
  },
  venue_level: {
    label: "Venue-level coordinates",
    shortLabel: "Venue level",
    markerClass: "point",
  },
  site_approximate: {
    label: "Approximate historical site",
    shortLabel: "Approximate site",
    markerClass: "approximate",
  },
  district_level: {
    label: "District-level reference point",
    shortLabel: "District level",
    markerClass: "area",
  },
  city_level: {
    label: "City-level reference point",
    shortLabel: "City level",
    markerClass: "area",
  },
});

function precisionMeta(place) {
  return PRECISION_META[place.mapPrecision] || {
    label: "Coordinate precision not specified",
    shortLabel: "Precision not specified",
    markerClass: "unspecified",
  };
}

function linkedPeriodLabel(place) {
  return periodValues(place).map(periodLabel).join(" · ");
}

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
  const precision = precisionMeta(place);
  const size = Math.min(24, 14 + Math.sqrt(Math.max(eventCount(place), 1)) * 2.2);
  return window.L.divIcon({
    className: "map-place-icon-shell",
    html: `<span class="map-place-marker map-place-marker--${escapeHtml(periodKey)} map-place-marker--precision-${escapeHtml(precision.markerClass)}${selected ? " is-selected" : ""}" style="--marker-size:${size}px" aria-hidden="true"></span>`,
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
  if (selectionPanel) selectionPanel.dataset.state = "empty";
  selectionKicker.textContent = "Explore the map";
  selectionTitle.textContent = "Select a place";
  selectionMeta.textContent = "Choose a marker or a place from the list to see its role in the archive.";
  if (selectionFacts) selectionFacts.hidden = true;
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
  if (selectionPanel) selectionPanel.dataset.state = "selected";
  document.querySelectorAll("#place-list button").forEach((button) => {
    button.setAttribute("aria-current", String(button.dataset.id === place.id));
  });

  selectionKicker.textContent = humanize(place.placeType || "Documented place");
  selectionTitle.textContent = place.displayName;
  const location = [place.city, place.country].filter(Boolean).join(", ");
  const linkedEvents = eventCount(place);
  selectionMeta.textContent = [location, humanize(place.placeType), `${linkedEvents} linked ${linkedEvents === 1 ? "event" : "events"}`]
    .filter(Boolean)
    .join(" · ");
  if (selectionFacts && selectionPrecision && selectionPeriods) {
    selectionPrecision.textContent = precisionMeta(place).label;
    selectionPeriods.textContent = linkedPeriodLabel(place) || "No linked event period";
    selectionFacts.hidden = false;
  }
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
  const { places, timelineEvents } = await loadTables(["places", "timelineEvents"]);
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

  // The itinerary is data, not a literal in this file. Every stage is a timeline
  // event that carries an ordered routePlaceIds, so its dates, description and
  // sources come from the same record the rest of the archive cites, and the
  // route cannot drift from the chronology.
  //
  // Stages are drawn as separate polylines rather than one continuous line.
  // Kaper reached Los Angeles in October 1934 and re-entered at Calexico in
  // November 1935; joining those points would draw a leg no source documents.
  // The earlier stages are moves between places of residence years apart, which
  // is a different kind of claim from a single Atlantic crossing, and separate
  // segments keep them from reading as one continuous trip.
  const placeById = new Map(publicPlaces.map((place) => [place.id, place]));
  const routeStages = (timelineEvents || [])
    .filter((event) => Array.isArray(event.routePlaceIds) && event.routePlaceIds.length > 1)
    .sort((a, b) => String(a.dateStart).localeCompare(String(b.dateStart)))
    .map((event) => ({
      event,
      places: event.routePlaceIds
        .map((id) => placeById.get(id))
        .filter((place) => place && Number.isFinite(place.latitude) && Number.isFinite(place.longitude)),
    }))
    .filter((stage) => stage.places.length > 1);

  let journeyPoints = routeStages.flatMap((stage) => stage.places.map((place) => [place.latitude, place.longitude]));
  let routeLayer = null;
  let routeVisible = true;
  if (map && window.L && routeStages.length) {
    routeLayer = window.L.layerGroup(routeStages.map((stage) => {
      const line = window.L.polyline(
        stage.places.map((place) => [place.latitude, place.longitude]),
        { color: "#8a5a2b", weight: 3, opacity: 0.9, dashArray: "2 6", lineCap: "round", lineJoin: "round" },
      );
      line.bindTooltip(
        `${escapeHtml(stage.event.title)} · ${escapeHtml(stage.event.displayDate || stage.event.dateStart)}`,
        { sticky: true },
      );
      return line;
    }));
  }

  function renderRouteStages() {
    const list = document.querySelector("#route-stages");
    if (!list) return;
    if (!routeStages.length) {
      list.innerHTML = "";
      return;
    }
    list.innerHTML = routeStages.map((stage) => `
      <li class="route-stage">
        <p class="route-stage__date">${escapeHtml(stage.event.displayDate || stage.event.dateStart)}</p>
        <p class="route-stage__path">${stage.places.map((place) => `<a href="${recordUrl("place", place.id)}">${escapeHtml(place.displayName)}</a>`).join(' <span aria-hidden="true">→</span> ')}</p>
        <p class="route-stage__note">${escapeHtml(stage.event.shortDescription || "")}</p>
        <p class="route-stage__links"><a href="${recordUrl("event", stage.event.id)}">${escapeHtml(stage.event.title)}</a></p>
      </li>`).join("");
  }
  renderRouteStages();

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
    const stagesPanel = document.querySelector("#route-stages-panel");
    if (stagesPanel) stagesPanel.hidden = false;
  }

  if (toggleJourney) {
    toggleJourney.addEventListener("click", () => {
      routeVisible = !routeVisible;
      applyRoute();
    });
  }
  applyRoute();

  // The opening view frames the documented stages on the historical map.
  let firstView = true;

  // On a phone the selection card used to sit below the map and below the
  // place list, so tapping a marker moved the answer off-screen. Below 680px
  // the card is moved into the map canvas and shown as an overlay across the
  // foot of the map, where the tap happened; above that width it returns to
  // the top of the side panel, which is where it reads best.
  // On a phone the selection card used to sit below the map and below the
  // place list, so tapping a marker moved the answer off-screen. Below 680px
  // the card is moved into the map canvas and shown as an overlay across the
  // foot of the map, where the tap happened, and the legend is moved the other
  // way — out of the canvas and into the panel — because two absolutely
  // positioned blocks were stacking on top of each other at the bottom of a
  // 24rem map. Above that width both return to where they read best.
  function bindResponsivePlacement() {
    var selection = document.getElementById('place-selection');
    var legend = document.getElementById('map-legend');
    var canvas = document.querySelector('.map-canvas');
    var panel = document.querySelector('.map-panel');
    if (!selection || !legend || !canvas || !panel || !window.matchMedia) return;
    var narrow = window.matchMedia('(max-width: 680px)');
    function place() {
      var selTarget = narrow.matches ? canvas : panel;
      if (selection.parentElement !== selTarget) {
        if (selTarget === canvas) selTarget.appendChild(selection);
        else selTarget.insertBefore(selection, selTarget.firstElementChild);
      }
      var legTarget = narrow.matches ? panel : canvas;
      if (legend.parentElement !== legTarget) {
        if (legTarget === canvas) legTarget.appendChild(legend);
        else legTarget.insertBefore(legend, legTarget.firstElementChild);
      }
      // The summary is hidden on wide screens, so a legend closed on a phone
      // would otherwise stay shut with no control to reopen it.
      if (!narrow.matches) legend.open = true;
    }
    place();
    if (typeof narrow.addEventListener === 'function') narrow.addEventListener('change', place);
    else if (typeof narrow.addListener === 'function') narrow.addListener(place);
  }

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
          const precision = precisionMeta(place);
          const location = [place.city, place.country].filter(Boolean).join(", ");
          return `
            <li>
              <button type="button" data-id="${escapeHtml(place.id)}" aria-current="false" aria-label="${escapeHtml(`${place.displayName}; ${precision.label}; ${linkedEvents} linked ${linkedEvents === 1 ? "event" : "events"}`)}">
                <span class="place-list__main">
                  <strong>${escapeHtml(place.displayName)}</strong>
                  <small>${escapeHtml([location, humanize(place.placeType)].filter(Boolean).join(" · "))}</small>
                  <span class="place-list__precision">${escapeHtml(precision.shortLabel)}</span>
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
      const precision = precisionMeta(place);
      const periods = linkedPeriodLabel(place);
      const accessibleLabel = `${place.displayName} — ${precision.label}${periods ? `; linked-event periods: ${periods}` : ""}`;
      const marker = window.L.marker([place.latitude, place.longitude], {
        icon: markerIcon(place, place.id === selectedId),
        keyboard: true,
        title: accessibleLabel,
        alt: accessibleLabel,
        placeRecord: place,
      });
      marker.bindTooltip(
        `<strong>${escapeHtml(place.displayName)}</strong><span class="leaflet-tooltip__meta">${escapeHtml(precision.shortLabel)}</span>`,
        { direction: "top", offset: [0, -14], opacity: 0.96 },
      );
      marker.on("click", () => selectPlace(place, { moveMap: false }));
      marker.addTo(markerLayer);
      markerById.set(place.id, marker);
      bounds.push([place.latitude, place.longitude]);
    }

    // Typing used to refit the view on every keystroke, and because a zoom
    // change swaps the 1926 sheet for the modern reference layer, the basemap
    // flickered underneath the search box. The map now holds still while a
    // query is being typed and moves only when the result is specific enough
    // to be worth flying to, or when the field is cleared.
    if (map && bounds.length) {
      if (firstView && !query && journeyPoints.length > 1) {
        map.fitBounds(journeyPoints, { padding: [48, 48], maxZoom: HISTORICAL_FULL_ZOOM });
      } else if (!query) {
        map.fitBounds(bounds, { padding: [42, 42], maxZoom: filtered.length > 8 ? 5 : 10 });
      } else if (bounds.length === 1) {
        map.setView(bounds[0], 11);
      } else if (bounds.length <= 4) {
        map.fitBounds(bounds, { padding: [42, 42], maxZoom: 9 });
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
  bindResponsivePlacement();
  render();
} catch (error) {
  countTarget.textContent = "—";
  renderError(listTarget, error);
}
