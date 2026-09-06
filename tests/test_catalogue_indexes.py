from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
INDEXES = ROOT / "data/site/indexes"

CONFIG = {
    "works": ("works.html", "work-results", "article", 36, "assets/site/works.js"),
    "people": ("people.html", "person-results", "article", 48, "assets/site/people.js"),
    "media": ("media.html", "media-results", "article", 30, "assets/site/gallery.js"),
    "sources": ("sources.html", "source-results", "article", 40, "assets/site/sources.js"),
}


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class CompactCatalogueIndexTests(unittest.TestCase):
    def test_each_index_is_complete_and_uses_the_public_schema_version(self) -> None:
        schema_version = read(PUBLIC / "manifest.json")["schemaVersion"]
        for name in CONFIG:
            with self.subTest(index=name):
                compact = read(INDEXES / f"{name}.json")
                canonical = read(PUBLIC / f"{name}.json")
                self.assertEqual(compact["schemaVersion"], schema_version)
                self.assertEqual(compact["count"], len(compact["records"]))
                self.assertEqual(
                    {record["id"] for record in compact["records"]},
                    {record["id"] for record in canonical["records"]},
                )

    def test_browse_scripts_load_one_compact_payload_not_relational_tables(self) -> None:
        for name, (_, _, _, _, script_name) in CONFIG.items():
            source = (ROOT / script_name).read_text(encoding="utf-8")
            with self.subTest(index=name):
                self.assertIn(f'loadSiteIndex("{name}")', source)
                self.assertNotIn("loadTables", source)

    def test_prerendered_first_results_are_present_in_the_html(self) -> None:
        for name, (page_name, target_id, element, limit, _) in CONFIG.items():
            text = (ROOT / page_name).read_text(encoding="utf-8")
            match = re.search(
                r"<!-- catalogue-prerender:start -->(.*?)<!-- catalogue-prerender:end -->",
                text,
                flags=re.DOTALL,
            )
            with self.subTest(index=name):
                self.assertIsNotNone(match)
                self.assertRegex(text, rf'<div[^>]+id="{target_id}"[^>]+data-prerendered="true"')
                block = match.group(1)
                self.assertEqual(block.count(f"<{element} "), limit)
                self.assertNotIn('class="loading"', block)

    def test_compact_payloads_are_materially_smaller_than_previous_page_loads(self) -> None:
        old_loads = {
            "works": ("works.json", "people.json", "films.json", "songs.json", "other-works.json", "contributions.json", "title-variants.json"),
            "people": ("people.json", "works.json", "media.json", "sources.json", "timeline-events.json", "contributions.json", "person-name-variants.json"),
            "media": ("media.json", "sources.json"),
            "sources": ("sources.json",),
        }
        for name, filenames in old_loads.items():
            compact_size = (INDEXES / f"{name}.json").stat().st_size
            previous_size = sum((PUBLIC / filename).stat().st_size for filename in filenames)
            with self.subTest(index=name):
                self.assertLess(compact_size, previous_size * 0.7)

    def test_compact_indexes_keep_search_material_needed_for_browse_queries(self) -> None:
        works = {item["id"]: item for item in read(INDEXES / "works.json")["records"]}
        people = {item["id"]: item for item in read(INDEXES / "people.json")["records"]}
        sources = {item["id"]: item for item in read(INDEXES / "sources.json")["records"]}
        canonical_sources = {item["id"]: item for item in read(PUBLIC / "sources.json")["records"]}

        self.assertIn("Richard Tauber", works["W-S059"]["searchSupplement"])
        self.assertIn("Chwast", people["P009"]["searchSupplement"])

        # A source's short citation is not merely a display abbreviation: it
        # carries common research queries such as archive acronyms, catalogue
        # shorthands and shelfmarks. Every one must remain searchable after
        # replacing the full relational Sources payload with the compact index.
        for source_id, source in canonical_sources.items():
            short_citation = source.get("shortCitation")
            if short_citation:
                with self.subTest(source=source_id):
                    self.assertIn(short_citation, sources[source_id]["searchSupplement"])


if __name__ == "__main__":
    unittest.main()
