import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=c77ada42a0";
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
  renderError,
} from "./core.js?v=c77ada42a0";
import { createCatalogueFilters } from "./catalogue-filters.js?v=c77ada42a0";
import {
  curatedMediaOrder,
  registerCatalogueImageDerivatives,
  renderMediaIndexCard,
  sortMediaIndex,
} from "./catalogue-results.js?v=c77ada42a0";

registerCatalogueImageDerivatives(IMAGE_DERIVATIVES);
mountSiteChrome("media");

const controls = {
  search: document.querySelector("#media-search"),
  category: document.querySelector("#media-category"),
  period: document.querySelector("#media-period"),
  rights: document.querySelector("#media-rights"),
  scope: document.querySelector("#media-scope"),
};

// The gallery used to filter on mediaType, which sorts 240 items into five
// buckets of which one — image — holds 188 of them, so the control barely
// discriminated. Category is the axis that actually separates a portrait from
// a press clipping from a film poster. Rights is exposed because this archive
// records them per item and a reader looking for a reusable image should be
// able to ask for one.
const CATEGORY_LABELS = {
  "portrait": "Portraits",
  "press clipping": "Press clippings",
  "place / context image": "Places and contexts",
  "film poster": "Film posters",
  "film-periodical cover": "Film-periodical covers",
  "audio/video reference": "Audio and video",
  "sheet music": "Sheet music",
  "archival document": "Archival documents",
  "trade advertisement": "Trade advertisements",
  "document gallery": "Document galleries",
  "lobby card / title card": "Lobby and title cards",
  "event photograph": "Event photographs",
};
const filterToggle = document.querySelector("#media-filter-toggle");
const advancedFilters = document.querySelector("#media-filter-options");
const activeFilters = document.querySelector("#media-active-filters");
const filterCount = document.querySelector("#media-filter-count");
const resetButton = document.querySelector("#media-reset");
// The gallery carries one control more than the catalogue, so it uses the same
// pattern: the search stays in reach and the facets fold away on a narrow
// screen. "Show" defaults to the curated selection rather than to nothing,
// which is why it declares its own default here.
const filterOptions = [
  { key: "category", label: "Kind", defaultValue: "" },
  { key: "period", label: "Period", defaultValue: "" },
  { key: "rights", label: "Rights", defaultValue: "" },
  { key: "scope", label: "Show", defaultValue: "selected" },
];
const target = document.querySelector("#media-results");
const countTarget = document.querySelector("#media-count");
const more = document.querySelector("#media-more");
const showAll = document.querySelector("#media-show-all");
const PAGE_SIZE = 30;
let visible = PAGE_SIZE;
let showingAll = false;
let current = [];
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
  const { records: media } = await loadSiteIndex("media");
  const categoryCounts = new Map();
  for (const item of media) {
    if (item.category) categoryCounts.set(item.category, (categoryCounts.get(item.category) || 0) + 1);
  }
  addOptions(
    controls.category,
    media.map((item) => item.category),
    (value) => `${CATEGORY_LABELS[value] || humanize(value)} (${categoryCounts.get(value) || 0})`,
  );
  const availablePeriods = new Set(media.flatMap(periodValues));
  addOptions(controls.period, PERIOD_ORDER.filter((value) => availablePeriods.has(value)), periodLabel, true);
  const indexed = media.map((item) => ({
    ...item,
    _search: normalizeSearch([item.title, item.category, item.publicCaption, item.description, item.publicCreditLine, ...periodValues(item), item.category].filter(Boolean).join(" ")),
  }));
  let filterController;

  function render() {
    filterController.update();
    const query = normalizeSearch(controls.search.value.trim());
    current = indexed
      .filter((item) => (
        (!query || item._search.includes(query))
        && (!controls.category.value || item.category === controls.category.value)
        && matchesPeriod(item, controls.period.value)
        && (!controls.rights.value || item.rightsStatus === controls.rights.value)
        && (controls.scope.value === "all" || item.galleryStatus === controls.scope.value)
      ));
    const isDefaultCuratedView = controls.scope.value === "selected"
      && !query
      && !controls.category.value
      && !controls.period.value
      && !controls.rights.value;
    current = isDefaultCuratedView ? curatedMediaOrder(current) : sortMediaIndex(current);
    const shown = current.slice(0, showingAll ? current.length : visible);
    countTarget.innerHTML = `<strong>Showing ${shown.length}</strong> of ${current.length} ${current.length === 1 ? "item" : "items"}`;
    const remaining = current.length - shown.length;
    more.hidden = remaining <= 0;
    showAll.hidden = remaining <= 0;
    if (remaining > 0) {
      const nextCount = Math.min(PAGE_SIZE, remaining);
      more.textContent = `Load ${nextCount} more`;
      more.setAttribute("aria-label", `Load ${nextCount} more media items`);
      showAll.textContent = `Show all ${current.length}`;
      showAll.setAttribute("aria-label", `Show all ${current.length} media items`);
    }
    if (!shown.length) {
      target.innerHTML = `<div class="empty-state"><h2>No matching media</h2><p>Try a broader search, another kind, or show all public media.</p></div>`;
      filterController.write();
      return;
    }
    target.innerHTML = shown.map(renderMediaIndexCard).join("");
    target.dataset.prerendered = "false";
    filterController.write();
  }

  function resetAndRender() {
    visible = PAGE_SIZE;
    showingAll = false;
    render();
  }
  const startDiscovery = () => {
    // The curated selection is the landing view, not a hidden limit on a
    // reader's query. Once a reader searches or chooses a facet, search the
    // complete public media set and reflect that change in the visible scope
    // control. The reader can still select Curated selection afterwards.
    if (controls.scope.value === "selected") controls.scope.value = "all";
    resetAndRender();
  };
  filterController = createCatalogueFilters({
    controls,
    options: filterOptions,
    toggle: filterToggle,
    panel: advancedFilters,
    activeFilters,
    count: filterCount,
    resetButton,
    onChange: resetAndRender,
    toggleLabel: "Filters",
    indexType: "media",
  });
  filterController.read();
  controls.search.addEventListener("input", debounce(startDiscovery));
  for (const control of [controls.category, controls.period, controls.rights]) control.addEventListener("change", startDiscovery);
  controls.scope.addEventListener("change", resetAndRender);
  resetButton.addEventListener("click", () => {
    controls.search.value = "";
    controls.category.value = "";
    controls.period.value = "";
    controls.rights.value = "";
    controls.scope.value = "selected";
    filterController.close();
    resetAndRender();
  });
  function revealFrom(firstNewIndex) {
    const firstNewCard = target.children[firstNewIndex];
    if (firstNewCard) {
      firstNewCard.setAttribute("tabindex", "-1");
      firstNewCard.focus({ preventScroll: true });
      firstNewCard.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
        block: "start",
      });
    }
  }
  more.addEventListener("click", () => {
    const firstNewIndex = Math.min(visible, current.length);
    visible += PAGE_SIZE;
    render();
    revealFrom(firstNewIndex);
  });
  showAll.addEventListener("click", () => {
    const firstNewIndex = Math.min(visible, current.length);
    showingAll = true;
    render();
    revealFrom(firstNewIndex);
  });
  render();
} catch (error) {
  if (!hasPrerenderedResults) {
    countTarget.textContent = "Media unavailable";
    renderError(target, error);
  }
}
