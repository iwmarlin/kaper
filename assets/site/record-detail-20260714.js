import {
  certaintyBadge,
  escapeHtml,
  getIds,
  humanize,
  indexById,
  loadTables,
  mediaPreview,
  mountSiteChrome,
  periodBadge,
  recordUrl,
  renderError,
  renderSourceCitation,
  rightsBadge,
  rightsLabel,
  safeExternalUrl,
  setCanonicalRecordUrl,
  galleryScopeLabel,
  storageLabel,
  typeBadge,
  updateMeta,
} from "./core.js";

mountSiteChrome("");

const target = document.querySelector("#record-root");
const params = new URLSearchParams(location.search);
const requestedType = params.get("type");
const requestedId = params.get("id");
const TYPE_CONFIG = {
  work: { table: "works", label: "Work", title: (item) => item.title },
  event: { table: "timelineEvents", label: "Timeline event", title: (item) => item.title },
  place: { table: "places", label: "Place", title: (item) => item.displayName },
  media: { table: "media", label: "Media", title: (item) => item.title },
  person: { table: "people", label: "Person", title: (item) => item.displayName },
  organization: { table: "organizations", label: "Organization", title: (item) => item.displayName },
  source: { table: "sources", label: "Source", title: (item) => item.title || item.shortCitation },
};

