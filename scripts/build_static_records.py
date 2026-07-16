#!/usr/bin/env python3
"""Generate crawlable HTML record pages and a complete sitemap."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote


ORIGIN = "https://iwmarlin.github.io/kaper/"
PUBLIC_PAGES = ["", "works.html", "life.html", "map.html", "media.html"]
RECORD_TABLES = {
    "work": "works",
    "event": "timelineEvents",
    "place": "places",
    "media": "media",
    "person": "people",
    "organization": "organizations",
    "source": "sources",
}
TYPE_LABELS = {
    "work": "Work",
    "event": "Timeline event",
    "place": "Place",
    "media": "Media record",
    "person": "Person",
    "organization": "Organization",
    "source": "Source",
}
CSP = (
    "default-src 'self'; script-src 'self' https://unpkg.com; "
    "style-src 'self' 'unsafe-inline' https://unpkg.com; "
    "img-src 'self' data: https://*.tile.openstreetmap.org; media-src 'self'; "
    "connect-src 'self'; frame-src 'none'; object-src 'none'; "
    "base-uri 'self'; form-action 'self'"
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value) -> str:
    return html.escape(display_value(value), quote=True)


def display_value(value) -> str:
    if isinstance(value, list):
        return ", ".join(display_value(item) for item in value if item not in (None, ""))
    return str(value or "")


def compact_text(value, limit: int = 300) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    shortened = text[: limit + 1].rsplit(" ", 1)[0]
    return f"{shortened}…"


def title_for(record_type: str, record: dict) -> str:
    if record_type == "place":
        return record.get("displayName") or record["id"]
    if record_type in {"person", "organization"}:
        return record.get("displayName") or record["id"]
    if record_type == "source":
        return record.get("title") or record.get("shortCitation") or record["id"]
    return record.get("title") or record["id"]


def summary_for(record_type: str, record: dict, tables: dict) -> str:
    if record_type == "work":
        subtype = next(
            (
                item
                for table in ("films", "songs", "otherWorks")
                for item in tables[table]
                if record["id"] in item.get("workIds", [])
            ),
            {},
        )
        return compact_text(
            subtype.get("publicNote")
            or record.get("publicNote")
            or f"A documented {str(record.get('workType') or 'work').lower()} in the Bronisław Kaper research archive."
        )
    if record_type == "event":
        return compact_text(record.get("longDescription") or record.get("shortDescription") or record.get("title"))
    if record_type == "place":
        return compact_text(
            record.get("publicNote")
            or ", ".join(filter(None, [record.get("city"), record.get("country")]))
            or record.get("displayName")
        )
    if record_type == "media":
        return compact_text(record.get("publicCaption") or record.get("description") or record.get("title"))
    if record_type == "person":
        roles = [record.get("primaryRole"), *record.get("roles", [])]
        roles = list(dict.fromkeys(filter(None, roles)))
        return compact_text(
            f"{record.get('displayName')}, documented as {', '.join(roles).lower()} in the Bronisław Kaper research archive."
            if roles
            else f"{record.get('displayName')} in the Bronisław Kaper research archive."
        )
    if record_type == "organization":
        context = ", ".join(
            filter(None, [display_value(record.get("city")), display_value(record.get("country"))])
        )
        types = display_value(record.get("types"))
        return compact_text(
            f"{record.get('displayName')}: {'; '.join(filter(None, [types, context]))}."
            if types or context
            else f"{record.get('displayName')} in the Bronisław Kaper research archive."
        )
    return compact_text(record.get("fullCitation") or record.get("shortCitation") or record.get("title"))


def facts_for(record_type: str, record: dict) -> list[tuple[str, str]]:
    if record_type == "work":
        return [("Year", record.get("year")), ("Type", record.get("workType")), ("Period", record.get("period"))]
    if record_type == "event":
        return [
            ("Date", record.get("displayDate") or record.get("dateStart")),
            ("Place", record.get("placeDisplay")),
            ("Category", record.get("category")),
        ]
    if record_type == "place":
        return [("City", record.get("city")), ("Country", record.get("country")), ("Type", record.get("placeType"))]
    if record_type == "media":
        if record.get("mediaType") == "document_gallery":
            return [("Images", len(record.get("assetPaths", []))), ("Period", record.get("period"))]
        return [("Media type", record.get("mediaType")), ("Period", record.get("period")), ("Rights", record.get("rightsStatus"))]
    if record_type == "person":
        return [("Authorized name", record.get("authorizedName")), ("Primary role", record.get("primaryRole"))]
    if record_type == "organization":
        return [("Authorized name", record.get("authorizedName")), ("City", record.get("city")), ("Country", record.get("country"))]
    return [("Creator", record.get("creator")), ("Date", record.get("date")), ("Repository", record.get("repository"))]


def source_links(record_type: str, record: dict, tables: dict) -> str:
    if record_type in {"person", "organization", "source"}:
        return ""
    source_by_id = {item["id"]: item for item in tables["sources"]}
    sources = [source_by_id[source_id] for source_id in record.get("sourceIds", []) if source_id in source_by_id]
    if not sources:
        return ""
    items = "".join(
        f'<li><a href="records/source/{quote(source["id"], safe="")}/">{esc(source.get("shortCitation") or source.get("title") or source["id"])}</a></li>'
        for source in sources
    )
    return f'<section class="record-section"><h2>Sources</h2><ol class="citation-list">{items}</ol></section>'


def static_page(record_type: str, record: dict, tables: dict) -> str:
    title = title_for(record_type, record)
    summary = summary_for(record_type, record, tables)
    label = TYPE_LABELS[record_type]
    record_id = record["id"]
    is_gallery = record_type == "media" and record.get("mediaType") == "document_gallery"
    style_version = "20260716-2"
    record_script_version = "20260716-4"
    route = f"records/{record_type}/{quote(record_id, safe='')}/"
    canonical = f"{ORIGIN}{route}"
    facts = "".join(
        f"<div><dt>{esc(label_text)}</dt><dd>{esc(value)}</dd></div>"
        for label_text, value in facts_for(record_type, record)
        if value not in (None, "", [])
    )
    sources = "" if is_gallery else source_links(record_type, record, tables)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="{esc(CSP)}">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <base href="../../../">
  <meta name="description" content="{esc(compact_text(summary, 180))}">
  <meta name="theme-color" content="#152c33">
  <meta name="robots" content="index,follow">
  <meta property="og:title" content="{esc(title)} — Bronisław Kaper archive">
  <meta property="og:description" content="{esc(compact_text(summary, 200))}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{esc(canonical)}">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="stylesheet" href="assets/site/styles.css?v={style_version}">
  <title>{esc(title)} — Bronisław Kaper, 1902–1939</title>
</head>
<body>
  <header class="site-header" data-site-header>
    <a class="skip-link" href="#main-content">Skip to content</a>
    <div class="site-header__inner shell">
      <a class="brand" href="index.html"><span class="brand__monogram" aria-hidden="true">BK</span><span class="brand__text"><strong>Bronisław Kaper</strong><small>A source-based archive · 1902–1939</small></span></a>
      <nav class="site-nav" aria-label="Primary navigation"><a href="index.html">Home</a><a href="works.html">Works</a><a href="life.html">Timeline</a><a href="map.html">Map</a><a href="media.html">Media</a></nav>
    </div>
  </header>
  <main id="main-content">
    <div id="record-root" data-record-type="{esc(record_type)}" data-record-id="{esc(record_id)}">
      <section class="record-hero">
        <div class="shell record-hero__grid">
          <div><p class="eyebrow">{esc(label)} · <span class="record-id">{esc(record_id)}</span></p><h1>{esc(title)}</h1></div>
          <dl class="record-facts">{facts}</dl>
        </div>
      </section>
      <section class="section"><div class="shell record-layout"><div><section class="record-section"><h2>Summary</h2><p class="lead">{esc(summary)}</p></section>{sources}</div></div></section>
    </div>
  </main>
  <footer class="site-footer" data-site-footer><div class="shell"><p>Bronisław Kaper research archive · documented through 1939</p></div></footer>
  <script type="module" src="assets/site/record-detail-20260714.js?v={record_script_version}"></script>
</body>
</html>
"""


