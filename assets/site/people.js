import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=3188e7e598";
import {
  debounce,
  escapeHtml,
  humanize,
  indexById,
  loadTables,
  mountSiteChrome,
  normalizeSearch,
  PERIOD_ORDER,
  periodBadge,
  periodLabel,
  periodValues,
  recordUrl,
  registerImageDerivatives,
  renderError,
  renderLoading,
  responsiveImage,
  typeBadge,
} from "./core.js?v=3188e7e598";

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
    const defaultValue = key === "sort" ? "works-desc" : "";
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

function initials(name = "") {
  const parts = String(name).trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  const first = [...parts[0]][0] || "";
  const last = parts.length > 1 ? [...parts[parts.length - 1]][0] || "" : "";
  return (first + last).toUpperCase();
}

try {
  const { people, works, media, sources, contributions } = await loadTables([
    "people",
    "works",
    "media",
    "sources",
    "contributions",
  ]);
  const worksById = indexById(works);
  const mediaById = indexById(media);
  const sourcesById = indexById(sources);

  // Most person→source evidence hangs off contributions, not the person record:
  // only 93 of 119 people carry their own sourceIds, but all 119 are cited somewhere.
  const sourcesByPerson = new Map();
  for (const contribution of contributions) {
    for (const personId of contribution.personIds || []) {
      const bucket = sourcesByPerson.get(personId) || new Set();
      for (const sourceId of contribution.sourceIds || []) bucket.add(sourceId);
      sourcesByPerson.set(personId, bucket);
    }
  }

  // A person reaches a portrait indirectly: person → sources → media (category "portrait").
  function portraitFor(person) {
    for (const sourceId of person.sourceIds || []) {
      for (const mediaId of sourcesById.get(sourceId)?.mediaIds || []) {
        const item = mediaById.get(mediaId);
        if (item?.category === "portrait" && item.assetPath && IMAGE_DERIVATIVES[item.assetPath]) return item;
      }
    }
    return null;
  }

  const indexed = people.map((person) => {
    const personWorks = (person.workIds || []).map((id) => worksById.get(id)).filter(Boolean);
    const periods = [...new Set(personWorks.flatMap((work) => periodValues(work)))];
    const roles = person.roles?.length ? person.roles : [person.primaryRole].filter(Boolean);
    return {
      ...person,
      _works: personWorks.length,
      _sources: new Set([...(person.sourceIds || []), ...(sourcesByPerson.get(person.id) || [])]).size,
      _periods: periods,
      _roles: roles,
      _portrait: portraitFor(person),
      _search: normalizeSearch([
        person.displayName,
        person.sortName,
        person.authorizedName,
        ...roles,
      ].filter(Boolean).join(" ")),
    };
  });

  if (totalLabelTarget) {
    totalLabelTarget.textContent = `${people.length} documented ${people.length === 1 ? "person" : "people"}`;
  }

  addOptions(controls.role, indexed.flatMap((person) => person._roles));
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
    const query = normalizeSearch(controls.search.value.trim());
    filtered = indexed.filter((person) => (
      (!query || person._search.includes(query))
      && (!controls.role.value || person._roles.includes(controls.role.value))
      && (!controls.period.value || person._periods.includes(controls.period.value))
    ));

    filtered.sort((a, b) => {
      const byName = String(a.sortName || a.displayName).localeCompare(String(b.sortName || b.displayName), "pl");
      if (controls.sort.value === "name") return byName;
      if (controls.sort.value === "role") {
        return String(a.primaryRole || "").localeCompare(String(b.primaryRole || "")) || byName;
      }
      return b._works - a._works || byName;
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
      const tally = [
        person._works ? `${person._works} ${person._works === 1 ? "work" : "works"}` : "",
        person._sources ? `${person._sources} ${person._sources === 1 ? "source" : "sources"}` : "",
      ].filter(Boolean).join(" · ") || "Linked from records";
      return `
        <article class="person-row">
          <div class="person-row__avatar">${avatar(person)}</div>
          <div class="person-row__identity">
            <div class="meta-row">${person._roles.map(typeBadge).join("")}</div>
            <h2><a href="${recordUrl("person", person.id)}">${escapeHtml(person.displayName)}</a></h2>
          </div>
          <div class="person-row__count">${escapeHtml(tally)}</div>
          <div class="person-row__period">${periodBadge(person._periods)}</div>
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
    controls.sort.value = "works-desc";
    resetAndRender();
  });
  render();
} catch (error) {
  countTarget.textContent = "Index unavailable";
  renderError(target, error);
}
