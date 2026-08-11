#!/usr/bin/env python3
"""Generate crawlable HTML record pages and a complete sitemap."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Optional
from urllib.parse import quote, urlsplit


ORIGIN = "https://iwmarlin.github.io/kaper/"
PUBLIC_PAGES = ["", "works.html", "people.html", "life.html", "map.html", "media.html"]
SITEMAP_STATE_PATH = Path("data/site/sitemap-state.json")
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
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


def render_static_record_bodies(root: Path) -> dict[str, str]:
    """Render every record with the browser's canonical view templates.

    This keeps crawlable HTML and the JavaScript-enhanced view structurally
    identical instead of maintaining a second, abbreviated Python template.
    """
    node = shutil.which("node")
    if not node:
        bundled = (
            Path.home()
            / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
        )
        if bundled.is_file():
            node = str(bundled)
    if not node:
        raise RuntimeError(
            "Node.js is required to prerender complete record pages with the shared renderer"
        )
    runner = root / "scripts/render_static_record_bodies.mjs"
    try:
        result = subprocess.run(
            [node, str(runner), str(root)],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        rendered = json.loads(result.stdout)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        detail = getattr(error, "stderr", "") or str(error)
        raise RuntimeError(f"Complete record prerendering failed: {detail.strip()}") from error
    if not isinstance(rendered, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in rendered.items()
    ):
        raise RuntimeError("Complete record prerendering returned an invalid payload")
    return rendered


def content_hash(text: str) -> str:
    """Return a stable digest for the exact public representation of a route."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_sitemap_state(root: Path) -> dict:
    path = root / SITEMAP_STATE_PATH
    if not path.is_file():
        return {}
    payload = read_json(path)
    if payload.get("schemaVersion") != "1.0.0":
        return {}
    entries = payload.get("entries")
    return entries if isinstance(entries, dict) else {}


def sitemap_route_documents(root: Path, outputs: dict[Path, str], routes: list[str]) -> dict[str, str]:
    """Map each canonical sitemap URL to the HTML whose changes it represents."""
    documents: dict[str, str] = {}
    for public_path in PUBLIC_PAGES:
        disk_path = root / (public_path or "index.html")
        documents[f"{ORIGIN}{public_path}"] = disk_path.read_text(encoding="utf-8")
    for route in routes:
        disk_path = root / route / "index.html"
        expected = outputs.get(disk_path)
        if expected is None:
            raise RuntimeError(f"No generated document found for sitemap route {route}")
        documents[f"{ORIGIN}{route}"] = expected
    return documents


def sitemap_disk_path(root: Path, url: str) -> Path:
    relative = url.removeprefix(ORIGIN)
    if not relative:
        return root / "index.html"
    path = root / relative
    return path / "index.html" if relative.endswith("/") else path


def git_lastmod_dates(root: Path, documents: dict[str, str]) -> dict[str, str]:
    """Seed first-run dates from the latest commit that changed each public page."""
    paths_by_url: dict[str, Path] = {}
    for url, expected in documents.items():
        path = sitemap_disk_path(root, url)
        # A modified or newly generated page belongs to the upcoming publication,
        # not to its previous Git commit.
        if path.is_file() and path.read_text(encoding="utf-8") == expected:
            paths_by_url[url] = path.relative_to(root)
    if not paths_by_url:
        return {}
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--format=@@%cs",
                "--name-only",
                "--",
                *(path.as_posix() for path in paths_by_url.values()),
            ],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return {}
    latest_by_path: dict[str, str] = {}
    current_date = ""
    for line in result.stdout.splitlines():
        if line.startswith("@@"):
            current_date = line[2:]
        elif line and current_date and line not in latest_by_path:
            latest_by_path[line] = current_date
    return {
        url: latest_by_path.get(path.as_posix(), "")
        for url, path in paths_by_url.items()
        if ISO_DATE_PATTERN.fullmatch(latest_by_path.get(path.as_posix(), ""))
    }


def updated_sitemap_state(
    documents: dict[str, str],
    previous: dict,
    publication_date: Optional[str],
    initial_dates: Optional[dict[str, str]] = None,
) -> tuple[dict, list[str], int]:
    """Preserve lastmod for unchanged content and date only new or changed routes."""
    entries: dict[str, dict[str, str]] = {}
    stale_routes: list[str] = []
    updated_count = 0
    for url, document in documents.items():
        digest = content_hash(document)
        old = previous.get(url) if isinstance(previous.get(url), dict) else {}
        old_date = str(old.get("lastmod") or "")
        if old.get("contentHash") == digest and ISO_DATE_PATTERN.fullmatch(old_date):
            lastmod = old_date
        elif initial_dates and ISO_DATE_PATTERN.fullmatch(initial_dates.get(url, "")):
            lastmod = initial_dates[url]
        elif publication_date:
            lastmod = publication_date
            updated_count += 1
        else:
            # Check mode must never invent a publication date. Retaining the old
            # value here lets the caller report the precise stale routes while
            # keeping the expected sitemap structurally comparable.
            lastmod = old_date
            stale_routes.append(url)
        entries[url] = {"contentHash": digest, "lastmod": lastmod}
    return entries, stale_routes, updated_count


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


