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

    def test_the_polish_ninon_keeps_halicz(self):
        song = self.songs["S214"]
        self.assertIn("Wycislik", song["publicNote"])
        self.assertIn("SRC0972", song["sourceIds"])
        self.assertEqual(self.credits["CON-S214-L-P156"]["role"], "lyricist")
        self.assertFalse(any("Wyci" in (c.get("nameAsPrinted") or "") for c in self.credits.values()))

    def test_publishers_need_a_document_of_the_time(self):
        self.assertNotIn("CON-S200-PUB-ORG035", self.credits)
        self.assertEqual(self.credits["CON-S103-PUB-ORG032"]["certainty"], "probable")
        for credit_id, source_id in (("CON-S119-PUB-ORG035", "SRC0443"), ("CON-S123-PUB-ORG035", "SRC0046")):
            credit = self.credits[credit_id]
            self.assertEqual((credit["certainty"], credit["sourceIds"][0]), ("confirmed", source_id))
        self.assertIn("SRC0973", self.credits["CON-S106-L-P006"]["sourceIds"])
        self.assertIn("André de Badet alone", self.songs["S106"]["publicNote"])

    def test_signorina_and_madonna_are_one_work(self):
        works, relations = table("works"), table("work-relations")
        self.assertNotIn("S068", self.songs)
        self.assertNotIn("W-S068", works)
        self.assertFalse([c for c in self.credits if c.startswith("CON-S068-")])
        madonna = works["W-S078"]
        self.assertEqual(madonna["title"], "Oh Madonna!")
        self.assertIn("SRC0216", madonna["sourceIds"])
        self.assertTrue(madonna["publicNote"].startswith("One tune with two German texts"))
        printed = self.variants["TV0325"]
        self.assertEqual((printed["variantTitle"], printed["workIds"], printed["sourceIds"]),
                         ("Signorina! komm zu mir", ["W-S078"], ["SRC0216"]))
        self.assertEqual(self.variants["TV0307"]["workIds"], ["W-S078"])
        self.assertEqual(relations["REL0198"]["targetWorkIds"], ["W-S078"])
        self.assertNotIn("REL0036", relations)
        self.assertIn("SRC0216", relations["REL0043"]["sourceIds"])
        for record in list(table("people").values()) + list(table("organizations").values()):
            self.assertNotIn("W-S068", record.get("workIds", []))
        page = (DATA.parents[2] / "records/work/W-S068/index.html").read_text(encoding="utf-8")
        self.assertIn('url=../W-S078/', page)

    def test_ich_suche_rests_on_the_film_programme(self):
        work = table("works")["W-S052"]
        self.assertEqual(work["title"], "Ich suche einen, der mir allein gehört")
        self.assertEqual(work["sourceIds"][0], "SRC0974")
        self.assertNotIn("Fritsch", work["publicNote"])
        self.assertNotIn("Fritsch", self.variants["TV0314"]["note"])
        self.assertIn("Ich suche Einen, der mir allein gehört", table("sources")["SRC0974"]["researchNote"])

    def test_la_vie_et_lamour_stays_the_french_schade(self):
        relation = table("work-relations")["REL0143"]
        self.assertEqual((relation["sourceWorkIds"], relation["targetWorkIds"]), (["W-S073"], ["W-S059"]))
        self.assertIn("SRC0975", self.songs["S073"]["sourceIds"])


if __name__ == "__main__":
    unittest.main()
