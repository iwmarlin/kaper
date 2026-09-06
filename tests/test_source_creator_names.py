import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
HOFMEISTER_REPOSITORY = "Österreichische Nationalbibliothek / ANNO"
INVERTED_PERSONAL_NAME = re.compile(
    r"(?:^|;\s*)[^,;]+,\s*(?:[A-ZÀ-ÖØ-Þ]\.?|[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ])"
    r"[^,;]*(?=;|$)"
)


def sources():
    return json.loads((PUBLIC / "sources.json").read_text(encoding="utf-8"))["records"]


class SourceCreatorNameTests(unittest.TestCase):
    """Hofmeister supplies catalogue-order names, but the public ``creator``
    field is normalized for reading and searching.  The citation remains the
    place for the register's original bibliographic form."""

    def test_hofmeister_sheet_music_creators_use_natural_name_order(self):
        offenders = [
            f"{record['id']}: {record.get('creator', '')}"
            for record in sources()
            if record.get("sourceType") == "sheet_music"
            and record.get("repository") == HOFMEISTER_REPOSITORY
            and INVERTED_PERSONAL_NAME.search(record.get("creator") or "")
        ]
        self.assertEqual(
            offenders,
            [],
            "a Hofmeister sheet-music creator uses catalogue order in a display field",
        )


if __name__ == "__main__":
    unittest.main()
