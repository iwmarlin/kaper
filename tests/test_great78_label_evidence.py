"""A catalogue's metadata provenance does not determine image availability."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from add_listening_reference import apply_disc
from normalize_sources import normalized_source

REVIEWED = {"SRC0783": "M407", "SRC0784": "M408", "SRC0788": "M410"}


class Great78LabelEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for table in ("sources", "media"):
            records = json.loads((ROOT / "data/public/v1" / f"{table}.json").read_text())["records"]
            setattr(cls, table, {r["id"]: r for r in records})
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    def test_cataloguer_does_not_imply_absence_or_presence_of_label_images(self):
        for cataloguer in ("Great 78 Project", "Another digitising library"):
            for credit in (None, "Kaper; Jurmann"):
                with self.subTest(cataloguer=cataloguer, credit=credit):
                    source, medium = {"id": "SRC9999"}, {}
                    apply_disc(medium, source, work_title="Test song", host="archive.org",
                               disc={"label": "Test label", "catalogue": "123",
                                     "catalogued_by": cataloguer, "credit": credit})
                    self.assertEqual(source["researchNote"],
                                     f"The discographic metadata are supplied by {cataloguer}.")
                    text = source["researchNote"] + medium["publicCaption"]
                    for claim in ("sound alone", "label is not shown", "label in view",
                                  "photograph", "which prints", "catalogued it from the label"):
                        self.assertNotIn(claim, text)
                    self.assertIn("catalogued as Test label 123", medium["publicCaption"])

    def test_explicit_description_only_option_keeps_its_qualification(self):
        source, medium = {"id": "SRC9999"}, {}
        apply_disc(medium, source, work_title="Test song", host="youtube.com",
                   disc={"label": "Test label", "catalogue": "123", "from_description": True})
        self.assertIn("uploader's description", source["researchNote"])
        self.assertIn("label is not shown", source["researchNote"])
        self.assertEqual(source["reliability"], "medium")
        self.assertIn("without showing the label", medium["publicCaption"])

    def test_three_reviewed_sources_link_the_actual_label_photographs(self):
        for sid, mid in REVIEWED.items():
            with self.subTest(source=sid):
                source, medium = self.sources[sid], self.media[mid]
                link = source["additionalLinks"][0]
                item = source["primaryUrl"].rsplit("/", 1)[-1]
                self.assertEqual(link["url"],
                                 f"https://archive.org/download/{item}/{item}_itemimage.jpg")
                self.assertIn("photograph", source["researchNote"])
                self.assertIn("photograph", medium["publicCaption"])
                self.assertNotIn("sound alone", source["researchNote"])
                self.assertNotIn("sound alone", medium["publicCaption"])
                self.assertEqual(medium["sourceIds"], [sid])
                self.assertEqual(medium["externalUrl"], source["primaryUrl"])
                self.assertEqual(medium["rightsStatus"], "external_content_not_rehosted")

    def test_hmv_film_and_year_have_explicit_evidence(self):
        for sid, matrix in (("SRC0783", "OA.09934"), ("SRC0784", "OA.09937")):
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertIn(matrix, source["fullCitation"])
                self.assertIn("Everybody Sing", source["fullCitation"])
                self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                                 ("1938", "issue", "confirmed"))
                self.assertIn("7 May 1938", source["researchNote"])
                self.assertIn("indexed text was consulted", source["researchNote"])
                self.assertIn("complete PDF could not be retrieved", source["researchNote"])
                self.assertIn("does not date the manufacture", source["researchNote"])
        self.assertIn("A Night at the Opera", self.sources["SRC0784"]["researchNote"])

    def test_australian_tauber_pressing_is_not_dated_from_the_german_session(self):
        source = self.sources["SRC0788"]
        self.assertNotIn("date", source)
        self.assertEqual((source["dateRole"], source["dateQualifier"]), ("issue", "unknown"))
        for text in ("Paul Dessau", "Sung in German", "Australia", "Be 9887"):
            self.assertIn(text, source["fullCitation"])
        self.assertIn("take 2", source["researchNote"])
        self.assertIn("Patent dates", source["researchNote"])
        self.assertNotIn("1932", source["fullCitation"])
        self.assertIn("Australia", self.media["M410"]["publicCaption"])

    def test_normalizer_restores_reviewed_evidence_and_date_semantics(self):
        for sid in REVIEWED:
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual(normalized_source(source), source)
                stale = dict(source, researchNote="The transfer carries sound alone.",
                             fullCitation="Old citation", date="1932", dateRole="recording")
                self.assertEqual(normalized_source(stale), source)

    def test_audit_log_preserves_fields_and_explicit_date_removal(self):
        for sid, mid in REVIEWED.items():
            for table, rid, records in (("Sources", sid, self.sources), ("Media", mid, self.media)):
                with self.subTest(table=table, record=rid):
                    fields = self.overrides["records"][table][rid]["fields"]
                    for key, value in fields.items():
                        self.assertEqual(records[rid][key], value)
        entry = self.overrides["records"]["Sources"]["SRC0788"]
        self.assertIn("date", entry["removeFields"])
        self.assertNotIn("date", entry["fields"])
