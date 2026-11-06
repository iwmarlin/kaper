import json
import unittest
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data/public/v1"


def table(name):
    return {r["id"]: r for r in json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))["records"]}


class MediumOnlyWorkReinforcementTests(unittest.TestCase):
    """Two Works that rested only on sources rated medium now also cite a
    national-library catalogue record."""

    @classmethod
    def setUpClass(cls):
        cls.sources, cls.works = table("sources"), table("works")
        cls.relations, cls.contributions = table("work-relations"), table("contributions")

    def test_moze_tak_moze_nie_cites_the_biblioteka_narodowa_record_of_its_disc(self):
        source = self.sources["SRC0964"]
        self.assertEqual(source["reliability"], "high")
        self.assertIn("DM 1624", source["fullCitation"])
        self.assertIn("991043120839705066", source["primaryUrl"])
        self.assertIn("SRC0964", self.works["W-S216"]["sourceIds"])
        self.assertIn("SRC0964", self.relations["REL0199"]["sourceIds"])
        for cid in ("CON-S216-C-P009", "CON-S216-L-P159"):
            self.assertIn("SRC0964", self.contributions[cid]["sourceIds"])

    def test_parade_de_france_cites_each_song_notice_that_names_the_revue(self):
        for relation, source in (
            ("REL0073", "SRC0057"), ("REL0074", "SRC0058"),
            ("REL0075", "SRC0059"), ("REL0076", "SRC0060"),
        ):
            with self.subTest(relation=relation):
                self.assertIn("Parade de France", self.sources[source]["fullCitation"])
                self.assertEqual(self.sources[source]["reliability"], "high")
                self.assertIn(source, self.relations[relation]["sourceIds"])
                self.assertIn(source, self.works["W-O010"]["sourceIds"])
        # The song notices say nothing of who wrote the revue's music as a
        # whole, so the revue's own credits still rest on the collective notice.
        for cid in self.works["W-O010"]["contributionIds"]:
            for source in ("SRC0057", "SRC0058", "SRC0059", "SRC0060"):
                self.assertNotIn(source, self.contributions[cid].get("sourceIds") or [])


if __name__ == "__main__":
    unittest.main()
