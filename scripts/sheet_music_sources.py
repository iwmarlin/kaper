#!/usr/bin/env python3
"""Keep examined scores distinct from catalogue descriptions of scores."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


# These public URLs are catalogue landing pages, not page images or score PDFs.
# A record pointing only to one of them documents a bibliographic description;
# it must not imply that the notated object itself was examined.
SHEET_MUSIC_CATALOGUE_HOSTS = {
    "catalogue.bnf.fr",
    "catalogue.nla.gov.au",
    "data.bnf.fr",
    "kvk.bibliothek.kit.edu",
    "stabikat.de",
}


# Audited exceptions whose URLs do not by themselves reveal what was consulted.
# Keep this list deliberately small: these records were checked against the
# linked object or finding aid, rather than inferred from a host name.
AUDITED_SOURCE_TYPE_OVERRIDES = {
    # The linked NYPL PDF is a finding aid that identifies a physical holding;
    # it does not reproduce the score or its item-level credit line.
    "SRC0203": "archival_manuscript_holding",
    # The linked Sirius-Mappe page is a publisher's contents list for the
    # anthology, not the anthology's notation.
    "SRC0286": "sheet_music_catalogue",
    # These collection-level records currently rely on uploader-supplied
    # indexed contents. Individual issue scans may become sheet_music sources
    # only after the relevant notation has been examined.
    "SRC0854": "sheet_music_catalogue",
    "SRC0855": "sheet_music_catalogue",
}


def source_hostname(source: dict[str, Any]) -> str:
    url = str(source.get("primaryUrl") or source.get("url") or "").strip()
    return urlparse(url).netloc.casefold()


def is_catalogue_landing_page_for_sheet_music(source: dict[str, Any]) -> bool:
    return (
        source.get("sourceType") in {"sheet_music", "sheet_music_catalogue"}
        and source_hostname(source) in SHEET_MUSIC_CATALOGUE_HOSTS
    )


def normalize_sheet_music_source(source: dict[str, Any]) -> None:
    """Normalize a catalogue-only score description without rewriting its data."""

    audited_type = AUDITED_SOURCE_TYPE_OVERRIDES.get(str(source.get("id") or ""))
    if audited_type:
        source["sourceType"] = audited_type
    elif source.get("sourceType") == "sheet_music" and is_catalogue_landing_page_for_sheet_music(source):
        source["sourceType"] = "sheet_music_catalogue"


def normalize_file(path: Path) -> int:
    """Normalize catalogue-only score descriptions in canonical JSON atomically."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for source in payload.get("records", []):
        before = dict(source)
        normalize_sheet_music_source(source)
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
    print(f"normalized sheet-music catalogue landing pages: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
