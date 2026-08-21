#!/usr/bin/env python3
"""Validate the static research website and its public data references."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


PUBLIC_PAGES = [
    "index.html",
    "works.html",
    "people.html",
    "life.html",
    "map.html",
    "media.html",
    "record.html",
    "404.html",
]

# Pages that must appear in sitemap.xml (record.html and 404.html are shells, not routes).
SITEMAP_PAGES = PUBLIC_PAGES[:6]

PRERENDERED_RELATION_SECTIONS = {
    "work": {
        "contributionIds": "Contributors and credits",
        "titleVariantIds": "Title variants",
        "relationIds": "Related works and versions",
        "timelineEventIds": "Timeline",
        "sourceIds": "Sources",
    },
    "event": {
        "personIds": "People",
        "workIds": "Works",
        "organizationIds": "Organizations",
        "placeIds": "Places",
        "sourceIds": "Sources",
    },
    "place": {
        "timelineEventIds": "Documented events",
        "personIds": "People",
        "sourceIds": "Sources",
    },
    "media": {
        "workIds": "Related works",
        "timelineEventIds": "Timeline",
        "placeIds": "Places",
        "organizationIds": "Organizations",
    },
    "person": {
        "workIds": "Documented works",
        "timelineEventIds": "Documented chronology",
        "contributionIds": "Evidence for documented credits",
        "sourceIds": "Sources linked directly to this person",
    },
    "organization": {
        "workIds": "Works",
        "timelineEventIds": "Timeline",
        "sourceIds": "Sources",
    },
    "source": {
        "workIds": "Supported works",
        "mediaIds": "Media",
        "timelineEventIds": "Timeline",
        "placeIds": "Places",
        "personIds": "People",
        "organizationIds": "Organizations",
    },
}

PRERENDERED_RELATION_LINKS = {
    "work": {"timelineEventIds": "event", "sourceIds": "source", "mediaIds": "media"},
    "event": {
        "personIds": "person",
        "workIds": "work",
        "organizationIds": "organization",
        "placeIds": "place",
        "sourceIds": "source",
        "mediaIds": "media",
    },
    "place": {
        "timelineEventIds": "event",
        "personIds": "person",
        "sourceIds": "source",
        "mediaIds": "media",
    },
    "media": {
        "workIds": "work",
        "timelineEventIds": "event",
        "placeIds": "place",
        "organizationIds": "organization",
        "sourceIds": "source",
    },
    "person": {"workIds": "work", "timelineEventIds": "event", "sourceIds": "source"},
    "organization": {"workIds": "work", "timelineEventIds": "event", "sourceIds": "source"},
    "source": {
        "workIds": "work",
        "mediaIds": "media",
        "timelineEventIds": "event",
        "placeIds": "place",
        "personIds": "person",
        "organizationIds": "organization",
    },
}

MEDIA_SCHEMA_TYPES = {
    "audio": "AudioObject",
    "video": "VideoObject",
    "image": "ImageObject",
    "sheet music": "ImageObject",
    "document_gallery": "CollectionPage",
}

ASSET_REFERENCE_RE = re.compile(
    r'((?:assets/site/|\./)[A-Za-z0-9._/-]+\.(?:css|js))\?v=([A-Za-z0-9._-]+)'
)
ASSET_VERSION_RE = re.compile(r'\?v=[A-Za-z0-9._-]+')


class ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[tuple[str, str]] = []
        self.iframes = 0
        self.lang: str | None = None
        self.has_viewport = False
        self.has_title = False
        self.canonicals: list[str] = []
        self.has_csp_meta = False
        self.referrer_policy: str | None = None
        self.skip_links = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html":
            self.lang = values.get("lang")
        if tag == "meta" and values.get("name") == "viewport":
            self.has_viewport = True
        if tag == "meta" and values.get("http-equiv", "").lower() == "content-security-policy":
            self.has_csp_meta = bool(values.get("content"))
        if tag == "meta" and values.get("name") == "referrer":
            self.referrer_policy = values.get("content")
        if tag == "link" and values.get("rel") == "canonical" and values.get("href"):
            self.canonicals.append(values["href"])
        if tag == "iframe":
            self.iframes += 1
        if tag == "a" and "skip-link" in (values.get("class") or "").split():
            self.skip_links += 1
        for attribute in ("href", "src"):
            if values.get(attribute):
                self.references.append((attribute, values[attribute]))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        if getattr(self, "_in_title", False) and data.strip():
            self.has_title = True

    def handle_starttag_with_title(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._in_title = tag == "title"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def expected_asset_version(root: Path) -> str:
    """Return the content-derived version used by scripts/stamp_assets.py."""
    site = root / "assets/site"
    parts: list[str] = []
    for path in sorted(site.glob("*.css")) + sorted(site.glob("*.js")):
        normalized = ASSET_VERSION_RE.sub("?v=", path.read_text(encoding="utf-8"))
        parts.append(path.name + "\0" + normalized)
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:10]


def stale_asset_references(root: Path, expected: str) -> list[str]:
    """Find pages or modules that can keep an obsolete CSS/JS bundle cached."""
    candidates = [*root.glob("*.html"), *(root / "assets/site").glob("*.js")]
    candidates.extend((root / "records").glob("*/*/index.html"))
    stale: list[str] = []
    for path in candidates:
        text = path.read_text(encoding="utf-8")
        versions = {
            version for _, version in ASSET_REFERENCE_RE.findall(text)
            if version != expected
        }
        if versions:
            stale.append(path.relative_to(root).as_posix())
    return stale


def local_target(root: Path, page: Path, value: str) -> Path | None:
    if value.startswith(("#", "data:", "mailto:", "tel:")):
        return None
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    if not path:
        return None
    if path.startswith("/"):
        return root / path.lstrip("/")
    return page.parent / path


def validate(root: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    parsed_pages: dict[str, ReferenceParser] = {}

    for filename in PUBLIC_PAGES:
        path = root / filename
        if not path.is_file():
            errors.append(f"Missing public page: {filename}")
            continue
        text = path.read_text(encoding="utf-8")
        parser = ReferenceParser()
        parser.feed(text)
        parsed_pages[filename] = parser
        if parser.lang != "en":
            errors.append(f"{filename}: html language is not English")
        if not parser.has_viewport:
            errors.append(f"{filename}: viewport metadata is missing")
        if "<title>" not in text or "</title>" not in text:
            errors.append(f"{filename}: title is missing")
        if parser.iframes:
            errors.append(f"{filename}: automatic iframe embedding is not allowed")
        if not parser.has_csp_meta:
            errors.append(f"{filename}: document CSP fallback is missing")
        if parser.referrer_policy != "strict-origin-when-cross-origin":
            errors.append(f"{filename}: referrer policy fallback is missing")
        if filename not in {"404.html", "record.html"} and len(parser.canonicals) != 1:
            errors.append(f"{filename}: expected exactly one canonical URL")
        if parser.skip_links != 1:
            errors.append(
                f"{filename}: expected exactly one skip link, found {parser.skip_links}"
            )
        for attribute, value in parser.references:
            target = local_target(root, path, value)
            if target is not None and not target.exists():
                errors.append(
                    f"{filename}: broken local {attribute} reference {value!r}"
                )

    required_files = [
        ".nojekyll",
        "netlify.toml",
        "robots.txt",
        "sitemap.xml",
        "assets/site/styles.css",
        "assets/site/core.js",
        "assets/site/image-derivatives.js",
        "data/public/v1/manifest.json",
        "data/public/v1/build-report.json",
        "data/site/home.json",
        "data/site/performance-report.json",
        "data/site/record-report.json",
        "data/site/sitemap-state.json",
        "data/site/static-record-report.json",
    ]
    for filename in required_files:
        if not (root / filename).is_file():
            errors.append(f"Missing deployment file: {filename}")

    # The compact phone portrait may visually hide its long caption, but it
    # must never hide the focusable record link with the entire figcaption.
    home_js_path = root / "assets/site/home.js"
    home_css_path = root / "assets/site/home.css"
    if home_js_path.is_file() and home_css_path.is_file():
        home_js = home_js_path.read_text(encoding="utf-8")
        home_css = home_css_path.read_text(encoding="utf-8")
        if not re.search(
            r'<span class="hero__portrait-caption">.*?</span>\s*'
            r'<a href=',
            home_js,
            flags=re.DOTALL,
        ):
            errors.append(
                "Home portrait must keep the record link outside its visually "
                "hidden caption text"
            )
        if re.search(
            r"\.home-page\s+\.hero__portrait\s+figcaption\s*\{[^}]*"
            r"width:\s*1px",
            home_css,
            flags=re.DOTALL,
        ):
            errors.append(
                "Home portrait figcaption hides a focusable record link on phones"
            )

    manifest_path = root / "data/public/v1/manifest.json"
    home_path = root / "data/site/home.json"
    if manifest_path.is_file() and home_path.is_file():
        counts = read_json(manifest_path).get("counts", {})
        home = read_json(home_path)
        count_keys = {
            "Works": "Works",
            "People": "People",
            "Timeline": "Timeline Events",
            "Places": "Places",
            "Media": "Media",
        }
        for pathway in home.get("pathways", []):
            label = pathway.get("label")
            manifest_key = count_keys.get(label)
            if manifest_key and pathway.get("count") != counts.get(manifest_key):
                errors.append(
                    f"Home-page {label} count does not match the public manifest"
                )
        if home.get("glance", {}).get("sources") != counts.get("Sources"):
            errors.append("Home-page Sources count does not match the public manifest")

    asset_version = expected_asset_version(root)
    stale_assets = stale_asset_references(root, asset_version)
    if stale_assets:
        sample = ", ".join(stale_assets[:5])
        remainder = len(stale_assets) - min(5, len(stale_assets))
        suffix = f" and {remainder} more" if remainder else ""
        errors.append(
            "Stale cache-busting version in "
            f"{sample}{suffix}; expected {asset_version}. "
            "Run scripts/stamp_assets.py and rebuild static records."
        )

    for script in (root / "assets/site").glob("*.js"):
        text = script.read_text(encoding="utf-8")
        for imported in re.findall(r'from\s+["\'](\./[^"\']+)["\']', text):
            target = (script.parent / urlsplit(imported).path).resolve()
            if not target.is_file():
                errors.append(f"{script.relative_to(root)}: missing module {imported}")
    report_path = root / "data/public/v1/build-report.json"
    media_path = root / "data/public/v1/media.json"
    if report_path.is_file():
        report = read_json(report_path)
        if not report.get("ok") or report.get("errors") or report.get("warnings"):
            errors.append("Public data build report is not clean")
    if media_path.is_file():
        media_payload = read_json(media_path)
        for media in media_payload.get("records", []):
            for relative in [media.get("assetPath"), *media.get("assetPaths", [])]:
                if relative and not (root / relative).is_file():
                    errors.append(f"Media {media['id']}: missing asset {relative}")

    performance_path = root / "data/site/performance-report.json"
    if performance_path.is_file():
        performance = read_json(performance_path)
        if performance.get("homePayloadBytes", 0) > 50_000:
            errors.append("Compact home-page payload exceeds 50 KB")
        if performance.get("largestDerivative", {}).get("bytes", 0) > 1_200_000:
            errors.append("A responsive screen derivative exceeds 1.2 MB")
        portrait_default = performance.get("homePortrait", {}).get("default")
        if portrait_default:
            portrait_path = root / portrait_default
            if not portrait_path.is_file():
                errors.append("Responsive home portrait is missing")
            elif portrait_path.stat().st_size > 150_000:
                errors.append("Default responsive home portrait exceeds 150 KB")

    record_report_path = root / "data/site/record-report.json"
    if record_report_path.is_file():
        record_report = read_json(record_report_path)
        baseline = record_report.get("baselineAllTablesBytes", 0)
        largest = record_report.get("largestPayload", {}).get("bytes", 0)
        if not record_report.get("recordCount"):
            errors.append("Record payload report contains no records")
        if not baseline or largest >= baseline:
            errors.append("A record payload is not smaller than the all-table baseline")
        for record_id in ("P009", "W-F004", "M081", "TE0004"):
            if record_id not in record_report.get("examples", {}):
                errors.append(f"Record payload report omits reference record {record_id}")

    sitemap = (root / "sitemap.xml").read_text(encoding="utf-8") if (root / "sitemap.xml").is_file() else ""
    static_report_path = root / "data/site/static-record-report.json"
    sitemap_state_path = root / "data/site/sitemap-state.json"
    if static_report_path.is_file():
        static_report = read_json(static_report_path)
        expected_records = sum(static_report.get("countsByType", {}).values())
        if static_report.get("recordPageCount") != expected_records:
            errors.append("Static record report count is inconsistent")
        if static_report.get("completePrerenderedPageCount") != expected_records:
            errors.append("Not every static record is reported as completely prerendered")
        if static_report.get("progressiveEnhancement") is not True:
            errors.append("Static record report does not confirm progressive enhancement")
        work_seo = static_report.get("workSeo", {})
        if work_seo.get("recordCount") != static_report.get("countsByType", {}).get("work"):
            errors.append("Work SEO report does not cover every static Work page")
        if work_seo.get("longestMetaDescription", 0) > work_seo.get(
            "metaDescriptionLimit", 0
        ):
            errors.append("A Work meta description exceeds its declared length limit")
        if work_seo.get("descriptions", {}).get("duplicateGroupCount") != 0:
            errors.append("Static Work pages contain duplicate meta descriptions")
        if work_seo.get("pageTitles", {}).get("duplicateGroupCount") != 0:
            errors.append("Static Work pages contain duplicate HTML titles")
        static_pages = list((root / "records").glob("*/*/index.html"))
        if len(static_pages) != expected_records:
            errors.append("Static record page count does not match its report")
        sitemap_urls = re.findall(r"<loc>([^<]+)</loc>", sitemap)
        if len(sitemap_urls) != static_report.get("sitemapUrlCount"):
            errors.append("Sitemap URL count does not match the static record report")
        sitemap_entries = dict(
            re.findall(
                r"<url><loc>([^<]+)</loc><lastmod>([^<]+)</lastmod></url>",
                sitemap,
            )
        )
        if len(sitemap_entries) != len(sitemap_urls):
            errors.append("Every sitemap URL must have exactly one lastmod date")
        if sitemap_state_path.is_file():
            sitemap_state = read_json(sitemap_state_path)
            state_entries = sitemap_state.get("entries", {})
            if sitemap_state.get("schemaVersion") != "1.0.0":
                errors.append("Sitemap state has an unsupported schema version")
            if set(state_entries) != set(sitemap_urls):
                errors.append("Sitemap state URLs do not match sitemap.xml")
            for url, entry in state_entries.items():
                lastmod = entry.get("lastmod") if isinstance(entry, dict) else ""
                digest = entry.get("contentHash") if isinstance(entry, dict) else ""
                try:
                    parsed_date = date.fromisoformat(lastmod)
                except (TypeError, ValueError):
                    errors.append(f"Sitemap state has an invalid lastmod date for {url}")
                else:
                    if parsed_date > date.today():
                        errors.append(f"Sitemap state has a future lastmod date for {url}")
                if not re.fullmatch(r"[0-9a-f]{64}", digest or ""):
                    errors.append(f"Sitemap state has an invalid content hash for {url}")
                if sitemap_entries.get(url) != lastmod:
                    errors.append(f"Sitemap lastmod does not match its state for {url}")
        for page in static_pages:
            relative = page.relative_to(root).parent.as_posix() + "/"
            expected_url = f"https://iwmarlin.github.io/kaper/{relative}"
            if expected_url not in sitemap_urls:
                errors.append(f"Sitemap omits static record {relative}")
            page_parser = ReferenceParser()
            text = page.read_text(encoding="utf-8")
            page_parser.feed(text)
            if page_parser.skip_links != 1:
                errors.append(
                    f"{relative}: expected exactly one skip link, "
                    f"found {page_parser.skip_links}"
                )
            if "<base " in text and re.search(r'href=["\']#', text):
                errors.append(
                    f"{relative}: fragment-only link resolves against <base> instead of this record"
                )
            parts = page.relative_to(root).parts
            if 'data-prerendered="true"' not in text:
                errors.append(f"{relative}: complete record content is not prerendered")
            if '<section class="record-hero' not in text or '<div class="shell record-layout' not in text:
                errors.append(f"{relative}: prerendered record structure is incomplete")
            for hidden_relation in (
                "data-progressive-panel hidden",
                "data-group-body hidden",
                "data-row-detail hidden",
            ):
                if hidden_relation in text:
                    errors.append(
                        f"{relative}: prerendered relations are hidden without JavaScript"
                    )
            if len(parts) >= 4 and parts[0] == "records":
                record_type, record_id = parts[1], parts[2]
                payload_path = root / "data/site/records" / record_type / f"{record_id}.json"
                if not payload_path.is_file():
                    errors.append(f"{relative}: record payload is missing")
                else:
                    payload = read_json(payload_path)
                    table_name = {
                        "work": "works",
                        "event": "timelineEvents",
                        "place": "places",
                        "media": "media",
                        "person": "people",
                        "organization": "organizations",
                        "source": "sources",
                    }.get(record_type)
                    record = next(
                        (
                            item
                            for item in payload.get("tables", {}).get(table_name, [])
                            if item.get("id") == record_id
                        ),
                        None,
                    )
                    if not record:
                        errors.append(f"{relative}: primary record is missing from its payload")
                    else:
                        if record_type == "media":
                            match = re.search(
                                r'<script type="application/ld\+json">(.*?)</script>',
                                text,
                                flags=re.DOTALL,
                            )
                            if not match:
                                errors.append(f"{relative}: schema.org JSON-LD is missing")
                            else:
                                try:
                                    structured = json.loads(match.group(1))
                                except json.JSONDecodeError:
                                    errors.append(
                                        f"{relative}: schema.org JSON-LD is invalid JSON"
                                    )
                                else:
                                    media_type = record.get("mediaType")
                                    expected_schema_type = MEDIA_SCHEMA_TYPES.get(media_type)
                                    if expected_schema_type is None:
                                        errors.append(
                                            f"{relative}: unsupported mediaType {media_type!r}"
                                        )
                                    elif structured.get("@type") != expected_schema_type:
                                        errors.append(
                                            f"{relative}: schema.org type must be "
                                            f"{expected_schema_type}, found "
                                            f"{structured.get('@type')!r}"
                                        )
                        for field, heading in PRERENDERED_RELATION_SECTIONS.get(record_type, {}).items():
                            if record.get(field) and f"<h2>{heading}" not in text:
                                errors.append(
                                    f"{relative}: prerendered relation section {heading!r} is missing"
                                )
                        for field, linked_type in PRERENDERED_RELATION_LINKS.get(record_type, {}).items():
                            for linked_id in record.get(field) or []:
                                href = f'href="records/{linked_type}/{linked_id}/"'
                                if href not in text:
                                    errors.append(
                                        f"{relative}: prerendered relation {field} -> {linked_id} is missing"
                                    )
                        if record_type == "work":
                            contributions = {
                                item.get("id"): item
                                for item in payload.get("tables", {}).get("contributions", [])
                            }
                            for contribution_id in record.get("contributionIds") or []:
                                contribution = contributions.get(contribution_id) or {}
                                for linked_type, field in (
                                    ("person", "personIds"),
                                    ("organization", "organizationIds"),
                                ):
                                    for linked_id in contribution.get(field) or []:
                                        if f'href="records/{linked_type}/{linked_id}/"' not in text:
                                            errors.append(
                                                f"{relative}: contribution {contribution_id} omits {linked_id}"
                                            )
                            relations = {
                                item.get("id"): item
                                for item in payload.get("tables", {}).get("workRelations", [])
                            }
                            for relation_id in record.get("relationIds") or []:
                                relation = relations.get(relation_id) or {}
                                linked_ids = {
                                    *(relation.get("sourceWorkIds") or []),
                                    *(relation.get("targetWorkIds") or []),
                                } - {record_id}
                                if linked_ids and not any(
                                    f'href="records/work/{linked_id}/"' in text
                                    for linked_id in linked_ids
                                ):
                                    errors.append(
                                        f"{relative}: work relation {relation_id} has no linked work"
                                    )
                        if record_type == "person":
                            contributions = {
                                item.get("id"): item
                                for item in payload.get("tables", {}).get("contributions", [])
                            }
                            for contribution_id in record.get("contributionIds") or []:
                                contribution = contributions.get(contribution_id) or {}
                                for source_id in contribution.get("sourceIds") or []:
                                    if f'href="records/source/{source_id}/"' not in text:
                                        errors.append(
                                            f"{relative}: contribution {contribution_id} omits source {source_id}"
                                        )
            if len(parts) >= 4 and parts[0] == "records" and parts[1] == "person":
                match = re.search(
                    r'<script type="application/ld\+json">(.*?)</script>',
                    text,
                    flags=re.DOTALL,
                )
                if not match:
                    errors.append(f"{relative}: schema.org JSON-LD is missing")
                    continue
                try:
                    structured = json.loads(match.group(1))
                except json.JSONDecodeError:
                    errors.append(f"{relative}: schema.org JSON-LD is invalid JSON")
                    continue
                same_as = structured.get("sameAs")
                if same_as is None:
                    continue
                urls = same_as if isinstance(same_as, list) else [same_as]
                if not urls:
                    errors.append(f"{relative}: schema.org sameAs is empty")
                for url in urls:
                    parsed = urlsplit(url) if isinstance(url, str) else None
                    if (
                        not parsed
                        or parsed.scheme not in {"http", "https"}
                        or not parsed.netloc
                        or re.search(r"\s", url)
                    ):
                        errors.append(
                            f"{relative}: schema.org sameAs contains a non-URL value"
                        )

    netlify_path = root / "netlify.toml"
    if netlify_path.is_file() and "frame-ancestors 'self'" not in netlify_path.read_text(encoding="utf-8"):
        errors.append("Netlify CSP lacks frame-ancestors protection")

    core_path = root / "assets/site/core.js"
    if core_path.is_file() and '<a class="skip-link"' in core_path.read_text(
        encoding="utf-8"
    ):
        errors.append("Shared JavaScript shell must not inject a duplicate skip link")

    for filename in SITEMAP_PAGES:
        expected = "https://iwmarlin.github.io/kaper/" if filename == "index.html" else f"https://iwmarlin.github.io/kaper/{filename}"
        if expected not in sitemap:
            errors.append(f"Sitemap omits {filename}")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "pagesChecked": len(parsed_pages),
        "publicMediaChecked": len(read_json(media_path).get("records", [])) if media_path.is_file() else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    result = validate(args.root.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
