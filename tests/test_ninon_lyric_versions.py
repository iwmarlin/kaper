import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def records(table):
    data = json.loads((ROOT / "data/public/v1" / f"{table}.json").read_text())
    return {item["id"]: item for item in data["records"]}


class NinonLyricVersionsTests(unittest.TestCase):
    def test_credit_scopes_and_reciprocal_evidence(self):
        credits = records("contributions")
        sources = records("sources")
        work = records("works")["W-S077"]
        people = records("people")
        cases = (
            ("CON-S077-L-P010", "P010", "concert version"),
            ("CON-S077-L-P033", "P033", "film version"),
            ("CON-S077-L-P206", "P206", "film version"),
        )
        for cid, pid, phrase in cases:
            with self.subTest(credit=cid):
                credit = credits[cid]
                self.assertIn(phrase, credit["scopeNote"])
                self.assertIn(cid, work["contributionIds"])
                self.assertIn(pid, work["personIds"])
                self.assertIn(cid, people[pid]["contributionIds"])
                for sid in ("SRC0298", "SRC0584"):
                    self.assertIn(sid, credit["sourceIds"])
                    self.assertIn(cid, sources[sid]["contributionIds"])

    def test_public_page_and_search_description_distinguish_versions(self):
        page = (ROOT / "records/work/W-S077/index.html").read_text()
        self.assertIn("Lyrics for the concert version.", page)
        self.assertIn("Lyrics for the film version, with Serge Veber.", page)
        self.assertIn("Lyrics for the film version, with Georges Clouzot.", page)
        self.assertNotIn("with words by Ch.-L. Pothier, Henri-Georges Clouzot and Serge Veber", page)
        self.assertIn("concert-version lyrics", page)
        self.assertTrue((ROOT / "records/person/P206/index.html").is_file())
