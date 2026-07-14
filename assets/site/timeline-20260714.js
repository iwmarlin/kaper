import {
  debounce,
  escapeHtml,
  humanize,
  indexById,
  loadTables,
  mountSiteChrome,
  normalizeSearch,
  periodBadge,
  recordUrl,
  renderError,
  renderLoading,
  resolveIds,
  typeBadge,
} from "./core.js";

mountSiteChrome("timeline");

const target = document.querySelector("#timeline-results");
const countTarget = document.querySelector("#timeline-count");
const controls = {
  search: document.querySelector("#timeline-search"),
  period: document.querySelector("#timeline-period"),
  category: document.querySelector("#timeline-category"),
};
renderLoading(target, "Loading documented events…");

function addOptions(select, values) {
  for (const value of [...new Set(values.filter(Boolean))].sort()) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = humanize(value);
    select.append(option);
  }
}

try {
  const { timelineEvents, media, people } = await loadTables(["timelineEvents", "media", "people"]);
  const mediaById = indexById(media);
  const peopleById = indexById(people);
  addOptions(controls.period, timelineEvents.map((event) => event.period));
  addOptions(controls.category, timelineEvents.map((event) => event.category));

  const indexed = timelineEvents.map((event) => ({
    ...event,
    _search: normalizeSearch([
      event.title,
      event.displayDate,
      event.placeDisplay,
      event.shortDescription,
      event.longDescription,
      ...resolveIds(event, "personIds", peopleById).map((person) => person.displayName),
    ].filter(Boolean).join(" ")),
  }));

  function render() {
    const query = normalizeSearch(controls.search.value.trim());
    const filtered = indexed
      .filter((event) => (
        (!query || event._search.includes(query))
        && (!controls.period.value || event.period === controls.period.value)
        && (!controls.category.value || event.category === controls.category.value)
      ))
      .sort((a, b) => String(a.sortDate || a.dateStart).localeCompare(String(b.sortDate || b.dateStart)) || Number(a.sortOrder || 0) - Number(b.sortOrder || 0));

    countTarget.innerHTML = `<strong>${filtered.length}</strong> ${filtered.length === 1 ? "event" : "events"} shown`;
    if (!filtered.length) {
      target.innerHTML = `<div class="empty-state"><h2>No matching events</h2><p>Try a broader search or remove a filter.</p></div>`;
      return;
    }
    target.innerHTML = filtered.map((event) => {
      const hero = (event.heroMediaIds || []).map((id) => mediaById.get(id)).find((item) => item?.assetPath && item.mediaType !== "audio");
      return `
        <article class="timeline-item">
          <div class="timeline-item__date">${escapeHtml(event.displayDate || event.dateStart)}</div>
          <div class="timeline-item__body">
            <div class="meta-row">${typeBadge(event.category || event.eventType)}${periodBadge(event.period)}</div>
            <h2><a href="${recordUrl("event", event.id)}">${escapeHtml(event.title)}</a></h2>
            ${event.placeDisplay ? `<p class="timeline-item__place">${escapeHtml(event.placeDisplay)}</p>` : ""}
            ${hero ? `<img class="timeline-item__image" src="${escapeHtml(hero.assetPath)}" alt="${escapeHtml(hero.altText || hero.title)}" loading="lazy" decoding="async">` : ""}
            <p>${escapeHtml(event.shortDescription || event.longDescription || "")}</p>
          </div>
        </article>`;
    }).join("");
  }

  controls.search?.addEventListener("input", debounce(render));
  for (const control of [controls.period, controls.category].filter(Boolean)) control.addEventListener("change", render);
  document.querySelector("#timeline-reset")?.addEventListener("click", () => {
    for (const control of Object.values(controls).filter(Boolean)) control.value = "";
    render();
  });
  render();
} catch (error) {
  countTarget.textContent = "Timeline unavailable";
  renderError(target, error);
}
