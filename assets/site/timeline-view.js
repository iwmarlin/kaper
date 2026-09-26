import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=2fb206d950";
import {
  escapeHtml,
  periodBadge,
  recordUrl,
  renderMediaDisclosure,
  responsiveImage,
} from "./core.js?v=2fb206d950";

// The timeline page and the build both render the chronology from this module,
// so the printed first view and the interactive one cannot describe the same
// events differently.

const CATEGORY_GROUPS = {
  birth_family: "life", family: "life", religion_identity: "life", military: "life", citizenship: "life",
  education: "education", law_studies: "education", music_education: "education",
  composition: "music", warsaw_music: "music", concert_life: "music", recording: "music",
  publication: "music", performance: "music", berlin: "music",
  film_career: "career", hollywood: "career", professional_network: "career",
  collaboration: "career", paris: "career", reception: "career",
  migration: "migration", refugee_support: "migration",
};
export const GROUP_LABELS = {
  life: "Life & family",
  education: "Education",
  music: "Music & performance",
  career: "Film & career",
  migration: "Migration",
};
export const GROUP_ORDER = ["life", "education", "music", "career", "migration"];

export function eventGroup(event) {
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

function eventDates(event) {
  const rawDate = event.displayDate || event.dateStart || "";
  const isCompoundDate = rawDate.includes("/") || (rawDate.includes("–") && /january|february|march|april|may|june|july|august|september|october|november|december/i.test(rawDate));
  const startYear = String(event.dateStart || "").slice(0, 4);
  const endYear = String(event.dateEnd || "").slice(0, 4);
  return {
    railDate: isCompoundDate ? (endYear && endYear !== startYear ? `${startYear}–${endYear}` : startYear) : rawDate,
    fullDate: isCompoundDate ? rawDate.replace(/\s*–\s*/g, " – ").replace(/\s*\/\s*/g, " / ") : "",
  };
}

// How an event is presented is an editorial decision about that event, so it
// is read from the record rather than from a list of identifiers kept here:
// the chronology the page draws and the one the data states cannot drift
// apart, and a milestone can be added or withdrawn without touching the site.
function presentationForEvent(event) {
  if (event.displayMode === "milestone") return "milestone";
  if (event.displayMode === "period band") return "period";
  if (event.displayMode === "cluster") return "cluster";
  return "point";
}

/** The events the highlights view shows, and the ones it presents large. */
export function isMilestone(event) {
  return presentationForEvent(event) === "milestone";
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
    ${presentation === "milestone" ? `<a class="timeline-entry__record-link" href="${recordUrl("event", event.id)}">Open event record <span aria-hidden="true">→</span></a>` : ""}`;
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

export function sortEvents(events) {
  return [...events].sort((a, b) => (
    String(a.sortDate || a.dateStart).localeCompare(String(b.sortDate || b.dateStart))
    || Number(a.sortOrder || 0) - Number(b.sortOrder || 0)
  ));
}

// Takes the events that match the reader's search and category, already in
// chronological order, and returns the count sentence and the chronology.
export function renderTimeline(matching, view) {
  const filtered = view === "highlights"
    ? matching.filter(isMilestone)
    : matching;
  const countHtml = view === "highlights"
    ? `<strong>${filtered.length}</strong> ${filtered.length === 1 ? "highlight" : "highlights"} selected from ${matching.length} matching ${matching.length === 1 ? "event" : "events"}`
    : `<strong>${filtered.length}</strong> ${filtered.length === 1 ? "event" : "events"} shown`;
  if (!filtered.length) {
    return {
      countHtml,
      shown: 0,
      markup: view === "highlights" && matching.length
        ? `<div class="empty-state"><h2>No highlighted events match</h2><p>Switch to the full chronology to see all ${matching.length} matching ${matching.length === 1 ? "event" : "events"}.</p></div>`
        : `<div class="empty-state"><h2>No matching events</h2><p>Try a broader search or remove a filter.</p></div>`,
    };
  }
  let currentChapter = "";
  const timelineMarkup = [];
  for (const event of filtered) {
    const chapter = chapterForEvent(event);
    if (chapter !== currentChapter) {
      timelineMarkup.push(chapterMarkup(chapter));
      currentChapter = chapter;
    }
    const hero = event.hero || null;
    const heroProfile = hero ? IMAGE_DERIVATIVES[hero.assetPath] : null;
    const heroPortrait = Boolean(heroProfile && heroProfile.height > heroProfile.width);
    const heroSources = event.heroSource ? [event.heroSource] : [];
    const description = event.shortDescription || event.longDescription || "";
    const presentation = presentationForEvent(event);
    const dates = eventDates(event);
    // One structure carries every event: the date on the rail, the node on the
    // spine, then a single column of text with its image beside it. A
    // milestone is the same entry with more room — a larger image, a larger
    // title, more air around it — rather than a different shape. The reader
    // keeps one left edge down the whole chronology, and the highlights view
    // is the same chronicle with fewer rows.
    const copy = eventCopyMarkup(event, presentation, dates, description, { includeDate: false });
    timelineMarkup.push(`
        <article class="timeline-entry timeline-entry--${presentation}${heroPortrait ? " timeline-entry--portrait" : ""}${hero ? " timeline-entry--has-media" : ""}" id="event-${escapeHtml(event.id)}" data-event-id="${escapeHtml(event.id)}" data-chapter="${escapeHtml(chapter)}">
          <time class="timeline-entry__rail-date" datetime="${escapeHtml(event.dateStart || event.sortDate || "")}">${escapeHtml(dates.railDate)}</time>
          <span class="timeline-entry__node" aria-hidden="true"></span>
          <div class="timeline-entry__body">
            <div class="timeline-entry__copy">${copy}</div>
            ${heroMarkup(hero, heroSources, presentation === "milestone" ? "feature" : "compact")}
          </div>
        </article>`);
  }
  return { countHtml, shown: filtered.length, markup: timelineMarkup.join("") };
}
