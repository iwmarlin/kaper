#!/usr/bin/env python3
"""Validate an already generated public JSON export without Airtable access."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}

MEDIA_PUBLIC_WORKFLOW_PATTERN = re.compile(
    r"(?:"
    r"assets/|"
    r"\blocal asset\b|"
    r"\bsource route\b|"
    r"\bcurrent local path\b|"
    r"\bsource SRC\d+\b|"
    r"\brecorded in SRC\d+\b|"
    r"\blinked through SRC\d+\b|"
    r"\blinked works?\s*:|"
    r"\brelated works?\s*:|"
    r"\brights note records\b|"
    r"\bpublication status\b|"
    r"\bverification remains open\b|"
    r"\bcurrent asset field\b|"
    r"\bbibliographic source not yet linked\b|"
    r"\bsource:\s*|"
    r"\bidentifiers?:\s*|"
    r"\bexact visual provenance\b|"
    r"\b(?:reviewed|checked|updated|revised|confirmed)\s+20\d{2}(?:-\d{2}-\d{2})?\b|"
    r"\b20\d{2}-\d{2}-\d{2}\b|"
    r"\bsupplied by user\b|"
    r"\brights upgraded\b|"
    r"\bnot legal advice\b|"
    r"\bcurrent public repository derivative\b|"
    r"\bwebsite must\b|"
    r"\bdo not offer\b|"
    r"\bdo not provide\b|"
    r"\bdo not rehost\b|"
    r"\bno rehosting\b|"
    r"\bdo not reuse\b|"
    r"\bdo not imply\b|"
    r"\bindependent verification before publication\b|"
    r"\bnot a licence or legal determination\b"
    r")",
    flags=re.IGNORECASE,
)

MEDIA_PUBLIC_IDENTIFIER_PATTERN = re.compile(
    r"(?<![A-Za-z0-9-])(?:SRC\d{4}|W-[A-Z]\d{3}|TE\d{4}|PL\d{3}|M\d{3}|"
    r"F\d{3}|S\d{3}|O\d{3}|P\d{3}|ORG\d{3})(?![A-Za-z0-9-])"
)


class ExportValidator:
    def __init__(
        self,
        data_root: Path,
        config_path: Path,
        overrides_path: Path | None,
        assets_root: Path | None,
    ):
        self.data_root = data_root.resolve()
        self.config_path = config_path.resolve()
        self.overrides_path = overrides_path.resolve() if overrides_path else None
        self.assets_root = assets_root.resolve() if assets_root else None
        self.config = read_json(self.config_path)
        self.manifest = read_json(self.data_root / "manifest.json")
        self.report = read_json(self.data_root / "build-report.json")
        self.payloads: dict[str, dict[str, Any]] = {}
        self.errors: list[str] = []
        self.warnings: list[dict[str, Any]] = []

    def _load_tables(self) -> None:
        expected = {"manifest.json", "build-report.json"}
        for table_name, table_config in self.config["tables"].items():
            filename = table_config["file"]
            expected.add(filename)
            path = self.data_root / filename
            if not path.is_file():
                self.errors.append(f"Missing public table file: {filename}")
                continue
            self.payloads[table_name] = read_json(path)
        actual = {path.name for path in self.data_root.glob("*.json")}
        for filename in sorted(actual - expected):
            self.errors.append(f"Unexpected JSON file in public export: {filename}")

    def _validate_manifest(self) -> None:
        if self.manifest.get("schemaVersion") != self.config["schemaVersion"]:
            self.errors.append("Manifest schemaVersion does not match the allowlist")
        public_inputs = self.manifest.get("publicInputs", {})
        allowlist = public_inputs.get("allowlist", {})
        if allowlist.get("sha256") != sha256(self.config_path):
            self.errors.append("Manifest allowlist checksum does not match current config")
        override_entry = public_inputs.get("overrides")
        if self.overrides_path is not None:
            if not self.overrides_path.is_file():
                self.errors.append("Configured public override file is missing")
            elif not override_entry or override_entry.get("sha256") != sha256(
                self.overrides_path
            ):
                self.errors.append(
                    "Manifest override checksum does not match current overrides"
                )
        generator_path = Path(__file__).with_name("export_public_data.py").resolve()
        generator_entry = self.manifest.get("generator", {})
        if not generator_path.is_file() or generator_entry.get("sha256") != sha256(
            generator_path
        ):
            self.errors.append("Manifest generator checksum does not match exporter")
        file_entries = self.manifest.get("files", [])
        listed_files = {item["file"]: item for item in file_entries}
        if len(listed_files) != len(file_entries):
            self.errors.append("Manifest contains duplicate file entries")
        for filename, entry in listed_files.items():
            path = self.data_root / filename
            if not path.is_file():
                self.errors.append(f"Manifest lists missing file: {filename}")
                continue
            if entry.get("bytes") != path.stat().st_size:
                self.errors.append(f"Manifest byte count mismatch: {filename}")
            if entry.get("sha256") != sha256(path):
                self.errors.append(f"Manifest checksum mismatch: {filename}")
        expected_listed = {
            table_config["file"] for table_config in self.config["tables"].values()
        } | {"build-report.json"}
        missing_entries = expected_listed - set(listed_files)
        if missing_entries:
            self.errors.append(
                f"Manifest omits files: {sorted(missing_entries)}"
            )
        unexpected_entries = set(listed_files) - expected_listed
        if unexpected_entries:
            self.errors.append(
                f"Manifest contains unexpected files: {sorted(unexpected_entries)}"
            )
        if not self.report.get("ok") or self.report.get("errors"):
            self.errors.append("Embedded build report is not clean")

    def _validate_schema_and_links(self) -> None:
        ids_by_table: dict[str, set[str]] = {}
        banned_fragments = [
            item.casefold()
            for item in self.config.get("bannedPublicKeyFragments", [])
        ]
        for table_name, payload in self.payloads.items():
            table_config = self.config["tables"][table_name]
            records = payload.get("records")
            if not isinstance(records, list):
                self.errors.append(f"{table_name}: records is not an array")
                continue
            if payload.get("schemaVersion") != self.config["schemaVersion"]:
                self.errors.append(f"{table_name}: schemaVersion mismatch")
            if payload.get("scope") != self.config["scope"]:
                self.errors.append(f"{table_name}: scope mismatch")
            if payload.get("count") != len(records):
                self.errors.append(f"{table_name}: count does not match records")
            allowed = set(table_config["fields"]) | set(table_config["links"])
            allowed |= set(table_config.get("derivedFields", []))
            ids = [record.get("id") for record in records]
            ids_by_table[table_name] = set(ids)
            if len(ids) != len(ids_by_table[table_name]):
                self.errors.append(f"{table_name}: duplicate IDs")
            slugs = [record["slug"] for record in records if record.get("slug")]
            duplicate_slugs = sorted(
                slug for slug, count in Counter(slugs).items() if count > 1
            )
            if duplicate_slugs:
                self.errors.append(
                    f"{table_name}: duplicate slugs {duplicate_slugs}"
                )
            for record in records:
                record_id = record.get("id", "<missing-id>")
                unexpected = set(record) - allowed
                if unexpected:
                    self.errors.append(
                        f"{table_name} {record_id}: non-allowlisted keys {sorted(unexpected)}"
                    )
                for key in record:
                    if any(fragment in key.casefold() for fragment in banned_fragments):
                        self.errors.append(
                            f"{table_name} {record_id}: banned public key {key!r}"
                        )
                for key in table_config["required"]:
                    if is_empty(record.get(key)):
                        self.errors.append(
                            f"{table_name} {record_id}: required field {key!r} is empty"
                        )

        for table_name, payload in self.payloads.items():
            table_config = self.config["tables"][table_name]
            for record in payload.get("records", []):
                for key, link_spec in table_config["links"].items():
                    for target in record.get(key, []):
                        if target not in ids_by_table.get(link_spec["target"], set()):
                            self.errors.append(
                                f"{table_name} {record['id']}: dangling {key} target {target}"
                            )

        expected_counts = {
            table_name: len(payload.get("records", []))
            for table_name, payload in self.payloads.items()
        }
        if self.manifest.get("counts") != expected_counts:
            self.errors.append("Manifest table counts do not match exported records")
        if self.report.get("counts") != expected_counts:
            self.errors.append("Build report table counts do not match exported records")

    def _validate_content(self) -> None:
        forbidden_phrases = [
            item.casefold()
            for item in self.config.get("forbiddenPublicContentPhrases", [])
        ]
        forbidden_ids = set(self.config.get("forbiddenPublicRecordIds", []))
        identifier_pattern = (
            re.compile(
                r"(?<![A-Za-z0-9-])(?:"
                + "|".join(
                    re.escape(item)
                    for item in sorted(forbidden_ids, key=lambda value: (-len(value), value))
                )
                + r")(?![A-Za-z0-9-])"
            )
            if forbidden_ids
            else None
        )

        def walk(value: Any, context: str) -> None:
            if isinstance(value, str):
                folded = value.casefold()
                if "airtableusercontent.com" in folded:
                    self.errors.append(
                        f"{context}: contains an expiring Airtable attachment URL"
                    )
                for phrase in forbidden_phrases:
                    if phrase in folded:
                        self.errors.append(
                            f"{context}: contains forbidden workflow phrase {phrase!r}"
                        )
                if identifier_pattern:
                    for match in identifier_pattern.finditer(value):
                        self.errors.append(
                            f"{context}: mentions forbidden non-public record {match.group(0)}"
                        )
            elif isinstance(value, dict):
                for key, item in value.items():
                    walk(item, f"{context}.{key}")
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    walk(item, f"{context}[{index}]")

        for table_name, payload in self.payloads.items():
            walk(payload.get("records", []), table_name)

    def _validate_scope(self) -> None:
        end_year = self.config["scope"]["endYear"]
        for work in self.payloads.get("Works", {}).get("records", []):
            if work.get("year") and int(work["year"]) > end_year:
                self.errors.append(
                    f"Works {work['id']}: year {work['year']} exceeds {end_year}"
                )
        for event in self.payloads.get("Timeline Events", {}).get("records", []):
            for key in ("dateStart", "dateEnd"):
                if event.get(key) and int(str(event[key])[:4]) > end_year:
                    self.errors.append(
                        f"Timeline Events {event['id']}: {key} exceeds {end_year}"
                    )

    @staticmethod
    def _detect_media_type(path: Path) -> str | None:
        head = path.read_bytes()[:12]
        if head.startswith(b"\xff\xd8\xff"):
            return "jpeg"
        if head.startswith(b"\x89PNG\r\n\x1a\n"):
            return "png"
        if head[:3] == b"ID3" or (
            len(head) >= 2 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0
        ):
            return "mp3"
        return None

    def _validate_media(self) -> None:
        exceptions = set(
            self.config.get("mediaExceptions", {}).get(
                "sourceOptionalForExternalContextCards", []
            )
        )
        seen_assets: set[str] = set()
        for media in self.payloads.get("Media", {}).get("records", []):
            media_id = media["id"]
            for key in ("description", "publicCaption", "rightsNote", "publicCreditLine"):
                value = str(media.get(key, ""))
                if value and MEDIA_PUBLIC_WORKFLOW_PATTERN.search(value):
                    self.errors.append(
                        f"Media {media_id}: public field {key} contains editorial workflow text"
                    )
                if value and MEDIA_PUBLIC_IDENTIFIER_PATTERN.search(value):
                    self.errors.append(
                        f"Media {media_id}: public field {key} contains a technical record identifier"
                    )
            if media.get("rightsStatus") == "ok":
                rights_text = " ".join(
                    str(media.get(key, ""))
                    for key in ("rightsNote", "publicCreditLine")
                )
                if re.search(
                    r"not cleared|personal or research use only|"
                    r"publication.*(?:permission|rights assessment)|"
                    r"remain under copyright|confirm before US-based reuse",
                    rights_text,
                    flags=re.IGNORECASE,
                ):
                    self.errors.append(
                        f"Media {media_id}: rightsStatus ok conflicts with restrictive public rights text"
                    )
            external_url = media.get("externalUrl", "")
            if external_url and re.search(r"[\r\n]", external_url):
                self.errors.append(
                    f"Media {media_id}: externalUrl contains more than one URL"
                )
            if not media.get("sourceIds"):
                self.errors.append(f"Media {media_id}: public medium has no sourceIds")
            if media.get("galleryStatus") == "external_link_only":
                if not media.get("externalUrl"):
                    self.errors.append(f"Media {media_id}: external card has no URL")
                if media.get("embedUrl"):
                    self.errors.append(
                        f"Media {media_id}: external card contains an embed URL"
                    )
            if media.get("storageType") == "local" and not media.get("assetPath"):
                self.errors.append(f"Media {media_id}: local record has no asset path")
            if media.get("rightsStatus") == "permission_needed_or_fair_use_claimed":
                required = ["rightsNote", "publicCreditLine"]
                if media_id not in exceptions:
                    required.append("sourceIds")
                for key in required:
                    if is_empty(media.get(key)):
                        self.errors.append(
                            f"Media {media_id}: fair-use record lacks {key}"
                        )
                if media.get("storageType") == "local":
                    rationale = " ".join(
                        str(media.get(key, ""))
                        for key in ("rightsNote", "publicCreditLine")
                    )
                    if not re.search(
                        r"reduced|resolution|\d+\s*[×x]\s*\d+",
                        rationale,
                        flags=re.IGNORECASE,
                    ):
                        self.errors.append(
                            f"Media {media_id}: limited resolution is not documented"
                        )
            if self.assets_root is None:
                continue
            paths = ([media["assetPath"]] if media.get("assetPath") else [])
            paths.extend(media.get("assetPaths", []))
            for relative in paths:
                if relative in seen_assets:
                    continue
                seen_assets.add(relative)
                path = self.assets_root / relative
                if not path.is_file():
                    self.errors.append(f"Missing public asset: {relative}")
                    continue
                if path.stat().st_size <= 20:
                    self.errors.append(f"Public asset is 0–20 bytes: {relative}")
                actual = self._detect_media_type(path)
                expected = {
                    ".jpg": "jpeg",
                    ".jpeg": "jpeg",
                    ".png": "png",
                    ".mp3": "mp3",
                }.get(path.suffix.casefold())
                if actual and expected and actual != expected:
                    self.warnings.append(
                        {
                            "code": "asset_extension_mismatch",
                            "path": relative,
                            "extensionImplies": expected,
                            "contentIs": actual,
                        }
                    )

    def run(self) -> dict[str, Any]:
        self._load_tables()
        self._validate_manifest()
        self._validate_schema_and_links()
        self._validate_content()
        self._validate_scope()
        self._validate_media()
        return {
            "ok": not self.errors,
            "errors": self.errors,
            "warnings": sorted(
                self.warnings,
                key=lambda item: (item.get("code", ""), item.get("path", "")),
            ),
            "counts": {
                table_name: len(payload.get("records", []))
                for table_name, payload in self.payloads.items()
            },
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("public_export_config.json"),
    )
    parser.add_argument("--assets-root", type=Path)
    parser.add_argument(
        "--overrides",
        type=Path,
        default=Path(__file__).with_name("public_export_overrides.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = ExportValidator(
        args.data,
        args.config,
        args.overrides,
        args.assets_root,
    ).run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
