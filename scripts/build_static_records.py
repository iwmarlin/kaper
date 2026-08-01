#!/usr/bin/env python3
"""Generate crawlable HTML record pages and a complete sitemap."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote, urlsplit


ORIGIN = "https://iwmarlin.github.io/kaper/"
PUBLIC_PAGES = ["", "works.html", "people.html", "life.html", "map.html", "media.html"]
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
PERIOD_META = {
    "warsaw": ("Warsaw", "1902–1926"),
    "european": ("European", "1926–1934"),
    "hollywood": ("Hollywood", "1935–1939"),
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


def period_label(value: str) -> str:
    key = str(value or "").strip().lower().replace(" ", "_")
    label, year_range = PERIOD_META.get(key, (str(value or ""), ""))
    return f"{label} · {year_range}" if year_range else label


def period_labels(record: dict) -> str:
    values = record.get("periods") or [record.get("period")]
    return ", ".join(period_label(value) for value in values if value)


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


AUTHORITY_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")
AUTHORITY_URL_TRAILING_PUNCTUATION = ".,;:!?"


def authority_urls(value) -> list[str]:
    """Extract stable HTTP(S) identity links from a labelled authority field."""
    if isinstance(value, list):
        candidates = value
    else:
        candidates = [value]
    urls: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        for match in AUTHORITY_URL_PATTERN.findall(str(candidate or "")):
            url = match.rstrip(AUTHORITY_URL_TRAILING_PUNCTUATION)
            parsed = urlsplit(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                continue
            if url not in seen:
                seen.add(url)
                urls.append(url)
    return urls


def title_for(record_type: str, record: dict) -> str:
    if record_type == "place":
        return record.get("displayName") or record["id"]
    if record_type in {"person", "organization"}:
        return record.get("displayName") or record["id"]
    if record_type == "source":
        return record.get("title") or record.get("shortCitation") or record["id"]
    return record.get("title") or record["id"]


def _names(ids, index) -> list[str]:
    return [index[i]["displayName"] for i in (ids or []) if i in index and index[i].get("displayName")]


def _people_index(tables: dict) -> dict:
    return {item["id"]: item for item in tables.get("people", [])}


def _org_index(tables: dict) -> dict:
    return {item["id"]: item for item in tables.get("organizations", [])}


def credited(tables: dict, work_id: str, role: str) -> list[str]:
    """Names credited in a given role on this work, people first then organizations."""
    people, orgs = _people_index(tables), _org_index(tables)
    out: list[str] = []
    for item in sorted(tables.get("contributions", []), key=lambda c: c.get("sortOrder") or 999):
        if item.get("role") != role or work_id not in (item.get("workIds") or []):
            continue
        out.extend(_names(item.get("personIds"), people))
        out.extend(_names(item.get("organizationIds"), orgs))
    return list(dict.fromkeys(out))


def join_names(names: list[str], limit: int = 3) -> str:
    if not names:
        return ""
    shown = names[:limit]
    text = " and ".join([", ".join(shown[:-1]), shown[-1]]) if len(shown) > 1 else shown[0]
    return f"{text} and others" if len(names) > limit else text


def related_film_titles(record: dict, tables: dict) -> list[str]:
    works = {item["id"]: item for item in tables.get("works", [])}
    titles = []
    for relation in tables.get("workRelations", []):
        if relation.get("relationType") != "associated_with_film":
            continue
        if record["id"] not in (relation.get("sourceWorkIds") or []):
            continue
        for target in relation.get("targetWorkIds") or []:
            title = works.get(target, {}).get("title")
            if title:
                titles.append(title)
    return list(dict.fromkeys(titles))


def work_summary(record: dict, tables: dict, subtype: dict) -> str:
    """Factual, record-specific summary used when no curated note exists."""
    work_type = str(record.get("workType") or "Work")
    year = record.get("year")
    composers = join_names(credited(tables, record["id"], "composer"))
    lyricists = join_names(credited(tables, record["id"], "lyricist"))
    directors = join_names(credited(tables, record["id"], "film_director"))
    companies = join_names(credited(tables, record["id"], "production_company"), limit=2)
    publisher = subtype.get("publisherAsPrinted") or join_names(
        credited(tables, record["id"], "publisher"), limit=1
    )
    opening = f"{work_type}" + (f" ({year})" if year else "")
    parts: list[str] = []
    if work_type.lower() == "film":
        if directors:
            opening += f" directed by {directors}"
        if companies:
            opening += f", produced by {companies}"
        parts.append(opening + ".")
        if composers:
            parts.append(f"Music by {composers}.")
    else:
        if composers:
            opening += f" by {composers}"
        if lyricists:
            opening += f", words by {lyricists}"
        parts.append(opening + ".")
        films = related_film_titles(record, tables)
        if films:
            parts.append(f"Associated with the film {join_names(films, limit=2)}.")
        if publisher:
            parts.append(f"Published by {publisher}.")
    count = len(record.get("sourceIds") or [])
    if count:
        parts.append(f"{count} linked source{'s' if count != 1 else ''}.")
    return " ".join(parts)


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
            or work_summary(record, tables, subtype)
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
    # Sources: lead with the short citation, which identifies the item, because many full
    # citations share an identical opening (catalogue volumes) and would truncate alike.
    short = compact_text(record.get("shortCitation") or record.get("title"))
    full = compact_text(record.get("fullCitation"))
    if short and full and not full.startswith(short[:40]):
        return compact_text(f"{short} {full}")
    return compact_text(full or short)


def facts_for(record_type: str, record: dict) -> list[tuple[str, str]]:
    if record_type == "work":
        return [("Year", record.get("year")), ("Type", record.get("workType")), ("Period", period_labels(record))]
    if record_type == "event":
        return [
            ("Date", record.get("displayDate") or record.get("dateStart")),
            ("Period", period_labels(record)),
            ("Place", record.get("placeDisplay")),
            ("Category", record.get("category")),
        ]
    if record_type == "place":
        return [("City", record.get("city")), ("Country", record.get("country")), ("Type", record.get("placeType")), ("Period", period_labels(record))]
    if record_type == "media":
        if record.get("mediaType") == "document_gallery":
            return [("Images", len(record.get("assetPaths", []))), ("Period", period_labels(record))]
        return [("Media type", record.get("mediaType")), ("Period", period_labels(record)), ("Rights", record.get("rightsStatus"))]
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


SCHEMA_TYPE = {
    "person": "Person",
    "organization": "Organization",
    "place": "Place",
    "work": "CreativeWork",
    "event": "Event",
    "media": "ImageObject",
    "source": "CreativeWork",
}

DEFAULT_OG_IMAGE = f"{ORIGIN}assets/images/portraits/kaper-mature.jpg"


def og_image_for(record_type: str, record: dict) -> str:
    if (
        record_type == "media"
        and record.get("mediaType") == "image"
        and record.get("assetPath")
    ):
        return f"{ORIGIN}{record['assetPath']}"
    return DEFAULT_OG_IMAGE


WORK_SCHEMA_TYPE = {"song": "MusicComposition", "film": "Movie"}


def agent_entities(tables: dict, work_id: str, role: str) -> list[dict]:
    """Linked-data entities for a credited role, carrying record URLs and authority IDs."""
    people, orgs = _people_index(tables), _org_index(tables)
    out: list[dict] = []
    seen: set[str] = set()
    for item in sorted(tables.get("contributions", []), key=lambda c: c.get("sortOrder") or 999):
        if item.get("role") != role or work_id not in (item.get("workIds") or []):
            continue
        for pid in item.get("personIds") or []:
            person = people.get(pid)
            if not person or pid in seen:
                continue
            seen.add(pid)
            entity = {
                "@type": "Person",
                "name": person.get("displayName"),
                "@id": f"{ORIGIN}records/person/{quote(pid, safe='')}/",
            }
            authorities = authority_urls(person.get("authorityUrl"))
            if authorities:
                entity["sameAs"] = authorities[0] if len(authorities) == 1 else authorities
            out.append(entity)
        for oid in item.get("organizationIds") or []:
            org = orgs.get(oid)
            if not org or oid in seen:
                continue
            seen.add(oid)
            out.append({
                "@type": "Organization",
                "name": org.get("displayName"),
                "@id": f"{ORIGIN}records/organization/{quote(oid, safe='')}/",
            })
    return out


def work_structured_data(record: dict, tables: dict, data: dict) -> None:
    work_type = str(record.get("workType") or "").lower()
    data["@type"] = WORK_SCHEMA_TYPE.get(work_type, "CreativeWork")
    if record.get("year"):
        data["datePublished"] = str(record["year"])
    mapping = (
        [("director", "film_director"), ("musicBy", "composer"), ("productionCompany", "production_company")]
        if work_type == "film"
        else [("composer", "composer"), ("lyricist", "lyricist"), ("publisher", "publisher")]
    )
    for key, role in mapping:
        entities = agent_entities(tables, record["id"], role)
        if entities:
            data[key] = entities[0] if len(entities) == 1 else entities
    works = {item["id"]: item for item in tables.get("works", [])}
    parents = []
    for relation in tables.get("workRelations", []):
        if relation.get("relationType") != "associated_with_film":
            continue
        if record["id"] not in (relation.get("sourceWorkIds") or []):
            continue
        for target in relation.get("targetWorkIds") or []:
            film = works.get(target)
            if film:
                parents.append({
                    "@type": "Movie",
                    "name": film.get("title"),
                    "@id": f"{ORIGIN}records/work/{quote(target, safe='')}/",
                })
    if parents:
        data["isPartOf"] = parents[0] if len(parents) == 1 else parents


def structured_data(
    record_type: str, record: dict, canonical: str, title: str, summary: str, tables: dict | None = None
) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": SCHEMA_TYPE.get(record_type, "CreativeWork"),
        "name": title,
        "url": canonical,
    }
    if summary:
        data["description"] = compact_text(summary, 300)
    if record_type == "work":
        work_structured_data(record, tables or {}, data)
    if record_type == "source":
        link = record.get("primaryUrl") or record.get("accessUrl")
        if link:
            data["sameAs"] = link
        # schema.org expects ISO 8601; archival date strings such as "[1938?]" or
        # "1935; copyright June 3, 1935" are kept out of the machine-readable field.
        iso = re.match(r"\s*(\d{4}(?:-\d{2}(?:-\d{2})?)?)\s*$", str(record.get("date") or ""))
        if iso:
            data["datePublished"] = iso.group(1)
        if record.get("creator"):
            data["creator"] = {"@type": "Person", "name": record["creator"]}
        if record.get("repository"):
            data["holdingArchive"] = {"@type": "Organization", "name": record["repository"]}
    if record_type == "person":
        same_as = authority_urls(record.get("authorityUrl"))
        if same_as:
            data["sameAs"] = same_as[0] if len(same_as) == 1 else same_as
    if record_type == "place":
        lat, lon = record.get("latitude"), record.get("longitude")
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            data["geo"] = {"@type": "GeoCoordinates", "latitude": lat, "longitude": lon}
        locality = ", ".join(v for v in (record.get("city"), record.get("country")) if v)
        if locality:
            data["address"] = locality
    if record_type == "event" and record.get("dateStart"):
        data["startDate"] = record["dateStart"]
    if record_type == "media" and record.get("assetPath"):
        data["contentUrl"] = f"{ORIGIN}{record['assetPath']}"
        if record.get("publicCreditLine"):
            data["creditText"] = record["publicCreditLine"]
    payload = json.dumps(data, ensure_ascii=False)
    return f'<script type="application/ld+json">{payload}</script>'


def static_page(record_type: str, record: dict, tables: dict) -> str:
    title = title_for(record_type, record)
    summary = summary_for(record_type, record, tables)
    meta_summary = summary or f"{title}, a documented record in the Bronisław Kaper research archive."
    label = TYPE_LABELS[record_type]
    # Media, source and organization titles collide with work titles across the archive;
    # qualifying them keeps every <title> distinct in search results.
    page_title = title if record_type in {"work", "person", "place", "event"} else f"{title} ({label.lower()})"
    record_id = record["id"]
    is_gallery = record_type == "media" and record.get("mediaType") == "document_gallery"
    style_version = "d436156396"
    record_script_version = "d436156396"
    route = f"records/{record_type}/{quote(record_id, safe='')}/"
    canonical = f"{ORIGIN}{route}"
    facts = "".join(
        f"<div><dt>{esc(label_text)}</dt><dd>{esc(value)}</dd></div>"
        for label_text, value in facts_for(record_type, record)
        if value not in (None, "", [])
    )
    sources = "" if is_gallery else source_links(record_type, record, tables)
    summary_section = (
        f'<section class="record-section"><h2>Summary</h2><p class="lead">{esc(summary)}</p></section>'
        if summary
        else ""
    )
    og_image = og_image_for(record_type, record)
    ld_json = structured_data(record_type, record, canonical, title, meta_summary, tables)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="{esc(CSP)}">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <base href="../../../">
  <meta name="description" content="{esc(compact_text(meta_summary, 180))}">
  <meta name="theme-color" content="#152c33">
  <meta name="robots" content="index,follow">
  <meta property="og:title" content="{esc(title)} — Bronisław Kaper archive">
  <meta property="og:description" content="{esc(compact_text(meta_summary, 200))}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:image" content="{esc(og_image)}">
  <meta property="og:image:alt" content="{esc(title)}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <link rel="icon" href="favicon.ico" sizes="any">
  <link rel="apple-touch-icon" href="apple-touch-icon.png">
  <link rel="stylesheet" href="assets/site/styles.css?v={style_version}">
  <title>{esc(page_title)} — Bronisław Kaper, 1902–1939</title>
  {ld_json}
</head>
<body>
  <a class="skip-link" href="#main-content">Skip to main content</a>
  <header class="site-header" data-site-header>
    <div class="site-header__inner shell">
      <a class="brand" href="index.html"><span class="brand__monogram" aria-hidden="true">BK</span><span class="brand__text"><strong>Bronisław Kaper</strong><small>A source-based archive · 1902–1939</small></span></a>
      <nav class="site-nav" aria-label="Primary navigation"><a href="index.html">Home</a><a href="works.html">Works</a><a href="people.html">People</a><a href="life.html">Timeline</a><a href="map.html">Map</a><a href="media.html">Media</a></nav>
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
      <section class="section"><div class="shell record-layout"><div>{summary_section}{sources}</div></div></section>
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
    lastmod = ""
    manifest_path = root / "data/public/v1/manifest.json"
    if manifest_path.is_file():
        snapshot = str(read_json(manifest_path).get("sourceSnapshot") or "")
        match = re.match(r"(\d{4}-\d{2}-\d{2})", snapshot)
        if match:
            lastmod = match.group(1)
    stamp = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "".join(f"  <url><loc>{esc(url)}</loc>{stamp}</url>\n" for url in sitemap_urls)
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
