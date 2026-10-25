"""A filmed label identifies a disc but does not automatically date it."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source

REVIEWED = {"SRC0710", "SRC0712", "SRC0718", "SRC0724"}


class FilmedLabelChronologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {r["id"]: r for r in json.loads(
            (ROOT / "data/public/v1/sources.json").read_text())["records"]}
        cls.media = {r["id"]: r for r in json.loads(
            (ROOT / "data/public/v1/media.json").read_text())["records"]}

    def test_brioni_photograph_and_other_versions_do_not_date_weber_disc(self):
        source = self.sources["SRC0710"]
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1931", "issue", "reported"))
        self.assertIn("1930 photograph depicts Brioni and does not date the disc", source["researchNote"])
        self.assertIn("without a newly established session date", source["researchNote"])

    def test_novaphon_year_follows_the_correct_recording_group(self):
        source = self.sources["SRC0712"]
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1932", "recording", "confirmed"))
        self.assertIn("pp. 53–54", source["researchNote"])
        self.assertIn("Wien, 1932", source["researchNote"])
        self.assertIn("matrix 2647", source["fullCitation"])
        self.assertIn("supersedes the uploader’s approximate 1931 issue dating", source["researchNote"])
        self.assertIn("no month or day is inferred", source["researchNote"])
        self.assertTrue(source["additionalLinks"][0]["url"].endswith("discographie_oesterreich.pdf#page=53"))

    def test_hylton_date_is_a_session_not_a_commercial_release(self):
        source = self.sources["SRC0718"]
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1931-03-11", "recording", "confirmed"))
        self.assertIn("Recording Date", source["researchNote"])
        self.assertIn("issue date not established", source["fullCitation"])
        self.assertEqual(source["additionalLinks"][0]["url"], "https://www.jackhylton.com/mp3-downloads")

    def test_derby_ambiguous_date_column_does_not_acquire_a_false_role(self):
        source = self.sources["SRC0724"]
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1930-10", "described_item", "uncertain"))
        self.assertIn("1930-10-?", source["researchNote"])
        self.assertIn("..6 RB2", source["researchNote"])
        self.assertIn("neighbouring rows", source["researchNote"])
        self.assertIn("not expanded", source["researchNote"])

    def test_normalization_repairs_legacy_dates_and_is_idempotent(self):
        for sid in REVIEWED:
            with self.subTest(source=sid):
                source = self.sources[sid]
                stale = dict(source, date="1931", dateRole="issue", dateQualifier="reported")
                self.assertEqual(normalized_source(stale), source)
                self.assertEqual(normalized_source(normalized_source(source)), source)

    def test_captions_and_audit_log_keep_the_same_evidence_boundary(self):
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        for sid, mid in (("SRC0710", "M349"), ("SRC0712", "M351"),
                         ("SRC0718", "M357"), ("SRC0724", "M362")):
            with self.subTest(source=sid):
                source = self.sources[sid]
                fields = overrides["records"]["Sources"][sid]["fields"]
                self.assertEqual(fields["researchNote"], source["researchNote"])
                self.assertEqual(self.media[mid]["sourceIds"], [sid])
                self.assertEqual(self.media[mid]["externalUrl"], source["primaryUrl"])
                self.assertEqual(self.media[mid]["rightsStatus"], "external_content_not_rehosted")
        self.assertIn("Vienna, 1932", self.media["M351"]["publicCaption"])
        self.assertIn("11 March 1931", self.media["M357"]["publicCaption"])
        self.assertIn("October 1930", self.media["M362"]["publicCaption"])
