"""The timeline keeps its order in sortDate, and its claim in dateStart."""
from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def events() -> list[dict]:
    path = ROOT / "data/public/v1/timeline-events.json"
    return json.loads(path.read_text(encoding="utf-8"))["records"]


class TimelineDateEncodingTests(unittest.TestCase):
    """Three fields do three jobs. ``displayDate`` is what the reader is told,
    ``sortDate`` is where the entry sits on the rail, and ``dateStart`` is the
    date the record claims. A year-precision event has no day to claim, so its
    dateStart is the first of January — in eighteen of twenty-one records. The
    other three carried the first of July, which is the midpoint sortDate uses
    to place a bare year inside its own year. Ordering never depended on it:
    sortDate and sortOrder decide the rail, and sortOrder is distinct for every
    one of the fifty-six events."""

    def test_a_bare_year_starts_on_the_first_of_january(self) -> None:
        offenders = []
        checked = 0
        for event in events():
            if event.get("datePrecision") != "year":
                continue
            checked += 1
            if not str(event.get("dateStart", "")).endswith("-01-01"):
                offenders.append(f"{event['id']}: dateStart {event['dateStart']}")
        self.assertGreater(checked, 15, "no year-precision events were checked")
        self.assertEqual(offenders, [], "a bare year claims a day it does not have")

    def test_the_rail_is_ordered_without_reading_dateStart(self) -> None:
        # The guard above is only safe while this holds.
        records = events()
        self.assertEqual(len({event["sortOrder"] for event in records}), len(records),
                         "sortOrder no longer separates every event")

    def test_a_day_precision_event_names_a_day(self) -> None:
        offenders = [event["id"] for event in events()
                     if event.get("datePrecision") == "day"
                     and str(event.get("dateStart", "")).endswith("-01-01")]
        self.assertEqual(offenders, [], "a day-precision event sits on a year placeholder")


if __name__ == "__main__":
    unittest.main()
