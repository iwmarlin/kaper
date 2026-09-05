from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
sys.path.insert(0, str(ROOT / "scripts"))

from sheet_music_sources import (  # noqa: E402
    is_catalogue_landing_page_for_sheet_music,
    normalize_sheet_music_source,
)


def sources() -> list[dict]:
    return json.loads((PUBLIC / "sources.json").read_text(encoding="utf-8"))["records"]


class SheetMusicSourceSemanticsTests(unittest.TestCase):
    def test_catalogue_landing_pages_are_not_presented_as_examined_scores(self) -> None:
        wrong = [
            f"{source['id']}: {source.get('primaryUrl')}"
            for source in sources()
            if is_catalogue_landing_page_for_sheet_music(source)
            and source.get("sourceType") != "sheet_music_catalogue"
        ]
        self.assertEqual(wrong, [])

    def test_catalogue_normalizer_does_not_touch_a_digitized_score(self) -> None:
        source = {
            "id": "SRC9999",
            "sourceType": "sheet_music",
            "primaryUrl": "https://polona.pl/item-view/example?page=1",
        }
        original = dict(source)

        normalize_sheet_music_source(source)

        self.assertEqual(source, original)

    def test_catalogue_normalizer_reclassifies_but_does_not_rewrite_metadata(self) -> None:
        source = {
            "id": "SRC9998",
            "sourceType": "sheet_music",
            "title": "Example score",
            "publication": "Example Publisher",
            "primaryUrl": "https://catalogue.bnf.fr/ark:/12148/example",
        }

        normalize_sheet_music_source(source)

        self.assertEqual(source["sourceType"], "sheet_music_catalogue")
        self.assertEqual(source["title"], "Example score")
        self.assertEqual(source["publication"], "Example Publisher")


if __name__ == "__main__":
    unittest.main()