function fact(label, value) {
  if (value === undefined || value === null || value === "" || (Array.isArray(value) && !value.length)) return "";
  const display = Array.isArray(value) ? value.map(humanize).join(", ") : value;
  return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(display)}</dd></div>`;
}

function section(title, content, className = "") {
  if (!content) return "";
  return `<section class="record-section ${className}"><h2>${escapeHtml(title)}</h2>${content}</section>`;
}

function entityList(records, type, meta = () => "") {
  if (!records.length) return "";
  return `<ul class="entity-list">${records.map((item) => `
    <li>
      <a href="${recordUrl(type, item.id)}">${escapeHtml(item.title || item.displayName || item.shortCitation || item.id)}</a>
      <small>${escapeHtml(meta(item))}</small>
    </li>`).join("")}</ul>`;
}

function sourceList(records) {
  return records.length ? `<ol class="citation-list">${records.map(renderSourceCitation).join("")}</ol>` : "";
}

function related(ids, index) {
  return [...new Set(ids || [])].map((id) => index.get(id)).filter(Boolean);
}

function mediaFigures(items) {
  if (!items.length) return "";
  return `<div>${items.map((item) => `
    <figure class="record-media">
      ${mediaPreview(item)}
      <figcaption>
        <a href="${recordUrl("media", item.id)}">${escapeHtml(item.title)}</a>
        ${item.publicCaption ? `<p>${escapeHtml(item.publicCaption)}</p>` : ""}
      </figcaption>
    </figure>`).join("")}</div>`;
}

function contributionList(items, indexes) {
  if (!items.length) return "";
  return `<ul class="entity-list">${items
    .sort((a, b) => Number(a.sortOrder || 999) - Number(b.sortOrder || 999))
    .map((item) => {
      const people = related(item.personIds, indexes.people);
      const organizations = related(item.organizationIds, indexes.organizations);
      const names = [
        ...people.map((person) => `<a href="${recordUrl("person", person.id)}">${escapeHtml(person.displayName)}</a>`),
        ...organizations.map((organization) => `<a href="${recordUrl("organization", organization.id)}">${escapeHtml(organization.displayName)}</a>`),
      ];
      const printed = item.nameAsPrinted && !names.some((name) => name.includes(escapeHtml(item.nameAsPrinted)))
        ? ` · printed as “${escapeHtml(item.nameAsPrinted)}”`
        : "";
      return `<li><span><strong>${names.join(" · ") || escapeHtml(item.nameAsPrinted || "Unresolved contributor")}</strong>${printed}<br><small>${escapeHtml(item.scopeNote || item.publicNote || item.evidenceContext || "")}</small></span><span>${typeBadge(item.role)} ${certaintyBadge(item.certainty)}</span></li>`;
    }).join("")}</ul>`;
}

function relationList(items, work, indexes) {
  if (!items.length) return "";
  return `<ul class="entity-list">${items.map((item) => {
    const candidateIds = [...getIds(item, "targetWorkIds"), ...getIds(item, "sourceWorkIds")].filter((id) => id !== work.id);
    const targetWork = candidateIds.map((id) => indexes.works.get(id)).find(Boolean);
    const title = targetWork?.title || item.targetWorkTitle || item.targetTitleAsSource || "Related work";
    const titleHtml = targetWork ? `<a href="${recordUrl("work", targetWork.id)}">${escapeHtml(title)}</a>` : escapeHtml(title);
    return `<li><span>${typeBadge(item.relationType)} ${titleHtml}${item.publicNote ? `<br><small>${escapeHtml(item.publicNote)}</small>` : ""}</span>${certaintyBadge(item.certainty)}</li>`;
  }).join("")}</ul>`;
}

function variantList(items) {
  if (!items.length) return "";
  return `<ul class="entity-list">${items.map((item) => `<li><span><strong>${escapeHtml(item.variantTitle)}</strong>${item.titleAsSource && item.titleAsSource !== item.variantTitle ? `<br><small>Source form: ${escapeHtml(item.titleAsSource)}</small>` : ""}</span><span>${typeBadge(item.variantType)} ${item.language ? periodBadge(item.language) : ""} ${certaintyBadge(item.certainty)}</span></li>`).join("")}</ul>`;
}

function rightsPanel(media) {
  if (!media.rightsStatus && !media.rightsNote && !media.publicCreditLine) return "";
  return `<div class="rights-panel">
    <p class="eyebrow">Rights and permitted use</p>
    <h2>${escapeHtml(rightsLabel(media.rightsStatus, media.rightsNote))}</h2>
    ${media.publicCreditLine ? `<p><strong>Credit:</strong> ${escapeHtml(media.publicCreditLine)}</p>` : ""}
    ${media.rightsNote ? `<p>${escapeHtml(media.rightsNote)}</p>` : ""}
  </div>`;
}

function publicText(...values) {
  const value = values.find((item) => typeof item === "string" && item.trim());
  return value ? `<p class="lead">${escapeHtml(value)}</p>` : "";
}

function renderWork(work, data, indexes) {
  const subtype = [
    ...related(work.filmIds, indexes.films),
    ...related(work.songIds, indexes.songs),
    ...related(work.otherWorkIds, indexes.otherWorks),
  ][0];
  const contributions = related(work.contributionIds, indexes.contributions);
  const variants = related(work.titleVariantIds, indexes.titleVariants);
  const relations = related(work.relationIds, indexes.workRelations);
  const sources = related(work.sourceIds, indexes.sources);
  const media = related(work.mediaIds, indexes.media);
  const events = related(work.timelineEventIds, indexes.timelineEvents);
  const overview = publicText(subtype?.publicNote, work.publicNote)
    + (subtype ? `<dl class="record-facts">
      ${fact("Genre", subtype.genre)}${fact("Credit", subtype.creditType)}${fact("Composer status", subtype.composerStatus)}
      ${fact("Lyricist as printed", subtype.lyricistAsPrinted)}${fact("Lyricist status", subtype.lyricistStatus)}
      ${fact("Publisher as printed", subtype.publisherAsPrinted || subtype.publisherOrHoldingAsPrinted)}
      ${fact("Instrumentation", subtype.instrumentation)}${fact("Material status", subtype.materialStatus)}${fact("Shelfmark", subtype.shelfmark)}
    </dl>` : "");
  const main = [
    section("About this work", overview),
    section("Contributors and credits", contributionList(contributions, indexes)),
    section("Title variants", variantList(variants)),
    section("Related works and versions", relationList(relations, work, indexes)),
    section("Timeline", entityList(events, "event", (item) => item.displayDate || item.dateStart)),
    section("Sources", sourceList(sources)),
  ].join("");
  const aside = mediaFigures(media) || `<div class="scope-note">No public media are linked to this work.</div>`;
  return {
    title: work.title,
    label: work.workType || "Work",
    badges: `${typeBadge(work.workType)}${periodBadge(work.period)}${certaintyBadge(work.certainty)}`,
    facts: `${fact("Year", work.year)}${fact("Type", work.workType)}${fact("Period", work.period)}${fact("Certainty", humanize(work.certainty))}${fact("Public scope", humanize(work.publicScope))}`,
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
    badges: `${typeBadge(event.category || event.eventType)}${periodBadge(event.period)}`,
    facts: `${fact("Date", event.displayDate || event.dateStart)}${fact("Precision", humanize(event.datePrecision))}${fact("Place", event.placeDisplay)}${fact("Category", humanize(event.category))}`,
    main: [
      section("Event", publicText(event.longDescription, event.shortDescription)),
      section("People", entityList(people, "person", (item) => humanize(item.primaryRole))),
      section("Works", entityList(works, "work", (item) => [item.year, item.workType].filter(Boolean).join(" · "))),
      section("Organizations", entityList(organizations, "organization", (item) => (item.types || []).map(humanize).join(", "))),
      section("Places", entityList(places, "place", (item) => [item.city, item.country].filter(Boolean).join(", "))),
      section("Sources", sourceList(sources)),
    ].join(""),
    aside: mediaFigures(media),
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
    badges: `${typeBadge(place.placeType)}${periodBadge(place.period)}`,
    facts: `${fact("City", place.city)}${fact("Region", place.region)}${fact("Country", place.country)}${fact("Place type", humanize(place.placeType))}${fact("Map precision", humanize(place.mapPrecision))}${fact("Coordinates", place.latitude && place.longitude ? `${place.latitude}, ${place.longitude}` : "")}`,
    main: [
      section("About this place", publicText(place.publicNote)),
      section("Documented events", entityList(events, "event", (item) => item.displayDate || item.dateStart)),
      section("People", entityList(people, "person", (item) => humanize(item.primaryRole))),
      section("Sources", sourceList(sources)),
    ].join(""),
    aside: mediaFigures(media),
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

function documentGallery(media, allMedia) {
  const paths = [...new Set(media.assetPaths || [])].filter(Boolean);
  if (media.mediaType !== "document_gallery" || paths.length < 2) return "";
  const items = paths.map((path, index) => {
    const fileName = String(path).split("/").pop();
    const member = allMedia.find((item) => (
      item.id !== media.id
      && (item.assetPath === path || (item.assetPaths || []).includes(path))
    )) || allMedia.find((item) => (
      item.id !== media.id
      && (item.assetPaths || []).some((candidate) => String(candidate).split("/").pop() === fileName)
    ));
    const title = member?.title || `Gallery image ${index + 1}`;
    const caption = member?.publicCaption || member?.description || `Image ${index + 1} of ${paths.length} in this documentary gallery.`;
    const credit = member?.publicCreditLine;
    return `
      <figure class="record-gallery__item">
        <a class="record-gallery__image" href="${escapeHtml(path)}" target="_blank" rel="noreferrer" aria-label="Open full image: ${escapeHtml(title)}">
          <img src="${escapeHtml(path)}" alt="${escapeHtml(member?.altText || title)}" loading="lazy" decoding="async">
          <span>Open full image <span aria-hidden="true">↗</span></span>
        </a>
        <figcaption>
          <strong>${member ? `<a href="${recordUrl("media", member.id)}">${escapeHtml(title)}</a>` : escapeHtml(title)}</strong>
          <p>${escapeHtml(caption)}</p>
          ${credit ? `<small>${escapeHtml(credit)}</small>` : ""}
        </figcaption>
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
  const external = safeExternalUrl(media.externalUrl);
  const gallery = documentGallery(media, data.media);
  return {
    title: media.title,
    label: "Media record",
    badges: `${typeBadge(media.mediaType)}${periodBadge(media.period)}${rightsBadge(media.rightsStatus, media.rightsNote)}`,
    facts: `${fact("Media type", humanize(media.mediaType))}${fact("Category", humanize(media.category))}${fact("Items", gallery ? media.assetPaths.length : "")}${fact("Storage", storageLabel(media.storageType))}${fact("Gallery scope", galleryScopeLabel(media.galleryStatus))}${fact("Rights status", rightsLabel(media.rightsStatus, media.rightsNote))}`,
    main: [
      section("Caption and context", `${publicText(media.publicCaption, media.description)}${media.publicImageText ? `<p><strong>Image text:</strong> ${escapeHtml(media.publicImageText)}</p>` : ""}${external ? `<p><a class="button button--ghost button--small" href="${escapeHtml(external)}" target="_blank" rel="noreferrer">Open at source institution <span aria-hidden="true">↗</span></a></p>` : ""}`),
      gallery ? section(`Gallery · ${media.assetPaths.length} images`, gallery, "record-section--gallery") : "",
      section("Rights", rightsPanel(media)),
      section("Related works", entityList(works, "work", (item) => [item.year, item.workType].filter(Boolean).join(" · "))),
      section("Timeline", entityList(events, "event", (item) => item.displayDate || item.dateStart)),
      section("Places", entityList(places, "place", (item) => [item.city, item.country].filter(Boolean).join(", "))),
      section("Organizations", entityList(organizations, "organization", (item) => (item.types || []).map(humanize).join(", "))),
      section("Sources and provenance", sourceList(sources)),
    ].join(""),
    aside: `<figure class="record-media">${mediaPreview(media, { eager: true })}<figcaption>${escapeHtml(media.publicCreditLine || media.publicCaption || media.title)}</figcaption></figure>`,
  };
}

