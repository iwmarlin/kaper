import { escapeHtml, humanize, PERIOD_ORDER, periodValues } from "./core.js?v=2f91b87db0";

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

/* Forty-four of the forty-five places carry dated events. The forty-fifth,
   the Morskie Oko revue theatre, is on the map because a song of Kaper's was
   sung there, which three sources attest and no timeline event records — so
   saying "0 linked events" about it stated an absence instead of the evidence
   there is. */
export function evidenceSummary(place) {
  const events = eventCount(place);
  if (events) return `${events} linked ${events === 1 ? "event" : "events"}`;
  const sources = (place.sourceIds || []).length;
  if (sources) return `no dated event; ${sources} linked ${sources === 1 ? "source" : "sources"}`;
  return "no linked records";
}

export function placeListLabel(place) {
  return `${place.displayName}; ${precisionMeta(place).label}; ${evidenceSummary(place)}`;
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
                <span class="place-list__count" aria-label="${escapeHtml(evidenceSummary(place))}">${linkedEvents || "·"}</span>`;
}
