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
