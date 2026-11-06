"""Three performance scopes must not outgrow their linked witnesses."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RecordingFinalScopeReviewTests(unittest.TestCase):
    def test_scoped_descriptions_and_unchanged_evidence_links(self):
        def records(table):
            return {r["id"]: r for r in json.loads((ROOT / "data/public/v1" /
                    (table + ".json")).read_text())["records"]}
        credits, sources = records("contributions"), records("sources")
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        expected = {
            "CON-O019-P-P009": ("SRC0002", "personIds", "P009"),
            "CON-S009-P-P118": ("SRC0881", "personIds", "P118"),
            "CON-S057-P-ORG144": ("SRC0754", "organizationIds", "ORG144"),
        }
        for cid, (sid, field, subject) in expected.items():
            with self.subTest(credit=cid):
                c = credits[cid]
                self.assertEqual(c["sourceIds"], [sid])
                self.assertEqual(c[field], [subject])
                self.assertEqual(c["certainty"], "confirmed")
                self.assertIn(cid, sources[sid]["contributionIds"])
                self.assertEqual(overrides["records"]["Contributions"][cid]["fields"]["scopeNote"], c["scopeNote"])
        piano = credits["CON-O019-P-P009"]["scopeNote"]
        self.assertNotIn("Played the second piano", piano)
        self.assertIn("does not specify", piano)
        self.assertNotIn("published arrangement", piano)
        tauber = credits["CON-S009-P-P118"]["scopeNote"]
        self.assertIn("22 June 1929", tauber)
        self.assertIn("Be 8339", tauber)
        self.assertNotIn("AFI", tauber)
        self.assertNotIn("oral history", tauber)
        bela = credits["CON-S057-P-ORG144"]["scopeNote"]
        self.assertIn("O-11768 b", bela)
        self.assertIn("does not establish the recording location", bela)
        self.assertNotIn("in Berlin", bela)


if __name__ == "__main__":
    unittest.main()
