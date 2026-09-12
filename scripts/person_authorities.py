#!/usr/bin/env python3
"""Normalize authority control and contextual identity links for People.

The source package historically stores every person-related URL in one
newline-delimited ``authorityUrl`` field.  That field contains both formal
authority identifiers (VIAF, LCNAF, GND, BnF, etc.) and contextual pages such
as Wikipedia, Filmportal or an archival collection.  Public data keeps the
legacy line-stack representation for compatibility, but separates the two
semantics:

``authorityUrl``
    Formal authority and identity identifiers only.

``referenceUrl``
    Biographical, archival and filmographic reference pages.

A person-specific authority Source may also supply a formal identifier.  Such
an identifier is copied to the person's authority stack only when the Source
asserts the accepted identity.  Candidate identities and separately
controlled pseudonyms remain citations, not assertions about the main person.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from urllib.parse import urlsplit, urlunsplit


LINK_LINE = re.compile(r"^([^:]+):\s*(https?://\S+)$", flags=re.IGNORECASE)
BNF_IDENTIFIER = re.compile(r"(?:ark:/12148/)?(cb[0-9a-z]+)", flags=re.IGNORECASE)

AUTHORITY_ORDER = {
    "BN": 10,
    "BnF": 20,
    "GND": 30,
    "LCNAF": 40,
    "NUKAT": 50,
    "VIAF": 60,
    "ISNI": 70,
    "Wikidata": 80,
    "MusicBrainz": 90,
}

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

HEADING_SOURCE_ALIASES = {
    "viaf main heading": "VIAF",
}

# These Sources are legitimately linked to a person but do not assert the
# authority identity represented by that person's main record.
AUTHORITY_SOURCE_PERSON_EXCEPTIONS = {
    "SRC0632": "candidate identity explicitly left unresolved",
    "SRC0686": "separate authority record for the pseudonym Guy Marylis",
}


def _clean_url(value: str) -> str | None:
    url = value.strip().rstrip(".,;)")
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    path = parsed.path if parsed.path == "/" else parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, ""))


def parse_link_stack(value: object) -> list[tuple[str, str]]:
    """Parse a legacy ``Label: URL`` stack without accepting loose text."""

    if not value:
        return []
    lines = value if isinstance(value, list) else str(value).splitlines()
    result: list[tuple[str, str]] = []
    for raw in lines:
        if isinstance(raw, dict):
            label = str(raw.get("label") or raw.get("scheme") or "").strip()
            url = _clean_url(str(raw.get("url") or ""))
        else:
            match = LINK_LINE.match(str(raw).strip())
            if not match:
                continue
            label = match.group(1).strip()
            url = _clean_url(match.group(2))
        if label and url:
            result.append((label, url))
    return result


def authority_label_for_url(url: str) -> str | None:
    """Return the controlled authority scheme identified by a URL."""

    parsed = urlsplit(url)
    host = (parsed.hostname or "").casefold()
    path = parsed.path.casefold()
    if host == "viaf.org" or host.endswith(".viaf.org"):
        return "VIAF"
    if host == "id.loc.gov" and "/authorities/names/" in path:
        return "LCNAF"
    if host == "d-nb.info" and path.startswith("/gnd/"):
        return "GND"
    if host == "isni.org" and path.startswith("/isni/"):
        return "ISNI"
    if host in {"catalogue.bnf.fr", "data.bnf.fr"}:
        return "BnF"
    if host == "dbn.bn.org.pl" and "/descriptor-details/" in path:
        return "BN"
    if host == "nukat.edu.pl":
        return "NUKAT"
    if host.endswith("wikidata.org"):
        return "Wikidata"
    if host == "musicbrainz.org" and path.startswith("/artist/"):
        return "MusicBrainz"
    return None


def reference_label(label: str, url: str) -> str:
    host = (urlsplit(url).hostname or "").casefold()
    if host in REFERENCE_LABEL_BY_HOST:
        return REFERENCE_LABEL_BY_HOST[host]
    return REFERENCE_LABEL_ALIASES.get(label.casefold(), label.strip())


def authority_identity_key(label: str, url: str) -> tuple[str, str]:
    """Key equivalent BnF catalogue/data routes as one authority identity."""

    if label == "BnF":
        match = BNF_IDENTIFIER.search(url)
        if match:
            return (label, match.group(1).casefold())
    return (label, url.casefold())


def equivalent_authority_url(left: str, right: str) -> bool:
    left_clean = _clean_url(left)
    right_clean = _clean_url(right)
    if not left_clean or not right_clean:
        return False
    left_label = authority_label_for_url(left_clean)
    right_label = authority_label_for_url(right_clean)
    if not left_label or left_label != right_label:
        return False
    return authority_identity_key(left_label, left_clean) == authority_identity_key(
        right_label, right_clean
    )


def _prefer_authority_url(existing: str, candidate: str) -> str:
    """Prefer the catalogue route when BnF exposes the same ARK twice."""

    existing_host = (urlsplit(existing).hostname or "").casefold()
    candidate_host = (urlsplit(candidate).hostname or "").casefold()
    if existing_host == "data.bnf.fr" and candidate_host == "catalogue.bnf.fr":
        return candidate
    return existing


def format_link_stack(entries: Iterable[tuple[str, str]]) -> str:
    return "\n".join(f"{label}: {url}" for label, url in entries)


def normalize_person_authority_fields(person: dict) -> None:
    """Normalize and separate one public Person record in place."""

    parsed = parse_link_stack(person.get("authorityUrl"))
    parsed.extend(parse_link_stack(person.get("referenceUrl")))

    authorities: dict[tuple[str, str], tuple[str, str]] = {}
    references: dict[str, tuple[str, str]] = {}
    for supplied_label, url in parsed:
        authority_label = authority_label_for_url(url)
        if authority_label:
            key = authority_identity_key(authority_label, url)
            if key in authorities:
                old_label, old_url = authorities[key]
                authorities[key] = (
                    old_label,
                    _prefer_authority_url(old_url, url),
                )
            else:
                authorities[key] = (authority_label, url)
        else:
            references.setdefault(
                url.casefold(),
                (reference_label(supplied_label, url), url),
            )

    authority_entries = sorted(
        authorities.values(),
        key=lambda item: (AUTHORITY_ORDER[item[0]], item[1].casefold()),
    )
    reference_entries = sorted(
        references.values(),
        key=lambda item: (item[0].casefold(), item[1].casefold()),
    )

    if authority_entries:
        person["authorityUrl"] = format_link_stack(authority_entries)
    else:
        person.pop("authorityUrl", None)
    if reference_entries:
        person["referenceUrl"] = format_link_stack(reference_entries)
    else:
        person.pop("referenceUrl", None)

    heading_source = str(person.get("authorizedNameSource") or "").strip()
    if heading_source.casefold() == "local heading":
        person.pop("authorizedNameSource", None)
    elif heading_source:
        person["authorizedNameSource"] = HEADING_SOURCE_ALIASES.get(
            heading_source.casefold(), heading_source
        )


def synchronize_person_authority_sources(
    people: list[dict],
    sources: list[dict],
) -> None:
    """Expose accepted person-authority Source identifiers in the fact block."""

    people_by_id = {person["id"]: person for person in people}
    for source in sources:
        if source.get("sourceType") != "authority_record":
            continue
        if source.get("workIds") or source.get("id") in AUTHORITY_SOURCE_PERSON_EXCEPTIONS:
            continue
        url = _clean_url(str(source.get("primaryUrl") or ""))
        label = authority_label_for_url(url or "")
        if not url or not label:
            continue
        for person_id in source.get("personIds") or []:
            person = people_by_id.get(person_id)
            if not person:
                continue
            existing = parse_link_stack(person.get("authorityUrl"))
            existing.append((label, url))
            person["authorityUrl"] = format_link_stack(existing)

    for person in people:
        normalize_person_authority_fields(person)


def person_authority_errors(person: dict) -> list[str]:
    """Return normalization/schema errors for a public Person authority stack."""

    expected = dict(person)
    normalize_person_authority_fields(expected)
    errors: list[str] = []
    for field in ("authorityUrl", "referenceUrl", "authorizedNameSource"):
        if person.get(field) != expected.get(field):
            errors.append(f"{field} is not normalized")
    for label, url in parse_link_stack(person.get("authorityUrl")):
        detected = authority_label_for_url(url)
        if detected != label:
            errors.append(
                f"authorityUrl label {label!r} does not match controlled scheme {detected!r}"
            )
    for _, url in parse_link_stack(person.get("referenceUrl")):
        if authority_label_for_url(url):
            errors.append(f"formal authority URL is stored as a reference: {url}")
    return errors


def person_authority_urls(person: dict) -> list[str]:
    return [url for _, url in parse_link_stack(person.get("authorityUrl"))]


def authority_source_alignment_errors(
    people: list[dict],
    sources: list[dict],
) -> list[str]:
    """Check that accepted person-authority Sources reach the fact block."""

    people_by_id = {person["id"]: person for person in people}
    errors: list[str] = []
    for source in sources:
        source_id = str(source.get("id") or "")
        if source.get("sourceType") != "authority_record":
            continue
        if source.get("workIds") or source_id in AUTHORITY_SOURCE_PERSON_EXCEPTIONS:
            continue
        source_url = str(source.get("primaryUrl") or "")
        if not authority_label_for_url(source_url):
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
    return errors
