"""Corrections from docs/title-variants-audit.md, held in place."""

import json
import unittest
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data/public/v1"


def table(name):
    return {r["id"]: r for r in json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))["records"]}


class TitleVariantsAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.variants = table("title-variants")
        cls.works = table("works")

    def test_no_title_is_recorded_twice_on_one_work(self):
        seen = {}
        for variant in self.variants.values():
            for work_id in variant["workIds"]:
                # The same words in two languages are two versions, as Adieu
                # is on W-S074 in French and in English.
                key = (work_id, variant["language"], variant["variantTitle"].casefold())
                self.assertNotIn(key, seen, f"{variant['id']} repeats {seen.get(key)}")
                seen[key] = variant["id"]

    def test_another_films_title_is_not_a_variant(self):
        for variant_id in ("TV0012", "TV0019", "TV0050", "TV0286"):
            self.assertNotIn(variant_id, self.variants)
        films = {w["title"] for w in self.works.values() if w["workType"] == "Film"}
        for variant in self.variants.values():
            if any(self.works[w]["workType"] == "Film" for w in variant["workIds"]):
                self.assertNotIn(variant["variantTitle"], films, variant["id"])

    def test_the_us_title_of_moscow_nights(self):
        variant = self.variants["TV0053"]
        self.assertEqual(variant["variantTitle"], "I Stand Condemned")
        self.assertIn("SRC1025", variant["sourceIds"])

    def test_laubenkolonie_rests_on_the_trade_press(self):
        self.assertIn("SRC1026", self.variants["TV0002"]["sourceIds"])
        self.assertIn("SRC1027", self.variants["TV0002"]["sourceIds"])
        self.assertIn("SRC1026", table("contributions")["CON-F001-C-P009"]["sourceIds"])

    def test_versions_cite_the_edition_of_the_time_first(self):
        for variant_id, source_id in (
            ("TV0110", "SRC0981"),
            ("TV0111", "SRC0212"),
            ("TV0124", "SRC0950"),
            ("TV0151", "SRC0298"),
        ):
            self.assertEqual(self.variants[variant_id]["sourceIds"][0], source_id)

    def test_no_working_notes_in_public_notes(self):
        for variant in self.variants.values():
            self.assertNotIn("to be added", variant.get("note", ""), variant["id"])


if __name__ == "__main__":
    unittest.main()