function renderPerson(person, data, indexes) {
  const works = related(person.workIds, indexes.works);
  const events = related(person.timelineEventIds, indexes.timelineEvents);
  const places = related(person.placeIds, indexes.places);
  const sources = related(person.sourceIds, indexes.sources);
  const variants = related(person.nameVariantIds, indexes.personNameVariants);
  const authority = safeExternalUrl(person.authorityUrl);
  const displayedRoles = [person.primaryRole, ...(person.roles || [])].filter((role, index, roles) => (
    role && roles.findIndex((candidate) => String(candidate).toLowerCase() === String(role).toLowerCase()) === index
  ));
  return {
    title: person.displayName,
    label: "Person",
    badges: displayedRoles.map(typeBadge).join(""),
    facts: `${fact("Authorized name", person.authorizedName)}${fact("Primary role", humanize(person.primaryRole))}${fact("Roles", (person.roles || []).map(humanize))}`,
    main: [
      authority ? section("Authority record", `<p><a href="${escapeHtml(authority)}" target="_blank" rel="noreferrer">Open authority record <span aria-hidden="true">↗</span></a></p>`) : "",
      section("Works", entityList(works, "work", (item) => [item.year, item.workType].filter(Boolean).join(" · "))),
      section("Attested name variants", variants.length ? `<ul class="entity-list">${variants.map((item) => `<li><span><strong>${escapeHtml(item.variantName)}</strong><br><small>${escapeHtml(item.publicNote || item.attestedWording || "")}</small></span>${typeBadge(item.variantType)}</li>`).join("")}</ul>` : ""),
      section("Timeline", entityList(events, "event", (item) => item.displayDate || item.dateStart)),
      section("Places", entityList(places, "place", (item) => [item.city, item.country].filter(Boolean).join(", "))),
      section("Sources", sourceList(sources)),
    ].join(""),
    aside: `<div class="scope-note">Historical credit forms and role attributions are presented on individual work records, where they can be read with their source context.</div>`,
  };
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
      section("Works", entityList(works, "work", (item) => [item.year, item.workType].filter(Boolean).join(" · "))),
      section("Timeline", entityList(events, "event", (item) => item.displayDate || item.dateStart)),
      section("Sources", sourceList(sources)),
    ].join(""),
    aside: `<div class="scope-note">Organization links are induced from approved public records and their documented contributions.</div>`,
  };
}

