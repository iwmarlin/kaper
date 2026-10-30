"""Bibliographic database citations must not absorb biographical analysis."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from database_sources import REVIEWED_DATABASE_FIELDS
from normalize_sources import normalized_source


class DatabaseCitationAndUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {
            r["id"]: r
            for r in json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        }
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    def test_nine_sacem_citations_identify_entries_not_life_histories(self):
        records = {
            "SRC0818": "3449", "SRC0819": "3854", "SRC0822": "3868",
            "SRC0823": "2689", "SRC0824": "2993", "SRC0825": "3842",
            "SRC0826": "3141", "SRC0827": "4243", "SRC0828": "3084",
        }
        for source_id, record_id in records.items():
            with self.subTest(source=source_id):
                source = self.sources[source_id]
                self.assertTrue(source["fullCitation"].endswith(
                    "Musée SACEM, Les créateurs, creator record " + record_id + "."
                ))
                for biographical_word in ["born", "died", "admitted", "elected", "Prix"]:
                    self.assertNotIn(biographical_word, source["fullCitation"])
                self.assertEqual(source["researchNoteType"], "authority_note")
                self.assertEqual(source["organizationIds"], ["ORG085"])
                self.assertEqual(source["dateQualifier"], "unknown")
                self.assertNotIn("date", source)

    def test_sacem_biographical_facts_and_existing_assessments_are_preserved(self):
        evidence = {
            "SRC0818": ["21 June 1966 in Prague", "Prix Ferny, 1939", "qualifier “fils”"],
            "SRC0819": ["30 October 1908 in Saumur", "17 January 1945 in Paris", "Paris death certificate"],
            "SRC0822": ["8 April 1933", "surname “Monteaux”", "membership photograph"],
            "SRC0823": ["30 August 1918", "10 April 1969", "Casino de Paris"],
            "SRC0824": ["29 April 1933", "Prix Célestin Joubert, 1964", "authority heading"],
            "SRC0825": ["27 April 1928", "secretary general of the SDRM", "mechanical rights body"],
            "SRC0826": ["21 November 1923", "Prix Albert Willemetz, 1949", "without a hyphen"],
            "SRC0827": ["13 September 1911", "Prix Salabert, 1958", "BnF heading"],
            "SRC0828": ["17 February 1912", "Grand Prix de la Chanson, 1958", "catalogue records"],
        }
        for source_id, phrases in evidence.items():
            for phrase in phrases:
                with self.subTest(source=source_id, evidence=phrase):
                    self.assertIn(phrase, self.sources[source_id]["researchNote"])

    def test_pbm_citation_and_pedagogical_evidence_remain_separate(self):
        source = self.sources["SRC0816"]
        self.assertTrue(source["fullCitation"].endswith("Polskie Wydawnictwo Muzyczne, 2023."))
        self.assertNotIn("Entry for", source["fullCitation"])
        for phrase in ["1905–13", "1953–59", "first three International Chopin Competitions", "school concert of June 1925", "Witold Lutosławski"]:
            self.assertIn(phrase, source["researchNote"])
        self.assertEqual(source["personIds"], ["P009", "P131"])
        self.assertEqual(source["timelineEventIds"], ["TE0013"])

    def test_feline_membership_is_not_a_professional_debut(self):
        note = self.sources["SRC0819"]["researchNote"]
        self.assertIn("1 May 1935", note)
        self.assertIn("not the beginning of his professional songwriting career", note)
        self.assertNotIn("marks the start", note)
        self.assertNotIn("shortly before the first songs", note)

    def test_other_membership_notes_do_not_promote_admission_to_a_career_start(self):
        self.assertNotIn("start of his registered authorship", self.sources["SRC0822"]["researchNote"])
        self.assertIn("election as a full member to 1918", self.sources["SRC0823"]["researchNote"])

    def test_oeml_date_is_explicit_content_update_not_first_publication(self):
        source = self.sources["SRC0684"]
        self.assertEqual(source["date"], "2003-04-25")
        self.assertEqual(source["dateRole"], "record_update")
        self.assertEqual(source["dateQualifier"], "confirmed")
        self.assertIn("Last content update 25 April 2003", source["fullCitation"])
        self.assertIn("Letzte inhaltliche Änderung", source["researchNote"])
        self.assertIn("not an independently established first-publication date", source["researchNote"])
        self.assertIn("without the h", source["researchNote"])
        self.assertEqual(normalized_source(dict(source, date="", dateRole="described_item", dateQualifier="unknown")), source)

    def test_reviewed_editorial_fields_are_idempotent_and_export_logged(self):
        for source_id in REVIEWED_DATABASE_FIELDS:
            with self.subTest(source=source_id):
                source = self.sources[source_id]
                self.assertEqual(source["sourceType"], "online_database")
                self.assertEqual(normalized_source(source), source)
                self.assertEqual(normalized_source(dict(source, fullCitation="Legacy mixed citation", researchNote="Legacy incomplete note")), source)
                for key, value in self.overrides["records"]["Sources"][source_id]["fields"].items():
                    self.assertEqual(source.get(key), value, key)


if __name__ == "__main__":
    unittest.main()
