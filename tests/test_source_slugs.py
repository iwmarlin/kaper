from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
sys.path.insert(0, str(ROOT / "scripts"))

from source_slugs import canonical_source_slug  # noqa: E402


class SourceSlugTests(unittest.TestCase):
    def test_every_canonical_source_uses_its_id_as_the_slug_prefix(self) -> None:
        records = json.loads(
            (PUBLIC / "sources.json").read_text(encoding="utf-8")
        )["records"]
        offenders = [
            source["id"]
            for source in records
            if source.get("slug") != canonical_source_slug(source)
        ]
        self.assertEqual(offenders, [])

    def test_legacy_trailing_id_is_moved_without_losing_the_description(self) -> None:
        source = {
            "id": "SRC0009",
            "slug": "bronislaw-kaper-papers-early-composition-manuscripts-src0009",
        }
        self.assertEqual(
            canonical_source_slug(source),
            "src0009-bronislaw-kaper-papers-early-composition-manuscripts",
        )

    def test_zero_padded_legacy_prefix_is_not_duplicated(self) -> None:
        source = {"id": "SRC0816", "slug": "src00816-pbm-smidowicz-jozef"}
        self.assertEqual(
            canonical_source_slug(source),
            "src0816-pbm-smidowicz-jozef",
        )


if __name__ == "__main__":
    unittest.main()
