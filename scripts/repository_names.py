#!/usr/bin/env python3
"""Canonical spellings for the ``repository`` field of public Sources.

The repository is printed on every row of the Sources index and folded into the
search text, so one institution entered under several spellings reads as
several institutions.  Two rules keep the field controlled:

``REPOSITORY_ALIASES`` folds spellings the archive has actually used into the
form it uses elsewhere for the same resource.  ``REPOSITORY_ALIASES_BY_HOST``
does the same where the old spelling is only wrong for the resource cited — the
bare name of an institution stays correct for its other holdings.

``BNF_REPOSITORY_BY_HOST`` then keeps the BnF family split by the resource
actually cited rather than by the hand that typed the entry.  Authority records
are left to :mod:`authority_sources`, which marks them ``(BnF)`` by rule.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from filmographic_sources import CANONICAL_REPOSITORY_BY_HOST


BNF = "Bibliothèque nationale de France"
SACEM = "Société des auteurs, compositeurs et éditeurs de musique"

REPOSITORY_ALIASES: dict[str, str] = {
    # One work-search portal of the Austrian society, entered twice.
    "AKM/austro mechana repertory database": "AKM/AUME Werke suchen",
    # The division's own name includes the library it belongs to.
    "Billy Rose Theatre Division, The New York Public Library": (
        "Billy Rose Theatre Division, The New York Public Library "
        "for the Performing Arts"
    ),
    "California Digital Newspaper Collection": (
        "California Digital Newspaper Collection, Center for Bibliographical "
        "Studies and Research, University of California, Riverside"
    ),
    "Discogs (discogs.com)": "Discogs",
    # DIF is the former name of the DFF.
    "Filmportal.de / Deutsches Filminstitut & Filmmuseum (DIF)": (
        CANONICAL_REPOSITORY_BY_HOST["www.filmportal.de"]
    ),
    # One portal, its German name.
    "GEMA Repertoire Search": "GEMA Online-Repertoiresuche",
    # The photograph's reference number belongs to the citation, not the
    # repository name.
    "Imperial War Museums, A 25390": "Imperial War Museums",
    f"{BNF}, département des Arts du spectacle, 8-RSUPP-879": f"{BNF} / Gallica",
    "Library of Congress Prints and Photographs Division": (
        "Library of Congress, Prints and Photographs Division"
    ),
    # The holding institution leads, the delivery platform follows.
    "Media History Digital Library / Internet Archive": (
        "Internet Archive / Media History Digital Library"
    ),
    "Polona / Biblioteka Narodowa": "Biblioteka Narodowa / Polona",
    # Two SACEM databases, kept apart: the museum's catalogue of creators and
    # the society's repertoire search.
    "SACEM Repertoire": f"{SACEM} / Répertoire",
    "University of Southern California Libraries": (
        "University of Southern California Digital Library"
    ),
}

REPOSITORY_ALIASES_BY_HOST: dict[tuple[str, str], str] = {
    ("Deutsche Nationalbibliothek", "kuenste-im-exil.de"): (
        "Deutsche Nationalbibliothek / Künste im Exil"
    ),
    ("Deutsches Filminstitut & Filmmuseum (DFF)", "www.filmportal.de"): (
        CANONICAL_REPOSITORY_BY_HOST["www.filmportal.de"]
    ),
    (SACEM, "musee.sacem.fr"): f"{SACEM} / Musée SACEM",
}

BNF_REPOSITORY_BY_HOST: dict[str, str] = {
    "catalogue.bnf.fr": f"{BNF} / Catalogue général",
    "commons.wikimedia.org": f"{BNF} / Wikimedia Commons",
    "data.bnf.fr": f"{BNF} / data.bnf.fr",
    "gallica.bnf.fr": f"{BNF} / Gallica",
}


def source_host(source: dict[str, Any]) -> str:
    """Return the host of the record's primary address."""

    return urlparse(str(source.get("primaryUrl") or "")).netloc


def canonical_repository_name(source: dict[str, Any]) -> str | None:
    """Return the canonical repository name for one Source record."""

    repository = str(source.get("repository") or "").strip()
    if not repository:
        return None
    host = source_host(source)
    repository = REPOSITORY_ALIASES_BY_HOST.get(
        (repository, host), REPOSITORY_ALIASES.get(repository, repository)
    )
    if (
        repository.startswith(BNF)
        and source.get("sourceType") != "authority_record"
        and host in BNF_REPOSITORY_BY_HOST
    ):
        repository = BNF_REPOSITORY_BY_HOST[host]
    return repository


def normalize_repository_name(source: dict[str, Any]) -> None:
    """Rewrite ``repository`` in place to its canonical spelling."""

    repository = canonical_repository_name(source)
    if repository:
        source["repository"] = repository
