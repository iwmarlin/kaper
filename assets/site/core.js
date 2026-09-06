const DATA_ROOT = "data/public/v1/";
const SITE_INDEX_ROOT = "data/site/indexes/";
let imageDerivatives = Object.freeze({});

export function registerImageDerivatives(mapping) {
  imageDerivatives = mapping && typeof mapping === "object" ? mapping : Object.freeze({});
}

export const TABLE_FILES = Object.freeze({
  people: "people.json",
  organizations: "organizations.json",
  sources: "sources.json",
  media: "media.json",
  works: "works.json",
  films: "films.json",
  songs: "songs.json",
  otherWorks: "other-works.json",
  titleVariants: "title-variants.json",
  workRelations: "work-relations.json",
  timelineEvents: "timeline-events.json",
  places: "places.json",
  contributions: "contributions.json",
  personNameVariants: "person-name-variants.json",
});

const tableCache = new Map();
const siteIndexCache = new Map();
let manifestPromise;

const SITE_INDEX_FILES = Object.freeze({
  works: "works.json",
  people: "people.json",
  media: "media.json",
  sources: "sources.json",
});

export function loadManifest() {
  if (!manifestPromise) {
    const url = new URL(`${DATA_ROOT}manifest.json`, document.baseURI);
    // The manifest is the small, mutable pointer to the current public data
    // release. Revalidate it on every page load; individual tables can then be
    // cached safely under a content-derived URL.
    manifestPromise = fetch(url, { cache: "no-cache" }).then(async (response) => {
      if (!response.ok) throw new Error(`Could not load public manifest (${response.status})`);
      return response.json();
    });
  }
  return manifestPromise;
}

function tableVersion(manifest, filename) {
  const file = manifest?.files?.find((item) => item.file === filename);
  return typeof file?.sha256 === "string" ? file.sha256.slice(0, 12) : "";
}

