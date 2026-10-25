"""Qualified upload claims must remain distinct from independent discography."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source


class RecordingEvidenceFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = cls.load("sources")
        cls.credits = cls.load("contributions")
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    @staticmethod
    def load(table):
        return {r["id"]: r for r in json.loads((ROOT / f"data/public/v1/{table}.json").read_text())["records"]}

    def test_four_uploader_only_credits_remain_qualified(self):
        expected = {
            "CON-S026-P-P077": "SRC0715", "CON-S030-CON-P167": "SRC0727",
            "CON-S003-CON-P119": "SRC0738", "CON-S003-LAB-ORG132": "SRC0738",
        }
        for credit_id, source_id in expected.items():
            with self.subTest(credit=credit_id):
                credit = self.credits[credit_id]
                self.assertEqual(credit["certainty"], "probable")
                self.assertEqual(credit["sourceIds"], [source_id])
                self.assertEqual(credit["evidenceContext"], ["online_catalogue"])
                self.assertIn("uploader-level", credit["scopeNote"])
                self.assertEqual(self.overrides["records"]["Contributions"][credit_id]["fields"]["certainty"], "probable")

    def test_independent_catalogue_credits_keep_their_certainty(self):
        expected = {
            "CON-S082-P-ORG120": "discography",
            "CON-S060-P-ORG148": "online_catalogue",
            "CON-S071-P-ORG144": "discography",
            "CON-S071-LAB-ORG128": "discography",
            "CON-S118-P-P173": "discography",
        }
        for credit_id, context in expected.items():
            with self.subTest(credit=credit_id):
                credit = self.credits[credit_id]
                self.assertEqual(credit["certainty"], "confirmed")
                self.assertEqual(credit["evidenceContext"], [context])

    def test_jones_note_retains_both_separate_issues(self):
        credit = self.credits["CON-S118-P-P173"]
        self.assertEqual(credit["sourceIds"], ["SRC0748", "SRC0784"])
        for text in ["Great 78 Project", "B.8724", "OA09937", "Victor 4381"]:
            self.assertIn(text, credit["scopeNote"])
        self.assertNotIn("credit is transcribed from the label by the uploader", credit["scopeNote"])

    def test_source_wording_survives_normalization(self):
        for source_id in ["SRC0715", "SRC0727", "SRC0738", "SRC0790"]:
            with self.subTest(source=source_id):
                source = self.sources[source_id]
                self.assertIn("upload", source["fullCitation"].lower())
                self.assertEqual(normalized_source(dict(source, fullCitation="Old citation")), source)
        source = self.sources["SRC0790"]
        self.assertIn("The upload reports a music credit", source["researchNote"])
        self.assertNotIn("The label credits the music", source["researchNote"])

    def test_upload_dates_are_not_confused_with_recording_dates(self):
        self.assertEqual(self.sources["SRC0715"]["dateRole"], "digital_publication")
        self.assertEqual(self.sources["SRC0715"]["dateQualifier"], "confirmed")
        self.assertEqual(self.sources["SRC0727"]["dateQualifier"], "reported")
        self.assertEqual(self.sources["SRC0738"]["dateQualifier"], "reported")
        self.assertEqual(self.sources["SRC0790"]["dateQualifier"], "confirmed")


if __name__ == "__main__":
    unittest.main()
