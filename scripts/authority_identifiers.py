#!/usr/bin/env python3
"""The controlled vocabulary of authority registers, and the structured form.

Authority identifiers were kept as a newline-delimited ``Label: URL`` stack,
one string per record, holding up to seven identifiers at once.  The label was
free text, so the same register arrived under two spellings — ``BN`` beside
``Biblioteka Narodowa``, ``LC Providers`` beside ``Library of Congress
Providers`` — and nothing could be queried without a regular expression.
Source dates were given a controlled, sortable model for exactly this reason;
the name control the archive rests on had not been given one.

Public data now holds two lists, in the shape ``Sources`` already uses for its
own identifiers:

``authorities``
    ``[{"scheme": "lcnaf", "url": "…"}]`` — formal authority and identity
    registers only.  ``scheme`` is a key from :data:`AUTHORITY_SCHEMES`, never
    free text, and it is *derived from the URL* rather than transcribed, so a
    mislabelled identifier cannot enter the field.

``references``
    ``[{"label": "Official website", "url": "…"}]`` — biographical, archival
    and institutional pages, which are context rather than identity.

The label a reader sees is held once, here, so a register cannot acquire a
second spelling by being typed again.  The legacy stack stays readable on the
input side, because the private source package still supplies that form.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from urllib.parse import urlsplit, urlunsplit


LINK_LINE = re.compile(r"^([^:]+):\s*(https?://\S+)$", flags=re.IGNORECASE)
BNF_IDENTIFIER = re.compile(r"(?:ark:/12148/)?(cb[0-9a-z]+)", flags=re.IGNORECASE)
BNF_DATA_IDENTIFIER = re.compile(
    r"data\.bnf\.fr/(?:[a-z]{2}/)?([0-9]{8})(?:/|$)",
    flags=re.IGNORECASE,
)

# The registers, with the display label and the precedence position each one
# holds.  The first four are the precedence order docs/authority-headings.md
# sets for transcribing a heading.  LC Providers is the Library of Congress
# register for corporate providers; it names publishers and labels rather than
# people, so it sits outside that four-register head and ahead of the hubs.
# VIAF and Wikidata come last on purpose: they are hubs used to find which
# register holds a record, never the source of a heading.
AUTHORITY_SCHEMES: dict[str, dict[str, object]] = {
    "lcnaf": {"label": "LCNAF", "order": 10},
    "gnd": {"label": "GND", "order": 20},
    "bnf": {"label": "BnF", "order": 30},
    "bn": {"label": "BN", "order": 40},
    "nukat": {"label": "NUKAT", "order": 50},
    "lc_providers": {"label": "LC Providers", "order": 55},
    "viaf": {"label": "VIAF", "order": 60},
    "isni": {"label": "ISNI", "order": 70},
    "wikidata": {"label": "Wikidata", "order": 80},
    "musicbrainz": {"label": "MusicBrainz", "order": 90},
}

# Every spelling a register has been recorded under, mapped to its scheme. The
# legacy stack is read through this, so an identifier keeps its register when a
# label was typed a second way.  Detection still runs from the URL; this only
# decides what a supplied label was trying to say.
SCHEME_BY_LEGACY_LABEL = {
    "lcnaf": "lcnaf",
    "gnd": "gnd",
    "bnf": "bnf",
    "bn": "bn",
    "biblioteka narodowa": "bn",
    "nukat": "nukat",
    "lc providers": "lc_providers",
    "library of congress providers": "lc_providers",
    "viaf": "viaf",
    "isni": "isni",
    "wikidata": "wikidata",
    "musicbrainz": "musicbrainz",
}


def scheme_label(scheme: str) -> str:
    entry = AUTHORITY_SCHEMES.get(scheme)
    return str(entry["label"]) if entry else scheme


def scheme_order(scheme: str) -> int:
    entry = AUTHORITY_SCHEMES.get(scheme)
    return int(entry["order"]) if entry else 999


def clean_url(value: str) -> str | None:
    url = value.strip().rstrip(".,;)")
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    path = parsed.path if parsed.path == "/" else parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, ""))


def authority_scheme_for_url(url: str) -> str | None:
    """Return the controlled scheme a URL itself identifies, or None."""

    parsed = urlsplit(url)
    host = (parsed.hostname or "").casefold()
    path = parsed.path.casefold()
    if host == "viaf.org" or host.endswith(".viaf.org"):
        return "viaf"
    if host == "id.loc.gov":
        if "/authorities/names/" in path:
            return "lcnaf"
        # The provider register is a separate LC entity file, and the two
        # organizations that carry one arrived under two different labels.
        if "/entities/providers/" in path:
            return "lc_providers"
        return None
    if host == "d-nb.info" and path.startswith("/gnd/"):
        return "gnd"
    if host == "isni.org" and path.startswith("/isni/"):
        return "isni"
    if host in {"catalogue.bnf.fr", "data.bnf.fr"}:
        return "bnf"
    # The Polish national library publishes its authority file on two hosts:
    # the descriptor view and the institutional data service.
    if host == "dbn.bn.org.pl" and "/descriptor-details/" in path:
        return "bn"
    if host == "data.bn.org.pl" and "/authorities/" in path:
        return "bn"
    if host == "nukat.edu.pl":
        return "nukat"
    if host.endswith("wikidata.org"):
        return "wikidata"
    if host == "musicbrainz.org" and path.startswith("/artist/"):
        return "musicbrainz"
    return None


def parse_link_stack(value: object) -> list[tuple[str, str]]:
    """Read a legacy ``Label: URL`` stack or an already structured list."""

    if not value:
        return []
    entries = value if isinstance(value, list) else str(value).splitlines()
    result: list[tuple[str, str]] = []
    for raw in entries:
        if isinstance(raw, dict):
            supplied = str(raw.get("scheme") or raw.get("label") or "").strip()
            url = clean_url(str(raw.get("url") or raw.get("uri") or ""))
        else:
            match = LINK_LINE.match(str(raw).strip())
            if not match:
                continue
            supplied = match.group(1).strip()
            url = clean_url(match.group(2))
        if supplied and url:
            result.append((supplied, url))
    return result


def authority_identity_key(scheme: str, url: str) -> tuple[str, str]:
    """Key equivalent BnF catalogue/data routes as one authority identity."""

    if scheme == "bnf":
        match = BNF_IDENTIFIER.search(url)
        if match:
            identifier = match.group(1).casefold().removeprefix("cb")
            # BnF ARKs append a check character to the eight-digit record
            # number used in older data.bnf.fr routes.
            return (scheme, identifier[:-1] if len(identifier) == 9 else identifier)
        match = BNF_DATA_IDENTIFIER.search(url)
        if match:
            return (scheme, match.group(1))
    return (scheme, url.casefold())


def equivalent_authority_url(left: str, right: str) -> bool:
    left_clean = clean_url(left)
    right_clean = clean_url(right)
    if not left_clean or not right_clean:
        return False
    left_scheme = authority_scheme_for_url(left_clean)
    right_scheme = authority_scheme_for_url(right_clean)
    if not left_scheme or left_scheme != right_scheme:
        return False
    return authority_identity_key(left_scheme, left_clean) == authority_identity_key(
        right_scheme, right_clean
    )


def prefer_authority_url(existing: str, candidate: str) -> str:
    """Prefer the catalogue route when BnF exposes the same ARK twice."""

    existing_host = (urlsplit(existing).hostname or "").casefold()
    candidate_host = (urlsplit(candidate).hostname or "").casefold()
    if existing_host == "data.bnf.fr" and candidate_host == "catalogue.bnf.fr":
        return candidate
    return existing


def format_link_stack(entries: Iterable[tuple[str, str]]) -> str:
    """Render the legacy stack.  Kept for reading and comparing legacy input."""

    return "\n".join(f"{label}: {url}" for label, url in entries)


def split_authority_links(
    parsed: Iterable[tuple[str, str]],
    *,
    reference_label: object = None,
    rejected_urls: frozenset[str] | set[str] = frozenset(),
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Split parsed links into the structured authority and reference lists.

    The scheme is taken from the URL, so a label cannot promote a contextual
    page into an identifier, and a register cannot be renamed by retyping it.
    """

    authorities: dict[tuple[str, str], tuple[str, str]] = {}
    references: dict[str, tuple[str, str]] = {}
    for supplied_label, url in parsed:
        if url in rejected_urls:
            continue
        scheme = authority_scheme_for_url(url)
        if scheme:
            key = authority_identity_key(scheme, url)
            if key in authorities:
                held_scheme, held_url = authorities[key]
                authorities[key] = (held_scheme, prefer_authority_url(held_url, url))
            else:
                authorities[key] = (scheme, url)
            continue
        label = (
            reference_label(supplied_label, url)
            if callable(reference_label)
            else supplied_label.strip()
        )
        if label:
            references.setdefault(url.casefold(), (label, url))

    authority_list = [
        {"scheme": scheme, "url": url}
        for scheme, url in sorted(
            authorities.values(),
            key=lambda item: (scheme_order(item[0]), item[1].casefold()),
        )
    ]
    reference_list = [
        {"label": label, "url": url}
        for label, url in sorted(
            references.values(),
            key=lambda item: (item[0].casefold(), item[1].casefold()),
        )
    ]
    return authority_list, reference_list


