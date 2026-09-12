#!/usr/bin/env python3
"""Canonical normalization rules for recording and discographic sources.

The citation identifies the recording, issue and access copy.  Interpretation
of conflicting dates, identities, incomplete labels or later reissues belongs
in a typed research note.  Access dates are structured fields and are not
repeated in the citation.  A modern digital issue without an identified
historical carrier is an ``online_audio_source``, not a discographic source.
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


# Individually verified digital releases and remasters.  Their public Source
# date describes the cited modern edition, never the year of the underlying
# work or performance.  Keeping the mapping here makes the distinction survive
# a fresh export instead of relying on a one-off edit to canonical JSON.
AUDITED_DIGITAL_AUDIO_FIELDS: dict[str, dict[str, Any]] = {
    "SRC0301": {
        "sourceType": "online_audio_source",
        "shortCitation": (
            "Joséphine Baker, “J’ai un message pour toi” (Jube Pops digital "
            "remaster, 2014)"
        ),
        "title": (
            "J’ai un message pour toi — Joséphine Baker, Jube Pops digital "
            "remaster"
        ),
        "date": "2014-11-04",
        "dateRole": "digital_publication",
        "dateQualifier": "confirmed",
        "researchNote": (
            "The date identifies the Jube Pops digital issue released on 4 "
            "November 2014. The supplied metadata does not identify the "
            "original recording session, label, catalogue number or matrix; "
            "this source therefore documents the modern reissue and provides "
            "a listening reference, not evidence for a historical carrier."
        ),
        "researchNoteType": "discographic_note",
    },
    "SRC0749": {
        "sourceType": "online_audio_source",
        "shortCitation": (
            "Allan Jones, “A Message from the Man in the Moon” — MGM outtake, "
            "2006 remaster"
        ),
        "title": (
            "A Message from the Man in the Moon — Allan Jones, MGM outtake, "
            "2006 remaster"
        ),
        "date": "2006",
        "dateRole": "issue",
        "dateQualifier": "confirmed",
        "researchNote": (
            "The date identifies the 2006 soundtrack-anthology remaster and "
            "issue, not the underlying 1937 performance or the YouTube access "
            "copy published in 2021. The number was recorded for A Day at the "
            "Races but cut before the film’s release; the performance and "
            "production credits are supplied by the rights holder to the "
            "distributing channel."
        ),
        "researchNoteType": "discographic_note",
    },
    "SRC0751": {
        "sourceType": "online_audio_source",
        "shortCitation": (
            "Allan Jones, “Tomorrow Is Another Day” (Blue Mood digital "
            "reissue, 2016)"
        ),
        "title": (
            "Tomorrow Is Another Day — Allan Jones, Blue Mood digital reissue"
        ),
        "date": "2016-07-12",
        "dateRole": "digital_publication",
        "dateQualifier": "confirmed",
        "researchNote": (
            "The date identifies the Blue Mood digital issue released on 12 "
            "July 2016; 1937 is the year of the underlying performance for A "
            "Day at the Races. The supplied release metadata identifies no "
            "original label, catalogue number or matrix. Consulted discographic "
            "literature instead lists contemporary versions by Ted Fio Rito "
            "and Hal Kemp."
        ),
        "researchNoteType": "discographic_note",
    },
    "SRC0756": {
        "sourceType": "online_audio_source",
        "shortCitation": (
            "Richard Tauber, “Schade, daß Liebe ein Märchen ist” (Membran "
            "Music digital reissue, 2010)"
        ),
        "title": (
            "Schade, daß Liebe ein Märchen ist — Richard Tauber, Membran "
            "Music digital reissue"
        ),
        "date": "2010-04-15",
        "dateRole": "digital_publication",
        "dateQualifier": "confirmed",
        "researchNote": (
            "The date identifies the Membran Music digital issue released on "
            "15 April 2010; 1932 is the year of the underlying performance. The "
            "reissue identifies no original label, catalogue number or matrix. "
            "A digitised Parlophone pressing of the same recording is linked "
            "separately and remains the preferred listening reference."
        ),
        "researchNoteType": "discographic_note",
    },
    "SRC0815": {
        "sourceType": "online_audio_source",
        "shortCitation": (
            "Allan Jones, “The Show Must Go On” (Bamboodi digital reissue, "
            "2018)"
        ),
        "title": (
            "The Show Must Go On — Allan Jones, Bamboodi digital reissue"
        ),
        "date": "2018-01-29",
        "dateRole": "digital_publication",
        "dateQualifier": "confirmed",
        "researchNote": (
            "The date identifies the Bamboodi digital issue released on 29 "
            "January 2018; 1938 is the year of the underlying performance for "
            "Everybody Sing. The release names no original session, label, "
            "catalogue number or matrix. It replaces an Audiomack page that "
            "carried the same performance without credits and refused playback "
            "outside its licensed territories."
        ),
        "researchNoteType": "discographic_note",
    },
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
    },
    "SRC0785": {
        "fullCitation": (
            "Eric Harden’s danseorkester, refrain sung by Carljohann Volbach. "
            "“Wie gern möcht’ ich dich verwöhnen.” From the sound film Melodie "
            "der Liebe; catalogue number D 4431, matrix Bi 644, 1932. Digital "
            "transfer published by the Internet Archive from the 78 rpm "
            "collection of Leif Druedahl."
        ),
        "researchNote": (
            "The Internet Archive metadata gives catalogue number D 4431 and "
            "matrix Bi 644 but contains no label field. Because the item supplies "
            "audio only, the physical disc label has not been examined. Matrix "
            "data identifies the master with the Gloria issue G.O. 10303, "
            "recorded in Berlin, studio 4, on 11 June 1932 and released in "
            "November 1932 according to the title list at musiktiteldb.de; the "
            "Danish wording of the performer credit belongs to the described "
            "pressing, not to that recording session."
        ),
        "researchNoteType": "discographic_note",
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
    source_id = str(source.get("id", ""))
    is_audited_digital_audio = source_id in AUDITED_DIGITAL_AUDIO_FIELDS
    if (
        source.get("sourceType") != "recording_discographic_source"
        and not is_audited_digital_audio
    ):
        return

    if source.get("accessDate"):
        source["fullCitation"] = strip_redundant_access_statement(
            source.get("fullCitation")
        )

    fields = RECORDING_FIELDS.get(source_id)
    if fields:
        source.update(fields)

    digital_fields = AUDITED_DIGITAL_AUDIO_FIELDS.get(source_id)
    if digital_fields:
        source.update(digital_fields)

    organization = RECORDING_ORGANIZATION_BY_HOST.get(recording_hostname(source))
    if organization:
        source["organizationIds"] = sorted(
            set(source.get("organizationIds", [])) | {organization}
        )
