"""A named digital singer is not automatically a verified film performance."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source


class JonesDigitalPerformanceScopeTests(unittest.TestCase):
    def test_two_releases_remain_recording_not_film_evidence(self):
        def records(table):
            return {r["id"]: r for r in json.loads(
                (ROOT / "data/public/v1" / (table + ".json")).read_text())["records"]}
        sources, media, credits = (records(t) for t in ("sources", "media", "contributions"))
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        for sid, mid, cid, date in (
            ("SRC0751", "M385", "CON-S155-P-P173", "2016-07-12"),
            ("SRC0815", "M430", "CON-S162-P-P173", "2018-01-29"),
        ):
            with self.subTest(source=sid):
                s, m, c = sources[sid], media[mid], credits[cid]
                self.assertEqual(c["evidenceContext"], ["online_recording"])
                self.assertEqual(c["personIds"], ["P173"])
                self.assertEqual(c["certainty"], "confirmed")
                self.assertEqual(c["sourceIds"], [sid])
                self.assertIn(cid, s["contributionIds"])
                self.assertEqual(m["sourceIds"], [sid])
                self.assertEqual(m["externalUrl"], s["primaryUrl"])
                self.assertEqual(m["rightsStatus"], "external_content_not_rehosted")
                self.assertEqual((s["date"], s["dateRole"]), (date, "digital_publication"))
                self.assertIn("does not independently establish", s["researchNote"])
                self.assertNotIn("performance recorded for", m["publicCaption"])
                self.assertEqual(normalized_source(s), s)
                stale = dict(s, researchNote="1937/1938 is the year of the film performance")
                self.assertEqual(normalized_source(stale), s)
                for table, rid, rec, fields in (
                    ("Sources", sid, s, ("researchNote",)),
                    ("Media", mid, m, ("publicCaption",)),
                    ("Contributions", cid, c, ("scopeNote", "evidenceContext")),
                ):
                    for field in fields:
                        self.assertEqual(overrides["records"][table][rid]["fields"][field], rec[field])
        outtake = credits["CON-S153-P-P173"]
        self.assertEqual(outtake["sourceIds"], ["SRC0749"])
        self.assertEqual(outtake["evidenceContext"], ["film_song"])
        self.assertIn("outtake", outtake["scopeNote"])


if __name__ == "__main__":
    unittest.main()
