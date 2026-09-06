from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SourcesIndexContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (ROOT / "sources.html").read_text(encoding="utf-8")
        cls.script = (ROOT / "assets/site/sources.js").read_text(encoding="utf-8")
        cls.core = (ROOT / "assets/site/core.js").read_text(encoding="utf-8")
        cls.home = (ROOT / "index.html").read_text(encoding="utf-8")

    def test_page_loads_the_source_index_module(self) -> None:
        self.assertIn('src="assets/site/sources.js?', self.page)
        self.assertIn('await loadSiteIndex("sources")', self.script)
        self.assertIn("renderSourceIndexRow", self.script)

    def test_page_offers_search_facets_and_progressive_loading(self) -> None:
        for element_id in (
            "source-search",
            "source-type",
            "source-date-role",
            "source-access",
            "source-sort",
            "source-more",
            "source-show-all",
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', self.page)

    def test_mobile_intro_keeps_the_scope_note_in_a_compact_disclosure(self) -> None:
        self.assertIn('class="sources-page"', self.page)
        self.assertIn('class="source-index-scope source-index-scope--compact"', self.page)
        self.assertIn("<summary>About this index</summary>", self.page)

    def test_page_is_not_yet_linked_from_primary_or_home_navigation(self) -> None:
        self.assertNotIn('"sources.html"', self.core)
        self.assertNotIn('href="sources.html"', self.home)


if __name__ == "__main__":
    unittest.main()
