"""Publisher evidence is source-specific, not inherited from the work."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source
from recording_sources import (
    REVIEWED_RECORDING_PUBLISHER_CREDITS,
    reviewed_publisher_evidence_errors,
    reviewed_printed_number_errors,
)


REMOVED = {
    "SRC0008": "CON-S152-PUB-ORG035",
    "SRC0710": "CON-S049-PUB-ORG031",
    "SRC0712": "CON-S043-PUB-ORG029",
    "SRC0716": "CON-S024-PUB-ORG029",
    "SRC0717": "CON-S042-PUB-ORG031",
    "SRC0718": "CON-S046-PUB-ORG033",
    "SRC0753": "CON-S034-PUB-ORG031",
    "SRC0754": "CON-S057-PUB-ORG038",
}


class RecordingPublisherEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = {
            t: {r["id"]: r for r in json.loads(
                (ROOT / f"data/public/v1/{t}.json").read_text())["records"]}
            for t in ("sources", "contributions", "songs", "works", "organizations", "media")
        }

    def test_all_eleven_reviewed_publisher_scopes_are_consistent(self):
        self.assertEqual(len(REVIEWED_RECORDING_PUBLISHER_CREDITS), 11)
        for sid in REVIEWED_RECORDING_PUBLISHER_CREDITS:
            self.assertEqual(reviewed_publisher_evidence_errors(
                self.tables["sources"][sid], self.tables["contributions"]), [], sid)

    def test_unsupported_disc_links_are_removed_but_printed_evidence_survives(self):
        for sid, cid in REMOVED.items():
            source = self.tables["sources"][sid]
            credit = self.tables["contributions"][cid]
            self.assertNotIn(cid, source["contributionIds"])
            self.assertNotIn(sid, credit["sourceIds"])
            self.assertTrue(credit["sourceIds"], cid)
            self.assertEqual(credit["role"], "publisher")
            self.assertEqual(credit["certainty"], "confirmed")

    def test_validator_catches_either_direction_of_a_reintroduced_link(self):
        for sid, cid in REMOVED.items():
            source = copy.deepcopy(self.tables["sources"][sid])
            source["contributionIds"].append(cid)
            self.assertTrue(reviewed_publisher_evidence_errors(
                source, self.tables["contributions"]))
            credits = copy.deepcopy(self.tables["contributions"])
            credits[cid]["sourceIds"].append(sid)
            self.assertTrue(reviewed_publisher_evidence_errors(
                self.tables["sources"][sid], credits))

    def test_explicit_roehr_and_coda_evidence_is_not_removed(self):
        for sid, cid in (("SRC0695", "CON-S007-PUB-ORG118"),
                         ("SRC0705", "CON-S112-PUB-ORG030")):
            self.assertIn(cid, self.tables["sources"][sid]["contributionIds"])
            self.assertIn(sid, self.tables["contributions"][cid]["sourceIds"])
        self.assertIn("recording_label", self.tables["contributions"]["CON-S007-PUB-ORG118"]["evidenceContext"])
        self.assertIn("online_catalogue", self.tables["contributions"]["CON-S112-PUB-ORG030"]["evidenceContext"])

    def test_coda_source_and_organization_links_are_reciprocal(self):
        self.assertIn("ORG030", self.tables["sources"]["SRC0705"]["organizationIds"])
        self.assertIn("SRC0705", self.tables["organizations"]["ORG030"]["sourceIds"])
        self.assertNotIn("ORG035", self.tables["sources"]["SRC0008"]["organizationIds"])
        self.assertNotIn("SRC0008", self.tables["organizations"]["ORG035"]["sourceIds"])

    def test_echo_wording_survives_without_an_invented_salabert_publisher(self):
        self.assertEqual(self.tables["songs"]["S116"]["publisherAsPrinted"], "Éditions Echo")
        self.assertIn("Éditions Echo", self.tables["sources"]["SRC0115"]["fullCitation"])
        self.assertIn("Éditions Echo", self.tables["works"]["W-S116"]["publicNote"])
        self.assertIn("Éditions Echo", self.tables["media"]["M143"]["publicCaption"])
        self.assertNotIn("CON-S116-PUB-ORG039", self.tables["contributions"])
        for table, rid, key in (("sources", "SRC0115", "contributionIds"),
                                ("works", "W-S116", "contributionIds"),
                                ("organizations", "ORG039", "contributionIds")):
            self.assertNotIn("CON-S116-PUB-ORG039", self.tables[table][rid][key])
        self.assertIn("CON-S116-LAB-ORG039", self.tables["sources"]["SRC0115"]["contributionIds"])

    def test_session_is_not_called_an_issue_in_the_conductor_credit(self):
        note = self.tables["contributions"]["CON-S116-CON-P009"]["scopeNote"]
        self.assertIn("recording session", note)
        self.assertNotIn("issued 7 November", note)

    def test_three_60_numbers_are_not_promoted_to_matrices(self):
        for table, rid in (("sources", "SRC0717"), ("sources", "SRC0718"),
                           ("sources", "SRC0731"), ("media", "M356"),
                           ("media", "M357"), ("media", "M369")):
            self.assertEqual(reviewed_printed_number_errors(self.tables[table][rid]), [])
        for rid, number in (("SRC0717", "60-1740"), ("SRC0718", "60-1496"),
                            ("SRC0731", "60-1853")):
            stale = dict(self.tables["sources"][rid], fullCitation="matrix " + number)
            self.assertTrue(reviewed_printed_number_errors(stale))
        self.assertTrue(reviewed_printed_number_errors(
            dict(self.tables["media"]["M369"], publicCaption="matrix 60-1853")))

    def test_dolly_haas_description_does_not_assign_a_matrix_function(self):
        note = self.tables["sources"]["SRC0731"]["researchNote"]
        self.assertIn("without identifying its function", note)
        self.assertNotIn("uploader calls", note)

    def test_normalization_preserves_all_reviewed_metadata(self):
        for sid in set(REVIEWED_RECORDING_PUBLISHER_CREDITS) | {"SRC0731"}:
            source = self.tables["sources"][sid]
            self.assertEqual(normalized_source(source), source, sid)


if __name__ == "__main__":
    unittest.main()
