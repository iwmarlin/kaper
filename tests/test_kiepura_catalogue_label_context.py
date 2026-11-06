"""BN's coupled-disc catalogue is not a label inspection of both sides."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class KiepuraCatalogueLabelContextTests(unittest.TestCase):
    def test_both_performance_contexts_match_their_witnesses(self):
        def records(name):
            return {r["id"]: r for r in json.loads((ROOT / "data/public/v1" /
                    (name + ".json")).read_text())["records"]}
        credits, sources = records("contributions"), records("sources")
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        self.assertEqual(sources["SRC0633"]["sourceType"], "sound_recording_catalogue")
        self.assertEqual((sources["SRC0633"]["date"], sources["SRC0633"]["dateQualifier"],
                          sources["SRC0633"]["dateDisplay"]), ("1930", "after", "[post 1930]"))
        cases = {
            "CON-S214-P-P117": (["SRC0633"], ["online_catalogue"], "W-S214"),
            "CON-S215-P-P117": (["SRC0633", "SRC0761"],
                                ["online_catalogue", "recording_label"], "W-S215"),
        }
        for cid, (sids, contexts, wid) in cases.items():
            with self.subTest(credit=cid):
                c = credits[cid]
                self.assertEqual(c["sourceIds"], sids)
                self.assertEqual(c["evidenceContext"], contexts)
                self.assertEqual(c["personIds"], ["P117"])
                self.assertEqual(c["workIds"], [wid])
                self.assertEqual(c["certainty"], "confirmed")
                self.assertEqual(c["role"], "performer")
                for sid in sids:
                    self.assertIn(cid, sources[sid]["contributionIds"])
                self.assertEqual(overrides["records"]["Contributions"][cid]["fields"]["evidenceContext"], contexts)
        self.assertNotIn("CON-S214-P-P117", sources["SRC0761"]["contributionIds"])


if __name__ == "__main__":
    unittest.main()
