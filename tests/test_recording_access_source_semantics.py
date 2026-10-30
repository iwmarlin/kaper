"""Do not promote a listening copy into a verified physical-disc description."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source
from recording_sources import private_upload_semantic_errors

ACCESS = {
    "SRC0707": ("1929", "described_item"),
    "SRC0730": ("1933", "issue"),
    "SRC0735": ("1933", "recording"),
    "SRC0738": ("1926", "recording"),
    "SRC0759": ("1937", "described_item"),
}
REVIEWED = set(ACCESS) | {"SRC0731"}


class RecordingAccessSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = cls.load("sources")
        cls.credits = cls.load("contributions")
        cls.media = cls.load("media")

    @staticmethod
    def load(name):
        return {r["id"]: r for r in json.loads((ROOT / f"data/public/v1/{name}.json").read_text())["records"]}

    def test_five_unidentified_carriers_are_access_sources(self):
        for sid, (date, role) in ACCESS.items():
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual(source["sourceType"], "online_audio_source")
                self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                                 (date, role, "reported"))
                self.assertNotIn("publication", source)
                self.assertIn("YouTube", source["title"])
                self.assertIn("upload", source["researchNote"].lower())

    def test_specific_but_unverified_disc_identification_is_qualified(self):
        source = self.sources["SRC0731"]
        self.assertEqual(source["sourceType"], "recording_discographic_source")
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1932", "recording", "reported"))
        self.assertIn("E.G. 2481", source["fullCitation"])
        self.assertIn("60-1853", source["fullCitation"])
        self.assertIn("the upload identifies", source["fullCitation"])
        self.assertIn("uploader-level", self.credits["CON-S054-LAB-ORG126"]["scopeNote"])
        self.assertEqual(self.credits["CON-S054-LAB-ORG126"]["certainty"], "probable")

    def test_sole_upload_credits_are_probable_but_independent_credits_remain_confirmed(self):
        for credit in self.credits.values():
            sources = set(credit.get("sourceIds", []))
            if sources and sources <= REVIEWED:
                with self.subTest(credit=credit["id"]):
                    self.assertEqual(credit["certainty"], "probable")
        for cid in ("CON-S009-C-P009", "CON-S009-L-P020"):
            self.assertEqual(self.credits[cid]["certainty"], "confirmed")
            self.assertIn("SRC0103", self.credits[cid]["sourceIds"])

    def test_no_unproven_ninon_pressing_is_assigned_to_the_access_copy(self):
        self.assertEqual(self.media["M368"]["sourceIds"], ["SRC0730"])
        self.assertEqual(self.sources["SRC0583"]["sourceType"], "sound_recording_catalogue")
        self.assertIn("Odeon O-4661", self.sources["SRC0730"]["researchNote"])
        self.assertIn("not assigned to this transfer", self.sources["SRC0730"]["researchNote"])

    def test_listening_copies_and_external_rights_are_preserved(self):
        expected = {"M347": "SRC0707", "M368": "SRC0730", "M369": "SRC0731",
                    "M372": "SRC0735", "M377": "SRC0738", "M393": "SRC0759"}
        for mid, sid in expected.items():
            with self.subTest(medium=mid):
                medium = self.media[mid]
                self.assertEqual(medium["sourceIds"], [sid])
                self.assertIn(mid, self.sources[sid]["mediaIds"])
                self.assertEqual(medium["externalUrl"], self.sources[sid]["primaryUrl"])
                self.assertEqual(medium["mediaType"], "audio")
                self.assertEqual(medium["rightsStatus"], "external_content_not_rehosted")

    def test_normalization_restores_access_semantics_without_other_changes(self):
        for sid in REVIEWED:
            with self.subTest(source=sid):
                source = self.sources[sid]
                stale = dict(source, dateRole="issue", dateQualifier="confirmed")
                if sid in ACCESS:
                    stale.update(sourceType="recording_discographic_source", publication="Unverified label")
                self.assertEqual(normalized_source(stale), source)
                self.assertEqual(normalized_source(normalized_source(source)), source)

    def test_semantic_validation_rejects_regressions(self):
        for sid in REVIEWED:
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual(private_upload_semantic_errors(source), [])
                self.assertTrue(private_upload_semantic_errors(dict(source, dateQualifier="confirmed")))
                if sid in ACCESS:
                    self.assertTrue(private_upload_semantic_errors(dict(source, sourceType="recording_discographic_source")))
                    self.assertTrue(private_upload_semantic_errors(dict(source, publication="Unverified label")))
        # Do not classify unrelated sources using keyword or number heuristics.
        self.assertEqual(private_upload_semantic_errors({"id": "STEST", "sourceType": "recording_discographic_source"}), [])


if __name__ == "__main__":
    unittest.main()
