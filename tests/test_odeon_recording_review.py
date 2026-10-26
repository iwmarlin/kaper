"""Keep independently checked Odeon chronology distinct from upload claims."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source

REVIEWED = {"SRC0487": "M395", "SRC0697": "M338", "SRC0699": "M340", "SRC0790": "M411"}


class OdeonRecordingReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for table in ("sources", "media", "contributions"):
            rows = json.loads((ROOT / "data/public/v1" / f"{table}.json").read_text())["records"]
            setattr(cls, table, {r["id"]: r for r in rows})
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    def test_kiepura_disc_is_identified_from_label_and_runout(self):
        source = self.sources["SRC0487"]
        for text in ("O-4707 a", "Be 10220", "take 2", "Weissmann"):
            self.assertIn(text, source["fullCitation"])
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1933-02-11", "recording", "confirmed"))
        self.assertIn("Internet Archive instead supplies 1932", source["researchNote"])
        self.assertIn("release-date column empty", source["researchNote"])
        self.assertIn("indexed PDF text was consulted", source["researchNote"])
        self.assertTrue(source["additionalLinks"][0]["url"].endswith("_itemimage.jpg"))

    def test_publisher_credit_is_not_supported_by_the_record_label(self):
        cid = "CON-S078-PUB-ORG029"
        self.assertEqual(self.contributions[cid]["sourceIds"], ["SRC0297"])
        self.assertNotIn(cid, self.sources["SRC0487"]["contributionIds"])
        removals = self.overrides["linkRemovals"]
        self.assertIn(cid, removals["Sources"]["SRC0487"]["fields"]["contributionIds"])
        self.assertIn("SRC0487", removals["Contributions"][cid]["fields"]["sourceIds"])

    def test_albers_issue_month_is_distinct_from_session_date(self):
        for sid in ("SRC0697", "SRC0699"):
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                                 ("1933-04", "issue", "confirmed"))
                self.assertIn("13 February 1933", source["researchNote"])
                self.assertEqual(source["additionalLinks"][0]["url"],
                                 "http://musiktiteldb.de/Label/Ode_11.html")
        self.assertNotIn("10227-2", self.sources["SRC0697"]["fullCitation"])
        self.assertIn("without a take suffix", self.sources["SRC0697"]["researchNote"])

    def test_other_side_label_is_not_direct_orchestra_or_conductor_evidence(self):
        for cid in ("CON-S080-CON-P167", "CON-S080-P-ORG120"):
            with self.subTest(credit=cid):
                credit = self.contributions[cid]
                self.assertEqual(credit["certainty"], "probable")
                self.assertEqual(credit["evidenceContext"], ["online_recording"])
                self.assertIn("uploader", credit["scopeNote"])
        for cid in ("CON-S080-P-P153", "CON-S080-LAB-ORG128"):
            self.assertEqual(self.contributions[cid]["certainty"], "confirmed")
            self.assertEqual(self.contributions[cid]["evidenceContext"], ["discography"])
        self.assertEqual(self.contributions["CON-S081-CON-P167"]["certainty"], "confirmed")

    def test_bela_upload_has_no_verified_carrier_identification(self):
        source = self.sources["SRC0790"]
        self.assertEqual(source["sourceType"], "online_audio_source")
        self.assertEqual(source["publication"], "YouTube")
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1932", "recording", "reported"))
        self.assertNotIn("11667", source["title"])
        self.assertNotIn("9946", source["fullCitation"])
        self.assertIn("same list also assigns Be 9946", source["researchNote"])
        self.assertIn("Heute Nacht oder nie!", source["researchNote"])
        self.assertIn("Bob Henders", source["fullCitation"])
        self.assertIn("does not by itself resolve", source["researchNote"])
        self.assertNotIn("O-11667", self.media["M411"]["publicCreditLine"])

    def test_bela_catalogue_credits_do_not_claim_to_identify_the_upload(self):
        for cid in ("CON-S071-P-ORG144", "CON-S071-LAB-ORG128"):
            credit = self.contributions[cid]
            self.assertEqual(credit["evidenceContext"], ["discography"])
            self.assertIn("Henry König", credit["scopeNote"])
            self.assertNotIn("recorded in Berlin on 10 June", credit["scopeNote"])
        self.assertIn("not a separately verified conductor identification",
                      self.contributions["CON-S071-CON-P205"]["scopeNote"])

    def test_review_is_idempotent_and_preserved_by_the_audit_log(self):
        for sid, mid in REVIEWED.items():
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual(normalized_source(source), source)
                stale = dict(source, date="1930", dateRole="publication", researchNote="Old note",
                             fullCitation="Old citation", sourceType="recording_discographic_source")
                self.assertEqual(normalized_source(stale), source)
                self.assertEqual(self.overrides["records"]["Sources"][sid]["fields"]["researchNote"],
                                 source["researchNote"])
                self.assertEqual(self.media[mid]["sourceIds"], [sid])
                self.assertEqual(self.media[mid]["externalUrl"], source["primaryUrl"])
                self.assertEqual(self.media[mid]["rightsStatus"], "external_content_not_rehosted")
