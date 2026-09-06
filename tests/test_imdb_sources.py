from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from filmographic_sources import expected_imdb_source_type, source_hostname  # noqa: E402


def records(filename: str) -> list[dict]:
    return json.loads((PUBLIC / filename).read_text(encoding="utf-8"))["records"]


class ImdbSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = {record["id"]: record for record in records("sources.json")}
        cls.media = {record["id"]: record for record in records("media.json")}
        cls.organizations = {
            record["id"]: record for record in records("organizations.json")
        }

    def test_imdb_page_kind_determines_source_type(self) -> None:
        imdb_sources = [
            source
            for source in self.sources.values()
            if source_hostname(source) in {"imdb.com", "www.imdb.com"}
        ]
        self.assertTrue(imdb_sources, "the IMDb-specific rules inspected no sources")
        for source in imdb_sources:
            self.assertEqual(
                expected_imdb_source_type(source),
                source.get("sourceType"),
                source["id"],
            )
            self.assertEqual("IMDb", source.get("repository"), source["id"])
            self.assertIn("ORG092", source.get("organizationIds") or [], source["id"])
            self.assertTrue(source.get("accessDate"), source["id"])

    def test_imdb_organization_contains_only_imdb_primary_records(self) -> None:
        linked_ids = self.organizations["ORG092"].get("sourceIds") or []
        for source_id in linked_ids:
            self.assertIn(source_id, self.sources)
            self.assertIn(
                source_hostname(self.sources[source_id]),
                {"imdb.com", "www.imdb.com"},
                source_id,
            )

    def test_obsolete_duplicate_image_sources_are_absent(self) -> None:
        for source_id in ("SRC0339", "SRC0340", "SRC0342", "SRC0343"):
            self.assertNotIn(source_id, self.sources)

    def test_shot_at_dawn_medium_uses_its_direct_ucla_source(self) -> None:
        self.assertEqual(["SRC0166"], self.media["M151"].get("sourceIds"))
        self.assertIn("M151", self.sources["SRC0166"].get("mediaIds") or [])
        self.assertNotIn("mediaIds", self.sources["SRC0516"])

    def test_wikipedia_non_free_programme_covers_are_restricted(self) -> None:
        expected_sources = {
            "M077": "SRC0414",
            "M149": "SRC0413",
            "M164": "SRC0403",
            "M167": "SRC0412",
        }
        for media_id, source_id in expected_sources.items():
            medium = self.media[media_id]
            self.assertEqual("restricted", medium.get("rightsStatus"), media_id)
            self.assertEqual("detail_only", medium.get("galleryStatus"), media_id)
            self.assertEqual([source_id], medium.get("sourceIds"), media_id)
            self.assertEqual(
                "wikimedia_article_page",
                self.sources[source_id].get("sourceType"),
                source_id,
            )
            self.assertEqual(["ORG090"], self.sources[source_id].get("organizationIds"))


if __name__ == "__main__":
    unittest.main()
