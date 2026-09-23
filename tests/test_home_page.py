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

    def test_the_portrait_itself_leads_to_its_record(self) -> None:
        """The caption carried the only link, so the one thing a reader clicks —
        the picture — did nothing. It links to the same record, stays out of the
        tab order and out of the accessibility tree, so the caption's link is
        still announced once."""
        record = f"records/media/{self.home['portrait']['id']}/"
        link = re.search(
            r'<a class="hero__portrait-link" href="([^"]+)"([^>]*)>\s*<img',
            self.page,
        )
        self.assertIsNotNone(link, "the home portrait image is not a link")
        self.assertEqual(link.group(1), record)
        self.assertIn('tabindex="-1"', link.group(2))
        self.assertIn('aria-hidden="true"', link.group(2))
        self.assertIn(f'<a href="{record}">See the record</a>', self.page)

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