export async function loadTable(name) {
  if (!TABLE_FILES[name]) throw new Error(`Unknown public table: ${name}`);
  if (!tableCache.has(name)) {
    const filename = TABLE_FILES[name];
    tableCache.set(
      name,
      loadManifest().then(async (manifest) => {
        const url = new URL(`${DATA_ROOT}${filename}`, document.baseURI);
        const version = tableVersion(manifest, filename);
        if (version) url.searchParams.set("v", version);
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Could not load ${filename} (${response.status})`);
        }
        const payload = await response.json();
        if (!Array.isArray(payload.records)) {
          throw new Error(`${filename} has an invalid public payload`);
        }
        return payload.records;
      }),
    );
  }
  return tableCache.get(name);
}

export async function loadTables(names) {
  const entries = await Promise.all(
    names.map(async (name) => [name, await loadTable(name)]),
  );
  return Object.fromEntries(entries);
}

/** Load the small, presentation-oriented payload for one browse page. */
export async function loadSiteIndex(name) {
  const filename = SITE_INDEX_FILES[name];
  if (!filename) throw new Error(`Unknown site index: ${name}`);
  if (!siteIndexCache.has(name)) {
    const url = new URL(`${SITE_INDEX_ROOT}${filename}`, document.baseURI);
    siteIndexCache.set(name, fetch(url, { cache: "no-cache" }).then(async (response) => {
      if (!response.ok) throw new Error(`Could not load catalogue index ${filename} (${response.status})`);
      const payload = await response.json();
      if (!Array.isArray(payload.records) || payload.count !== payload.records.length) {
        throw new Error(`${filename} has an invalid catalogue-index payload`);
      }
      return payload;
    }));
  }
  return siteIndexCache.get(name);
}

export function indexById(records) {
  return new Map(records.map((record) => [record.id, record]));
}

export function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function safeExternalUrl(value) {
  if (!value) return null;
  if (/[\r\n]/.test(String(value))) return null;
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}

export function recordUrl(type, id) {
  return `records/${encodeURIComponent(type)}/${encodeURIComponent(id)}/`;
}

export function humanize(value = "") {
  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function certaintyBadge(certainty) {
  if (!certainty) return "";
  const key = String(certainty).toLowerCase().replaceAll(" ", "_");
  return `<span class="badge badge--certainty badge--${escapeHtml(key)}">${escapeHtml(humanize(certainty))}</span>`;
}

export const PERIOD_META = Object.freeze({
  warsaw: Object.freeze({ label: "Warsaw", range: "1902–1926" }),
  european: Object.freeze({ label: "European", range: "1926–1934" }),
  hollywood: Object.freeze({ label: "Hollywood", range: "1935–1939" }),
});
export const PERIOD_ORDER = Object.freeze(Object.keys(PERIOD_META));

export function periodValues(value) {
  const raw = Array.isArray(value)
    ? value
    : (value && typeof value === "object"
      ? (value.periods || [value.period])
      : [value]);
  return [...new Set(raw
    .filter(Boolean)
    .map((item) => String(item).toLowerCase().replaceAll(" ", "_")))];
}

export function periodLabel(period) {
  const key = periodValues(period)[0];
  const meta = PERIOD_META[key];
  return meta ? `${meta.label} · ${meta.range}` : humanize(period);
}

export function matchesPeriod(record, selectedPeriod) {
  return !selectedPeriod || periodValues(record).includes(selectedPeriod);
}

export function periodBadge(period) {
  return periodValues(period)
    .map((key) => {
      const meta = PERIOD_META[key];
      const label = meta?.label || humanize(key);
      const fullLabel = periodLabel(key);
      return `<span class="badge badge--period" title="${escapeHtml(fullLabel)}" aria-label="${escapeHtml(fullLabel)}">${escapeHtml(label)}</span>`;
    })
    .join("");
}

// A language was being drawn with the period badge — the one that says Warsaw,
// European, Hollywood. Given "de" it produced a gold plaque reading "De", with
// "De" as its accessible name too, so a reader was told a two-letter word and
// nothing about what it meant. Languages get their own mark, and it says the
// language in full.
const LANGUAGE_NAMES = Object.freeze({
  de: "German",
  en: "English",
  fr: "French",
  pl: "Polish",
  it: "Italian",
  es: "Spanish",
  cs: "Czech",
  hu: "Hungarian",
  nl: "Dutch",
  ru: "Russian",
  sv: "Swedish",
  da: "Danish",
  yi: "Yiddish",
});

export function languageName(code) {
  const key = String(code || "").toLowerCase().trim();
  return LANGUAGE_NAMES[key] || humanize(code);
}

export function languageBadge(code) {
  if (!code) return "";
  const name = languageName(code);
  return `<span class="badge badge--language" title="${escapeHtml(name)}" aria-label="${escapeHtml(name)}">${escapeHtml(name)}</span>`;
}

export function typeBadge(type) {
  if (!type) return "";
  return `<span class="badge badge--type">${escapeHtml(humanize(type))}</span>`;
}

export function scopeBadge(scope) {
  if (scope !== "context_only") return "";
  return '<span class="badge badge--context">Context record</span>';
}

// Every source in the archive carries an assessment of how much weight it can
// bear and whether its own attribution was accepted without reservation. Both
// judgements were recorded and neither was ever shown, so a YouTube upload and
// a National Digital Archive negative were cited on identical rows. The
// assessment is stated in full on the source's own record, where a reader is
// weighing that source; in the citation lists on other records only the
// exception is flagged, because a mark carried by three quarters of the rows
// tells a reader nothing.
const SOURCE_RELIABILITY_LABELS = Object.freeze({
  high: "High",
  medium: "Medium",
  low: "Low",
});
const SOURCE_STATUS_LABELS = Object.freeze({
  verified: "Verified",
  verified_with_attribution_note: "Verified, with an attribution note",
});

export function sourceReliabilityLabel(reliability) {
  if (!reliability) return "";
  const key = String(reliability).toLowerCase().trim();
  return SOURCE_RELIABILITY_LABELS[key] || humanize(reliability);
}

export function sourceStatusLabel(status) {
  if (!status) return "";
  const key = String(status).toLowerCase().trim();
  return SOURCE_STATUS_LABELS[key] || humanize(status);
}

// Authority control is recorded as a stack of "SCHEME: url" lines. The person
// card has parsed it since it was written; the organization card never did, so
// twenty-one organizations carried complete LCNAF, GND, VIAF, ISNI and BnF
// records that no reader could reach. One parser now serves both.
export function authorityLinkList(value) {
  return String(value || "")
    .split(/\r?\n/)
    .map((entry) => {
      const match = entry.trim().match(/^([^:]+):\s*(https?:\/\/\S+)$/);
      if (!match) return null;
      const url = safeExternalUrl(match[2]);
      return url ? { label: match[1], url } : null;
    })
    .filter(Boolean);
}

export function sourceReliabilityBadge(reliability) {
  if (String(reliability || "").toLowerCase().trim() !== "low") return "";
  return '<span class="badge badge--reliability badge--reliability-low" title="Cited for the record it documents; not treated as independent authority.">Low reliability</span>';
}

const RIGHTS_LABELS = Object.freeze({
  ok: "Rights documented",
  public_domain: "Public domain",
  permission_granted: "Permission granted",
  permission_needed_or_fair_use_claimed: "Rights not cleared",
  external_content_not_rehosted: "External content · not hosted",
  copyright_undetermined: "Copyright undetermined",
  restricted: "Restricted use",
  mixed_rights: "Mixed rights",
});

export function rightsLabel(status, note = "") {
  if (!status) return "Rights information";
  const key = String(status).toLowerCase().trim().replaceAll(" ", "_");
  const normalizedNote = String(note).toLowerCase();
  if (key === "ok" && /public[ -]domain|rightsstatements\.org\/vocab\/noc/.test(normalizedNote)) return "Public domain";
  if (key === "ok" && /reproduced by permission|permission (?:was )?granted|used with permission/.test(normalizedNote)) return "Permission granted";
  if (key === "permission_needed_or_fair_use_claimed" && /fair[ -]use/.test(normalizedNote)) return "Fair use";
  return RIGHTS_LABELS[key] || humanize(status);
}

export function rightsBadge(status, note = "") {
  if (!status) return "";
  const key = String(status).toLowerCase().trim().replaceAll(" ", "_");
  return `<span class="badge badge--rights badge--${escapeHtml(key)}">${escapeHtml(rightsLabel(status, note))}</span>`;
}

export function mediaIsFairUse(media) {
  return Boolean(
    media?.assetPath
    && String(media.rightsStatus || "").toLowerCase().trim().replaceAll(" ", "_") === "permission_needed_or_fair_use_claimed"
    && /fair[ -]use/i.test(String(media.rightsNote || ""))
  );
}

export function mediaRightsLabel(media) {
  if (mediaIsFairUse(media)) return "Fair use";
  return rightsLabel(media?.rightsStatus, media?.rightsNote);
}

export function mediaRightsBadge(media) {
  if (!media?.rightsStatus) return "";
  const key = String(media.rightsStatus).toLowerCase().trim().replaceAll(" ", "_");
  return `<span class="badge badge--rights badge--${escapeHtml(key)}">${escapeHtml(mediaRightsLabel(media))}</span>`;
}

function conciseRightsRationale(note = "") {
  const sentences = String(note).match(/[^.!?]+[.!?]+|[^.!?]+$/g)?.map((sentence) => sentence.trim()).filter(Boolean) || [];
  const preferred = sentences.find((sentence) => (
    /low[- ]resolution|reduced[- ]resolution/i.test(sentence)
    && /scholarly|contextual|identification|criticism|commentary|documentation|discussion/i.test(sentence)
    && /use|used|published|approved|reproduce|shown|treat/i.test(sentence)
  ));
  return preferred || sentences.find((sentence) => (
    /fair[ -]use|low[- ]resolution|reduced[- ]resolution|scholarly|contextual|identification|criticism|documentation/i.test(sentence)
    && /use|used|published|approved|reproduce|shown|treat/i.test(sentence)
  )) || sentences[0] || "";
}

function creditIncludesFairUseRationale(credit = "") {
  return /low[- ]resolution|reduced[- ]resolution/i.test(credit)
    && /scholarly|contextual|identification|criticism|commentary|documentation|discussion/i.test(credit);
}

export function renderMediaDisclosure(media, sources = [], {
  compact = false,
  fairUseResolutionLabel = "Reduced-resolution local reference",
  includeCaption = true,
  includeCredit = true,
  includeFullRightsNote = true,
  includeRationale = true,
  includeResolutionLabel = true,
  includeRightsBadge = true,
  includeTitle = true,
  includeSource = true,
} = {}) {
  if (!media) return "";
  const source = sources.find((item) => item?.id) || null;
  const sourceExternal = safeExternalUrl(media.externalUrl)
    || safeExternalUrl(source?.primaryUrl)
    || safeExternalUrl(source?.accessUrl);
  const sourceHref = sourceExternal || (source?.id ? recordUrl("source", source.id) : "");
  const sourceLabel = source?.id ? `Source ${source.id}` : "Original source";
  const sourceAttributes = sourceExternal ? ' target="_blank" rel="noreferrer"' : "";
  const caption = media.publicCaption || media.description || "";
  const credit = media.publicCreditLine || "";
  const rationale = media.rightsNote || "";
  const conciseRationale = mediaIsFairUse(media) && !creditIncludesFairUseRationale(credit)
    ? conciseRightsRationale(rationale)
    : "";
  const fullRationale = rationale && rationale !== conciseRationale;
  const metaContent = [
    includeRightsBadge ? mediaRightsBadge(media) : "",
    mediaIsFairUse(media) && includeResolutionLabel ? `<span class="media-disclosure__resolution">${escapeHtml(fairUseResolutionLabel)}</span>` : "",
    includeSource && sourceHref ? `<a href="${escapeHtml(sourceHref)}"${sourceAttributes}>${escapeHtml(sourceLabel)}${sourceExternal ? ' <span aria-hidden="true">↗</span>' : ""}</a>` : "",
  ].filter(Boolean).join("");
  return `<div class="media-disclosure${compact ? " media-disclosure--compact" : ""}">
    ${includeTitle ? `<a class="media-disclosure__title" href="${recordUrl("media", media.id)}">${escapeHtml(media.title || media.id)}</a>` : ""}
    ${includeCaption && caption && caption !== media.title ? `<p class="media-disclosure__caption">${escapeHtml(caption)}</p>` : ""}
    ${includeCredit && credit ? `<p class="media-disclosure__credit"><strong>Credit:</strong> ${escapeHtml(credit)}</p>` : ""}
    ${metaContent ? `<div class="media-disclosure__meta">${metaContent}</div>` : ""}
    ${compact && includeRationale && conciseRationale ? `<p class="media-disclosure__rationale"><strong>Use rationale:</strong> ${escapeHtml(conciseRationale)}</p>` : ""}
    ${compact && includeRationale && includeFullRightsNote && fullRationale ? `<details class="media-disclosure__details"><summary>Full rights and use note</summary><p>${escapeHtml(rationale)}</p></details>` : ""}
    ${!compact && includeRationale && rationale ? `<p class="media-disclosure__rationale">${mediaIsFairUse(media) ? "<strong>Use rationale:</strong> " : ""}${escapeHtml(rationale)}</p>` : ""}
  </div>`;
}

export function storageLabel(storageType) {
  const labels = {
    local: "Local archival copy",
    multi_local_assets: "Curated local collection",
    external: "External reference",
  };
  return labels[storageType] || humanize(storageType);
}

export function galleryScopeLabel(status) {
  const labels = {
    selected: "Curated selection",
    eligible: "Available in the archive",
    detail_only: "Record detail only",
    external_link_only: "External reference",
  };
  return labels[status] || humanize(status);
}

export function formatDate(value) {
  if (!value) return "";
  const match = String(value).match(/^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?/);
  if (!match) return value;
  const [, year, month, day] = match;
  if (!month) return year;
  const date = new Date(Date.UTC(Number(year), Number(month) - 1, Number(day || 1)));
  return new Intl.DateTimeFormat("en-GB", {
    day: day ? "numeric" : undefined,
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(date);
}

export function normalizeSearch(value = "") {
  // Search must not turn on punctuation: a reader types "cosi cosa" for
  // "Così, cosa" and "gods chillun" for "God's Chillun". Apostrophes close up,
  // every other separator becomes one break, and diacritics are stripped.
  return String(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/['’‘`´]/g, "")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim();
}

// German titles are written both ways: Vergi\u00dfmeinnicht and Vergissmeinnicht,
// M\u00fchlhardt and Muehlhardt. Stripping the diacritic answers only half of that,
// so an index carries the transliterated form beside the plain one and a reader
// finds the record whichever spelling is typed.
const GERMAN_FOLDINGS = [
  [/\u00df/g, "ss"],
  [/\u00e4/g, "ae"],
  [/\u00f6/g, "oe"],
  [/\u00fc/g, "ue"],
  [/\u00c4/g, "Ae"],
  [/\u00d6/g, "Oe"],
  [/\u00dc/g, "Ue"],
];

export function indexText(value = "") {
  const plain = normalizeSearch(value);
  let transliterated = String(value);
  for (const [pattern, replacement] of GERMAN_FOLDINGS) {
    transliterated = transliterated.replace(pattern, replacement);
  }
  const folded = normalizeSearch(transliterated);
  return folded === plain ? plain : `${plain} ${folded}`;
}

// One ordering for the whole archive. The material is German, French, Polish
// and English at once, so browsing lists must not each fall back to a
// different collation: names and titles are compared with the same rules, and
// punctuation — the apostrophes, commas and guillemets that open many of these
// titles — is ignored rather than allowed to decide the order.
const TEXT_COLLATOR = new Intl.Collator("pl", {
  numeric: true,
  ignorePunctuation: true,
});

export function compareText(left, right) {
  return TEXT_COLLATOR.compare(String(left ?? ""), String(right ?? ""));
}

/** Filing title: the sort form when one is recorded, the display title otherwise. */
export function sortKey(record) {
  return String(record?.sortTitle || record?.title || "");
}

/** Filing name: the inverted form when one is recorded, the display name otherwise. */
export function nameKey(record) {
  return String(record?.sortName || record?.displayName || "");
}

/**
 * Free-text index for one Work.
 *
 * A reader searches for what the record shows: the title in any of the forms
 * the sources print, and the people credited on it — the singer and the
 * conductor as much as the composer. Credits carried by an organization are
 * left out on purpose. A label or an ensemble belongs to one issue of one
 * recording, not to the work, and a house name such as Metro-Goldwyn-Mayer or
 * Alrobi would answer a third of the catalogue at once; those records have
 * pages of their own that gather their works properly.
 */
export function workSearchText(work, lookup = {}) {
  const {
    peopleById = new Map(),
    subtypeByWorkId = new Map(),
    contributionsById = new Map(),
    titleVariantsById = new Map(),
  } = lookup;
  const subtype = subtypeByWorkId.get(work.id) || {};
  const variantIds = [
    ...getIds(work, "titleVariantIds"),
    ...getIds(subtype, "titleVariantIds"),
  ];
  const variantTitles = [...new Set(variantIds)]
    .map((id) => titleVariantsById.get(id))
    .filter(Boolean)
    .flatMap((variant) => [variant.variantTitle, variant.titleAsSource]);

  const creditNames = [];
  for (const contributionId of getIds(work, "contributionIds")) {
    const contribution = contributionsById.get(contributionId);
    const personIds = getIds(contribution, "personIds");
    if (!personIds.length) continue;
    creditNames.push(contribution.nameAsPrinted);
    for (const personId of personIds) {
      const person = peopleById.get(personId);
      if (person) creditNames.push(person.displayName, person.authorizedName);
    }
  }
  for (const person of getIds(work, "personIds").map((id) => peopleById.get(id))) {
    if (person) creditNames.push(person.displayName);
  }

  return indexText([
    work.title,
    work.sortTitle,
    ...variantTitles,
    work.year,
    work.workType,
    ...periodValues(work),
    ...creditNames,
    subtype.genre,
    subtype.lyricistAsPrinted,
  ].filter(Boolean).join(" "));
}

// How a person enters this archive. The role fields describe who someone was;
// these families describe what the sources credit them with here, which is what
// a reader filters by. People documented only through dated events — a teacher,
// a relative, a studio head Kaper worked under — keep a family of their own so
// that no filter hides them.
export const PERSON_FUNCTIONS = Object.freeze({
  creators: Object.freeze({
    label: "Creators",
    roles: Object.freeze([
      "composer",
      "lyricist",
      "arranger",
      "music_contributor_role_unresolved",
    ]),
    described: Object.freeze([
      "composer",
      "lyricist",
      "arranger",
      "poet",
      "satirist",
      "screenwriter",
      "writer",
    ]),
  }),
  performers: Object.freeze({
    label: "Performers",
    roles: Object.freeze(["performer", "conductor", "actor"]),
    described: Object.freeze([
      "performer",
      "singer",
      "pianist",
      "violinist",
      "conductor",
      "bandleader",
      "actor",
      "comedian",
    ]),
  }),
  film: Object.freeze({
    label: "Film production",
    roles: Object.freeze([
      "film_director",
      "music_director",
      "producer",
      "associate_producer",
      "dialogue_director",
    ]),
    described: Object.freeze([
      "film director",
      "producer",
      "studio executive",
      "studio founder",
      "animator",
      "talent agent",
    ]),
  }),
  documented: Object.freeze({
    label: "Documented without credits",
    roles: Object.freeze([]),
    described: Object.freeze([]),
  }),
});

export const PERSON_FUNCTION_ORDER = Object.freeze(Object.keys(PERSON_FUNCTIONS));

const FUNCTION_BY_ROLE = new Map(
  Object.entries(PERSON_FUNCTIONS).flatMap(([key, family]) =>
    family.roles.map((role) => [role, key])),
);

const FUNCTION_BY_DESCRIBED_ROLE = new Map(
  Object.entries(PERSON_FUNCTIONS).flatMap(([key, family]) =>
    family.described.map((role) => [role, key])),
);

export function functionLabel(key) {
  return PERSON_FUNCTIONS[key]?.label || humanize(key);
}

/**
 * The families a person belongs to, in a stable order.
 *
 * Credits come first, because they are what the sources prove. Someone the
 * archive holds only through a dated event still has a place: a pianist who
 * played at the school concert, a producer Kaper worked under, are filed by
 * the role their record states. Only a person with neither — Kaper's mother,
 * say — falls to the residual family, which exists so that no filter hides
 * anybody.
 */
export function personFunctions(person, contributionsById = new Map()) {
  const credited = new Set();
  for (const contributionId of getIds(person, "contributionIds")) {
    const contribution = contributionsById.get(contributionId);
    if (!contribution) continue;
    const family = FUNCTION_BY_ROLE.get(contribution.role);
    if (family) credited.add(family);
  }
  if (credited.size) return PERSON_FUNCTION_ORDER.filter((key) => credited.has(key));

  const described = new Set();
  const roles = person?.roles?.length
    ? person.roles
    : [person?.primaryRole].filter(Boolean);
  for (const role of roles) {
    const family = FUNCTION_BY_DESCRIBED_ROLE.get(role);
    if (family) described.add(family);
  }
  if (!described.size) described.add("documented");
  return PERSON_FUNCTION_ORDER.filter((key) => described.has(key));
}

export function debounce(callback, delay = 120) {
  let timer;
  return (...args) => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => callback(...args), delay);
  };
}

