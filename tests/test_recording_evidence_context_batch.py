"""Recording descriptions must not overstate uploader or issue evidence."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPLOADER_CREDITS = [
    "CON-S009-P-P086",
    "CON-S009-CON-P165",
    "CON-S070-CON-P165",
    "CON-S026-P-P077",
    "CON-S009-P-ORG119",
    "CON-S070-P-ORG119",
    "CON-S080-P-ORG120",
    "CON-S064-P-ORG124",
    "CON-S080-CON-P167",
    "CON-S009-LAB-ORG126",
    "CON-S070-LAB-ORG126",
    "CON-S064-LAB-ORG155",
    "CON-S030-CON-P167",
    "CON-S076-P-ORG120",
    "CON-S076-LAB-ORG128",
    "CON-S054-LAB-ORG126",
    "CON-S074-P-ORG121",
    "CON-S074-LAB-ORG138",
    "CON-S003-CON-P119",
    "CON-S003-LAB-ORG132",
    "CON-S033-P-ORG140",
    "CON-S033-LAB-ORG138",
    "CON-S067-P-ORG119",
    "CON-S067-CON-P165",
    "CON-S067-LAB-ORG126",
    "CON-S218-LAB-ORG132",
    "CON-S008-P-ORG134"
]

class RecordingEvidenceContextBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def records(name):
            return {r["id"]: r for r in json.loads((ROOT / "data/public/v1" /
                    (name + ".json")).read_text())["records"]}
        cls.credits = records("contributions")
        cls.sources = records("sources")
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    def test_27_uploader_credits_keep_qualified_identity_and_reciprocal_links(self):
        self.assertEqual(len(UPLOADER_CREDITS), 27)
        for cid in UPLOADER_CREDITS:
            with self.subTest(credit=cid):
                credit = self.credits[cid]
                self.assertEqual(credit["certainty"], "probable")
                self.assertEqual(credit["evidenceContext"], ["online_recording"])
                self.assertIn("upload", credit["scopeNote"].lower())
                self.assertEqual(len(credit["sourceIds"]), 1)
                for sid in credit["sourceIds"]:
                    self.assertIn(cid, self.sources[sid]["contributionIds"])
                fields = self.overrides["records"]["Contributions"][cid]["fields"]
                self.assertEqual(fields["evidenceContext"], ["online_recording"])

    def test_hmv_label_does_not_certify_a_victor_session(self):
        label = self.credits["CON-S158-LAB-ORG147"]
        singer = self.credits["CON-S158-P-P173"]
        self.assertEqual(label["organizationIds"], ["ORG147"])
        self.assertEqual(singer["personIds"], ["P173"])
        for c in (label, singer):
            self.assertEqual(c["sourceIds"], ["SRC0783"])
            self.assertEqual(c["certainty"], "confirmed")
            self.assertEqual(c["evidenceContext"], ["recording_label"])
            self.assertIn("OA.09934", c["scopeNote"])
        self.assertIn("does not independently establish", label["scopeNote"])
        self.assertIn("not an independently verified", singer["scopeNote"])

    def test_odeon_credit_distinguishes_catalogue_and_companion_label(self):
        label = self.credits["CON-S082-LAB-ORG128"]
        singer = self.credits["CON-S082-P-P153"]
        self.assertEqual(label["organizationIds"], ["ORG150"])
        self.assertEqual(label["sourceIds"], ["SRC0700"])
        self.assertEqual(label["evidenceContext"], ["online_catalogue"])
        self.assertIn("catalogue evidence", label["scopeNote"])
        self.assertIn("not a fresh reading", label["scopeNote"])
        self.assertEqual(singer["sourceIds"], ["SRC0698", "SRC0700"])
        self.assertEqual(singer["evidenceContext"], ["online_catalogue", "online_recording"])
        self.assertIn("not direct evidence", singer["scopeNote"])
        for c in (label, singer):
            self.assertEqual(c["certainty"], "confirmed")
            fields = self.overrides["records"]["Contributions"][c["id"]]["fields"]
            self.assertEqual(fields["scopeNote"], c["scopeNote"])
            for sid in c["sourceIds"]:
                self.assertIn(c["id"], self.sources[sid]["contributionIds"])
        for cid in ("CON-S158-LAB-ORG147", "CON-S158-P-P173"):
            self.assertEqual(self.overrides["records"]["Contributions"][cid]["fields"]["scopeNote"],
                             self.credits[cid]["scopeNote"])

if __name__ == "__main__":
    unittest.main()

