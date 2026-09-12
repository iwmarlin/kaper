#!/usr/bin/env python3
"""Normalization rules for photographic and Wikimedia source records.

Source citations identify the depicted object, author, first publication and
holding or access institution.  Copyright analysis and reuse conditions live
on the linked Media record, where they are presented once beside the image.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path
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
NAC_ORGANIZATION_ID = "ORG070"
NAC_REPOSITORY = "Narodowe Archiwum Cyfrowe"

WIKIPEDIA_FILE_NAMESPACES = {
    "archivo",
    "bestand",
    "datei",
    "ficheiro",
    "fichier",
    "file",
    "plik",
    "soubor",
    "файл",
}
WIKIPEDIA_REPOSITORY_BY_HOST = {
    "de.wikipedia.org": "German Wikipedia",
    "en.wikipedia.org": "English Wikipedia",
    "fr.wikipedia.org": "French Wikipedia",
    "pl.wikipedia.org": "Polish Wikipedia",
    "ru.wikipedia.org": "Russian Wikipedia",
}

# Individually verified corrections for records whose former title, creator or
# provenance contradicted the item-level page they cite.  These are deliberately
# explicit: generic Wikimedia normalization must never infer an author or an
# underlying holding institution from the delivery platform alone.
VISUAL_SOURCE_FIELDS: dict[str, dict[str, Any]] = {
    "SRC0110": {
        # RP 6854 is the aggregate student file containing several documents
        # and photographs, not an item-level portrait source.
        "sourceType": "archival_document",
    },
    "SRC0330": {
        "title": "Fritz Rotter — portrait by Becker & Maass",
        "shortCitation": "Becker & Maass / Marie Boehm, portrait of Fritz Rotter, 1920–1932",
        "fullCitation": (
            "Becker & Maass / Marie Boehm. Portrait of Fritz Rotter, between "
            "1920 and 1932. Universal Filmlexikon (Berlin, 1932), p. 266; "
            "digital image via Wikimedia Commons, File:Fritz Rotter (composer) "
            "by Becker & Maass.png."
        ),
        "creator": "Becker & Maass / Marie Boehm",
        "repository": "Wikimedia Commons",
        "publication": "Universal Filmlexikon (Berlin, 1932)",
        "slug": "src0330-fritz-rotter-portrait-becker-maass",
    },
    "SRC0351": {
        "title": "Potsdamer Platz with Columbushaus — photograph, 1933",
        "shortCitation": (
            "Waldemar Titzenthaler, Potsdamer Platz with Columbushaus, 1933"
        ),
        "fullCitation": (
            "Waldemar Titzenthaler. Potsdamer Platz with Columbushaus, Berlin, "
            "1933. Digital image via Wikimedia Commons, File:Potsdamer Platz mit "
            "Columbushaus, 1932.jpg; source identified on the file page as Nick "
            "Gay, Berlin Then & Now (San Diego, 2005), p. 88."
        ),
        "slug": "src0351-potsdamer-platz-columbushaus-photograph-1933",
    },
    "SRC0362": {
        "title": "Paris qui brille — Casino de Paris poster, 1931",
        "shortCitation": (
            "Louis Gaudin (Zig), Paris qui brille — Casino de Paris poster, 1931"
        ),
        "fullCitation": (
            "Louis Gaudin (Zig). Paris qui brille. Poster for the Casino de "
            "Paris, 1931; digital image via Wikimedia Commons, File:Louis Gaudin "
            "- Paris qui brille 1931.jpg."
        ),
        "creator": "Louis Gaudin (Zig)",
        "date": "1931",
        "dateRole": "creation",
        "dateQualifier": "confirmed",
        "slug": "src0362-paris-qui-brille-casino-de-paris-poster-1931",
    },
    "SRC0366": {
        "title": "Moritz Mayer-Mahr — signed portrait postcard, 1908",
        "shortCitation": (
            "Moritz Mayer-Mahr — signed portrait postcard (Verlag Hans "
            "Dursthoff, 1908)"
        ),
        "fullCitation": (
            "Photographer unidentified. Signed portrait postcard of Moritz "
            "Mayer-Mahr, published by Verlag Hans Dursthoff, Berlin, 1908. "
            "Portrait Collection Friedrich Nicolas Manskopf, Goethe University "
            "Frankfurt; digital image via Wikimedia Commons, File:Mayer-Mahr.jpg."
        ),
        "creator": "Photographer unidentified",
        "repository": (
            "Portrait Collection Friedrich Nicolas Manskopf, Goethe University "
            "Frankfurt; Wikimedia Commons"
        ),
        "publication": "Verlag Hans Dursthoff, Berlin",
        "date": "1908",
        "dateRole": "creation",
        "dateQualifier": "confirmed",
        "slug": "src0366-moritz-mayer-mahr-signed-portrait-postcard-1908",
    },
    "SRC0405": {
        "dateRole": "described_item",
    },
    "SRC0410": {
        "dateRole": "described_item",
    },
    "SRC0411": {
        "dateRole": "described_item",
    },
    "SRC0415": {
        "dateRole": "described_item",
    },
    "SRC0523": {
        "shortCitation": "Polish Wikipedia, “Morskie Oko (teatr)”",
        "fullCitation": (
            "Wikipedia contributors. “Morskie Oko (teatr).” Polish Wikipedia. "
            "Last modified 20 June 2026."
        ),
        "primaryUrl": "https://pl.wikipedia.org/wiki/Morskie_Oko_(teatr)",
    },
    "SRC0571": {
        "shortCitation": (
            "Photographer unidentified, Hôtel Ritz, Paris, 1900 — Wikimedia "
            "Commons"
        ),
        "fullCitation": (
            "Photographer unidentified. Hôtel Ritz, Place Vendôme, Paris, "
            "1900. Reproduced in Schweizer Familie, no. 27 (2018), p. 37; "
            "digital image via Wikimedia Commons, File:Hotel Ritz Paris 1900.jpg."
        ),
        "creator": "Photographer unidentified",
        "publication": "Schweizer Familie, no. 27 (2018)",
    },
    "SRC0572": {
        "creator": "Samuel Herman Gottscho",
    },
    "SRC0595": {
        "fullCitation": (
            "“Alfred Zeisler.” Autograph card, 1932. Wikimedia Commons, "
            "File:Smzeisle.jpg; the file page credits user Azeisler as author "
            "under an ‘own work’ claim."
        ),
        "creator": "Azeisler (file-page attribution)",
        "researchNote": (
            "The file page names uploader Azeisler as author and marks the "
            "upload as own work; it does not identify the photographer or the "
            "original publisher of the 1932 autograph card."
        ),
        "researchNoteType": "object_context",
    },
    "SRC0604": {
        "shortCitation": (
            "The Motion Picture Director, July 1926 — portrait of Robert Z. "
            "Leonard"
        ),
        "fullCitation": (
            "Photographer unidentified. Portrait of Robert Z. Leonard. The "
            "Motion Picture Director, July 1926; digitised by the Internet "
            "Archive and supplied as a digital image via Wikimedia Commons."
        ),
        "creator": "Photographer unidentified",
        "repository": "Internet Archive; Wikimedia Commons",
        "publication": "The Motion Picture Director",
    },
}

VISUAL_SOURCE_FIELD_REMOVALS = {
    "SRC0523": ("accessUrl",),
}

# Public creator labels use natural name order and one controlled expression for
# an unidentified photographer.  The mapping is intentionally record-specific:
# ``Unknown author`` can be correct for posters, drawings and photochroms, so a
# broad textual replacement would silently change the described role.
VISUAL_CREATOR_FIELDS = {
    "SRC0350": "Burton Frasher Sr.",
    "SRC0363": "Photographer unidentified",
    "SRC0537": "Photographer unidentified",
    "SRC0554": "Photographer unidentified",
    "SRC0556": "Photographer unidentified",
    "SRC0562": "Jules Greenbaum",
    "SRC0570": "William P. Gottlieb",
    "SRC0573": "Photographer unidentified",
    "SRC0586": "Photographer unidentified",
    "SRC0598": "Photographer unidentified (Universal Pictures)",
    "SRC0599": (
        "Photographer unidentified (Famous Players-Lasky Corporation / "
        "Paramount Pictures)"
    ),
    "SRC0603": "Photographer unidentified",
    "SRC0608": "Photographer unidentified",
    "SRC0609": (
        "Photographer unidentified (Bundesarchiv Bild 102, Georg Pahl collection)"
    ),
    "SRC0612": "Photographer unidentified (Bain News Service, publisher)",
    "SRC0642": "Photographer unidentified",
    "SRC0644": "Photographer unidentified (Universal Pictures)",
    "SRC0648": "Photographer unidentified",
    "SRC0649": "Photographer unidentified",
    "SRC0654": "Photographer unidentified",
    "SRC0655": "Photographer unidentified",
    "SRC0691": "Photographer unidentified",
    "SRC0711": "Jacob Merkelbach",
    "SRC0723": "Photographer unidentified",
    "SRC0747": "Photographer unidentified",
    "SRC0777": "Photographer unidentified",
    "SRC0778": "Photographer unidentified",
    "SRC0780": "Photographer unidentified",
    "SRC0794": "Photographer unidentified",
    "SRC0795": "Stanisław Brzozowski",
    "SRC0812": "Photographer unidentified",
    "SRC0814": "Photographer unidentified",
}

NAC_TITLE_SUFFIX = re.compile(
    r"\s+—\s+(?:Narodowe Archiwum Cyfrowe|Szukaj w Archiwach)\s*$",
    flags=re.IGNORECASE,
)

NAC_CANONICAL_TITLES = {
    "SRC0435": (
        "Uniwersytet Warszawski — Pałac Kazimierzowski przy Krakowskim "
        "Przedmieściu"
    ),
}

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


def normalize_unidentified_photographer_wording(value: Any) -> str:
    """Return public prose with the controlled photographer label.

    This deliberately leaves ``Unknown author`` untouched because that phrase
    may refer to a poster, drawing, photochrom or other non-photographic work.
    """

    normalized = str(value or "")
    normalized = re.sub(
        r"\bUnknown photographer\b",
        "Photographer unidentified",
        normalized,
    )
    normalized = re.sub(
        r"\bunknown photographer\b",
        "photographer unidentified",
        normalized,
    )
    normalized = re.sub(
        r"\bPhotographer (?:unknown|unnamed)\b",
        "Photographer unidentified",
        normalized,
    )
    normalized = re.sub(
        r"\bphotographer (?:unknown|unnamed)\b",
        "photographer unidentified",
        normalized,
    )
    return normalized


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
        "Photographer unidentified. Portrait of Edmund Goulding. Photoplay 22 "
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
        "Portrait of Joseph Santley, photographer unidentified. Celebrated Actor "
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
        "Rossini’s Der Barbier von Sevilla. Photographer unidentified. Ross Verlag, "
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


def is_direct_nac_photograph(source: dict[str, Any]) -> bool:
    """Return whether a source describes a photograph accessed from NAC/SzWA.

    The repository, access platform and source type describe different layers.
    A Szukaj w Archiwach catalogue page remains the access route; when the
    represented object is a linked photograph, its source kind is an archival
    photograph rather than a generic digital record.
    """

    return (
        source.get("repository") == NAC_REPOSITORY
        and NAC_ORGANIZATION_ID in (source.get("organizationIds") or [])
        and visual_hostname(source) == "www.szukajwarchiwach.gov.pl"
        and bool(source.get("mediaIds"))
        and source.get("sourceType")
        in {
            "archival_digital_record",
            "archival_photograph",
            "image_or_photograph",
            "visual_document",
        }
    )


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


def is_wikipedia_file_page(source: dict[str, Any]) -> bool:
    """Return whether the primary record is a file page on a Wikipedia edition."""

    url = str(source.get("primaryUrl") or source.get("url") or "").strip()
    parsed = urlparse(url)
    host = parsed.netloc.casefold()
    if not host.endswith(".wikipedia.org"):
        return False
    path = unquote(parsed.path)
    if not path.startswith("/wiki/"):
        return False
    namespace, separator, _ = path.removeprefix("/wiki/").partition(":")
    return bool(separator) and namespace.casefold() in WIKIPEDIA_FILE_NAMESPACES


def is_wikipedia_article_page(source: dict[str, Any]) -> bool:
    """Return whether the primary URL is an encyclopaedia article page."""

    url = str(source.get("primaryUrl") or source.get("url") or "").strip()
    parsed = urlparse(url)
    host = parsed.netloc.casefold()
    if not host.endswith(".wikipedia.org"):
        return False
    path = unquote(parsed.path)
    return path.startswith("/wiki/") and not is_wikipedia_file_page(source)


def wikipedia_file_repository(source: dict[str, Any]) -> str | None:
    """Return the public platform name for an item-level Wikipedia file page."""

    if not is_wikipedia_file_page(source):
        return None
    host = visual_hostname(source)
    return WIKIPEDIA_REPOSITORY_BY_HOST.get(
        host,
        f"{host.split('.', 1)[0].upper()} Wikipedia",
    )


def is_normalized_visual_source(source: dict[str, Any]) -> bool:
    return (
        source.get("sourceType") in VISUAL_SOURCE_TYPES
        or is_wikimedia_source(source)
        or source.get("id") in VISUAL_CITATION_FIELDS
    )


def normalize_visual_source(source: dict[str, Any]) -> None:
    """Normalize one visual source without changing the linked Media rights."""
    source_id = str(source.get("id", ""))
    fields = VISUAL_SOURCE_FIELDS.get(source_id)
    if fields:
        source.update(fields)
    creator = VISUAL_CREATOR_FIELDS.get(source_id)
    if creator:
        source["creator"] = creator
    for field_name in VISUAL_SOURCE_FIELD_REMOVALS.get(source_id, ()):
        source.pop(field_name, None)

    direct_nac_photograph = is_direct_nac_photograph(source)
    if not direct_nac_photograph and not is_normalized_visual_source(source):
        return

    if direct_nac_photograph:
        source["sourceType"] = "archival_photograph"
        title = NAC_CANONICAL_TITLES.get(str(source.get("id", ""))) or str(
            source.get("title", "")
        )
        source["title"] = NAC_TITLE_SUFFIX.sub("", title).strip()

    wikipedia_repository = wikipedia_file_repository(source)
    if wikipedia_repository:
        # A file page supplies an image, not an encyclopaedia article.
        # Wikipedia is the access platform, not the historical image creator.
        source["sourceType"] = "image_or_photograph"
        source["repository"] = wikipedia_repository
        source["publication"] = wikipedia_repository
        source["dateRole"] = "creation"
        if str(source.get("creator") or "").casefold() in {
            "wikipedia contributors",
            "wikimedia contributors",
        }:
            source.pop("creator", None)
    elif is_wikipedia_article_page(source):
        # An encyclopaedia article and an item-level File page supply different
        # evidence, even when the article happens to display an image.
        article_repository = WIKIPEDIA_REPOSITORY_BY_HOST.get(
            visual_hostname(source),
            f"{visual_hostname(source).split('.', 1)[0].upper()} Wikipedia",
        )
        source["sourceType"] = "wikimedia_article_page"
        source["repository"] = article_repository
        source["publication"] = article_repository

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

    # These phrases express the same absence of an identified photographer.
    # Apply this after item-specific citation overrides and do not touch
    # ``Unknown author``, which may describe a poster, drawing or other object.
    for field_name in ("shortCitation", "fullCitation"):
        value = str(source.get(field_name) or "")
        if not value:
            continue
        source[field_name] = normalize_unidentified_photographer_wording(value)

    if is_wikimedia_source(source):
        source["organizationIds"] = sorted(
            set(source.get("organizationIds", [])) | {WIKIMEDIA_ORGANIZATION_ID}
        )


def normalize_file(path: Path) -> int:
    """Normalize canonical visual Sources atomically."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for source in payload.get("records", []):
        before = dict(source)
        normalize_visual_source(source)
        if source != before:
            changed += 1

    if changed:
        rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(rendered)
            temporary = Path(handle.name)
        temporary.replace(path)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Path to canonical sources.json")
    args = parser.parse_args()
    changed = normalize_file(args.path)
    print(f"normalized visual sources: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
