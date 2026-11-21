"""A secondary catalogue alone does not make a statement confirmed.

docs/sources-audit.md, "Period evidence, 21 November 2026": Sieghardt's work
catalogue, Görner's work list and the Walter Jurmann website may be wrong, and
a title variant or a relation between a song and another work that rests on
them alone is at most probable.
"""

import json
import unittest
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data/public/v1"
SECONDARY_CATALOGUES = {"SRC0373", "SRC0306", "SRC0992"}


def table(name):
    return {r["id"]: r for r in json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))["records"]}


class PeriodEvidenceTests(unittest.TestCase):
    def test_no_confirmed_title_variant_rests_on_a_catalogue_alone(self):
        for variant in table("title-variants").values():
            if variant["certainty"] == "confirmed":
                with self.subTest(variant=variant["id"]):
                    self.assertFalse(set(variant["sourceIds"]) <= SECONDARY_CATALOGUES)

    def test_no_confirmed_song_relation_rests_on_a_catalogue_alone(self):
        works = table("works")
        for relation in table("work-relations").values():
            ids = relation["sourceWorkIds"] + relation["targetWorkIds"]
            if relation["certainty"] != "confirmed":
                continue
            if not any(works[w]["workType"] == "Song" for w in ids):
                continue
            with self.subTest(relation=relation["id"]):
                self.assertFalse(set(relation["sourceIds"]) <= SECONDARY_CATALOGUES)

    def test_the_period_documents_found_are_cited(self):
        relations = table("work-relations")
        for relation_id, source_id in (
            ("REL0080", "SRC1028"),
            ("REL0113", "SRC1029"),
            ("REL0116", "SRC1029"),
            ("REL0134", "SRC1030"),
            ("REL0139", "SRC0981"),
        ):
            self.assertIn(source_id, relations[relation_id]["sourceIds"])
        credits = table("contributions")
        self.assertIn("SRC1031", credits["CON-F034-C-P136"]["sourceIds"])
        self.assertIn("SRC1031", credits["CON-F034-D-P018"]["sourceIds"])


if __name__ == "__main__":
    unittest.main()
