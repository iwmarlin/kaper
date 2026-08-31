#!/usr/bin/env python3
"""Canonical normalization rules for authority-record sources."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from filmographic_sources import strip_redundant_access_statement


AUTHORITY_REPOSITORY_BY_HOST = {
    "catalogue.bnf.fr": "Bibliothèque nationale de France (BnF)",
    "data.bnf.fr": "Bibliothèque nationale de France (BnF)",
    "dbn.bn.org.pl": "Biblioteka Narodowa (Deskryptory BN)",
    "d-nb.info": "Deutsche Nationalbibliothek (GND)",
    "id.loc.gov": "Library of Congress (LCNAF)",
    "isni.org": "ISNI International Agency",
    "www.isni.org": "ISNI International Agency",
}

AUTHORITY_ORGANIZATION_BY_HOST = {
    "catalogue.bnf.fr": "ORG062",
    "data.bnf.fr": "ORG062",
    "dbn.bn.org.pl": "ORG063",
    "d-nb.info": "ORG074",
    "id.loc.gov": "ORG066",
}

# Multi-agency records use the primary URL to select the public repository,
# while these additional links preserve every authority file actually cited.
# ISNI is intentionally not represented by an Organization card: SRC0623 is
# the only ISNI-led source in this collection and the registry remains fully
# identified in the structured source metadata.
AUTHORITY_EXTRA_ORGANIZATIONS = {
    "SRC0628": ("ORG066",),
    "SRC0817": ("ORG066", "ORG074"),
    "SRC0847": ("ORG074",),
}

AUTHORITY_FIELDS: dict[str, dict[str, Any]] = {
    "SRC0532": {
        "shortCitation": "BnF, “Coup de feu à l’aube (film),” FRBNF14664260",
        "fullCitation": (
            "Bibliothèque nationale de France. “Coup de feu à l’aube (film).” "
            "Notice de titre conventionnel, FRBNF14664260, "
            "ark:/12148/cb14664260c."
        ),
        "researchNote": (
            "The record identifies the film as a French-German production directed "
            "by Serge de Poligny, filmed in 1932 and released in France on 17 "
            "August 1932."
        ),
        "researchNoteType": "evidence_note",
    },
    "SRC0588": {
        "shortCitation": "BnF, authority record “Marc-Cab (1901–1978)”",
        "fullCitation": (
            "Bibliothèque nationale de France. “Marc-Cab (1901–1978).” "
            "data.bnf.fr, ark:/12148/cb11914372q."
        ),
        "researchNote": (
            "The heading is established under the pseudonym Marc-Cab. BnF "
            "catalogue records for La belle de Cadix and La belle Arabelle credit "
            "the lyrics to Marcel Cabridens."
        ),
        "researchNoteType": "authority_note",
    },
    "SRC0589": {
        "shortCitation": "BnF, authority record “André de Badet (1891–1977)”",
        "fullCitation": (
            "Bibliothèque nationale de France. “André de Badet (1891–1977).” "
            "data.bnf.fr, ark:/12148/cb148356206."
        ),
    },
    "SRC0590": {
        "shortCitation": "BnF, authority record “Henri Varna (1887–1969)”",
        "fullCitation": (
            "Bibliothèque nationale de France. “Henri Varna (1887–1969).” "
            "data.bnf.fr, ark:/12148/cb14785637s."
        ),
    },
    "SRC0623": {
        "shortCitation": "ISNI, Andrzej Włast, 0000 0000 7143 777X",
        "fullCitation": (
            "ISNI International Agency. “Włast, Andrzej.” "
            "ISNI 0000 0000 7143 777X."
        ),
        "researchNote": (
            "The registry supplies the forms Włast; Włast, A.; and Włast, Andrzej. "
            "It relates Gustaw Baumritter and Willy as other identities of the same "
            "person and cites VIAF, NUKAT and BnF as contributing sources. The birth "
            "year is contested: ISNI, VIAF and the Library of Congress give 1895, "
            "while GND 1203212704 gives 17 March 1885 and Wikidata follows it. The "
            "preferred year is 1895; the discrepancy remains unresolved."
        ),
        "researchNoteType": "date_assessment",
    },
    "SRC0626": {
        "shortCitation": "BnF, authority record “Georges Rey (1908–2011)”",
        "fullCitation": (
            "Bibliothèque nationale de France. Notice de personne “Rey, Georges "
            "(1908–2011)”, FRBNF16974300, ark:/12148/cb16974300s."
        ),
        "researchNote": (
            "The notice gives 27 May 1908 in Papeete, Tahiti, and 6 January 2011 in "
            "Bazas, Gironde. It describes Rey as a Tahitian composer, singer and "
            "musician and records Tihoti-Ré and Tihoti-Re as pseudonymous forms. "
            "Its cited sources include the Pathé disc of “O chant d’amour de "
            "Tahiti !” and Claude Lestrade’s 1992 article in the Journal de la "
            "Société des océanistes."
        ),
        "researchNoteType": "authority_note",
    },
    "SRC0627": {
        "shortCitation": "GND, authority record “Mann, Paul,” 133442284",
        "fullCitation": (
            "Deutsche Nationalbibliothek. “Mann, Paul.” Gemeinsame Normdatei, "
            "GND 133442284."
        ),
        "researchNote": (
            "The GND records the composer as born in Vienna in 1910 and deceased "
            "in New York on 27 May 1983. It gives the variants Wechselmann, Paul; "
            "Mawersky, Paul Stephan; Bachinger, Alois; Marois, Jean; and Walden, "
            "Peter, and links BnF ark:/12148/cb14768347k, LCNAF nb2003055670, VIAF "
            "3662538 and Wikidata Q31202678. The Library of Congress heading reads "
            "“Mann, Paul, 1910–1983” and cites the 1944 sheet “Tell me I’m the only "
            "one you care for”. The day and month of birth are contested: German "
            "Wikipedia gives 3 September 1910 while the GND gives 3 October 1910; "
            "both agree on the year and on the death date."
        ),
        "researchNoteType": "date_assessment",
    },
    "SRC0628": {
        "shortCitation": "GND and LCNAF authority records for Robert Péguy",
        "fullCitation": (
            "Deutsche Nationalbibliothek. “Péguy, Robert.” Gemeinsame Normdatei, "
            "GND 1061685829. Library of Congress. “Péguy, Robert, 1883–1968.” "
            "LCNAF no2009019373."
        ),
        "researchNote": (
            "The GND records Robert Péguy as a director born 14 December 1883 and "
            "deceased 21 July 1968, with the variants Péguy, Marcel Robert and "
            "Robert, Marcel; LCNAF agrees on the years 1883–1968. The French "
            "Wikipedia article gives the birth name as Marcel Robert Péguy and "
            "locates both his birth and death in the 17th arrondissement of Paris. "
            "Neither authority file records the spelling Pégy; the GND links "
            "directly to the filmportal.de record for the same man. The form printed "
            "in the credits of Son altesse l’amour is therefore treated as a "
            "source-specific spelling rather than as a name he is known to have "
            "used elsewhere."
        ),
        "researchNoteType": "identity_assessment",
    },
    "SRC0629": {
        "fullCitation": (
            "Bibliothèque nationale de France. “Charlie Davson.” Authority record "
            "FRBNF13792811, ark:/12148/cb137928110."
        ),
    },
    "SRC0631": {
        "fullCitation": (
            "Bibliothèque nationale de France. Notice de personne “Steinhof, "
            "Ninon”, FRBNF14700943, ark:/12148/cb14700943p."
        ),
    },
    "SRC0632": {
        "fullCitation": (
            "Bibliothèque nationale de France. Notice de personne “Roubier "
            "d’Hérembault, André-Paul (18..–1961)”, FRBNF14842949, "
            "ark:/12148/cb148429497. ISNI 0000 0000 1013 0301."
        ),
    },
    "SRC0634": {
        "fullCitation": (
            "Biblioteka Narodowa. Deskryptory BN, personal descriptor “Halicz, "
            "Marcella”, identifier (PL)a0000002111045, control number p 2016350890, "
            "MMS ID 9810691594205606. VIAF 302995408; NUKAT n2014185547; ISNI "
            "0000 0004 0939 6902."
        ),
    },
    "SRC0686": {
        "shortCitation": "LCNAF, “Marylis, Guy, 1880–1944,” n2017060192",
        "fullCitation": (
            "Library of Congress. “Marylis, Guy, 1880–1944.” Library of Congress "
            "Name Authority File, LCCN n2017060192."
        ),
        "researchNote": (
            "The VIAF cluster 221170232 also carries the Bibliothèque nationale de "
            "France heading “Bonnal, Ermend, 1880–1944, compositeur” "
            "(ark:/12148/cb16557102j), with a see-also reference between the two "
            "names. This supports identifying Guy Marylis as a name used by "
            "Joseph-Ermend Bonnal."
        ),
        "researchNoteType": "identity_assessment",
    },
    "SRC0817": {
        "fullCitation": (
            "Bibliothèque nationale de France. “Léo Lelièvre (1899–1966).” "
            "data.bnf.fr, ark:/12148/cb147911725. Library of Congress. “Lelièvre, "
            "Léo.” LCNAF n2010078826. Deutsche Nationalbibliothek. “Lelièvre, "
            "Léo.” GND 140364778X. Wikidata Q110225870."
        ),
    },
    "SRC0845": {
        "fullCitation": (
            "Library of Congress. “Whitcup, Leonard, 1903–1979.” Library of "
            "Congress Name Authority File, LCCN n88172772."
        ),
    },
    "SRC0847": {
        "shortCitation": "LCNAF and GND authority records for Helmuth Wolfes",
        "fullCitation": (
            "Library of Congress. “Wolfes, Helmuth, 1901–1971.” LCNAF n2009033210. "
            "Deutsche Nationalbibliothek. “Wolfes, Helmut.” Gemeinsame Normdatei, "
            "GND 117446882."
        ),
        "researchNote": (
            "The GND identifies him as a conductor and composer, born 22 April "
            "1901 in Hanover and deceased 4 September 1971 in Cleveland, Ohio; it "
            "records Germany and the United States and identifies the United States "
            "as his place of exile. Its variant forms are Wolfes, Helmut Ernst and "
            "Wolfes, Helmuth. The heading is taken from the Library of Congress, "
            "which spells the forename Helmuth; the German form Helmut, under which "
            "he worked before emigration, remains the display name."
        ),
        "researchNoteType": "authority_note",
    },
}


def authority_hostname(source: dict[str, Any]) -> str:
    url = str(source.get("primaryUrl") or source.get("url") or "").strip()
    return urlparse(url).netloc.casefold()


def normalize_authority_source(source: dict[str, Any]) -> None:
    """Normalize an authority source in place without collapsing its assessment."""
    source_id = str(source.get("id", ""))
    if source.get("sourceType") != "authority_record":
        return

    if source.get("accessDate"):
        source["fullCitation"] = strip_redundant_access_statement(
            source.get("fullCitation")
        )

    fields = AUTHORITY_FIELDS.get(source_id)
    if fields:
        source.update(fields)

    host = authority_hostname(source)
    repository = AUTHORITY_REPOSITORY_BY_HOST.get(host)
    if repository:
        source["repository"] = repository

    organization_ids = list(source.get("organizationIds", []))
    primary_organization = AUTHORITY_ORGANIZATION_BY_HOST.get(host)
    if primary_organization:
        organization_ids.append(primary_organization)
    organization_ids.extend(AUTHORITY_EXTRA_ORGANIZATIONS.get(source_id, ()))
    if organization_ids:
        source["organizationIds"] = sorted(set(organization_ids))

    if host in {"catalogue.bnf.fr", "data.bnf.fr"}:
        source["creator"] = "Bibliothèque nationale de France"
        source["publication"] = (
            "data.bnf.fr" if host == "data.bnf.fr" else "Catalogue général de la BnF"
        )
    elif host == "dbn.bn.org.pl":
        source["creator"] = "Biblioteka Narodowa"
        source["publication"] = "Deskryptory Biblioteki Narodowej"
    elif host == "d-nb.info":
        source["creator"] = "Deutsche Nationalbibliothek"
        source["publication"] = "Gemeinsame Normdatei (GND)"
    elif host == "id.loc.gov":
        source["creator"] = "Library of Congress"
        source["publication"] = "Library of Congress Name Authority File (LCNAF)"
    elif host in {"isni.org", "www.isni.org"}:
        source["creator"] = "ISNI International Agency"
        source["publication"] = "ISNI registry"
