#!/usr/bin/env python3
"""Validate the static research website and its public data references."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


PUBLIC_PAGES = [
    "index.html",
    "works.html",
    "life.html",
    "map.html",
    "media.html",
    "record.html",
    "404.html",
]


class ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[tuple[str, str]] = []
        self.iframes = 0
        self.lang: str | None = None
        self.has_viewport = False
        self.has_title = False
        self.canonicals: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html":
            self.lang = values.get("lang")
        if tag == "meta" and values.get("name") == "viewport":
            self.has_viewport = True
        if tag == "link" and values.get("rel") == "canonical" and values.get("href"):
            self.canonicals.append(values["href"])
        if tag == "iframe":
            self.iframes += 1
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
        if filename not in {"404.html", "record.html"} and len(parser.canonicals) != 1:
            errors.append(f"{filename}: expected exactly one canonical URL")
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
        "data/public/v1/manifest.json",
        "data/public/v1/build-report.json",
    ]
    for filename in required_files:
        if not (root / filename).is_file():
            errors.append(f"Missing deployment file: {filename}")

    for script in (root / "assets/site").glob("*.js"):
        text = script.read_text(encoding="utf-8")
        for imported in re.findall(r'from\s+["\'](\./[^"\']+)["\']', text):
            target = (script.parent / urlsplit(imported).path).resolve()
            if not target.is_file():
                errors.append(f"{script.relative_to(root)}: missing module {imported}")
        if "airtableusercontent.com" in text.lower():
            errors.append(f"{script.relative_to(root)}: private Airtable URL found")

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

    sitemap = (root / "sitemap.xml").read_text(encoding="utf-8") if (root / "sitemap.xml").is_file() else ""
    for filename in PUBLIC_PAGES[:5]:
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
