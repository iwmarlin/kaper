#!/usr/bin/env python3
"""Normalization rules for photographic and Wikimedia source records.

Source citations identify the depicted object, author, first publication and
holding or access institution.  Copyright analysis and reuse conditions live
on the linked Media record, where they are presented once beside the image.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote, urlparse

from filmographic_sources import strip_redundant_access_statement


VISUAL_SOURCE_TYPES = {
    "archival_photograph",
    "image_or_photograph",
    "wikimedia_article_page",
    "wikimedia_commons_file",
}

WIKIMEDIA_ORGANIZATION_ID = "ORG090"

VISUAL_RIGHTS_NARRATIVE_PATTERN = re.compile(
    r"(?:"
    r"republished .*? under (?:the )?(?:Australian )?public-domain tag|"
    r"issued under the GNU Free Documentation License|"
    r"justifies free status|"
    r"carries an? URAA warning|"
    r"public-domain tag that does not hold|"
    r"no United States tag is offered|"
    r"photograph as out of copyright"
    r")",
    flags=re.IGNORECASE,
)


VISUAL_CITATION_FIELDS: dict[str, str] = {
    "SRC0593": (
        "Recueil. “Féerie de Paris” de Henri Varna. Press cuttings and programme "
        "concerning the performance of 20 December 1937. Bibliothèque nationale "
        "de France, département des Arts du spectacle, 8-RSUPP-120; catalogue "
        "notice ark:/12148/cb42600439x; digitised as Gallica "
        "ark:/12148/btv1b10501814m. Portrait plate, image 8 of 100, credited “Ph. "
        "R. Sobol” and captioned “M. Henri VARNA, Directeur du Casino de Paris et "
        "de l’Alcazar de Paris”; digital access via Wikimedia Commons."
    ),
    "SRC0597": (
        "“Zeichnung Austin Egen,” c. 1930. Drawing attributed on the file page to "
        "Austin Egen; original publication and holding institution unidentified. "
        "German-language Wikipedia, Datei:Austin Egen.png."
    ),
    "SRC0642": (
        "Unknown photographer. Portrait of Edmund Goulding. Photoplay 22 "
        "(December 1922): 61. Digitised volume at the Internet Archive; digital "
        "image via Wikimedia Commons."
    ),
    "SRC0645": (
        "Studio Harcourt. Portrait of Henri-Georges Clouzot, 1947. Réunion des "
        "musées nationaux, image 08-537855; digital image via Wikimedia Commons."
    ),
    "SRC0647": (
        "Max Dupain. Studio portrait of the pianist Alexander Zakin, July 1947. "
        "Vintage gelatin silver print. Mitchell Library, State Library of New "
        "South Wales, ON 558/Box 13/no. 90; digital image via Wikimedia Commons."
    ),
    "SRC0648": (
        "Portrait of Joseph Santley, photographer unnamed. Celebrated Actor "
        "Folks’ Cookeries (New York: Mabel Rowland, Inc., 1916), 77. Digital image "
        "via Wikimedia Commons."
    ),
    "SRC0687": (
        "Edward Stanford Ltd. The World on Mercator’s Projection. London, 1926. "
        "Stanford’s London Atlas of Universal Geography, Whitehall edition. David "
        "Rumsey Map Collection, David Rumsey Map Center, Stanford University "
        "Libraries, list no. 14508.007."
    ),
    "SRC0691": (
        "Signed artist postcard of Willi Domgraf-Fassbaender as Figaro in "
        "Rossini’s Der Barbier von Sevilla. Photographer unknown. Ross Verlag, "
        "Berlin, c. 1928; private collection; digital image via Wikimedia Commons."
    ),
    "SRC0747": (
        "Ossi Oswalda and Siegfried Arno in the Ama-Film production Schatz, mach’ "
        "Kasse (1926). Photographer not credited. Das Leben 4, no. 7 (January "
        "1926/27); cropped digital image via Wikimedia Commons."
    ),
    "SRC0752": (
        "Publicity photograph of the actor and tenor Allan Jones, issued by the "
        "Frederick Brothers Agency, 23 April 1945. Photographer not credited; "
        "digital image via Wikimedia Commons."
    ),
    "SRC0837": (
        "Studio Star. “Tino Rossi portrait années 1930.” Studio portrait from the "
        "collection of contributor Simonet63; original publication unidentified. "
        "Digital image via Wikimedia Commons."
    ),
    "SRC0839": (
        "Photographer unidentified. Publicity portrait of Emanuel Schlechter; "
        "original publication and date unidentified. Digital image via Wikimedia "
        "Commons, File:Emanuel-schlechter.jpg."
    ),
}


def visual_hostname(source: dict[str, Any]) -> str:
    url = str(source.get("primaryUrl") or source.get("url") or "").strip()
    return urlparse(url).netloc.casefold()


def is_wikimedia_source(source: dict[str, Any]) -> bool:
    host = visual_hostname(source)
    return host == "commons.wikimedia.org" or host.endswith(".wikipedia.org")


def is_wikimedia_commons_file_page(source: dict[str, Any]) -> bool:
    """Return whether the primary record is an item-level Commons file page.

    A Commons URL does not by itself make Commons the archival repository: an
    institutional photograph may merely use Commons as its delivery surface.
    This helper identifies the access page only; callers must still inspect the
    structured ``repository`` field before deciding the source type.
    """

    url = str(source.get("primaryUrl") or source.get("url") or "").strip()
    parsed = urlparse(url)
    return (
        parsed.netloc.casefold() == "commons.wikimedia.org"
        and unquote(parsed.path).startswith("/wiki/File:")
    )


def is_normalized_visual_source(source: dict[str, Any]) -> bool:
    return (
        source.get("sourceType") in VISUAL_SOURCE_TYPES
        or is_wikimedia_source(source)
        or source.get("id") in VISUAL_CITATION_FIELDS
    )


def normalize_visual_source(source: dict[str, Any]) -> None:
    """Normalize one visual source without changing the linked Media rights."""
    if not is_normalized_visual_source(source):
        return

    if source.get("accessDate"):
        source["fullCitation"] = strip_redundant_access_statement(
            source.get("fullCitation")
        )
        source["fullCitation"] = re.sub(
            r"\s+Accessed via [^.]+\.?(?=\s*$)",
            "",
            str(source.get("fullCitation", "")),
            flags=re.IGNORECASE,
        ).rstrip()

    citation = VISUAL_CITATION_FIELDS.get(str(source.get("id", "")))
    if citation:
        source["fullCitation"] = citation

    if is_wikimedia_source(source):
        source["organizationIds"] = sorted(
            set(source.get("organizationIds", [])) | {WIKIMEDIA_ORGANIZATION_ID}
        )