export function getIds(record, key) {
  return Array.isArray(record?.[key]) ? record[key] : [];
}

export function resolveIds(record, key, index) {
  return getIds(record, key).map((id) => index.get(id)).filter(Boolean);
}

export function renderLoading(target, label = "Loading public data…") {
  target.innerHTML = `<div class="loading" role="status"><span class="loading__mark" aria-hidden="true"></span><span>${escapeHtml(label)}</span></div>`;
}

export function renderError(target, error) {
  console.error(error);
  target.innerHTML = `
    <section class="notice notice--error" role="alert">
      <p class="eyebrow">Data unavailable</p>
      <h2>This section could not be loaded.</h2>
      <p>${escapeHtml(error?.message || "Unknown error")}</p>
      <p>When viewing locally, run the site through a static web server rather than opening the HTML file directly.</p>
    </section>`;
}

export function updateMeta({ title, description }) {
  if (title) {
    document.title = `${title} — Bronisław Kaper, 1902–1939`;
    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle) ogTitle.content = document.title;
  }
  if (description) {
    const meta = document.querySelector('meta[name="description"]');
    if (meta) meta.content = description;
    const ogDescription = document.querySelector('meta[property="og:description"]');
    if (ogDescription) ogDescription.content = description;
  }
}

export function setCanonicalRecordUrl(type, id) {
  const canonicalUrl = `https://iwmarlin.github.io/kaper/${recordUrl(type, id)}`;
  let canonical = document.querySelector('link[rel="canonical"]');
  if (!canonical) {
    canonical = document.createElement("link");
    canonical.rel = "canonical";
    document.head.append(canonical);
  }
  canonical.href = canonicalUrl;
  let ogUrl = document.querySelector('meta[property="og:url"]');
  if (!ogUrl) {
    ogUrl = document.createElement("meta");
    ogUrl.setAttribute("property", "og:url");
    document.head.append(ogUrl);
  }
  ogUrl.content = canonicalUrl;
}

