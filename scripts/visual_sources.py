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
# These citations establish the printed publication date, not the date when
# the photograph was taken. Keep this list explicit: other visual records do
# have independently documented creation dates, even when reproduced in print.
VISUAL_PUBLICATION_DATE_IDS = {
    "SRC0023", "SRC0404", "SRC0552", "SRC0687",
    "SRC0448", "SRC0620",
    "SRC0403", "SRC0412", "SRC0413", "SRC0414", "SRC0573",
    "SRC0366", "SRC0648", "SRC0664", "SRC0752",
    "SRC0777",
    "SRC0704",
    "SRC0577", "SRC0619", "SRC0622",
    "SRC0352", "SRC0368", "SRC0812",
    "SRC0642", "SRC0649", "SRC0650", "SRC0651", "SRC0652",
    "SRC0653", "SRC0654", "SRC0661", "SRC0778", "SRC0813",
}
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
    "SRC0417": {
        "fullCitation": "“Kind, ich freu’ mich auf Dein Kommen.” Film poster for the German film released in 1933. Filmportal.de, material record 746992, source credited as “DIF”.",
        "dateRole": "described_item",
        "dateDisplay": "1933 (film)",
        "accessDate": "2026-10-25",
        "researchNote": "Filmportal dates the film to 1933 and identifies the material as a film poster with source credit “DIF”. The record does not separately establish the poster’s designer, original publisher or printing date. The structured year refers to the film, not an independently verified date of the poster.",
        "researchNoteType": "date_assessment"
    },
    "SRC0432": {
        "title": "Jeśli chcesz by bolszewik nie bezcześcił ci kościołów i nie mordował kapłanów idź do wojska jako ochotnik",
        "shortCitation": "Biblioteka Narodowa / Polona, military recruiting poster, [1920]",
        "fullCitation": "Jeśli chcesz by bolszewik nie bezcześcił ci kościołów i nie mordował kapłanów idź do wojska jako ochotnik. [Place unidentified]: [publisher unidentified], [1920] (Łódź: Kotkowski i Frejlich Zakłady Graficzne). Military recruiting poster, 1 sheet, 100 × 65 cm. Biblioteka Narodowa, shelfmark DŻS IA 6a6, bibliographic record b1000000657375; digitised in Polona, item 088000ec-c4ce-496d-bba7-e44af30be3c6.",
        "publication": "[Place unidentified]: [publisher unidentified], [1920] (Łódź: Kotkowski i Frejlich Zakłady Graficzne)",
        "dateRole": "publication",
        "dateDisplay": "[1920]",
        "accessDate": "2026-10-25",
        "researchNote": "The full title, physical description, printer and shelfmark follow the Polona catalogue. The publication year is supplied there in square brackets as [1920]; no exact publication day or separate design date is established. “Bolszewik” is the archive’s shortened descriptive label, not the full catalogued title. The printer is not treated as an identified publisher or designer.",
        "researchNoteType": "verification_note"
    },
    "SRC0443": {
        "title": "You’re All I Need, 1935 [sheet music, pp. 1–2 & 6 only]",
        "creator": "Bronisław Kaper (composer); Walter Jurmann (composer); Gus Kahn (lyricist)",
        "publication": "Robbins Music Corporation, New York",
        "fullCitation": "Bronisław Kaper and Walter Jurmann, music; Gus Kahn, lyrics. “You’re All I Need,” from Escapade (Metro-Goldwyn-Mayer). New York: Robbins Music Corporation, 1935. Partial sheet music, pp. 1–2 and 6 only. USC Polish Music Center, Bronisław Kaper Collection, call number PMC 5/36; USC Digital Library, unique identifier UC17193693, legacy identifier kaper-sheet-536-partial, publisher number SH 1304-3. Digital publisher: University of Southern California Libraries. DOI 10.25549/pmc_09-03-2026_11-05-25_PM-oUC17193693.",
        "dateRole": "issue",
        "accessDate": "2026-10-25",
        "primaryUrl": "https://doi.org/10.25549/pmc_09-03-2026_11-05-25_PM-oUC17193693",
        "accessUrl": "https://digitallibrary.usc.edu/CS.aspx?VP3=DamView&DocRID=2A3BF1X8GAHTY",
        "researchNote": "USC identifies both the creation and issue year as 1935 and distinguishes Robbins Music Corporation as the original publisher from USC Libraries as the digital publisher. The online document contains only pages 1–2 and 6; the linked local medium reproduces the cover, not the complete score.",
        "researchNoteType": "verification_note"
    },
    "SRC0538": {
        "creator": "Walter Jurmann and Bronisław Kaper (music); Ernst Marischka and Fritz Rotter (lyrics); Herzig (cover design)",
        "publication": "Wiener Bohème Verlag, Berlin–Vienna",
        "fullCitation": "“Ein Lied für Dich.” Sheet-music cover for the 1933 film, with Jan Kiepura; texts by Ernst Marischka and Fritz Rotter, music by Walter Jurmann and B. Kaper. Wiener Bohème Verlag, Berlin–Vienna; cover design signed “Herzig”. Digital reproduction: Verein der Freunde und Förderer des Werks von Walter Jurmann, official cover gallery.",
        "dateRole": "described_item",
        "dateDisplay": "1933 (film)",
        "researchNote": "Credits and publisher imprints were checked against the locally preserved cover reproduction. The year refers to the associated film, not an independently established printing date. The Walter Jurmann society supplies the access reproduction; it is not the historical creator or publisher.",
        "researchNoteType": "verification_note"
    },
    "SRC0539": {
        "creator": "Herzig (cover design)",
        "publication": "Wiener Bohème Verlag, Berlin–Vienna",
        "fullCitation": "“Heut kommt’s drauf an!” Sheet-music cover for the 1933 film starring Hans Albers, described on the cover as “Ein Boston-Film im Verleih der Siegel-Monopol-Film / Vertrieb Cinema”. Wiener Bohème Verlag, Berlin–Vienna; cover design signed “Herzig”. Digital reproduction: Verein der Freunde und Förderer des Werks von Walter Jurmann, official cover gallery.",
        "dateRole": "described_item",
        "dateDisplay": "1933 (film)",
        "researchNote": "Credits and publisher imprints were checked against the locally preserved cover reproduction. The year refers to the associated film, not an independently established printing date. The Walter Jurmann society supplies the access reproduction; it is not the historical creator or publisher.",
        "researchNoteType": "verification_note"
    },
    "SRC0540": {
        "creator": "Walter Jurmann and Bronisław Kaper (music); René Pujol (lyrics)",
        "publication": "Éditions Salabert, Paris",
        "fullCitation": "“On a volé un homme.” Sheet-music collection cover for the 1934 film, advertising “Ni mal, ni bien” (java) and “Un regard de femme” (slow-fox), sung by Henry Garat; words by René Pujol, music by W. Jurmann and B. Kaper. Paris: Éditions Salabert. Digital reproduction: Verein der Freunde und Förderer des Werks von Walter Jurmann, official cover gallery.",
        "dateRole": "described_item",
        "dateDisplay": "1934 (film)",
        "researchNote": "Credits and publisher imprints were checked against the locally preserved cover reproduction. The year refers to the associated film, not an independently established printing date. The Walter Jurmann society supplies the access reproduction; it is not the historical creator or publisher.",
        "researchNoteType": "verification_note"
    },
    "SRC0541": {
        "creator": "Walter Jurmann and Bronisław Kaper (music); Fritz Rotter (lyrics); Herzig (cover design)",
        "publication": "Ufaton-Verlag, Berlin",
        "fullCitation": "“Kind, ich freu’ mich auf Dein Kommen.” Sheet-music cover for the 1933 film, described as “ein Ufaton-Film, Herstellung: Günther Stapenhorst”; texts by Fritz Rotter, music by Walter Jurmann and B. Kaper. Berlin: Ufaton-Verlag; drawing signed “Herzig”. Digital reproduction: Verein der Freunde und Förderer des Werks von Walter Jurmann, official cover gallery.",
        "dateRole": "described_item",
        "dateDisplay": "1933 (film)",
        "researchNote": "Credits and publisher imprints were checked against the locally preserved cover reproduction. The year refers to the associated film, not an independently established printing date. The Walter Jurmann society supplies the access reproduction; it is not the historical creator or publisher.",
        "researchNoteType": "verification_note"
    },
    "SRC0579": {
        "publication": "Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin (digital dataset provider)",
        "fullCitation": "Luftbilder 1928, Maßstab 1:4 000. Historical vertical aerial imagery of Berlin, digitally provided as a WMS aerial mosaic by the Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin. Detail covering Pommersche Straße at Sächsische Straße, Berlin-Wilmersdorf. Geoportal Berlin / Berlin Open Data, WMS service luftbild_1928_04. Datenlizenz Deutschland – Zero – Version 2.0.",
        "dateRole": "described_item",
        "dateDisplay": "1928 (aerial imagery)",
        "accessDate": "2026-10-25",
        "researchNote": "The year 1928 dates the historical aerial imagery, not the creation or publication of the modern digital dataset. Berlin Open Data identifies the Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin as the publishing body; this is a digital-provider credit, not an identification of the original aerial photographer. The earlier citation recorded layer c_luftbilder_1928_04_raster; the current dataset page links to WMS service luftbild_1928_04.",
        "researchNoteType": "verification_note",
        "additionalLinks": [
            {
                "label": "View aerial imagery in Geoportal Berlin",
                "url": "https://gdi.berlin.de/view/luftbild_1928_04",
                "role": "alternate_access"
            }
        ]
    },
    "SRC0477": {
        "publication": "Warszawa: publisher unidentified, [1927] (J. Burian, printer)",
        "researchNote": "The list gives each member’s name, pseudonym and qualification, “A.” for author and “C.” for composer. The first page reads “Chwast Henryk «Asper» C.”; page 3 reads “Tuwim Juljan «J. Wim» A.” and “Wiehler Zygmunt C.”. Polona marks the digitised item as public domain. The printed heading gives the membership list as current on 1 April 1927; the structured date records that stated currency date, not the day of printing or publication. Polona supplies the publication year in square brackets as [1927].",
        "accessDate": "2026-10-25"
    },
    "SRC0863": {
        "publication": "Warszawa: publisher unidentified, 1931 (Druk. R. Kucharski)",
        "researchNote": "The list resolves pseudonyms against names and marks authors “a.” and composers “k.”. Four entries concern people documented here: “Asper Bruno (n. Chwast Henryk) k. c.”, “Baumritter Gustaw (psd. Włast Andrzej) a. a.”, “Oldlen (n. Tuwim Juljan) a. a.” and “Wiehler Zygmunt”. Polona marks the digitised item as public domain. The same title page prints “na dzień 1 Listopada 1931 r.” in Polish and “au 1 Octobre 1931” in French. Both statements are retained as printed; the discrepancy is not a catalogue transcription error and is not resolved here. These are stated membership-list currency dates, not established publication days. The structured publication date therefore records only 1931, the year catalogued by Polona.",
        "accessDate": "2026-10-25"
    },
    "SRC0542": {
        "publication": "Robbins Music Corporation"
    },
    "SRC0023": {"publication": "Berliner Adreßbuch 1932"},
    "SRC0551": {
        "creator": "Photographer unidentified",
        "publication": "Bain News Service",
        "repository": "Library of Congress, Prints and Photographs Division, George Grantham Bain Collection"
    },
    "SRC0400": {
        "creator": "Metro-Goldwyn-Mayer",
        "publication": "Metro-Goldwyn-Mayer"
    },
    "SRC0621": {
        "researchNote": "The Commons file page attributes the photograph to the Academy of Motion Picture Arts and Sciences and cites the Academy’s 1930 ceremony page as its source. This institutional attribution is retained as stated by the file page; no individual photographer is identified there.",
        "researchNoteType": "verification_note",
        "accessDate": "2026-10-25"
    },
    "SRC0612": {
        "creator": "Photographer unidentified",
        "publication": "Bain News Service",
        "date": "1920",
        "dateEnd": "1925",
        "dateQualifier": "approximate",
        "dateDisplay": "c. 1920–c. 1925",
        "accessDate": "2026-10-25",
        "accessUrl": "https://www.flickr.com/photos/library_of_congress/49654681548/",
        "fullCitation": "Photographer unidentified. “Alfred Piccaver.” Bain News Service, publisher, between approximately 1920 and 1925. Glass negative, 5 × 7 in. or smaller. Library of Congress, George Grantham Bain Collection, LC-B2-5730-5, digital ID ggbain.34250. Digital reproduction via Wikimedia Commons, File:Alfred Piccaver 02.jpg.",
        "researchNote": "The Commons reproduction explicitly identifies its source as Library of Congress digital ID ggbain.34250 but leaves the date unknown. The Library’s own Flickr record for the same identifier dates the negative “[between ca. 1920 and ca. 1925]”. That approximate range is used here; it is not a confirmed date of 1920. The publisher is Bain News Service; the photographer remains unidentified.",
        "researchNoteType": "date_assessment"
    },
    "SRC0596": {
        "date": "1950",
        "dateEnd": "1959",
        "dateDisplay": "1950s",
        "dateQualifier": "approximate"
    },
    "SRC0608": {
        "date": "1930",
        "dateEnd": "1939",
        "dateDisplay": "1930s",
        "dateQualifier": "approximate"
    },
    "SRC0448": {
        "title": "Madame wünscht keine Kinder — Illustrierter Film-Kurier cover",
        "publication": "Illustrierter Film-Kurier",
        "dateRole": "publication"
    },
    "SRC0620": {
        "creator": "Photographer unidentified",
        "publication": "Universal-International",
        "dateRole": "publication",
        "fullCitation": "Photographer unidentified. Press photograph of director Henry Koster for Flower Drum Song, published by Universal-International in 1961. Cropped detail via Wikimedia Commons."
    },
    "SRC0839": {
        "researchNote": "The file page gives the date as “early 1900s”, but no independently documented photography date or original publication has been established. That file-page dating is not adopted here. The date remains unknown; no replacement decade is inferred from the sitter’s appearance.",
        "dateQualifier": "unknown"
    },
    "SRC0403": {
        "publication": "Illustrierter Film-Kurier, no. 677",
        "dateRole": "publication"
    },
    "SRC0412": {
        "publication": "Illustrierter Film-Kurier, no. 214",
        "dateRole": "publication"
    },
    "SRC0413": {
        "publication": "Illustrierter Film-Kurier, no. 1946",
        "dateRole": "publication"
    },
    "SRC0414": {
        "publication": "Illustrierter Film-Kurier, no. 524",
        "dateRole": "publication"
    },
    "SRC0593": {
        "publication": "Recueil. “Féerie de Paris” de Henri Varna",
        "dateRole": "described_item",
        "dateDisplay": "1937 (revue documentation)",
        "researchNote": "The year 1937 refers to the collection of press cuttings and programmes concerning the performance of 20 December 1937. It is not an independently established date of the portrait photograph. The plate credits the photographer as “Ph. R. Sobol”.",
        "researchNoteType": "date_assessment"
    },
    "SRC0573": {
        "dateRole": "publication",
        "dateDisplay": "1912 (reported)",
        "researchNote": "The forum dates the reproduced printed notice to 1912. This reported date concerns the notice, not an independently established date of the underlying photograph. The original publication and photographer remain unidentified; the historical object has not been examined directly.",
        "researchNoteType": "date_assessment"
    },
    "SRC0752": {"creator": "Photographer unidentified"},
    "SRC0840": {"creator": "Attributed to Émile Reutlinger"},
    "SRC0537": {
        "dateRole": "creation",
        "dateQualifier": "unknown",
    },
    "SRC0439": {
        "creator": "Creator unidentified",
        # Wien Museum's date is explicitly qualified as Gebrauch (use).
        "dateRole": "described_item",
        "dateDisplay": "1922 (use)",
    },
    "SRC0618": {
        # BnF dates the associated performance, not the photograph or printing.
        "dateRole": "described_item",
        "dateDisplay": "4 October 1941 (performance)",
    },
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
        "dateRole": "publication",
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
            "Photographer unidentified. “Alfred Zeisler.” Autograph card, "
            "1932. Digital image via Wikimedia Commons, File:Smzeisle.jpg."
        ),
        "creator": "Photographer unidentified",
        "researchNote": (
            "The file page names uploader Azeisler as author and marks the "
            "upload as own work; it does not identify the photographer or the "
            "original publisher of the 1932 autograph card. The upload claim "
            "is retained as provenance information, not as an established "
            "photographer credit."
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
    "SRC0417": ('publication',),
    "SRC0439": ('publication',),
    "SRC0579": ('creator',),
    "SRC0535": ("creator",),
    "SRC0537": ("date", "dateEnd", "dateDisplay"),
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
    "SRC0612": "Photographer unidentified",
    "SRC0642": "Photographer unidentified",
    "SRC0644": "Photographer unidentified (Universal Pictures)",
    "SRC0648": "Photographer unidentified",
    "SRC0649": "Photographer unidentified",
    "SRC0654": "Studio Harcourt",
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
        or source.get("id") in VISUAL_PUBLICATION_DATE_IDS
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
        # File hosting does not establish the original publication or date role.
        # Preserve independently documented object-level metadata.
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

    if source_id in VISUAL_PUBLICATION_DATE_IDS:
        source["dateRole"] = "publication"

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
