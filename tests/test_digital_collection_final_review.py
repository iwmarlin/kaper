"""Protect item-level decisions for the final six digital collection records."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source


class DigitalCollectionFinalReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {r["id"]: r for r in json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]}
        cls.media = {r["id"]: r for r in json.loads((ROOT / "data/public/v1/media.json").read_text())["records"]}

    def test_cosi_identifies_partial_score_and_actual_creators(self):
        s = self.sources["SRC0535"]
        self.assertEqual(s["dateRole"], "issue")
        self.assertEqual(s["publication"], "Robbins Music Corporation, New York")
        for text in ["Ned Washington", "PMC 5/13", "UC17191660", "SH 1364-4", "pp. 1 and 6 only"]:
            self.assertIn(text, s["fullCitation"])
        self.assertTrue(s["primaryUrl"].startswith("https://doi.org/"))
        self.assertEqual(self.media["M218"]["externalUrl"], s["primaryUrl"])

    def test_blue_qualifies_mismatched_description(self):
        s = self.sources["SRC0542"]
        self.assertEqual(s["dateRole"], "issue")
        self.assertEqual(s["date"], "1937")
        self.assertIn("incorrectly names", s["researchNote"])
        self.assertIn("All God’s Chillun Got Rhythm", s["researchNote"])
        self.assertNotIn("All God’s Chillun Got Rhythm", s["fullCitation"])

    def test_paris_publisher_and_broad_museum_dating(self):
        s = self.sources["SRC0574"]
        self.assertEqual(s["creator"], "Photographer unidentified")
        self.assertEqual(s["publication"], "Neurdein Frères")
        self.assertNotIn("date", s)
        self.assertNotIn("dateEnd", s)
        self.assertEqual(s["dateQualifier"], "unknown")
        self.assertEqual(s["dateDisplay"], "20th century (museum dating)")
        self.assertIn("20 December 2021", s["researchNote"])
        self.assertNotIn("early twentieth", self.media["M277"]["publicCaption"])
        self.assertEqual(self.media["M277"]["rightsStatus"], "open_licence")

    def test_pragher_holder_and_aggregator(self):
        s = self.sources["SRC0576"]
        self.assertNotIn("publication", s)
        self.assertEqual(s["creator"], "Willy Pragher")
        self.assertEqual(s["date"], "1935-12")
        self.assertIn("Staatsarchiv Freiburg", s["repository"])
        self.assertIn("aggregating access service", s["researchNote"])
        self.assertEqual(s["additionalLinks"][0]["url"], "https://www.landesarchiv-bw.de/plink/?f=5-91724")

    def test_editor_and_architects_are_not_image_authors(self):
        s = self.sources["SRC0577"]
        self.assertEqual(s["creator"], "Creator unidentified")
        self.assertEqual(s["dateRole"], "publication")
        self.assertIn("Hurkiewicz as editor and publisher", s["researchNote"])
        self.assertIn("M. Kontkiewicz and S. Zaleski", s["researchNote"])

    def test_badet_distinguishes_performance_and_digital_access(self):
        s = self.sources["SRC0618"]
        self.assertNotIn("publication", s)
        self.assertEqual(s["date"], "1941-10-04")
        self.assertEqual(s["dateRole"], "described_item")
        self.assertIn("29 September 2014", s["researchNote"])
        self.assertIn("FRBNF42642204", s["researchNote"])
        self.assertEqual(s["creator"], "Photographer unidentified")

    def test_idempotence_and_item_links(self):
        expected = {"SRC0535": "M218", "SRC0542": "M226", "SRC0574": "M277", "SRC0576": "M279", "SRC0577": "M280", "SRC0618": "M264"}
        for source_id, media_id in expected.items():
            with self.subTest(source=source_id):
                s = self.sources[source_id]
                self.assertEqual(normalized_source(s), s)
                self.assertIn(media_id, s["mediaIds"])
                self.assertIn(source_id, self.media[media_id]["sourceIds"])
        s = self.sources["SRC0574"]
        self.assertEqual(normalized_source(dict(s, date="1900", dateEnd="1933", dateQualifier="approximate")), s)


if __name__ == "__main__":
    unittest.main()

