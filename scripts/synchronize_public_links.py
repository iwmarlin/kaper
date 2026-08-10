#!/usr/bin/env python3
"""Synchronize reciprocal link fields in the current public JSON graph.

This maintenance command operates only on ``data/public/v1`` and never reads
or writes Airtable. It is intended for the repository's post-snapshot workflow,
where audited records and links may be added directly to the canonical public
JSON. Run ``scripts/reconcile_manifest.py`` afterwards when changes are applied.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


RECIPROCAL_LINKS = (
    ("People", "sourceIds", "Sources", "personIds"),
    ("People", "timelineEventIds", "Timeline Events", "personIds"),
    ("People", "placeIds", "Places", "personIds"),
    ("People", "nameVariantIds", "Person Name Variants", "personIds"),
    ("Organizations", "sourceIds", "Sources", "organizationIds"),
    ("Organizations", "placeIds", "Places", "organizationIds"),
    ("Organizations", "timelineEventIds", "Timeline Events", "organizationIds"),
    ("Sources", "workIds", "Works", "sourceIds"),
    ("Sources", "mediaIds", "Media", "sourceIds"),
    ("Sources", "timelineEventIds", "Timeline Events", "sourceIds"),
    ("Sources", "otherWorkIds", "Other Works", "sourceIds"),
    ("Sources", "placeIds", "Places", "sourceIds"),
    ("Sources", "filmIds", "Films", "sourceIds"),
    ("Sources", "songIds", "Songs", "sourceIds"),
    ("Sources", "titleVariantIds", "Title Variants", "sourceIds"),
    ("Sources", "nameVariantIds", "Person Name Variants", "sourceIds"),
    ("Media", "workIds", "Works", "mediaIds"),
    ("Media", "timelineEventIds", "Timeline Events", "mediaIds"),
    ("Media", "heroTimelineEventIds", "Timeline Events", "heroMediaIds"),
    ("Media", "placeIds", "Places", "mediaIds"),
    ("Works", "timelineEventIds", "Timeline Events", "workIds"),
    ("Works", "titleVariantIds", "Title Variants", "workIds"),
    ("Works", "nameVariantIds", "Person Name Variants", "workIds"),
    ("Works", "filmIds", "Films", "workIds"),
    ("Works", "songIds", "Songs", "workIds"),
    ("Works", "otherWorkIds", "Other Works", "workIds"),
    ("Works", "contributionIds", "Contributions", "workIds"),
    ("People", "contributionIds", "Contributions", "personIds"),
    ("Organizations", "contributionIds", "Contributions", "organizationIds"),
    ("Sources", "contributionIds", "Contributions", "sourceIds"),
    ("Sources", "workRelationIds", "Work Relations", "sourceIds"),
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def append_link(record: dict, field: str, record_id: str) -> bool:
    values = set(record.get(field, []))
    if record_id in values:
        return False
    values.add(record_id)
    record[field] = sorted(values)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    config = read_json(args.root / "scripts/public_export_config.json")
    data_root = args.root / "data/public/v1"
    payloads = {
        table_name: read_json(data_root / table_config["file"])
        for table_name, table_config in config["tables"].items()
    }
    indexes = {
        table_name: {record["id"]: record for record in payload["records"]}
        for table_name, payload in payloads.items()
    }
    changed_tables: set[str] = set()
    additions: list[str] = []

    def synchronize(
        left_table: str,
        left_field: str,
        right_table: str,
        right_field: str,
    ) -> None:
        for left_id, left_record in indexes[left_table].items():
            for right_id in left_record.get(left_field, []):
                right_record = indexes[right_table].get(right_id)
                if right_record and append_link(right_record, right_field, left_id):
                    changed_tables.add(right_table)
                    additions.append(
                        f"{right_table} {right_id}.{right_field} += {left_id}"
                    )

    for left_table, left_field, right_table, right_field in RECIPROCAL_LINKS:
        synchronize(left_table, left_field, right_table, right_field)
        synchronize(right_table, right_field, left_table, left_field)

    if args.check:
        if additions:
            print(f"DRIFT: {len(additions)} missing reciprocal links")
            for item in additions:
                print(f"  {item}")
            return 1
        print("clean: all configured reciprocal links are symmetric")
        return 0

    for table_name in sorted(changed_tables):
        filename = config["tables"][table_name]["file"]
        write_json(data_root / filename, payloads[table_name])
    print(
        f"synchronized: {len(additions)} reciprocal links across "
        f"{len(changed_tables)} tables"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
