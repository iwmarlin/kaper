"""Controlled repository-name to Organization relations for public Sources.

URL-based normalizers cover records whose primary address belongs to the
repository itself. Some records instead link to an object page, delivery
platform, or partner catalogue while naming the responsible repository in the
structured ``repository`` field. These narrow rules make that curated statement
enforceable without fuzzy institution matching or new Organization records.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


REPOSITORY_ORGANIZATION_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "ORG080",
        (
            "university of southern california",
            "usc digital library",
            "usc libraries",
        ),
    ),
    (
        "ORG062",
        (
            "bibliothèque nationale de france",
            "bnf",
            "gallica",
            "retronews",
        ),
    ),
    (
        "ORG074",
        (
            "deutsche nationalbibliothek",
            "dnb",
        ),
    ),
    (
        "ORG067",
        (
            "internet archive",
            "archive.org",
        ),
    ),
    (
        "ORG158",
        (
            "world radio history",
            "worldradiohistory",
        ),
    ),
    (
        "ORG093",
        (
            "youtube",
        ),
    ),
    (
        "ORG085",
        (
            "société des auteurs, compositeurs et éditeurs de musique",
            "sacem",
        ),
    ),
)


def expected_repository_organization_ids(
    source: Mapping[str, Any],
) -> tuple[str, ...]:
    """Return existing Organization IDs named by ``source.repository``.

    Matching is deliberately limited to the structured repository field and a
    small curated vocabulary. Citation prose and URLs are not searched, so a
    passing mention of an access platform cannot create a semantic graph edge.
    """

    repository = " ".join(str(source.get("repository", "")).casefold().split())
    if not repository:
        return ()
    return tuple(
        organization_id
        for organization_id, markers in REPOSITORY_ORGANIZATION_MARKERS
        if any(marker in repository for marker in markers)
    )
