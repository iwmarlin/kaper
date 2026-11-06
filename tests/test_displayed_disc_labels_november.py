"""Disc labels visible in transfers remain distinct from uploader-only details."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def records(table):
    return {record["id"]: record for record in json.loads(
        (ROOT / "data/public/v1" / f"{table}.json").read_text()
    )["records"]}


class DisplayedDiscLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = records("sources")
        cls.media = records("media")
        cls.credits = records("contributions")
        cls.organizations = records("organizations")
        cls.works = records("works")

    def test_all_five_labels_and_existing_transfers(self):
        cases = {
            "SRC0719": ("M358", "24604"),
            "SRC0727": ("M365", "G-10027 a"),
            "SRC0730": ("M368", "O-4707 b"),
            "SRC0735": ("M372", "A 169240 a"),
            "SRC0746": ("M381", "G.O. 10197 b"),
        }
        for sid, (mid, number) in cases.items():
            with self.subTest(source=sid):
                self.assertIn(number, self.sources[sid]["fullCitation"])
                self.assertEqual(self.media[mid]["sourceIds"], [sid])
                self.assertEqual(self.media[mid]["externalUrl"], self.sources[sid]["primaryUrl"])
                self.assertEqual(self.sources[sid]["sourceType"], "recording_discographic_source")

    def test_odeon_label_is_not_misattributed_to_gloria(self):
        credit = self.credits["CON-S074-LAB-ORG138"]  # Stable historical ID.
        self.assertEqual(credit["organizationIds"], ["ORG150"])
        self.assertEqual(credit["nameAsPrinted"], "Odeon")
        self.assertEqual(self.media["M372"]["organizationIds"], ["ORG121", "ORG150"])
        for field, value in (("sourceIds", "SRC0735"), ("workIds", "W-S074"),
                             ("contributionIds", credit["id"])):
            self.assertIn(value, self.organizations["ORG150"][field])
            self.assertNotIn(value, self.organizations["ORG138"][field])
        self.assertNotIn("ORG138", self.works["W-S074"]["organizationIds"])

    def test_label_does_not_prove_unnamed_conductor_or_ninon_take(self):
        self.assertEqual(self.credits["CON-S030-CON-P167"]["certainty"], "probable")
        self.assertIn("does not name the singer or conductor", self.sources["SRC0727"]["researchNote"])
        self.assertIn("does not establish which take", self.sources["SRC0730"]["researchNote"])


if __name__ == "__main__":
    unittest.main()
