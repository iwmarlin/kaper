from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"


def sources_by_id() -> dict[str, dict]:
    records = json.loads((PUBLIC / "sources.json").read_text(encoding="utf-8"))["records"]
    return {record["id"]: record for record in records}


class SecondarySourceTypeTests(unittest.TestCase):
    def test_dissertation_entries_are_secondary_literature(self) -> None:
        records = sources_by_id()
        for source_id in ("SRC0288", "SRC0289", "SRC0290"):
            self.assertEqual(
                records[source_id]["sourceType"],
                "secondary_literature",
                source_id,
            )

    def test_forthcoming_publications_use_their_document_form(self) -> None:
        records = sources_by_id()
        for source_id in ("SRC0490", "SRC0491"):
            self.assertEqual(
                records[source_id]["sourceType"],
                "periodical_article",
                source_id,
            )

        self.assertEqual(
            records["SRC0490"].get("publication"),
            "Roczniki Humanistyczne, fascicle 12",
        )

    def test_genuine_books_remain_books(self) -> None:
        records = sources_by_id()
        for source_id in ("SRC0354", "SRC0373", "SRC0375", "SRC0547", "SRC0692"):
            self.assertEqual(records[source_id]["sourceType"], "book", source_id)


if __name__ == "__main__":
    unittest.main()
