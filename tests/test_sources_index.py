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

    def test_the_footer_leads_to_the_index_and_the_primary_navigation_does_not(self) -> None:
        """Sources are cited at record level: a reader meets them on the record
        they support and reaches the catalogue from there, from its breadcrumb,
        or from the footer. Keeping it out of the header is the editorial
        position, not an omission, so both lists are checked."""
        self.assertIn('["sources", "sources.html", "Sources"]', self.core)
        primary_navigation = self.core[
            self.core.index("const NAV_ITEMS") : self.core.index("const FOOTER_EXPLORE_ITEMS")
        ]
        self.assertNotIn("sources.html", primary_navigation)
        self.assertNotIn('href="sources.html"', self.home)

    def test_the_index_is_crawlable_without_the_scripted_chrome(self) -> None:
        """The header and footer are built in the browser, so neither carries a
        link a crawler can follow. The sitemap entry and the breadcrumb printed
        into every source record are what make the index reachable."""
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("https://iwmarlin.github.io/kaper/sources.html", sitemap)
        record = (ROOT / "records/source/SRC0116/index.html").read_text(encoding="utf-8")
        self.assertIn('href="sources.html"', record)


if __name__ == "__main__":
    unittest.main()
