"""Arrangement credits must reflect the role and the source actually examined."""
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def records(table):
    payload = json.loads((ROOT / "data/public/v1" / f"{table}.json").read_text())
    return {record["id"]: record for record in payload["records"]}


class ArrangerEvidenceReviewTests(unittest.TestCase):
    def test_film_arrangement_notes_do_not_claim_musical_direction(self):
        credits = records("contributions")
        for ident, expected in (("CON-F007-A-P149", "Arrangement"),
                                ("CON-F024-A-P145", "Musik-Bearbeitung")):
            with self.subTest(credit=ident):
                credit = credits[ident]
                self.assertEqual(credit["role"], "arranger")
                self.assertEqual(credit["creditAsPrinted"], expected)
                self.assertIn("does not", credit["scopeNote"])
                self.assertNotIn("musical direction or arrangement", credit["scopeNote"])

    def test_examined_cover_and_fiesta_sample_support_their_arranger_credits(self):
        credits = records("contributions")
        source = records("sources")["SRC0789"]
        for ident in ("CON-O007-A-P009", "CON-O012-A-P009"):
            with self.subTest(credit=ident):
                self.assertIn("SRC0789", credits[ident]["sourceIds"])
                self.assertIn(ident, source["contributionIds"])
        fiesta = credits["CON-O012-A-P009"]
        self.assertEqual(fiesta["nameAsPrinted"], "Dr. B. Kaper")
        self.assertEqual(fiesta["creditAsPrinted"], "Transcription for 2 Pianos by Dr. B. Kaper")
        self.assertEqual(fiesta["nameVariantIds"], ["PNV0021"])
        self.assertIn("sheet_music", fiesta["evidenceContext"])
        self.assertIn("W-O012", records("person-name-variants")["PNV0021"]["workIds"])
        self.assertIn("PNV0021", records("works")["W-O012"]["nameVariantIds"])
        self.assertIn("PNV0021", source["nameVariantIds"])


if __name__ == "__main__":
    unittest.main()
