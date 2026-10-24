from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
sys.path.insert(0, str(ROOT / "scripts"))

from validate_public_export import SOURCE_PUBLIC_WORKFLOW_PATTERN  # noqa: E402


class SourceCitationEditorialLanguageTests(unittest.TestCase):
    def test_long_press_transcriptions_are_preserved_in_notes(self) -> None:
        sources = {record["id"]: record for record in json.loads((PUBLIC / "sources.json").read_text())["records"]}
        markers = {
            "SRC0841": ("Hoagy Carmichael, center", "Sidney Clare, left", "Fleishman Distilleries"),
            "SRC0842": ("opens at 8:45 tonight", "Valencia Ball Room", "does not distinguish which man is which"),
            "SRC0843": ("S/Sgt. Barry Sadler’s songs", "developing new talent and writers", "American Guild of Authors & Composers", "thirty-four years"),
            "SRC0850": ("Terry Shand, left", "Larry Shay, center", "Jimmie Eaton, right", "three or four thousand dollars", "sixty to two hundred and fifty dollars"),
        }
        for source_id, phrases in markers.items():
            with self.subTest(source=source_id):
                source = sources[source_id]
                self.assertEqual(source["sourceType"], "press_item")
                self.assertEqual(source["dateRole"], "publication")
                for phrase in phrases:
                    self.assertIn(phrase, source["researchNote"])
                    self.assertNotIn(phrase, source["fullCitation"])
                self.assertIn(source["publication"], source["fullCitation"])

    def test_stanicek_entries_keep_details_in_notes_not_citations(self) -> None:
        sources = {record["id"]: record for record in json.loads((PUBLIC / "sources.json").read_text())["records"]}
        details = {
            "SRC0288": ("Orchester Bernard Etté / Heinz Egon", "W 202", "Hermann Scheibenhofer", "Edition Karl Brüll"),
            "SRC0289": ("Roehr release E 12", "14 November 1930", "8 April 1930", "30 January 1930", "20 February 1931", "1689504-001", "T-800.619.517-2", "D-B 217.735"),
            "SRC0290": ("manuscript source", "20 February 1931", "no GEMA work number"),
        }
        for source_id, markers in details.items():
            with self.subTest(source=source_id):
                source = sources[source_id]
                self.assertEqual(source["sourceType"], "secondary_literature")
                self.assertEqual(source["date"], "2010")
                self.assertIn("doctoral dissertation, University of Vienna, 2010", source["fullCitation"])
                self.assertIn("Digital copy: grammophon-platten.de", source["fullCitation"])
                self.assertNotIn("author’s permission", source["fullCitation"])
                self.assertIn("author’s permission", source["researchNote"])
                self.assertIn("rights remain with the author", source["researchNote"])
                for marker in markers:
                    self.assertIn(marker, source["researchNote"])
                    self.assertNotIn(marker, source["fullCitation"])
                self.assertEqual(source["additionalLinks"][0]["role"], "source_record")

    def test_gmeindl_biographical_evidence_is_preserved_without_duplicate_dates(self) -> None:
        source = next(record for record in json.loads((PUBLIC / "sources.json").read_text())["records"] if record["id"] == "SRC0684")
        for marker in ("31 December 1890", "1 September 1958", "Munich Hofoper from 1915", "Dozent in 1922", "professor of composition", "Sergiu Celibidache", "Ernst Pepping", "without the h"):
            self.assertIn(marker, source["researchNote"])
            self.assertNotIn(marker, source["fullCitation"])
        self.assertEqual(source["researchNote"].count("31 December 1890"), 1)
        self.assertEqual(source["researchNote"].count("1929"), 1)
        self.assertIn("doi:10.1553/0x0001cf41", source["fullCitation"])

    def test_attributed_rights_statements_are_outside_archival_citations(self) -> None:
        sources = {record["id"]: record for record in json.loads((PUBLIC / "sources.json").read_text())["records"]}
        for source_id in ("SRC0477", "SRC0863"):
            self.assertNotIn("marked public domain", sources[source_id]["fullCitation"])
            self.assertIn("Polona marks the digitised item as public domain.", sources[source_id]["researchNote"])
            self.assertIn("pseudonym", sources[source_id]["researchNote"])
        statement = "Copies carry the Center’s notice that the material may be restricted by United States copyright law."
        self.assertNotIn(statement, sources["SRC0709"]["fullCitation"])
        self.assertEqual(statement, sources["SRC0709"]["researchNote"])
        self.assertIn("Text: Egon Schubert / Mus. B. Kaper", sources["SRC0709"]["fullCitation"])

    def test_visual_context_and_rights_are_preserved_outside_citations(self) -> None:
        sources = {
            record["id"]: record
            for record in json.loads((PUBLIC / "sources.json").read_text())["records"]
        }
        expectations = {
            "SRC0014": "archive’s economic rights to the work: public domain",
            "SRC0561": "Autorskie prawa majątkowe archiwum do utworu: domena publiczna",
            "SRC0654": "The issue appeared in Paris under German occupation.",
        }
        for source_id, text in expectations.items():
            with self.subTest(source=source_id):
                self.assertNotIn(text, sources[source_id]["fullCitation"])
                self.assertIn(text, sources[source_id]["researchNote"])
        self.assertIn("Photo Harcourt", sources["SRC0654"]["fullCitation"])
        self.assertIn("p. 26", sources["SRC0654"]["fullCitation"])
        self.assertNotIn("crop", sources["SRC0460"]["fullCitation"])
        self.assertEqual(sources["SRC0460"]["title"], "Dni Krakowa — photograph, June 1939")
        media = {
            record["id"]: record
            for record in json.loads((PUBLIC / "media.json").read_text())["records"]
        }
        self.assertIn("Portrait crop of Józef Śmidowicz", media["M153"]["description"])
        self.assertIn("SRC0460", media["M153"]["sourceIds"])

    def test_validator_recognizes_scope_and_use_assessments(self) -> None:
        examples = (
            "The entry was not checked against the database itself.",
            "Used here as image identification for the local poster.",
        )
        for example in examples:
            with self.subTest(example=example):
                self.assertIsNotNone(SOURCE_PUBLIC_WORKFLOW_PATTERN.search(example))

    def test_canonical_citations_do_not_contain_editorial_workflow(self) -> None:
        sources = json.loads(
            (PUBLIC / "sources.json").read_text(encoding="utf-8")
        )["records"]
        offenders = [
            (source["id"], field)
            for source in sources
            for field in ("shortCitation", "fullCitation")
            if SOURCE_PUBLIC_WORKFLOW_PATTERN.search(str(source.get(field, "")))
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
