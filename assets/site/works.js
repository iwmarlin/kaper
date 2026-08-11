import {
  certaintyBadge,
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
  resolveIds,
  scopeBadge,
  typeBadge,
} from "./core.js?v=a653d92b88";

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

try {
  const { works, people, films, songs, otherWorks } = await loadTables([
    "works",
    "people",
    "films",
    "songs",
    "otherWorks",
  ]);
  const peopleById = indexById(people);
  const subtypeByWorkId = new Map();
  for (const subtype of [...films, ...songs, ...otherWorks]) {
    for (const workId of subtype.workIds || []) subtypeByWorkId.set(workId, subtype);
  }

  addOptions(controls.type, works.map((work) => work.workType));
  const availablePeriods = new Set(works.flatMap(periodValues));
  addOptions(controls.period, PERIOD_ORDER.filter((value) => availablePeriods.has(value)), periodLabel, true);
  addOptions(controls.certainty, works.map((work) => work.certainty));
  loadQuery();

  function searchableWork(work) {
    const contributors = resolveIds(work, "personIds", peopleById).map((person) => person.displayName).join(" ");
    const subtype = subtypeByWorkId.get(work.id) || {};
    return normalizeSearch([
      work.title,
      work.sortTitle,
      work.year,
      work.workType,
      ...periodValues(work),
      contributors,
      subtype.genre,
      subtype.lyricistAsPrinted,
      subtype.publisherAsPrinted,
    ].filter(Boolean).join(" "));
  }

  const indexedWorks = works.map((work) => ({ ...work, _search: searchableWork(work) }));

  function render() {
    const query = normalizeSearch(controls.search.value.trim());
    filtered = indexedWorks.filter((work) => (
      (!query || work._search.includes(query))
      && (!controls.type.value || work.workType === controls.type.value)
      && matchesPeriod(work, controls.period.value)
      && (!controls.certainty.value || work.certainty === controls.certainty.value)
    ));

    filtered.sort((a, b) => {
      if (controls.sort.value === "title") return String(a.sortTitle || a.title).localeCompare(String(b.sortTitle || b.title), "en");
      const yearDifference = Number(a.year || 9999) - Number(b.year || 9999);
      return controls.sort.value === "year-desc" ? -yearDifference : yearDifference || String(a.title).localeCompare(String(b.title));
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
    resetAndRender();
  });
  render();
} catch (error) {
  countTarget.textContent = "Catalogue unavailable";
  renderError(target, error);
}
