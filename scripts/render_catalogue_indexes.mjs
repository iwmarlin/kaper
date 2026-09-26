#!/usr/bin/env node
/** Render the first page of each catalogue index and every home-page section. */

import process from "node:process";
import path from "node:path";
import { readFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(process.argv[2] || path.join(scriptDir, ".."));
const core = await import(pathToFileURL(path.join(projectRoot, "assets/site/core.js")).href);
const views = await import(pathToFileURL(path.join(projectRoot, "assets/site/catalogue-results.js")).href);
const derivatives = await import(pathToFileURL(path.join(projectRoot, "assets/site/image-derivatives.js")).href);
const timeline = await import(pathToFileURL(path.join(projectRoot, "assets/site/timeline-view.js")).href);
const mapPlaces = await import(pathToFileURL(path.join(projectRoot, "assets/site/map-places.js")).href);
const placeRecords = JSON.parse(await readFile(path.join(projectRoot, "data/public/v1/places.json"), "utf8")).records;

let input = "";
// Decode the stream continuously: coercing individual Buffer chunks can split
// a multibyte character at a chunk boundary and corrupt a title nondeterministically.
process.stdin.setEncoding("utf8");
for await (const chunk of process.stdin) input += chunk;
const indexes = JSON.parse(input);
views.registerCatalogueImageDerivatives(derivatives.IMAGE_DERIVATIVES);

const works = [...indexes.works.records].sort((left, right) => {
  const byTitle = core.compareText(left.sortTitle || left.title, right.sortTitle || right.title);
  return Number(left.year || 9999) - Number(right.year || 9999) || byTitle;
});
const people = [...indexes.people.records].sort((left, right) => (
  core.compareText(left.sortName || left.displayName, right.sortName || right.displayName)
));
const sources = [...indexes.sources.records].sort((left, right) => {
  const byTitle = core.compareText(views.sourceTitle(left), views.sourceTitle(right));
  const byId = core.compareText(left.id, right.id);
  return (views.sourceYear(left) ?? Number.POSITIVE_INFINITY)
    - (views.sourceYear(right) ?? Number.POSITIVE_INFINITY)
    || byTitle
    || byId;
});
const selectedMedia = indexes.media.records.filter((item) => item.galleryStatus === "selected");
const media = views.curatedMediaOrder(selectedMedia);

const page = (items, limit, renderer, noun) => {
  const shown = items.slice(0, limit);
  return {
    markup: shown.map(renderer).join("\n"),
    countText: `Showing ${shown.length} of ${items.length} ${items.length === 1 ? noun[0] : noun[1]}`,
    shown: shown.length,
  };
};

const mediaPage = page(media, 30, views.renderMediaIndexCard, ["item", "items"]);
mediaPage.countText = views.renderMediaResultsCount({
  shown: mediaPage.shown,
  matched: media.length,
  scope: "selected",
  publicTotal: indexes.media.records.length,
});

// The home sections render through this script's own core instance. The
// catalogue module imports core under its stamped URL, which Node keys as a
// separate module, so the image derivatives are registered on both.
core.registerImageDerivatives(derivatives.IMAGE_DERIVATIVES);
const numberFormat = new Intl.NumberFormat("en-GB");

// One gateway, one set of figures: each count says how much there is and leads
// straight to it.
function homePathways(pathways) {
  return pathways.map((pathway) => `
    <li>
      <a class="pathway-row" href="${core.escapeHtml(pathway.href)}">
        <span class="pathway-row__content">
          <span class="pathway-row__title">${core.escapeHtml(pathway.label)}</span>
          <span class="pathway-row__description">${core.escapeHtml(pathway.description)}</span>
        </span>
        <span class="pathway-row__count">${numberFormat.format(pathway.count)}</span>
        <span class="pathway-row__arrow" aria-hidden="true">→</span>
      </a>
    </li>`).join("");
}

// In a source-based archive the one image on the front page carries its caption
// and a link to its own record. The picture leads there too, because that is
// what a reader clicks; it stays out of the tab order and out of the
// accessibility tree, so the caption's link is announced once, not twice.
function homePortrait(portrait) {
  if (!portrait?.assetPath) return "";
  return `
    <a class="hero__portrait-link" href="${core.recordUrl("media", portrait.id)}" tabindex="-1" aria-hidden="true">${core.responsiveImage(portrait.assetPath, portrait.altText || portrait.title, {
      eager: true,
      sizes: "(max-width: 680px) 9rem, 20rem",
    })}</a>
    <figcaption>
      <span class="hero__portrait-caption">${core.escapeHtml(portrait.publicCaption || portrait.title || "")}</span>
      <a href="${core.recordUrl("media", portrait.id)}">See the record</a>
    </figcaption>`;
}

function homeEvents(events) {
  return events.map((event) => `
    <article class="home-event-card">
      ${event.image ? `<figure class="home-event-card__figure">${core.responsiveImage(event.image.assetPath, event.image.altText || event.title, {
        sizes: "(max-width: 680px) calc(100vw - 2.5rem), 22rem",
      })}</figure>` : ""}
      <div class="home-event-card__body">
        <div class="home-event-card__topline">
          <p class="home-event-card__date">${core.escapeHtml(event.displayDate || event.dateStart || "")}</p>
          ${core.periodBadge(event.periods || event.period)}
        </div>
        <h3><a href="${core.recordUrl("event", event.id)}">${core.escapeHtml(event.title)}</a></h3>
        <p class="card__description">${core.escapeHtml(event.shortDescription || event.longDescription || "")}</p>
        <div class="home-event-card__footer"><span>${core.escapeHtml(event.placeDisplay || "")}</span><span aria-hidden="true">→</span></div>
      </div>
    </article>`).join("");
}

// The figures belong to the statement of method: they say how firm the record
// is, not how large it is. They report qualified attributions rather than
// confirmed ones and leave out empty categories, because "0 uncertain" would
// read as a claim that nothing here is in doubt, in an archive whose doubts are
// recorded on individual attributions, scopes and rights.
function homeFigures(glance) {
  const certainty = glance.certainty || {};
  const total = Object.values(certainty).reduce((sum, value) => sum + (value || 0), 0);
  const qualified = (certainty.probable || 0) + (certainty.uncertain || 0);
  const parts = [];
  if (total) {
    parts.push(qualified
      ? `<strong>${numberFormat.format(total)}</strong> works, of which <strong>${qualified}</strong> carry a qualified attribution`
      : `<strong>${numberFormat.format(total)}</strong> works`);
  }
  if (glance.span) parts.push(`documented <strong>${glance.span.start}–${glance.span.end}</strong>`);
  if (glance.sources) parts.push(`<strong>${numberFormat.format(glance.sources)}</strong> linked sources`);
  return parts.join(" · ");
}

// A reader without saved filters first sees the highlights over every event.
const timelineEvents = timeline.sortEvents(indexes.timeline.records);
const timelineView = timeline.renderTimeline(timelineEvents, "highlights");

// The one ornament on the home page is the chronology itself: the archive's
// stated span, 1902 to 1939, ruled once, with a tick where each published
// event falls. It is drawn from the same records the chronology draws, so it
// cannot come to say something the archive does not. What it states is where
// the evidence is, not how much of it there is — one event, one tick, no
// heights to read as a quantity. The long emptiness after 1902 is the point:
// the record begins at a birth certificate and then falls silent for thirteen
// years, and the page says so before the reader has scrolled anywhere.
const RULE_WIDTH = 460;
const SPAN_START = Date.UTC(1902, 0, 1);
const SPAN_END = Date.UTC(1940, 0, 1);

function rulePosition(event) {
  const raw = String(event.sortDate || event.dateStart || "").slice(0, 10);
  const [year, month = "01", day = "01"] = raw.split("-");
  const stamp = Date.UTC(Number(year), Number(month) - 1, Number(day));
  if (!Number.isFinite(stamp)) return null;
  const share = (stamp - SPAN_START) / (SPAN_END - SPAN_START);
  return Math.round(Math.min(Math.max(share, 0), 1) * RULE_WIDTH * 10) / 10;
}

function ticks(events, top) {
  const marks = events.map(rulePosition).filter((x) => x !== null);
  return marks.map((x) => `M${x} ${top}V9.5`).join("");
}

function homeDateRule(events) {
  const dated = events.filter((event) => rulePosition(event) !== null);
  const milestones = dated.filter(timeline.isMilestone);
  const rest = dated.filter((event) => !timeline.isMilestone(event));
  return `<svg class="hero__span-rule" viewBox="0 0 ${RULE_WIDTH} 10" width="${RULE_WIDTH}" height="10" fill="none" shape-rendering="crispEdges" aria-hidden="true" focusable="false">`
    + `<path d="M0 9.5H${RULE_WIDTH}" stroke-opacity="0.26"></path>`
    + `<path d="${ticks(rest, 3.5)}" stroke-opacity="0.38"></path>`
    + `<path d="${ticks(milestones, 0.5)}" stroke-opacity="0.52"></path>`
    + `</svg>`;
}

// Without JavaScript a place cannot be selected on the map, so the printed list
// leads to each place's own record instead.
const placeList = mapPlaces.sortPlaces(placeRecords).map((place) => `
            <li>
              <a href="${core.recordUrl("place", place.id)}" aria-label="${core.escapeHtml(mapPlaces.placeListLabel(place))}">${mapPlaces.placeListContent(place)}
              </a>
            </li>`).join("");

process.stdout.write(JSON.stringify({
  works: page(works, 36, views.renderWorkIndexRow, ["record", "records"]),
  people: page(people, 48, views.renderPersonIndexRow, ["person", "people"]),
  media: mediaPage,
  sources: page(sources, 40, views.renderSourceIndexRow, ["source", "sources"]),
  timeline: {
    markup: timelineView.markup,
    countHtml: timelineView.countHtml,
    shown: timelineView.shown,
    totalLabel: `${timelineEvents.length} published ${timelineEvents.length === 1 ? "event" : "events"}`,
  },
  places: { markup: placeList, shown: placeRecords.length },
  home: {
    portrait: homePortrait(indexes.home.portrait),
    pathways: homePathways(indexes.home.pathways),
    events: homeEvents(indexes.home.events),
    figures: homeFigures(indexes.home.glance),
    dates: homeDateRule(timelineEvents),
  },
}));
