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

    def test_mauprey_rests_on_the_eschig_edition(self):
        # First probable on Sieghardt's filmography alone; the Eschig edition of
        # 1932 in the BnF prints his French words.
        credit = self.credits["CON-S036-L-P005"]
        self.assertEqual((credit["certainty"], credit["sourceIds"][0]), ("confirmed", "SRC0981"))
        self.assertIn("p. 221", credit["evidenceLocator"])

    def test_authors_sieghardt_adds_are_probable(self):
        for credit_id in ("CON-S076-L-P017", "CON-S079-L-P033", "CON-S079-L-P206", "CON-S113-L-P049",
                          "CON-S112-L-P049", "CON-S114-L-P052", "CON-S137-C-P135",
                          "CON-S138-C-P135", "CON-S140-C-P135"):
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

    def test_trink_dich_gesund_prints_pseudonyms(self):
        variants = table("person-name-variants")
        schmidt, schattner = variants["PNV0080"], variants["PNV0081"]
        self.assertEqual((schmidt["variantName"], schmidt["variantType"], schmidt["personIds"]),
                         ("Erich Walter Schmidt", "joint_pseudonym", ["P009", "P077"]))
        self.assertEqual((schattner["variantName"], schattner["personIds"]), ("Peter Schattner", ["P020"]))
        for credit_id, printed in (("CON-S100-C-P009", "Erich Walter Schmidt"),
                                   ("CON-S100-C-P077", "Erich Walter Schmidt"),
                                   ("CON-S100-L-P020", "P. Schattner")):
            credit = self.credits[credit_id]
            self.assertEqual(credit["nameAsPrinted"], printed)
            self.assertEqual(credit["sourceIds"][:2], ["SRC0976", "SRC0977"])
        self.assertEqual(self.songs["S100"]["genre"], "schunkelwalzer")
        self.assertIn("Schmidt, Erich Walter", table("sources")["SRC0976"]["researchNote"])

    def test_film_credits_follow_documents_of_the_time(self):
        works = table("works")
        for credit_id in ("CON-F045-BM-P009", "CON-F045-BM-P077"):
            self.assertEqual((self.credits[credit_id]["certainty"], self.credits[credit_id]["sourceIds"]),
                             ("probable", ["SRC0173"]))
        self.assertTrue({"SRC0979", "SRC0980"} <= set(works["W-F045"]["sourceIds"]))
        self.assertNotIn("CON-F018-C-P005", self.credits)
        self.assertEqual(self.credits["CON-F018-L-P005"]["role"], "lyricist")
        self.assertIn("SRC0978", works["W-F057"]["sourceIds"])
        self.assertIn("No document of the time credits", works["W-F057"]["publicNote"])
        self.assertIn("Signorina! Serenade", table("sources")["SRC0409"]["researchNote"])
        self.assertIn("SRC0409", works["W-S078"]["sourceIds"])

    def test_little_boy_blue_is_mgms_miniature(self):
        works, people = table("works"), table("people")
        film = works["W-F052"]
        self.assertTrue({"SRC0983", "SRC0984"} <= set(film["sourceIds"]))
        self.assertIn("MGM one-reel Miniature", film["publicNote"])
        self.assertEqual(self.credits["CON-F052-D-P209"]["role"], "film_director")
        self.assertEqual(people["P209"]["authorizedName"], "Bucquet, Harold S.")
        for credit_id in ("CON-F052-C-P009", "CON-F052-C-P077", "CON-F052-PR-P210"):
            self.assertEqual(self.credits[credit_id]["certainty"], "probable")
        for gone in ("P157", "P158"):
            self.assertNotIn(gone, people)
        self.assertNotIn("ORG116", table("organizations"))
        self.assertFalse({"M197", "M304"} & set(table("media")))
        root = DATA.parents[2]
        for kind, old in (("person", "P157"), ("organization", "ORG116"), ("media", "M197"), ("source", "SRC0384")):
            page = (root / "records" / kind / old / "index.html").read_text(encoding="utf-8")
            self.assertIn("url=../../work/W-F052/", page)

    def test_publishers_on_sieghardt_alone_are_probable(self):
        for credit_id in ("CON-S087-PUB-ORG039", "CON-S197-PUB-ORG035", "CON-S198-PUB-ORG035",
                          "CON-S201-PUB-ORG035", "CON-S202-PUB-ORG035", "CON-S032-PUB-ORG033"):
            credit = self.credits[credit_id]
            self.assertEqual(credit["certainty"], "probable")
            self.assertEqual(credit["sourceIds"], ["SRC0373"])
        self.assertNotIn("CON-S202-PUB-ORG001", self.credits)
        self.assertEqual(self.songs["S032"]["certainty"], "probable")
        self.assertIn("No document of the time names this song", self.songs["S032"]["publicNote"])

    def test_documented_versions_are_added(self):
        works, relations = table("works"), table("work-relations")
        for work_id, lyricist, source_id in (("W-S231", "Harry S. Pepper", "SRC0987"),
                                             ("W-S232", "Arne Olovson", "SRC0988"),
                                             ("W-S233", "Arne Olovson", "SRC0991")):
            song = self.songs[work_id[2:]]
            self.assertEqual(song["lyricistAsPrinted"], lyricist)
            self.assertEqual(works[work_id]["sourceIds"][0], source_id)
        for relation_id, target in (("REL0218", "W-S076"), ("REL0219", "W-S076"), ("REL0220", "W-S038")):
            self.assertEqual(relations[relation_id]["targetWorkIds"], [target])
        self.assertEqual(self.songs["S230"]["title"], "Melodie der Liebe")
        self.assertEqual(relations["REL0217"]["certainty"], "probable")
        page = (DATA.parents[2] / "records/work/W-S232/index.html").read_text(encoding="utf-8")
        self.assertIn("words by Arne Olovson", page)




class GornerWorkListTest(unittest.TestCase):
    """The list by year is Görner's (2014), not part of Sieghardt's catalogue."""

    def setUp(self):
        self.sources = {r["id"]: r for r in json.loads((DATA / "sources.json").read_text())["records"]}
        self.credits = {r["id"]: r for r in json.loads((DATA / "contributions.json").read_text())["records"]}

    def test_gorner_is_a_source_of_its_own(self):
        source = self.sources["SRC0992"]
        self.assertEqual(source["creator"], "Eberhard Görner")
        self.assertIn("pp. 200–217", source["fullCitation"])
        self.assertIn("jurmann.org", source["fullCitation"])

    def test_no_note_calls_it_sieghardts(self):
        for name in ("contributions", "films", "songs", "works", "title-variants"):
            text = (DATA / f"{name}.json").read_text()
            with self.subTest(file=name):
                self.assertNotIn("year-by-year", text)
                self.assertNotIn("adds Carl W. Stalling", text)

    def test_waxman_cues_off_the_opus_list_rest_on_gorner(self):
        for credit_id in ("CON-S135-C-P135", "CON-S139-C-P135", "CON-S141-C-P135"):
            credit = self.credits[credit_id]
            with self.subTest(credit=credit_id):
                self.assertEqual((credit["certainty"], credit["sourceIds"]), ("probable", ["SRC0992", "SRC0373"]))
                self.assertIn("p. 227", credit["evidenceLocator"])


if __name__ == "__main__":
    unittest.main()
