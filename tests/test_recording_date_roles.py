"""Keep reviewed recording dates attached to the event actually documented."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source
from source_dates import normalized_source_date_fields


CASES = {
    "SRC0710": ("1931", "issue", "reported", "recording"),
    "SRC0712": ("1932", "recording", "confirmed", "issue"),
    "SRC0718": ("1931-03-11", "recording", "confirmed", "issue"),
    "SRC0724": ("1930-10", "described_item", "uncertain", "issue"),
    "SRC0792": ("1998", "publication", "confirmed", "issue"),
    "SRC0807": ("1932-08-15", "recording", "confirmed", "issue"),
}


class RecordingDateRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {
            r["id"]: r
            for r in json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        }

    def test_canonical_dates_keep_precision_and_qualification(self):
        for sid, (date, role, qualifier, _) in CASES.items():
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual(source["date"], date)
                self.assertEqual(source["dateRole"], role)
                self.assertEqual(source["dateQualifier"], qualifier)

    def test_legacy_roles_are_corrected_without_other_record_changes(self):
        for sid, (_, role, _, legacy_role) in CASES.items():
            with self.subTest(source=sid):
                source = self.sources[sid]
                legacy = dict(source, dateRole=legacy_role)
                self.assertEqual(normalized_source_date_fields(legacy)["dateRole"], role)
                self.assertEqual(normalized_source(legacy), source)

    def test_normalization_is_idempotent(self):
        for sid in CASES:
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual(normalized_source(normalized_source(source)), source)

    def test_audit_log_persists_each_role_correction(self):
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        for sid, (_, role, _, _) in CASES.items():
            with self.subTest(source=sid):
                self.assertEqual(overrides["records"]["Sources"][sid]["fields"]["dateRole"], role)


if __name__ == "__main__":
    unittest.main()
