"""Distinguish print publication dates and uploader-reported recording years."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source


class PrintedDocumentsAndRecordingDatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {
            r["id"]: r
            for r in json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        }

    def test_audited_printed_documents_use_publication_dates(self):
        for source_id in ("SRC0023", "SRC0404", "SRC0552", "SRC0687"):
            with self.subTest(source=source_id):
                source = self.sources[source_id]
                self.assertEqual(source["sourceType"], "visual_document")
                self.assertEqual(source["dateRole"], "publication")
                self.assertEqual(normalized_source(dict(source, dateRole="creation")), source)

    def test_directory_publication_is_not_the_digitization_platform(self):
        source = self.sources["SRC0023"]
        self.assertEqual(source["publication"], "Berliner Adreßbuch 1932")
        self.assertIn("Digitale Landesbibliothek Berlin", source["repository"])
        self.assertEqual(
            normalized_source(dict(source, publication="Digitale Landesbibliothek Berlin")),
            source,
        )


if __name__ == "__main__":
    unittest.main()
