import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/public/v1"

# The same pattern linkRecordIds in assets/site/core.js uses.
LINKED = re.compile(r"(?<![\w-])(SRC\d{4}|ORG\d{3}|W-[SFO]\d{3}|M\d{3}|P\d{3})(?![\w-])")
TABLES = {"SRC": "sources", "ORG": "organizations", "W-": "works", "M": "media", "P": "people"}
# Identifiers of records with no page of their own: a reader could neither
# follow nor look them up, so a note names the record in words or links its
# Work instead.
PAGELESS = re.compile(r"(?<![\w-])(S\d{3}|F\d{3}|O\d{3}|PNV\d{4}|TV\d{4}|CON-[\w-]+)(?![\w-])")

# The note fields a record page prints.
NOTE_FIELDS = {
    "sources": ("researchNote",),
    "contributions": ("scopeNote", "publicNote"),
    "films": ("attributionNote",),
}


def records(table):
    return json.loads((DATA / f"{table}.json").read_text(encoding="utf-8"))["records"]


class NoteRecordLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ids = {table: {r["id"] for r in records(table)} for table in TABLES.values()}
        cls.notes = [
            (record["id"], field, record[field])
            for table, fields in NOTE_FIELDS.items()
            for record in records(table)
            for field in fields
            if record.get(field)
        ]

    def test_every_linked_identifier_names_an_existing_record(self):
        for record_id, field, text in self.notes:
            for match in LINKED.finditer(text):
                identifier = match.group(1)
                table = next(t for prefix, t in TABLES.items() if identifier.startswith(prefix))
                with self.subTest(record=record_id, field=field, identifier=identifier):
                    self.assertIn(identifier, self.ids[table])

    def test_no_note_names_a_record_that_has_no_page(self):
        offenders = [
            f"{record_id}.{field}: {match.group(1)}"
            for record_id, field, text in self.notes
            for match in PAGELESS.finditer(text)
        ]
        self.assertEqual(offenders, [])

    def test_a_matrix_number_is_not_taken_for_a_media_record(self):
        source = next(s for s in records("sources") if s["id"] == "SRC0008")
        self.assertIn("M519-1", source["researchNote"])
        self.assertNotIn("M519", [m.group(1) for m in LINKED.finditer(source["researchNote"])])

    def test_the_renderer_links_notes_with_the_same_pattern(self):
        core = (ROOT / "assets/site/core.js").read_text(encoding="utf-8")
        self.assertIn(
            r"/(?<![\w-])(SRC\d{4}|ORG\d{3}|W-[SFO]\d{3}|M\d{3}|P\d{3})(?![\w-])/g", core
        )
        detail = (ROOT / "assets/site/record-detail-20260714.js").read_text(encoding="utf-8")
        for call in (
            "linkRecordIds(note)",
            "linkRecordIds(subtype.attributionNote)",
            "linkRecordIds(source.researchNote)",
        ):
            self.assertIn(call, detail)


if __name__ == "__main__":
    unittest.main()
