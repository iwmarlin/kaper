import { escapeHtml, humanize, PERIOD_ORDER, periodValues } from "./core.js?v=4a21a1260e";

// The map page and the build both list the documented places from this module,
// so the list printed for a reader without JavaScript matches the interactive one.

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

export function precisionMeta(place) {
  return PRECISION_META[place.mapPrecision] || {
    label: "Coordinate precision not specified",
    shortLabel: "Precision not specified",
    markerClass: "unspecified",
  };
}

export function normalizedPeriod(place) {
  return periodValues(place)[0] || "";
}

export function eventCount(place) {
  return (place.timelineEventIds || []).length;
}

export function sortPlaces(places) {
  return [...places].sort((a, b) => (
    eventCount(b) - eventCount(a)
    || PERIOD_ORDER.indexOf(normalizedPeriod(a)) - PERIOD_ORDER.indexOf(normalizedPeriod(b))
    || String(a.displayName).localeCompare(String(b.displayName))
  ));
}

export function placeListLabel(place) {
  const linkedEvents = eventCount(place);
  return `${place.displayName}; ${precisionMeta(place).label}; ${linkedEvents} linked ${linkedEvents === 1 ? "event" : "events"}`;
}

export function placeListContent(place) {
  const linkedEvents = eventCount(place);
  const location = [place.city, place.country].filter(Boolean).join(", ");
  return `
                <span class="place-list__main">
                  <strong>${escapeHtml(place.displayName)}</strong>
                  <small>${escapeHtml([location, humanize(place.placeType)].filter(Boolean).join(" · "))}</small>
                  <span class="place-list__precision">${escapeHtml(precisionMeta(place).shortLabel)}</span>
                </span>
                <span class="place-list__count" aria-label="${linkedEvents} linked ${linkedEvents === 1 ? "event" : "events"}">${linkedEvents}</span>`;
}
