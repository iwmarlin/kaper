"""Uploader descriptions must not silently become verified disc-label evidence."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source


class UploaderEvidenceQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = cls.load("sources")
        cls.contributions = cls.load("contributions")
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    @staticmethod
    def load(table):
        return {r["id"]: r for r in json.loads((ROOT / f"data/public/v1/{table}.json").read_text())["records"]}

    def test_score_imprint_is_distinct_from_access_repository(self):
        source = self.sources["SRC0379"]
        self.assertEqual(source["publication"], "Gebethner i Wolff, Warszawa")
        self.assertEqual(source["creator"], "Bronisław Kaper (music); Andrzej Włast (words)")
        self.assertEqual(source["repository"], "Stare Melodie")
        self.assertIn("38004", source["additionalLinks"][0]["url"])
        changed = dict(source, publication="Stare Melodie")
        changed.pop("creator")
        self.assertEqual(normalized_source(changed), source)

    def test_recording_years_remain_reported_not_confirmed(self):
        for source_id, year in [("SRC0707", "1929"), ("SRC0759", "1937")]:
            with self.subTest(source=source_id):
                source = self.sources[source_id]
                self.assertEqual(source["date"], year)
                self.assertEqual(source["dateQualifier"], "reported")
                self.assertIn("upload", source["fullCitation"])
                self.assertNotIn("label credit", source["fullCitation"])
                self.assertEqual(normalized_source(dict(source, dateQualifier="confirmed")), source)

    def test_alrobi_credit_keeps_only_independent_score_evidence(self):
        credit_id = "CON-S009-PUB-ORG033"
        self.assertEqual(self.contributions[credit_id]["sourceIds"], ["SRC0103"])
        self.assertEqual(self.contributions[credit_id]["certainty"], "confirmed")
        self.assertNotIn(credit_id, self.sources["SRC0707"]["contributionIds"])
        removals = self.overrides["linkRemovals"]
        self.assertIn(credit_id, removals["Sources"]["SRC0707"]["fields"]["contributionIds"])
        self.assertIn("SRC0707", removals["Contributions"][credit_id]["fields"]["sourceIds"])

    def test_sole_upload_credits_are_qualified_in_data_and_export(self):
        ids = ["CON-S009-P-P086", "CON-S009-CON-P165", "CON-S009-P-ORG119",
               "CON-S009-LAB-ORG126", "CON-S218-C-P009", "CON-S218-C-P077",
               "CON-S218-L-P175", "CON-S218-LAB-ORG132"]
        for credit_id in ids:
            with self.subTest(credit=credit_id):
                credit = self.contributions[credit_id]
                self.assertEqual(credit["certainty"], "probable")
                self.assertEqual(credit["evidenceContext"], ["online_catalogue"])
                self.assertIn("upload", credit["scopeNote"].lower())
                fields = self.overrides["records"]["Contributions"][credit_id]["fields"]
                self.assertEqual(fields["certainty"], "probable")

    def test_independent_song_authorship_remains_confirmed(self):
        for credit_id in ["CON-S009-C-P009", "CON-S009-L-P020"]:
            self.assertEqual(self.contributions[credit_id]["certainty"], "confirmed")
            self.assertIn("SRC0103", self.contributions[credit_id]["sourceIds"])


if __name__ == "__main__":
    unittest.main()
