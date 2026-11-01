"""The newspaper's printed page must not be confused with its image number."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def records(name):
    return {r["id"]: r for r in json.loads((ROOT / "data/public/v1" / f"{name}.json").read_text())["records"]}


class ErklaReviewPageReferenceTest(unittest.TestCase):
    def test_source_credits_and_event_use_printed_page_two(self):
        source = records("sources")["SRC0521"]
        event = records("timeline-events")["TE0023"]
        contributions = records("contributions")
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())["records"]
        self.assertIn("evening edition, 10 December 1929, p. 2", source["fullCitation"])
        self.assertIn("image 12", source["fullCitation"])
        self.assertEqual(overrides["Sources"]["SRC0521"]["fields"]["fullCitation"], source["fullCitation"])
        self.assertIn("10 December 1929, p. 2", event["longDescription"])
        self.assertEqual(overrides["Timeline Events"]["TE0023"]["fields"]["longDescription"], event["longDescription"])
        for person_id in ("P009", "P088", "P089", "P090"):
            credit_id = f"CON-O011-P-{person_id}"
            with self.subTest(credit=credit_id):
                credit = contributions[credit_id]
                self.assertIn("p. 2 (image 12)", credit["evidenceLocator"])
                self.assertEqual(overrides["Contributions"][credit_id]["fields"]["evidenceLocator"], credit["evidenceLocator"])
                self.assertIn("SRC0521", credit["sourceIds"])

    def test_french_ninon_credit_identifies_catalogue_not_examined_disc(self):
        source = records("sources")["SRC0584"]
        credit = records("contributions")["CON-S077-P-P117"]
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())["records"]
        self.assertEqual(source["sourceType"], "sheet_music_catalogue")
        self.assertEqual(source["date"], "1933")
        self.assertEqual(source["dateRole"], "described_item")
        self.assertIn("© 1933", source["fullCitation"])
        self.assertIn("not the date of the online catalogue", source["researchNote"])
        self.assertEqual(credit["evidenceContext"], ["online_catalogue"])
        self.assertIn("does not identify a particular sound recording", credit["scopeNote"])
        for field, value in overrides["Sources"]["SRC0584"]["fields"].items():
            self.assertEqual(source[field], value, field)
        for field, value in overrides["Contributions"][credit["id"]]["fields"].items():
            self.assertEqual(credit[field], value, field)

    def test_dnb_ninon_matrix_is_not_assigned_to_a_different_transfer(self):
        source = records("sources")["SRC0583"]
        credit = records("contributions")["CON-S076-P-P117"]
        transfer = records("sources")["SRC0730"]
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())["records"]
        self.assertIn("Be.10221-4", source["fullCitation"])
        self.assertIn("full PDF could not be consulted", source["researchNote"])
        self.assertIn("not been independently matched", source["researchNote"])
        self.assertIn("not been independently matched", credit["scopeNote"])
        self.assertIn("not assigned to this transfer", transfer["researchNote"])
        self.assertEqual(overrides["Sources"]["SRC0583"]["fields"]["researchNote"], source["researchNote"])
        self.assertEqual(overrides["Contributions"][credit["id"]]["fields"]["scopeNote"], credit["scopeNote"])

