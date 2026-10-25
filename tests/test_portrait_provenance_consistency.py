"""Keep publisher, uploader, photography date and narrative chronology distinct."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source


class PortraitProvenanceConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {r["id"]: r for r in json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]}
        cls.media = {r["id"]: r for r in json.loads((ROOT / "data/public/v1/media.json").read_text())["records"]}

    def test_piccaver_uses_the_same_item_identifier_and_qualified_range(self):
        source = self.sources["SRC0612"]
        self.assertEqual((source["date"], source["dateEnd"]), ("1920", "1925"))
        self.assertEqual(source["dateQualifier"], "approximate")
        self.assertEqual(source["dateDisplay"], "c. 1920–c. 1925")
        self.assertEqual(source["dateRole"], "creation")
        self.assertEqual(source["publication"], "Bain News Service")
        self.assertEqual(source["creator"], "Photographer unidentified")
        self.assertIn("ggbain.34250", source["fullCitation"])
        self.assertIn("49654681548", source["accessUrl"])
        self.assertIn("1920 and 1925", self.media["M262"]["rightsNote"])
        changed = dict(source, dateQualifier="confirmed", creator="Bain News Service")
        changed.pop("dateEnd")
        changed.pop("dateDisplay")
        self.assertEqual(normalized_source(changed), source)

    def test_zeisler_uploader_is_not_the_photographer(self):
        source = self.sources["SRC0595"]
        self.assertEqual(source["creator"], "Photographer unidentified")
        self.assertNotIn("Azeisler", source["fullCitation"])
        self.assertIn("uploader Azeisler", source["researchNote"])
        self.assertIn("not as an established photographer credit", source["researchNote"])
        self.assertEqual(normalized_source(dict(source, creator="Azeisler (file-page attribution)")), source)
        self.assertIn("Photographer unidentified", self.media["M248"]["publicCreditLine"])
        self.assertIn("uploader", self.media["M248"]["rightsNote"])

    def test_garland_caption_uses_explicit_film_year(self):
        caption = self.media["M258"]["publicCaption"]
        self.assertIn("Pigskin Parade (1936)", caption)
        self.assertIn("In 1938", caption)
        self.assertNotIn("following year", caption)


if __name__ == "__main__":
    unittest.main()
