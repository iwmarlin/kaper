from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HomePagePrerenderTests(unittest.TestCase):
    """The portrait, pathways, selected moments and figures used to arrive by
    script, so without it the front page read "Loading portrait…" indefinitely."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.home = json.loads((ROOT / "data/site/home.json").read_text(encoding="utf-8"))
        cls.script = (ROOT / "assets/site/home.js").read_text(encoding="utf-8")

    def test_every_section_is_printed_into_the_document(self) -> None:
        self.assertEqual(self.page.count('class="pathway-row"'), len(self.home["pathways"]))
        self.assertEqual(self.page.count('class="home-event-card"'), len(self.home["events"]))
        self.assertIn('class="hero__portrait-caption"', self.page)
        self.assertIn(">See the record</a>", self.page)
        self.assertNotIn("Loading", self.page)

    def test_the_figures_carry_the_current_source_count(self) -> None:
        figures = re.search(r'id="method-figures">(.*?)</span>', self.page, re.DOTALL)
        self.assertIsNotNone(figures)
        self.assertIn(
            f"<strong>{self.home['glance']['sources']:,}</strong> linked sources",
            figures.group(1),
        )

    def test_the_page_script_requests_no_data(self) -> None:
        self.assertNotIn("fetch(", self.script)


if __name__ == "__main__":
    unittest.main()
