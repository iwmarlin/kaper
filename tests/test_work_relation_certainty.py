"""A relation may not be confirmed by a note that says it is not."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def relations() -> list[dict]:
    path = ROOT / "data/public/v1/work-relations.json"
    return json.loads(path.read_text(encoding="utf-8"))["records"]


class WorkRelationCertaintyTests(unittest.TestCase):
    """Three associated_with_film relations stood as confirmed over notes ending
    "direct screen use ... is not established". The song reached the film
    through its German source song, and the version's own appearance on screen
    was the thing nobody had shown — which is the relation the record asserts.
    The archive already had the word for that: four other relations say
    probable, one of them over a note of exactly the same shape."""

    #: Phrases that withdraw the claim the relation is making.
    WITHDRAWN = re.compile(
        r"not established|no direct .{0,30}source|not been (?:located|shown|documented)|"
        r"cannot be (?:established|shown)|no evidence",
        re.I,
    )

    def test_a_note_that_withdraws_the_claim_is_not_confirmed(self) -> None:
        offenders = []
        checked = 0
        for relation in relations():
            note = relation.get("publicNote") or ""
            if not note:
                continue
            checked += 1
            if relation.get("certainty") == "confirmed" and self.WITHDRAWN.search(note):
                offenders.append(f"{relation['id']}: confirmed over {note[:60]!r}")
        self.assertGreater(checked, 50, "no relation notes were checked")
        self.assertEqual(offenders, [], "a relation is confirmed by a note that withdraws it")

    def test_the_graph_keeps_its_shape(self) -> None:
        # The certainty change must not have disturbed anything else.
        records = relations()
        self.assertTrue(all(r.get("sourceIds") for r in records),
                        "a relation lost its sources")
        self.assertTrue(all(r.get("sourceWorkIds") and r.get("targetWorkIds")
                            for r in records), "a relation lost an end")
        self.assertFalse([r["id"] for r in records
                          if set(r["sourceWorkIds"]) & set(r["targetWorkIds"])],
                         "a relation points at itself")


if __name__ == "__main__":
    unittest.main()
