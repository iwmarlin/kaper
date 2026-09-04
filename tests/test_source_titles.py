import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
FILE_NAME_PREFIXES = ("File:", "File :", "Datei:", "Fichier:", "Archivo:")


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

    def test_the_copyright_catalogue_is_titled_one_way(self):
        # The Catalog of Copyright Entries was titled three ways: the house form
        # "Catalog of Copyright Entries: “X”" on 57 records, "CCE 1930 - X" on
        # ten, and "Catalog of Copyright Entries - X" on two. The house form is
        # not a preference — it is derivable, because the same record's short
        # citation already states the work in the same words and the same marks.
        #
        # Two records stay out and are named here rather than left to drift.
        # SRC0212 is filed as sheet music, not as a catalogue entry; SRC0689 is
        # cited by entry number instead of by title, so there is no quoted work
        # to lift. Both would have to be retitled by hand, from the volume.
        exempt = {"SRC0212", "SRC0689"}
        wrong = []
        for record in read("sources.json"):
            if record["id"] in exempt:
                continue
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
