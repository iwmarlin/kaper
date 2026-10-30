from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"


def records(filename: str) -> dict[str, dict]:
    data = json.loads((PUBLIC / filename).read_text(encoding="utf-8"))["records"]
    return {record["id"]: record for record in data}


class NacioHerbBrownPortraitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.medium = records("media.json")["M441"]
        self.source = records("sources.json")["SRC0838"]
        self.person = records("people.json")["P179"]
        self.organization = records("organizations.json")["ORG090"]

    def test_portrait_uses_the_documented_public_domain_photoplay_image(self) -> None:
        self.assertEqual(self.medium["rightsStatus"], "public_domain")
        self.assertEqual(self.medium["galleryStatus"], "eligible")
        self.assertEqual(self.source["sourceType"], "wikimedia_commons_file")
        self.assertEqual(self.source["sourceStatus"], "verified")
        self.assertEqual(self.source["reliability"], "high")
        self.assertEqual(self.source["date"], "1929-10")
        self.assertIn("Photoplay", self.source["fullCitation"])
        self.assertIn("Photoplay_-_1929.10", self.source["primaryUrl"])

    def test_portrait_source_graph_is_bidirectional(self) -> None:
        self.assertEqual(self.medium["sourceIds"], ["SRC0838"])
        self.assertIn("M441", self.source["mediaIds"])
        self.assertIn("P179", self.source["personIds"])
        self.assertIn("SRC0838", self.person["sourceIds"])
        self.assertIn("ORG090", self.source["organizationIds"])
        self.assertIn("SRC0838", self.organization["sourceIds"])

    def test_non_free_wikipedia_provenance_does_not_survive(self) -> None:
        serialized = json.dumps(
            {"medium": self.medium, "source": self.source}, ensure_ascii=False
        )
        self.assertNotIn("NNDB", serialized)
        self.assertNotIn("permission_needed_or_fair_use_claimed", serialized)
        asset = ROOT / self.medium["assetPath"]
        self.assertTrue(asset.is_file(), f"missing portrait asset: {asset}")


if __name__ == "__main__":
    unittest.main()