def authority_urls(record: dict) -> list[str]:
    """Every authority URL of a record, in register precedence order."""

    return [
        str(entry.get("url"))
        for entry in record.get("authorities") or []
        if entry.get("url")
    ]


def authority_schemes(record: dict) -> list[str]:
    return [
        str(entry.get("scheme"))
        for entry in record.get("authorities") or []
        if entry.get("scheme")
    ]


def structured_link_errors(
    record: dict,
    field: str,
    *,
    key: str,
    controlled: bool,
) -> list[str]:
    """Check one structured link list: shape, controlled scheme, and URL."""

    value = record.get(field)
    if value is None:
        return []
    if not isinstance(value, list) or not value:
        return [f"{field} must be a non-empty array when present"]
    errors: list[str] = []
    seen: set[str] = set()
    previous_order: int | None = None
    for entry in value:
        if not isinstance(entry, dict) or set(entry) != {key, "url"}:
            errors.append(f"{field} entries must hold exactly {key!r} and 'url'")
            continue
        url = str(entry.get("url") or "")
        name = str(entry.get(key) or "")
        if clean_url(url) != url:
            errors.append(f"{field} URL is not normalized: {url}")
        if url.casefold() in seen:
            errors.append(f"{field} repeats a URL: {url}")
        seen.add(url.casefold())
        if not name:
            errors.append(f"{field} entry has no {key}")
        elif controlled:
            if name not in AUTHORITY_SCHEMES:
                errors.append(f"{field} scheme is not controlled: {name!r}")
            else:
                detected = authority_scheme_for_url(url)
                if detected != name:
                    errors.append(
                        f"{field} scheme {name!r} does not match the register the "
                        f"URL identifies ({detected!r})"
                    )
                order = scheme_order(name)
                if previous_order is not None and order < previous_order:
                    errors.append(f"{field} is not in register precedence order")
                previous_order = order
        elif authority_scheme_for_url(url):
            errors.append(f"formal authority URL is stored as a reference: {url}")
    return errors
