import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=8b85a346f3";
import {
  debounce,
  humanize,
  loadSiteIndex,
  mountSiteChrome,
  normalizeSearch,
  registerImageDerivatives,
  renderError,
} from "./core.js?v=8b85a346f3";
import { createQueryState } from "./catalogue-filters.js?v=8b85a346f3";
import {
  GROUP_LABELS,
  GROUP_ORDER,
  eventGroup,
  renderTimeline,
  sortEvents,
} from "./timeline-view.js?v=8b85a346f3";

registerImageDerivatives(IMAGE_DERIVATIVES);
mountSiteChrome("timeline");

const target = document.querySelector("#timeline-results");
const countTarget = document.querySelector("#timeline-count");
const totalLabelTarget = document.querySelector("#timeline-total-label");
const controls = {
  search: document.querySelector("#timeline-search"),
  category: document.querySelector("#timeline-category"),
};
const viewControls = {
  highlights: document.querySelector("#timeline-view-highlights"),
  all: document.querySelector("#timeline-view-all"),
};
const hasPrerenderedResults = target?.dataset.prerendered === "true";

function updateActiveChapter() {
  const nav = document.querySelector(".timeline-nav");
  if (!nav) return;
  const chapters = [...document.querySelectorAll(".timeline-chapter")];
  if (!chapters.length) return;
  const marker = nav.getBoundingClientRect().bottom + 8;
  let activeKey = chapters[0].id.replace("chapter-", "");
  for (const chapter of chapters) {
    if (chapter.getBoundingClientRect().top - marker <= 0) activeKey = chapter.id.replace("chapter-", "");
    else break;
  }
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

  function render() {
    const query = normalizeSearch(controls.search.value.trim());
    const matching = indexed.filter((event) => (
      (!query || event._search.includes(query))
      && (!controls.category.value || eventGroup(event) === controls.category.value)
    ));
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
    defaults: { search: "", category: "", view: "highlights" },
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
  for (const control of [controls.category].filter(Boolean)) control.addEventListener("change", () => {
    if (control.value && activeView === "highlights") setView("all", { renderNow: false });
    render();
  });
  viewControls.highlights?.addEventListener("click", () => setView("highlights"));
  viewControls.all?.addEventListener("click", () => setView("all"));
  document.querySelector("#timeline-reset")?.addEventListener("click", () => {
    for (const control of Object.values(controls).filter(Boolean)) control.value = "";
    setView("highlights", { renderNow: false });
    render();
  });
  render();
} catch (error) {
  if (!hasPrerenderedResults) {
    countTarget.textContent = "Timeline unavailable";
    renderError(target, error);
  }
}
