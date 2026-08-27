from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Works, People and Media each list a collection and each carries more controls
# than fit a narrow screen. They share one pattern: the search field stays in
# reach, the facets fold behind a labelled toggle, and the choices in force are
# shown as chips that remove themselves.
LISTINGS = {
    "works.html": "work",
    "people.html": "person",
    "media.html": "media",
}


class ListingFilterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pages = {name: (ROOT / name).read_text(encoding="utf-8") for name in LISTINGS}

    def test_each_listing_uses_the_shared_filter_shell(self) -> None:
        for name, text in self.pages.items():
            with self.subTest(page=name):
                self.assertIn('class="filters filters--catalogue"', text)
                self.assertIn("filters__shell", text)
                self.assertIn("filters__search", text)

    def test_each_listing_can_fold_its_facets(self) -> None:
        for name, prefix in LISTINGS.items():
            text = self.pages[name]
            with self.subTest(page=name):
                self.assertIn(f'id="{prefix}-filter-toggle"', text)
                self.assertIn(f'id="{prefix}-filter-options"', text)
                self.assertIn(f'aria-controls="{prefix}-filter-options"', text)
                self.assertIn(f'id="{prefix}-active-filters"', text)

    def test_the_reset_button_starts_hidden(self) -> None:
        for name, text in self.pages.items():
            with self.subTest(page=name):
                match = re.search(r'<button[^>]*id="[a-z-]*reset[a-z-]*"[^>]*>', text)
                self.assertIsNotNone(match, "the listing has no reset control")
                self.assertIn("hidden", match.group(0))

    def test_the_search_field_is_the_first_control(self) -> None:
        for name, text in self.pages.items():
            with self.subTest(page=name):
                shell = re.search(r'filters__shell.*?</section>', text, re.S).group(0)
                self.assertLess(shell.index("filters__search"), shell.index("filters__toggle"))


if __name__ == "__main__":
    unittest.main()
