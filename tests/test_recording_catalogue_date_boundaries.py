"""Catalogue bounds and shared masters must not become invented issue dates."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source
from source_dates import normalized_source_date_fields, source_date_errors
from recording_sources import recording_catalogue_evidence_errors

REVIEWED = {"SRC0633", "SRC0773", "SRC0785", "SRC0829"}


class RecordingCatalogueDateBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {
            r["id"]: r for r in json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        }
        cls.media = {
            r["id"]: r for r in json.loads((ROOT / "data/public/v1/media.json").read_text())["records"]
        }

    def test_bn_lower_bound_is_not_an_exact_1933_issue_date(self):
        source = self.sources["SRC0633"]
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1930", "issue", "after"))
        self.assertEqual(source["dateDisplay"], "[post 1930]")
        self.assertIn("[post 1930]", source["fullCitation"])
        self.assertIn("does not assert an issue in 1933", source["researchNote"])

    def test_bn_catalogue_type_and_institution_remain_consistent(self):
        source = self.sources["SRC0633"]
        self.assertEqual(source["sourceType"], "sound_recording_catalogue")
        self.assertEqual(source["repository"], "Biblioteka Narodowa")
        self.assertIn("katalogi.bn.org.pl/", source["primaryUrl"])
        self.assertIn("Biblioteka Narodowa catalogue in SRC0633",
                      self.sources["SRC0761"]["researchNote"])
        self.assertNotIn("BnF catalogue in SRC0633", self.sources["SRC0761"]["researchNote"])
        stale = dict(source, sourceType="recording_discographic_source")
        self.assertEqual(normalized_source(stale), source)
        self.assertTrue(recording_catalogue_evidence_errors(stale, {}))
        self.assertEqual(recording_catalogue_evidence_errors(source, {}), [])
        stale_note = dict(self.sources["SRC0761"], researchNote="the BnF catalogue in SRC0633")
        self.assertEqual(normalized_source(stale_note), self.sources["SRC0761"])
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        self.assertEqual(overrides["records"]["Sources"]["SRC0633"]["fields"]["sourceType"],
                         "sound_recording_catalogue")
        self.assertIn("Biblioteka Narodowa catalogue in SRC0633",
                      overrides["records"]["Sources"]["SRC0761"]["fields"]["researchNote"])

    def test_fiesta_links_to_the_individual_record_not_only_the_composer(self):
        source = self.sources["SRC0773"]
        self.assertEqual(source["primaryUrl"], "https://diskografie.nm.cz/nahravky/fiesta-bianca/")
        self.assertIn("Ultraphon 20040 A", source["fullCitation"])
        self.assertIn("18145", source["fullCitation"])
        self.assertIn("1932–1933", source["researchNote"])
        self.assertIn("catalogue appearance", source["researchNote"])

    def test_undated_catalogue_issues_remain_undated(self):
        for sid in ("SRC0773", "SRC0829"):
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertNotIn("date", source)
                self.assertNotIn("dateDisplay", source)
                self.assertEqual(source["dateQualifier"], "unknown")
                self.assertEqual(source["dateRole"], "issue")
        self.assertEqual(self.sources["SRC0829"]["sourceType"], "sound_recording_catalogue")
        self.assertIn("field 264", self.sources["SRC0829"]["researchNote"])
        self.assertIn("field 008", self.sources["SRC0829"]["researchNote"])

    def test_danish_pressing_is_not_dated_from_the_german_release(self):
        source = self.sources["SRC0785"]
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1932-06-11", "recording", "confirmed"))
        self.assertIn("matrix Bi 644, n.d.", source["fullCitation"])
        self.assertIn("November 1932 as the German issue date", source["researchNote"])
        self.assertIn("Neither November 1932 nor the year of the film is assigned as the issue date of D 4431", source["researchNote"])
        self.assertIn("pressing’s label and issue date remain unestablished", source["researchNote"])
        self.assertTrue(source["additionalLinks"][0]["url"].endswith("titel_wi-wirf.html"))
        self.assertEqual(self.media["M409"]["sourceIds"], ["SRC0785"])
        self.assertEqual(self.media["M409"]["externalUrl"], source["primaryUrl"])

    def test_normalization_removes_legacy_inferences(self):
        for sid in REVIEWED:
            with self.subTest(source=sid):
                source = self.sources[sid]
                stale = dict(source, date="1933", dateRole="issue", dateQualifier="confirmed")
                if sid in {"SRC0773", "SRC0829"}:
                    stale["dateDisplay"] = "[1933]"
                self.assertEqual(normalized_source(stale), source)
                self.assertEqual(normalized_source(normalized_source(source)), source)
                self.assertEqual(source_date_errors(source), [])

    def test_reviewed_date_model_does_not_infer_a_year_from_citation_text(self):
        for sid in ("SRC0773", "SRC0829"):
            with self.subTest(source=sid):
                stale = dict(self.sources[sid], date="1930")
                self.assertEqual(normalized_source_date_fields(stale),
                                 {"dateRole": "issue", "dateQualifier": "unknown"})

    def test_audit_log_preserves_explicit_removals_and_lower_bound(self):
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        for sid in ("SRC0773", "SRC0829"):
            entry = overrides["records"]["Sources"][sid]
            self.assertTrue({"date", "dateDisplay"} <= set(entry["removeFields"]))
            self.assertNotIn("date", entry["fields"])
        self.assertEqual(overrides["records"]["Sources"]["SRC0633"]["fields"]["dateQualifier"], "after")


if __name__ == "__main__":
    unittest.main()
