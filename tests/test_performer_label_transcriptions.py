"""Preserve individually checked performer and conductor label transcriptions."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PerformerLabelTranscriptionsTest(unittest.TestCase):
    def test_transcriptions_and_export_overrides_match_the_recorded_evidence(self):
        contributions = json.loads((ROOT / "data/public/v1/contributions.json").read_text())
        credits = {credit["id"]: credit for credit in contributions["records"]}
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        expected = {
            "CON-S017-P-ORG121": ("Bernard Etté und sein Orchester", "SRC0004"),
            "CON-S096-P-P132": ("Henry Garat", "SRC0764"),
            "CON-S001-CON-P169": ("Z. Wiehler", "SRC0736"),
            "CON-S002-CON-P169": ("Z. Wiehler", "SRC0737"),
        }
        for credit_id, (printed_name, source_id) in expected.items():
            with self.subTest(credit=credit_id):
                credit = credits[credit_id]
                fields = overrides["records"]["Contributions"][credit_id]["fields"]
                self.assertEqual(credit["nameAsPrinted"], printed_name)
                self.assertEqual(fields["nameAsPrinted"], printed_name)
                self.assertIn("recording_label", credit["evidenceContext"])
                self.assertIn(source_id, credit["sourceIds"])

    def test_garland_performance_credits_identify_film_excerpt_evidence(self):
        contributions = json.loads((ROOT / "data/public/v1/contributions.json").read_text())
        credits = {credit["id"]: credit for credit in contributions["records"]}
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        for credit_id, source_id in [("CON-S157-P-P138", "SRC0321"),
                                     ("CON-S161-P-P138", "SRC0809")]:
            with self.subTest(credit=credit_id):
                credit = credits[credit_id]
                fields = overrides["records"]["Contributions"][credit_id]["fields"]
                self.assertEqual(credit["evidenceContext"], ["film_song", "online_recording"])
                self.assertEqual(fields["evidenceContext"], credit["evidenceContext"])
                self.assertEqual(fields["scopeNote"], credit["scopeNote"])
                self.assertIn("film excerpt", credit["scopeNote"])
                self.assertIn(source_id, credit["sourceIds"])

    def test_macdonald_credit_distinguishes_synopsis_and_edited_video(self):
        contributions = json.loads((ROOT / "data/public/v1/contributions.json").read_text())
        credit = next(c for c in contributions["records"] if c["id"] == "CON-S130-P-P139")
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        fields = overrides["records"]["Contributions"][credit["id"]]["fields"]
        self.assertEqual(credit["evidenceContext"], ["filmographic_database", "online_recording"])
        self.assertEqual(fields["evidenceContext"], credit["evidenceContext"])
        self.assertEqual(fields["scopeNote"], credit["scopeNote"])
        self.assertIn("restored and sweetened", credit["scopeNote"])
        self.assertEqual(set(credit["sourceIds"]), {"SRC0144", "SRC0319"})

