from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
sys.path.insert(0, str(ROOT / "scripts"))

from source_access_dates import (  # noqa: E402
    has_redundant_access_date,
    normalize_access_citation,
)


class SourceAccessDateTests(unittest.TestCase):
    def test_trailing_access_date_is_removed(self) -> None:
        self.assertEqual(
            normalize_access_citation(
                "IMDb. Title entry. Accessed 10 June 2026."
            ),
            "IMDb. Title entry.",
        )

    def test_parenthetical_us_access_date_is_removed(self) -> None:
        self.assertEqual(
            normalize_access_citation(
                "Deutsche Nationalbibliothek. (accessed July 10, 2026)."
            ),
            "Deutsche Nationalbibliothek.",
        )

    def test_access_route_is_retained_without_event_wording(self) -> None:
        self.assertEqual(
            normalize_access_citation(
                "StabiKat record no. 524465657, accessed via KVK."
            ),
            "StabiKat record no. 524465657, available via KVK.",
        )
        self.assertEqual(
            normalize_access_citation(
                "Digitized by SLUB; accessed via arthistoricum.net."
            ),
            "Digitized by SLUB; available via arthistoricum.net.",
        )

    def test_dated_finding_aid_consultation_is_removed(self) -> None:
        self.assertEqual(
            normalize_access_citation(
                "American Heritage Center. Finding aid consulted 20 August 2026."
            ),
            "American Heritage Center.",
        )

    def test_all_canonical_citations_keep_access_dates_structured(self) -> None:
        sources = json.loads(
            (PUBLIC / "sources.json").read_text(encoding="utf-8")
        )["records"]
        redundant = [
            source["id"]
            for source in sources
            if source.get("accessDate")
            and has_redundant_access_date(source.get("fullCitation"))
        ]
        self.assertEqual(redundant, [])


if __name__ == "__main__":
    unittest.main()
