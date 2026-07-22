import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=ddc6df159e";
import {
  debounce,
  escapeHtml,
  humanize,
  indexById,
  loadTables,
  mediaIsFairUse,
  mediaPreview,
  mediaRightsBadge,
  matchesPeriod,
  mountSiteChrome,
  normalizeSearch,
  PERIOD_ORDER,
  periodBadge,
  periodLabel,
  periodValues,
  recordUrl,
  registerImageDerivatives,
  renderMediaDisclosure,
  renderError,
  renderLoading,
  resolveIds,
  safeExternalUrl,
  typeBadge,
} from "./core.js?v=ddc6df159e";

registerImageDerivatives(IMAGE_DERIVATIVES);
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
const showAll = document.querySelector("#media-show-all");
const PAGE_SIZE = 30;
let visible = PAGE_SIZE;
let showingAll = false;
let current = [];
renderLoading(target, "Loading curated media…");

function addOptions(select, values, labeler = humanize, preserveOrder = false) {
  const uniqueValues = [...new Set(values.filter(Boolean))];
  for (const value of preserveOrder ? uniqueValues : uniqueValues.sort()) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = labeler(value);
    select.append(option);
  }
}

function compareMedia(a, b) {
  return Number(a.sortOrder || 99999) - Number(b.sortOrder || 99999)
    || String(a.title).localeCompare(String(b.title));
}

function curatedOrder(items) {
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

try {
  const { media, sources } = await loadTables(["media", "sources"]);
  const sourcesById = indexById(sources);
  addOptions(controls.type, media.map((item) => item.mediaType));
  const availablePeriods = new Set(media.flatMap(periodValues));
  addOptions(controls.period, PERIOD_ORDER.filter((value) => availablePeriods.has(value)), periodLabel, true);
  const indexed = media.map((item) => ({
    ...item,
    _search: normalizeSearch([item.title, item.category, item.publicCaption, item.description, ...periodValues(item), item.mediaType].filter(Boolean).join(" ")),
  }));

  function render() {
    const query = normalizeSearch(controls.search.value.trim());
    current = indexed
      .filter((item) => (
        (!query || item._search.includes(query))
        && (!controls.type.value || item.mediaType === controls.type.value)
        && matchesPeriod(item, controls.period.value)
        && (controls.scope.value === "all" || item.galleryStatus === controls.scope.value)
      ));
    const isDefaultCuratedView = controls.scope.value === "selected"
      && !query
      && !controls.type.value
      && !controls.period.value;
    current = isDefaultCuratedView ? curatedOrder(current) : current.sort(compareMedia);
    const shown = current.slice(0, showingAll ? current.length : visible);
    countTarget.innerHTML = `<strong>Showing ${shown.length}</strong> of ${current.length} ${current.length === 1 ? "item" : "items"}`;
    const remaining = current.length - shown.length;
    more.hidden = remaining <= 0;
    showAll.hidden = remaining <= 0;
    if (remaining > 0) {
      const nextCount = Math.min(PAGE_SIZE, remaining);
      more.textContent = `Load ${nextCount} more`;
      more.setAttribute("aria-label", `Load ${nextCount} more media items`);
      showAll.textContent = `Show all ${current.length}`;
      showAll.setAttribute("aria-label", `Show all ${current.length} media items`);
    }
    if (!shown.length) {
      target.innerHTML = `<div class="empty-state"><h2>No matching media</h2><p>Try a broader search or another gallery scope.</p></div>`;
      return;
    }
    target.innerHTML = shown.map((item) => {
      const external = safeExternalUrl(item.externalUrl);
      const isGallery = item.mediaType === "document_gallery" && Array.isArray(item.assetPaths) && item.assetPaths.length > 1;
      const isLocalVisual = Boolean(item.assetPath && item.storageType !== "external" && item.mediaType !== "audio");
      const isFairUse = mediaIsFairUse(item);
      const itemSources = resolveIds(item, "sourceIds", sourcesById);
      const preview = mediaPreview(item, {
        sizes: "(max-width: 680px) calc(100vw - 2rem), (max-width: 1100px) 46vw, 27rem",
      });
      const previewMarkup = isGallery
        ? `<a class="media-card__image-link" href="${recordUrl("media", item.id)}">${preview}<span>Open gallery · ${item.assetPaths.length} images</span></a>`
        : (isLocalVisual
          ? `<a class="media-card__preview-link" href="${recordUrl("media", item.id)}" aria-label="View media record: ${escapeHtml(item.title)}">${preview}</a>`
          : preview);
      return `
        <article class="media-card" data-media-id="${escapeHtml(item.id)}">
          <figure>${previewMarkup}</figure>
          <div class="media-card__body">
            <div class="meta-row">${typeBadge(item.mediaType)}${periodBadge(item.periods || item.period)}${mediaRightsBadge(item)}</div>
            <h2><a href="${recordUrl("media", item.id)}">${escapeHtml(item.title)}</a></h2>
            <p>${escapeHtml(item.publicCaption || item.description || "")}</p>
            ${isFairUse ? renderMediaDisclosure(item, itemSources, {
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
              ${external ? `<a href="${escapeHtml(external)}" target="_blank" rel="noreferrer">Open external media <span aria-hidden="true">↗</span></a>` : ""}
            </div>
          </div>
        </article>`;
    }).join("");
  }

  const resetAndRender = () => { visible = PAGE_SIZE; showingAll = false; render(); };
  controls.search.addEventListener("input", debounce(resetAndRender));
  for (const control of [controls.type, controls.period, controls.scope]) control.addEventListener("change", resetAndRender);
  document.querySelector("#media-reset").addEventListener("click", () => {
    controls.search.value = "";
    controls.type.value = "";
    controls.period.value = "";
    controls.scope.value = "selected";
    resetAndRender();
  });
  function revealFrom(firstNewIndex) {
    const firstNewCard = target.children[firstNewIndex];
    if (firstNewCard) {
      firstNewCard.setAttribute("tabindex", "-1");
      firstNewCard.focus({ preventScroll: true });
      firstNewCard.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
        block: "start",
      });
    }
  }
  more.addEventListener("click", () => {
    const firstNewIndex = Math.min(visible, current.length);
    visible += PAGE_SIZE;
    render();
    revealFrom(firstNewIndex);
  });
  showAll.addEventListener("click", () => {
    const firstNewIndex = Math.min(visible, current.length);
    showingAll = true;
    render();
    revealFrom(firstNewIndex);
  });
  render();
} catch (error) {
  countTarget.textContent = "Media unavailable";
  renderError(target, error);
}
