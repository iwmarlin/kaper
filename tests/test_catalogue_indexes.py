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

    def test_work_rows_use_role_qualified_canonical_credits(self) -> None:
        works = {item["id"]: item for item in read(INDEXES / "works.json")["records"]}
        canonical_works = {item["id"]: item for item in read(PUBLIC / "works.json")["records"]}
        contributions = {
            item["id"]: item
            for item in read(PUBLIC / "contributions.json")["records"]
        }
        people = {item["id"]: item for item in read(PUBLIC / "people.json")["records"]}

        allowed = {
            "Film": {"film_director", "composer"},
            "Song": {"composer", "lyricist", "arranger"},
            "Other": {"composer", "lyricist", "arranger"},
        }
        for work_id, work in canonical_works.items():
            expected = []
            for contribution_id in work.get("contributionIds") or []:
                contribution = contributions[contribution_id]
                if contribution.get("role") not in allowed[work["workType"]]:
                    continue
                for person_id in contribution.get("personIds") or []:
                    entry = {
                        "role": contribution["role"],
                        "name": people[person_id]["displayName"],
                    }
                    certainty = contribution.get("certainty")
                    if certainty and certainty != "confirmed":
                        entry["certainty"] = certainty
                    if entry not in expected:
                        expected.append(entry)
            actual = [
                {"role": group["role"], **person}
                for group in works[work_id]["principalCredits"]
                for person in group["people"]
            ]
            with self.subTest(work=work_id):
                self.assertCountEqual(actual, expected)

        song_credits = {
            group["role"]: group["people"]
            for group in works["W-S152"]["principalCredits"]
        }
        self.assertEqual(
            [person["name"] for person in song_credits["composer"]],
            ["Bronisław Kaper", "Walter Jurmann"],
        )
        self.assertEqual(
            [person["name"] for person in song_credits["lyricist"]],
            ["Gus Kahn"],
        )
        self.assertNotIn("performer", song_credits)
        self.assertNotIn("publisher", song_credits)

        qualified = {
            group["role"]: group["people"]
            for group in works["W-F015"]["principalCredits"]
        }
        probable = next(
            person
            for person in qualified["composer"]
            if person["name"] == "Bronisław Kaper"
        )
        self.assertEqual(probable["certainty"], "probable")

    def test_people_rows_carry_the_exact_documented_work_count(self) -> None:
        people = {item["id"]: item for item in read(INDEXES / "people.json")["records"]}
        canonical = {item["id"]: item for item in read(PUBLIC / "people.json")["records"]}
        work_ids = {item["id"] for item in read(PUBLIC / "works.json")["records"]}
        for person_id, person in canonical.items():
            with self.subTest(person=person_id):
                expected = len([
                    work_id
                    for work_id in person.get("workIds") or []
                    if work_id in work_ids
                ])
                self.assertEqual(people[person_id]["workCount"], expected)

    def test_hero_does_not_duplicate_dynamic_result_totals(self) -> None:
        for page_name in ("works.html", "people.html", "media.html", "sources.html"):
            with self.subTest(page=page_name):
                text = (ROOT / page_name).read_text(encoding="utf-8")
                hero = re.search(r'<section class="page-hero.*?</section>', text, re.DOTALL)
                self.assertIsNotNone(hero)
                self.assertNotIn("documented people", hero.group(0))
                self.assertNotIn("documented sources", hero.group(0))

    def test_prerendered_rows_expose_the_same_context_without_javascript(self) -> None:
        works_page = (ROOT / "works.html").read_text(encoding="utf-8")
        people_page = (ROOT / "people.html").read_text(encoding="utf-8")
        self.assertIn('class="work-row__credits"', works_page)
        self.assertIn("Music: Bronisław Kaper", works_page)
        self.assertIn('class="person-row__work-count"', people_page)
        self.assertIn("2 documented works", people_page)


if __name__ == "__main__":
    unittest.main()
