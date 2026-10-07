#!/usr/bin/env python3
"""Report or repair one-sided edges in the canonical public JSON graph.

The inverse-link contract lives in ``validate_public_export.SYMMETRIC_LINKS``
so repair and validation cannot silently drift apart.  The default mode is
read-only; pass ``--write`` to update only tables that need reciprocal links.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from validate_public_export import SYMMETRIC_LINKS


TABLE_FILES = {
    "People": "people.json",
    "Organizations": "organizations.json",
    "Sources": "sources.json",
    "Media": "media.json",
    "Works": "works.json",
    "Films": "films.json",
    "Songs": "songs.json",
    "Other Works": "other-works.json",
    "Title Variants": "title-variants.json",
    "Work Relations": "work-relations.json",
    "Timeline Events": "timeline-events.json",
    "Places": "places.json",
    "Contributions": "contributions.json",
    "Person Name Variants": "person-name-variants.json",
}


def read_tables(data_root: Path) -> dict[str, dict[str, Any]]:
    return {
        table_name: json.loads((data_root / filename).read_text(encoding="utf-8"))
        for table_name, filename in TABLE_FILES.items()
    }


def add_link(record: dict[str, Any], field: str, value: str) -> bool:
    values = list(record.get(field) or [])
    if value in values:
        return False
    record[field] = sorted({*values, value})
    return True


def reconcile(
    tables: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, str]], set[str]]:
    indexes = {
        table_name: {record["id"]: record for record in payload["records"]}
        for table_name, payload in tables.items()
    }
    additions: list[dict[str, str]] = []
    changed_tables: set[str] = set()

    def copy_missing_inverse(
        source_table: str,
        source_field: str,
        target_table: str,
        target_field: str,
    ) -> None:
        for source_id, source in indexes[source_table].items():
            for target_id in list(source.get(source_field) or []):
                target = indexes[target_table].get(target_id)
                # The validator reports dangling targets; this tool never
                # invents a record to satisfy one.
                if target is None:
                    continue
                if add_link(target, target_field, source_id):
                    changed_tables.add(target_table)
                    additions.append(
                        {
                            "table": target_table,
                            "record": target_id,
                            "field": target_field,
                            "added": source_id,
                        }
                    )

    for left_table, left_field, right_table, right_field in SYMMETRIC_LINKS:
        copy_missing_inverse(left_table, left_field, right_table, right_field)
        copy_missing_inverse(right_table, right_field, left_table, left_field)

    return additions, changed_tables


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    payload["count"] = len(payload.get("records", []))
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    data_root = args.data.resolve()
    tables = read_tables(data_root)
    additions, changed_tables = reconcile(tables)
    if args.write:
        for table_name in sorted(changed_tables):
            atomic_write_json(data_root / TABLE_FILES[table_name], tables[table_name])

    print(
        json.dumps(
            {
                "ok": not additions,
                "mode": "write" if args.write else "check",
                "addedInverseLinks": len(additions) if args.write else 0,
                "pendingInverseLinks": 0 if args.write else len(additions),
                "changedTables": sorted(changed_tables),
                "changes": additions,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if args.write or not additions else 1


if __name__ == "__main__":
    raise SystemExit(main())
