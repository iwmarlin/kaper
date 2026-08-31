#!/usr/bin/env python3
"""Canonical normalization rules for filmographic web sources."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse


TRAILING_ACCESSED_PATTERN = re.compile(
    r"\s+Accessed\s+\d{1,2}\s+[A-Za-z]+\s+\d{4}\.?(?=\s*$)",
    flags=re.IGNORECASE,
)

CANONICAL_REPOSITORY_BY_HOST = {
    "catalog.afi.com": "AFI Catalog of Feature Films",
    "en.unifrance.org": "Unifrance",
    "filmportal.de": "filmportal.de / DFF – Deutsches Filminstitut & Filmmuseum",
    "imdb.com": "IMDb",
    "unifrance.org": "Unifrance",
    "weimar.humspace.ucla.edu": "The Weimar Talkies Project (UCLA)",
    "www.filmportal.de": "filmportal.de / DFF – Deutsches Filminstitut & Filmmuseum",
    "www.imdb.com": "IMDb",
    "www.tcm.com": "Turner Classic Movies (TCM)",
    "www.unifrance.org": "Unifrance",
    "tcm.com": "Turner Classic Movies (TCM)",
}

REPOSITORY_ORGANIZATION_BY_HOST = {
    "catalog.afi.com": "ORG073",
    "en.unifrance.org": "ORG058",
    "filmportal.de": "ORG072",
    "imdb.com": "ORG092",
    "unifrance.org": "ORG058",
    "weimar.humspace.ucla.edu": "ORG059",
    "www.filmportal.de": "ORG072",
    "www.imdb.com": "ORG092",
    "www.unifrance.org": "ORG058",
}

UCLA_CITATIONS = {
    "SRC0164": (
        "The Corvette Captain",
        "Der Korvettenkapitän / Blaue Jungs von der Marine",
    ),
    "SRC0165": (
        "Marriage with Limited Liability",
        "Ehe mit beschränkter Haftung / Causa Kaiser",
    ),
    "SRC0166": ("A Shot at Dawn", "Schuß im Morgengrauen"),
}

IMDB_CITATIONS = {
    "SRC0169": ("Two Hearts in Wax Time", "Title tt0230909"),
    "SRC0170": ("Trouble for Two", "Full cast and crew, title tt0028416"),
    "SRC0171": ("We Went to College", "Title tt0028483"),
    "SRC0173": ("Wings of the Morning", "Soundtracks, title tt0029785"),
    "SRC0516": (
        "Schuß im Morgengrauen / A Shot at Dawn",
        "Full cast and crew, title tt0023435",
    ),
    "SRC0528": (
        "Schuß im Morgengrauen / A Shot at Dawn",
        "Company credits, title tt0023435",
    ),
    "SRC0601": ("René Nazelles", "Name entry nm0623410"),
}


def source_hostname(source: dict[str, Any]) -> str:
    """Return the lowercase hostname of the source's primary public URL."""
    url = str(source.get("primaryUrl") or source.get("url") or "").strip()
    return urlparse(url).netloc.casefold()


def strip_redundant_access_statement(value: Any) -> str:
    """Remove a prose access statement when the date lives in ``accessDate``."""
    text = str(value or "").strip()
    text = TRAILING_ACCESSED_PATTERN.sub("", text).rstrip()
    if text and not re.search(r"[.?!][”’\"']?$", text):
        text += "."
    return text


def citation_title(source: dict[str, Any]) -> str:
    """Return a clean work/person title suitable for a source citation."""
    title = str(source.get("title", "")).strip()
    title = re.sub(r"\s+—\s+(?:IMDb\s+)?(?:full|company).*$", "", title)
    title = re.sub(r"\s+\((?:19|20)\d{2}\)$", "", title)
    return title


def afi_record_number(source: dict[str, Any]) -> str:
    url = str(source.get("primaryUrl") or source.get("url") or "")
    match = re.search(r"/(?:Film/|Catalog/moviedetails/)(\d+)", url)
    return match.group(1) if match else ""


