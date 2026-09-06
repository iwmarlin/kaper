#!/usr/bin/env node
/** Render the default first page of each compact catalogue index. */

import process from "node:process";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(process.argv[2] || path.join(scriptDir, ".."));
const core = await import(pathToFileURL(path.join(projectRoot, "assets/site/core.js")).href);
const views = await import(pathToFileURL(path.join(projectRoot, "assets/site/catalogue-results.js")).href);
const derivatives = await import(pathToFileURL(path.join(projectRoot, "assets/site/image-derivatives.js")).href);

let input = "";
// Decode the stream continuously: coercing individual Buffer chunks can split
// a multibyte character at a chunk boundary and corrupt a title nondeterministically.
process.stdin.setEncoding("utf8");
for await (const chunk of process.stdin) input += chunk;
const indexes = JSON.parse(input);
views.registerCatalogueImageDerivatives(derivatives.IMAGE_DERIVATIVES);

const works = [...indexes.works.records].sort((left, right) => {
  const byTitle = core.compareText(left.sortTitle || left.title, right.sortTitle || right.title);
  return Number(left.year || 9999) - Number(right.year || 9999) || byTitle;
});
const people = [...indexes.people.records].sort((left, right) => (
  core.compareText(left.sortName || left.displayName, right.sortName || right.displayName)
));
const sources = [...indexes.sources.records].sort((left, right) => {
  const byTitle = core.compareText(views.sourceTitle(left), views.sourceTitle(right));
  const byId = core.compareText(left.id, right.id);
  return (views.sourceYear(left) ?? Number.POSITIVE_INFINITY)
    - (views.sourceYear(right) ?? Number.POSITIVE_INFINITY)
    || byTitle
    || byId;
});
const selectedMedia = indexes.media.records.filter((item) => item.galleryStatus === "selected");
const media = views.curatedMediaOrder(selectedMedia);

const page = (items, limit, renderer, noun) => {
  const shown = items.slice(0, limit);
  return {
    markup: shown.map(renderer).join("\n"),
    countText: `Showing ${shown.length} of ${items.length} ${items.length === 1 ? noun[0] : noun[1]}`,
    shown: shown.length,
    total: items.length,
  };
};

process.stdout.write(JSON.stringify({
  works: page(works, 36, views.renderWorkIndexRow, ["record", "records"]),
  people: page(people, 48, views.renderPersonIndexRow, ["person", "people"]),
  media: page(media, 30, views.renderMediaIndexCard, ["item", "items"]),
  sources: page(sources, 40, views.renderSourceIndexRow, ["source", "sources"]),
}));
