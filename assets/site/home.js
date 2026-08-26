import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=f9e09f5aea";
import {
  escapeHtml,
  mountSiteChrome,
  periodBadge,
  recordUrl,
  registerImageDerivatives,
  renderError,
  renderLoading,
  responsiveImage,
} from "./core.js?v=f9e09f5aea";

registerImageDerivatives(IMAGE_DERIVATIVES);
mountSiteChrome("home");

const pathwaysTarget = document.querySelector("#pathways-index");
const eventsTarget = document.querySelector("#featured-events");
const portraitTarget = document.querySelector("#hero-portrait");
const figuresTarget = document.querySelector("#method-figures");
renderLoading(eventsTarget, "Loading selected moments…");

const numberFormat = new Intl.NumberFormat("en-GB");

// One gateway, one set of figures. The counts used to sit in a band of their own
// above these links and again in a section of charts below them; here they say
// how much there is and lead straight to it.
function renderPathways(pathways) {
  if (!pathwaysTarget || !Array.isArray(pathways)) return;
  pathwaysTarget.innerHTML = pathways.map((pathway) => `
    <li>
      <a class="pathway-row" href="${escapeHtml(pathway.href)}">
        <span class="pathway-row__content">
          <span class="pathway-row__title">${escapeHtml(pathway.label)}</span>
          <span class="pathway-row__description">${escapeHtml(pathway.description)}</span>
        </span>
        <span class="pathway-row__count">${numberFormat.format(pathway.count)}</span>
        <span class="pathway-row__arrow" aria-hidden="true">→</span>
      </a>
    </li>`).join("");
}

function currentPathways(pathways, counts = {}) {
  const countKeys = {
    Works: "Works",
    People: "People",
    Timeline: "Timeline Events",
    Places: "Places",
    Media: "Media",
  };
  return (pathways || []).map((pathway) => {
    const currentCount = counts[countKeys[pathway.label]];
    return Number.isFinite(currentCount)
      ? { ...pathway, count: currentCount }
      : pathway;
  });
}

function renderPortrait(portrait) {
  if (!portraitTarget) return;
  if (!portrait?.assetPath) {
    portraitTarget.hidden = true;
    return;
  }
  // The one image on the page used to carry neither caption nor link. In a
  // source-based archive that is the wrong image to leave unattributed.
  const caption = escapeHtml(portrait.publicCaption || portrait.title || "");
  portraitTarget.innerHTML = `
    ${responsiveImage(portrait.assetPath, portrait.altText || portrait.title, {
      eager: true,
      sizes: "(max-width: 680px) 9rem, 20rem",
    })}
    <figcaption>
      <span class="hero__portrait-caption">${caption}</span>
      <a href="${recordUrl("media", portrait.id)}">See the record</a>
    </figcaption>`;
}

function renderEvents(events) {
  if (!eventsTarget) return;
  eventsTarget.innerHTML = (events || []).map((event) => `
    <article class="home-event-card">
      ${event.image ? `<figure class="home-event-card__figure">${responsiveImage(event.image.assetPath, event.image.altText || event.title, {
        sizes: "(max-width: 680px) calc(100vw - 2.5rem), 22rem",
      })}</figure>` : ""}
      <div class="home-event-card__body">
        <div class="home-event-card__topline">
          <p class="home-event-card__date">${escapeHtml(event.displayDate || event.dateStart || "")}</p>
          ${periodBadge(event.periods || event.period)}
        </div>
        <h3><a href="${recordUrl("event", event.id)}">${escapeHtml(event.title)}</a></h3>
        <p class="card__description">${escapeHtml(event.shortDescription || event.longDescription || "")}</p>
        <div class="home-event-card__footer"><span>${escapeHtml(event.placeDisplay || "")}</span><span aria-hidden="true">→</span></div>
      </div>
    </article>`).join("");
}

// The evidential figures belong to the statement of method, not to a section of
// their own: they say how firm the record is, not how large it is. They report
// the qualified attributions rather than the confirmed ones, and empty
// categories are left out — a category with nothing in it says only that the
// category exists, and "0 uncertain" reads as a claim that nothing here is in
// doubt, which would misdescribe an archive whose doubts are recorded on
// individual attributions, scopes and rights.
function renderFigures(glance) {
  if (!figuresTarget || !glance) return;
  const certainty = glance.certainty || {};
  const total = Object.values(certainty).reduce((sum, value) => sum + (value || 0), 0);
  const qualified = (certainty.probable || 0) + (certainty.uncertain || 0);
  const parts = [];
  if (total) {
    parts.push(qualified
      ? `<strong>${numberFormat.format(total)}</strong> works, of which <strong>${qualified}</strong> carry a qualified attribution`
      : `<strong>${numberFormat.format(total)}</strong> works`);
  }
  if (glance.span) parts.push(`documented <strong>${glance.span.start}–${glance.span.end}</strong>`);
  if (glance.sources) parts.push(`<strong>${numberFormat.format(glance.sources)}</strong> linked sources`);
  figuresTarget.innerHTML = parts.join(" · ");
}

try {
  const [homeResponse, manifestResponse] = await Promise.all([
    fetch(new URL("data/site/home.json", document.baseURI)),
    fetch(new URL("data/public/v1/manifest.json", document.baseURI)),
  ]);
  if (!homeResponse.ok) throw new Error(`Could not load home-page data (${homeResponse.status})`);
  if (!manifestResponse.ok) throw new Error(`Could not load public-data manifest (${manifestResponse.status})`);
  const [{ pathways, portrait, events, glance }, manifest] = await Promise.all([
    homeResponse.json(),
    manifestResponse.json(),
  ]);
  const counts = manifest.counts || {};
  renderPathways(currentPathways(pathways, counts));
  renderPortrait(portrait);
  renderEvents(events);
  renderFigures({ ...glance, sources: counts.Sources ?? glance?.sources });
} catch (error) {
  renderError(eventsTarget, error);
}