def normalize_filmographic_source(source: dict[str, Any]) -> None:
    """Normalize a filmographic source in place without inventing new evidence."""
    source_id = str(source.get("id", ""))
    host = source_hostname(source)

    if source.get("accessDate"):
        source["fullCitation"] = strip_redundant_access_statement(
            source.get("fullCitation")
        )

    if host in {"filmportal.de", "www.filmportal.de"}:
        title = citation_title(source)
        source.update(
            {
                "shortCitation": f"filmportal.de, “{title}”",
                "fullCitation": (
                    f"filmportal.de. “{title}.” "
                    "DFF – Deutsches Filminstitut & Filmmuseum."
                ),
                "creator": "DFF – Deutsches Filminstitut & Filmmuseum",
                "repository": CANONICAL_REPOSITORY_BY_HOST[host],
                "publication": "filmportal.de",
            }
        )
        return

    if host == "catalog.afi.com":
        title = citation_title(source)
        record_number = afi_record_number(source)
        record_suffix = f", record {record_number}" if record_number else ""
        source.update(
            {
                "shortCitation": f"AFI Catalog, “{title}”",
                "fullCitation": (
                    f"American Film Institute. “{title}.” "
                    f"AFI Catalog of Feature Films{record_suffix}."
                ),
                "creator": "American Film Institute",
                "repository": CANONICAL_REPOSITORY_BY_HOST[host],
                "publication": "AFI Catalog of Feature Films",
            }
        )
        return

    if host in {"imdb.com", "www.imdb.com"}:
        title, page_description = IMDB_CITATIONS.get(
            source_id,
            (citation_title(source), "Title entry"),
        )
        source.update(
            {
                "shortCitation": f"IMDb, “{title}” — {page_description}",
                "fullCitation": f"IMDb. “{title}.” {page_description}.",
                "creator": "IMDb",
                "repository": CANONICAL_REPOSITORY_BY_HOST[host],
                "publication": "IMDb",
            }
        )
        return

    if host in {"unifrance.org", "www.unifrance.org", "en.unifrance.org"}:
        title = citation_title(source)
        source.update(
            {
                "shortCitation": f"Unifrance, “{title}”",
                "fullCitation": f"Unifrance. “{title}.” Film database entry.",
                "creator": "Unifrance",
                "repository": CANONICAL_REPOSITORY_BY_HOST[host],
                "publication": "Unifrance",
            }
        )
        return

    if host == "weimar.humspace.ucla.edu":
        title, original_title = UCLA_CITATIONS.get(
            source_id,
            (citation_title(source), ""),
        )
        original_suffix = f" [{original_title}]" if original_title else ""
        source.update(
            {
                "shortCitation": f"Weimar Talkies Project, “{title}”",
                "fullCitation": (
                    f"The Weimar Talkies Project (UCLA). “{title}”"
                    f"{original_suffix}."
                ),
                "creator": "The Weimar Talkies Project",
                "repository": CANONICAL_REPOSITORY_BY_HOST[host],
                "publication": "The Weimar Talkies Project (UCLA)",
            }
        )
        return

    if host in {"tcm.com", "www.tcm.com"}:
        source["repository"] = CANONICAL_REPOSITORY_BY_HOST[host]
        source["publication"] = CANONICAL_REPOSITORY_BY_HOST[host]
        if source_id == "SRC0168":
            source.update(
                {
                    "shortCitation": "TCM, “Mutiny on the Bounty” (1935)",
                    "fullCitation": (
                        "Toole, Michael. “Mutiny on the Bounty” (1935). "
                        "Turner Classic Movies (TCM), 2004."
                    ),
                }
            )
        elif source_id == "SRC0530":
            source.update(
                {
                    "shortCitation": "TCM, “Balalaika” (1939)",
                    "fullCitation": (
                        "Turner Classic Movies (TCM). “Balalaika” (1939). "
                        "Watch TCM title page."
                    ),
                    "creator": "Turner Classic Movies",
                }
            )
        return

    if source_id == "SRC0602":
        source.update(
            {
                "shortCitation": "Encyclopédisque, René Nazelles",
                "fullCitation": (
                    "Encyclopédisque. “René Nazelles (auteur-compositeur).” "
                    "Discographie, artist 14261."
                ),
                "sourceType": "online_database",
            }
        )
        return

    if source_id == "SRC0174":
        source.update(
            {
                "shortCitation": "Wikipedia, “Maytime (1937 film)”",
                "fullCitation": (
                    "Wikipedia contributors. “Maytime (1937 film).” "
                    "Wikipedia, The Free Encyclopedia."
                ),
                "sourceType": "wikimedia_article_page",
                "primaryUrl": "https://en.wikipedia.org/wiki/Maytime_(1937_film)",
            }
        )
        source.pop("accessUrl", None)
