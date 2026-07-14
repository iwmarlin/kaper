import {
  debounce,
  escapeHtml,
  humanize,
  loadTables,
  mediaPreview,
  mountSiteChrome,
  normalizeSearch,
  periodBadge,
  recordUrl,
  renderError,
  renderLoading,
  safeExternalUrl,
  typeBadge,
} from "./core.js";

mountSiteChrome("media");

const controls = {
  search: document.querySelector("#media-search"),
  type: document.querySelector("#media-type"),
  period: document.querySelector("#media-period"),
  scope: document.querySelector("#media-scope"),
};
const target = document.querySelector("#media-results");
const countTarget = document.querySelector("#media-count");
const more = document.querySelector("#media-more");
const PAGE_SIZE = 30;
let visible = PAGE_SIZE;
let current = [];
renderLoading(target, "Loading curated media…");

function addOptions(select, values) {
  for (const value of [...new Set(values.filter(Boolean))].sort()) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = humanize(value);
    select.append(option);
  }
}

try {
  const { media } = await loadTables(["media"]);
  addOptions(controls.type, media.map((item) => item.mediaType));
  addOptions(controls.period, media.map((item) => item.period));
  const indexed = media.map((item) => ({
    ...item,
    _search: normalizeSearch([item.title, item.category, item.publicCaption, item.description, item.period, item.mediaType].filter(Boolean).join(" ")),
  }));

  function render() {
    const query = normalizeSearch(controls.search.value.trim());
    current = indexed
      .filter((item) => (
        (!query || item._search.includes(query))
        && (!controls.type.value || item.mediaType === controls.type.value)
        && (!controls.period.value || item.period === controls.period.value)
        && (controls.scope.value === "all" || item.galleryStatus === controls.scope.value)
      ))
      .sort((a, b) => Number(a.sortOrder || 99999) - Number(b.sortOrder || 99999) || String(a.title).localeCompare(String(b.title)));
    const shown = current.slice(0, visible);
    countTarget.innerHTML = `<strong>${current.length}</strong> ${current.length === 1 ? "item" : "items"} shown`;
    more.hidden = shown.length >= current.length;
    if (!shown.length) {
      target.innerHTML = `<div class="empty-state"><h2>No matching media</h2><p>Try a broader search or another gallery scope.</p></div>`;
      return;
    }
    target.innerHTML = shown.map((item) => {
      const external = safeExternalUrl(item.externalUrl);
      const isGallery = item.mediaType === "document_gallery" && Array.isArray(item.assetPaths) && item.assetPaths.length > 1;
      const preview = mediaPreview(item);
      return `
        <article class="media-card">
          <figure>${isGallery ? `<a class="media-card__image-link" href="${recordUrl("media", item.id)}">${preview}<span>Open gallery · ${item.assetPaths.length} images</span></a>` : preview}</figure>
          <div class="media-card__body">
            <div class="meta-row">${typeBadge(item.mediaType)}${periodBadge(item.period)}${typeBadge(item.rightsStatus)}</div>
            <h2><a href="${recordUrl("media", item.id)}">${escapeHtml(item.title)}</a></h2>
            <p>${escapeHtml(item.publicCaption || item.description || "")}</p>
            <div class="card__footer"><span>${escapeHtml(humanize(item.category || item.galleryStatus))}</span><span>${escapeHtml(item.id)}</span></div>
            <div class="media-card__actions">
              <a href="${recordUrl("media", item.id)}">${isGallery ? `Open gallery (${item.assetPaths.length})` : "View record"} <span aria-hidden="true">→</span></a>
              ${external ? `<a href="${escapeHtml(external)}" target="_blank" rel="noreferrer">Open external media <span aria-hidden="true">↗</span></a>` : ""}
            </div>
          </div>
        </article>`;
    }).join("");
  }

  const resetAndRender = () => { visible = PAGE_SIZE; render(); };
  controls.search.addEventListener("input", debounce(resetAndRender));
  for (const control of [controls.type, controls.period, controls.scope]) control.addEventListener("change", resetAndRender);
  document.querySelector("#media-reset").addEventListener("click", () => {
    controls.search.value = "";
    controls.type.value = "";
    controls.period.value = "";
    controls.scope.value = "selected";
    resetAndRender();
  });
  more.addEventListener("click", () => { visible += PAGE_SIZE; render(); });
  render();
} catch (error) {
  countTarget.textContent = "Media unavailable";
  renderError(target, error);
}
