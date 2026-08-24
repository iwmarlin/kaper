"""Semantic organization rules for external listening references.

Work-level organizations describe the composition or film (for example a
sheet-music publisher).  An external audio medium describes one particular
recording or issue.  Its organization links therefore come only from the
sources attached to that medium and are limited to recording labels and
performing ensembles.  A record company or manufacturer is admitted only when
a source-specific contribution states that role explicitly.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


RECORDING_CONTRIBUTION_ROLES = {
    "manufacturer",
    "performer",
    "record_company",
    "record_label",
}


def is_recording_label_or_ensemble(organization: Mapping[str, Any]) -> bool:
    types = set(organization.get("types") or [])
    return "record_label" in types or "ensemble" in types


def expected_audio_organization_ids(
    media: Mapping[str, Any],
    *,
    sources_by_id: Mapping[str, Mapping[str, Any]],
    organizations_by_id: Mapping[str, Mapping[str, Any]],
    contributions: Iterable[Mapping[str, Any]] = (),
) -> list[str]:
    """Return organizations evidenced for this exact external recording.

    Repository and access-platform organizations stay on Sources.  Publishers
    and production companies stay on Works.  This function intentionally does
    not inspect ``media.workIds`` and therefore cannot inherit organizations
    from the abstract work.
    """

    source_ids = set(media.get("sourceIds") or [])
    source_organization_ids = {
        organization_id
        for source_id in source_ids
        for organization_id in (
            sources_by_id.get(source_id, {}).get("organizationIds") or []
        )
    }

    expected = {
        organization_id
        for organization_id in source_organization_ids
        if organization_id in organizations_by_id
        and is_recording_label_or_ensemble(organizations_by_id[organization_id])
    }

    # Corporate manufacturing bodies are not inferred merely because a Source
    # mentions them.  They require a source-specific, typed contribution.
    for contribution in contributions:
        if not source_ids.intersection(contribution.get("sourceIds") or []):
            continue
        if contribution.get("role") not in RECORDING_CONTRIBUTION_ROLES:
            continue
        for organization_id in contribution.get("organizationIds") or []:
            organization = organizations_by_id.get(organization_id)
            if not organization:
                continue
            if (
                is_recording_label_or_ensemble(organization)
                or contribution.get("role") in {"manufacturer", "record_company"}
            ):
                expected.add(organization_id)

    return sorted(expected)

