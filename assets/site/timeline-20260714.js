import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=32394ba84e";
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
} from "./core.js?v=32394ba84e";

registerImageDerivatives(IMAGE_DERIVATIVES);
mountSiteChrome("timeline");

const target = document.querySelector("#timeline-results");
const countTarget = document.querySelector("#timeline-count");
const totalLabelTarget = document.querySelector("#timeline-total-label");
const controls = {
  search: document.querySelector("#timeline-search"),
  category: document.querySelector("#timeline-category"),
};
const viewControls = {
  highlights: document.querySelector("#timeline-view-highlights"),
  all: document.querySelector("#timeline-view-all"),
};
renderLoading(target, "Loading documented events…");

const MILESTONE_EVENT_IDS = new Set([
  "TE0001",
  "TE0004",
  "TE0013",
  "TE0015",
  "TE0019",
  "TE0049",
  "TE0026",
  "TE0028",
  "TE0052",
  "TE0035",
  "TE0053",
  "TE0037",
  "TE0038",
  "TE0041",
  "TE0043",
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
    title: "Warsaw · formation",
    range: "1902–1926",
    summary: "Formation · law studies · first compositions and songs",
  },
  european: {
    number: "02",
    title: "European career",
    range: "1926–1934",
    summary: "Berlin and Paris · recordings · cinema · the route to MGM",
  },
  hollywood: {
    number: "03",
    title: "Hollywood",
    range: "1935–1939",
    summary: "MGM · American film and song · continuing European networks",
  },
};

function chapterForEvent(event) {
  const periods = Array.isArray(event.periods) ? event.periods : [event.period].filter(Boolean);
  const year = Number(String(event.sortDate || event.dateStart || "").slice(0, 4));
  if (periods.includes("warsaw") && !periods.includes("european")) return "warsaw";
  if (periods.includes("hollywood") && year >= 1935) return "hollywood";
  if (periods.includes("european") || (year >= 1926 && year <= 1934)) return "european";
  return year >= 1935 ? "hollywood" : "warsaw";
}

const NAV_LABELS = { warsaw: "Warsaw", european: "European", hollywood: "Hollywood" };
const CHAPTER_ORDER = ["warsaw", "european", "hollywood"];

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
        <div class="timeline-chapter__eyebrow"><span class="timeline-chapter__number">Chapter ${chapter.number}</span><span class="timeline-chapter__range">${escapeHtml(chapter.range)}</span><h2>${escapeHtml(chapter.title)}</h2></div>
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

function eventDates(event) {
  const rawDate = event.displayDate || event.dateStart || "";
  const isCompoundDate = rawDate.includes("/") || (rawDate.includes("\u2013") && /january|february|march|april|may|june|july|august|september|october|november|december/i.test(rawDate));
  const startYear = String(event.dateStart || "").slice(0, 4);
  const endYear = String(event.dateEnd || "").slice(0, 4);
  return {
    railDate: isCompoundDate ? (endYear && endYear !== startYear ? `${startYear}\u2013${endYear}` : startYear) : rawDate,
    fullDate: isCompoundDate ? rawDate.replace(/\s*\u2013\s*/g, " \u2013 ").replace(/\s*\/\s*/g, " / ") : "",
  };
}

function presentationForEvent(event) {
  if (MILESTONE_EVENT_IDS.has(event.id)) return "milestone";
  if (event.displayMode === "period band") return "period";
  if (event.displayMode === "cluster") return "cluster";
  return "point";
}

function presentationLabel(presentation) {
  if (presentation === "milestone") return "Milestone";
  if (presentation === "period") return "Documented period";
  if (presentation === "cluster") return "Event group";
  return "";
}

function eventCopyMarkup(event, presentation, dates, description, { includeDate = true } = {}) {
  const label = presentationLabel(presentation);
  return `
    ${label ? `<span class="timeline-entry__kicker">${escapeHtml(label)}</span>` : ""}
    ${includeDate ? `<time class="timeline-entry__date" datetime="${escapeHtml(event.dateStart || event.sortDate || "")}">${escapeHtml(dates.railDate)}</time>` : ""}
    <div class="meta-row"><span class="badge badge--type">${escapeHtml(GROUP_LABELS[eventGroup(event)])}</span>${periodBadge(event.periods || event.period)}</div>
    <h3><a href="${recordUrl("event", event.id)}">${escapeHtml(event.title)}</a></h3>
    ${dates.fullDate ? `<p class="timeline-entry__fulldate">${escapeHtml(dates.fullDate)}</p>` : ""}
    ${event.placeDisplay ? `<p class="timeline-entry__place">${escapeHtml(event.placeDisplay)}</p>` : ""}
    ${description ? `<p class="timeline-entry__summary">${escapeHtml(description)}</p>` : ""}
    ${presentation === "milestone" ? `<a class="timeline-entry__record-link" href="${recordUrl("event", event.id)}">Open event record <span aria-hidden="true">\u2192</span></a>` : ""}`;
}

