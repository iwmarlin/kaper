import json
import unittest
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data/public/v1/sources.json"


class SourceContextPrecisionTests(unittest.TestCase):
    def test_film_article_is_not_misrepresented_as_cover_provenance(self):
        sources = {row["id"]: row for row in json.loads(DATA.read_text(encoding="utf-8"))["records"]}
        source = sources["SRC0533"]
        self.assertIn("M225", source["mediaIds"])
        self.assertEqual(source["researchNoteType"], "object_context")
        self.assertIn("not the source", source["researchNote"])
        self.assertIn("SRC0541", source["researchNote"])

    def test_fiesta_disc_does_not_claim_to_document_kaper_transcription(self):
        sources = {row["id"]: row for row in json.loads(DATA.read_text(encoding="utf-8"))["records"]}
        source = sources["SRC0773"]
        self.assertIn("W-O012", source["workIds"])
        self.assertIn("does not name Kaper", source["researchNote"])
        self.assertNotIn("CON-O012-A-P009", source.get("contributionIds", []))

    def test_konarski_citation_gives_complete_article_pages(self):
        sources = {row["id"]: row for row in json.loads(DATA.read_text(encoding="utf-8"))["records"]}
        self.assertIn("(138): 5–19", sources["SRC0947"]["fullCitation"])


if __name__ == "__main__":
    unittest.main()
