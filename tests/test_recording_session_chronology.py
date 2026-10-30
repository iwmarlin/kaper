"""Session dates must not silently become commercial issue dates."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source
from normalize_source_dates import merged_identifiers
from source_dates import usco_identifiers

SESSIONS = {
    "SRC0008": "1937-06-08",
    "SRC0115": "1933-11-07",
    "SRC0705": "1934-10",
    "SRC0744": "1931-03-15",
    "SRC0750": "1935-03-23",
    "SRC0753": "1931-09-15",
    "SRC0760": "1931-04-29",
    "SRC0767": "1930-03",
}


class RecordingSessionChronologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {
            r["id"]: r for r in json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        }

    def test_reviewed_dates_describe_sessions_at_documented_precision(self):
        for sid, date in SESSIONS.items():
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual(source["date"], date)
                self.assertEqual(source["dateRole"], "recording")
                self.assertEqual(source["dateQualifier"], "confirmed")
                self.assertEqual(source["sourceType"], "recording_discographic_source")

    def test_phonobase_month_is_not_completed_with_an_invented_day(self):
        source = self.sources["SRC0705"]
        self.assertEqual(source["date"], "1934-10")
        self.assertIn("1934-10-xx", source["researchNote"])
        self.assertIn("4 February 2023", source["researchNote"])

    def test_garat_session_has_independent_discographic_evidence(self):
        source = self.sources["SRC0115"]
        self.assertIn("recorded Paris, 7 November 1933", source["fullCitation"])
        self.assertIn("10–11", source["fullCitation"])
        self.assertIn("SS 1729", source["fullCitation"])
        self.assertIn("SS 1730", source["fullCitation"])
        self.assertIn("no particular take is assigned", source["researchNote"])
        self.assertTrue(source["additionalLinks"][0]["url"].endswith("Phonoscopies-005.pdf#page=6"))

    def test_stare_melodie_catalogue_and_embedded_upload_are_distinguished(self):
        source = self.sources["SRC0767"]
        self.assertEqual(source["date"], "1930-03")
        self.assertIn("1929", source["researchNote"])
        self.assertIn("site’s editor", source["researchNote"])
        self.assertIn("not a separately established issue date", source["researchNote"])

    def test_hmv_r_series_is_not_a_copyright_renewal(self):
        for citation in (
            "His Master’s Voice AM 3411 and R 14602.",
            "His Master's Voice AM 3411 and HMV R 14602.",
            "HMV R.14602.",
        ):
            with self.subTest(citation=citation):
                source = {"fullCitation": citation}
                self.assertEqual(usco_identifiers(source), [])
                source["identifiers"] = [
                    {"scheme": "usco_renewal", "value": "R 14602"},
                    {"scheme": "doi", "value": "10.1234/example"},
                ]
                self.assertEqual(merged_identifiers(source), [{"scheme": "doi", "value": "10.1234/example"}])
        self.assertNotIn("identifiers", self.sources["SRC0744"])

    def test_real_copyright_identifiers_are_preserved(self):
        source = {"fullCitation": "HMV R 14602. Copyright renewal R 54321; registration E pub. 48561."}
        self.assertEqual(usco_identifiers(source), [
            {"scheme": "usco_registration", "value": "E pub. 48561"},
            {"scheme": "usco_renewal", "value": "R 54321"},
        ])

    def test_normalization_repairs_legacy_roles_and_false_identifiers(self):
        for sid in SESSIONS:
            with self.subTest(source=sid):
                source = self.sources[sid]
                stale = dict(source, dateRole="issue")
                if sid == "SRC0744":
                    stale["identifiers"] = [{"scheme": "usco_renewal", "value": "R 14602"}]
                self.assertEqual(normalized_source(stale), source)
                self.assertEqual(normalized_source(normalized_source(source)), source)

    def test_audit_log_persists_session_dates(self):
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        for sid, date in SESSIONS.items():
            with self.subTest(source=sid):
                fields = overrides["records"]["Sources"][sid]["fields"]
                self.assertEqual(fields["date"], date)
                self.assertEqual(fields["dateRole"], "recording")
        self.assertIn("identifiers", overrides["records"]["Sources"]["SRC0744"]["removeFields"])


if __name__ == "__main__":
    unittest.main()
