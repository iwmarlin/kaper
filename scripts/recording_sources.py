#!/usr/bin/env python3
"""Canonical normalization rules for recording and discographic sources.

The citation identifies the recording, issue and access copy.  Interpretation
of conflicting dates, identities, incomplete labels or later reissues belongs
in a typed research note.  Access dates are structured fields and are not
repeated in the citation.  An online transfer without an identified historical
carrier is an ``online_audio_source``, not a discographic source.  A specific
disc identification reported by an uploader may be retained, but must not
silently acquire a confirmed date or label attribution.
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
        "repository": "Bibliothèque nationale de France / Catalogue général",
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


# These corrections concern citation syntax, not the date of a modern issue.
# Keep uploader-reported recording dates distinct from upload dates.
AUDITED_RECORDING_CITATIONS = {
    "SRC0715": "“Ich hab’ heut grad Geburtstag.” YouTube audio reference published by Jan van den Belt on 24 June 2011. The upload identifies Theo Mackeben mit seinem Jazz-Orchester and Walter Jurmann as refrain singer.",
    "SRC0727": "“Ich steh im Schnee und wart auf dich.” YouTube audio reference published by Brillantspecial, presented by the uploader as Gloria-Tanz-Orchester mit Refraingesang.",
    "SRC0738": "“Zgaś lampę!” Shimmy. YouTube audio reference published by jurek46pink; the upload identifies Henryk Gold and his ensemble.",
    "SRC0790": "“Du liebst mich nicht mehr.” Slow-Fox. Digital transfer published on YouTube by Radiomuseum Hardthausen; the upload identifies Tanz-Orchester Dajos Béla, Odeon O-11667 (1932), and a music credit to “Bob Henders”.",
    "SRC0713": "Marek Weber und sein Orchester, vocal by John Hendrik. “Du bist in meinem Leben die erste Sensation.” Tango. Digital transfer on YouTube; the uploader identifies Electrola E.G. 2508 and gives the year as 1932.",
    "SRC0719": "Ilja Livschakoff Tanzorchester. “Ein Lied aus meiner Heimat.” Slowfox. Digital transfer on YouTube; the uploader identifies Polydor 24604 and gives the year as 1932.",
    "SRC0729": "Ted Fio Rito and his orchestra, vocal by Muzzy Marcellino and The Debutantes. “Love Song of Tahiti.” Music by Bronislaw Kaper and Walter Jurmann; words by Gus Kahn. YouTube transfer published by Croonr1; the upload identifies Brunswick 7446, 78 rpm, and gives the year as 1935.",
    "SRC0730": "Jan Kiepura with the Odeon-Künstler-Orchester under Dr. Weissmann. “Ninon”, from Ein Lied für dich; music by Walter Jurmann and Dr. Bronislaw Kaper, words by Fritz Rotter and Ernst Marischka. YouTube transfer published by 78Upm; the upload describes an Odeon red-label issue and gives the year as 1933.",
    "SRC0735": "Bernhard Etté mit seinem Tanz-Orchester, vocal by Wolfgang Schmidt. “Adieu es ist zu schön um wahr zu sein.” Tango by Walter Jurmann, Bronislaw Kaper and Fritz Rotter from Abenteuer am Lido. YouTube transfer published by Radiomuseum Hardthausen; the upload dates the recording to 1933.",
    "SRC0746": "Melody Gents with orchestra. “Wer weint heut’ aus Liebe Tränen?” Slowfox from Ehe mit beschränkter Haftung. YouTube transfer uploaded 19 June 2014; the upload identifies Gloria G.O. 10197, side b, matrix Bi 412, and gives the year as 1932.",
    "SRC0755": "Marek Weber und sein Orchester. “Ganz ohne Liebe wär’ das Leben so bescheiden.” Fox-trot with refrain vocal. Digital transfer on YouTube; the upload identifies Electrola E.G. 2532, gives the year as 1932 and credits Jurmann and Kaper with music and Fritz Rotter with words.",
    "SRC0758": "Kurt Mühlhardt with Bernard Etté und sein Orchester. “Sagen kleine Mädels ‘nein’.” Waltz from Der Korvettenkapitän. Digital transfer on YouTube; the upload identifies Kristall 78N, gives the year as 1930 and credits Bronislaw Kaper, Fritz Rotter and Armin Lackenbach Robinson.",
    "SRC0707": "Marek Weber und sein Orchester, refrain sung by Austin Egen. “Tränen weint jede Frau so gern.” Tango. Digital transfer on YouTube; the upload identifies His Master’s Voice / Electrola and gives the year as 1929.",
    "SRC0759": "Orkiestra taneczna. “San Francisco.” Foxtrot. Digital transfer on YouTube; the upload identifies Syrena Record, gives the year as 1937 and credits Bronisław Kaper and Walter Jurmann with music and Emanuel Schlechter with Polish words.",
    "SRC0740": (
        "Ted Fio Rito and his orchestra, vocal chorus by Stanley Hickman. "
        "“Blue Venetian Waters”, from A Day at the Races; words and music by "
        "Gus Kahn, Bronislaw Kaper and Walter Jurmann. YouTube audio reference "
        "uploaded by RobinsRareRecordings; recording dated 1937 in the upload "
        "description."
    ),
}


# A conflicting catalogue number must not become a verified disc description.
AUDITED_PRIVATE_UPLOAD_FIELDS = {
    "SRC0790": {
        "researchNote": "Uploader-supplied information, not transcribed from the disc label: The upload calls the Odeon issue the first release of the recording and shows a portrait of the bandleader from a Funk-Almanach rather than the disc. The discographic details are taken from the uploader’s description; the label is not shown in the external recording. The Odeon matrix book, indexed at musiktiteldb.de, places the recording in Berlin, Schlesische Straße 26, room 4, on 10 June 1932 under matrix Be 9946, coupled with “Heute Nacht oder nie!”. The upload reports a music credit to Bob Henders alone, the recording name under which Walter Jurmann worked with Kaper."
    },
    "SRC0713": {
        "sourceType": "online_audio_source",
        "title": "Du bist in meinem Leben die erste Sensation — external listening reference",
        "shortCitation": "YouTube, “Du bist in meinem Leben die erste Sensation” — uploader-identified recording",
        "dateRole": "recording",
        "reliability": "low",
        "researchNote": "An uploader-created opening card gives Electrola E.G. 2508, matrix E-OD 795 / I and a recording date of 17 February 1932. The disc label is not shown and the card contains no authorship credits. The Electrola label list at musiktiteldb.de instead lists E.G. 2508 against “Spanischer Zigeunertanz” (OD 773-1) and “Die alte Spieluhr” (OD770-1), not this title. These descriptions conflict; the upload has not been identified with a verified historical pressing. Its year and performer details remain uploader-supplied, and it is retained as a listening reference rather than a verified description of E.G. 2508.",
        "researchNoteType": "identity_assessment",
        "additionalLinks": [
            {
                "label": "Electrola label list — conflicting catalogue-number evidence",
                "url": "http://musiktiteldb.de/Label/EMI_EG02.html",
                "role": "catalogue_entry"
            }
        ]
    },
    "SRC0707": {
        "title": "Tränen weint jede Frau so gern — Marek Weber, YouTube",
        "shortCitation": "YouTube, Marek Weber and Austin Egen, “Tränen weint jede Frau so gern”",
        "date": "1929",
        "dateRole": "described_item",
        "dateQualifier": "reported",
        "researchNote": "The upload identifies Marek Weber und sein Orchester with Austin Egen, a His Master’s Voice / Electrola issue and the year 1929, but supplies no catalogue or matrix number and does not show the disc label. It does not distinguish recording from issue year. Nico Dostal’s arrangement credit, Kaper’s music credit and Fritz Rotter’s words credit are uploader-supplied, not label transcriptions. The separate Tauber session documented for the same song does not identify this Weber transfer.",
        "sourceType": "online_audio_source",
        "researchNoteType": "discographic_note"
    },
    "SRC0730": {
        "title": "Ninon — Jan Kiepura, YouTube",
        "shortCitation": "YouTube, Jan Kiepura, “Ninon”",
        "date": "1933",
        "dateRole": "issue",
        "dateQualifier": "reported",
        "researchNote": "The upload describes a red-label Odeon issue of 1933 with Jan Kiepura and the Odeon-Künstler-Orchester under Dr. Weissmann, but gives no catalogue or matrix number and does not show the disc label. These remain uploader-supplied issue and credit details. A separate catalogue source documents Kiepura’s Odeon O-4661, matrix Be 10221; without matching label or matrix evidence, that pressing is not assigned to this transfer.",
        "sourceType": "online_audio_source",
        "researchNoteType": "discographic_note"
    },
    "SRC0735": {
        "title": "Adieu, es ist zu schön, um wahr zu sein — Bernhard Etté, YouTube",
        "shortCitation": "YouTube, Bernhard Etté and Wolfgang Schmidt, “Adieu, es ist zu schön, um wahr zu sein”",
        "date": "1933",
        "dateRole": "recording",
        "dateQualifier": "reported",
        "researchNote": "The upload description identifies a 1933 recording by Bernhard Etté mit seinem Tanz-Orchester with Wolfgang Schmidt, issued by Lindström on Gloria in Germany and Odeon elsewhere, but gives no catalogue or matrix number and does not show the disc label. The structured year refers to the uploader-reported recording, not an independently established release date. The separate Alfred Piccaver film performance does not identify this transfer or its carrier.",
        "sourceType": "online_audio_source",
        "researchNoteType": "discographic_note"
    },
    "SRC0738": {
        "title": "Zgaś lampę! — Henryk Gold ensemble, YouTube",
        "shortCitation": "YouTube, Henryk Gold ensemble, “Zgaś lampę!”",
        "date": "1926",
        "dateRole": "recording",
        "dateQualifier": "reported",
        "researchNote": "The upload description dates the recording to 1926, identifies Henryk Gold and his ensemble in an acoustically recorded instrumental Syrena version and associates the composition with the name Bruno Asper. No label, catalogue or matrix number is supplied and the disc is not shown. The year and recording details remain uploader-supplied; the printed sheet music documents the composition, not this recording or its carrier.",
        "sourceType": "online_audio_source",
        "researchNoteType": "discographic_note"
    },
    "SRC0759": {
        "title": "San Francisco — Polish-language recording, YouTube",
        "shortCitation": "YouTube, “San Francisco” — Polish-language recording",
        "date": "1937",
        "dateRole": "described_item",
        "dateQualifier": "reported",
        "researchNote": "The upload identifies an unnamed dance orchestra and a Syrena Record issue, gives the year as 1937 and attributes the Polish words to Emanuel Schlechter. It supplies no catalogue or matrix number, does not show the disc label and does not distinguish recording from issue year. These details remain uploader-supplied, not a verified description of a historical pressing.",
        "sourceType": "online_audio_source",
        "researchNoteType": "discographic_note"
    },
    "SRC0731": {
        "date": "1932",
        "dateRole": "recording",
        "dateQualifier": "reported",
        "fullCitation": "Dolly Haas with a chamber orchestra directed by Hans Sommer. “’S wird schon wieder besser.” YouTube transfer published by Marconiphone; the upload identifies His Master’s Voice E.G. 2481, matrix 60-1853, credits the music to Jurmann and Kaper, associates the song with Liebe mit Bewährungsfrist and dates the recording to Berlin, 1932.",
        "researchNote": "The catalogue and matrix numbers, performers, film association, music credits and recording year are supplied by the upload description; the disc label is not shown. No independent label or session record has been matched to this transfer. The source retains the uploader’s specific disc identification as reported, not verified, and 1932 is not treated as an established issue date.",
        "researchNoteType": "discographic_note"
    }
}


# Individually checked catalogue and reissue chronology; no session date is inferred
# from a film year, a file name or the first release of a later compilation.
VERIFIED_RECORDING_CHRONOLOGY: dict[str, dict[str, Any]] = {
    "SRC0300": {
        "researchNote": "The BnF catalogue supplies [1934] as the issue date, reconstructed from Répertoire phonographique, 3e supplément annuel 1934. The brackets indicate a catalogue-supplied date, not a date transcribed from the disc. This bibliographic dating is independent of the film's release chronology.",
        "researchNoteType": "discographic_note",
        "accessDate": "2026-10-25"
    },
    "SRC0714": {
        "date": "2000",
        "dateRole": "issue",
        "dateQualifier": "confirmed",
        "fullCitation": "The Jack Hylton Orchestra, directed by Jack Hylton, with Jack Jackson, Philippe Brun and Leo Vauchant. “Herr Lehmann, Herr Lehmann, Was Macht Die Frau Gemahlin In Marienbad?” On Hot Hylton 1926–1930. Retrieval RTR 79024, CD compilation, first issued 2000; distributed by Challenge Records International. YouTube art track supplied by The Orchard Enterprises and published 10 February 2015.",
        "researchNote": "The date identifies the compilation's first issue in 2000, not its digital publication or a historical recording session. Challenge Records identifies the format as CD, states “First release in 2000” and separately lists 21 November 2005 as the release date of its catalogue product. The YouTube access copy was published on 10 February 2015. The reissue metadata cited here does not identify the label, catalogue number or matrix of the original disc.",
        "researchNoteType": "discographic_note",
        "additionalLinks": [
            {
                "label": "Challenge Records — Hot Hylton, Retrieval RTR 79024",
                "url": "https://www.challengerecords.com/products/1182852218",
                "role": "catalogue_entry"
            }
        ]
    },
    "SRC0754": {
        "date": "1932",
        "dateRole": "issue",
        "dateQualifier": "uncertain",
        "researchNote": "The uploader dates the issue to 1932 and associates the side with Hochzeitsreise zu dritt. The Odeon label list identifies the matching title and performers as O-11768, side B, matrix Be 10147, with 1933 in its general year column; its separate release-date column is empty. The filmed label carries no year. The structured date retains the uploader's 1932 as disputed, not confirmed: the catalogue's 1933 does not by itself establish a precise issue or session date.",
        "researchNoteType": "date_assessment",
        "additionalLinks": [
            {
                "label": "Odeon label list — O-11768 B, matrix Be 10147",
                "url": "http://musiktiteldb.de/Label/Ode_11.html",
                "role": "catalogue_entry"
            }
        ]
    },
    "SRC0801": {
        "dateRole": "issue",
        "dateQualifier": "unknown",
        "researchNote": "The BnF publication statement is “S.l. : s.n., s.d.” and supplies no issue year. The film's 1934 release does not establish the disc's release date. The Internet Archive collection associates DF 1622 with 1934 without distinguishing recording from issue; the specialist discography Tino Rossi – Le Site instead places the issue in January 1935. No year is entered as a confirmed or inferred BnF issue date. The catalogue lists matrices CL 5068 and CL 5093 but does not assign each matrix to a title in the displayed metadata, so no side-level matrix assignment is inferred here.",
        "researchNoteType": "date_assessment",
        "accessDate": "2026-10-25",
        "additionalLinks": [
            {
                "label": "Tino Rossi – Le Site — DF 1622 issue chronology",
                "url": "https://www.tinorossi.fr/discographie-78t-partie-1/",
                "role": "catalogue_entry"
            }
        ]
    },
    "SRC0802": {
        "researchNote": "The BnF catalogue supplies only the decade as [193.]. The structured year 1934 remains supplied and uncertain, not transcribed from the catalogue. The Internet Archive collection lists DF 1606 under 1934 without distinguishing recording from issue; the specialist discography Tino Rossi – Le Site places the issue in November 1934. The BnF catalogue lists matrices CL 5022 and CL 5038 without assigning them to individual titles in the displayed metadata.",
        "researchNoteType": "date_assessment",
        "accessDate": "2026-10-25",
        "additionalLinks": [
            {
                "label": "Tino Rossi – Le Site — DF 1606 issue chronology",
                "url": "https://www.tinorossi.fr/discographie-78t-partie-1/",
                "role": "catalogue_entry"
            }
        ]
    },
    "SRC0805": {
        "date": "1934",
        "dateRole": "issue",
        "dateQualifier": "confirmed",
        "researchNote": "The BnF catalogue supplies [1934] as the issue date, reconstructed from Répertoire phonographique, 3e supplément, 1934. This is a catalogue-supported issue year, not a recording-session date or a date transcribed from the label. The record therefore retains the bracketed display while distinguishing the basis of the dating.",
        "researchNoteType": "discographic_note",
        "accessDate": "2026-10-25"
    },
    "SRC0800": {
        "title": "Tino Rossi — Nuits moscovites — Internet Archive",
        "shortCitation": "Internet Archive, Tino Rossi, “Nuits moscovites”",
        "fullCitation": "Tino Rossi. “Nuits moscovites.” Audio transfer in Tino Rossi Collection 1933–1939. The Popular Jazz Archive, Internet Archive.",
        "date": "1934",
        "dateRole": "described_item",
        "dateQualifier": "reported",
        "researchNote": "The collection description associates this file with Columbia DF 1622; 1934 appears in the file name and collection disc list. The uploader does not distinguish the recording year from the issue year or supply a recording-session date, so 1934 is retained as a reported year for the described recording, not a confirmed session date. BnF independently catalogues the same title, singer and disc with Orchestre de Tango Rafaelo. BnF supplies no issue year; the specialist discography Tino Rossi – Le Site places DF 1622 in January 1935, which must not be confused with a recording year. The Internet Archive file is used as the external access copy.",
        "researchNoteType": "discographic_note",
        "accessDate": "2026-10-25"
    },
    "SRC0803": {
        "title": "Tino Rossi — Vivons l’amour, vivons la vie — Internet Archive",
        "shortCitation": "Internet Archive, Tino Rossi, “Vivons l’amour, vivons la vie”",
        "fullCitation": "Tino Rossi. “Vivons l’amour, vivons la vie.” Audio transfer in Tino Rossi Collection 1933–1939. The Popular Jazz Archive, Internet Archive.",
        "date": "1934",
        "dateRole": "described_item",
        "dateQualifier": "reported",
        "researchNote": "The collection description associates this file with Columbia DF 1606; 1934 appears in the file name and collection disc list. The uploader does not distinguish the recording year from the issue year or supply a recording-session date, so 1934 is retained as a reported year for the described recording, not a confirmed session date. BnF independently catalogues the disc but dates it only to the 1930s. The Internet Archive file is used as the external access copy.",
        "researchNoteType": "discographic_note",
        "accessDate": "2026-10-25"
    },
    "SRC0804": {
        "title": "Tino Rossi — Un baiser de femme sous un ciel de feu — Internet Archive",
        "shortCitation": "Internet Archive, Tino Rossi, “Un baiser de femme sous un ciel de feu”",
        "fullCitation": "Tino Rossi. “Un baiser de femme sous un ciel de feu.” Audio transfer in Tino Rossi Collection 1933–1939. The Popular Jazz Archive, Internet Archive.",
        "date": "1934",
        "dateRole": "described_item",
        "dateQualifier": "reported",
        "researchNote": "The collection description associates this file with Columbia DF 1606; 1934 appears in the file name and collection disc list. The uploader does not distinguish the recording year from the issue year or supply a recording-session date, so 1934 is retained as a reported year for the described recording, not a confirmed session date. BnF independently catalogues the disc but dates it only to the 1930s. The Internet Archive file is used as the external access copy.",
        "researchNoteType": "discographic_note",
        "accessDate": "2026-10-25"
    },
    "SRC0806": {
        "title": "Tino Rossi — C’est ton amour — Internet Archive",
        "shortCitation": "Internet Archive, Tino Rossi, “C’est ton amour”",
        "fullCitation": "Tino Rossi. “C’est ton amour.” Audio transfer in Tino Rossi Collection 1933–1939. The Popular Jazz Archive, Internet Archive.",
        "date": "1934",
        "dateRole": "described_item",
        "dateQualifier": "reported",
        "researchNote": "The collection description associates this file with Columbia DF 1610; 1934 appears in the file name and collection disc list. The uploader does not distinguish the recording year from the issue year or supply a recording-session date, so 1934 is retained as a reported year for the described recording, not a confirmed session date. BnF independently catalogues the disc and supplies [1934] as its issue year, not its recording-session date. The Internet Archive file is used as the external access copy.",
        "researchNoteType": "discographic_note",
        "accessDate": "2026-10-25"
    }
}

VERIFIED_RECORDING_FIELD_REMOVALS: dict[str, list[str]] = {
    "SRC0801": [
        "date",
        "dateDisplay"
    ]
}


PRIVATE_UPLOAD_FIELD_REMOVALS: dict[str, list[str]] = {
    "SRC0707": [
        "publication"
    ],
    "SRC0730": [
        "publication"
    ],
    "SRC0735": [
        "publication"
    ],
    "SRC0738": [
        "publication"
    ],
    "SRC0759": [
        "publication"
    ]
}


def private_upload_semantic_errors(source: dict[str, Any]) -> list[str]:
    """Validate reviewed access/issue distinctions, not guessed text patterns.

    A catalogue number alone is not proof of identification, and a printed
    discography need not have one in its short citation.  Only individually
    reviewed records are constrained here; new cases require evidence review.
    """
    source_id = str(source.get("id", ""))
    expected = AUDITED_PRIVATE_UPLOAD_FIELDS.get(source_id, {})
    errors = []
    for field in ("sourceType", "date", "dateRole", "dateQualifier"):
        if field in expected and source.get(field) != expected[field]:
            errors.append(
                f"reviewed upload evidence requires {field}={expected[field]!r}, "
                f"not {source.get(field)!r}"
            )
    for field in PRIVATE_UPLOAD_FIELD_REMOVALS.get(source_id, []):
        if field in source:
            errors.append(
                f"unverified historical {field} belongs in the upload note, "
                "not in the access source's publication metadata"
            )
    return errors


def recording_hostname(source: dict[str, Any]) -> str:
    url = str(source.get("primaryUrl") or source.get("url") or "").strip()
    return urlparse(url).netloc.casefold()


def normalize_recording_source(source: dict[str, Any]) -> None:
    """Normalize one recording source in place."""
    source_id = str(source.get("id", ""))
    source.update(VERIFIED_RECORDING_CHRONOLOGY.get(source_id, {}))
    for field in VERIFIED_RECORDING_FIELD_REMOVALS.get(source_id, []):
        source.pop(field, None)
    if source_id in {"SRC0707", "SRC0759", "SRC0713", "SRC0719", "SRC0729", "SRC0730", "SRC0735", "SRC0746", "SRC0755", "SRC0758"}:
        source["dateQualifier"] = "reported"
    source.update(AUDITED_PRIVATE_UPLOAD_FIELDS.get(source_id, {}))
    for field in PRIVATE_UPLOAD_FIELD_REMOVALS.get(source_id, []):
        source.pop(field, None)
    citation = AUDITED_RECORDING_CITATIONS.get(source_id)
    if citation:
        source["fullCitation"] = citation
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
