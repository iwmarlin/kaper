import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=c899f6ed5c";
import {
  compareText,
  debounce,
  escapeHtml,
  functionLabel,
  humanize,
  indexById,
  indexText,
  loadTables,
  mountSiteChrome,
  nameKey,
  normalizeSearch,
  periodBadge,
  periodLabel,
  periodValues,
  PERIOD_ORDER,
  personFunctions,
  PERSON_FUNCTION_ORDER,
  recordUrl,
  registerImageDerivatives,
  renderError,
  renderLoading,
  responsiveImage,
  typeBadge,
} from "./core.js?v=c899f6ed5c";

registerImageDerivatives(IMAGE_DERIVATIVES);
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

renderLoading(target, "Loading documented people…");

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
    const defaultValue = key === "sort" ? "name" : "";
    if (control.value && control.value !== defaultValue) params.set(key, control.value);
  }
  history.replaceState(null, "", params.toString() ? `?${params}` : location.pathname);
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

function initials(name = "") {
  const parts = String(name).trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  const first = [...parts[0]][0] || "";
  const last = parts.length > 1 ? [...parts[parts.length - 1]][0] || "" : "";
  return (first + last).toUpperCase();
}

try {
  const { people, works, media, sources, timelineEvents, contributions, personNameVariants } = await loadTables([
    "people",
    "works",
    "media",
    "sources",
    "timelineEvents",
    "contributions",
    "personNameVariants",
  ]);
  const worksById = indexById(works);
  const contributionsById = indexById(contributions);
  const nameVariantsByPersonId = new Map();
  for (const variant of personNameVariants) {
    for (const personId of variant.personIds || []) {
      const existing = nameVariantsByPersonId.get(personId) || [];
      existing.push(variant.variantName, variant.attestedWording);
      nameVariantsByPersonId.set(personId, existing);
    }
  }
  const mediaById = indexById(media);
  const sourcesById = indexById(sources);
  const eventsById = indexById(timelineEvents);

  // A person reaches a portrait indirectly, through the sources attached to
  // them, and a source can document several people at once: the photograph of
  // the Kiepura reception in Paris carries Kaper, his wife, Kiepura and Halicz.
  // Taking the first portrait found in any of a person's sources put one
  // sitter's face on three other people. A portrait is claimed only when its
  // slug is the person's own — the convention these records follow — or when
  // the source it comes from names this person and no one else.
  function portraitFor(person) {
    const reachable = [];
    for (const sourceId of person.sourceIds || []) {
      const source = sourcesById.get(sourceId);
      for (const mediaId of source?.mediaIds || []) {
        const item = mediaById.get(mediaId);
        if (item?.category === "portrait" && item.assetPath && IMAGE_DERIVATIVES[item.assetPath]) {
          reachable.push({ item, source });
        }
      }
    }
    const own = reachable.find(({ item }) => String(item.slug || "").startsWith(`${person.slug}-`));
    if (own) return own.item;
    const sole = reachable.find(({ source }) => (source?.personIds || []).length === 1
      && source.personIds[0] === person.id);
    return sole ? sole.item : null;
  }

  const indexed = people.map((person) => {
    const personWorks = (person.workIds || []).map((id) => worksById.get(id)).filter(Boolean);
    // Periods were read from linked works alone, so anyone documented only
    // through a dated event — a teacher, a family member, a producer Kaper
    // worked under rather than with — carried no badge at all. Linked timeline
    // events are dated and periodised on the same evidence, so they count too.
    const personEvents = (person.timelineEventIds || []).map((id) => eventsById.get(id)).filter(Boolean);
    const periodSet = new Set([
      ...personWorks.flatMap((work) => periodValues(work)),
      ...personEvents.flatMap((event) => periodValues(event)),
    ]);
    const periods = PERIOD_ORDER.filter((period) => periodSet.has(period));
    const roles = person.roles?.length ? person.roles : [person.primaryRole].filter(Boolean);
    const functions = personFunctions(person, contributionsById);
    // The names a person worked under are part of finding them: the archive
    // documents Kaper as Chwast, Jurmann as Bob Henders, Bernauer as Fred
    // Lustig, and a reader who knows only the pseudonym must arrive somewhere.
    const usedNames = (nameVariantsByPersonId.get(person.id) || []).filter(Boolean);
    return {
      ...person,
      _works: personWorks.length,
      _periods: periods,
      _roles: roles,
      _functions: functions,
      _portrait: portraitFor(person),
      _search: indexText([
        person.displayName,
        person.sortName,
        person.authorizedName,
        ...usedNames,
        ...roles,
        ...functions.map(functionLabel),
      ].filter(Boolean).join(" ")),
    };
  });

  if (totalLabelTarget) {
    totalLabelTarget.textContent = `${people.length} documented ${people.length === 1 ? "person" : "people"}`;
  }

  const availableFunctions = new Set(indexed.flatMap((person) => person._functions));
  addOptions(
    controls.role,
    PERSON_FUNCTION_ORDER.filter((value) => availableFunctions.has(value)),
    functionLabel,
    true,
  );
  const availablePeriods = new Set(indexed.flatMap((person) => person._periods));
  addOptions(controls.period, PERIOD_ORDER.filter((value) => availablePeriods.has(value)), periodLabel, true);
  loadQuery();

  function avatar(person) {
    if (person._portrait) {
      return responsiveImage(person._portrait.assetPath, person._portrait.altText || person.displayName, {
        className: "person-row__portrait",
        sizes: "4rem",
      });
    }
    return `<span class="person-row__monogram" aria-hidden="true">${escapeHtml(initials(person.displayName))}</span>`;
  }

  function render() {
    renderFilterChrome();
    const query = normalizeSearch(controls.search.value.trim());
    filtered = indexed.filter((person) => (
      (!query || person._search.includes(query))
      && (!controls.role.value || person._functions.includes(controls.role.value))
      && (!controls.period.value || person._periods.includes(controls.period.value))
    ));

    filtered.sort((a, b) => {
      const byName = compareText(nameKey(a), nameKey(b));
      // The counted quantity is the number of works a person is linked to,
      // which is what the option now says; sources, media and dated events are
      // not weighed, so the index files by name unless asked otherwise.
      if (controls.sort.value === "works-desc") return b._works - a._works || byName;
      if (controls.sort.value === "role") {
        const rank = (person) => PERSON_FUNCTION_ORDER.indexOf(person._functions[0] || "documented");
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
      syncQuery();
      return;
    }

    target.innerHTML = shown.map((person) => {
      return `
        <article class="person-row">
          <div class="person-row__avatar">${avatar(person)}</div>
          <div class="person-row__identity">
            <h2><a href="${recordUrl("person", person.id)}">${escapeHtml(person.displayName)}</a></h2>
            <div class="meta-row" aria-label="Documented roles">${person._roles.map(typeBadge).join("")}</div>
          </div>
          ${person._periods.length
            ? `<div class="person-row__period" aria-label="Documented periods">${periodBadge(person._periods)}</div>`
            : ""}
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
  for (const control of [controls.role, controls.period, controls.sort]) {
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
    controls.role.value = "";
    controls.period.value = "";
    controls.sort.value = "name";
    advancedFilters.classList.remove("filters__advanced--open");
    filterToggle.setAttribute("aria-expanded", "false");
    resetAndRender();
  });
  render();
} catch (error) {
  countTarget.textContent = "Index unavailable";
  renderError(target, error);
}
