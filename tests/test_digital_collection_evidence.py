import json
import unittest
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data/public/v1"


def records(name):
    return {record["id"]: record for record in json.loads(
        (DATA / f"{name}.json").read_text(encoding="utf-8")
    )["records"]}


class DigitalCollectionEvidenceTests(unittest.TestCase):
    def test_usc_covers_support_printed_credits_only(self):
        sources, credits = records("sources"), records("contributions")
        evidence = {
            "SRC0443": ("CON-S119-C-P009", "CON-S119-C-P077", "CON-S119-L-P025"),
            "SRC0535": ("CON-S118-C-P009", "CON-S118-C-P077", "CON-S118-L-P058", "CON-S118-PUB-ORG035"),
        }
        for source_id, credit_ids in evidence.items():
            for credit_id in credit_ids:
                with self.subTest(source=source_id, credit=credit_id):
                    self.assertIn(credit_id, sources[source_id]["contributionIds"])
                    self.assertIn(source_id, credits[credit_id]["sourceIds"])
        self.assertNotIn("CON-S119-L-P028", sources["SRC0443"]["contributionIds"])
        self.assertNotIn("CON-S118-P-P173", sources["SRC0535"]["contributionIds"])

    def test_film_cover_sources_are_linked_to_the_named_films(self):
        sources, works = records("sources"), records("works")
        for source_id, work_id in (("SRC0538", "W-F023"),
                                   ("SRC0539", "W-F021"),
                                   ("SRC0541", "W-F024")):
            with self.subTest(source=source_id):
                self.assertIn(work_id, sources[source_id]["workIds"])
                self.assertIn(source_id, works[work_id]["sourceIds"])
                self.assertFalse(sources[source_id].get("contributionIds"))
        self.assertFalse(sources["SRC0541"].get("songIds"))

    def test_blue_venetian_waters_cover_documents_only_named_credits(self):
        source = records("sources")["SRC0542"]
        works, songs, contributions = records("works"), records("songs"), records("contributions")
        for work_id in ("W-S129", "W-F046"):
            self.assertIn(work_id, source["workIds"])
            self.assertIn("SRC0542", works[work_id]["sourceIds"])
        self.assertIn("S129", source["songIds"])
        self.assertIn("SRC0542", songs["S129"]["sourceIds"])
        for credit_id in ("CON-S129-C-P009", "CON-S129-C-P077",
                          "CON-S129-L-P025", "CON-S129-PUB-ORG035"):
            self.assertIn(credit_id, source["contributionIds"])
            self.assertIn("SRC0542", contributions[credit_id]["sourceIds"])
        self.assertNotIn("CON-S129-P-P173", source["contributionIds"])


if __name__ == "__main__":
    unittest.main()
