import json
import unittest
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data/public/v1"


def table(name):
    return {r["id"]: r for r in json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))["records"]}


class SieghardtComparisonTests(unittest.TestCase):
    """Corrections from docs/sieghardt-comparison.md."""

    @classmethod
    def setUpClass(cls):
        cls.credits, cls.songs, cls.variants = table("contributions"), table("songs"), table("title-variants")

    def test_sieghardt_is_not_cited_for_davson(self):
        self.assertNotIn("SRC0373", self.credits["CON-S196-L-P106"]["sourceIds"])
        self.assertIn("Secchia", self.songs["S196"]["publicNote"])

    def test_mauprey_rests_on_the_filmography(self):
        credit = self.credits["CON-S036-L-P005"]
        self.assertEqual(credit["certainty"], "probable")
        self.assertIn("p. 221", credit["evidenceLocator"])

    def test_authors_sieghardt_adds_are_probable(self):
        for credit_id in ("CON-S076-L-P017", "CON-S079-L-P033", "CON-S079-L-P206", "CON-S113-L-P049",
                          "CON-S112-L-P049", "CON-S114-L-P052", "CON-S135-C-P135", "CON-S137-C-P135",
                          "CON-S138-C-P135", "CON-S139-C-P135", "CON-S140-C-P135", "CON-S141-C-P135"):
            credit = self.credits[credit_id]
            with self.subTest(credit=credit_id):
                self.assertEqual((credit["certainty"], credit["sourceIds"]), ("probable", ["SRC0373"]))
                self.assertTrue(credit["evidenceLocator"])

    def test_mgm_claims_and_robbins_publishes(self):
        for song in ("S119", "S123"):
            with self.subTest(song=song):
                self.assertEqual(self.credits[f"CON-{song}-CC-ORG001"]["role"], "copyright_claimant")
                self.assertEqual(self.credits[f"CON-{song}-PUB-ORG035"]["role"], "publisher")
                self.assertNotIn(f"CON-{song}-PUB-ORG001", self.credits)

    def test_kinderlied_is_a_variant(self):
        variant = self.variants["TV0324"]
        self.assertEqual((variant["variantTitle"], variant["workIds"]), ("Kinderlied", ["W-S062"]))


if __name__ == "__main__":
    unittest.main()
