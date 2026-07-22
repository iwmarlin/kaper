import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=30f3d51e0a";
import {
  escapeHtml,
  humanize,
  mediaPreview,
  mountSiteChrome,
  periodBadge,
  recordUrl,
  registerImageDerivatives,
  renderError,
  renderLoading,
  responsiveImage,
  typeBadge,
} from "./core.js?v=30f3d51e0a";

registerImageDerivatives(IMAGE_DERIVATIVES);
mountSiteChrome("home");

const eventsTarget = document.querySelector("#featured-events");
const mediaTarget = document.querySelector("#media-highlights");
renderLoading(eventsTarget, "Loading selected events…");
renderLoading(mediaTarget, "Loading selected media…");

try {
  const response = await fetch(new URL("data/site/home.json", document.baseURI));
  if (!response.ok) throw new Error(`Could not load home-page data (${response.status})`);
  const { stats, portrait, events: eventSelection, highlights } = await response.json();
  document.querySelectorAll("#collection-stats strong").forEach((node, index) => {
    node.textContent = new Intl.NumberFormat("en-GB").format(stats[index]);
  });

  const portraitTarget = document.querySelector("#hero-portrait");
  if (portrait?.assetPath) {
    portraitTarget.innerHTML = `
      ${responsiveImage(portrait.assetPath, portrait.altText || portrait.title, {
        eager: true,
        sizes: "(max-width: 680px) calc(100vw - 2rem), 26rem",
      })}
      <figcaption>${escapeHtml(portrait.publicCaption || portrait.title)}</figcaption>`;
  } else {
    portraitTarget.hidden = true;
  }

  eventsTarget.innerHTML = eventSelection.map((event, index) => `
    <article class="home-event-card">
      <div class="home-event-card__topline">
        <span class="home-event-card__number" aria-hidden="true">0${index + 1}</span>
        ${periodBadge(event.periods || event.period)}
      </div>
      <p class="home-event-card__date">${escapeHtml(event.displayDate || event.dateStart)}</p>
      <h3><a href="${recordUrl("event", event.id)}">${escapeHtml(event.title)}</a></h3>
      <p class="card__description">${escapeHtml(event.shortDescription || event.longDescription || "")}</p>
      <div class="home-event-card__footer"><span>${escapeHtml(event.placeDisplay || "")}</span><span aria-hidden="true">→</span></div>
    </article>`).join("");

  mediaTarget.innerHTML = highlights.map((item) => `
    <article class="media-card home-media-card">
      <figure>${mediaPreview(item, { sizes: "(max-width: 680px) calc(100vw - 2rem), 30vw" })}</figure>
      <div class="media-card__body">
        <div class="meta-row">${typeBadge(item.mediaType)}${periodBadge(item.periods || item.period)}</div>
        <h2><a href="${recordUrl("media", item.id)}">${escapeHtml(item.title)}</a></h2>
        <p>${escapeHtml(item.publicCaption || item.description || "")}</p>
      </div>
    </article>`).join("");
} catch (error) {
  renderError(eventsTarget, error);
  renderError(mediaTarget, error);
}
