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
    "SRC0694": {
        "researchNote": "The filmed label identifies Ben Berlin und sein Orchester, Grammophon B 51823, order no. 23042, and the Rotter–Kaper credit. The uploader names Alexander Fleßburg as the refrain singer and gives 1930 as the recording year; neither statement is printed on the label. No independently documented session or issue date has been established for this transfer. Dates of other recordings of the song are not used to date this disc.",
        "fullCitation": "Ben Berlin und sein Orchester, with German refrain vocal. “Auf Wiederseh’n, Herr Doktor!” Fox-trot; label credit “(Rotter-Kaper)”. Grammophon, electrical recording, catalogue B 51823, order no. 23042, side 2, n.d. Shellac disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube."
    },
    "SRC0695": {
        "researchNote": "The filmed label identifies Ben Berlin und sein Orchester, Grammophon B 50959, order no. 22222, and the Kaper–Rotter and Roehr credits. The uploader places the recording and first release in Berlin in 1929; the year is not printed on the label. The structured date retains that reported recording year, not a separately verified issue date. The composition’s publication chronology does not establish the session or release date of this disc.",
        "fullCitation": "Ben Berlin und sein Orchester. “Nimm diesen Strauß Vergißmeinnicht.” Fox-trot; label credits “(Kaper – Rotter)” and “(Verlag: Roehr A.-G., Berlin)”. Grammophon, electrical recording, Polyfar “R” Orchester series, catalogue B 50959, order no. 22222, side 2, n.d. Shellac disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube."
    },
    "SRC0716": {
        "researchNote": "The filmed label identifies Parlophone 80.235, matrix B 38451, Saxophon Orchester Dobbri and Max Mensing. R. Pfau’s Lexikon der deutschen Tanzmusik, part 8, printed p. 926, independently lists this song with “B 38451 Dobbri Saxophon Orch.” Its general year 1930 does not specify a session or issue date. The Berlin session in 1930 and the description of the copy as a French issue remain uploader-supplied; neither is printed on the label.",
        "additionalLinks": [
            {
                "label": "R. Pfau, Lexikon der deutschen Tanzmusik, part 8, p. 926",
                "url": "https://www.db-thueringen.de/servlets/MCRFileNodeServlet/dbt_derivate_00060580/Pfau_Lexikon_deutschen_Tanzmusik_008.pdf#page=68",
                "role": "additional_evidence"
            }
        ],
        "fullCitation": "Saxophon Orchester Dobbri, vocal by Max Mensing. “Was macht jede Nacht so ein kleines Baby in der Bar.” Slow fox; label credit “Fritz Rotter & Dr. B. Kaper”. Parlophone 80.235, matrix B 38451, n.d. Shellac disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube."
    },
    "SRC0717": {
        "researchNote": "The filmed label identifies Marek Weber und sein Orchester, Electrola E.G. 2406 and matrix 60-1740. R. Pfau’s Lexikon der deutschen Tanzmusik, part 6, printed p. 736, independently lists “EG 2406 Marek Weber” under “Margarethe wander mit mir”. Its general year 1931 is not a separately documented session or issue date. The source retains 1931 as the uploader-reported recording year. The uploader’s link to an Italian version does not identify or date this pressing.",
        "additionalLinks": [
            {
                "label": "R. Pfau, Lexikon der deutschen Tanzmusik, part 6, p. 736",
                "url": "https://www.db-thueringen.de/servlets/MCRFileNodeServlet/dbt_derivate_00060562/Pfau_Lexikon_deutschen_Tanzmusik_006.pdf#page=82",
                "role": "additional_evidence"
            }
        ],
        "fullCitation": "Marek Weber und sein Orchester, dance orchestra with refrain vocal. “Margarete, wander mit mir ….” Fox-trot; label credits music and text to Fritz Rotter and Dr. B. Kaper. Electrola E.G. 2406, matrix 60-1740, n.d. Shellac disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube."
    },
    "SRC0004": {
        "title": "Blaue Jungs von der Marine — Kristall 3098",
        "shortCitation": "Kristall 3098, “Blaue Jungs von der Marine”",
        "slug": "src0004-kristall-3098-blaue-jungs-von-der-marine",
        "fullCitation": "Bernard Etté und sein Orchester, refrain by Kurt Mühlhardt. “Blaue Jungs von der Marine.” Marschlied from Korvettenkapitän; label credit “Dr. Kaper / Rotter / Robinson”. Kristall, order no. 3098, n.d. YouTube transfer by Wunschkonzert.",
        "date": "1930",
        "dateRole": "recording",
        "dateQualifier": "reported",
        "accessDate": "2026-10-25",
        "researchNote": "The label image accompanying the upload reads “Best.-Nr. 3098”, not “78 N”, and names Bernard Etté und sein Orchester and refrain singer Kurt Mühlhardt. SRC0758 shows the other title on the same catalogue issue, also numbered 3098; this does not establish that the transfers came from the same physical copy. “Aufnahme 1930” is the uploader’s recording-year statement, not an independently established issue date. SRC0471 documents the composition’s copyright registration, not the disc or its publisher; the record label does not name Alrobi.",
        "researchNoteType": "discographic_note",
        "contributionIds": [
            "CON-S017-C-P009",
            "CON-S017-L-P020",
            "CON-S017-L-P083",
            "CON-S017-LAB-ORG129",
            "CON-S017-P-ORG121"
        ]
    },
    "SRC0725": {
        "date": "1931-05",
        "dateRole": "issue",
        "dateQualifier": "confirmed",
        "accessDate": "2026-10-25",
        "fullCitation": "Austin Egen, accompanied by the Odeon-Tango-Orchester. “Ich weiß ein kleines Café.” Tango; label credits Dr. B. Kaper and Austin Egen, with words by Fritz Rotter. Odeon O-11439 a, matrix Be 9409; issued May 1931. Label filmed in the YouTube upload by Ilja Livschakoff.",
        "researchNote": "Wolfgang Stanicek’s dissertation Austin Egen (2010), p. 156, lists Odeon O-11439a, matrix Be 9409, with Austin Egen and the Odeon-Tango-Orchester: “NE 05/1931” and a Berlin session on 12 March 1931, citing Weihermüller’s Egen discography, p. 380. The structured date describes the May 1931 issue, not the March session. The label in the transfer independently matches the catalogue number, matrix and performers; it also prints “Auch als Tanzplatte geeignet”, B.I.E.M. and Carl Lindström A.-G.",
        "researchNoteType": "discographic_note",
        "additionalLinks": [
            {
                "label": "Wolfgang Stanicek, Austin Egen (2010), p. 156 — session and issue chronology",
                "url": "https://grammophon-platten.de/e107_files/public/1353002785_232_FT5904_austin_egen_dr_stanicek.pdf#page=156",
                "role": "additional_evidence"
            }
        ]
    },
    "SRC0782": {
        "fullCitation": "Orchestra Mascotte. “Moonlight at Sanssouci.” Waltz; label credit “Rotter–Kaper”. Parlophone A3436, matrix Be 9615, n.d. Australian pressing, labelled “Made in Australia for Parlophone Co. Ltd.” Disc label photograph and digital transfer published by the Great 78 Project, Internet Archive.",
        "accessDate": "2026-10-25",
        "researchNote": "The Internet Archive item includes a photograph of the disc, not audio alone. The label identifies Orchestra Mascotte, Parlophone A3436 and Australia; the runout shows Be 9615, also transcribed in the item metadata. The patent dates printed around the label rim are not recording or issue dates. No independently documented issue date has been established for this Australian pressing; dates assigned to other Parlophone issues are not transferred to A3436. Orchestra Mascotte is a house name and does not identify the individual players.",
        "researchNoteType": "discographic_note",
        "additionalLinks": [
            {
                "label": "Great 78 Project — photograph of the Australian Parlophone A3436 label",
                "url": "https://archive.org/download/78_moonlight-at-sanssouci_orchestra-mascotte-rotter-kaper_gbia3007402a/78_moonlight-at-sanssouci_orchestra-mascotte-rotter-kaper_gbia3007402a_itemimage.jpg",
                "role": "additional_evidence"
            }
        ]
    },
    "SRC0740": {
        "accessDate": "2026-10-25",
        "researchNote": "The upload gives no label, catalogue or matrix number and does not show the disc; the performer, credit and year details are uploader-supplied metadata. The independent Decca 1000 Series Numerical Listing documents Ted Fio Rito’s “Blue Venetian Waters” on Decca 1257, matrix DLA705, recorded 19 February 1937. That entry establishes the existence of a Fio Rito recording, but does not by itself identify this upload with that master or pressing; the listed session date and catalogue number are not assigned to the transfer.",
        "additionalLinks": [
            {
                "label": "Decca 1000 Series Numerical Listing — 1257, matrix DLA705 (comparison, not transfer identification)",
                "url": "https://www.78discography.com/Dec1000.htm",
                "role": "additional_evidence"
            }
        ],
        "fullCitation": "Ted Fio Rito and his orchestra, vocal chorus by Stanley Hickman. “Blue Venetian Waters”, from A Day at the Races; words and music by Gus Kahn, Bronislaw Kaper and Walter Jurmann. YouTube audio reference uploaded by RobinsRareRecordings; recording dated 1937 in the upload description."
    },
    "SRC0811": {
        "date": "1937",
        "dateRole": "described_item",
        "dateQualifier": "uncertain",
        "accessDate": "2026-10-25",
        "fullCitation": "“Blue Venetian Waters”, attributed to Allan Jones. Audio transfer uploaded by Archiveradio1930 to YouTube; the title describes it as a 1937 broadcast.",
        "researchNote": "The upload title calls this a 1937 broadcast, but its description ends with “ALLAN JONES SINGS MY HEAVEN ON EARTH 1939 RADIO SHOW”, naming a different song and year. No programme documentation, exact broadcast date, label or matrix resolves this inconsistency; 1937 is retained only as an uncertain date of the described item. Jasmine Records’ official listing for Allan Jones: There’s a Song in the Air (JASCD110, released 10 January 1998) includes “Blue Venetian Waters” as track 8, independently documenting a Jones performance, but does not establish that this upload reproduces the same performance. The singer attribution for this particular transfer remains qualified.",
        "researchNoteType": "discographic_note",
        "additionalLinks": [
            {
                "label": "Jasmine Records, Allan Jones: There’s a Song in the Air — JASCD110, track 8",
                "url": "https://jasmine-records.co.uk/shop/jones-allan/allan-jones-theres-a-song-in-the-air/",
                "role": "additional_evidence"
            }
        ]
    },
    "SRC0710": {
        "accessDate": "2026-10-25",
        "researchNote": "The uploader identifies the singer credited as Leo Moll as Leo Monosson and reports 1931 as the Electrola issue year. Neither that identification nor the issue year is printed on the filmed label; the year remains reported, without a newly established session date. The accompanying 1930 photograph depicts Brioni and does not date the disc. Discographic entries for other performers’ recordings of this song are not used to date Electrola E.G. 2400.",
        "researchNoteType": "discographic_note",
        "fullCitation": "Marek Weber und sein Orchester, refrain credited as Leo Moll. “Signorina aus Brioni.” Tango; label credits Fritz Rotter and Dr. Kaper for music and text. Electrola E.G. 2400, n.d. Shellac disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube."
    },
    "SRC0712": {
        "date": "1932",
        "dateRole": "recording",
        "dateQualifier": "confirmed",
        "accessDate": "2026-10-25",
        "fullCitation": "Tanzorchester J. Geiger, refrain sung by Hans Rotter. “Du bist verrückt, mein Schatz, du denkst an Liebe.” Lied und foxtrot; label credits music and text to Fritz Rotter and Dr. B. Kaper. Novaphon Electro Record B 4051, made in Austria, n.d.; matrix 2647 identified in Discographie der österreichischen Populärmusik. Flexible disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube.",
        "researchNote": "Discographie der österreichischen Populärmusik, pp. 53–54, lists “Du bist verückt mein Schatz, denn du denkst ...”, matrix 2647, on Novaphon 4051 under “Tanzorchester J. Geiger” and the recording-group heading “Wien, 1932”. The structured date follows that year-level recording chronology, not a separately documented issue date. It supersedes the uploader’s approximate 1931 issue dating; no month or day is inferred. The matrix is only partly legible in the filmed label, so 2647 is identified from the discography rather than presented as a complete label reading. The uploader’s expansion of J. Geiger to Isy Geiger is not silently substituted for the label wording.",
        "researchNoteType": "discographic_note",
        "additionalLinks": [
            {
                "label": "Discographie der österreichischen Populärmusik, pp. 53–54 — J. Geiger, matrix 2647",
                "url": "https://www.phonomuseum.at/includes/content/disko/discographie_oesterreich.pdf#page=53",
                "role": "catalogue_entry"
            }
        ]
    },
    "SRC0718": {
        "date": "1931-03-11",
        "dateRole": "recording",
        "dateQualifier": "confirmed",
        "accessDate": "2026-10-25",
        "fullCitation": "Jack Hylton und sein Orchester, refrain sung by Siegfried Arno. “Das verliebte Orchester.” Fox-trot; label credits text and music to Fritz Rotter and Dr. B. Kaper. Electrola E.G. 2259, matrix 60-1496; recorded 11 March 1931, issue date not established. Shellac disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube.",
        "researchNote": "The Jack Hylton website’s MP3 Downloads discography lists this title, Electrola EG-2259 and Siegfried Arno, with 11/03/31 in the “Recording Date” column. The structured date therefore identifies the session on 11 March 1931, not the commercial issue date. The label supplies the matrix and printed credits; the independent listing does not specify a take. The uploader’s general statement that Electrola issued the disc in 1931 remains distinct from this session evidence.",
        "researchNoteType": "discographic_note",
        "additionalLinks": [
            {
                "label": "Jack Hylton — MP3 Downloads discography, “Das Verliebte Orchester”",
                "url": "https://www.jackhylton.com/mp3-downloads",
                "role": "catalogue_entry"
            }
        ]
    },
    "SRC0724": {
        "date": "1930-10",
        "dateRole": "described_item",
        "dateQualifier": "uncertain",
        "accessDate": "2026-10-25",
        "researchNote": "The Derby 20 cm discography at Lotz-Verlag independently lists Karkoff-Orchester mit Refraingesang, “In der Laubenkolonie”, Derby 5710-A, with the incomplete matrix designation “..6 RB2” and “1930-10-?” in its “Datum” column. The structured date preserves this month-level discographic dating without inventing a day or treating the column as a separately established commercial issue date. The table does not label this row’s date as mechanical copyright; that wording appears on neighbouring rows and is not carried over. Its incomplete matrix designation is not expanded. The uploader’s 1930 issue dating remains an upload statement, not independent proof of first publication.",
        "researchNoteType": "discographic_note",
        "additionalLinks": [
            {
                "label": "Lotz-Verlag — Derby 20 cm discography, 5710-A",
                "url": "https://www.lotz-verlag.de/Derby-20.htm",
                "role": "catalogue_entry"
            }
        ],
        "fullCitation": "Karkoff-Orchester mit Refraingesang. “In der Laubenkolonie.” Foxtrot from the sound film In der Laubenkolonie; label credit “(Kaper)”. Derby D.O. 5710 a, marked “Nur für Deutschland”, n.d. Shellac disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube."
    },
    "SRC0719": {
        "date": "1932-05",
        "dateRole": "recording",
        "dateQualifier": "reported",
        "dateDisplay": "c. May 1932",
        "accessDate": "2026-10-25",
        "fullCitation": "Ilja Livschakoff Tanzorchester. “Ein Lied aus meiner Heimat.” Slowfox from Melodie der Liebe. YouTube transfer; the uploader identifies Polydor 24604, matrix 4735 BD VII, and reports a Berlin recording session around May 1932.",
        "researchNote": "The catalogue number, matrix, performer and film identification are supplied by the uploader; they have not been independently corroborated for this transfer. The description explicitly says “Aufnahme: Berlin, ca. Mai 1932”, so the source date describes an approximate reported recording session, not an issue date. Other recordings of the song, including the Rosvaenge/Livschakoff master 4733 ½ BD, are not evidence for matrix 4735 BD VII.",
        "researchNoteType": "discographic_note"
    },
    "SRC0729": {
        "date": "1935-05-06",
        "dateRole": "recording",
        "dateQualifier": "confirmed",
        "accessDate": "2026-10-25",
        "fullCitation": "Ted Fio Rito and his orchestra. “Love Song of Tahiti.” Brunswick 7446, matrix C971; recorded 6 May 1935. YouTube transfer published by Croonr1, who identifies the vocals as Muzzy Marcellino with The Debutantes and credits music to Bronislaw Kaper and Walter Jurmann and words to Gus Kahn.",
        "researchNote": "The independent Brunswick 7300 Series Numerical Listing identifies “Love Song of Tahiti” by Ted Fio Rito on Brunswick 7446, matrix C971, dated 6 May 1935; the coupled side is “You’re All I Need”, matrix C972, from the same session. The source date describes that recording session, not the commercial issue date. The upload identifies the transfer as Brunswick 7446, but does not show the label; the particular transferred copy and take remain unverified. The vocal identification and authorship statement are supplied by the uploader, not by that numerical listing.",
        "researchNoteType": "discographic_note",
        "additionalLinks": [
            {
                "label": "Brunswick 7300 Series Numerical Listing — 7446, matrix C971",
                "url": "https://www.78discography.com/BRN7300.htm",
                "role": "additional_evidence"
            }
        ]
    },
    "SRC0746": {
        "dateRole": "described_item",
        "dateQualifier": "reported",
        "accessDate": "2026-10-25",
        "fullCitation": "Melody Gents with orchestra. “Wer weint heut’ aus Liebe Tränen?” Slowfox from Ehe mit beschränkter Haftung. YouTube transfer; the uploader identifies Gloria G.O. 10197 b, matrix Bi 412, and gives 1932 in the video title.",
        "researchNote": "The label, matrix, performer and authorship details are supplied by the uploader; they have not been independently corroborated for this transfer. The description credits music to Dr. Bronislaw Kaper and Walter Jurmann and words to Fritz Rotter. The year 1932 appears in the video title without specifying a recording or issue date, so it is retained only as a reported date of the described item. Entries for other performers and matrices of this song are not used to date or identify this transfer.",
        "researchNoteType": "discographic_note"
    },
    "SRC0755": {
        "date": "1932-03",
        "dateRole": "recording",
        "dateQualifier": "reported",
        "dateDisplay": "c. March 1932",
        "accessDate": "2026-10-25",
        "fullCitation": "Marek Weber und sein Orchester. “Ganz ohne Liebe wär’ das Leben so bescheiden.” Fox-trot with refrain vocal; music by Walter Jurmann and Bronislaw Kaper, words by Fritz Rotter. Electrola E.G. 2532. YouTube transfer by Underlabelcrack; the uploader reports matrix OD 879-2 and a Berlin recording session around March 1932.",
        "researchNote": "R. Pfau’s Lexikon der deutschen Tanzmusik, part 3, printed p. 321, independently lists this title, its Kaper–Jurmann/Rotter credit, the film Skandal in der Parkstraße and “EG 2532 Marek Weber”. Its general year 1932 is not a separately documented issue or session date. The approximate March 1932 Berlin session and matrix OD 879-2 remain uploader-supplied. The uploader tentatively names the refrain singer as “John Hendrick”; this is not treated as a confirmed singer identification. The particular transferred pressing and take remain unverified.",
        "researchNoteType": "discographic_note",
        "additionalLinks": [
            {
                "label": "R. Pfau, Lexikon der deutschen Tanzmusik, part 3, p. 321",
                "url": "https://www.db-thueringen.de/servlets/MCRFileNodeServlet/dbt_derivate_00060559/Pfau_Lexikon_deutschen_Tanzmusik_003.pdf#page=54",
                "role": "additional_evidence"
            }
        ]
    },
    "SRC0758": {
        "dateRole": "recording",
        "dateQualifier": "reported",
        "accessDate": "2026-10-25",
        "fullCitation": "Bernard Etté und sein Orchester, refrain by Kurt Mühlhardt. “Sagen kleine Mädels ‘nein’.” Waltz from Korvettenkapitän; label credit “Dr. Kaper / Rotter / Robinson”. Kristall, order no. 3098, n.d. YouTube transfer by Wunschkonzert.",
        "researchNote": "The label image accompanying the upload reads “Best.-Nr. 3098” and names Bernard Etté und sein Orchester and refrain singer Kurt Mühlhardt. It corrects the upload description’s “Kristall 78N”; the earlier claim that no label was shown was incorrect. SRC0004 shows the other title on the same catalogue issue, also numbered 3098; this does not establish that the transfers came from the same physical copy. The description’s “Aufnahme 1930” remains a reported recording year, not a separately established issue date.",
        "researchNoteType": "discographic_note",
        "title": "Sagen kleine Mädels “nein” — Kristall 3098",
        "shortCitation": "Kristall 3098, “Sagen kleine Mädels ‘nein’”",
        "slug": "src0758-kristall-3098-sagen-kleine-madels-nein",
        "date": "1930"
    },
    "SRC0633": {
        "date": "1930",
        "dateRole": "issue",
        "dateQualifier": "after",
        "dateDisplay": "[post 1930]",
        "researchNote": "The Biblioteka Narodowa publication statement supplies only [post 1930], meaning after 1930, and gives no exact issue or recording date. The structured date preserves that catalogue boundary; it does not assert an issue in 1933. Dates assigned to the film, a recording session or a different pressing are not substituted for the dating of Odeon O. 236842.",
        "researchNoteType": "date_assessment",
        "accessDate": "2026-10-25"
    },
    "SRC0773": {
        "title": "Fiesta (Bianca) — Ultraphon 20040 A",
        "fullCitation": "National Museum, Prague, Discographic Database. “Fiesta (Bianca),” rumba. Efim Schachmeister, conductor, with jazz orchestra; music by W. G. Samuels and L. Whitcup. Ultraphon 20040 A, matrix 18145. One 25 cm standard gramophone disc. Individual recording entry.",
        "publication": "Ultraphon",
        "dateRole": "issue",
        "dateQualifier": "unknown",
        "primaryUrl": "https://diskografie.nm.cz/nahravky/fiesta-bianca/",
        "researchNote": "The individual recording entry identifies Ultraphon 20040 A, matrix 18145, but supplies no recording or issue date. Its note places the orchestral recording in Ultraphon catalogues of 1932–1933; those years describe catalogue appearance, not a dated session or an established first issue. No year is inferred from that note.",
        "researchNoteType": "discographic_note",
        "accessDate": "2026-10-25",
        "additionalLinks": [
            {
                "label": "National Museum — L. Whitcup index",
                "url": "https://diskografie.nm.cz/osoby/l-whitcup/",
                "role": "alternate_access"
            }
        ]
    },
    "SRC0829": {
        "dateRole": "issue",
        "dateQualifier": "unknown",
        "researchNote": "The DNB catalogue supplies no recording or issue date. Its MARC record has no publication-date subfield in field 264 and no historical year in field 008; the film association does not establish a date for this pressing. The label credit is given by the catalogue as “Alfred Beres mit Orchester, Refraingesang: Eric Helgar”, with the generic description “Tanzorchester mit Refraingesang”. The same library holds a second issue of the song, Decca F 40007, matrix FGB 2355, played by The Rhythm Maniacs with a German refrain sung by Leo Mond and coupled with “In meinem Herzen ist nur Platz für eine”.",
        "researchNoteType": "discographic_note",
        "accessDate": "2026-10-25"
    },
    "SRC0008": {
        "date": "1937-06-08",
        "dateRole": "recording",
        "dateQualifier": "confirmed",
        "researchNote": "The Internet Archive item metadata gives 1937-06-08. The Dooji Collection discography independently identifies Master MA 137, matrix M519-1, with the New York session of 8 June 1937. The structured date describes that recording session, not an independently established commercial release date.",
        "researchNoteType": "discographic_note",
        "accessDate": "2026-10-25",
        "additionalLinks": [
            {
                "label": "Dooji Collection — Master MA 137, matrix M519-1",
                "url": "https://ellingtonweb.ca/Hostedpages/DoojiCollection/DoojiCollection-1937-38.html",
                "role": "catalogue_entry"
            }
        ]
    },
    "SRC0705": {
        "date": "1934-10",
        "dateRole": "recording",
        "dateQualifier": "confirmed",
        "researchNote": "Phonobase explicitly gives the recording date as 1934-10-xx; the structured date therefore retains month precision and does not identify the disc’s commercial issue date. The transfer date is separately given as 4 February 2023. The record additionally states that Tino Rossi created the song in 1934, that Mireille, Guy Berry and Priolet also performed it, and that Coda / Heugel published it in Paris in 1934.",
        "researchNoteType": "discographic_note",
        "accessDate": "2026-10-25"
    },
    "SRC0744": {
        "date": "1931-03-15",
        "dateRole": "recording",
        "dateQualifier": "confirmed",
        "fullCitation": "Mitja Nikisch und sein Orchester, refrain sung by Paul Dorn. “Ich steh’ im Schnee und wart’ auf Dich.” Foxtrot from Die grosse Attraktion. Electrola E.G. 2228, matrix OD106-2, recorded Berlin, 15 March 1931; also issued as His Master’s Voice AM 3411 and HMV R 14602. Electrola label and title lists at musiktiteldb.de, following the Discographie der deutschen Tanzmusik, vol. 4.",
        "researchNote": "The discographic entry assigns both words and music to Bronisław Kaper. Hofmeister (February 1931, p. 35) registers the song under Kaper with words by Fritz Rotter and Armin Robinson; the discographic lyric credit is not used to replace that. The Electrola label list gives 15 March 1931 in its recording-date column and leaves the release-date column empty. HMV R 14602 is a parallel record issue, not a U.S. copyright renewal identifier.",
        "researchNoteType": "evidence_note",
        "accessDate": "2026-10-25"
    },
    "SRC0750": {
        "date": "1935-03-23",
        "dateRole": "recording",
        "dateQualifier": "confirmed",
        "researchNote": "The title-list entry gives Los Angeles, 23 March 1935, as the recording place and date and leaves the release-date column empty; the structured date therefore describes the session, not the issue of Decca 466. The entry credits Kaper and Jurmann for the music and Harold Adamson for the words. That combination supports identifying this record as the English-language version of the song written for Ein Lied für dich.",
        "researchNoteType": "evidence_note",
        "accessDate": "2026-10-25"
    },
    "SRC0753": {
        "date": "1931-09-15",
        "dateRole": "recording",
        "dateQualifier": "confirmed",
        "researchNote": "The filmed label confirms the title and authorship credit. The uploader supplies the Berlin and film context; the catalogue number and session date are independently supplied by musiktiteldb.de. Its title-list entry dates the Berlin recording to 15 September 1931 and leaves the release-date column empty. The structured date identifies that session, not the commercial issue of Kristall 3229.",
        "researchNoteType": "discographic_note",
        "additionalLinks": [
            {
                "label": "musiktiteldb.de — Kristall 3229 session entry",
                "url": "http://musiktiteldb.de/musiktitel/titel_I_Want_To-Ich_trink.html",
                "role": "catalogue_entry"
            }
        ]
    },
    "SRC0760": {
        "date": "1931-04-29",
        "dateRole": "recording",
        "dateQualifier": "confirmed",
        "researchNote": "The title-list entry gives 29 April 1931 as the recording date and leaves the release-date column empty. The structured date therefore identifies the session, not the commercial issue of Gloria G.O. 10155. No publicly accessible transfer of this disc was located during the recording-link audit.",
        "researchNoteType": "discographic_note",
        "accessDate": "2026-10-25"
    },
    "SRC0767": {
        "date": "1930-03",
        "dateRole": "recording",
        "dateQualifier": "confirmed",
        "fullCitation": "Stare Melodie. “O tym już wróble świergocą na dachu.” Tadeusz Faliszewski with the orchestra of Towarzystwo Syrena Record; recording dated March 1930 in the listening-entry metadata. Syrena-Electro 3461, matrix 20876.",
        "researchNote": "The Stare Melodie listening entry dates the recording to March 1930. An embedded YouTube title instead gives 1929; the site’s editor explicitly corrects that year to March 1930 in the comments. The structured date follows the site’s catalogue entry and identifies the recording, not a separately established issue date.",
        "researchNoteType": "date_assessment",
        "accessDate": "2026-10-25"
    },
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
        "fullCitation": "Henry Garat, vocal; orchestra conducted by Bronisław Kaper. “Pourvu qu’on ait vingt ans,” from Une femme au volant. Music by Bronisław Kaper and Walter Jurmann; words by Louis Poterat. Salabert 3384, 78 rpm disc; recorded Paris, 7 November 1933. Digital transfer from David Silvestre’s private collection, published by lysgauty1 on YouTube, video JA57rCoKoyI. Gérard Roig, “Discographie d’Henry Garat,” Phonoscopies 5 (January 1994): 10–11, lists matrix SS 1729 and the coupled side “Ninon, quand tu me souris,” matrix SS 1730, as Salabert 3384.",
        "repository": "YouTube / private collection of David Silvestre",
        "date": "1933-11-07",
        "dateRole": "recording",
        "dateQualifier": "confirmed",
        "researchNote": "Roig’s discography places SS 1729 under the Paris session heading of 7 November 1933, continuing onto the next printed page with the coupled side SS 1730. It also mentions a dated test pressing of SS 1729B. The date therefore describes a recording session, not the commercial release of Salabert 3384; no particular take is assigned to the YouTube transfer from that note alone.",
        "researchNoteType": "discographic_note",
        "additionalLinks": [
            {
                "label": "Phonoscopies 5 — Garat discography, printed pp. 10–11",
                "url": "https://www.old.archeophone.org/Phonoscopies/Phonoscopies-005.pdf#page=6",
                "role": "catalogue_entry"
            }
        ]
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
        "fullCitation": "Eric Harden’s danseorkester, refrain sung by Carljohann Volbach. “Wie gern möcht’ ich dich verwöhnen.” From the sound film Melodie der Liebe; catalogue number D 4431, matrix Bi 644, n.d. Digital transfer published by the Internet Archive from the 78 rpm collection of Leif Druedahl.",
        "researchNote": "The Internet Archive metadata supplies catalogue number D 4431 and matrix Bi 644 but no label or date; only an audio transfer is supplied, not a photograph of the physical label. The title-list entry for Gloria G.O. 10303 identifies the same title, performers and matrix, dates the master to Berlin, studio 4, on 11 June 1932 and gives November 1932 as the German issue date. The structured date identifies the shared recording session. Neither November 1932 nor the year of the film is assigned as the issue date of D 4431; that pressing’s label and issue date remain unestablished. The Danish performer wording is transcribed from the Internet Archive metadata.",
        "researchNoteType": "discographic_note",
        "shortCitation": "D 4431, “Wie gern möcht’ ich dich verwöhnen” (master recorded 1932)",
        "date": "1932-06-11",
        "dateRole": "recording",
        "dateQualifier": "confirmed",
        "accessDate": "2026-10-25",
        "additionalLinks": [
            {
                "label": "musiktiteldb.de — Bi 644 session and Gloria G.O. 10303 issue",
                "url": "http://musiktiteldb.de/musiktitel/titel_wi-wirf.html",
                "role": "catalogue_entry"
            }
        ],
        "organizationIds": [
            "ORG067",
            "ORG148"
        ],
        "contributionIds": [
            "CON-S060-C-P009",
            "CON-S060-C-P077",
            "CON-S060-L-P020",
            "CON-S060-P-ORG148"
        ]
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
    "SRC0694": "Ben Berlin und sein Orchester, with German refrain vocal. “Auf Wiederseh’n, Herr Doktor!” Fox-trot; label credit “(Rotter-Kaper)”. Grammophon, electrical recording, catalogue B 51823, order no. 23042, side 2, n.d. Shellac disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube.",
    "SRC0695": "Ben Berlin und sein Orchester. “Nimm diesen Strauß Vergißmeinnicht.” Fox-trot; label credits “(Kaper – Rotter)” and “(Verlag: Roehr A.-G., Berlin)”. Grammophon, electrical recording, Polyfar “R” Orchester series, catalogue B 50959, order no. 22222, side 2, n.d. Shellac disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube.",
    "SRC0716": "Saxophon Orchester Dobbri, vocal by Max Mensing. “Was macht jede Nacht so ein kleines Baby in der Bar.” Slow fox; label credit “Fritz Rotter & Dr. B. Kaper”. Parlophone 80.235, matrix B 38451, n.d. Shellac disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube.",
    "SRC0717": "Marek Weber und sein Orchester, dance orchestra with refrain vocal. “Margarete, wander mit mir ….” Fox-trot; label credits music and text to Fritz Rotter and Dr. B. Kaper. Electrola E.G. 2406, matrix 60-1740, n.d. Shellac disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube.",
    "SRC0004": "Bernard Etté und sein Orchester, refrain by Kurt Mühlhardt. “Blaue Jungs von der Marine.” Marschlied from Korvettenkapitän; label credit “Dr. Kaper / Rotter / Robinson”. Kristall, order no. 3098, n.d. YouTube transfer by Wunschkonzert.",
    "SRC0725": "Austin Egen, accompanied by the Odeon-Tango-Orchester. “Ich weiß ein kleines Café.” Tango; label credits Dr. B. Kaper and Austin Egen, with words by Fritz Rotter. Odeon O-11439 a, matrix Be 9409; issued May 1931. Label filmed in the YouTube upload by Ilja Livschakoff.",
    "SRC0782": "Orchestra Mascotte. “Moonlight at Sanssouci.” Waltz; label credit “Rotter–Kaper”. Parlophone A3436, matrix Be 9615, n.d. Australian pressing, labelled “Made in Australia for Parlophone Co. Ltd.” Disc label photograph and digital transfer published by the Great 78 Project, Internet Archive.",
    "SRC0811": "“Blue Venetian Waters”, attributed to Allan Jones. Audio transfer uploaded by Archiveradio1930 to YouTube; the title describes it as a 1937 broadcast.",
    "SRC0710": "Marek Weber und sein Orchester, refrain credited as Leo Moll. “Signorina aus Brioni.” Tango; label credits Fritz Rotter and Dr. Kaper for music and text. Electrola E.G. 2400, n.d. Shellac disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube.",
    "SRC0712": "Tanzorchester J. Geiger, refrain sung by Hans Rotter. “Du bist verrückt, mein Schatz, du denkst an Liebe.” Lied und foxtrot; label credits music and text to Fritz Rotter and Dr. B. Kaper. Novaphon Electro Record B 4051, made in Austria, n.d.; matrix 2647 identified in Discographie der österreichischen Populärmusik. Flexible disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube.",
    "SRC0718": "Jack Hylton und sein Orchester, refrain sung by Siegfried Arno. “Das verliebte Orchester.” Fox-trot; label credits text and music to Fritz Rotter and Dr. B. Kaper. Electrola E.G. 2259, matrix 60-1496; recorded 11 March 1931, issue date not established. Shellac disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube.",
    "SRC0724": "Karkoff-Orchester mit Refraingesang. “In der Laubenkolonie.” Foxtrot from the sound film In der Laubenkolonie; label credit “(Kaper)”. Derby D.O. 5710 a, marked “Nur für Deutschland”, n.d. Shellac disc, Radiomuseum Hardthausen / Schallarchiv; filmed-label transfer on YouTube.",
    "SRC0715": "“Ich hab’ heut grad Geburtstag.” YouTube audio reference published by Jan van den Belt on 24 June 2011. The upload identifies Theo Mackeben mit seinem Jazz-Orchester and Walter Jurmann as refrain singer.",
    "SRC0727": "“Ich steh im Schnee und wart auf dich.” YouTube audio reference published by Brillantspecial, presented by the uploader as Gloria-Tanz-Orchester mit Refraingesang.",
    "SRC0738": "“Zgaś lampę!” Shimmy. YouTube audio reference published by jurek46pink; the upload identifies Henryk Gold and his ensemble.",
    "SRC0790": "“Du liebst mich nicht mehr.” Slow-Fox. Digital transfer published on YouTube by Radiomuseum Hardthausen; the upload identifies Tanz-Orchester Dajos Béla, Odeon O-11667 (1932), and a music credit to “Bob Henders”.",
    "SRC0713": "Marek Weber und sein Orchester, vocal by John Hendrik. “Du bist in meinem Leben die erste Sensation.” Tango. Digital transfer on YouTube; the uploader identifies Electrola E.G. 2508 and gives the year as 1932.",
    "SRC0719": "Ilja Livschakoff Tanzorchester. “Ein Lied aus meiner Heimat.” Slowfox from Melodie der Liebe. YouTube transfer; the uploader identifies Polydor 24604, matrix 4735 BD VII, and reports a Berlin recording session around May 1932.",
    "SRC0729": "Ted Fio Rito and his orchestra. “Love Song of Tahiti.” Brunswick 7446, matrix C971; recorded 6 May 1935. YouTube transfer published by Croonr1, who identifies the vocals as Muzzy Marcellino with The Debutantes and credits music to Bronislaw Kaper and Walter Jurmann and words to Gus Kahn.",
    "SRC0730": "Jan Kiepura with the Odeon-Künstler-Orchester under Dr. Weissmann. “Ninon”, from Ein Lied für dich; music by Walter Jurmann and Dr. Bronislaw Kaper, words by Fritz Rotter and Ernst Marischka. YouTube transfer published by 78Upm; the upload describes an Odeon red-label issue and gives the year as 1933.",
    "SRC0735": "Bernhard Etté mit seinem Tanz-Orchester, vocal by Wolfgang Schmidt. “Adieu es ist zu schön um wahr zu sein.” Tango by Walter Jurmann, Bronislaw Kaper and Fritz Rotter from Abenteuer am Lido. YouTube transfer published by Radiomuseum Hardthausen; the upload dates the recording to 1933.",
    "SRC0746": "Melody Gents with orchestra. “Wer weint heut’ aus Liebe Tränen?” Slowfox from Ehe mit beschränkter Haftung. YouTube transfer; the uploader identifies Gloria G.O. 10197 b, matrix Bi 412, and gives 1932 in the video title.",
    "SRC0755": "Marek Weber und sein Orchester. “Ganz ohne Liebe wär’ das Leben so bescheiden.” Fox-trot with refrain vocal; music by Walter Jurmann and Bronislaw Kaper, words by Fritz Rotter. Electrola E.G. 2532. YouTube transfer by Underlabelcrack; the uploader reports matrix OD 879-2 and a Berlin recording session around March 1932.",
    "SRC0758": "Bernard Etté und sein Orchester, refrain by Kurt Mühlhardt. “Sagen kleine Mädels ‘nein’.” Waltz from Korvettenkapitän; label credit “Dr. Kaper / Rotter / Robinson”. Kristall, order no. 3098, n.d. YouTube transfer by Wunschkonzert.",
    "SRC0707": "Marek Weber und sein Orchester, refrain sung by Austin Egen. “Tränen weint jede Frau so gern.” Tango. Digital transfer on YouTube; the upload identifies His Master’s Voice / Electrola and gives the year as 1929.",
    "SRC0759": "Orkiestra taneczna. “San Francisco.” Foxtrot. Digital transfer on YouTube; the upload identifies Syrena Record, gives the year as 1937 and credits Bronisław Kaper and Walter Jurmann with music and Emanuel Schlechter with Polish words.",
    "SRC0740": (
        "Ted Fio Rito and his orchestra, vocal chorus by Stanley Hickman. “Blue Venetian Waters”, from A Day at the Races; words and music by Gus Kahn, Bronislaw Kaper and Walter Jurmann. YouTube audio reference uploaded by RobinsRareRecordings; recording dated 1937 in the upload description."
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
        "researchNote": "The BnF catalogue supplies [1934] as the issue date, reconstructed from Répertoire phonographique, 3e supplément annuel 1934. The brackets indicate a catalogue-supplied date, not a date transcribed from the disc. This bibliographic dating is independent of the film’s release chronology.",
        "researchNoteType": "discographic_note",
        "accessDate": "2026-10-25"
    },
    "SRC0714": {
        "date": "2000",
        "dateRole": "issue",
        "dateQualifier": "confirmed",
        "fullCitation": "The Jack Hylton Orchestra, directed by Jack Hylton, with Jack Jackson, Philippe Brun and Leo Vauchant. “Herr Lehmann, Herr Lehmann, Was Macht Die Frau Gemahlin In Marienbad?” On Hot Hylton 1926–1930. Retrieval RTR 79024, CD compilation, first issued 2000; distributed by Challenge Records International. YouTube art track supplied by The Orchard Enterprises and published 10 February 2015.",
        "researchNote": "The date identifies the compilation’s first issue in 2000, not its digital publication or a historical recording session. Challenge Records identifies the format as CD, states “First release in 2000” and separately lists 21 November 2005 as the release date of its catalogue product. The YouTube access copy was published on 10 February 2015. The reissue metadata cited here does not identify the label, catalogue number or matrix of the original disc.",
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
        "researchNote": "The uploader dates the issue to 1932 and associates the side with Hochzeitsreise zu dritt. The Odeon label list identifies the matching title and performers as O-11768, side B, matrix Be 10147, with 1933 in its general year column; its separate release-date column is empty. The filmed label carries no year. The structured date retains the uploader’s 1932 as disputed, not confirmed: the catalogue’s 1933 does not by itself establish a precise issue or session date.",
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
        "researchNote": "The BnF publication statement is “S.l. : s.n., s.d.” and supplies no issue year. The film’s 1934 release does not establish the disc’s release date. The Internet Archive collection associates DF 1622 with 1934 without distinguishing recording from issue; the specialist discography Tino Rossi – Le Site instead places the issue in January 1935. No year is entered as a confirmed or inferred BnF issue date. The catalogue lists matrices CL 5068 and CL 5093 but does not assign each matrix to a title in the displayed metadata, so no side-level matrix assignment is inferred here.",
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
        and source_id not in RECORDING_FIELDS
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
