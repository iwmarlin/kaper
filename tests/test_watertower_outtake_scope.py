"""Keep the rights-holder outtake distinct from unproven film extractions."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source


class WaterTowerOuttakeScopeTests(unittest.TestCase):
    def test_outtake_remaster_and_access_date_are_distinct(self):
        def record(table, rid):
            return next(r for r in json.loads((ROOT / "data/public/v1" /
                        (table + ".json")).read_text())["records"] if r["id"] == rid)
        s = record("sources", "SRC0749")
        m = record("media", "M384")
        c = record("contributions", "CON-S153-P-P173")
        self.assertEqual((s["date"], s["dateRole"], s["dateQualifier"]),
                         ("2021-05-06", "digital_publication", "confirmed"))
        self.assertIn("2006 Remaster", s["fullCitation"])
        self.assertIn("℗ 1937", s["fullCitation"])
        self.assertIn("does not by itself establish", s["researchNote"])
        self.assertIn("automated composer fields", s["researchNote"])
        self.assertEqual(normalized_source(s), s)
        self.assertEqual(normalized_source(dict(s, date="2006", dateRole="issue")), s)
        self.assertEqual(c["evidenceContext"], ["film_song", "online_recording"])
        self.assertIn("not a performance heard in its finished version", c["scopeNote"])
        self.assertEqual(c["sourceIds"], [s["id"]])
        self.assertIn(c["id"], s["contributionIds"])
        self.assertEqual(m["sourceIds"], [s["id"]])
        self.assertEqual(m["externalUrl"], s["primaryUrl"])
        self.assertEqual(m["rightsStatus"], "external_content_not_rehosted")
        self.assertNotIn("Co..", m["publicCreditLine"])
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        for table, r, keys in (("Sources", s, ("date", "dateRole", "researchNote")),
                              ("Media", m, ("publicCaption", "publicCreditLine")),
                              ("Contributions", c, ("evidenceContext", "scopeNote"))):
            for key in keys:
                self.assertEqual(overrides["records"][table][r["id"]]["fields"][key], r[key])


if __name__ == "__main__":
    unittest.main()
