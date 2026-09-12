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

    def test_audited_non_score_records_keep_their_specific_source_types(self) -> None:
        expected = {
            "SRC0203": "archival_manuscript_holding",
            "SRC0286": "sheet_music_catalogue",
            "SRC0854": "sheet_music_catalogue",
            "SRC0855": "sheet_music_catalogue",
        }
        by_id = {source["id"]: source for source in sources()}

        for source_id, source_type in expected.items():
            self.assertEqual(by_id[source_id]["sourceType"], source_type, source_id)
            source = dict(by_id[source_id])
            normalize_sheet_music_source(source)
            self.assertEqual(source["sourceType"], source_type, source_id)

    def test_verified_notated_objects_remain_sheet_music(self) -> None:
        by_id = {source["id"]: source for source in sources()}

        for source_id in ("SRC0296", "SRC0774", "SRC0775"):
            source = dict(by_id[source_id])
            normalize_sheet_music_source(source)
            self.assertEqual(source["sourceType"], "sheet_music", source_id)

    def test_finding_aid_does_not_claim_item_level_credit_evidence(self) -> None:
        by_id = {source["id"]: source for source in sources()}
        source = by_id["SRC0203"]

        self.assertEqual(source.get("organizationIds"), ["ORG164"])
        self.assertNotIn("contributionIds", source)
        self.assertNotIn("titleVariantIds", source)
        self.assertNotIn("date", source)
        self.assertEqual(source.get("dateQualifier"), "unknown")

    def test_contents_list_credit_evidence_comes_from_hofmeister(self) -> None:
        by_id = {source["id"]: source for source in sources()}
        contents = by_id["SRC0286"]
        hofmeister = by_id["SRC0101"]

        self.assertNotIn("contributionIds", contents)
        self.assertEqual(
            set(hofmeister.get("contributionIds", [])),
            {
                "CON-S045-C-P009",
                "CON-S045-L-P020",
                "CON-S045-PUB-ORG029",
            },
        )


if __name__ == "__main__":
    unittest.main()
