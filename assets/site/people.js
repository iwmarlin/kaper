import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=c77ada42a0";
import {
  compareText,
  debounce,
  functionLabel,
  humanize,
  indexText,
  loadSiteIndex,
  mountSiteChrome,
  nameKey,
  normalizeSearch,
  periodLabel,
  PERIOD_ORDER,
  PERSON_FUNCTION_ORDER,
  renderError,
} from "./core.js?v=c77ada42a0";
import { createCatalogueFilters } from "./catalogue-filters.js?v=c77ada42a0";
import {
  registerCatalogueImageDerivatives,
  renderPersonIndexRow,
} from "./catalogue-results.js?v=c77ada42a0";

registerCatalogueImageDerivatives(IMAGE_DERIVATIVES);
mountSiteChrome("people");

const controls = {
  search: document.querySelector("#person-search"),
  role: document.querySelector("#person-role"),
  period: document.querySelector("#person-period"),
  sort: document.querySelector("#person-sort"),
};
const target = document.querySelector("#person-results");
const countTarget = document.querySelector("#person-results-count");
const loadMore = document.querySelector("#load-more");
const showAll = document.querySelector("#show-all");
const resetButton = document.querySelector("#reset-filters");
const totalLabelTarget = document.querySelector("#person-total-label");
const filterToggle = document.querySelector("#person-filter-toggle");
const advancedFilters = document.querySelector("#person-filter-options");
const activeFilters = document.querySelector("#person-active-filters");
const filterCount = document.querySelector("#person-filter-count");
const filterOptions = [
  { key: "role", label: "Function", defaultValue: "" },
  { key: "period", label: "Period", defaultValue: "" },
  { key: "sort", label: "Sort", defaultValue: "name" },
];
const PAGE_SIZE = 48;
let visibleCount = PAGE_SIZE;
let showingAll = false;
let filtered = [];

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
  const { records: people } = await loadSiteIndex("people");
  const indexed = people.map((person) => ({
    ...person,
    _search: indexText([person.displayName, person.searchSupplement].filter(Boolean).join(" ")),
  }));

  if (totalLabelTarget) {
    totalLabelTarget.textContent = `${people.length} documented ${people.length === 1 ? "person" : "people"}`;
  }

  const availableFunctions = new Set(indexed.flatMap((person) => person.functions));
  addOptions(
    controls.role,
    PERSON_FUNCTION_ORDER.filter((value) => availableFunctions.has(value)),
    functionLabel,
    true,
  );
  const availablePeriods = new Set(indexed.flatMap((person) => person.periods));
  addOptions(controls.period, PERIOD_ORDER.filter((value) => availablePeriods.has(value)), periodLabel, true);
  let filterController;

  function render() {
    filterController.update();
    const query = normalizeSearch(controls.search.value.trim());
    filtered = indexed.filter((person) => (
      (!query || person._search.includes(query))
      && (!controls.role.value || person.functions.includes(controls.role.value))
      && (!controls.period.value || person.periods.includes(controls.period.value))
    ));

    filtered.sort((a, b) => {
      const byName = compareText(nameKey(a), nameKey(b));
      // The counted quantity is the number of works a person is linked to,
      // which is what the option now says; sources, media and dated events are
      // not weighed, so the index files by name unless asked otherwise.
      if (controls.sort.value === "works-desc") return b.workCount - a.workCount || byName;
      if (controls.sort.value === "role") {
        const rank = (person) => PERSON_FUNCTION_ORDER.indexOf(person.functions[0] || "documented");
        return rank(a) - rank(b) || byName;
      }
      return byName;
    });

    const shown = filtered.slice(0, showingAll ? filtered.length : visibleCount);
    countTarget.innerHTML = `<strong>Showing ${shown.length}</strong> of ${filtered.length} ${filtered.length === 1 ? "person" : "people"}`;
    const remaining = filtered.length - shown.length;
    loadMore.hidden = remaining <= 0;
    showAll.hidden = remaining <= 0;
    if (remaining > 0) {
      const nextCount = Math.min(PAGE_SIZE, remaining);
      loadMore.textContent = `Load ${nextCount} more`;
      loadMore.setAttribute("aria-label", `Load ${nextCount} more people`);
      showAll.textContent = `Show all ${filtered.length}`;
      showAll.setAttribute("aria-label", `Show all ${filtered.length} people`);
    }
    if (!shown.length) {
      target.innerHTML = `<div class="empty-state"><h2>No matching people</h2><p>Try removing a filter or using a broader search term.</p></div>`;
      filterController.write();
      return;
    }

    target.innerHTML = shown.map(renderPersonIndexRow).join("");
    target.dataset.prerendered = "false";
    filterController.write();
  }

  function resetAndRender() {
    visibleCount = PAGE_SIZE;
    showingAll = false;
    render();
  }
  filterController = createCatalogueFilters({
    controls,
    options: filterOptions,
    toggle: filterToggle,
    panel: advancedFilters,
    activeFilters,
    count: filterCount,
    resetButton,
    onChange: resetAndRender,
    indexType: "person",
  });
  filterController.read();
  controls.search.addEventListener("input", debounce(resetAndRender));
  for (const control of [controls.role, controls.period, controls.sort]) {
    control.addEventListener("change", resetAndRender);
  }
  function revealFrom(firstNewIndex) {
    const firstNewRecord = target.children[firstNewIndex];
    if (firstNewRecord) {
      firstNewRecord.setAttribute("tabindex", "-1");
      firstNewRecord.focus({ preventScroll: true });
      firstNewRecord.scrollIntoView({
        behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
        block: "start",
      });
    }
  }
  loadMore.addEventListener("click", () => {
    const firstNewIndex = Math.min(visibleCount, filtered.length);
    visibleCount += PAGE_SIZE;
    render();
    revealFrom(firstNewIndex);
  });
  showAll.addEventListener("click", () => {
    const firstNewIndex = Math.min(visibleCount, filtered.length);
    showingAll = true;
    render();
    revealFrom(firstNewIndex);
  });
  resetButton.addEventListener("click", () => {
    controls.search.value = "";
    controls.role.value = "";
    controls.period.value = "";
    controls.sort.value = "name";
    filterController.close();
    resetAndRender();
  });
  render();
} catch (error) {
  if (!hasPrerenderedResults) {
    countTarget.textContent = "Index unavailable";
    renderError(target, error);
  }
}
