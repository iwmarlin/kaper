import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=eac6d7ea60";
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
} from "./core.js?v=eac6d7ea60";
import { createQueryState } from "./catalogue-filters.js?v=eac6d7ea60";
import {
  GROUP_LABELS,
  GROUP_ORDER,
  eventGroup,
  renderTimeline,
  sortEvents,
} from "./timeline-view.js?v=eac6d7ea60";

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
const hasPrerenderedResults = target?.dataset.prerendered === "true";

function updateActiveChapter() {
  const nav = document.querySelector(".timeline-nav");
  if (!nav) return;
  const entries = [...document.querySelectorAll(".timeline-entry[data-chapter]")];
  if (!entries.length) return;
  const marker = nav.getBoundingClientRect().bottom + 8;
  // The era a reader is in is the era of the entry under the strip, not the
  // last chapter heading to have passed it: a heading and its first events can
  // fill the screen while the strip still lights the era before.
  const current = entries.find((entry) => entry.getBoundingClientRect().bottom > marker)
    || entries[entries.length - 1];
  const activeKey = current.dataset.chapter;
  for (const tab of nav.querySelectorAll(".timeline-nav__tab")) {
    const isActive = tab.dataset.chapter === activeKey;
    tab.classList.toggle("is-active", isActive);
    if (isActive) tab.setAttribute("aria-current", "true");
    else tab.removeAttribute("aria-current");
  }
}

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
  // era strip above it only jumps. The other indexes filter by period; this one
  // now does too, so "the Paris years" is a question the page can answer.
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
  let timelineQueryState;

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
    updateActiveChapter();
    timelineQueryState?.write();
  }

  timelineQueryState = createQueryState({
    ...controls,
    view: {
      getValue: () => activeView,
      setValue: (value) => { activeView = value === "all" ? "all" : "highlights"; },
    },
  }, {
    defaults: { search: "", category: "", period: "", view: "highlights" },
    indexType: "event",
    onRestore: () => {
      setView(activeView, { renderNow: false });
      render();
    },
  });
  timelineQueryState.read();
  setView(activeView, { renderNow: false });

  let scrollScheduled = false;
  function onScroll() {
    if (scrollScheduled) return;
    scrollScheduled = true;
    requestAnimationFrame(() => {
      scrollScheduled = false;
      updateActiveChapter();
    });
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll, { passive: true });

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
  document.querySelector("#timeline-reset")?.addEventListener("click", () => {
    for (const control of Object.values(controls).filter(Boolean)) control.value = "";
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
  if (printedStateStands) {
    updateActiveChapter();
  } else {
    render();
  }
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
