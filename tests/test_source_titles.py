import json
import re
import unicodedata
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
FILE_NAME_PREFIXES = ("File:", "File :", "Datei:", "Fichier:", "Archivo:")


def fold(value):
    """Strip a title down to what distinguishes it for a reader: case, accents,
    apostrophes, brackets and hyphens all go, because none of them is how anyone
    tells two records apart."""
    return re.sub(r"[^a-z0-9]+", "", unicodedata.normalize("NFKD", value.lower()))


def read(name):
    return json.loads((PUBLIC / name).read_text(encoding="utf-8"))["records"]


def portrait_media_ids():
    return {
        item["id"]
        for item in read("media.json")
        if item.get("category") == "portrait"
    }


class SourceTitleTests(unittest.TestCase):
    """A source title names the thing the source is. Twenty-nine portrait
    sources were called things like "File:Smzeisle.jpg", which names the upload
    and tells a reader nothing about who is in the picture — while the file name
    itself was already in the URL or in the citation."""

    def test_no_title_is_a_file_name(self):
        offenders = [
            f"{record['id']}: {record['title']}"
            for record in read("sources.json")
            if (record.get("title") or "").startswith(FILE_NAME_PREFIXES)
        ]
        self.assertEqual(offenders, [], "a source is titled with the name of a file")

    def test_a_portrait_source_names_the_sitter(self):
        # The archive's own majority form, and the only one derivable from the
        # record without inventing anything: the person is on the record, and
        # the media category says the picture is of them.
        portraits = portrait_media_ids()
        people = {item["id"]: item["displayName"] for item in read("people.json")}
        wrong = []
        for record in read("sources.json"):
            media = [m for m in record.get("mediaIds") or [] if m in portraits]
            linked = [p for p in record.get("personIds") or [] if p in people]
            if not media or len(linked) != 1:
                continue
            title = record.get("title") or ""
            if title.endswith("— portrait") and not title.startswith(people[linked[0]]):
                wrong.append(f"{record['id']}: {title!r} does not open with {people[linked[0]]!r}")
        self.assertEqual(wrong, [], "a portrait title names someone other than the sitter")

    def test_no_two_sources_share_a_title(self):
        # Thirty-seven records were sharing eighteen titles, every one of them a
        # genuinely different source: three reviews of the same recital in three
        # papers, a film entry and the sheet music for songs from that film, a
        # record and the sheet music of the same song. The distinguishing fact
        # was already on each record, in its short citation, its publication or
        # the works it links.
        #
        # Folded rather than compared literally, because two of the eighteen
        # were invisible to a literal comparison and to the audit that used one:
        # "[Mélodie d'amour]" against "Mélodie d'amour", and one label spelled
        # "Syrena-Grand-Record" against "Syrena Grand Record". A reader does not
        # tell two records apart by a bracket or a hyphen.
        seen = {}
        clashes = []
        for record in read("sources.json"):
            key = fold(record.get("title") or "")
            if key in seen:
                clashes.append(f"{seen[key]} and {record['id']}: {record['title']!r}")
            seen[key] = record["id"]
        self.assertEqual(clashes, [], "two sources cannot be told apart by their titles")

    def test_the_copyright_catalogue_is_titled_one_way(self):
        # The Catalog of Copyright Entries was titled three ways: the house form
        # "Catalog of Copyright Entries: “X”" on 57 records, "CCE 1930 - X" on
        # ten, and "Catalog of Copyright Entries - X" on two. The house form is
        # not a preference — it is derivable, because the same record's short
        # citation already states the work in the same words and the same marks.
        #
        # Two records were exempted here at first, on the grounds that there was
        # no quoted work to lift from their short citations, which cite by page
        # (SRC0212) and by entry number (SRC0689). That confused "the script
        # cannot derive it" with "the record does not say it". Both name the work
        # in their own full citations and in the works they link, so both were
        # retitled and the exemption is gone. SRC0212 needed more than a title:
        # it had been filed as sheet music while every field on it — creator,
        # publication, URL, registration number — belongs to the catalogue.
        wrong = []
        for record in read("sources.json"):
            short = record.get("shortCitation") or ""
            if not re.match(r"CCE \d{4}, ", short):
                continue
            title = record.get("title") or ""
            if not title.startswith("Catalog of Copyright Entries: "):
                wrong.append(f"{record['id']}: {title!r}")
        self.assertEqual(wrong, [], "a copyright-catalogue entry is titled off the house form")

    def test_a_descriptor_is_not_left_in_another_language(self):
        # Source titles describe in English; the thing being described keeps its
        # own language. Four records had the descriptor itself in German or
        # French — "— Filmplakat", "— notice de personne" — while their own
        # short citations said "poster" and "authority record".
        #
        # This tests the descriptor, never the name: "Max Colpet im Porträt" is
        # the published title of the article and stays exactly as printed, and
        # "serwis adresowy m.st. Warszawy" is the name of the city service.
        foreign = ("Filmplakat", "notice de personne", "Notice de personne")
        wrong = [
            f"{record['id']}: {record['title']!r}"
            for record in read("sources.json")
            if " — " in (record.get("title") or "")
            and record["title"].split(" — ", 1)[1] in foreign
        ]
        self.assertEqual(wrong, [], "a title's descriptor is not in English")

    def test_titles_are_not_empty_and_do_not_repeat_the_citation_wholesale(self):
        for record in read("sources.json"):
            title = (record.get("title") or "").strip()
            self.assertTrue(title, f"{record['id']} has no title")
            self.assertNotEqual(
                title, (record.get("fullCitation") or "").strip(),
                f"{record['id']}: the title is the whole citation",
            )


if __name__ == "__main__":
    unittest.main()
