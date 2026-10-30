#!/usr/bin/env python3
"""Normalize authority control and contextual identity links for People.

The source package stores every person-related URL in one newline-delimited
``authorityUrl`` field.  That field contains both formal authority identifiers
(VIAF, LCNAF, GND, BnF, etc.) and contextual pages such as Wikipedia,
Filmportal or an archival collection.  Public data separates the two
semantics, and holds each as a structured list rather than a packed string:

``authorities``
    ``[{"scheme": …, "url": …}]`` — formal authority and identity registers
    only, in the precedence order of :mod:`authority_identifiers`.

``references``
    ``[{"label": …, "url": …}]`` — biographical, archival and filmographic
    reference pages.

A person-specific authority Source may also supply a formal identifier.  Such
an identifier is copied to the person's authority list only when the Source
asserts the accepted identity.  Candidate identities and separately
controlled pseudonyms remain citations, not assertions about the main person.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from authority_identifiers import (
    authority_scheme_for_url,
    authority_urls,
    clean_url,
    equivalent_authority_url,
    parse_link_stack,
    split_authority_links,
    structured_link_errors,
)


REFERENCE_LABEL_BY_HOST = {
    "catalog.afi.com": "AFI Catalog",
    "chopin.nifc.pl": "Fryderyk Chopin Institute",
    "collections.arolsen-archives.org": "Arolsen Archives",
    "commons.wikimedia.org": "Wikimedia Commons",
    "en.wikipedia.org": "Wikipedia",
    "www.deutsche-digitale-bibliothek.de": "Deutsche Digitale Bibliothek",
    "www.discogs.com": "Discogs",
    "www.filmportal.de": "Filmportal",
    "www.lexm.uni-hamburg.de": "LexM",
    "www.scharwenka-stiftung.de": "LexM",
}

REFERENCE_LABEL_ALIASES = {
    "afi": "AFI Catalog",
    "nifc": "Fryderyk Chopin Institute",
    "öml": "Austrian Music Lexicon (ÖML)",
    "wreed en plezant pseudonyms list": "Wreed en Plezant pseudonyms list",
}

# VIAF aggregates headings supplied by other agencies; it is not itself the
# register from which an authorized heading may be transcribed.  Two thinly
# documented records have no identifiable contributing register and therefore
# keep an explicitly local heading.  Ferry van Delden is the documented
# exception: the Dutch NTA form is visible through the VIAF cluster.
HEADING_SOURCE_OVERRIDES = {
    "P004": "local heading",
    "P014": "local heading",
    "P096": "Dutch National Thesaurus (NTA), via VIAF cluster",
    "P139": "LCNAF",
}

# This Wikidata item merges Marcella Halicz with a German screen actress.  The
# linked BN evidence explicitly rejects that identification, so it must not be
# exposed as an accepted identity identifier.
REJECTED_AUTHORITY_URLS = {
    "P156": {"https://www.wikidata.org/wiki/Q95678216"},
}


def reference_label(label: str, url: str) -> str:
    host = (urlsplit(url).hostname or "").casefold()
    if host in REFERENCE_LABEL_BY_HOST:
        return REFERENCE_LABEL_BY_HOST[host]
    return REFERENCE_LABEL_ALIASES.get(label.casefold(), label.strip())


def _parsed_person_links(person: dict) -> list[tuple[str, str]]:
    """Read both structured lists and the legacy stacks they replaced."""

    parsed = parse_link_stack(person.get("authorities"))
    parsed.extend(parse_link_stack(person.get("references")))
    parsed.extend(parse_link_stack(person.get("authorityUrl")))
    parsed.extend(parse_link_stack(person.get("referenceUrl")))
    return parsed


def normalize_person_authority_fields(person: dict) -> None:
    """Normalize and separate one public Person record in place."""

    authorities, references = split_authority_links(
        _parsed_person_links(person),
        reference_label=reference_label,
        rejected_urls=REJECTED_AUTHORITY_URLS.get(str(person.get("id") or ""), set()),
    )

    person.pop("authorityUrl", None)
    person.pop("referenceUrl", None)
    if authorities:
        person["authorities"] = authorities
    else:
        person.pop("authorities", None)
    if references:
        person["references"] = references
    else:
        person.pop("references", None)

    heading_source = HEADING_SOURCE_OVERRIDES.get(
        str(person.get("id") or ""),
        str(person.get("authorizedNameSource") or "").strip(),
    )
    if heading_source:
        person["authorizedNameSource"] = heading_source
    else:
        person.pop("authorizedNameSource", None)


def source_asserts_same_person(source: dict) -> bool:
    return (
        source.get("sourceType") == "authority_record"
        and source.get("authoritySubject") == "person"
        and source.get("identityRelation") == "same"
    )


def person_reference_urls(person: dict) -> list[str]:
    return [
        str(entry.get("url"))
        for entry in person.get("references") or []
        if entry.get("url")
    ]


def synchronize_person_authority_sources(
    people: list[dict],
    sources: list[dict],
) -> None:
    """Expose accepted person-authority Source identifiers in the fact block."""

    people_by_id = {person["id"]: person for person in people}
    for source in sources:
        if not source_asserts_same_person(source):
            continue
        url = clean_url(str(source.get("primaryUrl") or ""))
        scheme = authority_scheme_for_url(url or "")
        if not url or not scheme:
            continue
        for person_id in source.get("personIds") or []:
            person = people_by_id.get(person_id)
            if not person:
                continue
            held = list(person.get("authorities") or [])
            held.append({"scheme": scheme, "url": url})
            person["authorities"] = held

    for person in people:
        normalize_person_authority_fields(person)

    sources_by_id = {source["id"]: source for source in sources}
    for person in people:
        direct_urls = {
            clean_url(str(source.get("primaryUrl") or ""))
            for source_id in person.get("sourceIds") or []
            if (source := sources_by_id.get(source_id))
        }
        references = [
            entry
            for entry in person.get("references") or []
            if clean_url(str(entry.get("url") or "")) not in direct_urls
        ]
        if references:
            person["references"] = references
        else:
            person.pop("references", None)


def person_authority_errors(person: dict) -> list[str]:
    """Return normalization/schema errors for a public Person authority list."""

    expected = dict(person)
    normalize_person_authority_fields(expected)
    errors: list[str] = []
    for field in ("authorities", "references", "authorizedNameSource"):
        if person.get(field) != expected.get(field):
            errors.append(f"{field} is not normalized")
    for legacy in ("authorityUrl", "referenceUrl"):
        if person.get(legacy) is not None:
            errors.append(f"{legacy} is the legacy packed form and must not be exported")
    errors.extend(
        structured_link_errors(person, "authorities", key="scheme", controlled=True)
    )
    errors.extend(
        structured_link_errors(person, "references", key="label", controlled=False)
    )
    if str(person.get("authorizedNameSource") or "").casefold() in {
        "viaf",
        "viaf main heading",
    }:
        errors.append("VIAF cannot be the source of an authorized heading")
    return errors


def person_authority_urls(person: dict) -> list[str]:
    return authority_urls(person)


def authority_source_alignment_errors(
    people: list[dict],
    sources: list[dict],
) -> list[str]:
    """Check that accepted person-authority Sources reach the fact block."""

    people_by_id = {person["id"]: person for person in people}
    errors: list[str] = []
    for source in sources:
        source_id = str(source.get("id") or "")
        if not source_asserts_same_person(source):
            continue
        source_url = str(source.get("primaryUrl") or "")
        if not authority_scheme_for_url(source_url):
            continue
        for person_id in source.get("personIds") or []:
            person = people_by_id.get(person_id)
            if person is None:
                continue
            if not any(
                equivalent_authority_url(source_url, person_url)
                for person_url in person_authority_urls(person)
            ):
                errors.append(
                    f"{person_id} omits accepted authority identifier from {source_id}"
                )

    sources_by_id = {source["id"]: source for source in sources}
    for person in people:
        direct_urls = {
            clean_url(str(source.get("primaryUrl") or ""))
            for source_id in person.get("sourceIds") or []
            if (source := sources_by_id.get(source_id))
        }
        for reference_url in person_reference_urls(person):
            if clean_url(reference_url) in direct_urls:
                errors.append(
                    f"{person['id']} repeats a direct Source URL in references"
                )
    return errors
