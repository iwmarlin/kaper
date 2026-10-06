"""Printed portrait dates must not silently become photography dates."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from normalize_sources import normalized_source
from visual_sources import normalize_visual_source


EXPECTED_DATES = {
    "SRC0642": "1922-12",
    "SRC0649": "1930",
    "SRC0650": "1955-07",
    "SRC0651": "1937",
    "SRC0652": "1937",
    "SRC0653": "1937",
    "SRC0654": "1941-07-20",
    "SRC0661": "1930-07-17",
    "SRC0778": "1920-05-01",
    "SRC0813": "1929-06-19",
}


class VisualPublicationDatesTests(unittest.TestCase):
    def test_export_corrects_roles_without_changing_dates(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        by_id = {record["id"]: record for record in records}
        for source_id, expected_date in EXPECTED_DATES.items():
            with self.subTest(source=source_id):
                record = dict(by_id[source_id])
                self.assertEqual(record["dateRole"], "publication")
                self.assertEqual(record["date"], expected_date)
                record["dateRole"] = "creation"
                normalized = normalized_source(record)
                self.assertEqual(normalized["dateRole"], "publication")
                self.assertEqual(normalized["date"], expected_date)
                self.assertEqual(normalized_source(normalized), normalized)

    def test_other_documented_creation_dates_are_preserved(self):
        record = {"id": "SRC0795", "sourceType": "archival_photograph", "date": "1929", "dateRole": "creation"}
        normalize_visual_source(record)
        self.assertEqual(record["dateRole"], "creation")
        self.assertEqual(record["date"], "1929")


if __name__ == "__main__":
    unittest.main()
