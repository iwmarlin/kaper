#!/usr/bin/env python3
"""Canonical slugs for Source records.

Source pages are routed by their stable IDs, but the slug remains public data
and is used for searching and diagnostics.  Keeping the ID at the beginning
makes every slug unambiguous and matches the convention used by newly created
Source records.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Any, Mapping


MAX_SOURCE_SLUG_LENGTH = 80
SOURCE_ID_PATTERN = re.compile(r"SRC\d{4}", re.IGNORECASE)
LEADING_SOURCE_ID_PATTERN = re.compile(r"^src(\d+)-", re.IGNORECASE)
TRAILING_SOURCE_ID_PATTERN = re.compile(r"-src\d{3,5}$", re.IGNORECASE)


def _slugify(value: str) -> str:
    ascii_text = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .casefold()
    )
    return re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")


def canonical_source_slug(source: Mapping[str, Any]) -> str:
    """Return ``srcNNNN-description`` while preserving the existing description.

    Older exports either put the ID at the end or omitted it.  One truncated
    slug contains only ``src003`` at the end and one contains the zero-padded
    typo ``src00816`` at the beginning; both are handled without changing the
    descriptive portion.  The established 80-character ceiling is retained.
    """

    source_id = str(source.get("id") or "").strip()
    raw_slug = str(source.get("slug") or "").strip().casefold()
    if not SOURCE_ID_PATTERN.fullmatch(source_id):
        return raw_slug

    numeric_id = int(source_id[3:])
    prefix = f"{source_id.casefold()}-"
    descriptor = raw_slug

    if descriptor.startswith(prefix):
        descriptor = descriptor[len(prefix):]
    else:
        descriptor = TRAILING_SOURCE_ID_PATTERN.sub("", descriptor)
        leading = LEADING_SOURCE_ID_PATTERN.match(descriptor)
        if leading and int(leading.group(1)) == numeric_id:
            descriptor = descriptor[leading.end():]

    descriptor = _slugify(descriptor)
    if not descriptor:
        descriptor = _slugify(
            str(source.get("title") or source.get("shortCitation") or "source")
        )

    available = MAX_SOURCE_SLUG_LENGTH - len(prefix)
    return f"{prefix}{descriptor[:available].rstrip('-')}"


def normalize_file(path: Path) -> int:
    """Normalize a canonical Sources JSON file atomically."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for source in payload.get("records", []):
        canonical = canonical_source_slug(source)
        if source.get("slug") != canonical:
            source["slug"] = canonical
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
    print(f"normalized source slugs: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
