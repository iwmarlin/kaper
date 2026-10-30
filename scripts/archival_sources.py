"""Individually verified archival source descriptions; no inferred entities."""
from copy import deepcopy

# These fields follow inspected document images and explicitly scoped existing
# archive consultations, not a type-wide rule that rewrites all archival records.
REVIEWED_ARCHIVAL_FIELDS = {
    "SRC0012": {
        "title": "Bronisław Kaper — baptism entry no. 482, St Alexander’s parish, Warsaw, 1920",
        "shortCitation": "St Alexander’s parish, Warsaw, baptism entry no. 482 (1920)",
        "fullCitation": "Roman Catholic parish of St Alexander, Warsaw. Birth/baptism register, 1920 (U-1920), entry no. 482, Bronisław Kaper. Digitized scan 479–482, record set id3-sy150. Metryki.Genealodzy.pl / Polskie Towarzystwo Genealogiczne.",
        "primaryUrl": "https://metryki.genealodzy.pl/index.php?op=pg&id=3&sy=150&kt=1&plik=479-482.jpg",
        "additionalLinks": [
            {
                "label": "Parish register U-1920 — record set id3-sy150",
                "url": "https://metryki.genealodzy.pl/id3-sy150",
                "role": "collection_record"
            }
        ],
        "accessDate": "2026-10-26",
        "researchNote": "Entry number 482 is visible on the reproduced document; 479–482 identifies the digitized scan containing it. The record describes an adult baptism in 1920 and also records Kaper’s earlier birth. The register year is not his year of birth.",
        "researchNoteType": "evidence_note"
    },
    "SRC0110": {
        "fullCitation": "Archiwum Uniwersytetu Warszawskiego. Bronisław Kaper student file, RP 6854. Archival file; consulted in the archive.",
        "researchNote": "This is an aggregate file citation, not an item-level portrait record. The materials already documented from the file include portraits, matriculation and study records, and the police certificate of 21 April 1920 recording Kaper’s religion as Mosaic. The linked student record-book reproduction is identified as fols. 38–39. The structured year 1920 refers to the documented student materials, not an independently established date span for the complete file.",
        "researchNoteType": "evidence_note"
    },
    "SRC0313": {
        "title": "Marriage-register name index, Standesamt Berlin I — Kaper and Sirot, 1927",
        "shortCitation": "Standesamt Berlin I, marriage-register name index, 1927, no. 273 — Kaper / Sirot",
        "fullCitation": "Landesarchiv Berlin, P Rep. 800, Nr. 284. Namensverzeichnis Heiratsregister 1927, Standesamt Berlin I. Alphabetical entries for Bronisław Kaper and Eleonora Sirot, both referring to marriage-register no. 273, 30 June 1927; PDF pp. 15 and 28.",
        "primaryUrl": "https://content.landesarchiv-berlin.de/labsa/pdf/P_Rep_800_0284.pdf#page=15",
        "dateRole": "described_item",
        "dateDisplay": "30 June 1927 (marriage indexed)",
        "accessDate": "2026-10-26",
        "researchNote": "The linked 37-page PDF is a marriage-register name index, not the full marriage act. Its cover identifies Standesamt Berlin I, P Rep. 800, Nr. 284, and 1927. The Kaper entry is on PDF p. 15 and the Sirot entry on p. 28; both show 30 June and register no. 273. The structured date describes the marriage indexed, not an independently dated compilation of the index. The archive’s official holdings list identifies P Rep. 800 as the former Berlin I district registry for Mitte. It must not be confused with the separate foreign-registry function of Standesamt I in Berlin. M060 and M061 reproduce cropped index entries, not extracts from the full marriage act.",
        "researchNoteType": "verification_note",
        "additionalLinks": [
            {
                "label": "Landesarchiv Berlin — official registry holdings (P Rep. 800, Berlin I)",
                "url": "https://landesarchiv-berlin.de/wp-content/uploads/2021/08/StandesaemterBerlin_Bestaende.pdf",
                "role": "contextual_reference"
            }
        ]
    },
    "SRC0678": {
        "date": "1941-05-01",
        "dateEnd": "1942-04-30",
        "dateRole": "described_item",
        "dateDisplay": "1 May 1941–30 April 1942 (donation period)",
        "accessDate": "2026-10-26",
        "primaryUrl": "https://kuenste-im-exil.de/KIE/Content/DE/Bilder/Themen/european-film-fund.html",
        "additionalLinks": [
            {
                "label": "Digitized donor list — first sheet",
                "url": "https://kuenste-im-exil.de/KIE/Content/DE/Bilder/Themen/european-film-fund.jpg?__blob=zoom&v=1",
                "role": "facsimile"
            },
            {
                "label": "European Film Fund — exhibition context",
                "url": "https://kuenste-im-exil.de/KIE/Content/DE/Themen/european-film-fund.html",
                "role": "contextual_reference"
            }
        ],
        "researchNote": "The reproduced heading gives donations from members for 1 May 1941 to 30 April 1942. These are the dates covered by the list, not a separately established creation date. The visible first sheet includes Kaper at $120 and Kohner at $213 and ends with a carried-forward total; the institutional extended description identifies an alphabetical list of 69 people. No document-creation date is inferred from the reporting period.",
        "researchNoteType": "date_assessment"
    }
}

def normalize_archival_source(source):
    fields = REVIEWED_ARCHIVAL_FIELDS.get(source.get("id"))
    if fields:
        source.update(deepcopy(fields))

