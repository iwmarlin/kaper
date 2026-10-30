"""Keep historical objects distinct from modern access reproductions."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source


class DigitalCollectionProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {
            record["id"]: record
            for record in json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        }
        cls.media = {
            record["id"]: record
            for record in json.loads((ROOT / "data/public/v1/media.json").read_text())["records"]
        }
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    def test_jurmann_gallery_is_not_the_historical_creator_or_imprint(self):
        publishers = {
            "SRC0538": "Wiener Bohème Verlag, Berlin–Vienna",
            "SRC0539": "Wiener Bohème Verlag, Berlin–Vienna",
            "SRC0540": "Éditions Salabert, Paris",
            "SRC0541": "Ufaton-Verlag, Berlin",
        }
        provider = "Verein der Freunde und Förderer des Werks von Walter Jurmann"
        for source_id, publisher in publishers.items():
            with self.subTest(source=source_id):
                source = self.sources[source_id]
                self.assertEqual(source["publication"], publisher)
                self.assertNotIn(provider, source["creator"])
                self.assertEqual(source["repository"], provider)
                self.assertEqual(source["dateRole"], "described_item")
                self.assertTrue(source["dateDisplay"].endswith("(film)"))
                self.assertIn("locally preserved cover", source["researchNote"])
                self.assertEqual(
                    normalized_source(dict(source, creator=provider, publication="Walter Jurmann official website", dateRole="creation")),
                    source,
                )

    def test_poster_year_dates_film_not_an_unverified_printing(self):
        source = self.sources["SRC0417"]
        self.assertEqual(source["dateRole"], "described_item")
        self.assertEqual(source["dateDisplay"], "1933 (film)")
        self.assertNotIn("publication", source)
        self.assertIn("not an independently verified date of the poster", source["researchNote"])
        self.assertEqual(normalized_source(dict(source, publication="Filmportal.de", dateRole="creation")), source)
        self.assertEqual(self.media["M183"]["rightsStatus"], "restricted")
        self.assertIn("Urheberrechtsschutz", self.media["M183"]["rightsNote"])
        self.assertNotIn("published in 1933", self.media["M183"]["rightsNote"])

    def test_polona_poster_uses_catalogued_title_imprint_and_shelfmark(self):
        source = self.sources["SRC0432"]
        self.assertTrue(source["title"].startswith("Jeśli chcesz by bolszewik"))
        self.assertIn("Kotkowski i Frejlich", source["publication"])
        self.assertIn("DŻS IA 6a6", source["fullCitation"])
        self.assertIn("b1000000657375", source["fullCitation"])
        self.assertEqual(source["dateRole"], "publication")
        self.assertEqual(source["dateDisplay"], "[1920]")
        self.assertNotIn("creator", source)

    def test_usc_partial_score_preserves_extent_and_original_publisher(self):
        source = self.sources["SRC0443"]
        self.assertEqual(source["publication"], "Robbins Music Corporation, New York")
        self.assertEqual(source["dateRole"], "issue")
        self.assertIn("pp. 1–2 and 6 only", source["fullCitation"])
        self.assertIn("PMC 5/36", source["fullCitation"])
        self.assertIn("UC17193693", source["fullCitation"])
        self.assertTrue(source["primaryUrl"].startswith("https://doi.org/"))
        self.assertIn("DocRID=2A3BF1X8GAHTY", source["accessUrl"])
        self.assertEqual(self.media["M074"]["externalUrl"], source["primaryUrl"])
        self.assertEqual(self.media["M074"]["rightsStatus"], "copyright_undetermined")

    def test_berlin_provider_is_not_identified_as_1928_photographer(self):
        source = self.sources["SRC0579"]
        self.assertNotIn("creator", source)
        self.assertIn("digital dataset provider", source["publication"])
        self.assertEqual(source["dateRole"], "described_item")
        self.assertEqual(source["dateDisplay"], "1928 (aerial imagery)")
        self.assertIn("not an identification of the original aerial photographer", source["researchNote"])
        self.assertEqual(normalized_source(dict(source, creator="Senatsverwaltung Berlin", dateRole="creation")), source)
        self.assertEqual(self.media["M282"]["rightsStatus"], "open_licence")

    def test_unidentified_postcard_maker_does_not_become_a_photographer(self):
        source = self.sources["SRC0439"]
        self.assertEqual(source["creator"], "Creator unidentified")
        self.assertEqual(source["dateRole"], "described_item")
        self.assertEqual(source["dateDisplay"], "1922 (use)")
        self.assertNotIn("publication", source)
        self.assertEqual(normalized_source(dict(source, creator="Unbekannt", publication="Wien Museum")), source)

    def test_audited_sources_keep_item_links_and_explicit_export_corrections(self):
        expected_media = {
            "SRC0417": "M183", "SRC0432": "M070", "SRC0439": "M095",
            "SRC0443": "M074", "SRC0538": "M222", "SRC0539": "M221",
            "SRC0540": "M223", "SRC0541": "M225", "SRC0579": "M282",
        }
        for source_id, media_id in expected_media.items():
            with self.subTest(source=source_id):
                source = self.sources[source_id]
                self.assertIn(media_id, source["mediaIds"])
                self.assertIn(source_id, self.media[media_id]["sourceIds"])
                self.assertEqual(normalized_source(source), source)
                override = self.overrides["records"]["Sources"][source_id]
                for key, value in override["fields"].items():
                    self.assertEqual(source.get(key), value, key)
                for key in override.get("removeFields", []):
                    self.assertNotIn(key, source)


if __name__ == "__main__":
    unittest.main()