def summary_for(
    record_type: str,
    record: dict,
    tables: dict,
    source_description_counts: Optional[dict[str, int]] = None,
) -> str:
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
    # Never concatenate the short and full forms of the same citation. Prefer the
    # fuller description when its search-result excerpt is unique; catalogue
    # families whose full citations truncate identically use their concise,
    # record-specific citation instead.
    short = compact_text(record.get("shortCitation") or record.get("title"))
    full = compact_text(record.get("fullCitation"))
    full_excerpt = compact_text(full, 180)
    if full and (source_description_counts or {}).get(full_excerpt, 1) == 1:
        return full
    return short or full


SCHEMA_TYPE = {
    "person": "Person",
    "organization": "Organization",
    "place": "Place",
    "work": "CreativeWork",
    "event": "Event",
    "media": "ImageObject",
    "source": "CreativeWork",
}

NEUTRAL_OG_IMAGE_PATH = "apple-touch-icon.png"
IMAGE_ASSET_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def image_asset_path(media: dict) -> str:
    """Return the first browser-shareable local image carried by a media record."""
    candidates = [media.get("assetPath"), *(media.get("assetPaths") or [])]
    for candidate in candidates:
        path = str(candidate or "").strip()
        if Path(urlsplit(path).path).suffix.lower() in IMAGE_ASSET_SUFFIXES:
            return path
    return ""


def og_image_for(record_type: str, record: dict, tables: dict) -> dict:
    """Choose a record-specific social image without borrowing another identity.

    Person payloads contain only portraits already verified as belonging to that
    person by build_record_payloads.py. Works, events and places retain the order
    of their explicit media links; event hero media take priority. A neutral
    archive mark is used when no suitable local image exists.
    """
    media_by_id = {item["id"]: item for item in tables.get("media", [])}
    candidates: list[dict] = []
    if record_type == "media":
        candidates = [record]
    elif record_type == "person":
        candidates = [
            item for item in tables.get("media", [])
            if item.get("category") == "portrait"
        ]
    elif record_type in {"work", "place", "event"}:
        hero_ids = (record.get("heroMediaIds") or []) if record_type == "event" else []
        linked_ids = [
            *hero_ids,
            *(record.get("mediaIds") or []),
        ]
        candidates = [
            media_by_id[media_id]
            for media_id in dict.fromkeys(linked_ids)
            if media_id in media_by_id
        ]

    for media in candidates:
        path = image_asset_path(media)
        if path:
            return {
                "url": f"{ORIGIN}{quote(path, safe='/')}",
                "alt": media.get("altText") or media.get("title") or title_for(record_type, record),
                "neutral": False,
                "portrait": media.get("category") == "portrait",
            }
    return {
        "url": f"{ORIGIN}{NEUTRAL_OG_IMAGE_PATH}",
        "alt": "Bronisław Kaper research archive",
        "neutral": True,
        "portrait": False,
    }


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


def static_page(
    record_type: str,
    record: dict,
    tables: dict,
    source_description_counts: dict[str, int],
    body_markup: str,
) -> str:
    title = title_for(record_type, record)
    summary = summary_for(record_type, record, tables, source_description_counts)
    meta_summary = summary or f"{title}, a documented record in the Bronisław Kaper research archive."
    label = TYPE_LABELS[record_type]
    # Media, source and organization titles collide with work titles across the archive;
    # qualifying them keeps every <title> distinct in search results.
    page_title = title if record_type in {"work", "person", "place", "event"} else f"{title} ({label.lower()})"
    record_id = record["id"]
    style_version = "7760050c5f"
    record_script_version = "7760050c5f"
    route = f"records/{record_type}/{quote(record_id, safe='')}/"
    canonical = f"{ORIGIN}{route}"
    og_image = og_image_for(record_type, record, tables)
    og_image_size = (
        '\n  <meta property="og:image:width" content="180">'
        '\n  <meta property="og:image:height" content="180">'
        if og_image["neutral"] else ""
    )
    twitter_card = "summary" if og_image["neutral"] or og_image["portrait"] else "summary_large_image"
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
  <meta property="og:image" content="{esc(og_image['url'])}">
  <meta property="og:image:alt" content="{esc(og_image['alt'])}">{og_image_size}
  <meta name="twitter:card" content="{twitter_card}">
  <meta name="twitter:image" content="{esc(og_image['url'])}">
  <meta name="twitter:image:alt" content="{esc(og_image['alt'])}">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <link rel="icon" href="favicon.ico" sizes="any">
  <link rel="apple-touch-icon" href="apple-touch-icon.png">
  <link rel="preload" href="assets/fonts/kaper-sans.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="assets/fonts/kaper-serif.woff2" as="font" type="font/woff2" crossorigin>
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
    <div id="record-root" data-record-type="{esc(record_type)}" data-record-id="{esc(record_id)}" data-prerendered="true">{body_markup}</div>
  </main>
  <footer class="site-footer" data-site-footer><div class="shell"><p>Bronisław Kaper research archive · documented through 1939</p></div></footer>
  <script type="module" src="assets/site/record-detail-20260714.js?v={record_script_version}"></script>
