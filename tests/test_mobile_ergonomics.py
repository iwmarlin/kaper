import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLES = ROOT / "assets/site/styles.css"
HOME = ROOT / "assets/site/home.css"


def rule_body(css: str, selector: str) -> str:
    """Return the declarations of the last rule written for this selector."""
    blocks = [
        match.group(1)
        for match in re.finditer(
            re.escape(selector) + r"\s*\{([^}]*)\}",
            css,
        )
    ]
    if not blocks:
        raise AssertionError(f"no rule for {selector}")
    return blocks[-1]


def declared_rem(body: str, property_name: str) -> float:
    match = re.search(property_name + r":\s*([0-9.]+)rem", body)
    if not match:
        raise AssertionError(f"{property_name} is not declared in rem: {body!r}")
    return float(match.group(1))


class FooterTargetTests(unittest.TestCase):
    """The six links in the footer are the only navigation on a phone once the
    page is scrolled, and they were the text alone: a 15px box with 6px to the
    next one. Measured at 375px, that is a 21px pitch — the 24px circles that
    WCAG 2.2's minimum target size asks for overlap, and a thumb aiming at Map
    can land on Media."""

    def test_the_footer_links_are_boxes_and_not_lines(self) -> None:
        body = rule_body(STYLES.read_text(encoding="utf-8"), ".site-footer .plain-list a")
        self.assertIn("display: block", body)
        # 0.4rem above and below a 21px line gives a 34px target at a 34px
        # pitch. Anything under 0.15rem drops the pitch back below 24px.
        self.assertGreaterEqual(declared_rem(body, "padding-block"), 0.3)


class HomeTypeFloorTests(unittest.TestCase):
    """The home page held the smallest visible type on the site: the link under
    the portrait at 9.6px, the pathway introduction and the hero buttons at
    11.7px, while the chronology reads at 14.4px and a record at 17.3px. The
    page a reader arrives on should not be the one they have to zoom."""

    #: Prose and controls, which a reader reads or presses. 0.72rem is the
    #: smallest ordinary step in the shared scale (--fs-2).
    PROSE_AND_CONTROLS = (
        ".home-page .hero__portrait figcaption",
        ".home-page .hero__actions .button",
        ".home-page .pathways-intro > p:not(.eyebrow)",
        ".home-page .pathway-row__description",
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.css = HOME.read_text(encoding="utf-8")

    def test_every_rule_for_prose_or_a_control_clears_the_floor(self) -> None:
        for selector in self.PROSE_AND_CONTROLS:
            for match in re.finditer(re.escape(selector) + r"\s*\{([^}]*)\}", self.css):
                body = match.group(1)
                if "font-size" not in body:
                    continue
                with self.subTest(selector=selector, line=self.css[: match.start()].count("\n") + 1):
                    self.assertGreaterEqual(declared_rem(body, "font-size"), 0.72)

    def test_no_rule_on_the_page_goes_below_the_label_size(self) -> None:
        # The eyebrows are set at 0.64rem, in family with the badges the rest
        # of the site sets at --fs-1. That is the floor for a tracked uppercase
        # label, and nothing on the page has any business below it.
        offenders = [
            (float(match.group(1)), self.css[: match.start()].count("\n") + 1)
            for match in re.finditer(r"font-size:\s*([0-9.]+)rem", self.css)
            if float(match.group(1)) < 0.64
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
