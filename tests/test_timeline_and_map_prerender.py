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

    def test_the_milestone_selection_is_stated_by_the_records(self) -> None:
        # Which events the chronology opens on is an editorial decision, so it
        # belongs to the records and not to a list of identifiers in the module
        # that draws them: the two cannot then disagree, and the selection is
        # visible where the rest of the archive's decisions are.
        events = json.loads(
            (ROOT / "data/public/v1/timeline-events.json").read_text(encoding="utf-8")
        )["records"]
        milestones = [
            event for event in events if event.get("displayMode") == "milestone"
        ]
        self.assertGreater(len(milestones), 0)
        self.assertEqual(
            self.page.count('class="timeline-entry timeline-entry--milestone'),
            len(milestones),
        )
        self.assertEqual(
            sum(
                1
                for event in self.index["records"]
                if event.get("displayMode") == "milestone"
            ),
            len(milestones),
        )
        view = (ROOT / "assets/site/timeline-view.js").read_text(encoding="utf-8")
        self.assertNotRegex(view, r"TE\d{4}")

    def test_every_entry_declares_the_era_it_belongs_to(self) -> None:
        # The era strip follows the entry under it rather than the last chapter
        # heading to have passed: a heading and its first events can fill the
        # screen while the strip still lights the era before.
        entries = re.findall(r'class="timeline-entry[^"]*"[^>]*?data-chapter="([a-z]+)"', self.page)
        self.assertEqual(
            len(entries),
            self.page.count('class="timeline-entry timeline-entry--milestone'),
        )
        self.assertTrue(entries)
        self.assertLessEqual(set(entries), {"warsaw", "european", "hollywood"})
        self.assertIn('.timeline-entry[data-chapter]', self.script)
        self.assertNotIn('querySelectorAll(".timeline-chapter")', self.script)

    def test_a_link_to_one_event_opens_the_view_that_contains_it(self) -> None:
        # Forty of the fifty-five events are not milestones, so a bare
        # "#event-TE0003" names an entry the opening view does not draw. The
        # view is a default nobody chose and gives way to the address; a
        # search or a filter the address states is the reader's own and stands.
        self.assertIn('/^#event-(TE\\d+)$/', self.script)
        self.assertIn("function hashNeedsFullView()", self.script)
        self.assertIn("event.id === eventId && matchesFilters(event)", self.script)
        self.assertIn('setView("all")', self.script)
        # Redrawn or left standing, an address naming an event ends on it:
        # the browser's own attempt at the fragment is made while the page is
        # still assembling itself and does not always hold.
        self.assertIn("function landOnHashTarget()", self.script)
        self.assertIn("function openHashTarget()", self.script)
        self.assertIn('document.readyState === "complete"', self.script)
        self.assertIn("scrollMarginTop", self.script)
        # The stylesheet asks for smooth scrolling and "auto" defers to it, so
        # the landing would be an animation the browser can cut short.
        self.assertIn('behavior: "instant"', self.script)
        self.assertIn('window.addEventListener("hashchange"', self.script)

    def test_the_printed_chronology_is_left_standing_when_it_is_the_one_asked_for(self) -> None:
        # Redrawing identical markup over the printed page is what defeated the
        # browser's own handling of "#event-…", and the landing machinery that
        # had to be written to compensate. The page now redraws only for a
        # state the print cannot show.
        self.assertIn("const printedStateStands = hasPrerenderedResults", self.script)
        self.assertIn('activeView === "highlights"', self.script)
        for control in ("search", "category", "period"):
            self.assertIn(f"!controls.{control}.value", self.script)
        self.assertIn("if (printedStateStands) {", self.script)
        # Nothing is left polling for the right moment to scroll.
        self.assertNotIn("setTimeout(scrollToHashTarget", self.script)
        self.assertNotIn("landingWindowEndsAt", self.script)

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
