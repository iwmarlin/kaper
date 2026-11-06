from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "assets/site/core.js"
CATALOGUE_RESULTS = ROOT / "assets/site/catalogue-results.js"
SOURCES_PAGE = ROOT / "sources.html"
SOURCES_DATA = ROOT / "data/public/v1/sources.json"


def object_entries(constant: str, value_pattern: str) -> dict[str, str]:
    text = CORE.read_text(encoding="utf-8")
    block = re.search(
        rf"export const {constant} = Object\.freeze\(\{{(.*?)\n\}}\);",
        text,
        re.S,
    )
    assert block, f"{constant} is no longer a literal object in core.js"
    return dict(re.findall(value_pattern, block.group(1), re.M))


def source_type_keys() -> set[str]:
    text = CORE.read_text(encoding="utf-8")
    block = re.search(
        r"export const SOURCE_TYPES = Object\.freeze\(\{(.*?)\n\}\);",
        text,
        re.S,
    )
    assert block, "SOURCE_TYPES is no longer a literal object in core.js"
    return set(re.findall(
        r'^\s*([a-z_]+): \{ one: "[^"]+", many: "[^"]+" \},',
        block.group(1),
        re.M,
    ))


def icon_mapping() -> dict[str, str]:
    return object_entries(
        "SOURCE_TYPE_ICON_FAMILIES",
        r'^\s*([a-z_]+): "([a-z_]+)",',
    )


class SourceTypeIconTests(unittest.TestCase):
    """The source icons form one complete, decorative visual vocabulary.

    The technical source type remains written in every row. These tests ensure
    that the assisting icon system cannot silently drift from the controlled
    source vocabulary or render a broken <use> reference.
    """

    def test_every_curated_source_type_has_exactly_one_icon_family(self) -> None:
        self.assertEqual(set(icon_mapping()), source_type_keys())

    def test_every_published_source_type_is_covered(self) -> None:
        records = json.loads(SOURCES_DATA.read_text(encoding="utf-8"))["records"]
        published_types = {record["sourceType"] for record in records}
        self.assertEqual(published_types - set(icon_mapping()), set())

    def test_the_system_stays_within_the_ten_approved_families(self) -> None:
        self.assertEqual(
            set(icon_mapping().values()),
            {
                "archive",
                "audio",
                "authority",
                "film",
                "press",
                "publication",
                "register",
                "score",
                "visual",
                "web",
            },
        )

    def test_the_page_defines_each_used_symbol_once(self) -> None:
        text = SOURCES_PAGE.read_text(encoding="utf-8")
        symbols = re.findall(r'<symbol id="source-icon-([a-z_]+)"', text)
        self.assertEqual(len(symbols), len(set(symbols)), "a source icon symbol is duplicated")
        self.assertEqual(set(symbols), set(icon_mapping().values()))

    def test_formerly_colliding_families_do_not_share_a_box_frame(self) -> None:
        text = SOURCES_PAGE.read_text(encoding="utf-8")
        for family in ("press", "film", "web", "archive"):
            block = re.search(
                rf'<symbol id="source-icon-{family}".*?</symbol>',
                text,
                re.S,
            )
            self.assertIsNotNone(block)
            self.assertNotIn(
                "<rect",
                block.group(0),
                f"{family} has regained the shared rectangular silhouette",
            )

    def test_authority_icon_keeps_its_optical_weight(self) -> None:
        text = SOURCES_PAGE.read_text(encoding="utf-8")
        opening = re.search(r'<symbol id="source-icon-authority"[^>]+>', text)
        self.assertIsNotNone(opening)
        self.assertIn('stroke-width="2"', opening.group(0))

    def test_icons_are_decorative_and_the_written_type_remains(self) -> None:
        renderer = CATALOGUE_RESULTS.read_text(encoding="utf-8")
        self.assertIn('class="source-type-icon" aria-hidden="true" focusable="false"', renderer)
        self.assertIn("sourceTypeLabel(source.sourceType)", renderer)

    def test_prerendered_rows_use_the_same_icon_markup(self) -> None:
        text = SOURCES_PAGE.read_text(encoding="utf-8")
        block = re.search(
            r"<!-- catalogue-prerender:start -->(.*?)<!-- catalogue-prerender:end -->",
            text,
            re.S,
        )
        self.assertIsNotNone(block)
        self.assertEqual(block.group(1).count('class="source-type-icon"'), 40)


if __name__ == "__main__":
    unittest.main()
