"""Label evidence, session chronology and unidentified uploads stay distinct."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source

REVIEWED = {
    "SRC0004", "SRC0694", "SRC0695", "SRC0716", "SRC0717",
    "SRC0725", "SRC0740", "SRC0758", "SRC0782", "SRC0811",
}


class RecordingLabelAndSessionReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for table in ("sources", "media", "contributions"):
            records = json.loads((ROOT / "data/public/v1" / f"{table}.json").read_text())["records"]
            setattr(cls, table, {r["id"]: r for r in records})
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    def test_first_four_dates_are_not_silently_upgraded(self):
        for sid, year in (("SRC0694", "1930"), ("SRC0695", "1929"),
                          ("SRC0716", "1930"), ("SRC0717", "1931")):
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                                 (year, "recording", "reported"))
        for sid, page in (("SRC0716", "926"), ("SRC0717", "736")):
            self.assertIn(f"printed p. {page}", self.sources[sid]["researchNote"])
            self.assertEqual(len(self.sources[sid]["additionalLinks"]), 1)

    def test_kristall_coupling_and_year_have_different_evidence(self):
        for sid, mid in (("SRC0004", "M004"), ("SRC0758", "M392")):
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertIn("Kristall 3098", source["title"])
                self.assertNotIn("78", source["slug"])
                self.assertIn("Best.-Nr. 3098", source["researchNote"])
                self.assertIn("same physical copy", source["researchNote"])
                self.assertEqual((source["dateRole"], source["dateQualifier"]),
                                 ("recording", "reported"))
                self.assertIn("Kristall 3098", self.media[mid]["publicCreditLine"])

    def test_disc_does_not_prove_the_sheet_music_publisher(self):
        cid = "CON-S017-PUB-ORG033"
        self.assertEqual(self.contributions[cid]["sourceIds"], ["SRC0471"])
        self.assertNotIn(cid, self.sources["SRC0004"]["contributionIds"])
        removals = self.overrides["linkRemovals"]
        self.assertIn("SRC0004", removals["Contributions"][cid]["fields"]["sourceIds"])
        self.assertIn(cid, removals["Sources"]["SRC0004"]["fields"]["contributionIds"])

    def test_odeon_issue_month_is_not_the_session_date(self):
        source = self.sources["SRC0725"]
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1931-05", "issue", "confirmed"))
        self.assertIn("12 March 1931", source["researchNote"])
        self.assertIn("NE 05/1931", source["researchNote"])
        self.assertTrue(source["additionalLinks"][0]["url"].endswith(".pdf#page=156"))

    def test_australian_parlophone_has_a_label_but_no_issue_date(self):
        source = self.sources["SRC0782"]
        self.assertNotIn("date", source)
        self.assertEqual((source["dateRole"], source["dateQualifier"]), ("issue", "unknown"))
        self.assertIn("Australia", source["fullCitation"])
        self.assertIn("Be 9615", source["fullCitation"])
        self.assertIn("patent dates", source["researchNote"])
        self.assertTrue(source["additionalLinks"][0]["url"].endswith("_itemimage.jpg"))
        self.assertNotIn("sound alone", self.media["M406"]["publicCaption"])

    def test_decca_comparison_does_not_identify_the_uploaded_carrier(self):
        source = self.sources["SRC0740"]
        self.assertEqual(source["sourceType"], "online_audio_source")
        self.assertEqual((source["date"], source["dateQualifier"]), ("1937", "reported"))
        self.assertIn("DLA705", source["researchNote"])
        self.assertIn("not assigned to the transfer", source["researchNote"])
        self.assertNotIn("1257", source["fullCitation"])

    def test_jones_broadcast_conflict_is_not_a_verified_session(self):
        source = self.sources["SRC0811"]
        self.assertEqual((source["dateRole"], source["dateQualifier"]),
                         ("described_item", "uncertain"))
        self.assertIn("1939 RADIO SHOW", source["researchNote"])
        self.assertIn("JASCD110", source["researchNote"])
        credit = self.contributions["CON-S129-P-P173"]
        self.assertEqual(credit["certainty"], "probable")
        self.assertEqual(credit["evidenceContext"], ["online_recording"])
        self.assertNotIn("no contemporary documentation", credit["scopeNote"])

    def test_normalizer_and_audit_log_preserve_the_review(self):
        for sid in REVIEWED:
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual(normalized_source(source), source)
                stale = dict(source, researchNote="Outdated transfer assessment")
                self.assertEqual(normalized_source(stale), source)
                fields = self.overrides["records"]["Sources"][sid]["fields"]
                self.assertEqual(fields["researchNote"], source["researchNote"])
                for mid in source["mediaIds"]:
                    item = self.media[mid]
                    self.assertIn(sid, item["sourceIds"])
                    self.assertEqual(item["externalUrl"], source["primaryUrl"])
                    self.assertEqual(item["rightsStatus"], "external_content_not_rehosted")
