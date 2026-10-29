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
    # The record cites a BnF catalogue notice; what else was consulted is
    # already named in its publication field, and is not a repository.
    "BNF song notices / secondary public references": f"{BNF} / Catalogue général",
    # A site whose own name is its domain is still entered as a name, as IMDb,
    # Culture.pl and Kino-Teatr.Ru are. These four read as a hostname beside
    # them, which is the one form the field never otherwise takes.
    "deutscheslied.com": "Deutsches Lied",
    "Discogs (discogs.com)": "Discogs",
    "grammophon-platten.de": "Grammophon-Platten.de",
    "karinkiradi.at": "Karins Blog über den Zentralfriedhof und seine Toten",
    "musiktiteldb.de": "Musiktiteldb.de",
    # DIF is the former name of the DFF.
    "Filmportal.de / Deutsches Filminstitut & Filmmuseum (DIF)": (
        CANONICAL_REPOSITORY_BY_HOST["www.filmportal.de"]
    ),
    # The same pair with the platform in front, which is the order this file
    # rules against. The filmography normalizer rewrites the field by host, but
    # six video, collection and archival records are outside it, so the old
    # order is folded in here instead.
    "filmportal.de / DFF – Deutsches Filminstitut & Filmmuseum": (
        CANONICAL_REPOSITORY_BY_HOST["www.filmportal.de"]
    ),
    # One portal, its German name.
    "GEMA Repertoire Search": "GEMA Online-Repertoiresuche",
    # The photograph's reference number belongs to the citation, not the
    # repository name.
    "Imperial War Museums, A 25390": "Imperial War Museums",
    # Two platforms and no institution, so "holder first" does not decide it;
    # the records' own citations do. Both say the periodical was digitised by
    # the Internet Archive and the image supplied through Commons, which is the
    # same scanner-then-distributor order the rule states for an institution.
    "Internet Archive; Wikimedia Commons": "Internet Archive / Wikimedia Commons",
    f"{BNF}, département des Arts du spectacle, 8-RSUPP-879": f"{BNF} / Gallica",
    "Library of Congress Prints and Photographs Division": (
        "Library of Congress, Prints and Photographs Division"
    ),
    # The holding institution leads, the delivery platform follows.
    "Media History Digital Library / Internet Archive": (
        "Internet Archive / Media History Digital Library"
    ),
    "Polona / Biblioteka Narodowa": "Biblioteka Narodowa / Polona",
    # Every other private collection in the archive is named — Jacques Gana,
    # Richard Kraft, Matthias Fanck, David Silvestre. This one names none,
    # because none is known: what the record has is a sale listing, and the
    # field said "collection" where it could only mean "someone was selling
    # one". eBay serves the page the record gives; that the listing documents
    # a physical copy, and does not establish the local scan's provenance, is
    # already stated in the citation and the research note.
    "Private collection (commercial listing via eBay)": "eBay",
    # Same rule, applied to the Commons files that had it backwards. Seventeen
    # records already name the holder first and five did not, four of them
    # separating the pair with a semicolon that nothing in either name needs.
    "Wikimedia Commons / Library of Congress": (
        "Library of Congress / Wikimedia Commons"
    ),
    "Wikimedia Commons; Heritage Auctions": "Heritage Auctions / Wikimedia Commons",
    "Wikimedia Commons; Internet Archive": "Internet Archive / Wikimedia Commons",
    "Wikimedia Commons; Narodowe Archiwum Cyfrowe": (
        "Narodowe Archiwum Cyfrowe / Wikimedia Commons"
    ),
    "Wikimedia Commons; The Marc Lavry Heritage Society": (
        "The Marc Lavry Heritage Society / Wikimedia Commons"
    ),
    # Two SACEM databases, kept apart: the museum's catalogue of creators and
    # the society's repertoire search.
    "SACEM Repertoire": f"{SACEM} / Répertoire",
    "University of Southern California Libraries": (
        "University of Southern California Digital Library"
    ),
}

REPOSITORY_ALIASES_BY_HOST: dict[tuple[str, str], str] = {
    # Both hold far more than the one file cited here, so the bare name stays
    # right everywhere else; on Commons it leaves out the body that serves it,
    # which every other Commons record names.
    ("Bundesarchiv", "commons.wikimedia.org"): "Bundesarchiv / Wikimedia Commons",
    ("Deutsche Nationalbibliothek", "kuenste-im-exil.de"): (
        "Deutsche Nationalbibliothek / Künste im Exil"
    ),
    ("Deutsches Filminstitut & Filmmuseum (DFF)", "www.filmportal.de"): (
        CANONICAL_REPOSITORY_BY_HOST["www.filmportal.de"]
    ),
    ("Imperial War Museums", "commons.wikimedia.org"): (
        "Imperial War Museums / Wikimedia Commons"
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
