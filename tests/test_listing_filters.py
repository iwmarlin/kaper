from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Works, People, Media and Sources each list a collection and each carries more controls
# than fit a narrow screen. They share one pattern: the search field stays in
# reach, the facets fold behind a labelled toggle, and the choices in force are
# shown as chips that remove themselves.
LISTINGS = {
    "works.html": ("work", "assets/site/works.js"),
    "people.html": ("person", "assets/site/people.js"),
    "media.html": ("media", "assets/site/gallery.js"),
    "sources.html": ("source", "assets/site/sources.js"),
}


class ListingFilterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pages = {name: (ROOT / name).read_text(encoding="utf-8") for name in LISTINGS}
        cls.scripts = {
            name: (ROOT / script).read_text(encoding="utf-8")
            for name, (_, script) in LISTINGS.items()
        }
        cls.shared = (ROOT / "assets/site/catalogue-filters.js").read_text(encoding="utf-8")

    def test_each_listing_uses_the_shared_filter_shell(self) -> None:
        for name, text in self.pages.items():
            with self.subTest(page=name):
                self.assertIn('class="filters filters--catalogue"', text)
                self.assertIn("filters__shell", text)
                self.assertIn("filters__search", text)

    def test_each_listing_can_fold_its_facets(self) -> None:
        for name, (prefix, _) in LISTINGS.items():
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

    def test_listing_behaviour_is_owned_by_one_shared_component(self) -> None:
        for name, source in self.scripts.items():
            with self.subTest(page=name):
                self.assertIn("createCatalogueFilters", source)
                self.assertNotIn("function syncQuery", source)
                self.assertNotIn('filterToggle.addEventListener("click"', source)

    def test_shared_component_has_the_accessibility_and_url_contract(self) -> None:
        self.assertIn('event.key !== "Escape"', self.shared)
        self.assertIn('close({ returnFocus: true })', self.shared)
        self.assertIn('window.addEventListener("popstate"', self.shared)
        self.assertIn("window.history.replaceState", self.shared)
        self.assertIn("url.searchParams.delete", self.shared)
        self.assertIn("fieldValue(field) !== requestedValue", self.shared)
        self.assertIn('"(max-width: 900px)"', self.shared)

    def test_timeline_and_map_share_the_same_query_state_layer(self) -> None:
        for script in ("timeline-20260714.js", "map-explorer-20260714.js"):
            source = (ROOT / "assets/site" / script).read_text(encoding="utf-8")
            with self.subTest(script=script):
                self.assertIn("createQueryState", source)
                self.assertNotIn("new URLSearchParams", source)


if __name__ == "__main__":
    unittest.main()
