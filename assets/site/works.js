import {
  certaintyBadge,
  compareText,
  debounce,
  escapeHtml,
  humanize,
  indexById,
  loadTables,
  matchesPeriod,
  mountSiteChrome,
  normalizeSearch,
  PERIOD_ORDER,
  periodBadge,
  periodLabel,
  periodValues,
  recordUrl,
  renderError,
  renderLoading,
  scopeBadge,
  sortKey,
  typeBadge,
  workSearchText,
} from "./core.js?v=3b5645e07c";

mountSiteChrome("works");

const controls = {
  search: document.querySelector("#work-search"),
  type: document.querySelector("#work-type"),
  period: document.querySelector("#work-period"),
  certainty: document.querySelector("#work-certainty"),
  sort: document.querySelector("#work-sort"),
};
const target = document.querySelector("#work-results");
const countTarget = document.querySelector("#work-results-count");
const loadMore = document.querySelector("#load-more");
const showAll = document.querySelector("#show-all");
const resetButton = document.querySelector("#reset-filters");
const filterToggle = document.querySelector("#work-filter-toggle");
const advancedFilters = document.querySelector("#work-filter-options");
const activeFilters = document.querySelector("#work-active-filters");
const filterCount = document.querySelector("#work-filter-count");
const filterOptions = [
  { key: "type", label: "Type", defaultValue: "" },
  { key: "period", label: "Period", defaultValue: "" },
  { key: "certainty", label: "Certainty", defaultValue: "" },
  { key: "sort", label: "Sort", defaultValue: "year-asc" },
];
const PAGE_SIZE = 36;
let visibleCount = PAGE_SIZE;
let showingAll = false;
let filtered = [];

renderLoading(target, "Loading the catalogue…");

function addOptions(select, values, labeler = humanize, preserveOrder = false) {
  const uniqueValues = [...new Set(values.filter(Boolean))];
  for (const value of preserveOrder ? uniqueValues : uniqueValues.sort()) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = labeler(value);
    select.append(option);
  }
}

function syncQuery() {
  const params = new URLSearchParams();
  for (const [key, control] of Object.entries(controls)) {
    const defaultValue = key === "sort" ? "year-asc" : "";
    if (control.value && control.value !== defaultValue) params.set(key, control.value);
  }
  const suffix = params.toString() ? `?${params}` : location.pathname;
  history.replaceState(null, "", suffix);
}

function loadQuery() {
  const params = new URLSearchParams(location.search);
  for (const [key, control] of Object.entries(controls)) {
    if (params.has(key)) control.value = params.get(key);
  }
}

function selectedOptionLabel(control) {
  return control.options[control.selectedIndex]?.textContent?.trim() || control.value;
}

function renderFilterChrome() {
  const selected = filterOptions.filter(({ key, defaultValue }) => controls[key].value !== defaultValue);
  const hasSearch = Boolean(controls.search.value.trim());

  filterCount.textContent = String(selected.length);
  filterCount.hidden = selected.length === 0;
  filterToggle.setAttribute(
    "aria-label",
    selected.length ? `Filters and sort, ${selected.length} active` : "Filters and sort",
  );
  resetButton.hidden = !hasSearch && selected.length === 0;

  activeFilters.hidden = selected.length === 0;
  activeFilters.innerHTML = selected.map(({ key, label }) => `
    <button class="active-filter" type="button" data-filter-key="${escapeHtml(key)}"
      aria-label="Remove ${escapeHtml(label)} filter: ${escapeHtml(selectedOptionLabel(controls[key]))}">
      <span>${escapeHtml(label)}: ${escapeHtml(selectedOptionLabel(controls[key]))}</span>
      <span class="active-filter__remove" aria-hidden="true">×</span>
    </button>`).join("");
}

