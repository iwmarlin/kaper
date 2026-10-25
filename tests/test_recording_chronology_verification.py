"""Protect individually checked recording, issue and access-copy chronology."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source
from recording_sources import VERIFIED_RECORDING_CHRONOLOGY, VERIFIED_RECORDING_FIELD_REMOVALS


class RecordingChronologyVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {
            r["id"]: r for r in json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        }
        cls.media = {
            r["id"]: r for r in json.loads((ROOT / "data/public/v1/media.json").read_text())["records"]
        }

    def test_salabert_date_has_a_catalogue_basis_not_a_film_inference(self):
        source = self.sources["SRC0300"]
        self.assertEqual(source["date"], "1934")
        self.assertEqual(source["dateRole"], "issue")
        self.assertEqual(source["dateQualifier"], "confirmed")
        self.assertIn("Répertoire phonographique", source["researchNote"])
        self.assertNotIn("1932", source["researchNote"])
        self.assertNotIn("cannot predate", source["researchNote"])
        self.assertEqual(source["researchNoteType"], "discographic_note")

    def test_retrieval_distinguishes_first_cd_issue_and_online_copy(self):
        source = self.sources["SRC0714"]
        self.assertEqual((source["date"], source["dateRole"]), ("2000", "issue"))
        self.assertIn("CD compilation", source["fullCitation"])
        self.assertIn("21 November 2005", source["researchNote"])
        self.assertIn("10 February 2015", source["researchNote"])
        self.assertEqual(source["additionalLinks"][0]["url"], "https://www.challengerecords.com/products/1182852218")

    def test_odeon_year_remains_explicitly_unresolved(self):
        source = self.sources["SRC0754"]
        self.assertEqual((source["date"], source["dateQualifier"]), ("1932", "uncertain"))
        for text in ("1933", "Be 10147", "release-date column is empty"):
            self.assertIn(text, source["researchNote"])
        self.assertEqual(source["researchNoteType"], "date_assessment")
        self.assertIn("Luigi Bernauer", source["fullCitation"])
        self.assertIn("Fred Lustig", source["fullCitation"])

    def test_four_archive_years_are_not_verified_session_dates(self):
        for sid in ("SRC0800", "SRC0803", "SRC0804", "SRC0806"):
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                                 ("1934", "described_item", "reported"))
                self.assertNotIn("1934 recording", source["fullCitation"])
                self.assertNotIn("(1934)", source["title"])
                self.assertIn("does not distinguish", source["researchNote"])

    def test_undated_bnf_disc_is_not_dated_from_its_film(self):
        source = self.sources["SRC0801"]
        self.assertNotIn("date", source)
        self.assertNotIn("dateDisplay", source)
        self.assertEqual(source["dateQualifier"], "unknown")
        self.assertIn("s.d.", source["researchNote"])
        self.assertIn("January 1935", source["researchNote"])
        medium = self.media["M420"]
        self.assertNotIn("in 1934", medium["description"])
        self.assertNotIn("(1934)", medium["publicCaption"])
        self.assertEqual(medium["sourceIds"], ["SRC0800", "SRC0801"])
        self.assertEqual(medium["rightsStatus"], "external_content_not_rehosted")

    def test_bnf_reconstructed_issue_year_is_not_a_session_date(self):
        source = self.sources["SRC0805"]
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1934", "issue", "confirmed"))
        self.assertEqual(source["dateDisplay"], "[1934]")
        self.assertIn("Répertoire phonographique", source["researchNote"])
        self.assertEqual(self.sources["SRC0802"]["dateQualifier"], "uncertain")
        self.assertIn("[193.]", self.sources["SRC0802"]["researchNote"])

    def test_normalization_restores_reviewed_fields_without_touching_links(self):
        for sid, fields in VERIFIED_RECORDING_CHRONOLOGY.items():
            with self.subTest(source=sid):
                source = self.sources[sid]
                stale = dict(source)
                for key in fields:
                    stale[key] = "stale" if not isinstance(fields[key], list) else []
                for key in VERIFIED_RECORDING_FIELD_REMOVALS.get(sid, []):
                    stale[key] = "1934"
                self.assertEqual(normalized_source(stale), source)
                self.assertEqual(normalized_source(normalized_source(source)), source)

    def test_audit_log_matches_reviewed_fields_and_removals(self):
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        for sid, fields in VERIFIED_RECORDING_CHRONOLOGY.items():
            with self.subTest(source=sid):
                entry = overrides["records"]["Sources"][sid]
                for key, value in fields.items():
                    self.assertEqual(entry["fields"][key], value)
                for key in VERIFIED_RECORDING_FIELD_REMOVALS.get(sid, []):
                    self.assertIn(key, entry["removeFields"])
                    self.assertNotIn(key, entry["fields"])


if __name__ == "__main__":
    unittest.main()
