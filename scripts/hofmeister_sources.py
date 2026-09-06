#!/usr/bin/env python3
"""Normalize sources that cite Hofmeister's music-publication register.

``sheet_music`` is reserved for an identified score or reproduction that was
actually consulted.  A notice in Hofmeisters Musikalisch-literarischer
Monatsbericht is bibliographic evidence *about* such an edition and therefore
uses ``sheet_music_catalogue``, irrespective of how fully the notice describes
the music.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping


REGISTER_TITLE = "Hofmeisters Musikalisch-literarischer Monatsbericht"
TITLE_PREFIX = f"{REGISTER_TITLE}: "
REGISTER_CITATION_MARKERS = (
    REGISTER_TITLE,
    "Friedrich Hofmeister, Musikalisch-literarischer Monatsbericht",
)

HOFMEISTER_SCAN_REPOSITORIES = {
    "Internet Archive",
    "Internet Archive / Friedrich Hofmeister",
    "Österreichische Nationalbibliothek / ANNO",
}

MONTH_NUMBER = {
    "January": "01",
    "February": "02",
    "March": "03",
    "April": "04",
    "May": "05",
    "June": "06",
    "July": "07",
    "August": "08",
    "September": "09",
    "October": "10",
    "November": "11",
    "December": "12",
}
MONTH_PATTERN = "|".join(MONTH_NUMBER)

DATED_ISSUE = re.compile(
    rf"Hofmeisters Musikalisch-literarischer Monatsbericht"
    rf"(?:\s+\d+,\s*no\.\s*\d+)?\s*"
    rf"\((?P<month>{MONTH_PATTERN})\s+(?P<year>\d{{4}})\):\s*"
    rf"(?P<pages>\d+(?:[–-]\d+)?(?:,\s*\d+)*)",
)
COMMA_DATED_ISSUE = re.compile(
    rf"Hofmeisters Musikalisch-literarischer Monatsbericht,\s*"
    rf"(?P<month>{MONTH_PATTERN})\s+(?P<year>\d{{4}}),\s*"
    rf"p\.\s*(?P<pages>\d+(?:[–-]\d+)?(?:,\s*\d+)*)",
)
YEAR_ONLY_ISSUE = re.compile(
    r"Hofmeisters Musikalisch-literarischer Monatsbericht\s*"
    r"\((?P<year>\d{4})\):\s*"
    r"(?P<pages>\d+(?:[–-]\d+)?(?:,\s*\d+)*)",
)

TITLE_SUFFIX = re.compile(
    r"\s+—\s+(?:sheet music(?:\s+\(ANNO\))?|"
    r"Hofmeister\s*/\s*Internet Archive entry|Internet Archive scan)$",
    flags=re.IGNORECASE,
)


def is_hofmeister_catalogue_source(source: Mapping[str, Any]) -> bool:
    """Return true only when the consulted object is a scan of the register."""

    citation = str(source.get("fullCitation") or "")
    if not any(marker in citation for marker in REGISTER_CITATION_MARKERS):
        return False
    repository = str(source.get("repository") or "")
    url = str(source.get("primaryUrl") or source.get("url") or "")
    return (
        repository in HOFMEISTER_SCAN_REPOSITORIES
        and (
            "anno.onb.ac.at/cgi-content/anno-plus?aid=hof" in url
            or "archive.org/details/Musikalisch-literarischerMonatsbericht" in url
            or source.get("sourceType") == "sheet_music_catalogue"
        )
    )


def _entry_title(source: Mapping[str, Any]) -> str:
    title = str(source.get("title") or "").strip()
    if title.startswith(TITLE_PREFIX):
        title = title[len(TITLE_PREFIX) :].strip()
        if title.startswith("“") and "”" in title:
            close = title.rfind("”")
            title = title[1:close]
    title = TITLE_SUFFIX.sub("", title).strip()
    if title.endswith(" (film)"):
        title = title[:-7].rstrip()
    return title


def _issue(citation: str) -> tuple[str, str, str] | None:
    for pattern in (DATED_ISSUE, COMMA_DATED_ISSUE):
        if match := pattern.search(citation):
            return match["month"], match["year"], match["pages"].replace("-", "–")
    if match := YEAR_ONLY_ISSUE.search(citation):
        return "", match["year"], match["pages"].replace("-", "–")
    return None


def _page_label(pages: str) -> str:
    return "pp." if "," in pages or "–" in pages else "p."


def normalize_hofmeister_source(source: dict[str, Any]) -> None:
    """Normalize one verified register scan in place without altering its citation."""

    if not is_hofmeister_catalogue_source(source):
        return

    entry_title = _entry_title(source)
    if not entry_title:
        return

    source["sourceType"] = "sheet_music_catalogue"
    source["dateRole"] = "catalogue_volume"
    title = f"{TITLE_PREFIX}“{entry_title}”"
    if source.get("id") == "SRC0461":
        # The same notice is represented by the canonical ANNO record SRC0207;
        # this separate record documents its Internet Archive access copy.
        title += " — Internet Archive scan"
        source["publication"] = "Alrobi, Berlin"
    source["title"] = title

    issue = _issue(str(source.get("fullCitation") or ""))
    if issue:
        month, year, pages = issue
        date_label = f"{month} {year}" if month else year
        source["shortCitation"] = (
            f"Hofmeister, {date_label}, {_page_label(pages)} {pages} — “{entry_title}”"
        )
        if month:
            source["date"] = f"{year}-{MONTH_NUMBER[month]}"
        elif not source.get("date"):
            source["date"] = year
    elif source.get("id") == "SRC0461":
        source["shortCitation"] = (
            f"Hofmeister, 1931, scan leaf n33 — “{entry_title}”"
        )


def normalize_file(path: Path) -> int:
    """Normalize the canonical Sources JSON atomically."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for source in payload.get("records", []):
        before = dict(source)
        normalize_hofmeister_source(source)
        if source != before:
            changed += 1

    if changed:
        rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(rendered)
            temporary = Path(handle.name)
        temporary.replace(path)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Path to canonical sources.json")
    args = parser.parse_args()
    changed = normalize_file(args.path)
    print(f"normalized Hofmeister catalogue sources: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