</body>
</html>
"""


def expected_outputs(
    root: Path,
    previous_sitemap_state: dict,
    publication_date: Optional[str],
    initial_dates: Optional[dict[str, str]] = None,
) -> tuple[dict[Path, str], str, dict, dict, list[str]]:
    record_root = root / "data/site/records"
    public_sources = read_json(root / "data/public/v1/sources.json").get("records", [])
    source_description_counts = Counter(
        compact_text(compact_text(item.get("fullCitation")), 180)
        for item in public_sources
        if item.get("fullCitation")
    )
    rendered_bodies = render_static_record_bodies(root)
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
            body_key = f"{record_type}/{payload['id']}"
            if body_key not in rendered_bodies:
                raise RuntimeError(f"Missing prerendered record body: {body_key}")
            outputs[output] = static_page(
                record_type,
                record,
                tables,
                source_description_counts,
                rendered_bodies[body_key],
            )
            routes.append(f"records/{record_type}/{quote(payload['id'], safe='')}/")
    documents = sitemap_route_documents(root, outputs, routes)
    sitemap_state, stale_routes, updated_count = updated_sitemap_state(
        documents,
        previous_sitemap_state,
        publication_date,
        initial_dates,
    )
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "".join(
        f"  <url><loc>{esc(url)}</loc><lastmod>{sitemap_state[url]['lastmod']}</lastmod></url>\n"
        for url in documents
    )
    sitemap += "</urlset>\n"
    lastmod_dates = sorted({entry["lastmod"] for entry in sitemap_state.values() if entry["lastmod"]})
    report = {
        "schemaVersion": "1.0.0",
        "recordPageCount": len(outputs),
        "completePrerenderedPageCount": len(outputs),
        "progressiveEnhancement": True,
        "countsByType": counts,
        "sitemapUrlCount": len(documents),
        "sitemapBytes": len(sitemap.encode("utf-8")),
        "sitemapLastmod": {
            "dateCount": len(lastmod_dates),
            "earliest": lastmod_dates[0] if lastmod_dates else "",
            "latest": lastmod_dates[-1] if lastmod_dates else "",
        },
    }
    state_payload = {
        "schemaVersion": "1.0.0",
        "entries": sitemap_state,
    }
    return outputs, sitemap, report, state_payload, stale_routes


def build(root: Path, publication_date: str) -> dict:
    previous_state = read_sitemap_state(root)
    initial_dates = None
    if not previous_state:
        # Render once to identify the exact current route documents, then use Git
        # only to seed dates for pages whose committed HTML already matches them.
        seed_outputs, _, _, _, _ = expected_outputs(root, {}, publication_date)
        seed_routes = [
            path.relative_to(root).parent.as_posix() + "/"
            for path in seed_outputs
        ]
        initial_dates = git_lastmod_dates(
            root,
            sitemap_route_documents(root, seed_outputs, seed_routes),
        )
    outputs, sitemap, report, state, _ = expected_outputs(
        root,
        previous_state,
        publication_date,
        initial_dates,
    )
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
    (root / SITEMAP_STATE_PATH).write_text(
        json.dumps(state, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def check(root: Path) -> list[str]:
    state_path = root / SITEMAP_STATE_PATH
    previous_state = read_sitemap_state(root)
    outputs, sitemap, report, state, stale_routes = expected_outputs(
        root,
        previous_state,
        None,
    )
    errors = []
    if not state_path.is_file():
        errors.append(f"Missing sitemap state: {SITEMAP_STATE_PATH}")
    for url in stale_routes:
        errors.append(f"Stale sitemap state for route: {url}")
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
    if state_path.is_file() and read_json(state_path) != state:
        errors.append("Sitemap state is stale")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--publication-date",
        help="ISO date assigned only to routes whose public HTML changed (default: today)",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    if args.check:
        if args.publication_date:
            parser.error("--publication-date cannot be used with --check")
        errors = check(root)
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        return 0 if not errors else 1
    publication_date = args.publication_date or date.today().isoformat()
    if not ISO_DATE_PATTERN.fullmatch(publication_date):
        parser.error("--publication-date must use YYYY-MM-DD")
    try:
        date.fromisoformat(publication_date)
    except ValueError:
        parser.error("--publication-date must be a valid calendar date")
    report = build(root, publication_date)
    print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
