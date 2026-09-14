#!/usr/bin/env python3
"""Migrate canonical Source dates to the controlled public date model.

The migration is deterministic and idempotent.  It separates sortable dates,
ranges, roles and qualifiers, and extracts U.S. Copyright Office registration
and renewal numbers into structured identifiers.  Bibliographic citations are
left untouched.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from source_dates import normalized_source_date_fields, usco_identifiers


DATE_FIELDS = {"date", "dateEnd", "dateRole", "dateQualifier", "dateDisplay"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def merged_identifiers(source: dict[str, Any]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for identifier in (*(source.get("identifiers") or []), *usco_identifiers(source)):
        if not isinstance(identifier, dict):
            continue
        scheme = str(identifier.get("scheme", "")).strip().casefold()
        value = str(identifier.get("value", "")).strip()
        key = (scheme, value.casefold())
        if scheme and value and key not in seen:
            seen.add(key)
            result.append({"scheme": scheme, "value": value})
    return result


def migrated_source(source: dict[str, Any]) -> dict[str, Any]:
    dates = normalized_source_date_fields(source)
    identifiers = merged_identifiers(source)
    result: dict[str, Any] = {}
    date_inserted = False
    identifiers_inserted = False

    for key, value in source.items():
        if key in DATE_FIELDS:
            if not date_inserted:
                result.update(dates)
                date_inserted = True
            continue
        if key == "identifiers":
            if identifiers:
                result["identifiers"] = identifiers
            identifiers_inserted = True
            continue
        result[key] = value
        if not date_inserted and key in {"publication", "creator"}:
            # Prefer the old bibliographic position when a record had no date.
            # A later legacy date key will replace this placement only in old
            # records, where it normally occurs immediately afterwards.
            next_keys = list(source)
            current_index = next_keys.index(key)
            if not any(item in DATE_FIELDS for item in next_keys[current_index + 1 :]):
                result.update(dates)
                date_inserted = True

    if not date_inserted:
        result.update(dates)
    if identifiers and not identifiers_inserted:
        result["identifiers"] = identifiers
    return result


def migrate(payload: dict[str, Any]) -> tuple[dict[str, Any], Counter[str]]:
    records = payload.get("records", [])
    migrated = [migrated_source(source) for source in records]
    stats: Counter[str] = Counter()
    for old, new in zip(records, migrated):
        if old != new:
            stats["records_changed"] += 1
        stats[f"role:{new['dateRole']}"] += 1
        stats[f"qualifier:{new['dateQualifier']}"] += 1
        stats["structured_identifiers"] += len(new.get("identifiers") or [])
    result = dict(payload)
    result["records"] = migrated
    if "count" in result:
        result["count"] = len(migrated)
    return result, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/public/v1/sources.json"),
        help="canonical sources.json file",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write the migration; without this flag only report drift",
    )
    args = parser.parse_args()

    payload = read_json(args.data)
    migrated, stats = migrate(payload)
    changed = payload != migrated
    print(f"Source date drift: {stats['records_changed']} record(s)")
    for key in sorted(key for key in stats if key.startswith("role:")):
        print(f"  {key}: {stats[key]}")
    for key in sorted(key for key in stats if key.startswith("qualifier:")):
        print(f"  {key}: {stats[key]}")
    print(f"  structured identifiers: {stats['structured_identifiers']}")

    if args.write and changed:
        args.data.write_text(
            json.dumps(migrated, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {args.data}")
    elif changed:
        print("Run again with --write to apply the migration.")
    return 0 if args.write or not changed else 1


if __name__ == "__main__":
    raise SystemExit(main())