def expected_outputs(root: Path) -> tuple[dict[Path, str], str, dict]:
    record_root = root / "data/site/records"
    outputs: dict[Path, str] = {}
    routes = []
    counts = {}
    for record_type, table in RECORD_TABLES.items():
        payload_paths = sorted((record_root / record_type).glob("*.json"))
        counts[record_type] = len(payload_paths)
        for payload_path in payload_paths:
            payload = read_json(payload_path)
            tables = payload["tables"]
            record = next(item for item in tables[table] if item["id"] == payload["id"])
            output = root / "records" / record_type / payload["id"] / "index.html"
            outputs[output] = static_page(record_type, record, tables)
            routes.append(f"records/{record_type}/{quote(payload['id'], safe='')}/")
    sitemap_urls = [f"{ORIGIN}{path}" for path in PUBLIC_PAGES]
    sitemap_urls.extend(f"{ORIGIN}{route}" for route in routes)
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "".join(f"  <url><loc>{esc(url)}</loc></url>\n" for url in sitemap_urls)
    sitemap += "</urlset>\n"
    report = {
        "schemaVersion": "1.0.0",
        "recordPageCount": len(outputs),
        "countsByType": counts,
        "sitemapUrlCount": len(sitemap_urls),
        "sitemapBytes": len(sitemap.encode("utf-8")),
    }
    return outputs, sitemap, report


def build(root: Path) -> dict:
    outputs, sitemap, report = expected_outputs(root)
    static_root = root / "records"
    if static_root.exists():
        shutil.rmtree(static_root)
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (root / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (root / "data/site/static-record-report.json").write_text(
        json.dumps(report, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return report


def check(root: Path) -> list[str]:
    outputs, sitemap, report = expected_outputs(root)
    errors = []
    for path, expected in outputs.items():
        if not path.is_file():
            errors.append(f"Missing static record page: {path.relative_to(root)}")
        elif path.read_text(encoding="utf-8") != expected:
            errors.append(f"Stale static record page: {path.relative_to(root)}")
    actual = set((root / "records").glob("*/*/index.html")) if (root / "records").is_dir() else set()
    unexpected = actual - set(outputs)
    for path in sorted(unexpected):
        errors.append(f"Unexpected static record page: {path.relative_to(root)}")
    if not (root / "sitemap.xml").is_file() or (root / "sitemap.xml").read_text(encoding="utf-8") != sitemap:
        errors.append("Sitemap is stale")
    report_path = root / "data/site/static-record-report.json"
    if not report_path.is_file() or read_json(report_path) != report:
        errors.append("Static record report is stale")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.check:
        errors = check(root)
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        return 0 if not errors else 1
    report = build(root)
    print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