const NAV_ITEMS = [
  ["home", "index.html", "Home"],
  ["works", "works.html", "Works"],
  ["people", "people.html", "People"],
  ["timeline", "life.html", "Timeline"],
  ["map", "map.html", "Map"],
  ["media", "media.html", "Media"],
];

export function mountSiteChrome(activePage) {
  const header = document.querySelector("[data-site-header]");
  if (header) {
    header.innerHTML = `
      <div class="site-header__inner shell">
        <a class="brand" href="index.html" aria-label="Bronisław Kaper research archive home">
          <span class="brand__monogram" aria-hidden="true">BK</span>
          <span class="brand__text">
            <strong>Bronisław Kaper</strong>
            <small>A source-based archive · 1902–1939</small>
          </span>
        </a>
        <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-navigation">
          <span></span><span></span><span></span><span class="sr-only">Toggle navigation</span>
        </button>
        <nav class="site-nav" id="site-navigation" aria-label="Primary navigation">
          ${NAV_ITEMS.map(
            ([key, href, label]) => `<a href="${href}"${key === activePage ? ' aria-current="page"' : ""}>${label}</a>`,
          ).join("")}
        </nav>
      </div>`;

    const button = header.querySelector(".nav-toggle");
    const nav = header.querySelector(".site-nav");
    if (button && nav) {
      const mobileNavigation = window.matchMedia?.("(max-width: 680px)");
      const isOpen = () => button.getAttribute("aria-expanded") === "true";
      const setOpen = (open, { returnFocus = false } = {}) => {
        button.setAttribute("aria-expanded", String(open));
        nav.classList.toggle("site-nav--open", open);
        if (returnFocus) button.focus();
      };

      button.addEventListener("click", () => setOpen(!isOpen()));

      nav.addEventListener("click", (event) => {
        if (event.target?.closest?.("a")) setOpen(false);
      });

      document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape" || !isOpen()) return;
        event.preventDefault();
        setOpen(false, { returnFocus: true });
      });

      const closeAboveMobileWidth = (event) => {
        if (!event.matches) setOpen(false);
      };
      if (mobileNavigation?.addEventListener) {
        mobileNavigation.addEventListener("change", closeAboveMobileWidth);
      } else {
        mobileNavigation?.addListener?.(closeAboveMobileWidth);
      }
    }
  }

  const footer = document.querySelector("[data-site-footer]");
  if (footer) {
    footer.innerHTML = `
      <div class="shell site-footer__grid">
        <div>
          <p class="eyebrow">Research archive</p>
          <p class="site-footer__title">Bronisław Kaper, documented through 1939</p>
          <p>Public data are generated from a curated relational research database and preserved as versioned static JSON.</p>
        </div>
        <div>
          <p class="site-footer__heading">Explore</p>
          <ul class="plain-list">
            ${NAV_ITEMS.slice(1).map(([, href, label]) => `<li><a href="${href}">${label}</a></li>`).join("")}
          </ul>
        </div>
        <div>
          <p class="site-footer__heading">Editorial scope</p>
          <p>Attributions and uncertain evidence are explicitly qualified. Media rights statements appear with each published item.</p>
          <a href="data/public/v1/manifest.json">Public data manifest</a>
        </div>
      </div>
      <div class="shell site-footer__bottom">
        <span>© ${new Date().getFullYear()} Bronisław Kaper Research Archive</span>
        <span>Scholarly use · Sources cited at record level</span>
      </div>`;
  }
}

