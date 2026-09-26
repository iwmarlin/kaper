import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=5c233b4282";
import {
  debounce,
  humanize,
  loadSiteIndex,
  matchesPeriod,
  mountSiteChrome,
  normalizeSearch,
  PERIOD_ORDER,
  periodLabel,
  periodValues,
  registerImageDerivatives,
  renderError,
} from "./core.js?v=5c233b4282";
import { createCatalogueFilters } from "./catalogue-filters.js?v=5c233b4282";
import {
  GROUP_LABELS,
  GROUP_ORDER,
  eventGroup,
  renderTimeline,
  sortEvents,
} from "./timeline-view.js?v=5c233b4282";

registerImageDerivatives(IMAGE_DERIVATIVES);
mountSiteChrome("timeline");

const target = document.querySelector("#timeline-results");
const countTarget = document.querySelector("#timeline-count");
const totalLabelTarget = document.querySelector("#timeline-total-label");
const controls = {
  search: document.querySelector("#timeline-search"),
  category: document.querySelector("#timeline-category"),
  period: document.querySelector("#timeline-period"),
};
const viewControls = {
  highlights: document.querySelector("#timeline-view-highlights"),
  all: document.querySelector("#timeline-view-all"),
};
const resetButton = document.querySelector("#timeline-reset");
const filterToggle = document.querySelector("#timeline-filter-toggle");
const advancedFilters = document.querySelector("#timeline-filter-options");
const activeFilters = document.querySelector("#timeline-active-filters");
const filterCount = document.querySelector("#timeline-filter-count");
const filterOptions = [
  { key: "category", label: "Category", defaultValue: "" },
  { key: "period", label: "Period", defaultValue: "" },
];
const hasPrerenderedResults = target?.dataset.prerendered === "true";

function addOptions(select, values, labeler = humanize, preserveOrder = false) {
  const uniqueValues = [...new Set(values.filter(Boolean))];
  for (const value of preserveOrder ? uniqueValues : uniqueValues.sort()) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = labeler(value);
    select.append(option);
  }
}

