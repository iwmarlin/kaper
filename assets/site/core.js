const DATA_ROOT = "data/public/v1/";
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
let manifestPromise;

export function loadManifest() {
  if (!manifestPromise) {
    const url = new URL(`${DATA_ROOT}manifest.json`, document.baseURI);
    manifestPromise = fetch(url).then(async (response) => {
      if (!response.ok) throw new Error(`Could not load public manifest (${response.status})`);
      return response.json();
    });
  }
  return manifestPromise;
}

export async function loadTable(name) {
  if (!TABLE_FILES[name]) throw new Error(`Unknown public table: ${name}`);
  if (!tableCache.has(name)) {
    const url = new URL(`${DATA_ROOT}${TABLE_FILES[name]}`, document.baseURI);
    tableCache.set(
      name,
      fetch(url).then(async (response) => {
        if (!response.ok) {
          throw new Error(`Could not load ${TABLE_FILES[name]} (${response.status})`);
        }
        const payload = await response.json();
        if (!Array.isArray(payload.records)) {
          throw new Error(`${TABLE_FILES[name]} has an invalid public payload`);
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

export function typeBadge(type) {
  if (!type) return "";
  return `<span class="badge badge--type">${escapeHtml(humanize(type))}</span>`;
}

export function scopeBadge(scope) {
  if (scope !== "context_only") return "";
  return '<span class="badge badge--context">Context record</span>';
}

const RIGHTS_LABELS = Object.freeze({
  ok: "Rights documented",
  public_domain: "Public domain",
  permission_granted: "Permission granted",
  permission_needed_or_fair_use_claimed: "Fair use / permission",
  copyright_undetermined: "Copyright undetermined",
  restricted: "Restricted use",
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
  includeResolutionLabel = true,
  includeRightsBadge = true,
  includeTitle = true,
  includeSource = true,
} = {}) {
  if (!media) return "";
  const source = sources.find((item) => item?.id) || null;
  const sourceExternal = safeExternalUrl(media.externalUrl) || safeExternalUrl(source?.url);
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
    ${compact && conciseRationale ? `<p class="media-disclosure__rationale"><strong>Use rationale:</strong> ${escapeHtml(conciseRationale)}</p>` : ""}
    ${compact && includeFullRightsNote && fullRationale ? `<details class="media-disclosure__details"><summary>Full rights and use note</summary><p>${escapeHtml(rationale)}</p></details>` : ""}
    ${!compact && rationale ? `<p class="media-disclosure__rationale">${mediaIsFairUse(media) ? "<strong>Use rationale:</strong> " : ""}${escapeHtml(rationale)}</p>` : ""}
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
  return String(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
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
  ["timeline", "life.html", "Timeline"],
  ["map", "map.html", "Map"],
  ["media", "media.html", "Media"],
];

export function mountSiteChrome(activePage) {
  const header = document.querySelector("[data-site-header]");
  if (header) {
    header.innerHTML = `
      <a class="skip-link" href="#main-content">Skip to content</a>
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
    button?.addEventListener("click", () => {
      const open = button.getAttribute("aria-expanded") === "true";
      button.setAttribute("aria-expanded", String(!open));
      nav?.classList.toggle("site-nav--open", !open);
    });
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
  const external = safeExternalUrl(source.url);
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
  const label = `Open external ${humanize(media.mediaType || "media").toLowerCase()}`;
  if (external) {
    return `<a class="media-preview media-preview--external" href="${escapeHtml(external)}" target="_blank" rel="noreferrer" aria-label="${escapeHtml(label)}: ${title}"><span aria-hidden="true">↗</span><span>${escapeHtml(label)}</span></a>`;
  }
  return `<div class="media-preview media-preview--external media-preview--unavailable"><span aria-hidden="true">—</span><span>External reference unavailable</span></div>`;
}
