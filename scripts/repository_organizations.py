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
    ("ORG063", ("biblioteka narodowa", "polona")),
    ("ORG066", ("library of congress", "lcnaf")),
    ("ORG164", ("billy rose theatre division", "new york public library for the performing arts")),
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

# Individually audited creator relation, distinct from the digital repository.
AUDITED_SOURCE_INSTITUTION_IDS = {"SRC0689": ("ORG068",)}


def expected_repository_organization_ids(
    source: Mapping[str, Any],
) -> tuple[str, ...]:
    """Return named repository IDs and explicitly audited institutional IDs.

    Matching is deliberately limited to the structured repository field and a
    small curated vocabulary. Citation prose and URLs are not searched, so a
    passing mention of an access platform cannot create a semantic graph edge.
    Audited exceptions can additionally require a documented institutional
    creator without mislabelling that creator as the digital repository.
    """

    repository = " ".join(str(source.get("repository", "")).casefold().split())
    repository_ids = tuple(
        organization_id
        for organization_id, markers in REPOSITORY_ORGANIZATION_MARKERS
        if any(marker in repository for marker in markers)
    )
    return tuple(dict.fromkeys(repository_ids + AUDITED_SOURCE_INSTITUTION_IDS.get(str(source.get("id", "")), ())))
