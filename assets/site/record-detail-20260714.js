import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=0c30e19329";
import {
  certaintyBadge,
  escapeHtml,
  getIds,
  humanize,
  indexById,
  mediaIsFairUse,
  mediaRightsBadge,
  mediaPreview,
  mountSiteChrome,
  normalizeSearch,
  periodBadge,
  periodLabel,
  periodValues,
  recordUrl,
  registerImageDerivatives,
  renderError,
  renderMediaDisclosure,
  responsiveImage,
  safeExternalUrl,
  setCanonicalRecordUrl,
  scopeBadge,
  typeBadge,
  updateMeta,
} from "./core.js?v=0c30e19329";

registerImageDerivatives(IMAGE_DERIVATIVES);
mountSiteChrome("");

const target = document.querySelector("#record-root");
const params = new URLSearchParams(location.search);
const requestedType = target?.dataset.recordType || params.get("type");
const requestedId = target?.dataset.recordId || params.get("id");
const TYPE_CONFIG = {
  work: { table: "works", label: "Work", title: (item) => item.title },
  event: { table: "timelineEvents", label: "Timeline event", title: (item) => item.title },
  place: { table: "places", label: "Place", title: (item) => item.displayName },
  media: { table: "media", label: "Media", title: (item) => item.title },
  person: { table: "people", label: "Person", title: (item) => item.displayName },
  organization: { table: "organizations", label: "Organization", title: (item) => item.displayName },
  source: { table: "sources", label: "Source", title: (item) => item.title || item.shortCitation },
};
const RECORD_TABLES = [
  "people", "organizations", "sources", "media", "works", "films", "songs", "otherWorks",
  "titleVariants", "workRelations", "timelineEvents", "places", "contributions", "personNameVariants",
];
const RECORD_DATA_VERSION = "20260726-1";
const LIST_PREVIEW_LIMIT = 6;
const LIST_SEARCH_THRESHOLD = 20;
let progressiveListSequence = 0;
const ENTITY_LIST_LABELS = {
  work: "works",
  event: "events",
  place: "places",
  media: "media",
  person: "people",
  organization: "organizations",
};
const MAP_PRECISION_LABELS = Object.freeze({
  address_level: "Address-level coordinates",
  venue_level: "Venue-level coordinates",
  site_approximate: "Approximate historical site",
  district_level: "District-level reference point",
  city_level: "City-level reference point",
});

function mapPrecisionLabel(value) {
  return MAP_PRECISION_LABELS[value] || humanize(value);
}

async function loadRecordPayload(type, id) {
  const url = new URL(
    `data/site/records/${encodeURIComponent(type)}/${encodeURIComponent(id)}.json?v=${RECORD_DATA_VERSION}`,
    document.baseURI,
  );
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Record data could not be loaded (${response.status}).`);
  const payload = await response.json();
  if (payload.type !== type || payload.id !== id || !payload.tables) {
    throw new Error("The record data does not match this page.");
  }
  for (const table of RECORD_TABLES) {
    if (!Array.isArray(payload.tables[table])) {
      throw new Error(`The record data is incomplete (${table}).`);
    }
  }
  return payload.tables;
}

function fact(label, value) {
  if (value === undefined || value === null || value === "" || (Array.isArray(value) && !value.length)) return "";
  const display = Array.isArray(value) ? value.map(humanize).join(", ") : value;
  return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(display)}</dd></div>`;
}

function factHtml(label, value) {
  if (!value) return "";
  return `<div><dt>${escapeHtml(label)}</dt><dd>${value}</dd></div>`;
}

function section(title, content, className = "", count = 0) {
  if (!content) return "";
  const countLabel = count > LIST_PREVIEW_LIMIT
    ? `<span class="record-section__count" aria-label="${count} records">${count}</span>`
    : "";
  return `<section class="record-section ${className}"><h2>${escapeHtml(title)}${countLabel}</h2>${content}</section>`;
}

function progressiveList(records, {
  tag = "ul",
  className = "entity-list",
  label = "records",
  renderItem,
  searchText = () => "",
  showTotal = true,
} = {}) {
  if (!records.length) return "";
  const isProgressive = records.length > LIST_PREVIEW_LIMIT;
  const items = records.map((item) => {
    const searchValue = normalizeSearch(searchText(item));
    const attributes = isProgressive
      ? ` data-progressive-item data-search="${escapeHtml(searchValue)}"`
      : "";
    return renderItem(item).replace("<li", `<li${attributes}`);
  });
  if (!isProgressive) return `<${tag} class="${className}">${items.join("")}</${tag}>`;
  const searchable = records.length > LIST_SEARCH_THRESHOLD;
  progressiveListSequence += 1;
  const panelId = `progressive-list-${progressiveListSequence}`;
  const initialToggleLabel = showTotal
    ? `Show all ${records.length} ${escapeHtml(label)}`
    : `Show more ${escapeHtml(label)}`;
  const previewItems = items.slice(0, LIST_PREVIEW_LIMIT);
  const remainingItems = items.slice(LIST_PREVIEW_LIMIT);
  return `<div class="progressive-list" data-progressive-list data-label="${escapeHtml(label)}" data-total="${records.length}" data-show-total="${showTotal}">
    <${tag} class="${className} progressive-list__preview">${previewItems.join("")}</${tag}>
    <div class="progressive-list__controls">
      <button class="button button--ghost button--small" type="button" data-progressive-toggle aria-expanded="false" aria-controls="${panelId}">
        ${initialToggleLabel}
      </button>
    </div>
    <div class="progressive-list__panel" id="${panelId}" data-progressive-panel hidden>
      ${searchable ? `<label class="progressive-list__search">
      <span>Search ${escapeHtml(label)}</span>
      <input type="search" data-progressive-search autocomplete="off">
      </label>` : ""}
      <${tag} class="${className} progressive-list__remainder"${tag === "ol" ? ` start="${LIST_PREVIEW_LIMIT + 1}"` : ""}>${remainingItems.join("")}</${tag}>
      <p class="progressive-list__empty" data-progressive-empty hidden>No matching records.</p>
    </div>
    <p class="sr-only" data-progressive-status aria-live="polite"></p>
  </div>`;
}

function entityList(records, type, meta = () => "", label = ENTITY_LIST_LABELS[type] || "records") {
  return progressiveList(records, {
    label,
    renderItem: (item) => `
    <li>
      <a href="${recordUrl(type, item.id)}">${escapeHtml(item.title || item.displayName || item.shortCitation || item.id)}</a>
      <small>${escapeHtml(meta(item))}</small>
    </li>`,
    searchText: (item) => [
      item.id,
      item.title,
      item.displayName,
      item.shortCitation,
      meta(item),
    ].filter(Boolean).join(" "),
  });
}