function renderSource(source, data, indexes) {
  const works = related(source.workIds, indexes.works);
  const media = related(source.mediaIds, indexes.media);
  const events = related(source.timelineEventIds, indexes.timelineEvents);
  const places = related(source.placeIds, indexes.places);
  const people = related(source.personIds, indexes.people);
  const organizations = related(source.organizationIds, indexes.organizations);
  const external = safeExternalUrl(source.url);
  return {
    title: source.title || source.shortCitation,
    label: "Source",
    badges: `${typeBadge(source.sourceType)}${typeBadge(source.reliability)}${typeBadge(source.sourceStatus)}`,
    facts: `${fact("Creator", source.creator)}${fact("Date", source.date)}${fact("Publication", source.publication)}${fact("Repository", source.repository)}${fact("Access date", source.accessDate)}${fact("Reliability", humanize(source.reliability))}`,
    main: [
      section("Citation", `<p class="lead">${escapeHtml(source.fullCitation || source.shortCitation)}</p>${external ? `<p><a class="button button--ghost button--small" href="${escapeHtml(external)}" target="_blank" rel="noreferrer">Open source <span aria-hidden="true">↗</span></a></p>` : ""}`),
      section("Supported works", entityList(works, "work", (item) => [item.year, item.workType].filter(Boolean).join(" · "))),
      section("Media", entityList(media, "media", (item) => humanize(item.mediaType))),
      section("Timeline", entityList(events, "event", (item) => item.displayDate || item.dateStart)),
      section("Places", entityList(places, "place", (item) => [item.city, item.country].filter(Boolean).join(", "))),
      section("People", entityList(people, "person", (item) => humanize(item.primaryRole))),
      section("Organizations", entityList(organizations, "organization", (item) => (item.types || []).map(humanize).join(", "))),
    ].join(""),
    aside: `<div class="scope-note">Stable source ID: <strong>${escapeHtml(source.id)}</strong><br>This record is included because it is approved and reachable from the public research graph.</div>`,
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
  const tableNames = [
    "people", "organizations", "sources", "media", "works", "films", "songs", "otherWorks",
    "titleVariants", "workRelations", "timelineEvents", "places", "contributions", "personNameVariants",
  ];
  const data = await loadTables(tableNames);
  const indexes = Object.fromEntries(tableNames.map((name) => [name, indexById(data[name])]));
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
      <div class="shell record-layout">
        <div>${view.main || `<div class="empty-state"><p>No additional public detail is available.</p></div>`}</div>
        <aside>${view.aside || ""}</aside>
      </div>
    </section>`;
} catch (error) {
  target.className = "shell";
  renderError(target, error);
}
