"""Independent disc identifications must not erase transfer-level uncertainty."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source

REVIEWED = {"SRC0719", "SRC0729", "SRC0746", "SRC0755", "SRC0758"}


class RecordingTransferReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {r["id"]: r for r in json.loads(
            (ROOT / "data/public/v1/sources.json").read_text())["records"]}
        cls.media = {r["id"]: r for r in json.loads(
            (ROOT / "data/public/v1/media.json").read_text())["records"]}

    def test_uploader_session_dates_are_not_issue_dates(self):
        for sid, date, display in (
            ("SRC0719", "1932-05", "c. May 1932"),
            ("SRC0755", "1932-03", "c. March 1932"),
            ("SRC0758", "1930", None),
        ):
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual(source["date"], date)
                self.assertEqual(source["dateRole"], "recording")
                self.assertEqual(source["dateQualifier"], "reported")
                self.assertEqual(source.get("dateDisplay"), display)

    def test_unspecified_title_year_does_not_become_a_session_date(self):
        source = self.sources["SRC0746"]
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1932", "described_item", "reported"))
        self.assertIn("without specifying a recording or issue date", source["researchNote"])

    def test_brunswick_session_and_specific_transfer_are_distinguished(self):
        source = self.sources["SRC0729"]
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1935-05-06", "recording", "confirmed"))
        self.assertIn("C971", source["fullCitation"])
        self.assertIn("C972", source["researchNote"])
        self.assertIn("particular transferred copy and take remain unverified", source["researchNote"])
        self.assertEqual(source["additionalLinks"][0]["url"],
                         "https://www.78discography.com/BRN7300.htm")

    def test_weber_corroboration_does_not_confirm_the_singer_or_matrix(self):
        source = self.sources["SRC0755"]
        self.assertIn("printed p. 321", source["researchNote"])
        self.assertIn("OD 879-2 remain uploader-supplied", source["researchNote"])
        self.assertIn("not treated as a confirmed singer identification", source["researchNote"])
        self.assertTrue(source["additionalLinks"][0]["url"].endswith("003.pdf#page=54"))

    def test_kristall_number_is_corrected_from_the_label_not_upload_metadata(self):
        source = self.sources["SRC0758"]
        self.assertIn("Best.-Nr. 3098", source["researchNote"])
        self.assertIn("Kristall 3098", self.media["M392"]["publicCaption"])
        self.assertNotIn("78N", source["title"])
        self.assertIn("reported recording year", source["researchNote"])
        self.assertIn("4733", self.sources["SRC0719"]["researchNote"])

    def test_normalization_restores_reviewed_dates_and_is_idempotent(self):
        for sid in REVIEWED:
            with self.subTest(source=sid):
                source = self.sources[sid]
                stale = dict(source, dateRole="issue", dateQualifier="confirmed")
                self.assertEqual(normalized_source(stale), source)
                self.assertEqual(normalized_source(normalized_source(source)), source)

    def test_audit_log_preserves_corrections_and_media_keep_their_sources(self):
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        for sid, mid in zip(
            ("SRC0719", "SRC0729", "SRC0746", "SRC0755", "SRC0758"),
            ("M358", "M367", "M381", "M389", "M392"),
        ):
            with self.subTest(source=sid):
                source = self.sources[sid]
                fields = overrides["records"]["Sources"][sid]["fields"]
                self.assertEqual(fields["dateRole"], source["dateRole"])
                self.assertEqual(fields["researchNote"], source["researchNote"])
                self.assertEqual(self.media[mid]["sourceIds"], [sid])
                self.assertEqual(self.media[mid]["externalUrl"], source["primaryUrl"])
                self.assertEqual(self.media[mid]["rightsStatus"], "external_content_not_rehosted")