try {
  const { records: timelineEvents } = await loadSiteIndex("timeline");
  if (totalLabelTarget) {
    totalLabelTarget.textContent = `${timelineEvents.length} published ${timelineEvents.length === 1 ? "event" : "events"}`;
  }
  addOptions(
    controls.category,
    GROUP_ORDER.filter((key) => timelineEvents.some((event) => eventGroup(event) === key)),
    (key) => GROUP_LABELS[key],
    true,
  );
  // The chronology is read by era before it is read by anything else, and the
  // other indexes all filter by period; this one does too, so "the Paris
  // years" is a question the page can answer rather than one a reader has to
  // scroll for.
  const availablePeriods = new Set(timelineEvents.flatMap(periodValues));
  addOptions(
    controls.period,
    PERIOD_ORDER.filter((value) => availablePeriods.has(value)),
    periodLabel,
    true,
  );

  const indexed = sortEvents(timelineEvents).map((event) => ({
    ...event,
    _search: normalizeSearch([
      event.title,
      event.displayDate,
      event.placeDisplay,
      event.shortDescription,
      event.longDescription,
      event.searchPeople,
    ].filter(Boolean).join(" ")),
  }));

  let activeView = "highlights";
  let filterController;

  function setView(view, { renderNow = true } = {}) {
    activeView = view === "all" ? "all" : "highlights";
    for (const [key, button] of Object.entries(viewControls)) {
      if (!button) continue;
      const isActive = key === activeView;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", String(isActive));
    }
    if (renderNow) render();
  }

  function matchesFilters(event) {
    const query = normalizeSearch(controls.search.value.trim());
    return (!query || event._search.includes(query))
      && (!controls.category.value || eventGroup(event) === controls.category.value)
      && matchesPeriod(event, controls.period.value);
  }

  function render() {
    const matching = indexed.filter(matchesFilters);
    const { countHtml, markup } = renderTimeline(matching, activeView);
    countTarget.innerHTML = countHtml;
    target.innerHTML = markup;
    target.dataset.prerendered = "false";
    filterController?.update();
    filterController?.write();
  }

  // The chronology joins the shell the other catalogues use: the search stays
  // in reach, the facets fold behind a labelled toggle on a narrow screen, and
  // the choices in force appear as chips that remove themselves. The view is
  // registered as a field so it keeps its place in the address, but it is not
  // a facet: choosing the full chronology is not a filter and earns no chip.
  filterController = createCatalogueFilters({
    controls: {
      ...controls,
      view: {
        getValue: () => activeView,
        setValue: (value) => { activeView = value === "all" ? "all" : "highlights"; },
      },
    },
    options: filterOptions,
    toggle: filterToggle,
    panel: advancedFilters,
    activeFilters,
    count: filterCount,
    resetButton,
    onChange: render,
    onRestore: () => {
      setView(activeView, { renderNow: false });
      render();
    },
    fieldDefaults: { view: "highlights" },
    toggleLabel: "Filters",
    indexType: "event",
  });
  filterController.read();
  setView(activeView, { renderNow: false });

  controls.search?.addEventListener("input", debounce(() => {
    if (controls.search.value.trim() && activeView === "highlights") setView("all", { renderNow: false });
    render();
  }));
  for (const control of [controls.category, controls.period].filter(Boolean)) control.addEventListener("change", () => {
    if (control.value && activeView === "highlights") setView("all", { renderNow: false });
    render();
  });
  // A link to one event names an entry the opening view may not draw: forty of
  // the fifty-five events are not milestones. The view is a default nobody
  // chose and gives way to the address — but only when it is the view that
  // hides the event, because an address that also filters to one era is
  // stating both things, and the filter is the reader's.
  function hashEventId() {
    const match = /^#event-(TE\d+)$/.exec(location.hash || "");
    return match ? match[1] : "";
  }

  function hashNeedsFullView() {
    const eventId = hashEventId();
    if (!eventId || document.getElementById(`event-${eventId}`)) return false;
    return indexed.some((event) => event.id === eventId && matchesFilters(event));
  }

  function landOnHashTarget() {
    const entry = document.getElementById(`event-${hashEventId()}`);
    if (!entry) return;
    const margin = Number.parseFloat(window.getComputedStyle(entry).scrollMarginTop) || 0;
    // "instant", not "auto": the stylesheet asks for smooth scrolling and
    // "auto" defers to it, so the landing became an animation that the
    // browser's own scrolling could cut short. A link should arrive, not
    // travel.
    window.scrollTo({
      top: Math.max(0, entry.getBoundingClientRect().top + window.scrollY - margin),
      behavior: "instant",
    });
  }

  window.addEventListener("hashchange", () => {
    if (!hashNeedsFullView()) return;
    setView("all");
    landOnHashTarget();
  });
  viewControls.highlights?.addEventListener("click", () => setView("highlights"));
  viewControls.all?.addEventListener("click", () => setView("all"));
  resetButton?.addEventListener("click", () => {
    for (const control of Object.values(controls).filter(Boolean)) control.value = "";
    filterController.close();
    setView("highlights", { renderNow: false });
    render();
  });
  // In the common case the printed chronology is already the one this state
  // asks for, and drawing identical markup over it is work for nothing that
  // also throws away the browser's own handling of "#event-…". So the print is
  // left standing, and only a state it cannot show — a filter, the full
  // chronology — is drawn here.
  const printedStateStands = hasPrerenderedResults
    && activeView === "highlights"
    && !controls.search.value
    && !controls.category.value
    && !controls.period.value;
  if (!printedStateStands) render();
  // The landing waits for the document to be complete. While the page is still
  // being parsed the browser is making its own attempts at the fragment, and
  // the last one wins — which, on a page whose entries arrive with the script,
  // is an attempt at an entry that was not there. Afterwards nothing else is
  // competing for the scroll position. Opening the full chronology for a link
  // happens in the same breath, so the redraw is not seen.
  function openHashTarget() {
    if (hashNeedsFullView()) setView("all");
    landOnHashTarget();
  }

  // Until the printed chronology was left standing, every load replaced it and
  // the page went back to the top by accident. Now that it stands, a reload
  // keeps whatever position the browser remembers, which on a chronology this
  // long is disorienting: the reader asked to see the page again, not to be
  // returned to the middle of 1931. A reload starts at the top — unless the
  // address names a place, which is a request to land there. Going back and
  // forward still restores the position, because that is what those buttons
  // are for.
  const [navigation] = performance.getEntriesByType("navigation");
  if (navigation?.type === "reload" && !location.hash) {
    window.scrollTo({ top: 0, behavior: "instant" });
    window.addEventListener("load", () => {
      if (!location.hash) window.scrollTo({ top: 0, behavior: "instant" });
    }, { once: true });
  }

  if (hashEventId()) {
    if (document.readyState === "complete") openHashTarget();
    else {
      const restingAt = window.scrollY;
      window.addEventListener("load", () => {
        if (Math.abs(window.scrollY - restingAt) < 5 || hashNeedsFullView()) openHashTarget();
      }, { once: true });
    }
  }
} catch (error) {
  if (!hasPrerenderedResults) {
    countTarget.textContent = "Timeline unavailable";
    renderError(target, error);
  }
}
