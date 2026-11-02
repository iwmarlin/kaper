"""Recording credits must describe the evidence actually linked to them."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source


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
                expected_context = (["recording_label", "online_recording"]
                                    if person == "P118" else ["recording_label"])
                self.assertEqual(c["evidenceContext"], expected_context)
                self.assertEqual(c["certainty"], "confirmed")
                self.assertEqual(c["personIds"], [person])
                expected_sources = {"SRC0756", "SRC0788"} if person == "P118" else {"SRC0788"}
                self.assertEqual(set(c["sourceIds"]), expected_sources)
                for sid in c["sourceIds"]:
                    self.assertIn(cid, self.sources[sid]["contributionIds"])
                self.assertIn("Parlophone AR 206 label", c["scopeNote"])
                self.assertIn("SRC0756", c["scopeNote"])
        self.assertIn("Sung in German", self.credits["CON-S059-P-P118"]["scopeNote"])
        self.assertIn("Conductor: Paul Dessau", self.credits["CON-S059-CON-P144"]["scopeNote"])
        self.assertNotIn("CON-S059-CON-P144", self.sources["SRC0756"]["contributionIds"])
        self.assertIn("featured artist", self.sources["SRC0756"]["fullCitation"])
        self.assertIn("does not specify his role", self.sources["SRC0756"]["researchNote"])
        self.assertIn("does not establish whether", self.sources["SRC0756"]["researchNote"])
        self.assertNotIn("conductor", self.sources["SRC0756"]["creator"])
        self.assertEqual(normalized_source(self.sources["SRC0756"]), self.sources["SRC0756"])
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
        removals = self.overrides["linkRemovals"]
        for key in ("creator", "fullCitation", "researchNote"):
            self.assertEqual(self.overrides["records"]["Sources"]["SRC0756"]["fields"][key], self.sources["SRC0756"][key])
        self.assertIn("CON-S059-CON-P144", removals["Sources"]["SRC0756"]["fields"]["contributionIds"])
        self.assertIn("SRC0756", removals["Contributions"]["CON-S059-CON-P144"]["fields"]["sourceIds"])


if __name__ == "__main__":
    unittest.main()
