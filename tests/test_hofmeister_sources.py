from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hofmeister_sources import normalize_hofmeister_source  # noqa: E402


class HofmeisterSourceNormalizationTests(unittest.TestCase):
    def test_register_notice_is_not_sheet_music(self) -> None:
        source = {
            "id": "SRC9999",
            "sourceType": "sheet_music",
            "title": "Example song — sheet music",
            "shortCitation": "Composer, Example song (Berlin, 1931).",
            "fullCitation": (
                "Composer, Example song. Berlin: Example Verlag, 1931. "
                "Registered in Hofmeisters Musikalisch-literarischer Monatsbericht "
                "103, no. 2 (February 1931): 35."
            ),
            "repository": "Österreichische Nationalbibliothek / ANNO",
            "primaryUrl": (
                "https://anno.onb.ac.at/cgi-content/anno-plus?aid=hof&datum=19310052"
            ),
            "date": "1931",
            "dateRole": "issue",
        }

        normalize_hofmeister_source(source)

        self.assertEqual(source["sourceType"], "sheet_music_catalogue")
        self.assertEqual(source["date"], "1931-02")
        self.assertEqual(source["dateRole"], "catalogue_volume")
        self.assertEqual(
            source["title"],
            "Hofmeisters Musikalisch-literarischer Monatsbericht: “Example song”",
        )
        self.assertEqual(
            source["shortCitation"],
            "Hofmeister, February 1931, p. 35 — “Example song”",
        )
        once = dict(source)
        normalize_hofmeister_source(source)
        self.assertEqual(source, once, "normalization must be idempotent")

    def test_concrete_score_at_another_holding_is_untouched(self) -> None:
        source = {
            "id": "SRC9998",
            "sourceType": "sheet_music",
            "title": "Example song",
            "fullCitation": (
                "Example song. Physical score, shelfmark Mus. 123. "
                "Also registered in Hofmeisters Musikalisch-literarischer Monatsbericht."
            ),
            "repository": "Example Music Library",
            "primaryUrl": "https://library.example/item/123",
        }
        original = dict(source)

        normalize_hofmeister_source(source)

        self.assertEqual(source, original)

    def test_internet_archive_wording_is_recognized_without_claiming_a_score(self) -> None:
        source = {
            "id": "SRC0461",
            "sourceType": "sheet_music",
            "title": "Example song — Hofmeister / Internet Archive entry",
            "shortCitation": "Example song — Hofmeister / Internet Archive",
            "fullCitation": (
                "Example song. Berlin: Alrobi, 1931. Bibliographic notice in "
                "Friedrich Hofmeister, Musikalisch-literarischer Monatsbericht "
                "über neue Musikalien, 1931, Internet Archive scan, page/leaf n33."
            ),
            "repository": "Internet Archive",
            "publication": "Berlin: Alrobi / Hofmeister",
            "primaryUrl": (
                "https://archive.org/details/Musikalisch-literarischerMonatsbericht1931/"
                "page/n33/mode/2up"
            ),
            "date": "1931",
        }

        normalize_hofmeister_source(source)

        self.assertEqual(source["sourceType"], "sheet_music_catalogue")
        self.assertEqual(source["publication"], "Alrobi, Berlin")
        self.assertEqual(
            source["title"],
            "Hofmeisters Musikalisch-literarischer Monatsbericht: “Example song” "
            "— Internet Archive scan",
        )
        once = dict(source)
        normalize_hofmeister_source(source)
        self.assertEqual(source, once, "Internet Archive normalization must be idempotent")


if __name__ == "__main__":
    unittest.main()
