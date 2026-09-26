#!/usr/bin/env python3
"""Remove prose access dates from the canonical public Source citations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from source_access_dates import normalize_access_citation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sources",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data/public/v1/sources.json",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write the normalized document; without this flag, only report",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.sources.read_text(encoding="utf-8"))
    changed: list[str] = []
    for source in payload.get("records", []):
        if not source.get("accessDate"):
            continue
        citation = str(source.get("fullCitation") or "")
        normalized = normalize_access_citation(citation)
        if normalized != citation:
            source["fullCitation"] = normalized
            changed.append(str(source.get("id") or ""))

    print(f"{len(changed)} Source citations require normalization")
    if changed:
        print(" ".join(changed))
    if args.write and changed:
        args.sources.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

