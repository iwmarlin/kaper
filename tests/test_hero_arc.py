from __future__ import annotations

import math
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLES = ROOT / "assets/site/styles.css"


def rule_body(css: str, selector: str) -> str:
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    if not match:
        raise AssertionError(f"no rule for {selector}")
    return match.group(1)


def percent(body: str, prop: str) -> float:
    match = re.search(r"(?<![-\w])" + re.escape(prop) + r":\s*(-?[0-9.]+)%", body)
    if not match:
        raise AssertionError(f"{prop} is not declared as a percentage: {body!r}")
    return float(match.group(1))


class HeroArcTests(unittest.TestCase):
    """The hero's ornament is an arc, as it was, but struck rather than cut.
    The old one was a full circle that the section's overflow happened to
    slice, so the page chose where it ended: at 700px sixty-nine per cent of
    the drawn arc lay behind the portrait, and the visible share of the circle
    grew from 40 per cent at 1280px to 63 at 1920. This one is a path with its
    own two ends, struck inside the portrait's frame and centred on the
    picture."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.css = STYLES.read_text(encoding="utf-8")
        cls.home = (ROOT / "assets/site/home.css").read_text(encoding="utf-8")
        cls.svg = re.search(r'<svg class="hero__arc".*?</svg>', cls.page, re.S).group(0)
        cls.box = rule_body(cls.css, ".hero__arc")

    def test_the_arc_is_drawn_and_not_a_clipped_circle(self) -> None:
        # A border-radius circle has no ends of its own, so the section's
        # overflow decided where the ornament stopped. A path has two.
        self.assertIn("<path", self.svg)
        self.assertNotIn("border-radius", self.box)
        self.assertIn('vector-effect="non-scaling-stroke"', self.svg)
        self.assertRegex(self.svg, r'd="M[\d.]+ [\d.]+A100 100 0 0 1 [\d.]+ [\d.]+"')

    def test_the_arc_is_concentric_with_the_frame_at_any_width(self) -> None:
        """Margin percentages resolve against the containing block's width on
        both axes, so a frame-relative arc keeps its centre as the column
        narrows. Fixed rem lengths did not: below about 1150px the frame stops
        reaching 18.5rem, and the arc drifted off centre and crossed the lead
        at 1024px."""
        self.assertIn("position: absolute", self.box)
        self.assertEqual(percent(self.box, "width"), 180)
        self.assertEqual(percent(self.box, "left"), 50)
        self.assertEqual(percent(self.box, "margin-left"), -90)
        self.assertEqual(percent(self.box, "margin-top"), -40)
        self.assertIn("aspect-ratio: 1", self.box)

    def test_the_radius_beats_the_frame_so_they_never_meet(self) -> None:
        # Radius is 0.9 of the frame's width. The frame measures 296 x 361 at
        # its full size and stays about that proportion as it shrinks, so its
        # half-diagonal in units of its own width is what the radius must beat.
        radius = percent(self.box, "width") / 200
        half_diagonal = math.hypot(0.5, (361 / 296) / 2)
        self.assertGreater(radius, half_diagonal)

    def test_the_frame_no_longer_clips_what_is_struck_inside_it(self) -> None:
        # Safe because the picture is inset by the frame's padding and carries
        # its own radius; the clip was keeping corners nothing reached.
        self.assertIn("overflow: visible", rule_body(self.home, ".home-page .hero__portrait"))
        self.assertIn("border-radius", rule_body(self.home, ".home-page .hero__portrait img"))
        after_figure = self.page.split('class="hero__portrait"', 1)[1][:400]
        self.assertIn('class="hero__arc"', after_figure)

    def test_nothing_here_is_measured_against_the_window(self) -> None:
        # The old circle took its offset from the viewport, which is why the
        # share of it on screen grew from 40 per cent at 1280px to 63 at 1920.
        self.assertNotIn("vw", self.box)
        self.assertNotIn("vh", self.box)

    def test_it_is_decorative_and_takes_the_palette(self) -> None:
        self.assertIn('aria-hidden="true"', self.svg)
        self.assertIn('focusable="false"', self.svg)
        self.assertIn("pointer-events: none", self.box)
        self.assertNotIn("183, 139, 69", self.svg)
        self.assertIn("stroke: var(--gold)", rule_body(self.css, ".hero__arc path"))

    def test_it_is_not_drawn_where_there_is_no_room(self) -> None:
        guard = re.search(
            r"@media \(max-width: (\d+)px\) \{\s*\.hero__arc \{\s*display: none;",
            self.css,
        )
        self.assertIsNotNone(guard, "the arc is drawn at every width")
        self.assertGreaterEqual(int(guard.group(1)), 680)

    def test_the_circle_it_replaced_left_nothing_behind(self) -> None:
        for name in ("assets/site/styles.css", "assets/site/home.css"):
            self.assertNotIn("hero::after", (ROOT / name).read_text(encoding="utf-8"), name)


if __name__ == "__main__":
    unittest.main()