const SOURCE_TYPE_LABELS = {
  sheet_music: "Sheet music",
  filmographic_database: "Filmographic databases",
  press_item: "Press items",
  copyright_catalogue: "Copyright catalogues",
  online_database: "Online databases",
  wikimedia_commons_file: "Wikimedia Commons files",
  wikimedia_article_page: "Wikipedia articles",
  image_or_photograph: "Images and photographs",
  archival_photo: "Archival photographs",
  archival_photograph: "Archival photographs",
  archival_document: "Archival documents",
  digital_collection_item: "Digital collection items",
  recording_discographic_source: "Recordings",
  online_video_source: "Online video",
  authority_record: "Authority records",
  web_page: "Web pages",
  book: "Books",
};

// Sources carry dates in mixed shapes: "1933", "1936-04-21", "n.d.", and a few
// malformed leftovers. Only a plausible four-digit year is trusted; everything
// else sorts to the end rather than being guessed at.
// One disclosure mark for both levels, drawn rather than typed. The glyphs
// used before — a plus on rows, a solid triangle on group headings — were two
// metaphors for one action, and the triangle's weight and baseline shift with
// whatever font happens to render it. A stroked chevron keeps its hairline at
// any size and rotates to carry the state.
function chevron(className) {
  return `<svg class="${className}" viewBox="0 0 12 12" width="12" height="12" aria-hidden="true" focusable="false"><path d="M4.5 2 L8.5 6 L4.5 10" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}

function sourceYear(source) {
  const match = String(source.date || "").match(/\b(1[5-9]\d{2}|20\d{2})\b/);
  return match ? Number(match[1]) : null;
}

function sortSourcesChronologically(records) {
  return [...records].sort((a, b) => {
    const yearA = sourceYear(a);
    const yearB = sourceYear(b);
    if (yearA === null && yearB === null) return a.id.localeCompare(b.id);
    if (yearA === null) return 1;
    if (yearB === null) return -1;
    return yearA - yearB || a.id.localeCompare(b.id);
  });
}

function sourceSearchText(source) {
  return [
    source.id,
    source.title,
    source.shortCitation,
    source.fullCitation,
    source.creator,
    source.publication,
    source.repository,
    source.date,
    SOURCE_TYPE_LABELS[source.sourceType] || humanize(source.sourceType || ""),
  ].filter(Boolean).join(" ");
}

// One row grammar for every source list: monospaced identifier at the left,
// citation in the middle, year at the right. Short lists print the full
// citation outright — there is nothing to scroll past, so hiding the only
// source a record has behind a disclosure would cost more than it saves.
// Long lists print the short citation and open the full one on request.
function sourceRow(source, index, { expanded = false } = {}) {
  const external = safeExternalUrl(source.primaryUrl) || safeExternalUrl(source.accessUrl);
  const summary = source.shortCitation || source.title || source.fullCitation || source.id;
  const full = source.fullCitation || source.shortCitation || source.title || "";
  const year = sourceYear(source);
  const yearLabel = year ? year : "n.d.";
  const links = `<p class="source-row__links">
    <a href="${recordUrl("source", source.id)}">Source record</a>
    ${external ? `<a href="${escapeHtml(external)}" target="_blank" rel="noreferrer">Open source <span aria-hidden="true">\u2197</span></a>` : ""}
  </p>`;
  if (expanded) {
    return `<li class="source-row source-row--open" id="source-${escapeHtml(source.id)}">
      <span class="source-row__meta">
        <a class="source-row__id" href="${recordUrl("source", source.id)}" aria-label="Open source record ${escapeHtml(source.id)}">${escapeHtml(source.id)}</a>
        <span class="source-row__year">${yearLabel}</span>
      </span>
      <div class="source-row__body">
        <p class="source-row__citation">${escapeHtml(full)}</p>
        ${external ? `<p class="source-row__links"><a href="${escapeHtml(external)}" target="_blank" rel="noreferrer">Open source <span aria-hidden="true">\u2197</span></a></p>` : ""}
      </div>
    </li>`;
  }
  const detailId = `source-detail-${escapeHtml(source.id)}-${index}`;
  return `<li class="source-row" id="source-${escapeHtml(source.id)}" data-ledger-item data-search="${escapeHtml(normalizeSearch(sourceSearchText(source)))}">
    <button class="source-row__summary" type="button" data-row-toggle aria-expanded="false" aria-controls="${detailId}">
      <span class="source-row__meta">
        <span class="source-row__id">${escapeHtml(source.id)}</span>
        <span class="source-row__year">${yearLabel}</span>
      </span>
      <span class="source-row__title">${escapeHtml(summary)}</span>
      ${chevron("source-row__chevron")}
    </button>
    <div class="source-row__detail" id="${detailId}" data-row-detail hidden>
      <p>${escapeHtml(full)}</p>
      ${links}
    </div>
  </li>`;
}

// Long source lists were previously rendered as one bordered card per citation,
// each carrying its full text. On the Kaper record that produced 16 000 px of
// boxes in no particular order. The ledger keeps every record on one page for
// Ctrl+F and for print, but gives it a spine: grouped by kind, chronological
// within each group, full citation on request.
function sourceLedger(records) {
  const sorted = sortSourcesChronologically(records);
  const groups = new Map();
  for (const source of sorted) {
    const key = source.sourceType || "other";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(source);
  }
  const ordered = [...groups.entries()].sort((a, b) => b[1].length - a[1].length);
  progressiveListSequence += 1;
  const ledgerId = `source-ledger-${progressiveListSequence}`;
  let counter = 0;
  const groupsMarkup = ordered.map(([key, items], groupIndex) => {
    const bodyId = `${ledgerId}-group-${groupIndex}`;
    const expanded = ordered.length === 1;
    const rows = items.map((item) => sourceRow(item, counter += 1)).join("");
    return `<section class="source-group" data-ledger-group>
      <button class="source-group__head" type="button" data-group-toggle aria-expanded="${expanded}" aria-controls="${bodyId}">
        ${chevron("source-group__chevron")}
        <span class="source-group__name">${escapeHtml(SOURCE_TYPE_LABELS[key] || humanize(key))}</span>
        <span class="source-group__count">${items.length}</span>
      </button>
      <ol class="source-rows" id="${bodyId}" data-group-body${expanded ? "" : " hidden"}>${rows}</ol>
    </section>`;
  }).join("");
  return `<div class="source-ledger" data-source-ledger data-total="${sorted.length}" id="${ledgerId}">
    <div class="source-ledger__bar">
      <label class="source-ledger__search">
        <span class="sr-only">Search sources</span>
        <input type="search" data-ledger-search autocomplete="off" placeholder="Search ${sorted.length} sources by title, publisher or year">
      </label>
      <button class="button button--ghost button--small" type="button" data-ledger-expand>Expand all</button>
    </div>
    <div class="source-ledger__groups">${groupsMarkup}</div>
    <p class="source-ledger__empty" data-ledger-empty hidden>No matching sources.</p>
    <p class="sr-only" data-ledger-status aria-live="polite"></p>
  </div>`;
}

function sourceList(records, { progressive = true } = {}) {
  if (!records.length) return "";
  if (!progressive || records.length <= LIST_PREVIEW_LIMIT) {
    const rows = sortSourcesChronologically(records)
      .map((source, index) => sourceRow(source, index, { expanded: true }))
      .join("");
    return `<ol class="source-rows source-rows--plain">${rows}</ol>`;
  }
  return sourceLedger(records);
}

function personDisclosure(title, records, renderItem, searchText) {
  if (!records.length) return "";
  const citationList = records.some((item) => item.sourceType || item.shortCitation || item.fullCitation);
  return `<section class="person-collection">
    <h3>${escapeHtml(title)}</h3>
    ${progressiveList(records, {
      tag: citationList ? "ol" : "ul",
      className: citationList ? "citation-list" : "entity-list",
      label: title.toLowerCase(),
      renderItem,
      searchText,
      showTotal: false,
    })}
  </section>`;
}

function personEntityDisclosure(title, records, type, meta = () => "") {
  return personDisclosure(
    title,
    records,
    (item) => {
      const itemMeta = meta(item);
      return `<li><span><a href="${recordUrl(type, item.id)}">${escapeHtml(item.title || item.displayName || item.id)}</a>${itemMeta ? `<br><small>${escapeHtml(itemMeta)}</small>` : ""}</span></li>`;
    },
    (item) => [item.title, item.displayName, item.id, meta(item)].filter(Boolean).join(" "),
  );
}

function related(ids, index) {
  return [...new Set(ids || [])].map((id) => index.get(id)).filter(Boolean);
}

function mediaFigures(items, sourceIndex) {
  if (!items.length) return "";
  return `<div>${items.map((item) => `
    <figure class="record-media">
      ${mediaPreview(item)}
      <figcaption>${renderMediaDisclosure(item, related(item.sourceIds, sourceIndex), { compact: true })}</figcaption>
    </figure>`).join("")}</div>`;
}

function contributionList(items, indexes, {
  conciseCredits = false,
  redundantNotes = [],
  creditLabel = "printed as",
  suppressCatalogueNames = false,
  suppressConfirmedCreatorNotes = false,
} = {}) {
  if (!items.length) return "";
  const redundantNoteSet = new Set(redundantNotes.filter(Boolean));
  return `<ul class="entity-list">${items
    .sort((a, b) => Number(a.sortOrder || 999) - Number(b.sortOrder || 999))
    .map((item) => {
      const people = related(item.personIds, indexes.people);
      const organizations = related(item.organizationIds, indexes.organizations);
      const names = [
        ...people.map((person) => `<a href="${recordUrl("person", person.id)}">${escapeHtml(person.displayName)}</a>`),
        ...organizations.map((organization) => `<a href="${recordUrl("organization", organization.id)}">${escapeHtml(organization.displayName)}</a>`),
      ];
      const catalogueName = suppressCatalogueNames && (
        /\b\d{4}\s*[-–]\s*\d{4}\b/.test(item.nameAsPrinted || "")
        || /^(?:AU|A2|RIS)\b/i.test(item.creditAsPrinted || "")
      );
      const printed = item.nameAsPrinted && !catalogueName && !names.some((name) => name.includes(escapeHtml(item.nameAsPrinted)))
        ? ` · ${escapeHtml(creditLabel)} “${escapeHtml(item.nameAsPrinted)}”`
        : "";
      const publicNote = item.publicNote && !redundantNoteSet.has(item.publicNote) ? item.publicNote : "";
      let note = conciseCredits
        ? publicNote || item.scopeNote || ""
        : item.scopeNote || publicNote || item.evidenceContext || "";
      if (
        suppressConfirmedCreatorNotes
        && ["composer", "arranger"].includes(item.role)
        && String(item.certainty || "").toLowerCase() === "confirmed"
      ) note = "";
      const certainty = conciseCredits && String(item.certainty || "").toLowerCase() === "confirmed"
        ? ""
        : certaintyBadge(item.certainty);
      return `<li><span><strong>${names.join(" · ") || escapeHtml(item.nameAsPrinted || "Unresolved contributor")}</strong>${printed}${note ? `<br><small>${escapeHtml(note)}</small>` : ""}</span><span>${typeBadge(item.role)} ${certainty}</span></li>`;
    }).join("")}</ul>`;
}

function contributionEntityLinks(items, indexes) {
  const seen = new Set();
  const links = [];
  for (const item of items) {
    for (const person of related(item.personIds, indexes.people)) {
      const key = `person:${person.id}`;
      if (seen.has(key)) continue;
      seen.add(key);
      links.push(`<a href="${recordUrl("person", person.id)}">${escapeHtml(person.displayName)}</a>`);
    }
    for (const organization of related(item.organizationIds, indexes.organizations)) {
      const key = `organization:${organization.id}`;
      if (seen.has(key)) continue;
      seen.add(key);
      links.push(`<a href="${recordUrl("organization", organization.id)}">${escapeHtml(organization.displayName)}</a>`);
    }
  }
  return links.join(" · ");
}

function publicationPlace(statement) {
  if (!statement) return "";
  const colonPlace = statement.match(/^([^:;,]+):/);
  if (colonPlace) return colonPlace[1].trim();
  const trailingPlace = statement.match(/,\s*([^,;]+)$/);
  return trailingPlace ? trailingPlace[1].trim().replace(/\.$/, "") : "";
}

function catalogueReference(statement) {
  if (!statement) return "";
  const match = statement.match(/(?:StabiKat record no\.\s*\d+|Bibliothèque nationale de France, notice\s+[A-Z0-9]+)/i);
  return match ? match[0] : "";
}

function otherWorkMaterialSection(subtype, institutionalContributions, indexes) {
  if (!subtype) return "";
  const status = subtype.materialStatus;
  const isManuscript = status === "manuscript";
  const isPublished = status === "published_print";
  const institutions = contributionEntityLinks(institutionalContributions, indexes);
  const materialLabel = isManuscript
    ? "Manuscript"
    : isPublished
      ? "Published score"
      : status === "press_documented"
        ? "Documented in contemporary press"
        : humanize(status);
  const details = `
    ${fact("Instrumentation", subtype.instrumentation)}
    ${fact("Material", materialLabel)}
    ${isManuscript ? factHtml("Holding institution", institutions) : ""}
    ${isManuscript ? fact("Collection and shelfmark", subtype.shelfmark) : ""}
    ${isPublished ? factHtml("Publisher", institutions) : ""}
    ${isPublished ? fact("Publication place", publicationPlace(subtype.publisherOrHoldingAsPrinted)) : ""}
    ${isPublished ? fact("Catalogue reference", catalogueReference(subtype.publisherOrHoldingAsPrinted)) : ""}`;
  const title = isManuscript ? "Material and holding" : isPublished ? "Edition details" : "Material and documentation";
  return section(title, `<dl class="record-facts">${details}</dl>`);
}

function relationList(items, work, indexes) {
  const relationMeta = (item) => {
    const candidateIds = [...getIds(item, "targetWorkIds"), ...getIds(item, "sourceWorkIds")].filter((id) => id !== work.id);
    const targetWork = candidateIds.map((id) => indexes.works.get(id)).find(Boolean);
    const title = targetWork?.title || item.targetWorkTitle || item.targetTitleAsSource || "Related work";
    return { targetWork, title };
  };
  return progressiveList(items, {
    label: "related works",
    renderItem: (item) => {
      const { targetWork, title } = relationMeta(item);
      const titleHtml = targetWork ? `<a href="${recordUrl("work", targetWork.id)}">${escapeHtml(title)}</a>` : escapeHtml(title);
      return `<li><span>${typeBadge(item.relationType)} ${titleHtml}${item.publicNote ? `<br><small>${escapeHtml(item.publicNote)}</small>` : ""}</span>${certaintyBadge(item.certainty)}</li>`;
    },
    searchText: (item) => {
      const { title } = relationMeta(item);
      return [item.id, title, item.relationType, item.publicNote].filter(Boolean).join(" ");
    },
  });
}

function variantList(items) {
  return progressiveList(items, {
    label: "title variants",
    renderItem: (item) => `<li><span><strong>${escapeHtml(item.variantTitle)}</strong>${item.titleAsSource && item.titleAsSource !== item.variantTitle ? `<br><small>Source form: ${escapeHtml(item.titleAsSource)}</small>` : ""}</span><span>${typeBadge(item.variantType)} ${item.language ? periodBadge(item.language) : ""} ${certaintyBadge(item.certainty)}</span></li>`,
    searchText: (item) => [item.variantTitle, item.titleAsSource, item.variantType, item.language].filter(Boolean).join(" "),
  });
}

function publicText(...values) {
  const value = values.find((item) => typeof item === "string" && item.trim());
  return value ? `<p class="lead">${escapeHtml(value)}</p>` : "";
}

const MEDIA_CONTEXT_INTERNAL_PATTERN = /\b(?:source metadata|source route|local asset|archival (?:reference|signature)|rights (?:note|marked|status|expired|remain)|publication status|asset paths?|recorded in SRC\d+|linked through SRC\d+|source\s*:?\s*SRC\d+|linked works?\s*:|related works?\s*:|via IMDb|NB\s*:|verify|verification remains open|needs? (?:review|verification))\b/i;

function mediaContext(media) {
  const sentences = String(media.description || "")
    .match(/[^.!?]+[.!?]+|[^.!?]+$/g)
    ?.map((sentence) => sentence
      .replace(/\s+(?:current\s+)?source(?:\s+route|\s+PDF)?\s*:.*$/i, "")
      .replace(/\s+source\s+SRC\d+.*$/i, "")
      .replace(/\s+(?:linked|related)\s+works?\s*:.*$/i, "")
      .trim())
    .filter((sentence) => sentence && !MEDIA_CONTEXT_INTERNAL_PATTERN.test(sentence)) || [];
  const description = sentences.join(" ");
  if (!description) return "";
  const comparableTokens = (value) => normalizeSearch(value)
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .split(/\s+/)
    .filter((token) => token.length >= 4);
  const referenceTokens = new Set(
    comparableTokens(`${media.title || ""} ${media.publicCaption || ""}`),
  );
  const additionalTokens = new Set(
    comparableTokens(description).filter((token) => !referenceTokens.has(token)),
  );
  const hasExplicitContext = /\b(?:not|rather than|reused|used as|context|evidence|documents?|shows?|depicts?|identifies?|attribution|timeline|illustration|distinguish|correction|version|variant)\b/i.test(description);
  return additionalTokens.size >= 5 || hasExplicitContext ? description : "";
}

function renderWork(work, data, indexes) {
  const isContextOnly = work.publicScope === "context_only";
  const isSong = work.workType === "Song";
  const isFilm = work.workType === "Film";
  const isOther = work.workType === "Other";
  const hasConciseCredits = isSong || isFilm || isOther;
  const subtype = [
    ...related(work.filmIds, indexes.films),
    ...related(work.songIds, indexes.songs),
    ...related(work.otherWorkIds, indexes.otherWorks),
  ][0];
  const contributions = related(work.contributionIds, indexes.contributions);
  const institutionalContributions = isOther
    ? contributions.filter((item) => ["publisher", "holding_institution"].includes(item.role))
    : [];
  const displayedContributions = isOther
    ? contributions.filter((item) => !["publisher", "holding_institution"].includes(item.role))
    : contributions;
  const variants = related(work.titleVariantIds, indexes.titleVariants);
  const relations = related(work.relationIds, indexes.workRelations);
  const sources = related(work.sourceIds, indexes.sources);
  const media = related(work.mediaIds, indexes.media);
  const events = related(work.timelineEventIds, indexes.timelineEvents);
  const subtypeFacts = subtype ? (hasConciseCredits ? `
    ${fact("Instrumentation", subtype.instrumentation)}${fact("Material status", subtype.materialStatus)}${fact("Shelfmark", subtype.shelfmark)}` : `
    ${fact("Genre", subtype.genre)}${isContextOnly ? "" : fact("Credit", subtype.creditType)}${fact("Composer status", subtype.composerStatus)}
    ${fact("Lyricist as printed", subtype.lyricistAsPrinted)}${fact("Lyricist status", subtype.lyricistStatus)}
    ${fact("Publisher as printed", subtype.publisherAsPrinted || subtype.publisherOrHoldingAsPrinted)}
    ${fact("Instrumentation", subtype.instrumentation)}${fact("Material status", subtype.materialStatus)}${fact("Shelfmark", subtype.shelfmark)}`) : "";
  const overview = publicText(subtype?.publicNote, work.publicNote)
    + (!isOther && subtypeFacts.trim() ? `<dl class="record-facts">${subtypeFacts}</dl>` : "");
  const main = [
    section("About this work", overview),
    isOther ? otherWorkMaterialSection(subtype, institutionalContributions, indexes) : "",
    section("Contributors and credits", contributionList(displayedContributions, indexes, {
      conciseCredits: hasConciseCredits || isOther,
      redundantNotes: [work.publicNote, subtype?.publicNote],
      creditLabel: isOther ? "credited as" : "printed as",
      suppressCatalogueNames: isOther,
      suppressConfirmedCreatorNotes: isOther,
    })),
    section("Title variants", variantList(variants), "", variants.length),
    section("Related works and versions", relationList(relations, work, indexes), "", relations.length),
    section("Timeline", entityList(events, "event", (item) => item.displayDate || item.dateStart), "", events.length),
    section("Sources", sourceList(sources), "", sources.length),
  ].join("");
  const aside = mediaFigures(media, indexes.sources) || `<div class="scope-note">No public media are linked to this work.</div>`;
  return {
    title: work.title,
    label: work.workType || "Work",
    badges: `${typeBadge(work.workType)}${periodBadge(work.periods || work.period)}${isContextOnly ? scopeBadge(work.publicScope) : (hasConciseCredits && work.certainty === "confirmed" ? "" : certaintyBadge(work.certainty))}`,
    facts: `${fact("Year", work.year)}${fact("Type", work.workType)}${hasConciseCredits ? fact("Genre", subtype?.genre) : ""}${fact("Period", periodValues(work).map(periodLabel).join(", "))}${isContextOnly ? fact("Kaper attribution", "Not confirmed") : (hasConciseCredits && work.certainty === "confirmed" ? "" : fact("Certainty", humanize(work.certainty)))}`,
    main,
    aside,
  };
}

function renderEvent(event, data, indexes) {
  const people = related(event.personIds, indexes.people);
  const works = related(event.workIds, indexes.works);
  const places = related(event.placeIds, indexes.places);
  const organizations = related(event.organizationIds, indexes.organizations);
  const media = related(event.mediaIds, indexes.media);
  const sources = related(event.sourceIds, indexes.sources);
  return {
    title: event.title,
    label: "Timeline event",
    badges: `${typeBadge(event.category || event.eventType)}${periodBadge(event.periods || event.period)}`,
    facts: `${fact("Date", event.displayDate || event.dateStart)}${fact("Period", periodValues(event).map(periodLabel).join(", "))}${fact("Precision", humanize(event.datePrecision))}${fact("Place", event.placeDisplay)}${fact("Category", humanize(event.category))}`,
    main: [
      section("Event", publicText(event.longDescription, event.shortDescription)),
      section("People", entityList(people, "person", (item) => humanize(item.primaryRole)), "", people.length),
      section("Works", entityList(works, "work", (item) => [item.year, item.workType].filter(Boolean).join(" · ")), "", works.length),
      section("Organizations", entityList(organizations, "organization", (item) => (item.types || []).map(humanize).join(", ")), "", organizations.length),
      section("Places", entityList(places, "place", (item) => [item.city, item.country].filter(Boolean).join(", ")), "", places.length),
      section("Sources", sourceList(sources), "", sources.length),
    ].join(""),
    aside: mediaFigures(media, indexes.sources),
  };
}

function renderPlace(place, data, indexes) {
  const events = related(place.timelineEventIds, indexes.timelineEvents);
  const people = related(place.personIds, indexes.people);
  const media = related(place.mediaIds, indexes.media);
  const sources = related(place.sourceIds, indexes.sources);
  return {
    title: place.displayName,
    label: "Place",
    badges: typeBadge(place.placeType),
    facts: `${fact("City", place.city)}${fact("Region", place.region)}${fact("Country", place.country)}${fact("Place type", humanize(place.placeType))}${fact("Coordinate precision", mapPrecisionLabel(place.mapPrecision))}${fact("Reference coordinates", Number.isFinite(place.latitude) && Number.isFinite(place.longitude) ? `${place.latitude}, ${place.longitude}` : "")}${fact("Linked-event periods", periodValues(place).map(periodLabel).join(", "))}`,
    main: [
      section("About this place", publicText(place.publicNote)),
      section("Documented events", entityList(events, "event", (item) => item.displayDate || item.dateStart), "", events.length),
      section("People", entityList(people, "person", (item) => humanize(item.primaryRole)), "", people.length),
      section("Sources", sourceList(sources), "", sources.length),
    ].join(""),
    aside: mediaFigures(media, indexes.sources),
  };
}

function mediaRelatedWorks(media, indexes) {
  const direct = related(media.workIds, indexes.works);
  const subtypeWorks = [
    ...related(media.songIds, indexes.songs),
    ...related(media.otherWorkIds, indexes.otherWorks),
  ].flatMap((item) => related(item.workIds, indexes.works));
  return [...new Map([...direct, ...subtypeWorks].map((item) => [item.id, item])).values()];
}

function documentGallery(media, allMedia, sourceIndex) {
  const paths = [...new Set(media.assetPaths || [])].filter(Boolean);
  if (media.mediaType !== "document_gallery" || paths.length < 2) return "";
  const explicitMembers = (media.galleryMemberIds || [])
    .map((id) => allMedia.find((item) => item.id === id))
    .filter(Boolean);
  const pathMatches = (item, path, fileName) => (
    item.assetPath === path
    || (item.assetPaths || []).includes(path)
    || [item.assetPath, ...(item.assetPaths || [])]
      .filter(Boolean)
      .some((candidate) => String(candidate).split("/").pop() === fileName)
  );
  const items = paths.map((path, index) => {
    const fileName = String(path).split("/").pop();
    const member = explicitMembers.find((item) => pathMatches(item, path, fileName))
      || allMedia.find((item) => (
        item.id !== media.id
        && item.mediaType !== "document_gallery"
        && pathMatches(item, path, fileName)
      ));
    const title = member?.title || `Gallery image ${index + 1}`;
    const caption = member?.publicCaption || member?.description || `Image ${index + 1} of ${paths.length} in this documentary gallery.`;
    const disclosure = member
      ? renderMediaDisclosure(member, related(member.sourceIds, sourceIndex), {
        compact: true,
        fairUseResolutionLabel: "Low-resolution copy",
        includeFullRightsNote: false,
      })
      : `<strong>${escapeHtml(title)}</strong><p>${escapeHtml(caption)}</p>`;
    return `
      <figure class="record-gallery__item">
        <a class="record-gallery__image" href="${escapeHtml(path)}" target="_blank" rel="noreferrer" aria-label="Open full image: ${escapeHtml(title)}">
          ${responsiveImage(path, member?.altText || title, {
            sizes: "(max-width: 680px) calc(100vw - 4rem), (max-width: 900px) 80vw, 34rem",
          })}
          <span>Open full image <span aria-hidden="true">↗</span></span>
        </a>
        <figcaption>${disclosure}</figcaption>
      </figure>`;
  }).join("");
  return `<div class="record-gallery" aria-label="${escapeHtml(media.title)}">${items}</div>`;
}

function renderMedia(media, data, indexes) {
  const works = mediaRelatedWorks(media, indexes);
  const events = related(media.timelineEventIds, indexes.timelineEvents);
  const places = related(media.placeIds, indexes.places);
  const organizations = related(media.organizationIds, indexes.organizations);
  const sources = related(media.sourceIds, indexes.sources);
  const people = related([...new Set(sources.flatMap((item) => item.personIds || []))], indexes.people);
  const gallery = documentGallery(media, data.media, indexes.sources);
  const isGalleryContainer = media.mediaType === "document_gallery" && Boolean(gallery);
  const galleryCount = [...new Set(media.assetPaths || [])].filter(Boolean).length;
  if (isGalleryContainer) {
    return {
      title: media.title,
      label: "Media gallery",
      badges: `${typeBadge(media.mediaType)}${periodBadge(media.periods || media.period)}`,
      facts: `${fact("Images", galleryCount)}${fact("Period", periodValues(media).map(periodLabel).join(", "))}`,
      main: [
        section("About this gallery", publicText(media.publicCaption, media.description)),
        section(`Gallery · ${galleryCount} images`, gallery, "record-section--gallery"),
        section("Rights and attribution", '<div class="scope-note">Credit, source and rights information are provided with each individual image.</div>'),
      ].join(""),
      aside: "",
      fullWidth: true,
    };
  }
  const context = mediaContext(media);
  return {
    title: media.title,
    label: "Media record",
    badges: `${typeBadge(media.mediaType)}${periodBadge(media.periods || media.period)}${mediaRightsBadge(media)}`,
    facts: `${fact("Category", humanize(media.category))}${fact("Period", periodValues(media).map(periodLabel).join(", "))}${fact("Items", gallery ? media.assetPaths.length : "")}`,
    main: [
      section("About this item", publicText(context)),
      gallery ? section(`Gallery · ${media.assetPaths.length} images`, gallery, "record-section--gallery") : "",
      section("Rights and provenance", `${renderMediaDisclosure(media, sources, {
        compact: mediaIsFairUse(media),
        includeCaption: false,
        includeFullRightsNote: false,
        includeResolutionLabel: false,
        includeRightsBadge: false,
        includeTitle: false,
        includeSource: false,
      })}${sourceList(sources, { progressive: false })}`),
      section("Related works", entityList(works, "work", (item) => [item.year, item.workType].filter(Boolean).join(" · ")), "", works.length),
      section("Timeline", entityList(events, "event", (item) => item.displayDate || item.dateStart), "", events.length),
      section("People", entityList(people, "person", (item) => humanize(item.primaryRole)), "", people.length),
      section("Places", entityList(places, "place", (item) => [item.city, item.country].filter(Boolean).join(", ")), "", places.length),
      section("Organizations", entityList(organizations, "organization", (item) => (item.types || []).map(humanize).join(", ")), "", organizations.length),
    ].join(""),
    aside: `<figure class="record-media">${mediaPreview(media, {
      eager: true,
      sizes: "(max-width: 900px) calc(100vw - 2rem), 20rem",
    })}<figcaption>${escapeHtml(media.publicCaption || media.title)}</figcaption></figure>`,
  };
}

// Life dates used to live inside authorizedName, in whichever convention the
// record happened to be typed in — "Kaper (1902–1983)" beside "Włast, Andrzej,
// 1895–1943" — so they could never display consistently. They are their own
// fields now and the display string is generated here, which makes the format
// a property of the code rather than of whoever entered the record. An open
// end is written as an en dash with nothing after it; a missing birth year as
// nothing before it.
function lifeDates(person) {
  const { birthYear, deathYear } = person;
  if (!birthYear && !deathYear) return "";
  const span = escapeHtml(`${birthYear || ""}\u2013${deathYear || ""}`);
  if (person.lifeDatesCertainty && person.lifeDatesCertainty !== "confirmed") {
    return `${span} ${certaintyBadge(person.lifeDatesCertainty)}`;
  }
  return span;
}

function renderPerson(person, data, indexes) {
  const works = related(person.workIds, indexes.works)
    .sort((a, b) => Number(a.year || 9999) - Number(b.year || 9999) || String(a.title).localeCompare(String(b.title)));
  const events = related(person.timelineEventIds, indexes.timelineEvents)
    .sort((a, b) => String(a.dateStart || "9999").localeCompare(String(b.dateStart || "9999")) || String(a.title).localeCompare(String(b.title)));
  const sources = related(person.sourceIds, indexes.sources)
    .sort((a, b) => String(a.date || "9999").localeCompare(String(b.date || "9999")) || String(a.shortCitation || a.title).localeCompare(String(b.shortCitation || b.title)));
  const portrait = data.media.find((item) => item.assetPath && item.category === "portrait");
  const portraitSources = portrait ? related(portrait.sourceIds, indexes.sources) : [];
  const identities = related(person.nameVariantIds, indexes.personNameVariants)
    .filter((item) => ["pseudonym", "joint_pseudonym", "registration_identity"].includes(item.variantType));
  const authorityLinks = String(person.authorityUrl || "")
    .split(/\r?\n/)
    .map((entry) => {
      const match = entry.trim().match(/^([^:]+):\s*(https?:\/\/\S+)$/);
      if (!match) return null;
      const url = safeExternalUrl(match[2]);
      return url ? { label: match[1], url } : null;
    })
    .filter(Boolean);
  const displayedRoles = [person.primaryRole, ...(person.roles || [])].filter((role, index, roles) => (
    role && roles.findIndex((candidate) => String(candidate).toLowerCase() === String(role).toLowerCase()) === index
  ));
  const workSections = [
    ["Film works", works.filter((item) => item.workType === "Film")],
    ["Songs", works.filter((item) => item.workType === "Song")],
    ["Other works", works.filter((item) => item.workType === "Other")],
  ].map(([title, items]) => personEntityDisclosure(title, items, "work", (item) => [item.year, item.workType].filter(Boolean).join(" · "))).join("");
  return {
    title: person.displayName,
    label: "Person",
    badges: displayedRoles.map(typeBadge).join(""),
    facts: `${factHtml("Life dates", lifeDates(person))}${fact("Authorized name", person.authorizedName)}${fact("Primary role", humanize(person.primaryRole))}${fact("Roles", (person.roles || []).map(humanize))}`,
    main: [
      authorityLinks.length ? section("Authority records", `<ul class="plain-list authority-links">${authorityLinks.map((item) => `<li><a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.label)} <span aria-hidden="true">↗</span></a></li>`).join("")}</ul>`) : "",
      section("Pseudonyms and documented identities", progressiveList(identities, {
        className: "entity-list identity-list",
        label: "documented identities",
        renderItem: (item) => `<li><span><strong>${escapeHtml(item.variantName)}</strong>${item.publicNote ? `<br><small>${escapeHtml(item.publicNote)}</small>` : ""}</span>${typeBadge(item.variantType)}</li>`,
        searchText: (item) => [item.variantName, item.variantType, item.publicNote].filter(Boolean).join(" "),
        showTotal: false,
      })),
      workSections ? section("Related records", `<div class="person-collections">${workSections}</div>`) : "",
      events.length ? section("Documented chronology", personEntityDisclosure("Timeline events", events, "event", (item) => item.displayDate || item.dateStart)) : "",
      section("Sources", sourceList(sources), "", sources.length),
    ].join(""),
    aside: portrait ? `
      <figure class="record-media">${mediaPreview(portrait, {
        eager: true,
        sizes: "(max-width: 900px) calc(100vw - 2rem), 20rem",
      })}</figure>
      ${renderMediaDisclosure(portrait, portraitSources, {
        compact: true,
        includeFullRightsNote: false,
        includeResolutionLabel: true,
      })}
    ` : `<div class="scope-note">Source-specific spellings and printed credit forms appear only on the relevant work records, where their evidentiary context is visible.</div>`,
  };
}

function initializeSourceLedgers() {
  target.querySelectorAll("[data-source-ledger]").forEach((ledger) => {
    const rows = [...ledger.querySelectorAll("[data-ledger-item]")];
    const groups = [...ledger.querySelectorAll("[data-ledger-group]")];
    const search = ledger.querySelector("[data-ledger-search]");
    const expandAll = ledger.querySelector("[data-ledger-expand]");
    const empty = ledger.querySelector("[data-ledger-empty]");
    const status = ledger.querySelector("[data-ledger-status]");
    const total = Number(ledger.dataset.total || rows.length);

    const setGroup = (group, open) => {
      const toggle = group.querySelector("[data-group-toggle]");
      const body = group.querySelector("[data-group-body]");
      toggle.setAttribute("aria-expanded", String(open));
      body.hidden = !open;
    };
    const allOpen = () => groups.every((group) => group.querySelector("[data-group-toggle]").getAttribute("aria-expanded") === "true");
    const syncExpandLabel = () => {
      if (expandAll) expandAll.textContent = allOpen() ? "Collapse all" : "Expand all";
    };

    groups.forEach((group) => {
      group.querySelector("[data-group-toggle]").addEventListener("click", () => {
        const open = group.querySelector("[data-group-toggle]").getAttribute("aria-expanded") === "true";
        setGroup(group, !open);
        syncExpandLabel();
      });
    });

    rows.forEach((row) => {
      const toggle = row.querySelector("[data-row-toggle]");
      const detail = row.querySelector("[data-row-detail]");
      toggle.addEventListener("click", () => {
        const open = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!open));
        detail.hidden = open;
      });
    });

    expandAll?.addEventListener("click", () => {
      const open = !allOpen();
      groups.forEach((group) => setGroup(group, open));
      syncExpandLabel();
    });

    // Searching reaches every group, including collapsed ones. A group that
    // ends up with no match is hidden outright rather than left as an empty
    // heading the reader has to open to discover is empty.
    search?.addEventListener("input", () => {
      const query = normalizeSearch(search.value.trim());
      let visible = 0;
      rows.forEach((row) => {
        const match = !query || row.dataset.search.includes(query);
        row.hidden = !match;
        if (match) visible += 1;
      });
      groups.forEach((group) => {
        const groupRows = [...group.querySelectorAll("[data-ledger-item]")];
        const hits = groupRows.filter((row) => !row.hidden).length;
        group.hidden = query ? hits === 0 : false;
        if (query && hits > 0) setGroup(group, true);
        if (!query) setGroup(group, groups.length === 1);
      });
      if (empty) empty.hidden = visible > 0;
      if (status) {
        status.textContent = query
          ? `${visible} of ${total} sources match the search.`
          : `All ${total} sources are shown, grouped by kind.`;
      }
      syncExpandLabel();
    });

    syncExpandLabel();
  });
}

function initializeProgressiveLists() {
  target.querySelectorAll("[data-progressive-list]").forEach((collection) => {
    const items = [...collection.querySelectorAll("[data-progressive-item]")];
    const toggle = collection.querySelector("[data-progressive-toggle]");
    const panel = collection.querySelector("[data-progressive-panel]");
    const search = collection.querySelector("[data-progressive-search]");
    const empty = collection.querySelector("[data-progressive-empty]");
    const status = collection.querySelector("[data-progressive-status]");
    const label = collection.dataset.label || "records";
    const total = Number(collection.dataset.total || items.length);
    const showTotal = collection.dataset.showTotal !== "false";
    const collapsedLabel = showTotal ? `Show all ${total} ${label}` : `Show more ${label}`;

    const setStatus = (message) => {
      if (status) status.textContent = message;
    };
    const applySearch = () => {
      const query = normalizeSearch(search?.value.trim() || "");
      let visibleCount = 0;
      items.forEach((item) => {
        const visible = !query || item.dataset.search.includes(query);
        item.hidden = !visible;
        if (visible) visibleCount += 1;
      });
      if (empty) empty.hidden = visibleCount > 0;
      setStatus(query
        ? `${visibleCount} of ${total} ${label} match the search.`
        : `All ${total} ${label} are shown.`);
    };
    const expand = () => {
      if (panel) panel.hidden = false;
      if (empty) empty.hidden = true;
      toggle.setAttribute("aria-expanded", "true");
      toggle.textContent = `Show fewer ${label}`;
      setStatus(`All ${total} ${label} are shown.`);
    };
    const collapse = () => {
      if (search) search.value = "";
      if (panel) panel.hidden = true;
      if (empty) empty.hidden = true;
      items.forEach((item) => { item.hidden = false; });
      toggle.setAttribute("aria-expanded", "false");
      toggle.textContent = collapsedLabel;
      setStatus(`Showing the first ${LIST_PREVIEW_LIMIT} of ${total} ${label}.`);
    };

    toggle?.addEventListener("click", () => {
      if (toggle.getAttribute("aria-expanded") === "true") collapse();
      else expand();
    });
    search?.addEventListener("input", applySearch);
  });
}

function renderOrganization(organization, data, indexes) {
  const works = related(organization.workIds, indexes.works);
  const events = related(organization.timelineEventIds, indexes.timelineEvents);
  const sources = related(organization.sourceIds, indexes.sources);
  return {
    title: organization.displayName,
    label: "Organization",
    badges: (organization.types || []).map(typeBadge).join(""),
    facts: `${fact("Authorized name", organization.authorizedName)}${fact("Type", (organization.types || []).map(humanize))}${fact("City", organization.city)}${fact("Country", organization.country)}${fact("Name variants", organization.nameVariants)}`,
    main: [
      section("Works", entityList(works, "work", (item) => [item.year, item.workType].filter(Boolean).join(" · ")), "", works.length),
      section("Timeline", entityList(events, "event", (item) => item.displayDate || item.dateStart), "", events.length),
      section("Sources", sourceList(sources), "", sources.length),
    ].join(""),
    aside: `<div class="scope-note">Organization links are induced from approved public records and their documented contributions.</div>`,
  };
}

function sourceActions(source) {
  const links = [];
  const seen = new Set();
  const add = (url, label) => {
    const safe = safeExternalUrl(url);
    if (!safe || seen.has(safe)) return;
    seen.add(safe);
    links.push({ url: safe, label });
  };
  add(source.primaryUrl, "Open source");
  add(source.accessUrl, "Open direct view");
  for (const link of source.additionalLinks || []) {
    add(link?.url, link?.label || "Open additional source");
  }
  if (!links.length) return "";
  return `<div class="source-actions">${links.map((link, index) => `
    <a class="button ${index ? "button--ghost" : ""} button--small" href="${escapeHtml(link.url)}" target="_blank" rel="noreferrer">
      ${escapeHtml(link.label)} <span aria-hidden="true">↗</span>
    </a>`).join("")}</div>`;
}

function renderSource(source, data, indexes) {
  const works = related(source.workIds, indexes.works);
  const media = related(source.mediaIds, indexes.media);
  const events = related(source.timelineEventIds, indexes.timelineEvents);
  const places = related(source.placeIds, indexes.places);
  const people = related(source.personIds, indexes.people);
  const organizations = related(source.organizationIds, indexes.organizations);
  return {
    title: source.title || source.shortCitation,
    label: "Source",
    badges: typeBadge(source.sourceType),
    facts: `${fact("Creator", source.creator)}${fact("Date", source.date)}${fact("Publication", source.publication)}${fact("Repository", source.repository)}`,
    main: [
      section("Citation", `<p class="lead">${escapeHtml(source.fullCitation || source.shortCitation)}</p>${sourceActions(source)}`),
      section("Supported works", entityList(works, "work", (item) => [item.year, item.workType].filter(Boolean).join(" · ")), "", works.length),
      section("Media", entityList(media, "media", (item) => humanize(item.mediaType)), "", media.length),
      section("Timeline", entityList(events, "event", (item) => item.displayDate || item.dateStart), "", events.length),
      section("Places", entityList(places, "place", (item) => [item.city, item.country].filter(Boolean).join(", ")), "", places.length),
      section("People", entityList(people, "person", (item) => humanize(item.primaryRole)), "", people.length),
      section("Organizations", entityList(organizations, "organization", (item) => (item.types || []).map(humanize).join(", ")), "", organizations.length),
    ].join(""),
    aside: "",
  };
}

const renderers = {
  work: renderWork,
  event: renderEvent,
  place: renderPlace,
  media: renderMedia,
  person: renderPerson,
  organization: renderOrganization,
  source: renderSource,
};

try {
  if (!TYPE_CONFIG[requestedType] || !requestedId) {
    throw new Error("The record URL is incomplete or uses an unsupported record type.");
  }
  const data = await loadRecordPayload(requestedType, requestedId);
  const indexes = Object.fromEntries(RECORD_TABLES.map((name) => [name, indexById(data[name])]));
  const config = TYPE_CONFIG[requestedType];
  const record = indexes[config.table].get(requestedId);
  if (!record) throw new Error(`No public ${config.label.toLowerCase()} record was found for ${requestedId}.`);

  const view = renderers[requestedType](record, data, indexes);
  const titleLength = Array.from(view.title || "").length;
  const titleClass = titleLength > 72 ? " record-hero--extra-long-title" : titleLength > 46 ? " record-hero--long-title" : "";
  updateMeta({
    title: view.title,
    description: `${config.label} ${requestedId} in the source-based Bronisław Kaper archive, documented through 1939.`,
  });
  setCanonicalRecordUrl(requestedType, requestedId);
  target.className = "";
  target.innerHTML = `
    <section class="record-hero${titleClass}">
      <div class="shell record-hero__grid">
        <div>
          <p class="eyebrow">${escapeHtml(view.label)} · <span class="record-id">${escapeHtml(requestedId)}</span></p>
          <h1>${escapeHtml(view.title)}</h1>
          <div class="meta-row">${view.badges}</div>
        </div>
        <dl class="record-facts">${view.facts}</dl>
      </div>
    </section>
    <section class="section">
      <div class="shell record-layout${view.fullWidth ? " record-layout--single" : ""}">
        <div>${view.main || `<div class="empty-state"><p>No additional public detail is available.</p></div>`}</div>
        <aside>${view.aside || ""}</aside>
      </div>
    </section>`;
  initializeProgressiveLists();
  initializeSourceLedgers();
} catch (error) {
  target.className = "shell";
  renderError(target, error);
}
