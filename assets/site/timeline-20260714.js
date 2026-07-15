import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=20260715-1";
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
  registerImageDerivatives,
  renderMediaDisclosure,
  renderError,
  renderLoading,
  resolveIds,
  responsiveImage,
  typeBadge,
} from "./core.js?v=20260715-5";

registerImageDerivatives(IMAGE_DERIVATIVES);
mountSiteChrome("timeline");

const target = document.querySelector("#timeline-results");
const countTarget = document.querySelector("#timeline-count");
const controls = {
  search: document.querySelector("#timeline-search"),
  period: document.querySelector("#timeline-period"),
  category: document.querySelector("#timeline-category"),
};
renderLoading(target, "Loading documented events…");

const MILESTONE_EVENT_IDS = new Set([
  "TE0001",
  "TE0013",
  "TE0015",
  "TE0019",
  "TE0049",
  "TE0026",
  "TE0028",
  "TE0052",
  "TE0035",
  "TE0037",
]);

const TIMELINE_CHAPTERS = {
  warsaw: {
    number: "01",
    title: "Warsaw years",
    range: "1902–1926",
    summary: "Formation · law studies · first compositions and songs",
  },
  berlin: {
    number: "02",
    title: "Berlin years",
    range: "1926–1933",
    summary: "Concert networks · recordings · the turn towards film",
  },
  paris: {
    number: "03",
    title: "Paris years",
    range: "1933–1934",
    summary: "French cinema · migration · the route to MGM",
  },
  america: {
    number: "04",
    title: "America and MGM",
    range: "1934–1939",
    summary: "Arrival · Hollywood · continuing transatlantic networks",
  },
};

function chapterForEvent(event) {
  const date = String(event.sortDate || event.dateStart || "");
  if (event.id === "TE0014" || date < "1926-07-01") return "warsaw";
  if (date < "1933-07-01") return "berlin";
  if (date < "1934-10-24") return "paris";
  return "america";
}

function chapterMarkup(key) {
  const chapter = TIMELINE_CHAPTERS[key];
  return `
    <div class="timeline-chapter" aria-label="${escapeHtml(`${chapter.title}, ${chapter.range}`)}">
      <div class="timeline-chapter__inner">
        <span class="timeline-chapter__number">Chapter ${chapter.number}</span>
        <h2>${escapeHtml(chapter.title)}</h2>
        <p class="timeline-chapter__range">${escapeHtml(chapter.range)}</p>
        <p class="timeline-chapter__summary">${escapeHtml(chapter.summary)}</p>
      </div>
    </div>`;
}

function addOptions(select, values) {
  for (const value of [...new Set(values.filter(Boolean))].sort()) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = humanize(value);
    select.append(option);
  }
}

try {
  const { timelineEvents, media, people, sources } = await loadTables(["timelineEvents", "media", "people", "sources"]);
  const mediaById = indexById(media);
  const peopleById = indexById(people);
  const sourcesById = indexById(sources);
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
    let currentChapter = "";
    let ordinaryEventIndex = 0;
    const timelineMarkup = [];
    for (const event of filtered) {
      const chapter = chapterForEvent(event);
      if (chapter !== currentChapter) {
        timelineMarkup.push(chapterMarkup(chapter));
        currentChapter = chapter;
        ordinaryEventIndex = 0;
      }
      const hero = (event.heroMediaIds || []).map((id) => mediaById.get(id)).find((item) => item?.assetPath && item.mediaType !== "audio");
      const heroSources = hero ? resolveIds(hero, "sourceIds", sourcesById) : [];
      const description = event.shortDescription || event.longDescription || "";
      const isMilestone = MILESTONE_EVENT_IDS.has(event.id);
      const side = ordinaryEventIndex % 2 === 0 ? "left" : "right";
      if (!isMilestone) ordinaryEventIndex += 1;
      timelineMarkup.push(`
        <article class="timeline-item timeline-item--${isMilestone ? "milestone" : side}" data-event-id="${escapeHtml(event.id)}">
          <span class="timeline-item__node" aria-hidden="true"></span>
          <div class="timeline-item__body">
            <div class="timeline-item__topline">
              ${isMilestone ? `<span class="timeline-item__kicker">Milestone</span>` : ""}
              <div class="timeline-item__date">${escapeHtml(event.displayDate || event.dateStart)}</div>
            </div>
            <div class="meta-row">${typeBadge(event.category || event.eventType)}${periodBadge(event.period)}</div>
            <h3><a href="${recordUrl("event", event.id)}">${escapeHtml(event.title)}</a></h3>
            ${event.placeDisplay ? `<p class="timeline-item__place">${escapeHtml(event.placeDisplay)}</p>` : ""}
            ${hero ? `<div class="timeline-item__media-row">
              <figure class="timeline-item__figure">
                ${responsiveImage(hero.assetPath, hero.altText || hero.title, {
                  className: "timeline-item__image",
                  sizes: "(max-width: 680px) calc(100vw - 4rem), (max-width: 1100px) 42vw, 28rem",
                })}
                <figcaption>${renderMediaDisclosure(hero, heroSources, { compact: true })}</figcaption>
              </figure>
              ${description ? `<p>${escapeHtml(description)}</p>` : ""}
            </div>` : (description ? `<p>${escapeHtml(description)}</p>` : "")}
          </div>
        </article>`);
    }
    target.innerHTML = timelineMarkup.join("");
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