try {
  const { works, people, films, songs, otherWorks, contributions, titleVariants } = await loadTables([
    "works",
    "people",
    "films",
    "songs",
    "otherWorks",
    "contributions",
    "titleVariants",
  ]);
  const peopleById = indexById(people);
  const contributionsById = indexById(contributions);
  const titleVariantsById = indexById(titleVariants);
  const subtypeByWorkId = new Map();
  for (const subtype of [...films, ...songs, ...otherWorks]) {
    for (const workId of subtype.workIds || []) subtypeByWorkId.set(workId, subtype);
  }

  addOptions(controls.type, works.map((work) => work.workType));
  const availablePeriods = new Set(works.flatMap(periodValues));
  addOptions(controls.period, PERIOD_ORDER.filter((value) => availablePeriods.has(value)), periodLabel, true);
  addOptions(controls.certainty, works.map((work) => work.certainty));
  loadQuery();

  const searchLookup = { peopleById, subtypeByWorkId, contributionsById, titleVariantsById };

  const indexedWorks = works.map((work) => ({ ...work, _search: workSearchText(work, searchLookup) }));

  function render() {
    renderFilterChrome();
    const query = normalizeSearch(controls.search.value.trim());
    filtered = indexedWorks.filter((work) => (
      (!query || work._search.includes(query))
      && (!controls.type.value || work.workType === controls.type.value)
      && matchesPeriod(work, controls.period.value)
      && (!controls.certainty.value || work.certainty === controls.certainty.value)
    ));

    filtered.sort((a, b) => {
      const byTitle = compareText(sortKey(a), sortKey(b));
      if (controls.sort.value === "title") return byTitle;
      const yearDifference = Number(a.year || 9999) - Number(b.year || 9999);
      return controls.sort.value === "year-desc" ? -yearDifference || byTitle : yearDifference || byTitle;
    });

    const shown = filtered.slice(0, showingAll ? filtered.length : visibleCount);
    countTarget.innerHTML = `<strong>Showing ${shown.length}</strong> of ${filtered.length} ${filtered.length === 1 ? "record" : "records"}`;
    const remaining = filtered.length - shown.length;
    loadMore.hidden = remaining <= 0;
    showAll.hidden = remaining <= 0;
    if (remaining > 0) {
      const nextCount = Math.min(PAGE_SIZE, remaining);
      loadMore.textContent = `Load ${nextCount} more`;
      loadMore.setAttribute("aria-label", `Load ${nextCount} more records`);
      showAll.textContent = `Show all ${filtered.length}`;
      showAll.setAttribute("aria-label", `Show all ${filtered.length} records`);
    }
    if (!shown.length) {
      target.innerHTML = `<div class="empty-state"><h2>No matching works</h2><p>Try removing a filter or using a broader search term.</p></div>`;
      syncQuery();
      return;
    }

    target.innerHTML = shown.map((work) => {
      const qualificationBadges = [
        work.publicScope === "context_only" ? scopeBadge(work.publicScope) : "",
        work.certainty && work.certainty !== "confirmed" ? certaintyBadge(work.certainty) : "",
      ].join("");
      return `
        <article class="work-row">
          <div class="work-row__year">${escapeHtml(work.year || "—")}</div>
          <div class="work-row__identity">
            <h2><a href="${recordUrl("work", work.id)}">${escapeHtml(work.title)}</a></h2>
            <div class="meta-row" aria-label="Work classification">${typeBadge(work.workType)}${qualificationBadges}</div>
          </div>
          <div class="work-row__period">${periodBadge(work.periods || work.period)}</div>
        </article>`;
    }).join("");
    syncQuery();
  }

  const resetAndRender = () => {
    visibleCount = PAGE_SIZE;
    showingAll = false;
    render();
  };
  controls.search.addEventListener("input", debounce(resetAndRender));
  for (const control of [controls.type, controls.period, controls.certainty, controls.sort]) {
    control.addEventListener("change", resetAndRender);
  }
  filterToggle.addEventListener("click", () => {
    const open = !advancedFilters.classList.contains("filters__advanced--open");
    advancedFilters.classList.toggle("filters__advanced--open", open);
    filterToggle.setAttribute("aria-expanded", String(open));
  });
  activeFilters.addEventListener("click", (event) => {
    const chip = event.target.closest("[data-filter-key]");
    if (!chip || !activeFilters.contains(chip)) return;
    const option = filterOptions.find(({ key }) => key === chip.dataset.filterKey);
    if (!option) return;
    controls[option.key].value = option.defaultValue;
    resetAndRender();
    // The chip has just been removed from the document, so focus would fall to
    // the body. Return it to the control the reader was working with: the
    // toggle when the panel is collapsed, otherwise the select itself.
    const fallback = filterToggle.offsetParent ? filterToggle : controls[option.key];
    fallback.focus({ preventScroll: true });
  });
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
    controls.type.value = "";
    controls.period.value = "";
    controls.certainty.value = "";
    controls.sort.value = "year-asc";
    advancedFilters.classList.remove("filters__advanced--open");
    filterToggle.setAttribute("aria-expanded", "false");
    resetAndRender();
  });
  render();
} catch (error) {
  countTarget.textContent = "Catalogue unavailable";
  renderError(target, error);
}
