"""A shared master does not transfer one pressing's label to another."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source
from recording_organizations import expected_audio_organization_ids


class RecordingPressingScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = {}
        for name in ("sources", "media", "organizations", "contributions", "works", "songs"):
            cls.tables[name] = {r["id"]: r for r in json.loads(
                (ROOT / f"data/public/v1/{name}.json").read_text())["records"]}

    def test_gloria_issue_and_d4431_master_have_distinct_dates(self):
        source = self.tables["sources"]["SRC0939"]
        transfer = self.tables["sources"]["SRC0785"]
        self.assertEqual((source["date"], source["dateRole"]), ("1932-11", "issue"))
        self.assertEqual((transfer["date"], transfer["dateRole"]), ("1932-06-11", "recording"))
        self.assertIn("Gloria G.O. 10303, matrix Bi 644", source["fullCitation"])
        self.assertIn("label and issue date remain unestablished", transfer["researchNote"])

    def test_gloria_credit_is_supported_only_by_the_gloria_source(self):
        credit = self.tables["contributions"]["CON-S060-LAB-ORG138"]
        self.assertEqual(credit["sourceIds"], ["SRC0939"])
        self.assertEqual(credit["certainty"], "confirmed")
        self.assertIn(credit["id"], self.tables["sources"]["SRC0939"]["contributionIds"])
        self.assertNotIn(credit["id"], self.tables["sources"]["SRC0785"]["contributionIds"])

    def test_gloria_does_not_become_the_issuing_label_of_d4431(self):
        source = self.tables["sources"]["SRC0785"]
        media = self.tables["media"]["M409"]
        self.assertNotIn("ORG138", source["organizationIds"])
        self.assertEqual(media["organizationIds"], ["ORG148"])
        self.assertEqual(expected_audio_organization_ids(
            media, sources_by_id=self.tables["sources"],
            organizations_by_id=self.tables["organizations"],
            contributions=self.tables["contributions"].values()), ["ORG148"])
        self.assertIn("not assigned to D 4431", media["publicCaption"])

    def test_recording_level_evidence_remains_on_the_work_not_the_transfer(self):
        source = self.tables["sources"]["SRC0939"]
        self.assertEqual(source["organizationIds"], ["ORG138", "ORG148", "ORG173"])
        for oid in source["organizationIds"]:
            self.assertIn("SRC0939", self.tables["organizations"][oid]["sourceIds"])
        self.assertNotIn("SRC0785", self.tables["organizations"]["ORG138"]["sourceIds"])
        self.assertIn("ORG138", self.tables["works"]["W-S060"]["organizationIds"])
        self.assertIn("SRC0939", self.tables["works"]["W-S060"]["sourceIds"])
        self.assertIn("SRC0939", self.tables["songs"]["S060"]["sourceIds"])
        for cid in source["contributionIds"]:
            self.assertIn("SRC0939", self.tables["contributions"][cid]["sourceIds"])

    def test_no_second_listening_reference_is_created(self):
        source = self.tables["sources"]["SRC0939"]
        media = self.tables["media"]["M409"]
        self.assertFalse(source.get("mediaIds"))
        self.assertEqual(media["sourceIds"], ["SRC0785"])
        self.assertEqual(media["externalUrl"], self.tables["sources"]["SRC0785"]["primaryUrl"])
        self.assertEqual(media["rightsStatus"], "external_content_not_rehosted")

    def test_normalization_preserves_the_split(self):
        for sid in ("SRC0785", "SRC0939"):
            with self.subTest(source=sid):
                source = self.tables["sources"][sid]
                self.assertEqual(normalized_source(source), source)

    def test_audit_log_preserves_addition_and_removals(self):
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        source = self.tables["sources"]["SRC0939"]
        self.assertEqual(overrides["additions"]["Sources"]["SRC0939"]["fields"], source)
        self.assertIn("SRC0785", overrides["linkRemovals"]["Organizations"]["ORG138"]["fields"]["sourceIds"])
        self.assertIn("ORG138", overrides["linkRemovals"]["Media"]["M409"]["fields"]["organizationIds"])
        self.assertIn("SRC0939", overrides["linkAdditions"]["Works"]["W-S060"]["fields"]["sourceIds"])
