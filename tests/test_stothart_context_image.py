"""Keep the captioned page without promoting an uncertain crop to a portrait."""

import json
import sys
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_catalogue_indexes import portrait_for
from build_record_payloads import portrait_belongs_to


def records(filename):
    return {r["id"]: r for r in json.loads((ROOT / "data/public/v1" / filename).read_text())["records"]}


class StothartContextImageTests(unittest.TestCase):
    def test_complete_page_remains_linked_to_its_source(self):
        media = records("media.json")["M297"]
        self.assertEqual(media["category"], "press clipping")
        self.assertEqual(media["sourceIds"], ["SRC0649"])
        self.assertIn("complete printed page", media["description"])
        self.assertNotIn("The caption reverses the two men", media["description"])
        with Image.open(ROOT / media["assetPath"]) as image:
            self.assertEqual(image.size, (1600, 2239))

    def test_page_is_not_used_as_stotharts_portrait(self):
        people, sources, media = records("people.json"), records("sources.json"), records("media.json")
        self.assertFalse(portrait_belongs_to(media["M297"], people["P136"], sources["SRC0649"]))
        self.assertIsNone(portrait_for(people["P136"], sources, media, ROOT))

    def test_obsolete_crop_is_removed(self):
        self.assertFalse((ROOT / "assets/images/portraits/herbert-stothart.jpg").exists())


if __name__ == "__main__":
    unittest.main()
