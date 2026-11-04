import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def records(name):
    data = json.loads((ROOT / "data/public/v1" / f"{name}.json").read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["records"]}


class WikipediaVisualSourcePrecisionTests(unittest.TestCase):
    def test_articles_are_not_presented_as_the_provenance_of_different_cards(self):
        sources = records("sources")
        media = records("media")
        for sid, mid, status in (("SRC0395", "M038", "copyright_undetermined"),
                                 ("SRC0436", "M076", "copyright_undetermined")):
            with self.subTest(source=sid):
                self.assertIn(mid, sources[sid]["mediaIds"])
                self.assertIn(sid, media[mid]["sourceIds"])
                self.assertIn("provenance", sources[sid]["researchNote"])
                self.assertIn("does not establish", sources[sid]["researchNote"])
                self.assertIn("unverified", media[mid]["publicCreditLine"])
                self.assertFalse(media[mid].get("externalUrl"))
                self.assertEqual(media[mid]["rightsStatus"], status)
                self.assertEqual(media[mid]["galleryStatus"], "detail_only")

    def test_kind_lady_wikipedia_is_context_not_image_source(self):
        source, medium = records("sources")["SRC0393"], records("media")["M145"]
        self.assertIn("M145", source["mediaIds"])
        self.assertIn("different", source["researchNote"])
        self.assertIn("SRC0339", medium["sourceIds"])
        self.assertEqual("restricted", medium["rightsStatus"])
        self.assertEqual("detail_only", medium["galleryStatus"])
