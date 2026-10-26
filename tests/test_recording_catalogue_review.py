"""Library records, matrix lists and listening transfers have separate scopes."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source
from recording_sources import (
    CATALOGUE_UNSUPPORTED_AUTHORSHIP, REVIEWED_RECORDING_CATALOGUES,
    recording_catalogue_evidence_errors,
)


class RecordingCatalogueReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = {
            t: {r["id"]: r for r in json.loads(
                (ROOT / f"data/public/v1/{t}.json").read_text())["records"]}
            for t in ("sources", "contributions", "media", "organizations", "person-name-variants")
        }

    def test_reviewed_catalogues_share_the_existing_source_type(self):
        self.assertEqual(len(REVIEWED_RECORDING_CATALOGUES), 10)
        for sid in REVIEWED_RECORDING_CATALOGUES:
            source = self.tables["sources"][sid]
            self.assertEqual(source["sourceType"], "sound_recording_catalogue")
            self.assertEqual(recording_catalogue_evidence_errors(
                source, self.tables["contributions"]), [], sid)

    def test_tahitian_recording_date_is_not_its_legal_deposit(self):
        source = self.tables["sources"]["SRC0625"]
        self.assertEqual((source["date"], source["dateRole"]), ("1937-06-23", "recording"))
        self.assertIn("[DL 1940]", source["fullCitation"])
        self.assertIn("legal deposit", source["researchNote"])
        self.assertIn("language code tah", source["researchNote"])
        self.assertEqual(source["workIds"], ["W-S123"])
        self.assertNotIn("W-S196", source["workIds"])
        self.assertIn("1937", self.tables["contributions"]["CON-S123-C-P155"]["scopeNote"])
        self.assertNotIn("issued by Pathé-Marconi in 1940", self.tables["contributions"]["CON-S123-C-P155"]["scopeNote"])

    def test_pathe_catalogue_brand_link_is_reciprocal(self):
        self.assertIn("ORG133", self.tables["sources"]["SRC0625"]["organizationIds"])
        self.assertIn("SRC0625", self.tables["organizations"]["ORG133"]["sourceIds"])

    def test_ninon_resolves_to_its_own_dnb_record_not_the_coupled_side(self):
        source = self.tables["sources"]["SRC0583"]
        self.assertEqual(source["primaryUrl"], "https://d-nb.info/380669366")
        self.assertIn("field 777", source["researchNote"])
        self.assertIn("380669358", source["researchNote"])
        self.assertIn("rate-limited", source["researchNote"])
        self.assertEqual(source["sourceStatus"], "verified_with_attribution_note")
        self.assertNotIn("accessUrl", source)
        self.assertTrue(any(link["url"] == "https://d-nb.info/380669358"
                            for link in source["additionalLinks"]))
        self.assertTrue(any("odmxBe10000.pdf" in link["url"]
                            for link in source["additionalLinks"]))

    def test_ninon_session_and_coupled_side_matrix_are_not_conflated(self):
        source = self.tables["sources"]["SRC0583"]
        self.assertEqual((source["date"], source["dateRole"]), ("1933-02-07", "recording"))
        self.assertIn("Be 10221", source["fullCitation"])
        self.assertNotIn("Be.10220-2", source["fullCitation"])
        self.assertIn("coupled", source["researchNote"])

    def test_library_entries_do_not_become_unprinted_composer_evidence(self):
        for sid, cids in CATALOGUE_UNSUPPORTED_AUTHORSHIP.items():
            for cid in cids:
                self.assertNotIn(cid, self.tables["sources"][sid]["contributionIds"])
                credit = self.tables["contributions"][cid]
                self.assertNotIn(sid, credit["sourceIds"])
                self.assertTrue(credit["sourceIds"])
                self.assertEqual(credit["certainty"], "confirmed")

    def test_semantic_validator_catches_reintroduced_credit_date_or_record_errors(self):
        credits = self.tables["contributions"]
        for sid, cids in CATALOGUE_UNSUPPORTED_AUTHORSHIP.items():
            cid = sorted(cids)[0]
            stale = copy.deepcopy(self.tables["sources"][sid])
            stale["contributionIds"].append(cid)
            self.assertTrue(recording_catalogue_evidence_errors(stale, credits))
            reverse = copy.deepcopy(credits)
            reverse[cid]["sourceIds"].append(sid)
            self.assertTrue(recording_catalogue_evidence_errors(self.tables["sources"][sid], reverse))
        self.assertTrue(recording_catalogue_evidence_errors(dict(
            self.tables["sources"]["SRC0625"], date="1940", dateRole="issue"), credits))
        self.assertTrue(recording_catalogue_evidence_errors(dict(
            self.tables["sources"]["SRC0583"], primaryUrl="https://d-nb.info/380669358"), credits))

    def test_catalogue_transcription_does_not_silently_resolve_lelievre_identity(self):
        credit = self.tables["contributions"]["CON-S112-L-P051"]
        self.assertEqual(credit["certainty"], "probable")
        self.assertIn("no forename", credit["scopeNote"])
        self.assertIn("online_catalogue", credit["evidenceContext"])
        self.assertIn("Jurmann-Kaber", self.tables["sources"]["SRC0802"]["fullCitation"])

    def test_undated_live_lists_do_not_inherit_their_coverage_years(self):
        for sid in ("SRC0741", "SRC0742"):
            source = self.tables["sources"][sid]
            self.assertEqual((source["dateRole"], source["dateQualifier"]), ("publication", "unknown"))
            self.assertNotIn("date", source)
            self.assertNotIn("sides recorded", source["fullCitation"])
            stale = dict(source, date="1930", dateEnd="1934", dateDisplay="1930–1934")
            self.assertEqual(normalized_source(stale), source)

    def test_ultraphon_authorship_has_reciprocal_catalogue_evidence(self):
        source = self.tables["sources"]["SRC0829"]
        for cid in ("CON-S016-C-P009", "CON-S016-L-P020"):
            self.assertIn(cid, source["contributionIds"])
            self.assertIn("SRC0829", self.tables["contributions"][cid]["sourceIds"])
        self.assertNotIn("date", source)
        self.assertIn("repeats matrix 15875", source["researchNote"])
        self.assertIn("381098273", source["researchNote"])

    def test_recorded_issues_do_not_certify_the_four_transferred_copies(self):
        for mid in ("M345", "M420", "M421", "M422"):
            medium = self.tables["media"][mid]
            self.assertIn("take", medium["publicCaption"])
            self.assertEqual(medium["rightsStatus"], "external_content_not_rehosted")
            self.assertEqual(medium["storageType"], "external")
        for mid in ("M345", "M421"):
            self.assertIn("[193.]", self.tables["media"][mid]["publicCaption"])

    def test_metadata_normalization_is_idempotent_and_keeps_reviewed_types(self):
        for sid in REVIEWED_RECORDING_CATALOGUES:
            source = self.tables["sources"][sid]
            self.assertEqual(normalized_source(source), source, sid)
            self.assertEqual(normalized_source(dict(source, sourceType="recording_discographic_source")), source, sid)


if __name__ == "__main__":
    unittest.main()
