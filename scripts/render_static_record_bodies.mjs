#!/usr/bin/env node
/** Render record bodies with the same templates used by the browser. */

import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(process.argv[2] || path.join(scriptDir, ".."));
const { renderRecordMarkup, renderRecordView } = await import(
  pathToFileURL(path.join(projectRoot, "assets/site/record-detail-20260714.js")).href
);

const recordsRoot = path.join(projectRoot, "data/site/records");
const recordTypes = ["work", "event", "place", "media", "person", "organization", "source"];
const rendered = {};

for (const recordType of recordTypes) {
  const directory = path.join(recordsRoot, recordType);
  const filenames = (await readdir(directory))
    .filter((filename) => filename.endsWith(".json"))
    .sort((left, right) => left.localeCompare(right));
  for (const filename of filenames) {
    const payload = JSON.parse(await readFile(path.join(directory, filename), "utf8"));
    if (payload.type !== recordType || !payload.id || !payload.tables) {
      throw new Error(`Invalid record payload: ${recordType}/${filename}`);
    }
    const { view } = renderRecordView(recordType, payload.id, payload.tables);
    rendered[`${recordType}/${payload.id}`] = renderRecordMarkup(view, payload.id, recordType);
  }
}

process.stdout.write(JSON.stringify(rendered));
