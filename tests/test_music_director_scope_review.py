"""Music-direction credits must not conflate direction with arrangement."""
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def records(table):
    data = json.loads((ROOT / "data/public/v1" / f"{table}.json").read_text())
    return {record["id"]: record for record in data["records"]}


class MusicDirectorScopeReviewTests(unittest.TestCase):
    def test_filmportal_direction_is_not_described_as_an_alternative_to_arrangement(self):
        credits = records("contributions")
        ids = (
            "CON-F002-MD-P146", "CON-F004-MD-P142", "CON-F007-MD-P144",
            "CON-F012-MD-P145", "CON-F017-MD-P143", "CON-F020-MD-P143",
            "CON-F023-MD-P142", "CON-F025-MD-P142", "CON-F026-MD-P143",
        )
        for ident in ids:
            with self.subTest(credit=ident):
                credit = credits[ident]
                self.assertEqual(credit["role"], "music_director")
                self.assertEqual(credit["creditAsPrinted"], "Musikalische Leitung")
                self.assertEqual(credit["scopeNote"],
                                 "filmportal.de lists this person under “Musikalische Leitung” for the film.")
                self.assertEqual(len(credit["sourceIds"]), 1)

    def test_two_separate_filmportal_headings_are_not_collapsed_into_one(self):
        credits = records("contributions")
        for ident, name in (("CON-F011-MD-P144", "Paul Dessau"),
                            ("CON-F021-MD-P148", "Helmut Wolfes")):
            with self.subTest(credit=ident):
                credit = credits[ident]
                self.assertEqual(credit["creditAsPrinted"], "Musikalische Leitung")
                self.assertIn(name, credit["scopeNote"])
                self.assertIn("both “Musikalische Leitung” and “Musik-Bearbeitung”", credit["scopeNote"])

    def test_verified_kaper_and_jurmann_credits_record_the_catalogue_heading(self):
        credits = records("contributions")
        for ident, source in (("CON-F009-MD-P009", "SRC0124"),
                              ("CON-F019-MD-P009", "SRC0130"),
                              ("CON-F022-MD-P009", "SRC0131"),
                              ("CON-F022-MD-P077", "SRC0131")):
            with self.subTest(credit=ident):
                credit = credits[ident]
                self.assertEqual(credit["creditAsPrinted"], "Musikalische Leitung")
                self.assertIn(source, credit["sourceIds"])


if __name__ == "__main__":
    unittest.main()
