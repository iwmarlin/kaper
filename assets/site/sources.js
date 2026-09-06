import {
  compareText,
  debounce,
  escapeHtml,
  formatDate,
  humanize,
  indexText,
  loadTables,
  mountSiteChrome,
  normalizeSearch,
  recordUrl,
  renderError,
  renderLoading,
  safeExternalUrl,
} from "./core.js?v=c77ada42a0";
import { createCatalogueFilters } from "./catalogue-filters.js?v=c77ada42a0";

// This page is intentionally not part of NAV_ITEMS yet. It can be reviewed as
// a direct route without changing the site's established primary pathways.
mountSiteChrome("sources");

const SOURCE_TYPE_LABELS = Object.freeze({
  archival_digital_record: "Archival digital record",
  archival_document: "Archival document",
  archival_manuscript_holding: "Archival manuscript holding",
  archival_photograph: "Archival photograph",
  authority_record: "Authority record",
  book: "Book",
  copyright_catalogue: "Copyright catalogue",
  digital_collection_item: "Digital collection item",
  filmographic_database: "Filmographic database",
  image_or_photograph: "Image or photograph",
  online_audio_source: "Online audio",
  online_database: "Online database",
  online_video_source: "Online video",
  periodical_article: "Periodical article",
  press_item: "Press item",
  recording_discographic_source: "Recording or discographic source",
  secondary_literature: "Secondary literature",
  sheet_music: "Sheet music",
  sheet_music_catalogue: "Sheet-music catalogue",
  sound_recording_catalogue: "Sound-recording catalogue",
  soundtrack_database: "Soundtrack database",
  visual_document: "Visual document",
  web_page: "Web page",
  wikimedia_article_page: "Wikipedia article",
  wikimedia_commons_file: "Wikimedia Commons file",
});

const DATE_ROLE_LABELS = Object.freeze({
  catalogue_volume: "Catalogue volume",
  creation: "Creation of the object",
  data_currency: "Currency of the data",
  described_item: "Described item",
  digital_publication: "Digital publication",
  digitization: "Digitization",
  issue: "Issue or edition",
  publication: "Publication",
  record_creation: "Catalogue-record creation",
  record_update: "Catalogue-record update",
  recording: "Recording",
});

const controls = {
  search: document.querySelector("#source-search"),
  type: document.querySelector("#source-type"),
  dateRole: document.querySelector("#source-date-role"),
  access: document.querySelector("#source-access"),
  sort: document.querySelector("#source-sort"),
};
const target = document.querySelector("#source-results");
const countTarget = document.querySelector("#source-results-count");
const totalLabelTarget = document.querySelector("#source-total-label");
const loadMore = document.querySelector("#source-more");
const showAll = document.querySelector("#source-show-all");
const resetButton = document.querySelector("#source-reset");
const filterToggle = document.querySelector("#source-filter-toggle");
const advancedFilters = document.querySelector("#source-filter-options");
const activeFilters = document.querySelector("#source-active-filters");
const filterCount = document.querySelector("#source-filter-count");
const filterOptions = [
  { key: "type", label: "Type", defaultValue: "" },
  { key: "dateRole", label: "Date represents", defaultValue: "" },
  { key: "access", label: "Access", defaultValue: "" },
  { key: "sort", label: "Sort", defaultValue: "date-asc" },
];
const PAGE_SIZE = 40;
let visibleCount = PAGE_SIZE;
let showingAll = false;
let filtered = [];

renderLoading(target, "Loading source records…");

function sourceTypeLabel(value) {
  return SOURCE_TYPE_LABELS[value] || humanize(value || "Other source");
}

function dateRoleLabel(value) {
  return DATE_ROLE_LABELS[value] || humanize(value || "Unknown date role");
}

function sourceDateDisplay(source) {
  if (source.dateDisplay) return source.dateDisplay;
  const qualifier = source.dateQualifier || "confirmed";
  if (qualifier === "unknown") return "n.d.";
  if (qualifier === "forthcoming" && !source.date) return "forthcoming";
  if (!source.date) return "n.d.";
  const start = formatDate(source.date);
  const end = source.dateEnd ? formatDate(source.dateEnd) : "";
  const range = end && end !== start ? `${start}–${end}` : start;
  const prefix = {
    after: "after ",
    approximate: "c. ",
    before: "before ",
    not_before: "not before ",
  }[qualifier] || "";
  if (qualifier === "forthcoming") return `${range} (forthcoming)`;
  if (qualifier === "reported") return `${range} (reported)`;
  if (qualifier === "uncertain") return `${range}?`;
  return `${prefix}${range}`;
}

function sourceYear(source) {
  const match = String(source.date || "").match(/^(\d{4})(?:-|$)/);
  return match ? Number(match[1]) : null;
}

function sourceTitle(source) {
  return source.title || source.shortCitation || source.fullCitation || source.id;
}

function addCountedOptions(select, values, labeler) {
  const counts = new Map();
  for (const value of values.filter(Boolean)) counts.set(value, (counts.get(value) || 0) + 1);
  const entries = [...counts.entries()].sort((a, b) => compareText(labeler(a[0]), labeler(b[0])));
  for (const [value, count] of entries) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = `${labeler(value)} (${count})`;
    select.append(option);
  }
}

function typeMark(source) {
  return `<span class="badge badge--type">${escapeHtml(sourceTypeLabel(source.sourceType))}</span>`;
}

