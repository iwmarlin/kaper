import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=ddc6df159e";
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
} from "./core.js?v=ddc6df159e";

registerImageDerivatives(IMAGE_DERIVATIVES);
mountSiteChrome("timeline");

const target = document.querySelector("#timeline-results");
const countTarget = document.querySelector("#timeline-count");
const controls = {
  search: document.querySelector("#timeline-search"),
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

const CATEGORY_GROUPS = {
  birth_family: "life", family: "life", religion_identity: "life", military: "life", citizenship: "life",
  education: "education", law_studies: "education", music_education: "education",
  composition: "music", warsaw_music: "music", concert_life: "music", recording: "music",
  publication: "music", performance: "music", berlin: "music",
  film_career: "career", hollywood: "career", professional_network: "career",
  collaboration: "career", paris: "career", reception: "career",
  migration: "migration", refugee_support: "migration",
};
const GROUP_LABELS = {
  life: "Life & family",
  education: "Education",
  music: "Music & performance",
  career: "Film & career",
  migration: "Migration",
};
const GROUP_ORDER = ["life", "education", "music", "career", "migration"];

function eventGroup(event) {
  return CATEGORY_GROUPS[event.category] || (event.eventType === "life" ? "life" : "career");
}

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

const NAV_LABELS = { warsaw: "Warsaw", berlin: "Berlin", paris: "Paris", america: "America" };
const CHAPTER_ORDER = ["warsaw", "berlin", "paris", "america"];

function shortRange(range) {
  const match = String(range || "").match(/^(\d{4})\D+(\d{2})(\d{2})$/);
  return match ? `${match[1]}–${match[3]}` : range;
}

function navMarkup(chaptersPresent) {
  if (chaptersPresent.length < 2) return "";
  const tabs = chaptersPresent
    .map((key) => `<a class="timeline-nav__tab" href="#chapter-${key}" data-chapter="${key}"><span class="timeline-nav__era">${escapeHtml(NAV_LABELS[key])}</span><span class="timeline-nav__years">${escapeHtml(shortRange(TIMELINE_CHAPTERS[key].range))}</span></a>`)
    .join("");
  return `<nav class="timeline-nav" aria-label="Jump to era">${tabs}</nav>`;
}

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

function chapterMarkup(key) {
  const chapter = TIMELINE_CHAPTERS[key];
  return `
    <div class="timeline-chapter" id="chapter-${key}" aria-label="${escapeHtml(`${chapter.title}, ${chapter.range}`)}">
      <div class="timeline-chapter__inner">
        <p class="timeline-chapter__eyebrow"><span class="timeline-chapter__number">Chapter ${chapter.number}</span><span class="timeline-chapter__range">${escapeHtml(chapter.range)}</span></p>
        <h2>${escapeHtml(chapter.title)}</h2>
        <p class="timeline-chapter__summary">${escapeHtml(chapter.summary)}</p>
      </div>
    </div>`;
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
  const { timelineEvents, media, people, sources } = await loadTables(["timelineEvents", "media", "people", "sources"]);
  const mediaById = indexById(media);
  const peopleById = indexById(people);
  const sourcesById = indexById(sources);
  addOptions(
    controls.category,
    GROUP_ORDER.filter((key) => timelineEvents.some((event) => eventGroup(event) === key)),
    (key) => GROUP_LABELS[key],
    true,
  );

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
        && (!controls.category.value || eventGroup(event) === controls.category.value)
      ))
      .sort((a, b) => String(a.sortDate || a.dateStart).localeCompare(String(b.sortDate || b.dateStart)) || Number(a.sortOrder || 0) - Number(b.sortOrder || 0));

    countTarget.innerHTML = `<strong>${filtered.length}</strong> ${filtered.length === 1 ? "event" : "events"} shown`;
    if (!filtered.length) {
      target.innerHTML = `<div class="empty-state"><h2>No matching events</h2><p>Try a broader search or remove a filter.</p></div>`;
      return;
    }
    const chaptersPresent = CHAPTER_ORDER.filter((key) => filtered.some((event) => chapterForEvent(event) === key));
    let currentChapter = "";
    const timelineMarkup = [navMarkup(chaptersPresent)];
    for (const event of filtered) {
      const chapter = chapterForEvent(event);
      if (chapter !== currentChapter) {
        timelineMarkup.push(chapterMarkup(chapter));
        currentChapter = chapter;
      }
      const hero = (event.heroMediaIds || []).map((id) => mediaById.get(id)).find((item) => item?.assetPath && item.mediaType !== "audio");
      const heroProfile = hero ? IMAGE_DERIVATIVES[hero.assetPath] : null;
      const heroPortrait = Boolean(heroProfile && heroProfile.height > heroProfile.width);
      const heroSources = hero ? resolveIds(hero, "sourceIds", sourcesById) : [];
      const description = event.shortDescription || event.longDescription || "";
      const isMilestone = MILESTONE_EVENT_IDS.has(event.id);
      const rawDate = event.displayDate || event.dateStart || "";
      const isCompoundDate = rawDate.includes("/") || (rawDate.includes("\u2013") && /january|february|march|april|may|june|july|august|september|october|november|december/i.test(rawDate));
      const startYear = String(event.dateStart || "").slice(0, 4);
      const endYear = String(event.dateEnd || "").slice(0, 4);
      const railDate = isCompoundDate ? (endYear && endYear !== startYear ? `${startYear}\u2013${endYear}` : startYear) : rawDate;
      const fullDate = isCompoundDate ? rawDate.replace(/\s*\u2013\s*/g, " \u2013 ").replace(/\s*\/\s*/g, " / ") : "";
      timelineMarkup.push(`
        <article class="timeline-item${isMilestone ? " timeline-item--milestone" : ""}" id="event-${escapeHtml(event.id)}" data-event-id="${escapeHtml(event.id)}">
          <div class="timeline-item__date">${escapeHtml(railDate)}</div>
          <span class="timeline-item__node" aria-hidden="true"></span>
          <div class="timeline-item__body">
            ${isMilestone ? `<span class="timeline-item__kicker">Milestone</span>` : ""}
            <div class="meta-row"><span class="badge badge--type">${escapeHtml(GROUP_LABELS[eventGroup(event)])}</span>${periodBadge(event.periods || event.period)}</div>
            <h3><a href="${recordUrl("event", event.id)}">${escapeHtml(event.title)}</a></h3>
            ${fullDate ? `<p class="timeline-item__fulldate">${escapeHtml(fullDate)}</p>` : ""}
            ${event.placeDisplay ? `<p class="timeline-item__place">${escapeHtml(event.placeDisplay)}</p>` : ""}
            ${hero ? `<div class="timeline-item__media-row${heroPortrait ? " timeline-item__media-row--portrait" : ""}">
              <figure class="timeline-item__figure">
                ${responsiveImage(hero.assetPath, hero.altText || hero.title, {
                  className: "timeline-item__image",
                  sizes: "(max-width: 680px) calc(100vw - 3rem), (max-width: 1100px) 46vw, 24rem",
                })}
                <figcaption>${renderMediaDisclosure(hero, heroSources, {
                  compact: true,
                  fairUseResolutionLabel: "Low-resolution scholarly reproduction",
                  includeCaption: false,
                  includeCredit: false,
                  includeFullRightsNote: false,
                  includeRationale: false,
                })}</figcaption>
              </figure>
              ${description ? `<p>${escapeHtml(description)}</p>` : ""}
            </div>` : (description ? `<div class="timeline-item__note"><p>${escapeHtml(description)}</p></div>` : "")}
          </div>
        </article>`);
    }
    target.innerHTML = timelineMarkup.join("");
    updateActiveChapter();
  }

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

  controls.search?.addEventListener("input", debounce(render));
  for (const control of [controls.category].filter(Boolean)) control.addEventListener("change", render);
  document.querySelector("#timeline-reset")?.addEventListener("click", () => {
    for (const control of Object.values(controls).filter(Boolean)) control.value = "";
    render();
  });
  render();
} catch (error) {
  countTarget.textContent = "Timeline unavailable";
  renderError(target, error);
}
