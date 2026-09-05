#!/usr/bin/env python3
"""Validate the canonical public JSON graph and its publication constraints."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse, urlunparse

from authority_sources import (
    AUTHORITY_ORGANIZATION_BY_HOST,
    AUTHORITY_REPOSITORY_BY_HOST,
    authority_hostname,
)
from filmographic_sources import (
    CANONICAL_REPOSITORY_BY_HOST,
    REPOSITORY_ORGANIZATION_BY_HOST,
    source_hostname,
)
from recording_organizations import expected_audio_organization_ids
from recording_sources import (
    RECORDING_ORGANIZATION_BY_HOST,
    recording_hostname,
)
from repository_organizations import expected_repository_organization_ids
from source_dates import SOURCE_IDENTIFIER_SCHEMES, source_date_errors
from source_access_dates import has_redundant_access_date
from visual_sources import (
    VISUAL_RIGHTS_NARRATIVE_PATTERN,
    WIKIMEDIA_ORGANIZATION_ID,
    is_normalized_visual_source,
    is_wikimedia_source,
)


def read_json(path: Path) -> dict[str, Any]:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{path}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_keys,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


# A URL that serves data to a program rather than a page to a person: a IIIF
# manifest, an API path, a format=json switch, a bare .json or .xml, or the raw
# OCR text of a scan.
MACHINE_ENDPOINT = re.compile(
    r"manifest\.json|/api/|/iiif/|[?&]format=json|\.json(?:$|[?#])|\.xml(?:$|[?#])"
    r"|_djvu\.txt|\.txt(?:$|[?#])",
    re.IGNORECASE,
)

# This archive's own record numbers, in text a reader sees.
INTERNAL_ID = re.compile(r"\b(?:S0?\d{2,4}|W-S\d+|W-F\d+|SRC\d+|M\d{3}|ORG\d{3}|P\d{3}|TE\d{4})\b")

# A value that is only an identifier: "D 4431", "E.G. 2392", "17919".
BARE_IDENTIFIER = re.compile(r"^(?:[A-Z]{1,3}\.?[\-\s]?){0,3}\d[\d.\-\s]*[a-z]?$")

# An Internet Archive *node* host. The node is assigned per request and is not a
# durable address, so a link built on one rots; the item page is the stable form
# and 85 records already used it while 33 pointed at a node.
UNSTABLE_HOST = re.compile(r"^https?://ia\d+\.us\.archive\.org/", re.IGNORECASE)

# The archive's own copy of a file, standing where the external origin belongs.
SELF_REFERENCE = re.compile(
    r"^https?://(?:github\.com/iwmarlin/kaper|iwmarlin\.github\.io/kaper)", re.IGNORECASE
)

# Every field whose value is put in front of a reader as a link to follow.
READER_FACING_LINKS = (
    ("Sources", "primaryUrl"),
    ("Sources", "accessUrl"),
    ("Media", "externalUrl"),
)


# A year range inside parentheses, written with a hyphen. A register states an
# unknown century as "18.." and an open end as "...." or "?", so a range can be
# (1908-2011), (18..-1961) or (1908-....) and all three take an en dash.
YEAR_RANGE_WITH_HYPHEN = re.compile(
    r"\((?:\d{4}|\d{2}\.\.)\s*-\s*(?:\d{4}|\d{2}\.\.|\.\.\.\.|\?)\)"
)

# Hofmeister's register prints personal names in catalogue order (surname,
# forename).  That transcription belongs in the citation; ``creator`` is a
# reader-facing display and search field and follows the archive's natural-name
# convention.  Scope the rule to this one source family so that commas used for
# roles, institutional subdivisions or ensemble credits are not misread as
# inverted personal names.
HOFMEISTER_INVERTED_CREATOR_PATTERN = re.compile(
    r"(?:^|;\s*)[^,;]+,\s*(?:[A-ZÀ-ÖØ-Þ]\.?|[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ])"
    r"[^,;]*(?=;|$)"
)
HOFMEISTER_REPOSITORY = "Österreichische Nationalbibliothek / ANNO"


PUBLIC_NARRATIVE_FIELDS = {
    "People": ("publicNote", "biography"),
    "Organizations": ("publicNote", "description"),
    "Sources": ("shortCitation", "fullCitation", "researchNote"),
    "Media": ("description", "publicCaption", "publicCreditLine", "rightsNote"),
    "Works": ("publicNote",),
    "Films": ("publicNote", "attributionNote"),
    "Songs": ("publicNote",),
    "Other Works": ("publicNote",),
    "Work Relations": ("publicNote",),
    "Timeline Events": ("shortDescription", "longDescription", "publicNote"),
    "Places": ("description", "publicNote", "publicSummary"),
    "Contributions": ("scopeNote", "publicNote"),
    "Person Name Variants": ("publicNote",),
}

PUBLIC_EDITORIAL_NARRATOR_PATTERN = re.compile(
    r"(?:"
    r"\bfor (?:this|these) works?\b|"
    r"\bthis catalogue\b|"
    r"\bthis archive\b|"
    r"\bthis database\b|"
    r"\bthe archive (?:keeps|holds|records|reproduces)\b|"
    r"\bfor indexing\b|"
    r"\bcanonical person P\d+\b|"
    r"\bthe supplied archival object metadata\b"
    r")",
    flags=re.IGNORECASE,
)

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
    r"\bclick (?:above|below)\b|"
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

PERSON_AUTHORIZED_NAME_DATES_PATTERN = re.compile(
    r"(?:,\s*|\s*\()\d{4}\s*[–—-]\s*\d{4}\)?\s*$"
)

MEDIA_PUBLIC_IDENTIFIER_PATTERN = re.compile(
    r"(?<![A-Za-z0-9-])(?:SRC\d{4}|W-[A-Z]\d{3}|TE\d{4}|PL\d{3}|M\d{3}|"
    r"F\d{3}|S\d{3}|O\d{3}|P\d{3}|ORG\d{3})(?![A-Za-z0-9-])"
)

SOURCE_PUBLIC_IDENTIFIER_PATTERN = re.compile(
    r"(?<![A-Za-z0-9-])(?:SRC\d{4}|W-[A-Z]\d{3}|TE\d{4}|PL\d{3}|M\d{3}|"
    r"F\d{3}|S\d{3}|O\d{3}|P\d{3}|ORG\d{3}|TV\d{4}|PNV\d{4}|CON-[A-Z0-9-]+)"
    r"(?![A-Za-z0-9-])"
)

SOURCE_RESEARCH_NOTE_TYPES = {
    "authority_note",
    "date_assessment",
    "discographic_note",
    "evidence_note",
    "identity_assessment",
    "object_context",
    "verification_note",
}

MEDIA_TYPES = {"audio", "video", "image", "sheet music", "document_gallery"}

SOURCE_PUBLIC_WORKFLOW_PATTERN = re.compile(
    r"(?:"
    r"assets/|"
    r"\blocal asset\b|"
    r"\bsource record\b|"
    r"\bproject (?:owner|media asset)\b|"
    r"\bretained in this database\b|"
    r"\b(?:data|metadata|RIS export) supplied (?:by (?:the )?(?:user|project)|from)\b|"
    r"\bsource (?:used )?for (?:media|work|song)\b|"
    r"\bused in Media\b|"
    r"\breferenced as a (?:listening|viewing/listening) source\b|"
    r"\blistening/viewing source for\b|"
    r"\bdistinct clipping from\b|"
    r"\bused here\b|"
    r"\b(?:entry|record|source|item) (?:was )?not (?:independently )?"
    r"(?:checked|verified) against\b"
    r")",
    flags=re.IGNORECASE,
)

# Source citations identify and locate an object.  The legal assessment belongs
# to the linked Media record, where it can be presented once with its credit
# line and use rationale.  Keep this deliberately narrower than a generic
# search for words such as "copyright": a historical copyright notice printed
# on sheet music can be bibliographic evidence rather than editorial analysis.
SOURCE_IMAGE_RIGHTS_ANALYSIS_PATTERN = re.compile(
    r"(?:"
    r"\bright[s]?\s*:\s*(?:expired|unknown|not cleared)|"
    r"\b(?:rights|copyright) status (?:shown|recorded|unknown|unverified)|"
    r"\bright[s]? have expired\b|"
    r"\bcopyright (?:was not renewed|in the collection was deeded|not renewed)\b|"
    r"\bpublic domain (?:in|according to|worldwide|under)\b|"
    r"\b(?:marks|labels|identifies|released?|releasing|made available)"
    r"[^.]{0,120}\bpublic domain\b|"
    r"\b(?:licensed|distributed|made available|published|republished|supplied|uploaded)"
    r"[^.]{0,120}\b(?:CC0|CC BY|Creative Commons|PD-US)\b|"
    r"\bunder (?:the )?(?:CC0|CC BY|Creative Commons|PD-US)\b|"
    r"\b(?:non-free|fair[ -]use)\b|"
    r"\bgrants no licence\b|"
    r"\bthe non-free rationale\b|"
    r"\bunderlying rights status\b|"
    r"\bimage rights holder\b"
    r")",
    flags=re.IGNORECASE,
)

SOURCE_LITERAL_URL_PATTERN = re.compile(r"https?://[^\s<>]+", flags=re.IGNORECASE)


def comparable_source_url(value: str) -> str:
    try:
        parsed = urlparse(value)
    except ValueError:
        return value
    path = parsed.path.rstrip("/") or "/"
    query = "&".join(
        f"{key}={item}"
        for key, item in sorted(parse_qsl(parsed.query, keep_blank_values=True))
    )
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            parsed.params,
            query,
            "",
        )
    )


def comparable_external_media_url(value: str) -> str:
    """Normalize provider URLs without conflating distinct media objects."""
    try:
        parsed = urlparse(value.strip())
    except ValueError:
        return value.strip()
    host = parsed.netloc.casefold().removeprefix("www.")
    if host in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
        video_id = dict(parse_qsl(parsed.query, keep_blank_values=True)).get("v", "")
        if video_id:
            return f"https://youtube.com/watch?v={video_id}"
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/", 1)[0]
        if video_id:
            return f"https://youtube.com/watch?v={video_id}"
    return comparable_source_url(value.strip())

PERIOD_ORDER = ("warsaw", "european", "hollywood")
MAP_PRECISION_VALUES = {
    "address_level",
    "venue_level",
    "site_approximate",
    "district_level",
    "city_level",
}
WARSAW_1926_EVENT_IDS = {"TE0014", "TE0047"}
EUROPEAN_1926_EVENT_IDS = {"TE0015", "TE0016", "TE0048"}

# These fields represent the same graph edge from opposite ends.  They are not
# merely denormalized search helpers: both ends are used independently by the
# public record views, so a one-sided edge produces different evidence
# depending on which record the reader opens.
SYMMETRIC_LINKS = (
    ("People", "sourceIds", "Sources", "personIds"),
    ("People", "timelineEventIds", "Timeline Events", "personIds"),
    ("People", "placeIds", "Places", "personIds"),
    ("People", "contributionIds", "Contributions", "personIds"),
    ("People", "nameVariantIds", "Person Name Variants", "personIds"),
    # A label and the company behind it: the relation the notes had always
    # stated in prose, and which the graph could not express. Both ends live in
    # the same table, so the pair is its own inverse.
    ("Organizations", "parentOrganizationIds", "Organizations", "imprintIds"),
    ("Organizations", "sourceIds", "Sources", "organizationIds"),
    ("Organizations", "placeIds", "Places", "organizationIds"),
    ("Organizations", "timelineEventIds", "Timeline Events", "organizationIds"),
    ("Organizations", "contributionIds", "Contributions", "organizationIds"),
    ("Sources", "workIds", "Works", "sourceIds"),
    ("Sources", "mediaIds", "Media", "sourceIds"),
    ("Sources", "timelineEventIds", "Timeline Events", "sourceIds"),
    ("Sources", "otherWorkIds", "Other Works", "sourceIds"),
    ("Sources", "placeIds", "Places", "sourceIds"),
    ("Sources", "filmIds", "Films", "sourceIds"),
    ("Sources", "songIds", "Songs", "sourceIds"),
    ("Sources", "workRelationIds", "Work Relations", "sourceIds"),
    ("Sources", "titleVariantIds", "Title Variants", "sourceIds"),
    ("Sources", "contributionIds", "Contributions", "sourceIds"),
    ("Sources", "nameVariantIds", "Person Name Variants", "sourceIds"),
    ("Media", "workIds", "Works", "mediaIds"),
    ("Media", "songIds", "Songs", "mediaIds"),
    ("Media", "timelineEventIds", "Timeline Events", "mediaIds"),
    ("Media", "heroTimelineEventIds", "Timeline Events", "heroMediaIds"),
    ("Media", "placeIds", "Places", "mediaIds"),
    ("Works", "timelineEventIds", "Timeline Events", "workIds"),
    ("Works", "titleVariantIds", "Title Variants", "workIds"),
    ("Works", "contributionIds", "Contributions", "workIds"),
    ("Works", "nameVariantIds", "Person Name Variants", "workIds"),
    ("Films", "workIds", "Works", "filmIds"),
    ("Songs", "workIds", "Works", "songIds"),
    ("Other Works", "workIds", "Works", "otherWorkIds"),
    ("Timeline Events", "placeIds", "Places", "timelineEventIds"),
)


def canonical_periods(values: list[str]) -> list[str]:
    return [period for period in PERIOD_ORDER if period in set(values)]


def expected_event_periods(event: dict[str, Any]) -> list[str]:
    event_id = event["id"]
    if event_id in WARSAW_1926_EVENT_IDS:
        return ["warsaw"]
    if event_id in EUROPEAN_1926_EVENT_IDS:
        return ["european"]
    start_year = int(str(event.get("dateStart") or event.get("sortDate"))[:4])
    end_year = int(str(event.get("dateEnd") or start_year)[:4])
    periods: list[str] = []
    if start_year <= 1926:
        periods.append("warsaw")
    if end_year >= 1927 and start_year <= 1934:
        periods.append("european")
    if end_year >= 1935:
        periods.append("hollywood")
    return periods


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

    def _validate_work_titles(self) -> None:
        """Keep canonical display titles stable and synchronized across tables.

        Exact source capitalization belongs in citations and source-form fields.
        Public Work titles are normalized editorial access points; their linked
        Film, Song or Other Work record must therefore use the same display title.
        The explicit title map is deliberately curated instead of applying an
        English title-case algorithm to multilingual data.
        """
        works = {
            record["id"]: record
            for record in self.payloads.get("Works", {}).get("records", [])
        }
        canonical = self.config.get("titleStyle", {}).get(
            "canonicalDisplayTitles", {}
        )
        for work_id, expected in sorted(canonical.items()):
            work = works.get(work_id)
            if work is None:
                self.errors.append(
                    f"Canonical title rule {work_id}: Work does not exist"
                )
            elif work.get("title") != expected:
                self.errors.append(
                    f"Works {work_id}: canonical display title must be {expected!r}"
                )

        linked_tables = (
            ("filmIds", "Films"),
            ("songIds", "Songs"),
            ("otherWorkIds", "Other Works"),
        )
        for link_field, table_name in linked_tables:
            related = {
                record["id"]: record
                for record in self.payloads.get(table_name, {}).get("records", [])
            }
            for work_id, work in works.items():
                for related_id in work.get(link_field, []):
                    record = related.get(related_id)
                    if record is not None and record.get("title") != work.get("title"):
                        self.errors.append(
                            f"Works {work_id} and {table_name} {related_id}: "
                            "display titles do not match"
                        )

    def _validate_symmetric_links(self) -> None:
        records_by_table = {
            table_name: {
                record["id"]: record
                for record in payload.get("records", [])
                if record.get("id")
            }
            for table_name, payload in self.payloads.items()
        }

        def check_direction(
            source_table: str,
            source_field: str,
            target_table: str,
            target_field: str,
        ) -> None:
            source_records = records_by_table.get(source_table, {})
            target_records = records_by_table.get(target_table, {})
            for source_id, source in source_records.items():
                for target_id in source.get(source_field, []) or []:
                    target = target_records.get(target_id)
                    # Dangling targets are reported by _validate_schema_and_links.
                    if target is None:
                        continue
                    if source_id not in (target.get(target_field, []) or []):
                        self.errors.append(
                            f"Asymmetric relation: {source_table} {source_id}.{source_field} "
                            f"contains {target_id}, but {target_table} "
                            f"{target_id}.{target_field} omits {source_id}"
                        )

        for left_table, left_field, right_table, right_field in SYMMETRIC_LINKS:
            check_direction(left_table, left_field, right_table, right_field)
            check_direction(right_table, right_field, left_table, left_field)

        # Work Relations have two directional endpoints but a single inverse
        # list on Works.  They cannot be expressed as a simple field pair
        # above: requiring every relation to be both a source and a target
        # would destroy the direction of the relation.
        works = records_by_table.get("Works", {})
        relations = records_by_table.get("Work Relations", {})
        for relation_id, relation in relations.items():
            endpoint_ids = set(relation.get("sourceWorkIds", []) or []) | set(
                relation.get("targetWorkIds", []) or []
            )
            for work_id in endpoint_ids:
                work = works.get(work_id)
                if work is None:
                    continue
                if relation_id not in (work.get("relationIds", []) or []):
                    self.errors.append(
                        f"Asymmetric relation: Work Relations {relation_id} references "
                        f"Works {work_id}, but Works {work_id}.relationIds omits "
                        f"{relation_id}"
                    )
        for work_id, work in works.items():
            for relation_id in work.get("relationIds", []) or []:
                relation = relations.get(relation_id)
                if relation is None:
                    continue
                endpoint_ids = set(relation.get("sourceWorkIds", []) or []) | set(
                    relation.get("targetWorkIds", []) or []
                )
                if work_id not in endpoint_ids:
                    self.errors.append(
                        f"Asymmetric relation: Works {work_id}.relationIds contains "
                        f"{relation_id}, but Work Relations {relation_id} has no endpoint "
                        f"for {work_id}"
                    )

    def _validate_media_source_work_support(self) -> None:
        """Reject media-to-work links contradicted by item-level source links.

        The rule is deliberately limited to externally linked audio recordings:
        composite visual media may legitimately combine film- and song-level
        context.  Some recording sources do not identify a work at all, so an
        empty source-side work set is not an error.  Once at least one linked
        source does identify works, however, every work assigned to the recording
        must occur in that combined source evidence.  This catches stale but
        technically symmetric links such as attaching a recording to the wrong
        publication series.
        """
        media = {
            record["id"]: record
            for record in self.payloads.get("Media", {}).get("records", [])
            if record.get("id")
        }
        sources = {
            record["id"]: record
            for record in self.payloads.get("Sources", {}).get("records", [])
            if record.get("id")
        }
        for media_id, item in media.items():
            if not (
                item.get("mediaType") == "audio"
                and item.get("storageType") == "external"
            ):
                continue
            supported_work_ids: set[str] = set()
            for source_id in item.get("sourceIds", []) or []:
                source = sources.get(source_id)
                if source is not None:
                    supported_work_ids.update(source.get("workIds", []) or [])
            if not supported_work_ids:
                continue
            unsupported = sorted(
                set(item.get("workIds", []) or []) - supported_work_ids
            )
            if unsupported:
                self.errors.append(
                    f"Unsupported media relation: Media {media_id}.workIds contains "
                    f"{', '.join(unsupported)}, but none of its linked Sources "
                    "documents that Work"
                )

    def _validate_audio_organization_support(self) -> None:
        """Keep recording agents separate from work and access organizations."""

        sources_by_id = {
            record["id"]: record
            for record in self.payloads.get("Sources", {}).get("records", [])
        }
        organizations_by_id = {
            record["id"]: record
            for record in self.payloads.get("Organizations", {}).get("records", [])
        }
        contributions = self.payloads.get("Contributions", {}).get("records", [])
        for media in self.payloads.get("Media", {}).get("records", []):
            if not (
                media.get("mediaType") == "audio"
                and media.get("storageType") == "external"
            ):
                continue
            expected = expected_audio_organization_ids(
                media,
                sources_by_id=sources_by_id,
                organizations_by_id=organizations_by_id,
                contributions=contributions,
            )
            actual = sorted(set(media.get("organizationIds") or []))
            if actual != expected:
                self.errors.append(
                    f"Media {media['id']}: external audio organizationIds "
                    f"{actual or '[]'} do not match the exact recording agents "
                    f"supported by its Sources {expected or '[]'}"
                )

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
                host = urlparse(value).hostname or ""
                if host.casefold() in {
                    item.casefold()
                    for item in self.config.get("forbiddenRemoteAssetHosts", [])
                }:
                    self.errors.append(f"{context}: contains a forbidden temporary asset URL")
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

        for person in self.payloads.get("People", {}).get("records", []):
            authorized_name = str(person.get("authorizedName", "")).strip()
            if (
                person.get("birthYear") is not None
                and person.get("deathYear") is not None
                and PERSON_AUTHORIZED_NAME_DATES_PATTERN.search(authorized_name)
            ):
                self.errors.append(
                    f"People {person.get('id', 'unknown')}: authorizedName duplicates "
                    "the structured birthYear/deathYear values"
                )

        # Publisher contributions are public graph identifiers, not opaque
        # import handles: the role token and organization suffix are used when
        # tracing the same edge across Works, Sources and Organizations.  A
        # mismatched suffix previously left Dacapo credits carrying Edition
        # Coda identifiers, while an RL token concealed a publisher role.
        for contribution in self.payloads.get("Contributions", {}).get("records", []):
            if contribution.get("role") != "publisher":
                continue
            organization_ids = contribution.get("organizationIds", []) or []
            contribution_id = str(contribution.get("id", ""))
            if len(organization_ids) != 1:
                self.errors.append(
                    f"Contribution {contribution_id}: publisher role requires exactly "
                    "one organizationIds value"
                )
                continue
            expected_suffix = f"-PUB-{organization_ids[0]}"
            if not contribution_id.endswith(expected_suffix):
                self.errors.append(
                    f"Contribution {contribution_id}: publisher identifier must end "
                    f"with {expected_suffix}"
                )

        # A file name is not a title. Twenty-nine portrait sources were called
        # things like "File:Smzeisle.jpg", which tells a reader nothing about who
        # is in the picture, while the file name itself was already in the URL or
        # the citation. The title names the thing; the identifier lives where
        # identifiers live.
        for record in self.payloads.get("Sources", {}).get("records", []):
            title = record.get("title")
            if isinstance(title, str) and title.startswith(("File:", "File :", "Datei:")):
                self.errors.append(
                    f"Sources {record.get('id', 'unknown')}: title is a file name, not a title"
                )

        # This archive's own record numbers are for joining records, not for
        # reading. Three GEMA entries were titled "GEMA work entry for S026" and
        # one citation said "work entry for S0100" — a number that is not even a
        # GEMA identifier, and in the citation not even the right one, since the
        # record is S100. A reader cannot follow any of them anywhere.
        for record in self.payloads.get("Sources", {}).get("records", []):
            for field_name in ("title", "shortCitation", "fullCitation"):
                value = record.get(field_name)
                if isinstance(value, str) and INTERNAL_ID.search(value):
                    self.errors.append(
                        f"Sources {record.get('id', 'unknown')}: {field_name} shows "
                        f"an internal record number, which means nothing outside this archive"
                    )

        # A publication is named, not numbered. SRC0785 carried "D 4431" here —
        # a disc's catalogue number sitting where its label's name belongs, on a
        # pressing whose label is not named by any source on the record. Five
        # other sources carry no publication at all, which is the honest state
        # when nobody knows it; a number is not an improvement on that.
        for record in self.payloads.get("Sources", {}).get("records", []):
            value = record.get("publication")
            if isinstance(value, str) and BARE_IDENTIFIER.match(value.strip()):
                self.errors.append(
                    f"Sources {record.get('id', 'unknown')}: publication is a "
                    f"catalogue number, not the name of a publication"
                )

        # The link behind "Open source" is the one promise a source record makes
        # to a reader: click it and see the document. SRC0477 pointed at a IIIF
        # manifest and delivered a wall of JSON; M241 pointed at the raw OCR text
        # of a scan. Both while the archive's other records for the same
        # repositories used the readable item page.
        #
        # Checked on Media as well as Sources, because that is where two of the
        # four bad links were, and one rule that walks every reader-facing field
        # is the only kind that will not miss the next one.
        for table, field in READER_FACING_LINKS:
            for record in self.payloads.get(table, {}).get("records", []):
                url = record.get(field)
                if not isinstance(url, str):
                    continue
                rid = record.get("id", "unknown")
                if MACHINE_ENDPOINT.search(url):
                    self.errors.append(
                        f"{table} {rid}: {field} points at a machine endpoint, "
                        f"not a page a reader can open"
                    )
                if UNSTABLE_HOST.search(url):
                    self.errors.append(
                        f"{table} {rid}: {field} uses an Internet Archive node host, "
                        f"which is not a durable address"
                    )
                if SELF_REFERENCE.search(url):
                    self.errors.append(
                        f"{table} {rid}: {field} points at this archive's own copy "
                        f"instead of the external source"
                    )

        # Two sources that cannot be told apart by their titles are, for anyone
        # reading a list of them, the same record twice. Thirty-seven were, in
        # eighteen groups, and every one of them was a genuinely different
        # source — three papers reviewing one recital, a film entry beside the
        # sheet music for songs from that film. Folded rather than compared
        # literally: two of the eighteen differed only by a bracket or by how a
        # label's name was hyphenated, and a literal comparison walked past both.
        seen_titles: dict[str, str] = {}
        for record in self.payloads.get("Sources", {}).get("records", []):
            title = record.get("title")
            if not isinstance(title, str) or not title.strip():
                continue
            key = re.sub(
                r"[^a-z0-9]+", "", unicodedata.normalize("NFKD", title.lower())
            )
            if key in seen_titles:
                self.errors.append(
                    f"Sources {record.get('id', 'unknown')}: title cannot be told "
                    f"apart from {seen_titles[key]}"
                )
            seen_titles[key] = record.get("id", "unknown")

        # Citation typography is part of the citation. A straight quotation mark
        # or a hyphen standing in for an en dash is not a smaller mistake than a
        # wrong page number — it is the same record written two ways, and 64 of
        # them had drifted before this rule existed. Titles are exempt: one of
        # them is a Wikimedia file name, where the straight mark is the
        # identifier and changing it breaks the reference.
        for record in self.payloads.get("Sources", {}).get("records", []):
            record_id = record.get("id", "unknown")
            # Titles joined the rule once the last file-named title was gone:
            # the one string that needed a straight mark was a Wikimedia file
            # name, and it is no longer a title.
            for field_name in ("fullCitation", "shortCitation", "title"):
                value = record.get(field_name)
                if not isinstance(value, str):
                    continue
                if '"' in value:
                    self.errors.append(
                        f"Sources {record_id}: {field_name} uses a straight quotation mark"
                    )
                # The first version of this rule only knew about (1908-2011) and
                # so walked straight past (18..-1961) at SRC0632, where the same
                # record's own full citation already had the en dash. A register
                # writes an unknown century as 18.. and an open end as .... or ?,
                # and those ranges take the same dash as any other.
                if re.search(YEAR_RANGE_WITH_HYPHEN, value):
                    self.errors.append(
                        f"Sources {record_id}: {field_name} uses a hyphen where a date range needs an en dash"
                    )

        # The rule stopped at Sources, and a work's own name is quoted as often
        # as a citation is: W-S018 and S018 were both called Sagen kleine Mädels
        # "nein" with straight marks, which is the same drift one table over.
        for table_name in ("Works", "Songs", "Films", "Other Works", "Title Variants"):
            for record in self.payloads.get(table_name, {}).get("records", []):
                title = record.get("title")
                if isinstance(title, str) and '"' in title:
                    self.errors.append(
                        f"{table_name} {record.get('id', 'unknown')}: "
                        f"title uses a straight quotation mark"
                    )

        for table_name, fields in PUBLIC_NARRATIVE_FIELDS.items():
            for record in self.payloads.get(table_name, {}).get("records", []):
                record_id = record.get("id", "unknown")
                for field_name in fields:
                    value = record.get(field_name)
                    if isinstance(value, str) and PUBLIC_EDITORIAL_NARRATOR_PATTERN.search(value):
                        self.errors.append(
                            f"{table_name} {record_id}: public field {field_name} "
                            "contains context-dependent editorial narration"
                        )

        image_media_ids = {
            record["id"]
            for record in self.payloads.get("Media", {}).get("records", [])
            if record.get("mediaType") == "image"
        }

        for source in self.payloads.get("Sources", {}).get("records", []):
            source_id = source["id"]
            for error in source_date_errors(source):
                self.errors.append(f"Source {source_id}: {error}")
            if (
                source.get("sourceType") == "sheet_music"
                and source.get("repository") == HOFMEISTER_REPOSITORY
                and HOFMEISTER_INVERTED_CREATOR_PATTERN.search(
                    str(source.get("creator", ""))
                )
            ):
                self.errors.append(
                    f"Source {source_id}: creator uses inverted catalogue-name order"
                )
            for organization_id in expected_repository_organization_ids(source):
                if organization_id not in (source.get("organizationIds") or []):
                    self.errors.append(
                        f"Source {source_id}: repository field requires organization "
                        f"relation {organization_id}"
                    )
            if source.get("sourceType") == "discography":
                self.errors.append(
                    f"Source {source_id}: legacy sourceType 'discography' must be "
                    "normalized to recording_discographic_source"
                )
            research_note = str(source.get("researchNote", "")).strip()
            research_note_type = str(source.get("researchNoteType", "")).strip()
            if bool(research_note) != bool(research_note_type):
                self.errors.append(
                    f"Source {source_id}: researchNote and researchNoteType must be supplied together"
                )
            if (
                research_note_type
                and research_note_type not in SOURCE_RESEARCH_NOTE_TYPES
            ):
                self.errors.append(
                    f"Source {source_id}: unsupported researchNoteType "
                    f"{research_note_type!r}"
                )
            is_normalized_filmographic_source = (
                source.get("sourceType") == "filmographic_database"
                or source_id in {"SRC0174", "SRC0602"}
            )
            full_citation = str(source.get("fullCitation", ""))
            if source.get("accessDate") and has_redundant_access_date(
                full_citation
            ):
                self.errors.append(
                    f"Source {source_id}: fullCitation repeats the structured accessDate"
                )
            if (
                source.get("sourceType") == "filmographic_database"
                and not source.get("accessDate")
            ):
                self.errors.append(
                    f"Source {source_id}: filmographic database source lacks accessDate"
                )
            if source.get("sourceType") == "authority_record":
                if not source.get("accessDate"):
                    self.errors.append(
                        f"Source {source_id}: authority record lacks accessDate"
                    )
                authority_host = authority_hostname(source)
                authority_repository = AUTHORITY_REPOSITORY_BY_HOST.get(
                    authority_host
                )
                if (
                    authority_repository
                    and source.get("repository") != authority_repository
                ):
                    self.errors.append(
                        f"Source {source_id}: repository must be "
                        f"{authority_repository!r} for {authority_host}"
                    )
                authority_organization = AUTHORITY_ORGANIZATION_BY_HOST.get(
                    authority_host
                )
                if (
                    authority_organization
                    and authority_organization
                    not in source.get("organizationIds", [])
                ):
                    self.errors.append(
                        f"Source {source_id}: missing authority organization "
                        f"{authority_organization} for {authority_host}"
                    )
            if source.get("sourceType") == "recording_discographic_source":
                if not source.get("accessDate"):
                    self.errors.append(
                        f"Source {source_id}: recording source lacks accessDate"
                    )
                recording_organization = RECORDING_ORGANIZATION_BY_HOST.get(
                    recording_hostname(source)
                )
                if (
                    recording_organization
                    and recording_organization
                    not in source.get("organizationIds", [])
                ):
                    self.errors.append(
                        f"Source {source_id}: missing recording repository organization "
                        f"{recording_organization}"
                    )
            if is_normalized_visual_source(source):
                if source.get("primaryUrl") and not source.get("accessDate"):
                    self.errors.append(
                        f"Source {source_id}: online visual source lacks accessDate"
                    )
                if VISUAL_RIGHTS_NARRATIVE_PATTERN.search(full_citation):
                    self.errors.append(
                        f"Source {source_id}: fullCitation contains rights analysis "
                        "that belongs in the linked Media record"
                    )
                if (
                    is_wikimedia_source(source)
                    and WIKIMEDIA_ORGANIZATION_ID
                    not in source.get("organizationIds", [])
                ):
                    self.errors.append(
                        f"Source {source_id}: missing Wikimedia repository organization "
                        f"{WIKIMEDIA_ORGANIZATION_ID}"
                    )
            hostname = source_hostname(source)
            expected_repository = CANONICAL_REPOSITORY_BY_HOST.get(hostname)
            if (
                source.get("sourceType") == "filmographic_database"
                and expected_repository
                and source.get("repository") != expected_repository
            ):
                self.errors.append(
                    f"Source {source_id}: repository must be {expected_repository!r} "
                    f"for {hostname}"
                )
            expected_repository_organization = REPOSITORY_ORGANIZATION_BY_HOST.get(
                hostname
            )
            if (
                source.get("sourceType") == "filmographic_database"
                and expected_repository_organization
                and expected_repository_organization
                not in source.get("organizationIds", [])
            ):
                self.errors.append(
                    f"Source {source_id}: missing repository organization "
                    f"{expected_repository_organization} for {hostname}"
                )
            is_image_source = bool(
                image_media_ids.intersection(source.get("mediaIds", []))
            )
            for key in ("fullCitation", "shortCitation"):
                value = str(source.get(key, ""))
                if SOURCE_PUBLIC_IDENTIFIER_PATTERN.search(value):
                    self.errors.append(
                        f"Source {source_id}: public field {key} contains a technical record identifier"
                    )
                if SOURCE_PUBLIC_WORKFLOW_PATTERN.search(value):
                    self.errors.append(
                        f"Source {source_id}: public field {key} contains editorial workflow text"
                    )
                if re.search(r"https?:,\s", value, flags=re.IGNORECASE):
                    self.errors.append(
                        f"Source {source_id}: public field {key} contains a malformed URL"
                    )
                if SOURCE_LITERAL_URL_PATTERN.search(value):
                    self.errors.append(
                        f"Source {source_id}: public field {key} contains a navigational URL"
                    )
                if is_image_source and SOURCE_IMAGE_RIGHTS_ANALYSIS_PATTERN.search(value):
                    self.errors.append(
                        f"Source {source_id}: photographic field {key} contains rights "
                        "analysis that belongs in the linked Media record"
                    )

            link_urls: list[str] = []
            for key in ("primaryUrl", "accessUrl"):
                value = source.get(key)
                if not value:
                    continue
                parsed = urlparse(str(value))
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    self.errors.append(
                        f"Source {source_id}: {key} is not a valid HTTP(S) URL"
                    )
                link_urls.append(str(value))

            additional_links = source.get("additionalLinks", [])
            if not isinstance(additional_links, list):
                self.errors.append(
                    f"Source {source_id}: additionalLinks is not an array"
                )
            else:
                for index, link in enumerate(additional_links):
                    if not isinstance(link, dict) or set(link) != {
                        "label",
                        "url",
                        "role",
                    }:
                        self.errors.append(
                            f"Source {source_id}: additionalLinks[{index}] is malformed"
                        )
                        continue
                    parsed = urlparse(str(link.get("url", "")))
                    if (
                        parsed.scheme not in {"http", "https"}
                        or not parsed.netloc
                    ):
                        self.errors.append(
                            f"Source {source_id}: additionalLinks[{index}] has an invalid URL"
                        )
                    link_urls.append(str(link.get("url", "")))

            comparable_links = [
                comparable_source_url(url) for url in link_urls if url
            ]
            if len(comparable_links) != len(set(comparable_links)):
                self.errors.append(
                    f"Source {source_id}: structured source links contain duplicates"
                )

            identifiers = source.get("identifiers", [])
            if not isinstance(identifiers, list):
                self.errors.append(
                    f"Source {source_id}: identifiers is not an array"
                )
            else:
                seen_identifiers: set[tuple[str, str]] = set()
                for index, identifier in enumerate(identifiers):
                    if not isinstance(identifier, dict) or set(identifier) != {
                        "scheme",
                        "value",
                    }:
                        self.errors.append(
                            f"Source {source_id}: identifiers[{index}] is malformed"
                        )
                        continue
                    scheme = str(identifier.get("scheme", "")).casefold()
                    value = str(identifier.get("value", ""))
                    if scheme not in SOURCE_IDENTIFIER_SCHEMES or not value:
                        self.errors.append(
                            f"Source {source_id}: identifiers[{index}] has an unsupported scheme or empty value"
                        )
                    key = (scheme, value.casefold())
                    if key in seen_identifiers:
                        self.errors.append(
                            f"Source {source_id}: identifiers contain duplicates"
                        )
                    seen_identifiers.add(key)

        for organization in self.payloads.get("Organizations", {}).get("records", []):
            organization_id = organization["id"]
            organization_types = organization.get("types", []) or []
            if "record label" in organization_types:
                self.errors.append(
                    f"Organization {organization_id}: use canonical type 'record_label', "
                    "not 'record label'"
                )
            name_variants = str(organization.get("nameVariants", ""))
            if re.search(
                r"\b(?:the company|the record business|described by|according to|"
                r"probable affiliated|record series|from \d{4}|became|passed to)\b",
                name_variants,
                flags=re.IGNORECASE,
            ):
                self.errors.append(
                    f"Organization {organization_id}: nameVariants contains narrative text"
                )

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

        for table_name in (
            "Works",
            "Films",
            "Songs",
            "Other Works",
            "Media",
            "Timeline Events",
            "Places",
        ):
            for record in self.payloads.get(table_name, {}).get("records", []):
                periods = record.get("periods")
                if not isinstance(periods, list) or not periods:
                    self.errors.append(
                        f"{table_name} {record['id']}: missing chronological periods"
                    )
                    continue
                if any(period not in PERIOD_ORDER for period in periods):
                    self.errors.append(
                        f"{table_name} {record['id']}: invalid chronological periods {periods}"
                    )
                expected_order = [
                    period for period in PERIOD_ORDER if period in set(periods)
                ]
                if periods != expected_order:
                    self.errors.append(
                        f"{table_name} {record['id']}: chronological periods are not canonical"
                    )
                if record.get("period") != periods[0]:
                    self.errors.append(
                        f"{table_name} {record['id']}: primary period does not match periods"
                    )

        for work in self.payloads.get("Works", {}).get("records", []):
            year = int(work["year"])
            if year <= 1925:
                expected = "warsaw"
            elif year >= 1935:
                expected = "hollywood"
            elif year >= 1927:
                expected = "european"
            else:
                expected = None
            if expected and work.get("period") != expected:
                self.errors.append(
                    f"Works {work['id']}: {year} must use chronological period {expected}"
                )

        for media in self.payloads.get("Media", {}).get("records", []):
            if media.get("mediaType") not in MEDIA_TYPES:
                self.errors.append(
                    f"Media {media['id']}: unsupported mediaType {media.get('mediaType')!r}"
                )
            if (
                media.get("mediaType") != "document_gallery"
                and len(media.get("periods", [])) != 1
            ):
                self.errors.append(
                    f"Media {media['id']}: a non-gallery medium must have one editorial period"
                )

        events = {
            record["id"]: record
            for record in self.payloads.get("Timeline Events", {}).get("records", [])
        }
        for event in events.values():
            expected = expected_event_periods(event)
            if event.get("periods") != expected:
                self.errors.append(
                    f"Timeline Events {event['id']}: expected chronological periods {expected}"
                )

        works = {
            record["id"]: record
            for record in self.payloads.get("Works", {}).get("records", [])
        }
        for table_name in ("Films", "Songs", "Other Works"):
            for record in self.payloads.get(table_name, {}).get("records", []):
                linked_periods = canonical_periods(
                    [
                        period
                        for work_id in record.get("workIds", [])
                        for period in works.get(work_id, {}).get("periods", [])
                    ]
                )
                if linked_periods and record.get("periods") != linked_periods:
                    self.errors.append(
                        f"{table_name} {record['id']}: periods do not match its canonical Work"
                    )

        media_records = {
            record["id"]: record
            for record in self.payloads.get("Media", {}).get("records", [])
        }
        for media in media_records.values():
            if media.get("mediaType") != "document_gallery":
                continue
            expected = canonical_periods(
                [
                    period
                    for member_id in media.get("galleryMemberIds", [])
                    for period in media_records.get(member_id, {}).get("periods", [])
                ]
            )
            if not expected:
                expected = canonical_periods(
                    [
                        period
                        for event_id in media.get("timelineEventIds", [])
                        for period in events.get(event_id, {}).get("periods", [])
                    ]
                )
            if expected and media.get("periods") != expected:
                self.errors.append(
                    f"Media {media['id']}: gallery periods do not match its members"
                )

        for place in self.payloads.get("Places", {}).get("records", []):
            precision = place.get("mapPrecision")
            if precision not in MAP_PRECISION_VALUES:
                self.errors.append(
                    f"Places {place['id']}: invalid mapPrecision {precision!r}"
                )
            if precision == "site_approximate" and not str(
                place.get("publicNote", "")
            ).strip():
                self.errors.append(
                    f"Places {place['id']}: approximate site requires a public note"
                )
            expected = canonical_periods(
                [
                    period
                    for event_id in place.get("timelineEventIds", [])
                    for period in events.get(event_id, {}).get("periods", [])
                ]
            )
            if expected and place.get("periods") != expected:
                self.errors.append(
                    f"Places {place['id']}: periods do not match linked timeline events"
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
        sources_by_id = {
            source["id"]: source
            for source in self.payloads.get("Sources", {}).get("records", [])
        }
        seen_assets: set[str] = set()
        external_audio_by_work: dict[str, list[str]] = defaultdict(list)
        for media in self.payloads.get("Media", {}).get("records", []):
            media_id = media["id"]
            sort_order = media.get("sortOrder")
            if isinstance(sort_order, bool) or not isinstance(sort_order, int):
                self.errors.append(
                    f"Media {media_id}: sortOrder must be an integer"
                )
            if (
                media.get("storageType") == "external"
                and media.get("mediaType") == "audio"
            ):
                for work_id in media.get("workIds", []):
                    external_audio_by_work[work_id].append(media_id)
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
            if media.get("mediaType") == "document_gallery" and external_url:
                self.errors.append(
                    f"Media {media_id}: a document-gallery container cannot carry "
                    "an item-level externalUrl"
                )
            if media.get("storageType") == "external":
                if media.get("assetPath") or media.get("assetPaths"):
                    self.errors.append(
                        f"Media {media_id}: external medium cannot carry local asset paths"
                    )
                if media.get("assetCount") != 0:
                    self.errors.append(
                        f"Media {media_id}: external medium must declare assetCount 0"
                    )
                parsed_external = urlparse(str(external_url))
                if parsed_external.netloc.casefold().removeprefix("www.") in {
                    "youtube.com",
                    "m.youtube.com",
                    "music.youtube.com",
                }:
                    youtube_query = dict(
                        parse_qsl(parsed_external.query, keep_blank_values=True)
                    )
                    if any(key in youtube_query for key in ("list", "start_radio")):
                        self.errors.append(
                            f"Media {media_id}: YouTube URL must identify only the "
                            "canonical video, without playlist or radio parameters"
                        )
            if (
                media.get("storageType") == "external"
                and media.get("mediaType") == "image"
                and media.get("galleryStatus") != "external_link_only"
            ):
                self.errors.append(
                    f"Media {media_id}: an externally hosted image without a local "
                    "asset must use galleryStatus external_link_only"
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
            is_external_av = (
                media.get("storageType") == "external"
                and media.get("mediaType") in {"audio", "video"}
            )
            if is_external_av:
                external_key = comparable_external_media_url(str(external_url))
                has_access_source = any(
                    comparable_external_media_url(
                        str(sources_by_id.get(source_id, {}).get("primaryUrl", ""))
                    )
                    == external_key
                    for source_id in media.get("sourceIds", [])
                    if external_key and source_id in sources_by_id
                )
                if not has_access_source:
                    self.errors.append(
                        f"Media {media_id}: external audio/video has no linked Source "
                        "whose primaryUrl identifies the same external object"
                    )
                access_sources = [
                    sources_by_id[source_id]
                    for source_id in media.get("sourceIds", [])
                    if source_id in sources_by_id
                    and comparable_external_media_url(
                        str(sources_by_id[source_id].get("primaryUrl", ""))
                    )
                    == external_key
                ]
                expected_access_type = (
                    "online_audio_source"
                    if media.get("mediaType") == "audio"
                    else "online_video_source"
                )
                incompatible_access_sources = [
                    source.get("id")
                    for source in access_sources
                    if source.get("sourceType")
                    in {"online_audio_source", "online_video_source"}
                    and source.get("sourceType") != expected_access_type
                ]
                if incompatible_access_sources:
                    self.errors.append(
                        f"Media {media_id}: access Source type conflicts with "
                        f"mediaType ({', '.join(incompatible_access_sources)})"
                    )
                if media.get("rightsStatus") != "external_content_not_rehosted":
                    self.errors.append(
                        f"Media {media_id}: external audio/video must use "
                        "rightsStatus external_content_not_rehosted"
                    )
                rights_note = str(media.get("rightsNote", "")).casefold()
                if "no local copy is hosted" not in rights_note:
                    self.errors.append(
                        f"Media {media_id}: external audio/video rights note must "
                        "state that no local copy is hosted"
                    )
                if media.get("mediaType") == "audio":
                    public_text = " ".join(
                        str(media.get(key, ""))
                        for key in ("title", "description", "publicCaption", "altText")
                    )
                    if re.search(r"film[- ]excerpt|opening excerpt|complete film", public_text, re.I):
                        self.errors.append(
                            f"Media {media_id}: an external film excerpt or complete film "
                            "cannot be classified as audio"
                        )
            elif media.get("rightsStatus") == "external_content_not_rehosted":
                self.errors.append(
                    f"Media {media_id}: external_content_not_rehosted is reserved "
                    "for externally hosted audio/video"
                )
            if media.get("rightsStatus") == "permission_needed_or_fair_use_claimed":
                required = ["rightsNote", "publicCreditLine"]
                if media_id not in exceptions:
                    required.append("sourceIds")
                for key in required:
                    if is_empty(media.get(key)):
                        self.errors.append(
                            f"Media {media_id}: uncleared-rights record lacks {key}"
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
            if media.get("rightsStatus") in {
                "copyright_undetermined",
                "restricted",
                "mixed_rights",
            }:
                required = ["rightsNote", "publicCreditLine"]
                if media_id not in exceptions:
                    required.append("sourceIds")
                for key in required:
                    if is_empty(media.get(key)):
                        self.errors.append(
                            f"Media {media_id}: {media.get('rightsStatus')} record lacks {key}"
                        )
            if (
                media.get("storageType") == "local"
                and media.get("rightsStatus")
                in {
                    "permission_needed_or_fair_use_claimed",
                    "copyright_undetermined",
                    "restricted",
                    "mixed_rights",
                }
                and media.get("galleryStatus") != "detail_only"
            ):
                self.errors.append(
                    f"Media {media_id}: locally hosted material with unresolved or "
                    "restricted rights must use galleryStatus detail_only"
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

        multiplicity_exceptions = self.config.get("mediaExceptions", {}).get(
            "externalAudioMultiplicityExceptions", {}
        )
        works_by_id = {
            work["id"]: work
            for work in self.payloads.get("Works", {}).get("records", [])
        }
        for work_id, media_ids in sorted(external_audio_by_work.items()):
            actual = sorted(set(media_ids))
            if len(actual) <= 1:
                continue
            exception = multiplicity_exceptions.get(work_id)
            expected = sorted(set((exception or {}).get("mediaIds", [])))
            rationale = str((exception or {}).get("rationale", "")).strip()
            if expected != actual or len(rationale) < 40:
                self.errors.append(
                    f"Works {work_id}: multiple external audio references "
                    f"({', '.join(actual)}) require an exact media exception and "
                    "a substantive rationale in public_export_config.json"
                )

        for work_id, exception in sorted(multiplicity_exceptions.items()):
            if work_id not in works_by_id:
                self.errors.append(f"Media exception {work_id}: work does not exist")
                continue
            actual = sorted(set(external_audio_by_work.get(work_id, [])))
            expected = sorted(set(exception.get("mediaIds", [])))
            if len(actual) <= 1:
                self.errors.append(
                    f"Media exception {work_id}: stale exception; the work no longer "
                    "has multiple external audio references"
                )
            elif expected != actual:
                self.errors.append(
                    f"Media exception {work_id}: configured mediaIds "
                    f"{', '.join(expected) or '(none)'} do not match "
                    f"{', '.join(actual)}"
                )

    def run(self) -> dict[str, Any]:
        self._load_tables()
        self._validate_manifest()
        self._validate_schema_and_links()
        self._validate_work_titles()
        self._validate_symmetric_links()
        self._validate_media_source_work_support()
        self._validate_audio_organization_support()
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
