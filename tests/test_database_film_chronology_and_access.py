"""Verified film dates and item-level sheet-music catalogue addresses."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from database_sources import REVIEWED_DATABASE_ACCESS_FIELDS
from normalize_sources import normalized_source


class DatabaseFilmChronologyAndAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {r["id"]: r for r in json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]}
        cls.media = {r["id"]: r for r in json.loads((ROOT / "data/public/v1/media.json").read_text())["records"]}
        cls.works = {r["id"]: r for r in json.loads((ROOT / "data/public/v1/works.json").read_text())["records"]}
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    def test_voyage_distinguishes_production_from_french_release(self):
        source = self.sources["SRC0452"]
        self.assertEqual(source["date"], "1932")
        self.assertEqual(source["dateDisplay"], "1932 (production)")
        self.assertIn("6 January 1933", source["researchNote"])
        self.assertEqual(self.works["W-F016"]["year"], 1933)

    def test_ehe_retains_catalogue_range_and_separate_premiere(self):
        source = self.sources["SRC0478"]
        self.assertEqual((source["date"], source["dateEnd"]), ("1931", "1932"))
        self.assertEqual(source["dateDisplay"], "1931/1932 (film)")
        self.assertIn("31 December 1931", source["researchNote"])
        self.assertIn("15 January 1932", source["researchNote"])
        self.assertEqual(self.works["W-F008"]["year"], 1932)

    def test_other_film_years_date_films_not_database_publication(self):
        for source_id, year in {"SRC0479": "1930", "SRC0480": "1937", "SRC0481": "1937", "SRC0482": "1938"}.items():
            with self.subTest(source=source_id):
                source = self.sources[source_id]
                self.assertEqual(source["date"], year)
                self.assertEqual(source["dateRole"], "described_item")
                self.assertEqual(source["dateQualifier"], "confirmed")
        for source_id, release in {"SRC0480": "29 January 1937", "SRC0481": "19 February 1937", "SRC0482": "9 January 1938"}.items():
            self.assertIn(release, self.sources[source_id]["researchNote"])
        self.assertIn("1936", self.sources["SRC0481"]["researchNote"])

    def test_four_images_musicales_links_identify_distinct_verified_objects(self):
        expected = {"SRC0357": 18420, "SRC0358": 14336, "SRC0359": 4742, "SRC0360": 19315}
        urls = []
        for source_id, item_id in expected.items():
            source = self.sources[source_id]
            self.assertEqual(source["primaryUrl"], f"https://www.imagesmusicales.be/browse/item/{item_id}/150/")
            self.assertEqual(source["repository"], "Images Musicales")
            urls.append(source["primaryUrl"])
        self.assertEqual(len(set(urls)), 4)
        self.assertEqual(self.media["M053"]["externalUrl"], self.sources["SRC0358"]["primaryUrl"])
        self.assertEqual(self.media["M053"]["sourceIds"], ["SRC0358"])
        self.assertNotIn("date", self.sources["SRC0359"])
        self.assertEqual(self.sources["SRC0359"]["dateQualifier"], "unknown")

    def test_only_redundant_platform_suffixes_are_removed(self):
        titles = {"SRC0141": "A Day at the Races", "SRC0147": "Everybody Sing", "SRC0481": "Wings of the Morning", "SRC0587": "Trouble for Two"}
        for source_id, title in titles.items():
            source = self.sources[source_id]
            self.assertEqual(source["title"], title)
            self.assertTrue(source["publication"])
            self.assertTrue(source["repository"])
        # A section qualifier identifies evidence scope and is not redundant.
        self.assertEqual(self.sources["SRC0170"]["title"], "Trouble for Two — IMDb, full cast and crew")
        # This platform qualifier distinguishes two separate film records.
        self.assertEqual(self.sources["SRC0127"]["title"], "Voyage de noces")
        self.assertEqual(self.sources["SRC0452"]["title"], "Voyage de noces — Unifrance")

    def test_chronology_and_access_fields_survive_normalization_and_export(self):
        for source_id, fields in REVIEWED_DATABASE_ACCESS_FIELDS.items():
            with self.subTest(source=source_id):
                source = self.sources[source_id]
                legacy = dict(source)
                for key in fields:
                    legacy[key] = "Legacy value"
                self.assertEqual(normalized_source(legacy), source)
                self.assertEqual(normalized_source(source), source)
                logged = self.overrides["records"]["Sources"][source_id]["fields"]
                for key, value in fields.items():
                    self.assertEqual(logged[key], value)


if __name__ == "__main__":
    unittest.main()
