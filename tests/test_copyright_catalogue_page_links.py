import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Entries whose page could not be fixed with two agreeing signals — the
# registration number in its own series, and the title on the same or the
# next scan page — so they still open the volume. Shrink this set as entries
# are resolved; never grow it to make the test pass.
UNRESOLVED = {
    "SRC0230", "SRC0240", "SRC0241", "SRC0245", "SRC0246", "SRC0254",
    "SRC0257", "SRC0259", "SRC0260", "SRC0263", "SRC0264", "SRC0268",
    "SRC0272", "SRC0274", "SRC0275", "SRC0276", "SRC0311", "SRC0378",
    "SRC0469", "SRC0472", "SRC0473", "SRC0872",
}


class CopyrightCataloguePageLinkTests(unittest.TestCase):
    """A Catalog of Copyright Entries volume runs to well over a thousand
    pages. A citation that names the entry and links the volume leaves the
    reader to search it; each entry now opens on its page."""

    @classmethod
    def setUpClass(cls):
        sources = json.loads(
            (ROOT / "data/public/v1/sources.json").read_text(encoding="utf-8")
        )["records"]
        cls.cce = [
            s for s in sources
            if "archive.org/details/catalogofcopyrig" in (s.get("primaryUrl") or "")
        ]

    def test_every_resolved_entry_opens_on_its_page(self):
        for source in self.cce:
            if source["id"] in UNRESOLVED:
                continue
            with self.subTest(source=source["id"]):
                self.assertRegex(source["primaryUrl"], r"/page/n?\d+")

    def test_the_unresolved_set_is_exactly_what_still_opens_the_volume(self):
        still_volume = {
            s["id"] for s in self.cce if "/page/" not in s["primaryUrl"]
        }
        self.assertEqual(still_volume, UNRESOLVED)

    def test_scan_index_links_name_the_volume_they_were_found_in(self):
        for source in self.cce:
            match = re.search(r"details/(catalogofcopyrig\w+)/page/n\d+", source["primaryUrl"])
            if match:
                with self.subTest(source=source["id"]):
                    self.assertTrue(match.group(1).endswith("libr"))


if __name__ == "__main__":
    unittest.main()
