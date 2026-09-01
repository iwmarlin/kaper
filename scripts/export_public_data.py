#!/usr/bin/env python3
"""Create a deterministic public JSON graph from a compatible source package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from authority_sources import normalize_authority_source
from filmographic_sources import normalize_filmographic_source
from recording_sources import normalize_recording_source
from repository_organizations import expected_repository_organization_ids
from visual_sources import normalize_visual_source


TABLE_ORDER = [
    "People",
    "Organizations",
    "Sources",
    "Media",
    "Works",
    "Films",
    "Songs",
    "Other Works",
    "Title Variants",
    "Work Relations",
    "Timeline Events",
    "Places",
    "Contributions",
    "Person Name Variants",
]

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

MEDIA_DESCRIPTION_WORKFLOW_PATTERN = re.compile(
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
    r"\bexact visual provenance\b"
    r")",
    flags=re.IGNORECASE,
)

MEDIA_RIGHTS_WORKFLOW_PATTERN = re.compile(
    r"(?:"
    r"\b(?:reviewed|checked|updated|revised|confirmed)\s+20\d{2}(?:-\d{2}-\d{2})?\b|"
    r"\b20\d{2}-\d{2}-\d{2}\b|"
    r"\bsupplied by user\b|"
    r"\blocal asset path\b|"
    r"\bsource route\b|"
    r"\bsource:\s*|"
    r"\brecorded in SRC\d+\b|"
    r"\bsource SRC\d+\b|"
    r"\bpublication status\b|"
    r"\bverification remains open\b|"
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
    r"\bnot a licence or legal determination\b|"
    r"\bverify\b|"
    r"\bmay still be (?:checked|refined)\b|"
    r"\bif .* later identified\b"
    r")",
    flags=re.IGNORECASE,
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

SOURCE_LITERAL_URL_PATTERN = re.compile(r"https?://[^\s<>]+", flags=re.IGNORECASE)
SOURCE_DOI_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:DOI\s*:?\s*)?(10\.\d{4,9}/[-._;()/:A-Z0-9]+)",
    flags=re.IGNORECASE,
)
SOURCE_ARK_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:ARK\s*:?\s*)?(ark:/\d+/[A-Za-z0-9._~-]+)",
    flags=re.IGNORECASE,
)
SOURCE_NAID_PATTERN = re.compile(r"\bNAID\s*:?\s*(\d+)\b", flags=re.IGNORECASE)
SOURCE_URL_TRAILING_PUNCTUATION = ".,;:)]}"
SOURCE_RESEARCH_NOTE_TYPES = {
    "authority_note",
    "date_assessment",
    "discographic_note",
    "evidence_note",
    "identity_assessment",
    "object_context",
    "verification_note",
}


def source_url_from_match(value: str) -> str:
    return value.rstrip(SOURCE_URL_TRAILING_PUNCTUATION)


def source_urls(value: str) -> list[str]:
    return [
        source_url_from_match(match.group(0))
        for match in SOURCE_LITERAL_URL_PATTERN.finditer(value)
        if source_url_from_match(match.group(0))
    ]


def comparable_source_url(value: str) -> str:
    """Compare source links without treating a terminal slash as a new resource."""
    try:
        parsed = urlparse(value)
    except ValueError:
        return value
    path = parsed.path.rstrip("/") or "/"
    query = urlencode(
        sorted(parse_qsl(parsed.query, keep_blank_values=True))
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


def source_link_label(url: str) -> tuple[str, str]:
    """Return a concise public label and semantic role for a secondary link."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if "anno.onb.ac.at" in host:
        return ("Open additional catalogue issue", "additional_issue")
    if "kppg.waw.pl" in host:
        return ("Open recording catalogue entry", "catalogue_entry")
    if "/image/" in path or path.endswith(
        (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp")
    ):
        return ("View source image", "source_image")
    if path.endswith(".pdf"):
        return ("Open source PDF", "source_document")
    if "ark.cdlib.org" in host:
        return ("Open ARK resolver", "persistent_identifier")
    return ("Open additional source", "additional_source")


def source_identifiers(value: str) -> list[dict[str, str]]:
    identifiers: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(scheme: str, identifier: str) -> None:
        normalized = identifier.rstrip(SOURCE_URL_TRAILING_PUNCTUATION)
        key = (scheme, normalized.casefold())
        if normalized and key not in seen:
            seen.add(key)
            identifiers.append({"scheme": scheme, "value": normalized})

    for match in SOURCE_DOI_PATTERN.finditer(value):
        add("doi", match.group(1))
    for match in SOURCE_ARK_PATTERN.finditer(value):
        add("ark", match.group(1))
    for match in SOURCE_NAID_PATTERN.finditer(value):
        add("naid", match.group(1))
    return identifiers


def citation_without_literal_urls(value: str) -> str:
    """Remove navigational URLs while retaining DOI/ARK as citation locators."""

    def replace(match: re.Match[str]) -> str:
        raw = match.group(0)
        url = source_url_from_match(raw)
        punctuation = raw[len(url) :]
        doi = SOURCE_DOI_PATTERN.search(url)
        if doi:
            replacement = f"DOI {doi.group(1)}"
        else:
            ark = SOURCE_ARK_PATTERN.search(url)
            if ark:
                prefix = value[max(0, match.start() - 8) : match.start()]
                replacement = (
                    ark.group(1)
                    if re.search(r"\bARK\s*$", prefix, flags=re.IGNORECASE)
                    else f"ARK {ark.group(1)}"
                )
            else:
                replacement = ""
        if "." in punctuation:
            replacement += "."
        elif ";" in punctuation:
            replacement += ";"
        return replacement

    citation = SOURCE_LITERAL_URL_PATTERN.sub(replace, value)
    citation = re.sub(
        r"\s*\b(?:Image URL|Direct image|USC asset page)\s*:\s*\.",
        "",
        citation,
        flags=re.IGNORECASE,
    )
    citation = re.sub(r":\s*\.", ".", citation)
    citation = re.sub(r";\s*\.", ".", citation)
    citation = re.sub(r":\s+(?=\()", " ", citation)
    citation = re.sub(r"\.\s+\.", ".", citation)
    citation = re.sub(r"\s+([,.;:])", r"\1", citation)
    citation = re.sub(r"\s{2,}", " ", citation).strip()
    return citation

SOURCE_TRAILING_EDITORIAL_PATTERNS = [
    re.compile(
        r"\s+Source (?:used )?for (?:Media|Work|works|song|the French-language "
        r"version|replacement|rights-cleared route|Henryk Chwast).*?$",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\s+Used as (?:a )?(?:web |website/list )?source for .*?$",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\s+(?:User-uploaded|English-subtitled user upload).*?"
        r"referenced as a (?:listening|viewing/listening) source.*?$",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\s+Listening/viewing source for .*?$",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\s+Confirms the identity of, and serves as the source for, .*?$",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\s+Source record created from .*?$",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\s+(?:Data|Metadata) supplied (?:by user|from .*?).*?$",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\s+The local portrait .*?$",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\s+Kaper project media asset\.?",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\s+Source record corrected from .*?$",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\s+Used as a filmographic/songwriting-credit source,.*?$",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\s+Source used as evidence for .*?$",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\s+Source for local context image .*?$",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\s+The same or related portrait is also reproduced through .*?$",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\s+Parent catalogue record: .*?$",
        flags=re.IGNORECASE,
    ),
]

SOURCE_TRAILING_BRACKET_NOTE_PATTERN = re.compile(
    r"\s+\[((?:Note on|Notice|Clipping|Review|Item|Press item|"
    r"Broadcast-schedule entry|Production announcement|Premiere advertisement|"
    r"Robbins advertisement|Exact|Publisher|Credits|Richard Tauber item|"
    r"Ehe mit beschränkter Haftung|Song title)[^\]]*)\]\.?$",
    flags=re.IGNORECASE,
)

PERIOD_ORDER = ("warsaw", "european", "hollywood")
PERIOD_YEAR_RANGES = {
    "warsaw": (1902, 1926),
    "european": (1926, 1934),
    "hollywood": (1935, 1939),
}
WARSAW_1926_EVENT_IDS = {"TE0014", "TE0047"}
EUROPEAN_1926_EVENT_IDS = {"TE0015", "TE0016", "TE0048"}


def normalized_source_note(note: str) -> str:
    """Turn a trailing editorial bracket into concise public-facing prose."""
    note = note.strip().rstrip(".")
    note = re.sub(
        r";\s*attribution note retained$",
        "",
        note,
        flags=re.IGNORECASE,
    )
    if re.fullmatch(
        r"Song title not specified in this source record",
        note,
        flags=re.IGNORECASE,
    ):
        return "The source does not identify the song title."
    if re.search(r"\bto be checked\b", note, flags=re.IGNORECASE):
        subject = re.sub(
            r"\s+to be checked$",
            "",
            note,
            flags=re.IGNORECASE,
        )
        return f"{subject} have not been established."
    if re.search(r"\brequire verification\b", note, flags=re.IGNORECASE):
        subject = re.sub(
            r"\s+require verification$",
            "",
            note,
            flags=re.IGNORECASE,
        )
        if not subject.lower().startswith("the "):
            subject = f"The {subject[0].lower()}{subject[1:]}"
        return f"{subject} have not been established."
    return f"{note}."


def normalized_period_key(value: Any) -> str:
    key = str(value or "").strip().lower().replace(" ", "_")
    return key if key in PERIOD_ORDER else ""


def year_from_value(value: Any) -> int | None:
    match = re.search(r"\b(19\d{2})\b", str(value or ""))
    return int(match.group(1)) if match else None


def chronological_period_for_year(year: int) -> str:
    if year <= 1926:
        return "warsaw"
    if year <= 1934:
        return "european"
    return "hollywood"


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


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def selected_name(value: Any) -> Any:
    if isinstance(value, dict) and "name" in value:
        return value["name"]
    return value


def is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def source_record_id(record: dict[str, Any]) -> str | None:
    """Return the source-system key without coupling the public model to its name."""
    explicit = record.get("sourceRecordId")
    if explicit:
        return str(explicit)
    candidates = [
        value
        for key, value in record.items()
        if key != "stableId" and key.casefold().endswith("recordid") and value
    ]
    return str(candidates[0]) if len(candidates) == 1 else None


def normalized_scalar(value: Any) -> Any:
    if isinstance(value, dict):
        if "name" in value:
            return value["name"]
        return {key: normalized_scalar(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalized_scalar(item) for item in value]
    return value


def transform_value(value: Any, transform: str | None) -> Any:
    if transform is None:
        return normalized_scalar(value)
    if transform == "asset_paths":
        if not value:
            return []
        return [
            item.strip()
            for item in re.split(r"[|,;\r\n]+", str(value))
            if item.strip()
        ]
    raise ValueError(f"Unknown transform: {transform}")


class PublicExporter:
    def __init__(
        self,
        backup_root: Path,
        config_path: Path,
        overrides_path: Path | None,
        output_root: Path,
        assets_root: Path | None,
    ) -> None:
        self.backup_root = backup_root.resolve()
        self.config_path = config_path.resolve()
        self.overrides_path = overrides_path.resolve() if overrides_path else None
        self.output_root = output_root.resolve()
        self.assets_root = assets_root.resolve() if assets_root else None
        self.config = read_json(self.config_path)
        self.overrides = (
            read_json(self.overrides_path)
            if self.overrides_path is not None
            else {"schemaVersion": self.config["schemaVersion"], "records": {}}
        )
        self.database_index = read_json(self.backup_root / "database-index.json")
        self.schema = read_json(self.backup_root / "raw/schema.json")
        self.records: dict[str, list[dict[str, Any]]] = {}
        self.by_stable: dict[str, dict[str, dict[str, Any]]] = {}
        self.stable_by_record_id: dict[str, str] = {}
        self.table_by_record_id: dict[str, str] = {}
        self.included: dict[str, set[str]] = {name: set() for name in TABLE_ORDER}
        self.output_records: dict[str, list[dict[str, Any]]] = {}
        self.errors: list[str] = []
        self.warnings: list[dict[str, Any]] = []
        self.applied_overrides: list[dict[str, Any]] = []
        self.applied_exclusions: list[dict[str, Any]] = []
        self.applied_additions: list[dict[str, Any]] = []
        self.applied_link_additions: list[dict[str, Any]] = []
        self.applied_link_removals: list[dict[str, Any]] = []
        self.source_citation_stats: Counter[str] = Counter()
        self._load()

    def _load(self) -> None:
        table_files = {
            item["name"]: item["portableFile"]
            for item in self.database_index["tables"]
        }
        configured = set(self.config["tables"])
        missing_tables = configured - set(table_files)
        if missing_tables:
            raise ValueError(f"Backup is missing configured tables: {sorted(missing_tables)}")
        for table_name in TABLE_ORDER:
            payload = read_json(self.backup_root / table_files[table_name])
            table_records = payload["records"]
            self.records[table_name] = table_records
            self.by_stable[table_name] = {}
            for record in table_records:
                stable_id = record.get("stableId")
                record_id = source_record_id(record)
                if not stable_id:
                    self.errors.append(
                        f"{table_name}: source record {record_id or '[unidentified]'} has no stable ID"
                    )
                    continue
                if not record_id:
                    self.errors.append(f"{table_name}: {stable_id} has no unambiguous source record ID")
                    continue
                if stable_id in self.by_stable[table_name]:
                    self.errors.append(f"{table_name}: duplicate stable ID {stable_id}")
                self.by_stable[table_name][stable_id] = record
                if record_id in self.stable_by_record_id:
                    self.errors.append(f"Duplicate source record ID {record_id}")
                self.stable_by_record_id[record_id] = stable_id
                self.table_by_record_id[record_id] = table_name
        self._validate_config()
        self._validate_overrides()

    def _validate_config(self) -> None:
        schema_fields = {
            table["name"]: {field["name"] for field in table["fields"]}
            for table in self.schema["tables"]
        }
        banned = [
            fragment.lower()
            for fragment in self.config.get("bannedPublicKeyFragments", [])
        ]
        for table_name, table_config in self.config["tables"].items():
            allowed_public_keys = set(table_config["fields"]) | set(table_config["links"])
            allowed_public_keys |= set(table_config.get("derivedFields", []))
            for key in allowed_public_keys:
                lowered = key.lower()
                for fragment in banned:
                    if fragment in lowered:
                        self.errors.append(
                            f"{table_name}: public key {key!r} contains banned fragment {fragment!r}"
                        )
            for public_key, field_spec in table_config["fields"].items():
                source = field_spec if isinstance(field_spec, str) else field_spec["source"]
                if source not in schema_fields[table_name]:
                    self.errors.append(
                        f"{table_name}: allowlisted field {public_key!r} references unknown source {source!r}"
                    )
            for public_key, link_spec in table_config["links"].items():
                if link_spec["field"] not in schema_fields[table_name]:
                    self.errors.append(
                        f"{table_name}: allowlisted link {public_key!r} references unknown source {link_spec['field']!r}"
                    )
                if link_spec["target"] not in self.config["tables"]:
                    self.errors.append(
                        f"{table_name}: allowlisted link {public_key!r} targets unknown table {link_spec['target']!r}"
                    )

    def _validate_overrides(self) -> None:
        if self.overrides.get("schemaVersion") != self.config["schemaVersion"]:
            self.errors.append(
                "Public override schemaVersion does not match the export config"
            )
        records = self.overrides.get("records")
        if not isinstance(records, dict):
            self.errors.append("Public overrides must contain a records object")
            return
        for table_name, table_overrides in records.items():
            if table_name not in self.config["tables"]:
                self.errors.append(f"Overrides reference unknown table {table_name!r}")
                continue
            if not isinstance(table_overrides, dict):
                self.errors.append(f"Overrides for {table_name} must be an object")
                continue
            allowlisted_scalar_keys = set(self.config["tables"][table_name]["fields"])
            allowlisted_scalar_keys |= set(
                self.config["tables"][table_name].get("derivedFields", [])
            )
            for stable_id, override in table_overrides.items():
                if stable_id not in self.by_stable[table_name]:
                    self.errors.append(
                        f"{table_name}: override references unknown record {stable_id}"
                    )
                if not isinstance(override, dict) or not isinstance(
                    override.get("fields"), dict
                ):
                    self.errors.append(
                        f"{table_name} {stable_id}: override must contain a fields object"
                    )
                    continue
                if not override.get("reason"):
                    self.errors.append(
                        f"{table_name} {stable_id}: override requires an audit reason"
                    )
                unexpected = set(override["fields"]) - allowlisted_scalar_keys
                if unexpected:
                    self.errors.append(
                        f"{table_name} {stable_id}: override contains non-allowlisted or relational keys {sorted(unexpected)}"
                    )
                for key, value in override["fields"].items():
                    if key == "id":
                        self.errors.append(
                            f"{table_name} {stable_id}: stable ID cannot be overridden"
                        )
                    if is_empty(value):
                        self.errors.append(
                            f"{table_name} {stable_id}: override value for {key!r} is empty"
                        )
                remove_fields = override.get("removeFields", [])
                if not isinstance(remove_fields, list):
                    self.errors.append(
                        f"{table_name} {stable_id}: removeFields must be an array"
                    )
                    continue
                unexpected_removals = set(remove_fields) - allowlisted_scalar_keys
                if unexpected_removals:
                    self.errors.append(
                        f"{table_name} {stable_id}: removeFields contains non-allowlisted scalar keys {sorted(unexpected_removals)}"
                    )
                required_removals = set(remove_fields) & set(
                    self.config["tables"][table_name]["required"]
                )
                if required_removals:
                    self.errors.append(
                        f"{table_name} {stable_id}: required public fields cannot be removed {sorted(required_removals)}"
                    )

        for table_name, table_additions in self.overrides.get("additions", {}).items():
            if table_name not in self.config["tables"]:
                self.errors.append(f"Additions reference unknown table {table_name!r}")
                continue
            allowed = set(self.config["tables"][table_name]["fields"])
            allowed |= set(self.config["tables"][table_name]["links"])
            allowed |= set(self.config["tables"][table_name].get("derivedFields", []))
            for stable_id, addition in table_additions.items():
                fields = addition.get("fields") if isinstance(addition, dict) else None
                if stable_id in self.by_stable[table_name]:
                    self.errors.append(
                        f"{table_name}: addition duplicates snapshot record {stable_id}"
                    )
                if not isinstance(addition, dict) or not addition.get("reason") or not isinstance(fields, dict):
                    self.errors.append(
                        f"{table_name} {stable_id}: addition requires a reason and fields object"
                    )
                    continue
                if fields.get("id") != stable_id:
                    self.errors.append(
                        f"{table_name} {stable_id}: addition ID must match its stable key"
                    )
                unexpected = set(fields) - allowed
                if unexpected:
                    self.errors.append(
                        f"{table_name} {stable_id}: addition contains non-allowlisted keys {sorted(unexpected)}"
                    )

        for table_name, table_exclusions in self.overrides.get("exclusions", {}).items():
            if table_name not in self.config["tables"]:
                self.errors.append(f"Exclusions reference unknown table {table_name!r}")
                continue
            if not isinstance(table_exclusions, dict):
                self.errors.append(f"Exclusions for {table_name} must be an object")
                continue
            for stable_id, exclusion in table_exclusions.items():
                if stable_id not in self.by_stable[table_name]:
                    self.errors.append(
                        f"{table_name}: exclusion references unknown snapshot record {stable_id}"
                    )
                if not isinstance(exclusion, dict) or not exclusion.get("reason"):
                    self.errors.append(
                        f"{table_name} {stable_id}: exclusion requires an audit reason"
                    )

        for table_name, table_links in self.overrides.get("linkAdditions", {}).items():
            if table_name not in self.config["tables"]:
                self.errors.append(f"Link additions reference unknown table {table_name!r}")
                continue
            allowed = set(self.config["tables"][table_name]["links"])
            for stable_id, addition in table_links.items():
                fields = addition.get("fields") if isinstance(addition, dict) else None
                if not isinstance(addition, dict) or not addition.get("reason") or not isinstance(fields, dict):
                    self.errors.append(
                        f"{table_name} {stable_id}: link addition requires a reason and fields object"
                    )
                    continue
                unexpected = set(fields) - allowed
                if unexpected:
                    self.errors.append(
                        f"{table_name} {stable_id}: link addition contains non-link keys {sorted(unexpected)}"
                    )
                for key, values in fields.items():
                    if not isinstance(values, list) or not all(
                        isinstance(value, str) and value for value in values
                    ):
                        self.errors.append(
                            f"{table_name} {stable_id}: link addition {key!r} must be an array of stable IDs"
                        )

        for table_name, table_links in self.overrides.get("linkRemovals", {}).items():
            if table_name not in self.config["tables"]:
                self.errors.append(f"Link removals reference unknown table {table_name!r}")
                continue
            allowed = set(self.config["tables"][table_name]["links"])
            for stable_id, removal in table_links.items():
                fields = removal.get("fields") if isinstance(removal, dict) else None
                if not isinstance(removal, dict) or not removal.get("reason") or not isinstance(fields, dict):
                    self.errors.append(
                        f"{table_name} {stable_id}: link removal requires a reason and fields object"
                    )
                    continue
                unexpected = set(fields) - allowed
                if unexpected:
                    self.errors.append(
                        f"{table_name} {stable_id}: link removal contains non-link keys {sorted(unexpected)}"
                    )
                for key, values in fields.items():
                    if not isinstance(values, list) or not all(
                        isinstance(value, str) and value for value in values
                    ):
                        self.errors.append(
                            f"{table_name} {stable_id}: link removal {key!r} must be an array of stable IDs"
                        )

    def fields(self, record: dict[str, Any]) -> dict[str, Any]:
        return record.get("fieldsByName", {})

    def approved(self, table_name: str, record: dict[str, Any]) -> bool:
        status = selected_name(self.fields(record).get("Editorial Status"))
        return status == self.config["allowedEditorialStatus"]

    def linked_ids(self, record: dict[str, Any], field_name: str) -> list[str]:
        value = self.fields(record).get(field_name)
        if not value:
            return []
        if not isinstance(value, list):
            self.errors.append(
                f"{record.get('stableId')}: linked field {field_name!r} is not an array"
            )
            return []
        result = []
        for link in value:
            if not isinstance(link, dict) or not link.get("id"):
                self.errors.append(
                    f"{record.get('stableId')}: malformed link in {field_name!r}"
                )
                continue
            stable_id = self.stable_by_record_id.get(link["id"])
            if stable_id is None:
                self.errors.append(
                    f"{record.get('stableId')}: unresolved source-record link {link['id']} in {field_name!r}"
                )
                continue
            result.append(stable_id)
        return result

    def links_any(
        self,
        record: dict[str, Any],
        field_name: str,
        allowed_ids: set[str],
    ) -> bool:
        return bool(set(self.linked_ids(record, field_name)) & allowed_ids)

    def _eligible_core(self) -> None:
        for stable_id, record in self.by_stable["Works"].items():
            scope = selected_name(self.fields(record).get("Public Scope"))
            if self.approved("Works", record) and scope in self.config["allowedWorkScopes"]:
                self.included["Works"].add(stable_id)

        for stable_id, record in self.by_stable["Timeline Events"].items():
            if self.approved("Timeline Events", record) and self.fields(record).get("Display on Site") is True:
                self.included["Timeline Events"].add(stable_id)

        excluded_place_ids = set(self.config.get("excludedPlaceIds", []))
        for stable_id, record in self.by_stable["Places"].items():
            scope = selected_name(self.fields(record).get("Public Scope"))
            if (
                self.approved("Places", record)
                and scope in self.config["allowedPlaceScopes"]
                and stable_id not in excluded_place_ids
            ):
                self.included["Places"].add(stable_id)

        excluded_media_ids = set(self.config.get("excludedMediaIds", []))
        for stable_id, record in self.by_stable["Media"].items():
            gallery = selected_name(self.fields(record).get("Gallery Status"))
            if (
                self.approved("Media", record)
                and gallery in self.config["allowedGalleryStatuses"]
                and stable_id not in excluded_media_ids
            ):
                self.included["Media"].add(stable_id)

        subtype_specs = {
            "Films": "Works Linked",
            "Songs": "Works Linked",
            "Other Works": "Works Linked",
        }
        for table_name, work_field in subtype_specs.items():
            for stable_id, record in self.by_stable[table_name].items():
                if self.approved(table_name, record) and self.links_any(
                    record, work_field, self.included["Works"]
                ):
                    self.included[table_name].add(stable_id)

        for stable_id, record in self.by_stable["Title Variants"].items():
            if self.approved("Title Variants", record) and self.links_any(
                record, "Works Linked", self.included["Works"]
            ):
                self.included["Title Variants"].add(stable_id)

        for stable_id, record in self.by_stable["Work Relations"].items():
            fields = self.fields(record)
            if (
                self.approved("Work Relations", record)
                and fields.get("Publishable") is True
                and self.links_any(record, "Source Work", self.included["Works"])
            ):
                self.included["Work Relations"].add(stable_id)

        excluded_contribution_ids = set(
            self.config.get("excludedContributionIds", [])
        )
        for stable_id, record in self.by_stable["Contributions"].items():
            fields = self.fields(record)
            if (
                self.approved("Contributions", record)
                and fields.get("Publishable") is True
                and selected_name(fields.get("Validation Status")) == "OK"
                and self.links_any(record, "Work", self.included["Works"])
                and stable_id not in excluded_contribution_ids
            ):
                self.included["Contributions"].add(stable_id)

        for stable_id, record in self.by_stable["Person Name Variants"].items():
            fields = self.fields(record)
            reachable = self.links_any(
                record, "Applies to Works", self.included["Works"]
            ) or self.links_any(
                record, "Contributions", self.included["Contributions"]
            )
            if (
                self.approved("Person Name Variants", record)
                and fields.get("Publishable") is True
                and selected_name(fields.get("Validation Status")) == "OK"
                and reachable
            ):
                self.included["Person Name Variants"].add(stable_id)

    def _approved_ids(self, table_name: str) -> set[str]:
        return {
            stable_id
            for stable_id, record in self.by_stable[table_name].items()
            if self.approved(table_name, record)
        }

    def _collect(
        self,
        source_table: str,
        source_field: str,
        target_table: str,
        allowed_targets: set[str],
    ) -> set[str]:
        result: set[str] = set()
        for stable_id in self.included[source_table]:
            record = self.by_stable[source_table][stable_id]
            result.update(
                target
                for target in self.linked_ids(record, source_field)
                if target in allowed_targets
            )
        return result

    def _induce_authorities_and_sources(self) -> None:
        approved_people = self._approved_ids("People") - set(
            self.config.get("excludedPersonIds", [])
        )
        approved_organizations = self._approved_ids("Organizations")
        approved_sources = self._approved_ids("Sources") - set(
            self.config.get("excludedSourceIds", [])
        )

        people_specs = [
            ("Contributions", "Person"),
            ("Work Relations", "People"),
            ("Timeline Events", "People Linked"),
            ("Places", "Related People"),
            ("Person Name Variants", "People Resolved"),
        ]
        organization_specs = [
            ("Contributions", "Organization"),
            ("Timeline Events", "Organizations Linked"),
            ("Places", "Related Organizations"),
            ("Media", "Organizations"),
            ("Works", "Organizations"),
            ("Other Works", "Organizations"),
        ]
        source_specs = [
            ("Works", "Sources Linked"),
            ("Films", "Sources Linked"),
            ("Songs", "Sources Linked"),
            ("Other Works", "Sources Linked"),
            ("Title Variants", "Sources Linked"),
            ("Work Relations", "Sources Linked"),
            ("Timeline Events", "Sources Linked"),
            ("Places", "Sources"),
            ("Media", "Sources Linked"),
            ("Contributions", "Sources Linked"),
            ("Person Name Variants", "Sources Linked"),
        ]

        changed = True
        while changed:
            before = (
                len(self.included["People"]),
                len(self.included["Organizations"]),
                len(self.included["Sources"]),
            )
            for source_table, source_field in people_specs:
                self.included["People"].update(
                    self._collect(
                        source_table,
                        source_field,
                        "People",
                        approved_people,
                    )
                )
            for source_table, source_field in organization_specs:
                self.included["Organizations"].update(
                    self._collect(
                        source_table,
                        source_field,
                        "Organizations",
                        approved_organizations,
                    )
                )
            for source_table, source_field in source_specs:
                self.included["Sources"].update(
                    self._collect(
                        source_table,
                        source_field,
                        "Sources",
                        approved_sources,
                    )
                )

            self.included["People"].update(
                self._collect(
                    "Sources",
                    "Related Person IDs",
                    "People",
                    approved_people,
                )
            )
            self.included["Organizations"].update(
                self._collect(
                    "Sources",
                    "Related Organization IDs",
                    "Organizations",
                    approved_organizations,
                )
            )
            self.included["Sources"].update(
                self._collect("People", "Sources", "Sources", approved_sources)
            )
            self.included["Sources"].update(
                self._collect(
                    "Organizations",
                    "Source IDs",
                    "Sources",
                    approved_sources,
                )
            )
            after = (
                len(self.included["People"]),
                len(self.included["Organizations"]),
                len(self.included["Sources"]),
            )
            changed = before != after

    def select_public_graph(self) -> None:
        self._eligible_core()
        self._induce_authorities_and_sources()

    def _mapped_links(
        self,
        record: dict[str, Any],
        field_name: str,
        target_table: str,
    ) -> list[str]:
        return sorted(
            {
                stable_id
                for stable_id in self.linked_ids(record, field_name)
                if stable_id in self.included[target_table]
            }
        )

    def map_record(
        self,
        table_name: str,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        table_config = self.config["tables"][table_name]
        fields = self.fields(record)
        public: dict[str, Any] = {}
        for public_key, field_spec in table_config["fields"].items():
            if isinstance(field_spec, str):
                source = field_spec
                transform = None
            else:
                source = field_spec["source"]
                transform = field_spec.get("transform")
            value = transform_value(fields.get(source), transform)
            if not is_empty(value):
                public[public_key] = value
        for public_key, link_spec in table_config["links"].items():
            value = self._mapped_links(
                record,
                link_spec["field"],
                link_spec["target"],
            )
            if value:
                public[public_key] = value
        return public

    def _apply_overrides(self) -> None:
        output_by_id = {
            table: {record["id"]: record for record in records}
            for table, records in self.output_records.items()
        }
        for table_name, table_overrides in self.overrides.get("records", {}).items():
            if table_name not in output_by_id:
                continue
            for stable_id, override in table_overrides.items():
                public = output_by_id[table_name].get(stable_id)
                if public is None:
                    self.errors.append(
                        f"{table_name} {stable_id}: configured public override was not applied because the record is not in the public graph"
                    )
                    continue
                public.update(override["fields"])
                for key in override.get("removeFields", []):
                    public.pop(key, None)
                self.applied_overrides.append(
                    {
                        "table": table_name,
                        "id": stable_id,
                        "fields": sorted(override["fields"]),
                        "removedFields": sorted(override.get("removeFields", [])),
                    }
                )

    def _apply_exclusions(self) -> None:
        for table_name, table_exclusions in self.overrides.get("exclusions", {}).items():
            excluded_ids = set(table_exclusions)
            retained = [
                record
                for record in self.output_records.get(table_name, [])
                if record.get("id") not in excluded_ids
            ]
            removed_ids = {
                record.get("id")
                for record in self.output_records.get(table_name, [])
            } - {record.get("id") for record in retained}
            for stable_id in sorted(excluded_ids):
                if stable_id not in removed_ids:
                    self.errors.append(
                        f"{table_name} {stable_id}: configured exclusion was not applied because the record is not in the public graph"
                    )
                    continue
                self.applied_exclusions.append(
                    {"table": table_name, "id": stable_id}
                )
            self.output_records[table_name] = retained

    def _apply_additions(self) -> None:
        output_by_id = {
            table: {record["id"]: record for record in records}
            for table, records in self.output_records.items()
        }
        for table_name, table_additions in self.overrides.get("additions", {}).items():
            for stable_id, addition in table_additions.items():
                if stable_id in output_by_id[table_name]:
                    self.errors.append(
                        f"{table_name} {stable_id}: public addition duplicates an exported record"
                    )
                    continue
                record = normalized_scalar(addition["fields"])
                self.output_records[table_name].append(record)
                output_by_id[table_name][stable_id] = record
                self.applied_additions.append(
                    {"table": table_name, "id": stable_id, "fields": sorted(record)}
                )
            self.output_records[table_name].sort(key=lambda record: record["id"])

        for table_name, table_links in self.overrides.get("linkAdditions", {}).items():
            for stable_id, addition in table_links.items():
                public = output_by_id[table_name].get(stable_id)
                if public is None:
                    self.errors.append(
                        f"{table_name} {stable_id}: link addition target is not in the public graph"
                    )
                    continue
                for key, values in addition["fields"].items():
                    self._append(public, key, values)
                self.applied_link_additions.append(
                    {
                        "table": table_name,
                        "id": stable_id,
                        "fields": sorted(addition["fields"]),
                    }
                )

        for table_name, table_links in self.overrides.get("linkRemovals", {}).items():
            for stable_id, removal in table_links.items():
                public = output_by_id[table_name].get(stable_id)
                if public is None:
                    self.errors.append(
                        f"{table_name} {stable_id}: link removal target is not in the public graph"
                    )
                    continue
                for key, values in removal["fields"].items():
                    retained = [value for value in public.get(key, []) if value not in values]
                    if retained:
                        public[key] = retained
                    else:
                        public.pop(key, None)
                self.applied_link_removals.append(
                    {
                        "table": table_name,
                        "id": stable_id,
                        "fields": sorted(removal["fields"]),
                    }
                )

    def _normalize_media_public_text(self) -> None:
        """Project editorial Media notes into concise public-facing prose."""
        for media in self.output_records["Media"]:
            if (
                media.get("storageType") == "external"
                and media.get("mediaType") in {"audio", "video"}
            ):
                media["rightsStatus"] = "external_content_not_rehosted"
                media["rightsNote"] = (
                    "External content remains on the provider's website; no local copy "
                    "is hosted. Copyright and access conditions are governed by the provider."
                )
            description = str(media.get("description", ""))
            caption = str(media.get("publicCaption", ""))
            if description and MEDIA_DESCRIPTION_WORKFLOW_PATTERN.search(description):
                if caption:
                    media["description"] = caption
                else:
                    media.pop("description", None)

            rights_note = str(media.get("rightsNote", ""))
            fair_use = (
                media.get("rightsStatus") == "permission_needed_or_fair_use_claimed"
            )
            if rights_note and (
                MEDIA_RIGHTS_WORKFLOW_PATTERN.search(rights_note)
                or (fair_use and len(rights_note) > 320)
                or (not fair_use and len(rights_note) > 320)
            ):
                folded = rights_note.casefold()
                if fair_use and media.get("assetPath"):
                    title = str(media.get("title") or media["id"])
                    media["rightsNote"] = (
                        "Reuse rights are not cleared. A reduced-resolution image is "
                        f"used for scholarly identification and commentary on {title}."
                    )
                elif fair_use:
                    media["rightsNote"] = (
                        "External media is linked for scholarly reference and is not "
                        "rehosted; reuse rights are not cleared."
                    )
                elif "gallica" in folded or "bibliothèque nationale de france" in folded:
                    media["rightsNote"] = (
                        "The digitized item is presented under the reuse terms of "
                        "Gallica / Bibliothèque nationale de France, with source attribution."
                    )
                elif "anno" in folded or "österreichische nationalbibliothek" in folded:
                    media["rightsNote"] = (
                        "The digitized item is reused in the accessible web resolution "
                        "under the terms of ANNO / Österreichische Nationalbibliothek, "
                        "with source attribution."
                    )
                elif "chronicling america" in folded:
                    media["rightsNote"] = (
                        "The newspaper issue is identified by Library of Congress / "
                        "Chronicling America as public-domain or no-known-restrictions "
                        "material; separately credited content remains distinct."
                    )
                elif (
                    "copyright renew" in folded
                    or "issue renewals" in folded
                    or "cce" in folded
                    or "cprs" in folded
                ):
                    media["rightsNote"] = (
                        "The periodical issue layer is treated as public domain in the "
                        "United States under the recorded renewal assessment; separately "
                        "registered photographs, artwork and syndicated contributions "
                        "remain distinct."
                    )
                elif "cc by-nc" in folded:
                    media["rightsNote"] = (
                        "Available under CC BY-NC; attribution and the licence’s "
                        "non-commercial-use condition apply."
                    )
                elif "cc by 4.0" in folded or "creative commons attribution 4.0" in folded:
                    media["rightsNote"] = (
                        "Available under CC BY 4.0; attribution to the credited creator "
                        "and source is required."
                    )
                elif "cc0" in folded:
                    media["rightsNote"] = (
                        "Released under CC0 by the linked source; institutional attribution "
                        "is retained."
                    )
                elif (
                    "public domain" in folded
                    or "public-domain" in folded
                    or "rights: “wygasły”" in folded
                    or "rights: \"wygasły\"" in folded
                ):
                    media["rightsNote"] = (
                        "The linked source identifies this item as public domain or "
                        "otherwise free of known copyright restrictions; attribution is retained."
                    )
                else:
                    media.pop("rightsNote", None)

            if media.get("rightsStatus") == "ok" and media.get("publicCreditLine"):
                credit_parts = [
                    part.strip()
                    for part in str(media["publicCreditLine"]).split(";")
                    if part.strip() and "not cleared" not in part.casefold()
                ]
                if credit_parts:
                    media["publicCreditLine"] = "; ".join(credit_parts).rstrip(".") + "."
                else:
                    media.pop("publicCreditLine", None)

            if media.get("publicCreditLine"):
                credit = str(media["publicCreditLine"])
                credit = re.sub(
                    r"reproduction/source route not cleared for reuse",
                    "reuse rights not cleared",
                    credit,
                    flags=re.IGNORECASE,
                )
                credit = re.sub(
                    r"public-domain source route",
                    "public-domain image",
                    credit,
                    flags=re.IGNORECASE,
                )
                credit = re.sub(
                    r"\bsource route\b",
                    "source",
                    credit,
                    flags=re.IGNORECASE,
                )
                credit = re.sub(
                    r"\.\s*Contextual\s+(?:low|reduced)-resolution\s+use\s+under\s+"
                    r"the project’s scholarly fair-use rationale\.?$",
                    ".",
                    credit,
                    flags=re.IGNORECASE,
                )
                media["publicCreditLine"] = credit

            for key in ("description", "publicCaption", "rightsNote", "publicCreditLine"):
                value = str(media.get(key, ""))
                if not value or not MEDIA_PUBLIC_IDENTIFIER_PATTERN.search(value):
                    continue
                if key == "description" and media.get("publicCaption"):
                    value = str(media["publicCaption"])
                value = re.sub(
                    r",?\s+with\s+[^.]*?\b(?:in|through)\s+SRC\d{4}",
                    "",
                    value,
                    flags=re.IGNORECASE,
                )
                value = re.sub(
                    r"\s*/\s*SRC\d{4}",
                    "",
                    value,
                    flags=re.IGNORECASE,
                )
                value = re.sub(
                    r"\s*\(\s*SRC\d{4}\s*\)",
                    "",
                    value,
                    flags=re.IGNORECASE,
                )
                value = MEDIA_PUBLIC_IDENTIFIER_PATTERN.sub("", value)
                value = re.sub(r"\s+([,.;:])", r"\1", value)
                value = re.sub(r"([/·])\s*([,.;:])", r"\2", value)
                value = re.sub(r"\s{2,}", " ", value).strip()
                media[key] = value

    def _normalize_source_public_text(self) -> None:
        """Keep source citations bibliographic rather than graph- or workflow-oriented."""
        for source in self.output_records["Sources"]:
            normalize_visual_source(source)
            if source.get("sourceType") == "authority_record":
                normalize_authority_source(source)
            if source.get("sourceType") == "recording_discographic_source":
                normalize_recording_source(source)
            if source.get("sourceType") == "filmographic_database" or source.get(
                "id"
            ) in {"SRC0174", "SRC0602"}:
                normalize_filmographic_source(source)
            original_full_citation = str(source.get("fullCitation", "")).strip()
            original_url = str(source.get("url", "")).strip()
            citation_urls: list[str] = []
            for key in ("fullCitation", "shortCitation"):
                citation = str(source.get(key, "")).strip()
                if not citation:
                    continue

                citation = re.sub(
                    r";\s*retained in this database with resolved .*?$",
                    ".",
                    citation,
                    flags=re.IGNORECASE,
                )
                citation = re.sub(
                    r"\s*Distinct clipping from SRC\d{4}\.?",
                    "",
                    citation,
                    flags=re.IGNORECASE,
                )
                for pattern in SOURCE_TRAILING_EDITORIAL_PATTERNS:
                    citation = pattern.sub("", citation)

                citation = re.sub(
                    r"\s+Source for [^.]*?(?:"
                    r"SRC\d{4}|W-[A-Z]\d{3}|M\d{3}|S\d{3}|F\d{3}|"
                    r"TV\d{4}|PNV\d{4}|CON-[A-Z0-9-]+)[^.]*\.?$",
                    "",
                    citation,
                    flags=re.IGNORECASE,
                )
                citation = re.sub(
                    r"\s+and linked to Work [^.]+\.?$",
                    "",
                    citation,
                    flags=re.IGNORECASE,
                )
                citation = re.sub(
                    r"\s*\((?:Media|Work|Song|Film)\s+"
                    r"(?:M\d{3}|W-[A-Z]\d{3}|S\d{3}|F\d{3})\)\.?$",
                    "",
                    citation,
                    flags=re.IGNORECASE,
                )
                citation = re.sub(
                    r"\s*,?\s*local asset\s+assets/\S+",
                    "",
                    citation,
                    flags=re.IGNORECASE,
                )
                citation = re.sub(
                    r";?\s*(?:StabiKat data|RIS export|item-level scans?) supplied "
                    r"by (?:the )?project owner(?: from boxes? [^.;]+)?",
                    "",
                    citation,
                    flags=re.IGNORECASE,
                )
                citation = re.sub(
                    r";?\s*(?:Data|Metadata) supplied by (?:the )?(?:user|project owner)"
                    r"(?: from [^.;]+)?",
                    "",
                    citation,
                    flags=re.IGNORECASE,
                )
                citation = re.sub(
                    r"\bsource record\b",
                    "source",
                    citation,
                    flags=re.IGNORECASE,
                )
                citation = re.sub(
                    r"\bAccessed and verified\b",
                    "Accessed",
                    citation,
                    flags=re.IGNORECASE,
                )
                citation = re.sub(
                    r"\bsource verified and accessed\b",
                    "Accessed",
                    citation,
                    flags=re.IGNORECASE,
                )
                citation = re.sub(
                    r"this specific book entry has not yet been directly checked",
                    "the cited book entry has not been directly consulted",
                    citation,
                    flags=re.IGNORECASE,
                )
                trailing_note = SOURCE_TRAILING_BRACKET_NOTE_PATTERN.search(citation)
                if trailing_note:
                    note = normalized_source_note(trailing_note.group(1))
                    citation = (
                        citation[: trailing_note.start()].rstrip(" .")
                        + ". "
                        + note
                    )
                citation = SOURCE_PUBLIC_IDENTIFIER_PATTERN.sub("", citation)
                citation = re.sub(r"assets/\S+", "", citation, flags=re.IGNORECASE)
                citation = re.sub(
                    r"\s*\((?:Media|Work|Song|Film)\s*\)\.?$",
                    "",
                    citation,
                    flags=re.IGNORECASE,
                )
                citation = re.sub(r"\s+([,.;:])", r"\1", citation)
                citation = re.sub(r"([/·])\s*([,.;:])", r"\2", citation)
                citation = re.sub(r"\s{2,}", " ", citation).strip()
                citation = re.sub(r"(?:,\s*){2,}", ", ", citation)
                citation = re.sub(
                    r",\s*including\.$",
                    ".",
                    citation,
                    flags=re.IGNORECASE,
                )
                citation = re.sub(
                    r"([.?!][”’\"']?)\.+$",
                    r"\1",
                    citation,
                )
                if key == "fullCitation":
                    citation_urls = source_urls(citation)
                    citation = citation_without_literal_urls(citation)
                citation = citation.rstrip(" ,;/")
                if (
                    key == "fullCitation"
                    and citation
                    and not re.search(r"""[.?!][”’"']?$""", citation)
                ):
                    citation += "."
                source[key] = citation

            if citation_urls:
                self.source_citation_stats["citationsWithLiteralUrls"] += 1
                self.source_citation_stats["literalUrlOccurrences"] += len(
                    citation_urls
                )
                if len(citation_urls) > 1:
                    self.source_citation_stats["multiUrlCitations"] += 1
                if original_url and original_url in original_full_citation:
                    self.source_citation_stats["exactUrlDuplicates"] += 1
                elif original_url:
                    original_host = urlparse(original_url).netloc.casefold()
                    citation_hosts = {
                        urlparse(url).netloc.casefold() for url in citation_urls
                    }
                    if original_host in citation_hosts:
                        self.source_citation_stats["sameHostDistinctUrls"] += 1
                    else:
                        self.source_citation_stats["crossHostDistinctUrls"] += 1

            unique_citation_urls = list(dict.fromkeys(citation_urls))
            doi_urls = [
                url
                for url in unique_citation_urls
                if urlparse(url).netloc.casefold() in {"doi.org", "dx.doi.org"}
            ]
            primary_url = ""
            if doi_urls:
                primary_url = doi_urls[0]
            elif unique_citation_urls:
                first_url = unique_citation_urls[0]
                first_ark = SOURCE_ARK_PATTERN.search(first_url)
                existing_ark = (
                    SOURCE_ARK_PATTERN.search(original_url) if original_url else None
                )
                if (
                    first_ark
                    and original_url
                    and existing_ark
                    and urlparse(first_url).netloc.casefold()
                    != urlparse(original_url).netloc.casefold()
                    and first_ark.group(1).casefold()
                    == existing_ark.group(1).casefold()
                ):
                    primary_url = original_url
                else:
                    primary_url = first_url
            elif original_url:
                primary_url = original_url

            if primary_url:
                source["primaryUrl"] = primary_url
                self.source_citation_stats["recordsWithPrimaryUrl"] += 1

            used_urls = {
                comparable_source_url(primary_url)
            } if primary_url else set()
            if (
                original_url
                and comparable_source_url(original_url) not in used_urls
            ):
                source["accessUrl"] = original_url
                used_urls.add(comparable_source_url(original_url))
                self.source_citation_stats["recordsWithAccessUrl"] += 1

            additional_links = []
            for url in unique_citation_urls:
                comparable = comparable_source_url(url)
                if comparable in used_urls:
                    continue
                label, role = source_link_label(url)
                additional_links.append(
                    {"label": label, "url": url, "role": role}
                )
                used_urls.add(comparable)
            if additional_links:
                source["additionalLinks"] = additional_links
                self.source_citation_stats["recordsWithAdditionalLinks"] += 1
                self.source_citation_stats["additionalLinkCount"] += len(
                    additional_links
                )

            identifiers = source_identifiers(original_full_citation)
            if identifiers:
                source["identifiers"] = identifiers
                self.source_citation_stats["recordsWithIdentifiers"] += 1

            structured_urls = {
                comparable_source_url(url)
                for url in (
                    source.get("primaryUrl"),
                    source.get("accessUrl"),
                    *(
                        link["url"]
                        for link in source.get("additionalLinks", [])
                    ),
                )
                if url
            }
            for citation_url in citation_urls:
                if comparable_source_url(citation_url) not in structured_urls:
                    self.errors.append(
                        f"Source {source['id']}: citation URL was not preserved in the structured link model"
                    )
            source.pop("url", None)

            repository = str(source.get("repository", "")).strip()
            repository = re.sub(
                r"\s*/\s*source data supplied by (?:the )?user$",
                "",
                repository,
                flags=re.IGNORECASE,
            )
            if repository.lower() == "kaper project media asset":
                repository = ""
            if repository:
                source["repository"] = repository
            else:
                source.pop("repository", None)

            date = str(source.get("date", "")).strip()
            date = re.sub(
                r";\s*source (?:record )?verified \d{4}-\d{2}-\d{2}$",
                "",
                date,
                flags=re.IGNORECASE,
            )
            date = re.sub(
                r";\s*historical recording date not established by this source(?: record)?$",
                "",
                date,
                flags=re.IGNORECASE,
            )
            if date:
                source["date"] = date
            else:
                source.pop("date", None)

            creator = str(source.get("creator", "")).strip()
            creator = re.sub(
                r"\s*;\s*exact image creator not separately identified in the source\.?$",
                "; exact image creator not identified",
                creator,
                flags=re.IGNORECASE,
            )
            creator = re.sub(
                r"\s*;\s*exact image creator not separately identified in the source record\.?$",
                "; exact image creator not identified",
                creator,
                flags=re.IGNORECASE,
            )
            if creator:
                source["creator"] = creator
            else:
                source.pop("creator", None)

    @staticmethod
    def _append(record: dict[str, Any], key: str, values: list[str]) -> None:
        if not values:
            return
        record[key] = sorted(set(record.get(key, [])) | set(values))

    def _derive_graph_indexes(self) -> None:
        output_by_id = {
            table: {record["id"]: record for record in records}
            for table, records in self.output_records.items()
        }

        for contribution in self.output_records["Contributions"]:
            work_ids = contribution.get("workIds", [])
            person_ids = contribution.get("personIds", [])
            organization_ids = contribution.get("organizationIds", [])
            if not work_ids:
                continue
            work = output_by_id["Works"].get(work_ids[0])
            if work:
                self._append(work, "personIds", person_ids)
                self._append(work, "organizationIds", organization_ids)
            for person_id in person_ids:
                person = output_by_id["People"].get(person_id)
                if person:
                    self._append(person, "workIds", work_ids)
            for organization_id in organization_ids:
                organization = output_by_id["Organizations"].get(organization_id)
                if organization:
                    self._append(organization, "workIds", work_ids)

        for relation in self.output_records["Work Relations"]:
            for work_id in relation.get("sourceWorkIds", []) + relation.get("targetWorkIds", []):
                work = output_by_id["Works"].get(work_id)
                if work:
                    self._append(work, "relationIds", [relation["id"]])

        subtype_targets = {
            "Films": "filmIds",
            "Songs": "songIds",
            "Other Works": "otherWorkIds",
        }
        for table_name, derived_key in subtype_targets.items():
            for subtype in self.output_records[table_name]:
                for work_id in subtype.get("workIds", []):
                    work = output_by_id["Works"].get(work_id)
                    if work:
                        self._append(work, derived_key, [subtype["id"]])

    def _normalize_periods(self) -> None:
        """Use one chronological period model throughout the public graph."""
        output_by_id = {
            table: {record["id"]: record for record in records}
            for table, records in self.output_records.items()
        }

        def set_periods(record: dict[str, Any], values: list[str]) -> None:
            periods = [
                key
                for key in PERIOD_ORDER
                if key in {normalized_period_key(value) for value in values}
            ]
            if not periods:
                fallback = normalized_period_key(record.get("period"))
                if fallback:
                    periods = [fallback]
            if not periods:
                return
            record["periods"] = periods
            record["period"] = periods[0]
            if "periodKey" in record:
                record["periodKey"] = periods[0]

        events = output_by_id["Timeline Events"]
        for event in events.values():
            event_id = event["id"]
            if event_id in WARSAW_1926_EVENT_IDS:
                periods = ["warsaw"]
            elif event_id in EUROPEAN_1926_EVENT_IDS:
                periods = ["european"]
            else:
                start_year = year_from_value(event.get("dateStart") or event.get("sortDate"))
                end_year = year_from_value(event.get("dateEnd")) or start_year
                periods = []
                if start_year is not None and end_year is not None:
                    if start_year <= 1926:
                        periods.append("warsaw")
                    if end_year >= 1927 and start_year <= 1934:
                        periods.append("european")
                    if end_year >= 1935:
                        periods.append("hollywood")
                if start_year == 1926 and end_year == 1926:
                    existing = normalized_period_key(
                        event.get("periodKey") or event.get("period")
                    )
                    periods = [existing or "warsaw"]
            set_periods(event, periods)

        works = output_by_id["Works"]
        for work in works.values():
            year = year_from_value(work.get("year"))
            periods: list[str] = []
            if year == 1926:
                linked_periods = {
                    period
                    for event_id in work.get("timelineEventIds", [])
                    for period in events.get(event_id, {}).get("periods", [])
                }
                periods = [
                    period
                    for period in PERIOD_ORDER
                    if period in linked_periods and period != "hollywood"
                ]
            elif year is not None:
                periods = [chronological_period_for_year(year)]
            set_periods(work, periods)

        subtype_tables = ("Films", "Songs", "Other Works")
        for table_name in subtype_tables:
            for record in output_by_id[table_name].values():
                linked_periods = [
                    period
                    for work_id in record.get("workIds", [])
                    for period in works.get(work_id, {}).get("periods", [])
                ]
                if not linked_periods:
                    year = year_from_value(record.get("year"))
                    linked_periods = (
                        [chronological_period_for_year(year)]
                        if year is not None
                        else []
                    )
                set_periods(record, linked_periods)

        media_records = output_by_id["Media"]
        for media in media_records.values():
            if media.get("mediaType") == "document_gallery":
                continue
            # A medium has one editorially defined historical context. Its many
            # graph links must not silently broaden that context: a 1927 score
            # may illustrate a 1925–1926 narrative event, and a later contextual
            # photograph may document an earlier phase. Ambiguous corrections
            # belong in the auditable overrides file, not in relation-union
            # heuristics.
            set_periods(media, [media.get("period")])

        for media in media_records.values():
            if media.get("mediaType") != "document_gallery":
                continue
            member_periods = [
                period
                for member_id in media.get("galleryMemberIds", [])
                for period in media_records.get(member_id, {}).get("periods", [])
            ]
            if not member_periods:
                member_periods = [
                    period
                    for event_id in media.get("timelineEventIds", [])
                    for period in events.get(event_id, {}).get("periods", [])
                ]
            set_periods(media, member_periods)

        for place in output_by_id["Places"].values():
            linked_periods = [
                period
                for event_id in place.get("timelineEventIds", [])
                for period in events.get(event_id, {}).get("periods", [])
            ]
            set_periods(place, linked_periods)

    def build_records(self) -> None:
        for table_name in TABLE_ORDER:
            records = [
                self.map_record(table_name, self.by_stable[table_name][stable_id])
                for stable_id in sorted(self.included[table_name])
            ]
            self.output_records[table_name] = records
        self._apply_exclusions()
        self._apply_overrides()
        self._apply_additions()
        self._normalize_media_public_text()
        self._normalize_source_public_text()
        self._derive_graph_indexes()
        self._normalize_periods()

    def _validate_required(self) -> None:
        for table_name, table_config in self.config["tables"].items():
            for record in self.output_records[table_name]:
                for key in table_config["required"]:
                    if is_empty(record.get(key)):
                        self.errors.append(
                            f"{table_name} {record.get('id')}: required public field {key!r} is empty"
                        )

    def _validate_public_keys(self) -> None:
        banned = [
            fragment.lower()
            for fragment in self.config.get("bannedPublicKeyFragments", [])
        ]
        for table_name, records in self.output_records.items():
            table_config = self.config["tables"][table_name]
            allowed = set(table_config["fields"]) | set(table_config["links"])
            allowed |= set(table_config.get("derivedFields", []))
            for record in records:
                unexpected = set(record) - allowed
                if unexpected:
                    self.errors.append(
                        f"{table_name} {record.get('id')}: non-allowlisted keys {sorted(unexpected)}"
                    )
                for key in record:
                    lowered = key.lower()
                    if any(fragment in lowered for fragment in banned):
                        self.errors.append(
                            f"{table_name} {record.get('id')}: banned public key {key!r}"
                        )

    def _validate_identity_and_slugs(self) -> None:
        for table_name, records in self.output_records.items():
            ids = [record.get("id") for record in records]
            if len(ids) != len(set(ids)):
                self.errors.append(f"{table_name}: duplicate public IDs")
            slugs = [record["slug"] for record in records if record.get("slug")]
            duplicates = [
                slug for slug, count in Counter(slugs).items() if count > 1
            ]
            if duplicates:
                self.errors.append(
                    f"{table_name}: duplicate public slugs {sorted(duplicates)}"
                )

    def _validate_links(self) -> None:
        ids_by_table = {
            table: {record["id"] for record in records}
            for table, records in self.output_records.items()
        }
        for table_name, table_config in self.config["tables"].items():
            for record in self.output_records[table_name]:
                for public_key, link_spec in table_config["links"].items():
                    target_ids = ids_by_table[link_spec["target"]]
                    for target in record.get(public_key, []):
                        if target not in target_ids:
                            self.errors.append(
                                f"{table_name} {record['id']}: dangling {public_key} target {target}"
                            )

    def _validate_scope(self) -> None:
        end_year = self.config["scope"]["endYear"]
        for work in self.output_records["Works"]:
            if work.get("year") and int(work["year"]) > end_year:
                self.errors.append(
                    f"Works {work['id']}: year {work['year']} exceeds public scope {end_year}"
                )

        period_tables = (
            "Works",
            "Films",
            "Songs",
            "Other Works",
            "Media",
            "Timeline Events",
            "Places",
        )
        for table_name in period_tables:
            for record in self.output_records[table_name]:
                periods = record.get("periods", [])
                invalid = [period for period in periods if period not in PERIOD_ORDER]
                if invalid:
                    self.errors.append(
                        f"{table_name} {record['id']}: invalid chronological periods {invalid}"
                    )
                if periods and record.get("period") != periods[0]:
                    self.errors.append(
                        f"{table_name} {record['id']}: primary period does not match periods"
                    )
                if normalized_period_key(record.get("period")) not in PERIOD_ORDER:
                    self.errors.append(
                        f"{table_name} {record['id']}: missing canonical chronological period"
                    )
        for event in self.output_records["Timeline Events"]:
            for key in ("dateStart", "dateEnd"):
                value = event.get(key)
                if value and int(str(value)[:4]) > end_year:
                    self.errors.append(
                        f"Timeline Events {event['id']}: {key} {value} exceeds public scope {end_year}"
                    )

    def _validate_media(self) -> None:
        media_by_id = {
            media["id"]: media for media in self.output_records["Media"]
        }
        sources_by_id = {
            source["id"]: source for source in self.output_records["Sources"]
        }
        for media in self.output_records["Media"]:
            media_id = media["id"]
            gallery = media.get("galleryStatus")
            external_url = media.get("externalUrl", "")
            sort_order = media.get("sortOrder")
            if isinstance(sort_order, bool) or not isinstance(sort_order, int):
                self.errors.append(
                    f"Media {media_id}: sortOrder must be an integer"
                )
            if external_url and re.search(r"[\r\n]", external_url):
                self.errors.append(
                    f"Media {media_id}: externalUrl contains more than one URL"
                )
            if media.get("mediaType") == "document_gallery" and external_url:
                self.errors.append(
                    f"Media {media_id}: a document-gallery container cannot carry "
                    "an item-level externalUrl"
                )
            if not media.get("sourceIds"):
                self.errors.append(f"Media {media_id}: public medium has no sourceIds")
            if (
                media.get("storageType") == "external"
                and media.get("mediaType") == "image"
                and gallery != "external_link_only"
            ):
                self.errors.append(
                    f"Media {media_id}: an externally hosted image without a local "
                    "asset must use galleryStatus external_link_only"
                )
            if gallery == "external_link_only":
                if not media.get("externalUrl"):
                    self.errors.append(f"Media {media_id}: external link card has no URL")
                if media.get("embedUrl"):
                    self.errors.append(f"Media {media_id}: external link card contains embedUrl")
            if media.get("storageType") == "local" and not media.get("assetPath"):
                self.errors.append(f"Media {media_id}: local media has no assetPath")
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
                if media.get("rightsStatus") != "external_content_not_rehosted":
                    self.errors.append(
                        f"Media {media_id}: external audio/video must use "
                        "rightsStatus external_content_not_rehosted"
                    )
                rights_note = str(media.get("rightsNote", "")).casefold()
                if "no local copy is hosted" not in rights_note:
                    self.errors.append(
                        f"Media {media_id}: external audio/video rights note must state "
                        "that no local copy is hosted"
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
                source_optional = media_id in set(
                    self.config.get("mediaExceptions", {}).get(
                        "sourceOptionalForExternalContextCards", []
                    )
                )
                required_keys = ["rightsNote", "publicCreditLine"]
                if not source_optional:
                    required_keys.append("sourceIds")
                for key in required_keys:
                    if is_empty(media.get(key)):
                        self.errors.append(
                            f"Media {media_id}: fair-use record lacks {key}"
                        )
                if media.get("storageType") == "local":
                    if not media.get("assetPath"):
                        self.errors.append(
                            f"Media {media_id}: local fair-use record lacks assetPath"
                        )
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
                            f"Media {media_id}: fair-use record does not document limited resolution"
                        )
            if media.get("mediaType") == "document_gallery":
                paths = media.get("assetPaths", [])
                member_ids = media.get("galleryMemberIds", [])
                if media.get("assetCount") != len(paths):
                    self.errors.append(
                        f"Media {media_id}: assetCount does not match assetPaths"
                    )
                if len(member_ids) != len(paths):
                    self.errors.append(
                        f"Media {media_id}: Gallery Members count does not match assetPaths"
                    )
                if len(set(member_ids)) != len(member_ids):
                    self.errors.append(
                        f"Media {media_id}: duplicate Gallery Members"
                    )
                if media_id in member_ids:
                    self.errors.append(
                        f"Media {media_id}: gallery links to itself"
                    )
                members = []
                for member_id in member_ids:
                    member = media_by_id.get(member_id)
                    if member is None:
                        self.errors.append(
                            f"Media {media_id}: missing gallery member {member_id}"
                        )
                        continue
                    if member.get("mediaType") == "document_gallery":
                        self.errors.append(
                            f"Media {media_id}: gallery member {member_id} is another document gallery"
                        )
                    members.append(member)
                for path in paths:
                    matches = [
                        member["id"]
                        for member in members
                        if path == member.get("assetPath")
                        or path in member.get("assetPaths", [])
                    ]
                    if len(matches) != 1:
                        self.errors.append(
                            f"Media {media_id}: asset path {path} matches {len(matches)} explicit gallery members"
                        )

    @staticmethod
    def _detect_media_type(path: Path) -> str | None:
        head = path.read_bytes()[:12]
        if head.startswith(b"\xff\xd8\xff"):
            return "jpeg"
        if head.startswith(b"\x89PNG\r\n\x1a\n"):
            return "png"
        if head[:3] == b"ID3" or (len(head) >= 2 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0):
            return "mp3"
        return None

    def _validate_assets(self) -> None:
        if self.assets_root is None:
            return
        seen: set[str] = set()
        for media in self.output_records["Media"]:
            paths = []
            if media.get("assetPath"):
                paths.append(media["assetPath"])
            paths.extend(media.get("assetPaths", []))
            for relative in paths:
                if relative in seen:
                    continue
                seen.add(relative)
                path = self.assets_root / relative
                if not path.is_file():
                    self.errors.append(f"Missing public asset: {relative}")
                    continue
                actual = self._detect_media_type(path)
                suffix = path.suffix.lower()
                expected = {
                    ".jpg": "jpeg",
                    ".jpeg": "jpeg",
                    ".png": "png",
                    ".mp3": "mp3",
                }.get(suffix)
                if actual and expected and actual != expected:
                    self.warnings.append(
                        {
                            "code": "asset_extension_mismatch",
                            "path": relative,
                            "extensionImplies": expected,
                            "contentIs": actual,
                        }
                    )
                if path.stat().st_size <= 20:
                    self.errors.append(f"Public asset is 0–20 bytes: {relative}")

    def _validate_no_private_urls(self) -> None:
        def walk(value: Any, context: str) -> None:
            if isinstance(value, str):
                host = urlparse(value).hostname or ""
                if host.casefold() in {
                    item.casefold()
                    for item in self.config.get("forbiddenRemoteAssetHosts", [])
                }:
                    self.errors.append(f"{context}: contains a forbidden temporary asset URL")
            elif isinstance(value, dict):
                for key, item in value.items():
                    walk(item, f"{context}.{key}")
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    walk(item, f"{context}[{index}]")

        for table_name, records in self.output_records.items():
            walk(records, table_name)

    def _validate_public_content(self) -> None:
        forbidden_phrases = [
            phrase.casefold()
            for phrase in self.config.get("forbiddenPublicContentPhrases", [])
        ]
        public_ids = {
            stable_id
            for table_ids in self.included.values()
            for stable_id in table_ids
        }
        known_ids = {
            stable_id
            for table_records in self.by_stable.values()
            for stable_id in table_records
        }
        excluded_ids = known_ids - public_ids
        identifier_pattern = re.compile(
            r"(?<![A-Za-z0-9-])(?:"
            + "|".join(
                re.escape(stable_id)
                for stable_id in sorted(known_ids, key=lambda item: (-len(item), item))
            )
            + r")(?![A-Za-z0-9-])"
        )

        def walk(value: Any, context: str) -> None:
            if isinstance(value, str):
                folded = value.casefold()
                for phrase in forbidden_phrases:
                    if phrase in folded:
                        self.errors.append(
                            f"{context}: contains forbidden workflow phrase {phrase!r}"
                        )
                for match in identifier_pattern.finditer(value):
                    if match.group(0) in excluded_ids:
                        self.errors.append(
                            f"{context}: mentions non-public record {match.group(0)}"
                        )
            elif isinstance(value, dict):
                for key, item in value.items():
                    walk(item, f"{context}.{key}")
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    walk(item, f"{context}[{index}]")

        for table_name, records in self.output_records.items():
            walk(records, table_name)

        for table_name, fields in PUBLIC_NARRATIVE_FIELDS.items():
            for record in self.output_records.get(table_name, []):
                record_id = record.get("id", "unknown")
                for field_name in fields:
                    value = record.get(field_name)
                    if isinstance(value, str) and PUBLIC_EDITORIAL_NARRATOR_PATTERN.search(value):
                        self.errors.append(
                            f"{table_name} {record_id}: public field {field_name} "
                            "contains context-dependent editorial narration"
                        )

        for source in self.output_records["Sources"]:
            source_id = source["id"]
            for organization_id in expected_repository_organization_ids(source):
                if organization_id not in (source.get("organizationIds") or []):
                    self.errors.append(
                        f"Source {source_id}: repository field requires organization "
                        f"relation {organization_id}"
                    )
            research_note = str(source.get("researchNote", "")).strip()
            research_note_type = str(source.get("researchNoteType", "")).strip()
            if bool(research_note) != bool(research_note_type):
                self.errors.append(
                    f"Source {source_id}: researchNote and researchNoteType must be supplied together"
                )
            if research_note_type and research_note_type not in SOURCE_RESEARCH_NOTE_TYPES:
                self.errors.append(
                    f"Source {source_id}: unsupported researchNoteType {research_note_type!r}"
                )

            for key in ("fullCitation", "shortCitation", "researchNote"):
                value = str(source.get(key, ""))
                if SOURCE_PUBLIC_IDENTIFIER_PATTERN.search(value):
                    self.errors.append(
                        f"Source {source_id}: public field {key} contains a technical record identifier"
                    )
                if re.search(
                    r"assets/|\blocal asset\b|\bsource record\b|"
                    r"\bproject (?:owner|media asset)\b|"
                    r"\bretained in this database\b|\b(?:data|metadata) supplied "
                    r"(?:by (?:the )?(?:user|project)|from)\b|"
                    r"\bRIS export supplied by (?:the )?project\b|"
                    r"\bsource (?:used )?for (?:media|work|song)\b|\bused in Media\b|"
                    r"\breferenced as a (?:listening|viewing/listening) source\b|"
                    r"\blistening/viewing source for\b|\bdistinct clipping from\b",
                    value,
                    flags=re.IGNORECASE,
                ):
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
                    if scheme not in {"doi", "ark", "naid"} or not value:
                        self.errors.append(
                            f"Source {source_id}: identifiers[{index}] has an unsupported scheme or empty value"
                        )
                    key = (scheme, value.casefold())
                    if key in seen_identifiers:
                        self.errors.append(
                            f"Source {source_id}: identifiers contain duplicates"
                        )
                    seen_identifiers.add(key)

    def validate(self) -> None:
        self._validate_required()
        self._validate_public_keys()
        self._validate_identity_and_slugs()
        self._validate_links()
        self._validate_scope()
        self._validate_media()
        self._validate_assets()
        self._validate_no_private_urls()
        self._validate_public_content()

    def _table_payload(self, table_name: str) -> dict[str, Any]:
        return {
            "schemaVersion": self.config["schemaVersion"],
            "scope": self.config["scope"],
            "count": len(self.output_records[table_name]),
            "records": self.output_records[table_name],
        }

    def _write_export(self, temp_root: Path) -> None:
        for table_name in TABLE_ORDER:
            filename = self.config["tables"][table_name]["file"]
            write_json(temp_root / filename, self._table_payload(table_name))

        gallery_counts = Counter(
            item["galleryStatus"] for item in self.output_records["Media"]
        )
        report = {
            "ok": not self.errors,
            "errors": self.errors,
            "warnings": sorted(
                self.warnings,
                key=lambda item: (item.get("code", ""), item.get("path", "")),
            ),
            "counts": {
                table_name: len(records)
                for table_name, records in self.output_records.items()
            },
            "galleryStatusCounts": dict(sorted(gallery_counts.items())),
            "sourceCitationNormalization": dict(
                sorted(self.source_citation_stats.items())
            ),
            "appliedOverrides": sorted(
                self.applied_overrides,
                key=lambda item: (item["table"], item["id"]),
            ),
            "appliedExclusions": sorted(
                self.applied_exclusions,
                key=lambda item: (item["table"], item["id"]),
            ),
            "appliedAdditions": sorted(
                self.applied_additions,
                key=lambda item: (item["table"], item["id"]),
            ),
            "appliedLinkAdditions": sorted(
                self.applied_link_additions,
                key=lambda item: (item["table"], item["id"]),
            ),
            "appliedLinkRemovals": sorted(
                self.applied_link_removals,
                key=lambda item: (item["table"], item["id"]),
            ),
            "allowlist": {
                table_name: {
                    "sourceFieldsAvailable": len(
                        next(
                            table["fields"]
                            for table in self.schema["tables"]
                            if table["name"] == table_name
                        )
                    ),
                    "publicScalarFields": len(table_config["fields"]),
                    "publicLinkFields": len(table_config["links"]),
                    "derivedFields": len(table_config.get("derivedFields", [])),
                }
                for table_name, table_config in self.config["tables"].items()
            },
        }
        write_json(temp_root / "build-report.json", report)

        file_entries = []
        for path in sorted(temp_root.glob("*.json")):
            if path.name == "manifest.json":
                continue
            file_entries.append(
                {
                    "file": path.name,
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
        manifest = {
            "schemaVersion": self.config["schemaVersion"],
            "scope": self.config["scope"],
            "publicDataUpdatedAt": self.database_index["exportedAt"],
            "generator": {
                "file": Path(__file__).name,
                "sha256": sha256(Path(__file__).resolve()),
            },
            "publicInputs": {
                "allowlist": {
                    "file": self.config_path.name,
                    "sha256": sha256(self.config_path),
                },
                "overrides": (
                    {
                        "file": self.overrides_path.name,
                        "sha256": sha256(self.overrides_path),
                        "appliedCount": len(self.applied_overrides),
                        "additionCount": len(self.applied_additions),
                        "linkAdditionCount": len(self.applied_link_additions),
                        "linkRemovalCount": len(self.applied_link_removals),
                    }
                    if self.overrides_path is not None
                    else None
                ),
            },
            "exportPolicy": {
                "editorialStatus": self.config["allowedEditorialStatus"],
                "workScopes": self.config["allowedWorkScopes"],
                "placeScopes": self.config["allowedPlaceScopes"],
                "galleryStatuses": self.config["allowedGalleryStatuses"],
                "sources": "approved and reachable from the public graph",
                "authorities": "approved and reachable from the public graph",
                "legacyAndInternalFields": "excluded by explicit allowlist",
            },
            "counts": {
                table_name: len(records)
                for table_name, records in self.output_records.items()
            },
            "files": file_entries,
        }
        write_json(temp_root / "manifest.json", manifest)

    def run(self) -> dict[str, Any]:
        self.select_public_graph()
        self.build_records()
        self.validate()

        self.output_root.parent.mkdir(parents=True, exist_ok=True)
        temp_root = Path(
            tempfile.mkdtemp(
                prefix=".public-export-",
                dir=str(self.output_root.parent),
            )
        )
        self._write_export(temp_root)
        if self.errors:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "errors": self.errors,
                        "warnings": self.warnings,
                        "temporaryOutput": str(temp_root),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return {"ok": False, "temporaryOutput": str(temp_root)}

        if self.output_root.exists():
            shutil.rmtree(self.output_root)
        temp_root.replace(self.output_root)
        result = {
            "ok": True,
            "output": str(self.output_root),
            "counts": {
                table_name: len(records)
                for table_name, records in self.output_records.items()
            },
            "warnings": self.warnings,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backup",
        required=True,
        type=Path,
        help="Compatible private source-package directory",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Versioned public JSON output directory",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("public_export_config.json"),
        help="Explicit public field allowlist",
    )
    parser.add_argument(
        "--assets-root",
        type=Path,
        help="Repository root used to verify exported local asset paths",
    )
    parser.add_argument(
        "--overrides",
        type=Path,
        default=Path(__file__).with_name("public_export_overrides.json"),
        help="Auditable corrections and additions for the public graph",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    exporter = PublicExporter(
        backup_root=args.backup,
        config_path=args.config,
        overrides_path=args.overrides,
        output_root=args.output,
        assets_root=args.assets_root,
    )
    result = exporter.run()
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
