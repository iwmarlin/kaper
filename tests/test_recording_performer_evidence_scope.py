"""Recording credits must describe the evidence actually linked to them."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RecordingPerformerEvidenceScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.credits = {r["id"]: r for r in json.loads(
            (ROOT / "data/public/v1/contributions.json").read_text())["records"]}
        cls.sources = {r["id"]: r for r in json.loads(
            (ROOT / "data/public/v1/sources.json").read_text())["records"]}
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    def test_tauber_and_dessau_have_recording_not_film_evidence(self):
        for cid, person in (("CON-S059-P-P118", "P118"),
                            ("CON-S059-CON-P144", "P144")):
            with self.subTest(credit=cid):
                c = self.credits[cid]
                self.assertEqual(c["evidenceContext"], ["recording_label", "online_recording"])
                self.assertEqual(c["certainty"], "confirmed")
                self.assertEqual(c["personIds"], [person])
                self.assertEqual(set(c["sourceIds"]), {"SRC0756", "SRC0788"})
                for sid in c["sourceIds"]:
                    self.assertIn(cid, self.sources[sid]["contributionIds"])
                self.assertIn("Parlophone AR 206 label", c["scopeNote"])
                self.assertIn("SRC0756", c["scopeNote"])
        self.assertIn("Sung in German", self.credits["CON-S059-P-P118"]["scopeNote"])
        self.assertIn("Conductor: Paul Dessau", self.credits["CON-S059-CON-P144"]["scopeNote"])
        self.assertNotIn("carries no disc data", self.credits["CON-S059-P-P118"]["scopeNote"])

    def test_duchin_evidence_is_a_discography_not_a_label_reading(self):
        c = self.credits["CON-S119-P-P133"]
        self.assertEqual(c["evidenceContext"], ["discography", "online_recording"])
        self.assertEqual(c["sourceIds"], ["SRC0006"])
        self.assertIn(c["id"], self.sources["SRC0006"]["contributionIds"])
        self.assertIn("Bolig", c["scopeNote"])
        self.assertIn("29 April 1935", c["scopeNote"])
        self.assertIn("8 May 1935", c["scopeNote"])
        self.assertIn("not independently established", c["scopeNote"])
        self.assertEqual(c["certainty"], "confirmed")

    def test_export_overrides_preserve_the_reviewed_context_and_scope(self):
        for cid in ("CON-S059-P-P118", "CON-S059-CON-P144", "CON-S119-P-P133"):
            with self.subTest(credit=cid):
                fields = self.overrides["records"]["Contributions"][cid]["fields"]
                for key in ("evidenceContext", "scopeNote"):
                    self.assertEqual(fields[key], self.credits[cid][key])


if __name__ == "__main__":
    unittest.main()
