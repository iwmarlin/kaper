"""A portrait on the people index is somebody else's photograph."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PersonIndexPortraitTests(unittest.TestCase):
    """Thirty-seven portraits sat on the people index as bare images: no credit,
    no licence, and nothing to click through to. Two of them are Bundesarchiv
    photographs under CC BY-SA 3.0 DE, where attribution is a condition of the
    licence rather than a courtesy. A four-rem avatar has no room for a credit
    line, so the row links the portrait to the media record that carries one."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (ROOT / "people.html").read_text(encoding="utf-8")
        cls.index = json.loads(
            (ROOT / "data/site/indexes/people.json").read_text(encoding="utf-8"))

    def test_every_portrait_links_to_the_record_that_credits_it(self) -> None:
        avatars = re.findall(r'<div class="person-row__avatar">(.*?)</div>',
                             self.page, flags=re.S)
        with_image = [a for a in avatars if "person-row__portrait" in a and "<img" in a]
        self.assertGreater(len(with_image), 20, "no portraits were found on the index")
        unlinked = [a[:120] for a in with_image
                    if not re.search(r'<a class="person-row__portrait-link" '
                                     r'href="records/media/M\d+/"', a)]
        self.assertEqual(unlinked, [], "a portrait is shown with no way to its credit")

    def test_the_index_payload_carries_the_medium_behind_each_portrait(self) -> None:
        items = [item for item in self.index.get("records", [])
                 if isinstance(item, dict) and item.get("portrait")]
        self.assertGreater(len(items), 50, "no portraits in the people index payload")
        missing = [item["id"] for item in items
                   if not str(item["portrait"].get("mediaId") or "").startswith("M")]
        self.assertEqual(missing, [], "a portrait names no medium to credit")

    def test_the_link_fills_the_avatar_rather_than_the_image(self) -> None:
        # A grid item sized by its own content cannot take a percentage height
        # against the row it is sizing; the link is taken out of flow instead.
        css = (ROOT / "assets/site/styles.css").read_text(encoding="utf-8")
        rule = re.search(r"\.person-row__portrait-link\s*\{([^}]*)\}", css)
        self.assertIsNotNone(rule, "the portrait link has no rule")
        body = rule.group(1)
        self.assertIn("position: absolute", body)
        self.assertIn("inset: 0", body)
        avatar = re.search(r"\.person-row__avatar\s*\{([^}]*)\}", css)
        self.assertIn("position: relative", avatar.group(1))


if __name__ == "__main__":
    unittest.main()
