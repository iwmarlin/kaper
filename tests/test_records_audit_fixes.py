import json
import unittest
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data/public/v1"


def table(name):
    return {r["id"]: r for r in json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))["records"]}


class RecordsAuditFixTests(unittest.TestCase):
    """Fixes from docs/records-audit.md, findings 1, 2 and 5."""

    @classmethod
    def setUpClass(cls):
        cls.sources, cls.contributions, cls.people = table("sources"), table("contributions"), table("people")

    def test_credits_cite_the_label_list_their_note_relies_on(self):
        for source_id, credits in (
            ("SRC0742", ("CON-S071-P-ORG144", "CON-S071-LAB-ORG128", "CON-S071-CON-P205",
                         "CON-S080-P-P153", "CON-S080-LAB-ORG128", "CON-S082-P-ORG120")),
            ("SRC0741", ("CON-S038-P-ORG119",)),
        ):
            for credit in credits:
                with self.subTest(credit=credit):
                    self.assertIn(source_id, self.contributions[credit]["sourceIds"])
                    self.assertIn(credit, self.sources[source_id]["contributionIds"])

    def test_no_credit_is_confirmed_on_an_upload_rated_low_alone_but_the_filmed_one(self):
        low_only = [
            credit["id"] for credit in self.contributions.values()
            if credit["certainty"] == "confirmed"
            and all(self.sources[s]["reliability"] == "low" for s in credit["sourceIds"])
        ]
        # Judy Garland in Everybody Sing rests on film footage of the number.
        self.assertEqual(low_only, ["CON-S161-P-P138"])

    def test_register_entries_are_rated_alike(self):
        for source_id in ("SRC0212", "SRC0217", "SRC0218"):
            with self.subTest(source=source_id):
                self.assertEqual(self.sources[source_id]["reliability"], "high")

    def test_kaper_is_listed_as_a_pianist(self):
        self.assertIn("pianist", self.people["P009"]["roles"])
        for credit in ("CON-O011-P-P009", "CON-O019-P-P009"):
            self.assertEqual(self.contributions[credit]["role"], "performer")


if __name__ == "__main__":
    unittest.main()
