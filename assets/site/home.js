import {
  escapeHtml,
  humanize,
  indexById,
  loadManifest,
  loadTables,
  mediaPreview,
  mountSiteChrome,
  periodBadge,
  recordUrl,
  renderError,
  renderLoading,
  typeBadge,
} from "./core.js";

mountSiteChrome("home");

const eventsTarget = document.querySelector("#featured-events");
const mediaTarget = document.querySelector("#media-highlights");
renderLoading(eventsTarget, "Loading selected events…");
renderLoading(mediaTarget, "Loading selected media…");

try {
  const [{ works, timelineEvents, media }, manifest] = await Promise.all([loadTables([
    "works",
    "timelineEvents",
    "media",
  ]), loadManifest()]);

  const stats = [
    manifest.counts.Works,
    manifest.counts["Timeline Events"],
    manifest.counts.Places,
    manifest.counts.Sources,
  ];
  document.querySelectorAll("#collection-stats strong").forEach((node, index) => {
    node.textContent = new Intl.NumberFormat("en-GB").format(stats[index]);
  });

  const mediaById = indexById(media);
  const portrait = mediaById.get("M048") || media.find((item) => item.category === "portrait" && item.assetPath);
  const portraitTarget = document.querySelector("#hero-portrait");
  if (portrait?.assetPath) {
    portraitTarget.innerHTML = `
      <img src="${escapeHtml(portrait.assetPath)}" alt="${escapeHtml(portrait.altText || portrait.title)}" fetchpriority="high" decoding="async">
      <figcaption>${escapeHtml(portrait.publicCaption || portrait.title)}</figcaption>`;
  } else {
    portraitTarget.hidden = true;
  }

  const featured = timelineEvents
    .filter((event) => event.featured)
    .sort((a, b) => String(a.sortDate || a.dateStart).localeCompare(String(b.sortDate || b.dateStart)))
    .slice(0, 6);
  const eventSelection = featured.length >= 3
    ? featured.slice(0, 3)
    : timelineEvents
      .filter((event) => event.shortDescription)
      .sort((a, b) => Number(a.sortOrder || 999) - Number(b.sortOrder || 999))
      .filter((_, index, items) => index === 0 || index === Math.floor(items.length / 2) || index === items.length - 1)
      .slice(0, 3);

  eventsTarget.innerHTML = eventSelection.map((event) => `
    <article class="card">
      <div class="card__meta">${periodBadge(event.period)}</div>
      <h3><a href="${recordUrl("event", event.id)}">${escapeHtml(event.title)}</a></h3>
      <p class="card__description">${escapeHtml(event.shortDescription || event.longDescription || "")}</p>
      <div class="card__footer"><span>${escapeHtml(event.displayDate || event.dateStart)}</span><span>${escapeHtml(event.placeDisplay || "")}</span></div>
    </article>`).join("");

  const highlights = media
    .filter((item) => item.galleryStatus === "selected" && item.storageType === "local" && item.assetPath && item.mediaType !== "audio")
    .sort((a, b) => Number(a.sortOrder || 99999) - Number(b.sortOrder || 99999))
    .slice(0, 3);
  mediaTarget.innerHTML = highlights.map((item) => `
    <article class="media-card">
      <figure>${mediaPreview(item)}</figure>
      <div class="media-card__body">
        <div class="meta-row">${typeBadge(item.mediaType)}${periodBadge(item.period)}</div>
        <h2><a href="${recordUrl("media", item.id)}">${escapeHtml(item.title)}</a></h2>
        <p>${escapeHtml(item.publicCaption || item.description || "")}</p>
      </div>
    </article>`).join("");
} catch (error) {
  renderError(eventsTarget, error);
  renderError(mediaTarget, error);
}
