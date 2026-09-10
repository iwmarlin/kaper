#!/usr/bin/env python3
"""Apply every canonical Source normalizer in the exporter order.

The individual normalizers remain useful for focused migrations, but running
only one of them can leave ``sources.json`` inconsistent with the exporter.
This command provides one deterministic, idempotent entry point and a check
mode suitable for the site rebuild and CI quality gate.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any

from authority_sources import normalize_authority_source
from filmographic_sources import (
    IMDB_HOSTS,
    TCM_HOSTS,
    normalize_filmographic_source,
    source_hostname,
)
from hofmeister_sources import normalize_hofmeister_source
from normalize_source_dates import migrated_source
from recording_sources import normalize_recording_source
from sheet_music_sources import normalize_sheet_music_source
from source_access_dates import normalize_access_citation
from source_slugs import canonical_source_slug
from visual_sources import normalize_visual_source


def normalized_source(source: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical projection of one Source record."""

    result = deepcopy(source)
    normalize_visual_source(result)
    normalize_hofmeister_source(result)
    normalize_sheet_music_source(result)
    if result.get("sourceType") == "authority_record":
        normalize_authority_source(result)
    if result.get("sourceType") == "recording_discographic_source":
        normalize_recording_source(result)
    if (
        result.get("sourceType") == "filmographic_database"
        or source_hostname(result) in IMDB_HOSTS
        or source_hostname(result) in TCM_HOSTS
        or result.get("id") in {"SRC0174", "SRC0602"}
    ):
        normalize_filmographic_source(result)
    if result.get("accessDate"):
        result["fullCitation"] = normalize_access_citation(
            result.get("fullCitation")
        )

    result = migrated_source(result)
    result["slug"] = canonical_source_slug(result)
    return result


def normalize_payload(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Return a normalized payload and the IDs of records that drifted."""

    records = payload.get("records", [])
    normalized = [normalized_source(source) for source in records]
    changed_ids = [
        str(before.get("id", "<missing id>"))
        for before, after in zip(records, normalized)
        if before != after
    ]
    result = dict(payload)
    result["records"] = normalized
    if "count" in result:
        result["count"] = len(normalized)
    return result, changed_ids


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("data/public/v1/sources.json"),
        help="canonical sources.json file",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write the normalized file; without this flag, report drift",
    )
    args = parser.parse_args()

    payload = json.loads(args.path.read_text(encoding="utf-8"))
    normalized, changed_ids = normalize_payload(payload)
    if not changed_ids:
        print("Source normalization: no drift")
        return 0

    print(
        f"Source normalization drift: {len(changed_ids)} record(s): "
        + ", ".join(changed_ids)
    )
    if args.write:
        write_json_atomic(args.path, normalized)
        print(f"Wrote {args.path}")
        return 0
    print("Run again with --write to apply the normalization.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
