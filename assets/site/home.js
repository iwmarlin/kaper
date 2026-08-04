import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=af1e93751c";
import {
  escapeHtml,
  humanize,
  mediaPreview,
  mountSiteChrome,
  recordUrl,
  registerImageDerivatives,
  renderError,
  renderLoading,
  responsiveImage,
} from "./core.js?v=af1e93751c";

registerImageDerivatives(IMAGE_DERIVATIVES);
mountSiteChrome("home");

const journeyTarget = document.querySelector("#home-journey");
const mediaTarget = document.querySelector("#media-highlights");
renderLoading(journeyTarget, "Loading documented periods…");
renderLoading(mediaTarget, "Loading selected media…");

const numberFormat = new Intl.NumberFormat("en-GB");

const periodDetails = {
  warsaw: { number: "01", label: "Warsaw", years: "1902–1926" },
  european: { number: "02", label: "European years", years: "1926–1934" },
  hollywood: { number: "03", label: "Early Hollywood", years: "1935–1939" },
};

function renderJourney(chapters) {
  journeyTarget.innerHTML = chapters.map((chapter) => {
    const period = Array.isArray(chapter.periods) ? chapter.periods[0] : chapter.period;
    const detail = periodDetails[period] || {
      number: "—",
      label: humanize(period || "period"),
      years: chapter.displayDate || "",
    };
    const image = chapter.image;
    const mediaUrl = image ? recordUrl("media", image.id) : "";
    const figure = image?.assetPath ? `
      <figure class="journey-card__figure">
        <a href="${mediaUrl}" aria-label="View media record: ${escapeHtml(image.title)}">
          ${responsiveImage(image.assetPath, image.altText || image.title, {
            sizes: "(max-width: 760px) calc(100vw - 2rem), 42vw",
          })}
        </a>
        <figcaption>
          <span>${escapeHtml(image.title)}</span>
          <a href="${mediaUrl}">Source and rights <span aria-hidden="true">→</span></a>
        </figcaption>
      </figure>` : "";
    return `
      <article class="journey-card" data-period="${escapeHtml(period || "")}">
        ${figure}
        <div class="journey-card__copy">
          <p class="journey-card__chapter"><span>${detail.number}</span>${escapeHtml(detail.label)}</p>
          <p class="journey-card__years">${escapeHtml(detail.years)}</p>
          <h3><a href="${recordUrl("event", chapter.id)}">${escapeHtml(chapter.title)}</a></h3>
          <p>${escapeHtml(chapter.shortDescription || chapter.longDescription || "")}</p>
          <p class="journey-card__meta">
            <span>${escapeHtml(chapter.displayDate || chapter.dateStart || "")}</span>
            ${chapter.placeDisplay ? `<span>${escapeHtml(chapter.placeDisplay)}</span>` : ""}
          </p>
          <a class="journey-card__link" href="${recordUrl("event", chapter.id)}">Read the documented event <span aria-hidden="true">→</span></a>
        </div>
      </article>`;
  }).join("");
}

function renderEvidence(items) {
  mediaTarget.innerHTML = items.map((item, index) => `
    <article class="evidence-card${index === 0 ? " evidence-card--featured" : ""}">
      <a class="evidence-card__media" href="${recordUrl("media", item.id)}" aria-label="View media record: ${escapeHtml(item.title)}">
        ${mediaPreview(item, {
          sizes: index === 0
            ? "(max-width: 760px) calc(100vw - 2rem), 62vw"
            : "(max-width: 760px) calc(100vw - 2rem), 30vw",
        })}
      </a>
      <div class="evidence-card__body">
        <p class="evidence-card__meta">${escapeHtml(humanize(item.mediaType || item.category || "media"))} · ${escapeHtml(periodDetails[item.period]?.label || humanize(item.period || ""))}</p>
        <h3><a href="${recordUrl("media", item.id)}">${escapeHtml(item.title)}</a></h3>
        <p>${escapeHtml(item.publicCaption || item.description || "")}</p>
        <a class="evidence-card__link" href="${recordUrl("media", item.id)}">View record <span aria-hidden="true">→</span></a>
      </div>
    </article>`).join("");
}

try {
  const response = await fetch(new URL("data/site/home.json", document.baseURI));
  if (!response.ok) throw new Error(`Could not load home-page data (${response.status})`);
  const { stats, portrait, journey, events, highlights } = await response.json();
  document.querySelectorAll("#collection-stats strong").forEach((node, index) => {
    node.textContent = numberFormat.format(stats[index]);
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

  renderJourney(journey || events || []);
  renderEvidence(highlights || []);
} catch (error) {
  renderError(journeyTarget, error);
  renderError(mediaTarget, error);
}
