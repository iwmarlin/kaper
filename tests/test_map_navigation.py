from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MapNavigationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = (ROOT / "assets/site/map-explorer-20260714.js").read_text(encoding="utf-8")

    def test_a_place_chosen_from_the_list_on_a_phone_brings_the_map_into_view(self) -> None:
        """On a phone the list sits below the map, so a selection made there used
        to change a map several hundred pixels above the screen."""
        handler = re.search(r'listTarget\.querySelectorAll\("button"\)\.forEach\(.*?\n    \}\);', self.source, re.S)
        self.assertIsNotNone(handler)
        self.assertIn("revealMap", handler.group(0))
        reveal = re.search(r"function revealMap\(\)\s*\{.*?\n  \}", self.source, re.S)
        self.assertIsNotNone(reveal)
        self.assertIn("compactMapLayout", reveal.group(0))
        self.assertIn("prefers-reduced-motion", reveal.group(0))

    def test_a_focused_marker_is_activated_by_enter_and_space(self) -> None:
        """Markers are announced as buttons, but Leaflet maps Enter only to popups;
        these markers carry tooltips, so the key did nothing."""
        self.assertRegex(self.source, r'marker\.on\("keydown"')
        keydown = re.search(r'marker\.on\("keydown".*?\n      \}\);', self.source, re.S)
        self.assertIsNotNone(keydown)
        self.assertIn('"Enter"', keydown.group(0))
        self.assertIn('" "', keydown.group(0))
        self.assertIn("selectPlace(place", keydown.group(0))

    def test_escape_closes_a_selection_in_every_layout(self) -> None:
        escape = re.search(r'event\.key !== "Escape".*?\) return;', self.source, re.S)
        self.assertIsNotNone(escape)
        self.assertNotIn("compactMapLayout", escape.group(0))


if __name__ == "__main__":
    unittest.main()
