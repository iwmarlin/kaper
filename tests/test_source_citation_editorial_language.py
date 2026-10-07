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
