import json
import unittest
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data/public/v1"


def table(name):
    return {r["id"]: r for r in json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))["records"]}


# Each title is the form its earliest primary Source prints (docs/works-audit.md, finding 1).
PRINTED_TITLES = {
    "S002": "Jak się da, to się zrobi!",
    "S003": "Zgaś lampę!",
    "S022": "O tem wróble świergocą...",
    "S068": "Signorina! komm zu mir",
    "S078": "Oh Madonna!",
    "S082": "In 24 Stunden kann soviel geschehn",
    "S086": "Kind, ich freu mich auf dein Kommen",
    "S092": "Ich geh nie von dir fort",
    "S101": "Ganz Ihrer Meinung, jawohl",
    "S107": "En avant",
    "S112": "Vivons l’amour, vivons la vie",
    "S118": "Cosi Cosa",
    "S125": "Tillie the Tight Rope Walker",
    "S156": "Never Was There Ever Such a Perfect Day",
    "S157": "Swing Mister Mendelssohn",
    "S172": "Good-Night",
    "S191": "Mit dir möchte ich ziehn bis zum Ende der Welt",
    "S212": "Penny’s Return",
    "S228": "Dairy-Maid Song",
}


class WorksAuditFixTests(unittest.TestCase):
    """Fixes from docs/works-audit.md, findings 1 to 4."""

    @classmethod
    def setUpClass(cls):
        cls.works, cls.songs = table("works"), table("songs")
        cls.variants, cls.credits = table("title-variants"), table("contributions")
        cls.other_works = table("other-works")

    def test_titles_are_the_printed_forms(self):
        for song_id, title in PRINTED_TITLES.items():
            with self.subTest(song=song_id):
                self.assertEqual(self.songs[song_id]["title"], title)
                self.assertEqual(self.works[f"W-{song_id}"]["title"], title)

    def test_old_forms_a_source_prints_stay_findable_as_variants(self):
        for work_id, variant in (
            ("W-S022", "O tym już wróble świergocą na dachu"),
            ("W-S078", "O Madonna"),
            ("W-S092", "Ich geh’ nie von dir fort"),
            ("W-S118", "Così, cosa"),
            ("W-S156", "Never Was There Such a Perfect Day"),
            ("W-S157", "Swing, Mister Mendelssohn"),
        ):
            with self.subTest(work=work_id):
                self.assertTrue(any(
                    v["variantTitle"] == variant and work_id in v["workIds"] and v["sourceIds"]
                    for v in self.variants.values()
                ))

    def test_french_versions_are_not_variants_of_the_german_films(self):
        for variant_id in ("TV0025", "TV0036", "TV0043", "TV0284"):
            self.assertNotIn(variant_id, self.variants)
        german_films = ("W-F017", "W-F022", "W-F023", "W-F026")
        french_titles = {self.works[w]["title"] for w in ("W-F019", "W-F020", "W-F025", "W-F027")}
        for variant in self.variants.values():
            if set(variant["workIds"]) & set(german_films):
                self.assertNotIn(variant["variantTitle"], french_titles)

    def test_publisher_field_holds_only_publishers(self):
        for song_id in ("S004", "S012", "S165", "S166", "S167", "S181", "S192", "S212", "S213", "S214", "S215"):
            with self.subTest(song=song_id):
                self.assertNotIn("publisherAsPrinted", self.songs[song_id])

    def test_claimants_and_publishers_are_credited(self):
        for credit_id, role in (
            ("CON-S192-CC-ORG001", "copyright_claimant"),
            ("CON-S212-CC-ORG246", "copyright_claimant"),
            ("CON-S213-CC-ORG246", "copyright_claimant"),
            ("CON-S181-CC-P009", "copyright_claimant"),
            ("CON-S181-CC-P077", "copyright_claimant"),
            ("CON-S194-PUB-ORG050", "publisher"),
        ):
            with self.subTest(credit=credit_id):
                self.assertEqual(self.credits[credit_id]["role"], role)

    def test_jurmann_flag_agrees_with_the_credits(self):
        for song_id in ("S032", "S097", "S176", "S181", "S184", "S185", "S186", "S187",
                        "S192", "S223", "S226", "S227"):
            with self.subTest(song=song_id):
                self.assertTrue(self.songs[song_id].get("jurmannCollaboration"))

    def test_the_short_without_a_director_says_why(self):
        sources = table("sources")
        for record in (table("films")["F039"], self.works["W-F039"]):
            self.assertIn("SRC0967", record["sourceIds"])
            self.assertIn("names Earl Haley and Maurice Kusell", record["publicNote"])
        for credit_id in ("CON-F039-D-P207", "CON-F039-D-P208"):
            credit = self.credits[credit_id]
            self.assertEqual((credit["role"], credit["certainty"], credit["sourceIds"]),
                             ("film_director", "probable", ["SRC0373"]))
        self.assertEqual(sources["SRC0967"]["identifiers"], [{"scheme": "usco_registration", "value": "LP5806"}])
        self.assertEqual(self.credits["CON-F039-CC-ORG001"]["role"], "copyright_claimant")

    def test_wording_is_uniform(self):
        self.assertEqual(self.songs["S222"]["genre"], "slow_fox")
        self.assertIn("two pianos", self.other_works["O012"]["instrumentation"])


if __name__ == "__main__":
    unittest.main()
