from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TimelinePrerenderTests(unittest.TestCase):
    """The chronology arrived by script after four complete tables had loaded,
    so without it the timeline read "Loading timeline…" and showed no events."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (ROOT / "life.html").read_text(encoding="utf-8")
        cls.index = json.loads((ROOT / "data/site/indexes/timeline.json").read_text(encoding="utf-8"))
        cls.script = (ROOT / "assets/site/timeline-20260714.js").read_text(encoding="utf-8")

    def test_the_highlights_are_printed_into_the_document(self) -> None:
        count = re.search(r"<strong>(\d+)</strong> highlights selected from (\d+) matching events", self.page)
        self.assertIsNotNone(count)
        self.assertEqual(int(count.group(2)), self.index["count"])
        self.assertEqual(
            self.page.count('class="timeline-entry timeline-entry--milestone'),
            int(count.group(1)),
        )
        self.assertIn(f"{self.index['count']} published events", self.page)
        self.assertNotIn("Loading", self.page)

    def test_the_page_reads_the_compact_index_rather_than_the_full_tables(self) -> None:
        self.assertIn('loadSiteIndex("timeline")', self.script)
        self.assertNotIn("loadTables", self.script)

    def test_the_index_carries_only_what_the_disclosure_reads(self) -> None:
        hero_fields = {"id", "title", "assetPath", "altText", "externalUrl"}
        for event in self.index["records"]:
            with self.subTest(event=event["id"]):
                hero = event.get("hero", {})
                self.assertEqual({key for key in hero if not key.startswith("rights")} - hero_fields, set())
                self.assertLessEqual(set(event.get("heroSource", {})), {"id", "primaryUrl", "accessUrl"})


class PlaceListPrerenderTests(unittest.TestCase):
    """The architecture promises a place list that survives a map that cannot
    run; without JavaScript the list container used to be empty."""

    def test_every_place_is_listed_as_a_link_to_its_record(self) -> None:
        page = (ROOT / "map.html").read_text(encoding="utf-8")
        places = json.loads((ROOT / "data/public/v1/places.json").read_text(encoding="utf-8"))["records"]
        linked = re.findall(r'<li>\s*<a href="records/place/([^/"]+)/"', page)
        self.assertEqual(len(linked), len(places))
        self.assertEqual(set(linked), {place["id"] for place in places})


if __name__ == "__main__":
    unittest.main()
