from __future__ import annotations

import json
import sys
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
sys.path.insert(0, str(ROOT / "scripts"))

from public_data_dates import (  # noqa: E402
    resolve_public_data_updated_at,
    validated_public_data_date,
)


class PublicDataUpdatedAtTests(unittest.TestCase):
    def test_code_only_rebuild_preserves_dataset_date(self) -> None:
        self.assertEqual(
            resolve_public_data_updated_at(
                "2026-09-01",
                data_changed=False,
                today=date(2026, 9, 8),
            ),
            "2026-09-01",
        )

    def test_canonical_data_change_advances_dataset_date(self) -> None:
        self.assertEqual(
            resolve_public_data_updated_at(
                "2026-09-01",
                data_changed=True,
                today=date(2026, 9, 8),
            ),
            "2026-09-08",
        )

    def test_explicit_date_is_strict_and_deterministic(self) -> None:
        self.assertEqual(
            resolve_public_data_updated_at(
                "2026-09-01",
                data_changed=True,
                requested_value="2026-09-07",
                today=date(2026, 9, 8),
            ),
            "2026-09-07",
        )
        with self.assertRaises(ValueError):
            validated_public_data_date("2026-9-8")
        with self.assertRaises(ValueError):
            validated_public_data_date("2026-02-30")

    def test_manifest_is_not_older_than_documented_source_access(self) -> None:
        manifest = json.loads(
            (PUBLIC / "manifest.json").read_text(encoding="utf-8")
        )
        sources = json.loads(
            (PUBLIC / "sources.json").read_text(encoding="utf-8")
        )["records"]
        manifest_date = validated_public_data_date(
            manifest["publicDataUpdatedAt"]
        )
        latest_access_date = max(
            validated_public_data_date(source["accessDate"])
            for source in sources
            if source.get("accessDate")
        )
        self.assertGreaterEqual(
            manifest_date,
            latest_access_date,
            "publicDataUpdatedAt must cover the newest documented source consultation",
        )


if __name__ == "__main__":
    unittest.main()
