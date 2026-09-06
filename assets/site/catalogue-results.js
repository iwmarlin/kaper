import {
  certaintyBadge,
  escapeHtml,
  externalMediaActionLabel,
  formatDate,
  humanize,
  mediaIsFairUse,
  mediaPreview,
  mediaRightsBadge,
  periodBadge,
  recordUrl,
  renderMediaDisclosure,
  safeExternalUrl,
  scopeBadge,
  typeBadge,
  responsiveImage,
  registerImageDerivatives,
} from "./core.js?v=c77ada42a0";

// Build-time prerendering and browser rendering must configure the exact same
// core module instance. Query-stamped ES module URLs are distinct module keys
// in Node as well as in browsers, so expose this small bridge here.
export function registerCatalogueImageDerivatives(mapping) {
  registerImageDerivatives(mapping);
}

export const SOURCE_TYPE_LABELS = Object.freeze({
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

export const DATE_ROLE_LABELS = Object.freeze({
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

export function sourceTypeLabel(value) {
  return SOURCE_TYPE_LABELS[value] || humanize(value || "Other source");
}

export function dateRoleLabel(value) {
  return DATE_ROLE_LABELS[value] || humanize(value || "Unknown date role");
}

export function sourceDateDisplay(source) {
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

export function sourceYear(source) {
  const match = String(source.date || "").match(/^(\d{4})(?:-|$)/);
  return match ? Number(match[1]) : null;
}

export function sourceTitle(source) {
  return source.title || source.shortCitation || source.fullCitation || source.id;
}

export function renderWorkIndexRow(work) {
  const qualificationBadges = [
    work.publicScope === "context_only" ? scopeBadge(work.publicScope) : "",
    work.certainty && work.certainty !== "confirmed" ? certaintyBadge(work.certainty) : "",
  ].join("");
  return `<article class="work-row">
    <div class="work-row__year">${escapeHtml(work.year || "—")}</div>
    <div class="work-row__identity">
      <h2><a href="${recordUrl("work", work.id)}">${escapeHtml(work.title)}</a></h2>
      <div class="meta-row" aria-label="Work classification">${typeBadge(work.workType)}${qualificationBadges}</div>
    </div>
    <div class="work-row__period">${periodBadge(work.periods || work.period)}</div>
  </article>`;
}

function initials(name = "") {
  const parts = String(name).trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  const first = [...parts[0]][0] || "";
  const last = parts.length > 1 ? [...parts[parts.length - 1]][0] || "" : "";
  return (first + last).toUpperCase();
}

export function renderPersonIndexRow(person) {
  const avatar = person.portrait
    ? responsiveImage(person.portrait.assetPath, person.portrait.altText || person.displayName, {
      className: "person-row__portrait",
      sizes: "4rem",
    })
    : `<span class="person-row__monogram" aria-hidden="true">${escapeHtml(initials(person.displayName))}</span>`;
  return `<article class="person-row">
    <div class="person-row__avatar">${avatar}</div>
    <div class="person-row__identity">
      <h2><a href="${recordUrl("person", person.id)}">${escapeHtml(person.displayName)}</a></h2>
      <div class="meta-row" aria-label="Documented roles">${(person.roles || []).map(typeBadge).join("")}</div>
    </div>
    ${(person.periods || []).length
      ? `<div class="person-row__period" aria-label="Documented periods">${periodBadge(person.periods)}</div>`
      : ""}
  </article>`;
}

export function renderSourceIndexRow(source) {
  const external = safeExternalUrl(source.externalUrl);
  return `<article class="source-index-row">
    <div class="source-index-row__rail">
      <span class="source-index-row__id">${escapeHtml(source.id)}</span>
      <span class="source-index-row__date">${escapeHtml(sourceDateDisplay(source))}</span>
    </div>
    <div class="source-index-row__identity">
      <h2><a href="${recordUrl("source", source.id)}">${escapeHtml(sourceTitle(source))}</a></h2>
      <p class="source-index-row__citation">${escapeHtml(source.fullCitation || source.shortCitation || "")}</p>
    </div>
    <div class="source-index-row__context">
      <span class="badge badge--type">${escapeHtml(sourceTypeLabel(source.sourceType))}</span>
      ${source.repository ? `<span class="source-index-row__repository">${escapeHtml(source.repository)}</span>` : ""}
      ${external ? `<a href="${escapeHtml(external)}" target="_blank" rel="noreferrer">Open source <span aria-hidden="true">↗</span></a>` : ""}
    </div>
  </article>`;
}

function compareMedia(itemA, itemB) {
  return Number(itemA.sortOrder || 99999) - Number(itemB.sortOrder || 99999)
    || String(itemA.title).localeCompare(String(itemB.title));
}

export function curatedMediaOrder(items) {
  const collections = items.filter((item) => item.mediaType === "document_gallery").sort(compareMedia);
  const images = items.filter((item) => item.mediaType === "image").sort(compareMedia);
  const references = items.filter((item) => ["video", "audio", "sheet music"].includes(item.mediaType)).sort(compareMedia);
  const other = items.filter((item) => !["document_gallery", "image", "video", "audio", "sheet music"].includes(item.mediaType)).sort(compareMedia);
  const result = [...collections];
  let imageIndex = 0;
  let referenceIndex = 0;
  while (imageIndex < images.length || referenceIndex < references.length) {
    result.push(...images.slice(imageIndex, imageIndex + 2));
    imageIndex += 2;
    if (referenceIndex < references.length) result.push(references[referenceIndex++]);
  }
  return [...result, ...other];
}

export function sortMediaIndex(items) {
  return [...items].sort(compareMedia);
}

export function renderMediaIndexCard(item) {
  const external = safeExternalUrl(item.externalUrl);
  const isGallery = item.mediaType === "document_gallery" && Array.isArray(item.assetPaths) && item.assetPaths.length > 1;
  const isLocalVisual = Boolean(item.assetPath && item.storageType !== "external" && item.mediaType !== "audio");
  const isFairUse = mediaIsFairUse(item);
  const preview = mediaPreview(item, {
    sizes: "(max-width: 680px) calc(100vw - 2rem), (max-width: 1100px) 46vw, 27rem",
  });
  const previewMarkup = isGallery
    ? `<a class="media-card__image-link" href="${recordUrl("media", item.id)}">${preview}<span>Open gallery · ${item.assetPaths.length} images</span></a>`
    : (isLocalVisual
      ? `<a class="media-card__preview-link" href="${recordUrl("media", item.id)}" aria-label="View media record: ${escapeHtml(item.title)}">${preview}</a>`
      : preview);
  return `<article class="media-card" data-media-id="${escapeHtml(item.id)}">
    <figure>${previewMarkup}</figure>
    <div class="media-card__body">
      <div class="meta-row">${typeBadge(item.mediaType)}${periodBadge(item.periods || item.period)}${mediaRightsBadge(item)}</div>
      <h2><a href="${recordUrl("media", item.id)}">${escapeHtml(item.title)}</a></h2>
      <p>${escapeHtml(item.publicCaption || item.description || "")}</p>
      ${isFairUse ? renderMediaDisclosure(item, item.sourceRefs || [], {
        compact: true,
        fairUseResolutionLabel: "Low-resolution copy",
        includeTitle: false,
        includeCaption: false,
        includeRightsBadge: false,
        includeFullRightsNote: false,
      }) : ""}
      <div class="card__footer"><span>${escapeHtml(humanize(item.category || item.mediaType))}</span><span>${escapeHtml(item.id)}</span></div>
      <div class="media-card__actions">
        <a href="${recordUrl("media", item.id)}">${isGallery ? `Open gallery (${item.assetPaths.length})` : "View record"} <span aria-hidden="true">→</span></a>
        ${external ? `<a href="${escapeHtml(external)}" target="_blank" rel="noreferrer">${escapeHtml(externalMediaActionLabel(item))} <span aria-hidden="true">↗</span></a>` : ""}
      </div>
    </div>
  </article>`;
}
