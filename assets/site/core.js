const DATA_ROOT = "data/public/v1/";

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
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}

export function recordUrl(type, id) {
  const params = new URLSearchParams({ type, id });
  return `record.html?${params.toString()}`;
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

export function periodBadge(period) {
  if (!period) return "";
  return `<span class="badge badge--period">${escapeHtml(humanize(period))}</span>`;
}

export function typeBadge(type) {
  if (!type) return "";
  return `<span class="badge badge--type">${escapeHtml(humanize(type))}</span>`;
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

export function mediaPreview(media, { eager = false } = {}) {
  const title = escapeHtml(media.altText || media.title || "Media item");
  if (media.storageType === "local" && media.assetPath) {
    if (media.mediaType === "audio") {
      return `<div class="media-preview media-preview--audio"><span aria-hidden="true">♪</span><audio controls preload="none" src="${escapeHtml(media.assetPath)}">Your browser does not support audio.</audio></div>`;
    }
    return `<img src="${escapeHtml(media.assetPath)}" alt="${title}" ${eager ? 'fetchpriority="high"' : 'loading="lazy"'} decoding="async">`;
  }
  return `<div class="media-preview media-preview--external"><span aria-hidden="true">↗</span><span>External ${escapeHtml(humanize(media.mediaType || "media"))}</span></div>`;
}
