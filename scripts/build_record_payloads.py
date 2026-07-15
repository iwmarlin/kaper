#!/usr/bin/env python3
"""Build compact, relation-aware JSON payloads for public record pages."""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
from pathlib import Path


TABLE_FILES = {
    "people": "people.json",
    "organizations": "organizations.json",
    "sources": "sources.json",
    "media": "media.json",
    "works": "works.json",
    "films": "films.json",
    "songs": "songs.json",
    "otherWorks": "other-works.json",
    "titleVariants": "title-variants.json",
    "workRelations": "work-relations.json",
    "timelineEvents": "timeline-events.json",
    "places": "places.json",
    "contributions": "contributions.json",
    "personNameVariants": "person-name-variants.json",
}

RECORD_TYPES = {
    "work": "works",
    "event": "timelineEvents",
    "place": "places",
    "media": "media",
    "person": "people",
    "organization": "organizations",
    "source": "sources",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def record_ids(record: dict, key: str) -> list[str]:
    value = record.get(key, [])
    return value if isinstance(value, list) else []


class RecordPayloadBuilder:
    def __init__(self, public_root: Path) -> None:
        self.public_root = public_root
        self.tables = {
            name: read_json(public_root / filename).get("records", [])
            for name, filename in TABLE_FILES.items()
        }
        self.indexes = {
            name: {record["id"]: record for record in records}
            for name, records in self.tables.items()
        }

    @staticmethod
    def empty_bundle() -> dict[str, dict[str, dict]]:
        return {name: {} for name in TABLE_FILES}

    def add(self, bundle: dict, table: str, ids: list[str]) -> list[dict]:
        records = []
        for record_id in ids:
            record = self.indexes[table].get(record_id)
            if record is not None:
                bundle[table][record_id] = record
                records.append(record)
        return records

    def add_media_with_sources(self, bundle: dict, media_ids: list[str]) -> list[dict]:
        media = self.add(bundle, "media", media_ids)
        for item in media:
            self.add(bundle, "sources", record_ids(item, "sourceIds"))
        return media

    def add_work_detail(self, bundle: dict, work: dict) -> None:
        self.add(bundle, "works", [work["id"]])
        self.add(bundle, "films", record_ids(work, "filmIds"))
        self.add(bundle, "songs", record_ids(work, "songIds"))
        self.add(bundle, "otherWorks", record_ids(work, "otherWorkIds"))
        contributions = self.add(bundle, "contributions", record_ids(work, "contributionIds"))
        for contribution in contributions:
            self.add(bundle, "people", record_ids(contribution, "personIds"))
            self.add(bundle, "organizations", record_ids(contribution, "organizationIds"))
        self.add(bundle, "titleVariants", record_ids(work, "titleVariantIds"))
        relations = self.add(bundle, "workRelations", record_ids(work, "relationIds"))
        for relation in relations:
            related_ids = [
                *record_ids(relation, "sourceWorkIds"),
                *record_ids(relation, "targetWorkIds"),
            ]
            self.add(bundle, "works", related_ids)
        self.add(bundle, "sources", record_ids(work, "sourceIds"))
        self.add_media_with_sources(bundle, record_ids(work, "mediaIds"))
        self.add(bundle, "timelineEvents", record_ids(work, "timelineEventIds"))

    def add_gallery_members(self, bundle: dict, media: dict) -> None:
        paths = set(record_ids(media, "assetPaths"))
        if media.get("assetPath"):
            paths.add(media["assetPath"])
        member_ids = set(record_ids(media, "galleryMemberIds"))
        if paths:
            for candidate in self.tables["media"]:
                candidate_paths = set(record_ids(candidate, "assetPaths"))
                if candidate.get("assetPath"):
                    candidate_paths.add(candidate["assetPath"])
                if candidate["id"] != media["id"] and paths.intersection(candidate_paths):
                    member_ids.add(candidate["id"])
        members = self.add(bundle, "media", sorted(member_ids))
        if media.get("mediaType") == "document_gallery":
            for member in members:
                self.add(bundle, "sources", record_ids(member, "sourceIds"))

    def build(self, record_type: str, record_id: str) -> dict:
        table = RECORD_TYPES[record_type]
        root = self.indexes[table].get(record_id)
        if root is None:
            raise KeyError(f"Unknown {record_type} record: {record_id}")
        bundle = self.empty_bundle()
        self.add(bundle, table, [record_id])

        if record_type == "work":
            self.add_work_detail(bundle, root)
        elif record_type == "event":
            self.add(bundle, "people", record_ids(root, "personIds"))
            self.add(bundle, "works", record_ids(root, "workIds"))
            self.add(bundle, "places", record_ids(root, "placeIds"))
            self.add(bundle, "organizations", record_ids(root, "organizationIds"))
            self.add(bundle, "sources", record_ids(root, "sourceIds"))
            self.add_media_with_sources(bundle, record_ids(root, "mediaIds"))
        elif record_type == "place":
            self.add(bundle, "timelineEvents", record_ids(root, "timelineEventIds"))
            self.add(bundle, "people", record_ids(root, "personIds"))
            self.add(bundle, "sources", record_ids(root, "sourceIds"))
            self.add_media_with_sources(bundle, record_ids(root, "mediaIds"))
        elif record_type == "media":
            self.add(bundle, "sources", record_ids(root, "sourceIds"))
            self.add(bundle, "works", record_ids(root, "workIds"))
            subtype_records = [
                *self.add(bundle, "songs", record_ids(root, "songIds")),
                *self.add(bundle, "otherWorks", record_ids(root, "otherWorkIds")),
            ]
            for subtype in subtype_records:
                self.add(bundle, "works", record_ids(subtype, "workIds"))
            self.add(bundle, "timelineEvents", record_ids(root, "timelineEventIds"))
            self.add(bundle, "places", record_ids(root, "placeIds"))
            self.add(bundle, "organizations", record_ids(root, "organizationIds"))
            self.add_gallery_members(bundle, root)
        elif record_type == "person":
            self.add(bundle, "works", record_ids(root, "workIds"))
            self.add(bundle, "timelineEvents", record_ids(root, "timelineEventIds"))
            self.add(bundle, "sources", record_ids(root, "sourceIds"))
            self.add(bundle, "personNameVariants", record_ids(root, "nameVariantIds"))
        elif record_type == "organization":
            self.add(bundle, "works", record_ids(root, "workIds"))
            self.add(bundle, "timelineEvents", record_ids(root, "timelineEventIds"))
            self.add(bundle, "sources", record_ids(root, "sourceIds"))
        elif record_type == "source":
            self.add(bundle, "works", record_ids(root, "workIds"))
            self.add(bundle, "media", record_ids(root, "mediaIds"))
            self.add(bundle, "timelineEvents", record_ids(root, "timelineEventIds"))
            self.add(bundle, "places", record_ids(root, "placeIds"))
            self.add(bundle, "people", record_ids(root, "personIds"))
            self.add(bundle, "organizations", record_ids(root, "organizationIds"))

        return {
            "schemaVersion": "1.0.0",
            "type": record_type,
            "id": record_id,
            "tables": {
                name: [records[key] for key in sorted(records)]
                for name, records in bundle.items()
            },
        }


def write_compact_json(path: Path, payload: dict) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    path.write_text(text, encoding="utf-8")
    return len(text.encode("utf-8"))


def build_all(root: Path) -> dict:
    public_root = root / "data/public/v1"
    output_root = root / "data/site/records"
    report_path = root / "data/site/record-report.json"
    builder = RecordPayloadBuilder(public_root)
    if output_root.exists():
        shutil.rmtree(output_root)
    sizes = []
    counts = {}
    largest = {"type": "", "id": "", "bytes": 0}
    examples = {}

    for record_type, table in RECORD_TYPES.items():
        records = builder.tables[table]
        counts[record_type] = len(records)
        for record in records:
            payload = builder.build(record_type, record["id"])
            size = write_compact_json(output_root / record_type / f"{record['id']}.json", payload)
            sizes.append(size)
            if size > largest["bytes"]:
                largest = {"type": record_type, "id": record["id"], "bytes": size}
            if record["id"] in {"P009", "W-F004", "M081", "TE0004"}:
                examples[record["id"]] = size

    baseline = sum((public_root / filename).stat().st_size for filename in TABLE_FILES.values())
    ordered = sorted(sizes)
    report = {
        "schemaVersion": "1.0.0",
        "recordCount": len(sizes),
        "countsByType": counts,
        "baselineAllTablesBytes": baseline,
        "totalPayloadBytes": sum(sizes),
        "medianPayloadBytes": round(statistics.median(ordered)),
        "p95PayloadBytes": ordered[min(len(ordered) - 1, round(len(ordered) * 0.95))],
        "largestPayload": largest,
        "examples": examples,
    }
    write_compact_json(report_path, report)
    return report


def validate(root: Path) -> list[str]:
    public_root = root / "data/public/v1"
    output_root = root / "data/site/records"
    report_path = root / "data/site/record-report.json"
    errors = []
    if not report_path.is_file():
        return ["Missing record payload report"]
    report = read_json(report_path)
    builder = RecordPayloadBuilder(public_root)
    expected_paths = set()
    payload_sizes = []
    for record_type, table in RECORD_TYPES.items():
        records = builder.tables[table]
        for record in records:
            path = output_root / record_type / f"{record['id']}.json"
            expected_paths.add(path)
            if not path.is_file():
                errors.append(f"Missing record payload: {record_type}/{record['id']}")
                continue
            payload_sizes.append(path.stat().st_size)
            payload = read_json(path)
            if payload.get("type") != record_type or payload.get("id") != record["id"]:
                errors.append(f"Invalid record payload identity: {record_type}/{record['id']}")
            if set(payload.get("tables", {})) != set(TABLE_FILES):
                errors.append(f"Incomplete record payload tables: {record_type}/{record['id']}")
            if payload != builder.build(record_type, record["id"]):
                errors.append(f"Stale record payload: {record_type}/{record['id']}")
    actual_paths = set(output_root.glob("*/*.json")) if output_root.is_dir() else set()
    for path in sorted(actual_paths - expected_paths):
        errors.append(f"Unexpected record payload: {path.relative_to(output_root)}")
    if report.get("recordCount") != len(expected_paths):
        errors.append("Record payload report count is stale")
    baseline = sum((public_root / filename).stat().st_size for filename in TABLE_FILES.values())
    if report.get("baselineAllTablesBytes") != baseline:
        errors.append("Record payload report baseline is stale")
    if report.get("totalPayloadBytes") != sum(payload_sizes):
        errors.append("Record payload report total is stale")
    if report.get("largestPayload", {}).get("bytes", 0) >= report.get("baselineAllTablesBytes", 0):
        errors.append("Largest record payload is not smaller than the all-table baseline")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if args.check:
        errors = validate(root)
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        return 0 if not errors else 1
    report = build_all(root)
    print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