export function renderSourceCitation(source) {
  const external = safeExternalUrl(source.primaryUrl) || safeExternalUrl(source.accessUrl);
  return `
    <li class="citation" id="source-${escapeHtml(source.id)}">
      <a class="citation__id" href="${recordUrl("source", source.id)}" aria-label="Open source record ${escapeHtml(source.id)}">${escapeHtml(source.id)}</a>
      <div>
        <p>${escapeHtml(source.fullCitation || source.shortCitation || source.title)}</p>
        ${external ? `<a href="${escapeHtml(external)}" target="_blank" rel="noreferrer">Open source <span aria-hidden="true">↗</span></a>` : ""}
      </div>
    </li>`;
}

export function responsiveImage(assetPath, alt, {
  className = "",
  eager = false,
  sizes = "(max-width: 680px) calc(100vw - 2rem), (max-width: 1100px) 48vw, 28rem",
} = {}) {
  const title = escapeHtml(alt || "Image");
  const imageClass = className ? ` class="${escapeHtml(className)}"` : "";
  const profile = imageDerivatives[assetPath];
  if (!profile) {
    return `<img${imageClass} src="${escapeHtml(assetPath)}" alt="${title}" ${eager ? 'fetchpriority="high"' : 'loading="lazy"'} decoding="async">`;
  }
  const srcset = profile.variants.map((item) => `${escapeHtml(item.path)} ${item.width}w`).join(", ");
  return `<img${imageClass} src="${escapeHtml(profile.default)}" srcset="${srcset}" sizes="${escapeHtml(sizes)}" width="${profile.width}" height="${profile.height}" alt="${title}" ${eager ? 'fetchpriority="high"' : 'loading="lazy"'} decoding="async">`;
}

