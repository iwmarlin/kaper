#!/usr/bin/env python3
"""Create a deterministic, public-only JSON export from the private Airtable backup."""

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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
        self.applied_additions: list[dict[str, Any]] = []
        self.applied_link_additions: list[dict[str, Any]] = []
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
                if not stable_id:
                    self.errors.append(f"{table_name}: record {record['airtableRecordId']} has no stable ID")
                    continue
                if stable_id in self.by_stable[table_name]:
                    self.errors.append(f"{table_name}: duplicate stable ID {stable_id}")
                self.by_stable[table_name][stable_id] = record
                airtable_id = record["airtableRecordId"]
                if airtable_id in self.stable_by_record_id:
                    self.errors.append(f"Duplicate Airtable record ID {airtable_id}")
                self.stable_by_record_id[airtable_id] = stable_id
                self.table_by_record_id[airtable_id] = table_name
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
                    f"{record.get('stableId')}: unresolved Airtable link {link['id']} in {field_name!r}"
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

        for stable_id, record in self.by_stable["Media"].items():
            gallery = selected_name(self.fields(record).get("Gallery Status"))
            if self.approved("Media", record) and gallery in self.config["allowedGalleryStatuses"]:
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

        for stable_id, record in self.by_stable["Contributions"].items():
            fields = self.fields(record)
            if (
                self.approved("Contributions", record)
                and fields.get("Publishable") is True
                and selected_name(fields.get("Validation Status")) == "OK"
                and self.links_any(record, "Work", self.included["Works"])
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
        approved_people = self._approved_ids("People")
        approved_organizations = self._approved_ids("Organizations")
        approved_sources = self._approved_ids("Sources")

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

    def build_records(self) -> None:
        for table_name in TABLE_ORDER:
            records = [
                self.map_record(table_name, self.by_stable[table_name][stable_id])
                for stable_id in sorted(self.included[table_name])
            ]
            self.output_records[table_name] = records
        self._apply_overrides()
        self._apply_additions()
        self._derive_graph_indexes()

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
        for media in self.output_records["Media"]:
            media_id = media["id"]
            gallery = media.get("galleryStatus")
            external_url = media.get("externalUrl", "")
            if external_url and re.search(r"[\r\n]", external_url):
                self.errors.append(
                    f"Media {media_id}: externalUrl contains more than one URL"
                )
            if not media.get("sourceIds"):
                self.errors.append(f"Media {media_id}: public medium has no sourceIds")
            if gallery == "external_link_only":
                if not media.get("externalUrl"):
                    self.errors.append(f"Media {media_id}: external link card has no URL")
                if media.get("embedUrl"):
                    self.errors.append(f"Media {media_id}: external link card contains embedUrl")
            if media.get("storageType") == "local" and not media.get("assetPath"):
                self.errors.append(f"Media {media_id}: local media has no assetPath")
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
                if "airtableusercontent.com" in value.lower():
                    self.errors.append(
                        f"{context}: contains an expiring Airtable attachment URL"
                    )
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
            "appliedOverrides": sorted(
                self.applied_overrides,
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
            "sourceSnapshot": self.database_index["exportedAt"],
            "sourceRecordCount": self.database_index["totalRecordCount"],
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
        help="Private Airtable backup directory",
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
        help="Auditable public-text overrides for the frozen source snapshot",
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
