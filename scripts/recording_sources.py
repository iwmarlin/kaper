#!/usr/bin/env python3
"""Canonical normalization rules for recording and discographic sources.

The citation identifies the recording, issue and access copy.  Interpretation
of conflicting dates, identities, incomplete labels or later reissues belongs
in a typed research note.  Access dates are structured fields and are not
repeated in the citation.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from filmographic_sources import strip_redundant_access_statement


RECORDING_ORGANIZATION_BY_HOST = {
    "archive.org": "ORG067",
    "catalogue.bnf.fr": "ORG062",
    "katalogi.bn.org.pl": "ORG063",
    "www.discogs.com": "ORG094",
    "www.kppg.waw.pl": "ORG098",
    "www.youtube.com": "ORG093",
}


RECORDING_FIELDS: dict[str, dict[str, Any]] = {
    "SRC0005": {
        "fullCitation": (
            "Marek Weber und sein Orchester, refrain sung by Leo Moll. “Spiel’ "
            "mir auf der Balalaika einen russischen Tango.” Electrola E.G. 2392, "
            "matrix 00499-1; recorded in Berlin, 18 August 1931, released October "
            "1931; also issued as His Master’s Voice AM 3741. Session and issue "
            "data from the Electrola label list at musiktiteldb.de, based on the "
            "Discographie der deutschen Tanzmusik. Digital transfer on YouTube, "
            "video Oq4sWv9khw4."
        ),
        "repository": "YouTube / musiktiteldb.de",
        "researchNote": (
            "The transfer description dates the recording to 1932, whereas the "
            "Electrola label list gives a Berlin session on 18 August 1931 and an "
            "October 1931 release. The session-based chronology is preferred."
        ),
        "researchNoteType": "date_assessment",
    },
    "SRC0006": {
        "fullCitation": (
            "Eddy Duchin and His Orchestra, vocal by Lew Sherwood. “You’re All I "
            "Need.” Words by Gus Kahn; music by Bronisław Kaper and Walter "
            "Jurmann. Victor 25029, matrix BS-89700-1; recorded in New York, 29 "
            "April 1935; issued 8 May 1935. Session and issue data from the "
            "Discography of American Historical Recordings; digital transfer on "
            "YouTube, video xibMGdnilK0."
        ),
        "repository": (
            "Discography of American Historical Recordings / YouTube"
        ),
    },
    "SRC0115": {
        "fullCitation": (
            "Henry Garat, vocal; orchestra conducted by Bronisław Kaper. “Pourvu "
            "qu’on ait vingt ans,” from Une femme au volant. Music by Bronisław "
            "Kaper and Walter Jurmann; words by Louis Poterat. Salabert 3384, 78 "
            "rpm disc, 7 November 1933. Digital transfer from David Silvestre’s "
            "private collection, published by lysgauty1 on YouTube, video "
            "JA57rCoKoyI. Gérard Roig, “Discographie d’Henry Garat,” Phonoscopies "
            "5 (January 1994): 11, lists Salabert 3384 for the coupled side “Ninon, "
            "quand tu me souris.”"
        ),
        "repository": "YouTube / private collection of David Silvestre",
    },
    "SRC0625": {
        "fullCitation": (
            "“O chant d’amour de Tahiti ! : chanson tahitienne : du film ‘Les "
            "révoltés du Bounty’ / B. Kaper, W. Jurmann, G. Rey, comp.” Coupled "
            "with “Ho’i-maï : mélodie tahitienne / G. Rey, comp. et par.” "
            "Performed by Tihoti-ré et son ensemble tahitien, vocal duo by Mlle "
            "Maéva and Tihoti, presented by E. Ventrillon. Paris: Industries "
            "Musicales et Electriques Pathé-Marconi, 1940. One 78 rpm disc, 25 "
            "cm, Pathé PA 1234, matrices CPT 3351 and CPT 3352. Bibliothèque "
            "nationale de France, catalogue record FRBNF37963787."
        ),
        "repository": "Bibliothèque nationale de France (BnF)",
        "researchNote": (
            "The BnF catalogue describes the language of the recording as "
            "Tahitian."
        ),
        "researchNoteType": "discographic_note",
    },
    "SRC0658": {
        "fullCitation": (
            "Stare Melodie. “Może tak, może nie.” Polish-language song entry with "
            "words by Julian Tuwim and a recording by Zofia Terné, Columbia DM "
            "1624 a, matrix WJ 277, 1932; linked on the page to “Gib nur acht, "
            "über Nacht kommt die Liebe.”"
        ),
        "researchNote": (
            "The page groups Fritz Rotter and Bronisław Kaper under music. The "
            "work-level credits follow contemporary German registrations, which "
            "assign the music to Kaper and the German words to Rotter."
        ),
        "researchNoteType": "evidence_note",
    },
    "SRC0749": {
        "fullCitation": (
            "Allan Jones, vocal; orchestra conducted by Georgie Stoll; "
            "orchestration by Maurice DePackh. “A Message from the Man in the "
            "Moon (from A Day at the Races),” 1937 MGM outtake, 2006 remaster. "
            "That’s Entertainment: The Ultimate Soundtrack Anthology of MGM "
            "Musicals. Phonogram right © 1937 Turner Entertainment Co.; digital "
            "distribution by WaterTower Music."
        ),
        "researchNote": (
            "The number was recorded for A Day at the Races but cut before the "
            "film’s release. The performance and production credits are supplied "
            "by the rights holder to the distributing channel."
        ),
        "researchNoteType": "verification_note",
    },
    "SRC0807": {
        "fullCitation": (
            "Fred Marley und sein Tanz-Orchester, with Leo Monosson identified as "
            "refrain vocalist. “Eine Sommernacht am Meer.” Grammophon 885 B, "
            "matrix 1703 BN3; recorded at the Schumannsaal, Berlin, 15 August "
            "1932. Music credited to Bob Handers; words by Fritz Rotter. "
            "Labelliste “Grammophon” (1931–1932), based on Discographie der "
            "deutschen Tanzmusik, vol. 8, at musiktiteldb.de."
        ),
        "researchNote": (
            "Bob Handers was the joint recording pseudonym used by Bronisław "
            "Kaper and Walter Jurmann."
        ),
        "researchNoteType": "identity_assessment",
    },
}


def recording_hostname(source: dict[str, Any]) -> str:
    url = str(source.get("primaryUrl") or source.get("url") or "").strip()
    return urlparse(url).netloc.casefold()


def normalize_recording_source(source: dict[str, Any]) -> None:
    """Normalize one recording source in place."""
    if source.get("sourceType") != "recording_discographic_source":
        return

    source_id = str(source.get("id", ""))
    if source.get("accessDate"):
        source["fullCitation"] = strip_redundant_access_statement(
            source.get("fullCitation")
        )

    fields = RECORDING_FIELDS.get(source_id)
    if fields:
        source.update(fields)

    organization = RECORDING_ORGANIZATION_BY_HOST.get(recording_hostname(source))
    if organization:
        source["organizationIds"] = sorted(
            set(source.get("organizationIds", [])) | {organization}
        )
