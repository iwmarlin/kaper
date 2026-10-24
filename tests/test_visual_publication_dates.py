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
    "SRC0704": "1930",
    "SRC0577": "1916-04-30",
    "SRC0619": "1932",
    "SRC0622": "1929",
    "SRC0352": "2024",
    "SRC0368": "1928",
    "SRC0812": "1912-12-07",
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
    def test_graben_postcard_date_represents_use_not_creation(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        source = next(record for record in records if record["id"] == "SRC0439")
        self.assertEqual(source["date"], "1922")
        self.assertEqual(source["dateRole"], "described_item")
        self.assertEqual(source["dateDisplay"], "1922 (use)")
        self.assertIn("1922 (Gebrauch)", source["researchNote"])
        self.assertEqual(normalized_source(dict(source, dateRole="creation")), source)
        media = json.loads((ROOT / "data/public/v1/media.json").read_text())["records"]
        postcard = next(record for record in media if record["id"] == "M095")
        self.assertIn("used in 1922", postcard["title"])
        self.assertIn("used in 1922", postcard["publicCaption"])

    def test_badet_programme_retains_performance_date_without_redating_portrait(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        source = next(record for record in records if record["id"] == "SRC0618")
        self.assertEqual(source["date"], "1941-10-04")
        self.assertEqual(source["dateRole"], "described_item")
        self.assertEqual(source["dateDisplay"], "4 October 1941 (performance)")
        self.assertIn("not an established creation date", source["researchNote"])
        changed = dict(source, dateRole="creation")
        self.assertEqual(normalized_source(changed), source)

    def test_grothe_card_keeps_approximate_decade_and_qualified_note(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        source = next(record for record in records if record["id"] == "SRC0704")
        self.assertEqual(source["dateRole"], "publication")
        self.assertEqual(source["date"], "1930")
        self.assertEqual(source["dateEnd"], "1939")
        self.assertEqual(source["dateQualifier"], "approximate")
        self.assertEqual(source["dateDisplay"], "1930s")
        self.assertIn("not to the underlying photograph", source["researchNote"])
        self.assertIn("card 215", source["additionalLinks"][0]["label"])

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