try {
  const { sources } = await loadTables(["sources"]);
  addCountedOptions(controls.type, sources.map((source) => source.sourceType), sourceTypeLabel);
  addCountedOptions(controls.dateRole, sources.map((source) => source.dateRole), dateRoleLabel);
  const indexed = sources.map((source) => {
    const external = safeExternalUrl(source.primaryUrl) || safeExternalUrl(source.accessUrl);
    const identifiers = (source.identifiers || []).flatMap((identifier) => [identifier.scheme, identifier.value]);
    return {
      ...source,
      _external: external,
      _year: sourceYear(source),
      _search: indexText([
        source.id,
        source.title,
        source.shortCitation,
        source.fullCitation,
        source.creator,
        source.publication,
        source.repository,
        source.sourceType,
        sourceTypeLabel(source.sourceType),
        source.date,
        source.dateDisplay,
        dateRoleLabel(source.dateRole),
        ...identifiers,
      ].filter(Boolean).join(" ")),
    };
  });

  totalLabelTarget.textContent = `${sources.length} documented ${sources.length === 1 ? "source" : "sources"}`;
  let filterController;

  function render() {
    filterController.update();
    const query = normalizeSearch(controls.search.value.trim());
    filtered = indexed.filter((source) => (
      (!query || source._search.includes(query))
      && (!controls.type.value || source.sourceType === controls.type.value)
      && (!controls.dateRole.value || source.dateRole === controls.dateRole.value)
      && (!controls.access.value
        || (controls.access.value === "online" ? Boolean(source._external) : !source._external))
    ));

    filtered.sort((a, b) => {
      const byTitle = compareText(sourceTitle(a), sourceTitle(b));
      const byId = compareText(a.id, b.id);
      if (controls.sort.value === "title") return byTitle || byId;
      if (controls.sort.value === "type") {
        return compareText(sourceTypeLabel(a.sourceType), sourceTypeLabel(b.sourceType)) || byTitle || byId;
      }
      if (controls.sort.value === "id") return byId;
      const yearA = a._year ?? Number.POSITIVE_INFINITY;
      const yearB = b._year ?? Number.POSITIVE_INFINITY;
      if (controls.sort.value === "date-desc") {
        const descA = a._year ?? Number.NEGATIVE_INFINITY;
        const descB = b._year ?? Number.NEGATIVE_INFINITY;
        return descB - descA || byTitle || byId;
      }
      return yearA - yearB || byTitle || byId;
    });

    const shown = filtered.slice(0, showingAll ? filtered.length : visibleCount);
    countTarget.innerHTML = `<strong>Showing ${shown.length}</strong> of ${filtered.length} ${filtered.length === 1 ? "source" : "sources"}`;
    const remaining = filtered.length - shown.length;
    loadMore.hidden = remaining <= 0;
    showAll.hidden = remaining <= 0;
    if (remaining > 0) {
      const nextCount = Math.min(PAGE_SIZE, remaining);
      loadMore.textContent = `Load ${nextCount} more`;
      loadMore.setAttribute("aria-label", `Load ${nextCount} more sources`);
      showAll.textContent = `Show all ${filtered.length}`;
      showAll.setAttribute("aria-label", `Show all ${filtered.length} sources`);
    }

    if (!shown.length) {
      target.innerHTML = `<div class="empty-state"><h2>No matching sources</h2><p>Try removing a filter or using a broader search term.</p></div>`;
      filterController.write();
      return;
    }

    target.innerHTML = shown.map((source) => `
      <article class="source-index-row">
        <div class="source-index-row__rail">
          <span class="source-index-row__id">${escapeHtml(source.id)}</span>
          <span class="source-index-row__date">${escapeHtml(sourceDateDisplay(source))}</span>
        </div>
        <div class="source-index-row__identity">
          <h2><a href="${recordUrl("source", source.id)}">${escapeHtml(sourceTitle(source))}</a></h2>
          <p class="source-index-row__citation">${escapeHtml(source.fullCitation || source.shortCitation || "")}</p>
        </div>
        <div class="source-index-row__context">
          ${typeMark(source)}
          ${source.repository ? `<span class="source-index-row__repository">${escapeHtml(source.repository)}</span>` : ""}
          ${source._external ? `<a href="${escapeHtml(source._external)}" target="_blank" rel="noreferrer">Open source <span aria-hidden="true">↗</span></a>` : ""}
        </div>
      </article>`).join("");
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
    indexType: "source",
  });
  filterController.read();
  controls.search.addEventListener("input", debounce(resetAndRender));
  for (const control of [controls.type, controls.dateRole, controls.access, controls.sort]) {
    control.addEventListener("change", resetAndRender);
  }
  function revealFrom(firstNewIndex) {
    const firstNewRecord = target.children[firstNewIndex];
    if (!firstNewRecord) return;
    firstNewRecord.setAttribute("tabindex", "-1");
    firstNewRecord.focus({ preventScroll: true });
    firstNewRecord.scrollIntoView({
      behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
      block: "start",
    });
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
    controls.dateRole.value = "";
    controls.access.value = "";
    controls.sort.value = "date-asc";
    filterController.close();
    resetAndRender();
  });

  render();
} catch (error) {
  countTarget.textContent = "Source index unavailable";
  totalLabelTarget.textContent = "Source data unavailable";
  renderError(target, error);
}
