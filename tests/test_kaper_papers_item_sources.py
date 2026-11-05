import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_records(name):
    path = ROOT / "data/public/v1" / name
    return json.loads(path.read_text(encoding="utf-8"))["records"]


class KaperPapersItemSourceTests(unittest.TestCase):
    """The American Heritage Center asks for Kaper Papers material to be cited
    by item, box and folder, and its 1970 accession list describes each
    manuscript separately. One collective Source once stood for seven early
    works and a song while two later songs each had their own; every
    manuscript now has a Source of its own, as the repository cites them."""

    @classmethod
    def setUpClass(cls):
        cls.sources = {s["id"]: s for s in read_records("sources.json")}
        cls.works = {w["id"]: w for w in read_records("works.json")}
        cls.holdings = [
            s for s in cls.sources.values()
            if s.get("sourceType") == "archival_manuscript_holding"
            and "Collection 03193" in (s.get("fullCitation") or "")
        ]

    def test_each_manuscript_source_documents_one_work(self):
        self.assertGreaterEqual(len(self.holdings), 10)
        for source in self.holdings:
            with self.subTest(source=source["id"]):
                self.assertEqual(len(source.get("workIds") or []), 1)

    def test_every_manuscript_held_there_has_its_own_source(self):
        manuscripts = [
            o for o in read_records("other-works.json")
            if o.get("materialStatus") == "manuscript"
            and "Kaper Papers" in (o.get("shelfmark") or "")
        ]
        self.assertEqual(len(manuscripts), 7)
        for item in manuscripts:
            work_id = item["workIds"][0]
            own = [s for s in self.holdings if s.get("workIds") == [work_id]]
            with self.subTest(work=work_id):
                self.assertEqual(len(own), 1, "one Source per manuscript")
                self.assertIn(own[0]["id"], self.works[work_id]["sourceIds"])

    def test_the_box_cited_is_the_box_the_work_records(self):
        for item in read_records("other-works.json"):
            shelf = re.search(r"box (\d)", item.get("shelfmark") or "")
            if not shelf or item.get("materialStatus") != "manuscript":
                continue
            for source in self.holdings:
                if source.get("workIds") == item["workIds"]:
                    with self.subTest(work=item["id"]):
                        self.assertIn(f"box {shelf.group(1)}", source["fullCitation"])

    def test_a_date_that_disagrees_with_the_accession_list_says_so(self):
        # The accession list gives the Piece for Voice and Orchestra as
        # "Berlin, 1926"; the work is kept at 1928. The Source carries the
        # work's year, marks it uncertain and quotes the list.
        source = next(s for s in self.holdings if s.get("workIds") == ["W-O030"])
        self.assertEqual((source["date"], source["dateQualifier"]), ("1928", "uncertain"))
        self.assertIn("Berlin, 1926", source["fullCitation"])


if __name__ == "__main__":
    unittest.main()
