import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HofmeisterPageLinkTests(unittest.TestCase):
    """The Hofmeister entries cited ANNO and linked the first page of the
    monthly issue, and ANNO refuses connections from cloud hosts, so the
    pages could not be reached to fix that. The Internet Archive holds every
    yearly volume from 1929 to 1933; each entry now opens on its scan there,
    found by its title and checked against the page its own citation gives,
    and the ANNO issue stays beside it as alternate access."""

    @classmethod
    def setUpClass(cls):
        sources = json.loads(
            (ROOT / "data/public/v1/sources.json").read_text(encoding="utf-8")
        )["records"]
        cls.register = [
            s for s in sources
            if "Musikalisch-literarischerMonatsbericht" in (s.get("primaryUrl") or "")
            or "aid=hof" in (s.get("primaryUrl") or "")
        ]

    def test_no_entry_still_opens_an_anno_issue(self):
        self.assertTrue(self.register)
        for source in self.register:
            with self.subTest(source=source["id"]):
                self.assertNotIn("anno.onb.ac.at", source["primaryUrl"])

    def test_every_entry_opens_on_a_scan_and_says_which(self):
        for source in self.register:
            url = source["primaryUrl"]
            match = re.search(r"/page/n(\d+)/", url)
            with self.subTest(source=source["id"]):
                self.assertIsNotNone(match, url)
                if "Internet Archive scan, leaf n" in source["fullCitation"]:
                    self.assertIn(f"leaf n{match.group(1)}", source["fullCitation"])

    def test_the_anno_issue_is_kept_as_alternate_access(self):
        moved = [s for s in self.register if any(
            "anno.onb.ac.at" in link.get("url", "") for link in s.get("additionalLinks") or []
        )]
        self.assertGreaterEqual(len(moved), 57)
        for source in moved:
            roles = {link["role"] for link in source["additionalLinks"] if "anno.onb.ac.at" in link["url"]}
            with self.subTest(source=source["id"]):
                self.assertEqual(roles, {"alternate_access"})
                self.assertIn("ORG067", source["organizationIds"])


if __name__ == "__main__":
    unittest.main()
