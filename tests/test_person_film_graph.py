from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/public/v1"


def records(filename: str) -> dict[str, dict]:
    payload = json.loads((DATA / filename).read_text(encoding="utf-8"))
    return {record["id"]: record for record in payload["records"]}


class PersonFilmGraphTests(unittest.TestCase):
    def test_domgraf_fassbaender_acting_credit_is_fully_reciprocal(self) -> None:
        people = records("people.json")
        works = records("works.json")
        sources = records("sources.json")
        contributions = records("contributions.json")

        contribution_id = "CON-F022-A-P164"
        contribution = contributions[contribution_id]

        self.assertEqual(contribution["role"], "actor")
        self.assertEqual(contribution["workIds"], ["W-F022"])
        self.assertEqual(contribution["personIds"], ["P164"])
        self.assertEqual(
            contribution["sourceIds"], ["SRC0131", "SRC0690"]
        )
        self.assertIn(contribution_id, people["P164"]["contributionIds"])
        self.assertIn("W-F022", people["P164"]["workIds"])
        self.assertIn("SRC0131", people["P164"]["sourceIds"])
        self.assertIn(contribution_id, works["W-F022"]["contributionIds"])
        self.assertIn("P164", works["W-F022"]["personIds"])

        for source_id in contribution["sourceIds"]:
            with self.subTest(source_id=source_id):
                self.assertIn(
                    contribution_id, sources[source_id]["contributionIds"]
                )
                self.assertIn("P164", sources[source_id]["personIds"])


if __name__ == "__main__":
    unittest.main()
