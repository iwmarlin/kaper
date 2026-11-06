#!/usr/bin/env python3
"""Normalize record companies, labels and external-audio organization links.

This maintenance command is deliberately narrow.  It separates the corporate
body Carl Lindström AG from its Odeon and Parlophone labels, then recalculates
organization links for external audio media from the sources describing each
exact recording.  It never changes video or image media.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from recording_organizations import expected_audio_organization_ids


PARLOPHONE = "ORG146"
ODEON = "ORG150"
LINDSTROM = "ORG128"
AFFECTED_ORGANIZATIONS = {LINDSTROM, PARLOPHONE, ODEON}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload: dict[str, Any]) -> None:
    if "count" in payload:
        payload["count"] = len(payload.get("records", []))
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def target_label(text: str) -> str | None:
    folded = text.casefold()
    if "parlophon" in folded:
        return PARLOPHONE
    if "odeon" in folded:
        return ODEON
    return None


def replace(values: list[str] | None, old: str, new: str) -> list[str]:
    return sorted({new if value == old else value for value in values or []})


def normalize(data_root: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    names = ("organizations", "sources", "contributions", "works", "songs", "media")
    tables = {name: load(data_root / f"{name}.json") for name in names}
    changes: list[str] = []

    sources = tables["sources"]["records"]
    contributions = tables["contributions"]["records"]
    works = tables["works"]["records"]
    songs = tables["songs"]["records"]
    media_records = tables["media"]["records"]
    organizations = tables["organizations"]["records"]

    # Source records name the exact imprint in their citation.  A source that
    # discusses Otto Dobrindt's corporate affiliation (SRC0720) correctly
    # remains linked to Carl Lindström AG.
    for source in sources:
        if LINDSTROM not in (source.get("organizationIds") or []):
            continue
        if source.get("id") == "SRC0720":
            continue
        evidence = " ".join(
            str(source.get(field) or "")
            for field in ("publication", "shortCitation", "title")
        )
        target = target_label(evidence)
        if not target:
            continue
        source["organizationIds"] = replace(
            source.get("organizationIds"), LINDSTROM, target
        )
        changes.append(f"Source {source['id']}: {LINDSTROM} -> {target}")

    # Stable contribution IDs are retained; their endpoint is corrected from
    # the parent company to the label actually printed on the disc.
    contribution_targets: dict[str, str] = {}
    for contribution in contributions:
        if contribution.get("role") != "record_label":
            continue
        if LINDSTROM not in (contribution.get("organizationIds") or []):
            continue
        target = target_label(str(contribution.get("nameAsPrinted") or ""))
        if not target:
            continue
        contribution["organizationIds"] = replace(
            contribution.get("organizationIds"), LINDSTROM, target
        )
        contribution_targets[contribution["id"]] = target
        changes.append(f"Contribution {contribution['id']}: {LINDSTROM} -> {target}")

    # Work and Song organizationIds are denormalized public navigation fields.
    # Replace only the Lindström endpoint supported by the corrected label
    # contribution; unrelated organization links remain untouched.
    targets_by_work: dict[str, set[str]] = {}
    for contribution in contributions:
        target = contribution_targets.get(contribution["id"])
        if not target:
            continue
        for work_id in contribution.get("workIds") or []:
            targets_by_work.setdefault(work_id, set()).add(target)

    for records in (works, songs):
        for record in records:
            work_ids = {record.get("id"), *(record.get("workIds") or [])}
            targets = set().union(
                *(targets_by_work.get(work_id, set()) for work_id in work_ids)
            )
            if not targets or LINDSTROM not in (record.get("organizationIds") or []):
                continue
            organization_ids = set(record.get("organizationIds") or [])
            organization_ids.discard(LINDSTROM)
            organization_ids.update(targets)
            record["organizationIds"] = sorted(organization_ids)
            changes.append(
                f"{record['id']}: {LINDSTROM} -> {', '.join(sorted(targets))}"
            )

    sources_by_id = {record["id"]: record for record in sources}
    organizations_by_id = {record["id"]: record for record in organizations}
    for media in media_records:
        if not (
            media.get("storageType") == "external"
            and media.get("mediaType") == "audio"
        ):
            continue
        expected = expected_audio_organization_ids(
            media,
            sources_by_id=sources_by_id,
            organizations_by_id=organizations_by_id,
            contributions=contributions,
        )
        current = sorted(set(media.get("organizationIds") or []))
        if current == expected:
            continue
        if expected:
            media["organizationIds"] = expected
        else:
            media.pop("organizationIds", None)
        changes.append(
            f"Media {media['id']}: {current or '[]'} -> {expected or '[]'}"
        )

    # Rebuild backlinks only for the three identities changed here.
    works_by_organization = {
        organization_id: sorted(
            record["id"]
            for record in works
            if organization_id in (record.get("organizationIds") or [])
        )
        for organization_id in AFFECTED_ORGANIZATIONS
    }
    sources_by_organization = {
        organization_id: sorted(
            record["id"]
            for record in sources
            if organization_id in (record.get("organizationIds") or [])
        )
        for organization_id in AFFECTED_ORGANIZATIONS
    }
    contributions_by_organization = {
        organization_id: sorted(
            record["id"]
            for record in contributions
            if organization_id in (record.get("organizationIds") or [])
        )
        for organization_id in AFFECTED_ORGANIZATIONS
    }
    for organization in organizations:
        organization_id = organization["id"]
        if organization_id not in AFFECTED_ORGANIZATIONS:
            continue
        for field, values in (
            ("workIds", works_by_organization[organization_id]),
            ("sourceIds", sources_by_organization[organization_id]),
            ("contributionIds", contributions_by_organization[organization_id]),
        ):
            if values:
                organization[field] = values
            else:
                organization.pop(field, None)

    return tables, changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/public/v1"),
        help="canonical public data directory",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift without changing files",
    )
    args = parser.parse_args()

    tables, changes = normalize(args.data)
    if args.check:
        for change in changes:
            print(change)
        return 1 if changes else 0

    for name, payload in tables.items():
        write(args.data / f"{name}.json", payload)
    for change in changes:
        print(change)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
