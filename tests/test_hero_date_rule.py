from __future__ import annotations

import datetime
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPAN_START = datetime.date(1902, 1, 1)
SPAN_END = datetime.date(1940, 1, 1)
RULE_WIDTH = 460


def published_events() -> list[dict]:
    return json.loads(
        (ROOT / "data/public/v1/timeline-events.json").read_text(encoding="utf-8")
    )["records"]


def event_date(event: dict) -> datetime.date:
    raw = str(event.get("sortDate") or event.get("dateStart") or "")[:10]
    parts = raw.split("-")
    return datetime.date(int(parts[0]), int(parts[1]) if len(parts) > 1 else 1,
                         int(parts[2]) if len(parts) > 2 else 1)


def expected_position(event: dict) -> float:
    share = (event_date(event) - SPAN_START).days / (SPAN_END - SPAN_START).days
    return round(min(max(share, 0.0), 1.0) * RULE_WIDTH, 1)


def printed_rule() -> str:
    page = (ROOT / "index.html").read_text(encoding="utf-8")
    match = re.search(
        r"<!-- home-prerender:dates:start -->(.*?)<!-- home-prerender:dates:end -->",
        page,
        re.S,
    )
    if not match:
        raise AssertionError("index.html carries no generated date rule")
    return match.group(1).strip()


def tick_positions(rule: str, opacity: str) -> list[float]:
    path = re.search(r'<path d="([^"]*)" stroke-opacity="' + opacity + r'"', rule)
    if not path:
        raise AssertionError(f"no tick path at opacity {opacity}")
    return [float(x) for x in re.findall(r"M([0-9.]+) [0-9.]+V", path.group(1))]


class DateRuleTests(unittest.TestCase):
    """The home page's ornament is the chronology: the span the archive states,
    1902 to 1939, ruled once, with a tick where each published event falls. It
    is generated at build time from the records the chronology itself draws,
    because an ornament copied by hand would keep saying what was true on the
    day it was drawn. It replaced a decorative circle that ran through the
    portrait and that grew from 40 to 63 per cent of a full circle between a
    1280px window and a 1920px one."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rule = printed_rule()
        cls.events = published_events()

    def test_there_is_one_tick_for_every_published_event(self) -> None:
        ordinary = tick_positions(self.rule, "0.38")
        milestones = tick_positions(self.rule, "0.52")
        self.assertEqual(len(ordinary) + len(milestones), len(self.events))
        # The two heights are the chronology's own editorial distinction, the
        # same field the timeline reads to choose its highlights view.
        self.assertEqual(
            len(milestones),
            sum(1 for event in self.events if event.get("displayMode") == "milestone"),
        )

    def test_every_tick_stands_where_its_event_does(self) -> None:
        printed = sorted(tick_positions(self.rule, "0.38") + tick_positions(self.rule, "0.52"))
        expected = sorted(expected_position(event) for event in self.events)
        self.assertEqual(printed, expected)

    def test_the_rule_is_the_span_the_archive_states(self) -> None:
        self.assertIn(f'viewBox="0 0 {RULE_WIDTH} 10"', self.rule)
        self.assertIn(f'<path d="M0 9.5H{RULE_WIDTH}"', self.rule)
        first, last = min(self.events, key=event_date), max(self.events, key=event_date)
        self.assertEqual(event_date(first).year, 1902)
        self.assertEqual(event_date(last).year, 1939)
        # Nothing is clipped: the first and last ticks fall inside the rule,
        # so the mark ends where the documentation ends rather than running
        # off the page as the circle did.
        self.assertGreater(expected_position(first), 0)
        self.assertLess(expected_position(last), RULE_WIDTH)

    def test_the_mark_is_decorative_and_takes_the_palette(self) -> None:
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        container = re.search(r'<div class="hero__span"[^>]*>', page).group(0)
        self.assertIn('aria-hidden="true"', container)
        self.assertIn('focusable="false"', self.rule)
        self.assertIn('aria-hidden="true"', self.rule)
        self.assertNotIn("183, 139, 69", self.rule)
        styles = (ROOT / "assets/site/styles.css").read_text(encoding="utf-8")
        span = styles.split(".hero__span {", 1)[1].split("}", 1)[0]
        self.assertIn("pointer-events: none", span)
        # The gold reaches 2.4:1 on paper: right for a hairline, wrong for
        # type, so it arrives as a stroke and the palette guard stays intact.
        stroke = styles.split(".hero__span-rule path {", 1)[1].split("}", 1)[0]
        self.assertIn("stroke: var(--gold)", stroke)
        self.assertNotIn("color: var(--gold)", span)

    def test_the_mark_is_drawn_only_where_there_is_room_for_it(self) -> None:
        # Below a two-column hero the copy takes the full width and the buttons
        # drop into the band the rule stands in; at 375px it was drawn across
        # the second button, three pixels tall.
        styles = (ROOT / "assets/site/styles.css").read_text(encoding="utf-8")
        guard = re.search(
            r"@media \(max-width: (\d+)px\) \{\s*\.hero__span \{\s*display: none;",
            styles,
        )
        self.assertIsNotNone(guard, "the rule is drawn at every width")
        self.assertGreaterEqual(int(guard.group(1)), 680)

    def test_the_circle_it_replaced_is_gone_from_both_stylesheets(self) -> None:
        for name in ("assets/site/styles.css", "assets/site/home.css"):
            self.assertNotIn("hero::after", (ROOT / name).read_text(encoding="utf-8"), name)

    def test_the_rule_is_generated_and_not_kept_by_hand(self) -> None:
        renderer = (ROOT / "scripts/render_catalogue_indexes.mjs").read_text(encoding="utf-8")
        self.assertIn("function homeDateRule(", renderer)
        self.assertIn("dates: homeDateRule(timelineEvents)", renderer)
        builder = (ROOT / "scripts/build_catalogue_indexes.py").read_text(encoding="utf-8")
        self.assertIn('"dates"', builder.split("HOME_SECTIONS =", 1)[1].split("\n", 1)[0])


if __name__ == "__main__":
    unittest.main()
