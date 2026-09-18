from __future__ import annotations

import html
import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_static_records import (  # noqa: E402
    SOURCE_PAGE_TITLE_BUDGET,
    source_title_qualifier,
)


def read_records(name: str) -> list[dict]:
    return json.loads((ROOT / "data/public/v1" / f"{name}.json").read_text("utf-8"))["records"]


def page_title(record: dict) -> str:
    qualifier = source_title_qualifier(record)
    stem = f"{record['title']} — {qualifier}" if qualifier else record["title"]
    composed = f"{stem} (source)"
    if len(composed) > SOURCE_PAGE_TITLE_BUDGET:
        return f"{record['title']} (source)"
    return composed


class SourceTitleQualifierTests(unittest.TestCase):
    def test_bare_title_is_qualified_by_publication(self) -> None:
        self.assertEqual(
            source_title_qualifier({"title": "Alraune", "publication": "filmportal.de"}),
            "filmportal.de",
        )

    def test_repository_is_used_when_publication_is_absent(self) -> None:
        self.assertEqual(
            source_title_qualifier({"title": "Bolszewik", "repository": "Polona"}),
            "Polona",
        )

    def test_title_already_naming_its_publication_is_not_repeated(self) -> None:
        self.assertEqual(
            source_title_qualifier(
                {
                    "title": "Catalog of Copyright Entries: “Cosi cosa”",
                    "publication": "Catalog of Copyright Entries",
                }
            ),
            "",
        )

    def test_qualifier_is_absent_without_publication_or_repository(self) -> None:
        self.assertEqual(source_title_qualifier({"title": "Alraune"}), "")


class SourcePageTitleTests(unittest.TestCase):
    """A source page title must identify the document outside the page, where
    neither the record eyebrow, the type badge nor the citation block travels."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = read_records("sources")
        cls.titles = [page_title(record) for record in cls.sources]

    def test_no_source_page_title_repeats_a_work_title(self) -> None:
        work_titles = {item["title"].strip().casefold() for item in read_records("works")}
        collisions = [
            record["id"]
            for record, title in zip(self.sources, self.titles)
            if title.removesuffix(" (source)").strip().casefold() in work_titles
        ]
        self.assertEqual(collisions, [])

    def test_page_titles_are_unique(self) -> None:
        duplicates = {title for title in self.titles if self.titles.count(title) > 1}
        self.assertEqual(duplicates, set())

    def test_qualifier_never_pushes_a_title_past_the_budget(self) -> None:
        over = [
            (record["id"], len(title))
            for record, title in zip(self.sources, self.titles)
            if len(title) > SOURCE_PAGE_TITLE_BUDGET
            and title != f"{record['title']} (source)"
        ]
        self.assertEqual(over, [])

    def test_generated_pages_carry_the_qualified_title(self) -> None:
        for record in self.sources:
            document = ROOT / "records/source" / record["id"] / "index.html"
            if not document.exists():
                continue
            match = re.search(r"<title>([^<]*)</title>", document.read_text("utf-8"))
            self.assertIsNotNone(match, msg=record["id"])
            self.assertEqual(
                html.unescape(match.group(1)),
                f"{page_title(record)} | Kaper Archive",
                msg=record["id"],
            )


if __name__ == "__main__":
    unittest.main()
