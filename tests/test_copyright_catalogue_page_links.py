import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Every entry opens on its page. Each was placed on its scan by two signals
# that agree — its title, and its registration number or its entry number
# with the neighbouring entry numbers on the same scan — and the weaker
# matches were read on the page image.


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

    def test_every_entry_opens_on_its_page(self):
        self.assertEqual(len(self.cce), 89)
        for source in self.cce:
            with self.subTest(source=source["id"]):
                self.assertRegex(source["primaryUrl"], r"/page/n?\d+")

    def test_the_registration_numbers_read_on_the_scans_are_recorded(self):
        by_id = {s["id"]: s for s in self.cce}
        for source_id, number in (("SRC0257", "E unp. 136678"), ("SRC0259", "E unp. 137471")):
            with self.subTest(source=source_id):
                source = by_id[source_id]
                self.assertIn(number, source["fullCitation"])
                self.assertIn(number, [i["value"] for i in source.get("identifiers") or []])

    def test_scan_index_links_name_the_volume_they_were_found_in(self):
        for source in self.cce:
            match = re.search(r"details/(catalogofcopyrig\w+)/page/n\d+", source["primaryUrl"])
            if match:
                with self.subTest(source=source["id"]):
                    self.assertTrue(match.group(1).endswith("libr"))


if __name__ == "__main__":
    unittest.main()
