"""Separate score imprints, digital repositories and membership-list currency."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source


class SourcePublicationAndCurrencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {r["id"]: r for r in json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]}
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    def test_usc_is_not_assigned_as_creator_of_historical_cover(self):
        source = self.sources["SRC0535"]
        self.assertNotIn("creator", source)
        self.assertEqual(source["repository"], "University of Southern California Digital Library")
        self.assertEqual(normalized_source(dict(source, creator="University of Southern California Digital Library")), source)
        self.assertIn("creator", self.overrides["records"]["Sources"]["SRC0535"]["removeFields"])

    def test_blue_venetian_waters_preserves_original_and_digital_publishers(self):
        source = self.sources["SRC0542"]
        self.assertEqual(source["publication"], "Robbins Music Corporation")
        self.assertEqual(source["repository"], "University of Southern California Digital Library")
        self.assertIn("digital publisher: University of Southern California Libraries", source["fullCitation"])
        self.assertEqual(normalized_source(dict(source, publication="USC Digital Library")), source)

    def test_images_musicales_remains_repository_not_historical_publisher(self):
        expected = {
            "SRC0356": "Ufaton Verlag, Berlin",
            "SRC0357": "Editions Francis Salabert, Paris",
            "SRC0358": "Wiener Boheme Verlag, Vienna",
            "SRC0359": "Choudens, Editeur, Paris",
            "SRC0360": "Ufaton Verlag, Berlin",
        }
        for source_id, publication in expected.items():
            with self.subTest(source=source_id):
                source = self.sources[source_id]
                self.assertEqual(source["publication"], publication)
                self.assertEqual(source["repository"], "Images Musicales")
                self.assertEqual(normalized_source(dict(source, publication=publication + " / Images Musicales")), source)

    def test_1927_list_uses_printed_currency_date_not_an_invented_publication_day(self):
        source = self.sources["SRC0477"]
        self.assertEqual(source["date"], "1927-04-01")
        self.assertEqual(source["dateRole"], "data_currency")
        self.assertEqual(source["dateQualifier"], "confirmed")
        self.assertIn("[1927]", source["publication"])
        self.assertIn("not the day of printing or publication", source["researchNote"])
        self.assertEqual(normalized_source(dict(source, date="1927", dateRole="creation")), source)

    def test_1931_list_keeps_both_printed_dates_without_selecting_one_as_publication_day(self):
        source = self.sources["SRC0863"]
        self.assertEqual(source["date"], "1931")
        self.assertEqual(source["dateRole"], "publication")
        for wording in ["na dzień 1 Listopada 1931 r.", "au 1 Octobre 1931"]:
            self.assertIn(wording, source["fullCitation"])
            self.assertIn(wording, source["researchNote"])
        self.assertIn("same title page", source["researchNote"])
        self.assertIn("not resolved here", source["researchNote"])
        self.assertEqual(normalized_source(dict(source, date="1931-11-01", dateRole="creation")), source)


if __name__ == "__main__":
    unittest.main()