function heroMarkup(hero, heroSources, variant = "compact") {
  if (!hero) return "";
  return `<figure class="timeline-entry__media timeline-entry__media--${variant}">
    ${responsiveImage(hero.assetPath, hero.altText || hero.title, {
      className: "timeline-entry__image",
      sizes: variant === "feature"
        ? "(max-width: 760px) calc(100vw - 4.5rem), (max-width: 1100px) 42vw, 30rem"
        : "(max-width: 760px) 7rem, 8.5rem",
    })}
    <figcaption>${renderMediaDisclosure(hero, heroSources, {
      compact: true,
      fairUseResolutionLabel: "Low-resolution scholarly reproduction",
      includeCaption: false,
      includeCredit: false,
      includeFullRightsNote: false,
      includeRationale: false,
    })}</figcaption>
  </figure>`;
}

try {
  const { timelineEvents, media, people, sources } = await loadTables(["timelineEvents", "media", "people", "sources"]);
  if (totalLabelTarget) {
    totalLabelTarget.textContent = `${timelineEvents.length} published ${timelineEvents.length === 1 ? "event" : "events"}`;
  }
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

  let activeView = "highlights";

  function setView(view, { renderNow = true } = {}) {
    activeView = view === "all" ? "all" : "highlights";
    for (const [key, button] of Object.entries(viewControls)) {
      if (!button) continue;
      const isActive = key === activeView;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", String(isActive));
    }
    if (renderNow) render();
  }

  function render() {
    const query = normalizeSearch(controls.search.value.trim());
    const matching = indexed
      .filter((event) => (
        (!query || event._search.includes(query))
        && (!controls.category.value || eventGroup(event) === controls.category.value)
      ))
      .sort((a, b) => String(a.sortDate || a.dateStart).localeCompare(String(b.sortDate || b.dateStart)) || Number(a.sortOrder || 0) - Number(b.sortOrder || 0));
    const filtered = activeView === "highlights"
      ? matching.filter((event) => MILESTONE_EVENT_IDS.has(event.id))
      : matching;

    countTarget.innerHTML = activeView === "highlights"
      ? `<strong>${filtered.length}</strong> ${filtered.length === 1 ? "highlight" : "highlights"} selected from ${matching.length} matching ${matching.length === 1 ? "event" : "events"}`
      : `<strong>${filtered.length}</strong> ${filtered.length === 1 ? "event" : "events"} shown`;
    if (!filtered.length) {
      target.innerHTML = activeView === "highlights" && matching.length
        ? `<div class="empty-state"><h2>No highlighted events match</h2><p>Switch to the full chronology to see all ${matching.length} matching ${matching.length === 1 ? "event" : "events"}.</p></div>`
        : `<div class="empty-state"><h2>No matching events</h2><p>Try a broader search or remove a filter.</p></div>`;
      return;
    }
    const chaptersPresent = CHAPTER_ORDER.filter((key) => filtered.some((event) => chapterForEvent(event) === key));
    let currentChapter = "";
    let milestoneIndex = 0;
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
      const presentation = presentationForEvent(event);
      const dates = eventDates(event);
      const copy = eventCopyMarkup(event, presentation, dates, description, { includeDate: presentation === "milestone" });

      if (presentation === "milestone") {
        const mediaSide = milestoneIndex % 2 === 0 ? "right" : "left";
        milestoneIndex += 1;
        timelineMarkup.push(`
          <article class="timeline-entry timeline-entry--milestone timeline-entry--media-${mediaSide}${heroPortrait ? " timeline-entry--portrait" : ""}${hero ? "" : " timeline-entry--text-only"}" id="event-${escapeHtml(event.id)}" data-event-id="${escapeHtml(event.id)}">
            <div class="timeline-entry__copy">${copy}</div>
            <span class="timeline-entry__node" aria-hidden="true"></span>
            ${heroMarkup(hero, heroSources, "feature")}
          </article>`);
      } else {
        timelineMarkup.push(`
          <article class="timeline-entry timeline-entry--${presentation}${heroPortrait ? " timeline-entry--portrait" : ""}${hero ? " timeline-entry--has-media" : ""}" id="event-${escapeHtml(event.id)}" data-event-id="${escapeHtml(event.id)}">
            <time class="timeline-entry__rail-date" datetime="${escapeHtml(event.dateStart || event.sortDate || "")}">${escapeHtml(dates.railDate)}</time>
            <span class="timeline-entry__node" aria-hidden="true"></span>
            <div class="timeline-entry__body">
              <div class="timeline-entry__copy">${copy}</div>
              ${heroMarkup(hero, heroSources, "compact")}
            </div>
          </article>`);
      }
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

  controls.search?.addEventListener("input", debounce(() => {
    if (controls.search.value.trim() && activeView === "highlights") setView("all", { renderNow: false });
    render();
  }));
  for (const control of [controls.category].filter(Boolean)) control.addEventListener("change", () => {
    if (control.value && activeView === "highlights") setView("all", { renderNow: false });
    render();
  });
  viewControls.highlights?.addEventListener("click", () => setView("highlights"));
  viewControls.all?.addEventListener("click", () => setView("all"));
  document.querySelector("#timeline-reset")?.addEventListener("click", () => {
    for (const control of Object.values(controls).filter(Boolean)) control.value = "";
    setView("highlights", { renderNow: false });
    render();
  });
  setView("highlights");
} catch (error) {
  countTarget.textContent = "Timeline unavailable";
  renderError(target, error);
}