export function mediaPreview(media, { eager = false, sizes } = {}) {
  const title = escapeHtml(media.altText || media.title || "Media item");
  if (media.assetPath && media.storageType !== "external") {
    if (media.mediaType === "audio") {
      return `<div class="media-preview media-preview--audio">
        <div class="media-preview__audio-mark"><span aria-hidden="true">♪</span><strong>Audio sample</strong></div>
        <audio controls preload="metadata" src="${escapeHtml(media.assetPath)}" aria-label="Play ${title}">Your browser does not support audio.</audio>
      </div>`;
    }
    return responsiveImage(media.assetPath, media.altText || media.title, { eager, sizes });
  }
  const external = safeExternalUrl(media.externalUrl);
  const label = externalMediaActionLabel(media);
  if (external) {
    return `<a class="media-preview media-preview--external" href="${escapeHtml(external)}" target="_blank" rel="noreferrer" aria-label="${escapeHtml(label)}: ${title}"><span aria-hidden="true">↗</span><span>${escapeHtml(label)}</span></a>`;
  }
  return `<div class="media-preview media-preview--external media-preview--unavailable"><span aria-hidden="true">—</span><span>External reference unavailable</span></div>`;
}

export function externalMediaActionLabel(media) {
  if (media?.mediaType === "audio") return "Listen to recording";
  if (media?.mediaType === "video") return "Watch video";
  return "Open external media";
}
