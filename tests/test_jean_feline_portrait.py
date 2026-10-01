from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"


def records(filename: str) -> dict[str, dict]:
    payload = json.loads((PUBLIC / filename).read_text(encoding="utf-8"))
    return {record["id"]: record for record in payload["records"]}


class JeanFelinePortraitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.person = records("people.json")["P041"]
        self.medium = records("media.json")["M461"]
        self.source = records("sources.json")["SRC0935"]
        self.repository = records("organizations.json")["ORG062"]

    def test_portrait_identity_is_explicitly_qualified(self) -> None:
        self.assertEqual(self.medium["category"], "portrait")
        self.assertEqual(self.medium["rightsStatus"], "public_domain")
        self.assertIn("probable", self.medium["publicCaption"])
        self.assertEqual(self.source["researchNoteType"], "identity_assessment")
        self.assertIn("probable rather than certain", self.source["researchNote"])

    def test_press_source_graph_is_bidirectional(self) -> None:
        self.assertEqual(self.medium["sourceIds"], ["SRC0935"])
        self.assertEqual(self.source["mediaIds"], ["M461"])
        self.assertEqual(self.source["personIds"], ["P041"])
        self.assertIn("SRC0935", self.person["sourceIds"])
        self.assertEqual(self.source["organizationIds"], ["ORG062"])
        self.assertIn("SRC0935", self.repository["sourceIds"])

    def test_portrait_is_a_faithful_local_crop(self) -> None:
        asset = ROOT / self.medium["assetPath"]
        self.assertTrue(asset.is_file(), f"missing Jean Féline portrait: {asset}")
        self.assertNotIn("Piaz", self.medium["publicCreditLine"])
        self.assertIn("Excelsior", self.medium["publicCreditLine"])


if __name__ == "__main__":
    unittest.main()
