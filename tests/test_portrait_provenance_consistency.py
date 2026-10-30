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
        self.assertEqual(source["creator"], "L. Gutmann (studio mark); Bain News Service (publisher)")
        self.assertIn("ggbain.34250", source["fullCitation"])
        self.assertIn("49654681548", source["accessUrl"])
        self.assertIn("studio mark", source["researchNote"])
        self.assertIn("not assumed to identify the individual", source["researchNote"])
        self.assertTrue(any("ggbain.34250" in link["url"] for link in source["additionalLinks"]))
        self.assertIn("L. Gutmann", self.media["M262"]["publicCreditLine"])
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

    def test_tauber_publisher_is_not_assigned_as_photographer(self):
        source = self.sources["SRC0551"]
        self.assertEqual(source["creator"], "Photographer unidentified")
        self.assertEqual(source["publication"], "Bain News Service")
        self.assertIn("George Grantham Bain Collection", source["repository"])
        self.assertNotIn("photographed by the Bain", self.media["M229"]["publicCaption"])
        self.assertIn("Bain News Service, publisher", self.media["M229"]["publicCreditLine"])
        self.assertEqual(normalized_source(dict(source, creator="Bain News Service (publisher)")), source)

    def test_lloyd_institutional_attribution_is_retained_and_qualified(self):
        source = self.sources["SRC0621"]
        self.assertEqual(source["creator"], "Academy of Motion Picture Arts and Sciences")
        self.assertIn("no individual photographer", source["researchNote"])
        self.assertIn("attribution is retained", source["researchNote"])

    def test_salter_title_keeps_the_approximation(self):
        self.assertIn("c. 1940s", self.media["M346"]["title"])

    def test_film_still_and_publicity_card_share_one_family(self):
        self.assertEqual(self.media["M214"]["category"], "film still / publicity card")
        self.assertEqual(self.media["M076"]["category"], self.media["M214"]["category"])
        source = self.sources["SRC0400"]
        self.assertEqual(source["creator"], "Metro-Goldwyn-Mayer")
        self.assertEqual(normalized_source(dict(source, creator="Trailer frame, Metro-Goldwyn-Mayer")), source)
        gallery = (ROOT / "assets/site/gallery.js").read_text()
        self.assertIn('"film still / publicity card": "Film stills and cards"', gallery)
        self.assertIn('initialUrl.searchParams.get("category") === "lobby card / title card"', gallery)
        self.assertIn('initialUrl.searchParams.set("category", "film still / publicity card")', gallery)


if __name__ == "__main__":
    unittest.main()
