import { IMAGE_DERIVATIVES } from "./image-derivatives.js?v=dbdabd6d38";
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
} from "./core.js?v=dbdabd6d38";

registerImageDerivatives(IMAGE_DERIVATIVES);
mountSiteChrome("home");

const eventsTarget = document.querySelector("#featured-events");
const mediaTarget = document.querySelector("#media-highlights");
const figuresTarget = document.querySelector("#home-figures");
renderLoading(eventsTarget, "Loading selected events…");
renderLoading(mediaTarget, "Loading selected media…");

const numberFormat = new Intl.NumberFormat("en-GB");

function figureGroup(kind, title, rows) {
  const max = Math.max(...rows.map((row) => row.count), 1);
  const bars = rows.map((row, index) => `
    <div class="figure-row${index === 0 ? " is-lead" : ""}">
      <div class="figure-row__head">
        <span class="figure-row__label">${escapeHtml(row.label)}${row.note ? ` <span class="figure-row__note">${escapeHtml(row.note)}</span>` : ""}</span>
        <span class="figure-row__value">${numberFormat.format(row.count)}</span>
      </div>
      <div class="figure-bar"><span class="figure-bar__fill" style="width: ${Math.max(6, Math.round((row.count / max) * 100))}%"></span></div>
    </div>`).join("");
  return `<div class="figure-group" data-kind="${kind}"><h3 class="figure-group__title">${escapeHtml(title)}</h3>${bars}</div>`;
}

function renderFigures(data) {
  if (!figuresTarget) return;
  if (!data) {
    figuresTarget.closest("section")?.remove();
    return;
  }
  const groups = [
    figureGroup("type", "Works by type", data.byType),
    figureGroup("era", "Works by era", data.byEra),
    figureGroup("collaborators", "Closest collaborators", (data.collaborators || []).map((person) => ({ label: person.name, count: person.count }))),
  ].join("");
  const certainty = data.certainty || {};
  const footer = `
    <div class="figures-footer">
      ${data.span ? `<span class="figures-footer__item"><strong>${data.span.start}–${data.span.end}</strong> documented span</span>` : ""}
      <span class="figures-footer__item"><strong>${numberFormat.format(certainty.confirmed || 0)}</strong> confirmed · ${certainty.probable || 0} probable · ${certainty.uncertain || 0} uncertain</span>
      <span class="figures-footer__note">Collaborators counted by shared works, documented.</span>
    </div>`;
  figuresTarget.innerHTML = `<div class="figures-groups">${groups}</div>${footer}`;
}

try {
  const response = await fetch(new URL("data/site/home.json", document.baseURI));
  if (!response.ok) throw new Error(`Could not load home-page data (${response.status})`);
  const { stats, portrait, events: eventSelection, highlights, atAGlance } = await response.json();
  document.querySelectorAll("#collection-stats strong").forEach((node, index) => {
    node.textContent = numberFormat.format(stats[index]);
  });
  const timelinePathwayCount = document.querySelector("#timeline-pathway-count");
  if (timelinePathwayCount) {
    timelinePathwayCount.textContent = `${numberFormat.format(stats[1])} documented events`;
  }
  renderFigures(atAGlance);

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
  figuresTarget?.closest("section")?.remove();
}
