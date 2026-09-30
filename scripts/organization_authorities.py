#!/usr/bin/env python3
"""Normalize authority control and contextual links for Organizations.

People were given this separation when the person card was written.
Organizations never were, and it showed in the data: twenty-six institutional
homepages, a cooperation agreement, a digital-library platform and a finding
aid sat in the authority field beside LCNAF and GND identifiers, and the same
Library of Congress provider register arrived under two different labels while
the Polish national library arrived under a third.  One register cannot be two
registers because a label was typed twice, so the scheme is read from the URL
here exactly as it is for People.

An organization's contextual links keep the label they were given, because
those labels say what the page is — an official website, a finding aid — and
that is not derivable from the host the way ``Wikipedia`` or ``Filmportal`` is
for a person.
"""

from __future__ import annotations

from authority_identifiers import (
    parse_link_stack,
    split_authority_links,
    structured_link_errors,
)


# The heading source is prose describing where a name was transcribed from, not
# an identifier, so it stays free text.  It may still name a register, and when
# it does it has to use that register's one spelling.
HEADING_SOURCE_ALIASES = {
    "library of congress providers": "LC Providers",
    "lc providers": "LC Providers",
    "biblioteka narodowa": "BN",
    "local": "local heading",
}

REFERENCE_LABEL_ALIASES = {
    "website": "Official website",
    "official site": "Official website",
}


def reference_label(label: str, url: str) -> str:
    cleaned = label.strip()
    return REFERENCE_LABEL_ALIASES.get(cleaned.casefold(), cleaned)


def _parsed_organization_links(organization: dict) -> list[tuple[str, str]]:
    """Read both structured lists and the legacy stacks they replaced."""

    parsed = parse_link_stack(organization.get("authorities"))
    parsed.extend(parse_link_stack(organization.get("references")))
    parsed.extend(parse_link_stack(organization.get("authorityUrl")))
    parsed.extend(parse_link_stack(organization.get("referenceUrl")))
    return parsed


def normalize_organization_authority_fields(organization: dict) -> None:
    """Normalize and separate one public Organization record in place."""

    authorities, references = split_authority_links(
        _parsed_organization_links(organization),
        reference_label=reference_label,
    )

    organization.pop("authorityUrl", None)
    organization.pop("referenceUrl", None)
    if authorities:
        organization["authorities"] = authorities
    else:
        organization.pop("authorities", None)
    if references:
        organization["references"] = references
    else:
        organization.pop("references", None)

    heading_source = str(organization.get("authorizedNameSource") or "").strip()
    heading_source = HEADING_SOURCE_ALIASES.get(
        heading_source.casefold(), heading_source
    )
    if heading_source:
        organization["authorizedNameSource"] = heading_source
    else:
        organization.pop("authorizedNameSource", None)


def normalize_organization_authorities(organizations: list[dict]) -> None:
    for organization in organizations:
        normalize_organization_authority_fields(organization)


def organization_authority_errors(organization: dict) -> list[str]:
    """Return normalization/schema errors for one public Organization."""

    expected = dict(organization)
    normalize_organization_authority_fields(expected)
    errors: list[str] = []
    for field in ("authorities", "references", "authorizedNameSource"):
        if organization.get(field) != expected.get(field):
            errors.append(f"{field} is not normalized")
    for legacy in ("authorityUrl", "referenceUrl"):
        if organization.get(legacy) is not None:
            errors.append(f"{legacy} is the legacy packed form and must not be exported")
    errors.extend(
        structured_link_errors(
            organization, "authorities", key="scheme", controlled=True
        )
    )
    errors.extend(
        structured_link_errors(
            organization, "references", key="label", controlled=False
        )
    )
    return errors
