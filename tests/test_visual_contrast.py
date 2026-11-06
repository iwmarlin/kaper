import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLES = ROOT / "assets/site/styles.css"

# "border-color" and "text-decoration-color" also end in "color"; only the
# property that sets type is in question here.
TEXT_COLOUR = re.compile(r"(?<![-\w])color:\s*var\((--[\w-]+)\)")
BACKGROUNDS = ("--paper", "--surface")


def relative_luminance(value):
    value = value.lstrip("#")
    channels = [int(value[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(foreground, background):
    a, b = relative_luminance(foreground), relative_luminance(background)
    high, low = max(a, b), min(a, b)
    return (high + 0.05) / (low + 0.05)


def palette(css):
    return dict(re.findall(r"(--[\w-]+):\s*(#[0-9a-fA-F]{6})", css))


def rules(css):
    # Comments are removed first so that a comment above a rule is not read as
    # part of its selector; the whole selector group is kept, because a rule
    # that styles the marker and its legend swatch together names both.
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selector = " ".join(match.group(1).split())
        yield selector, match.group(2)


class PaletteContrastTests(unittest.TestCase):
    """The archive is read, not glanced at, and its smallest type carries the
    apparatus. Two palette entries do not reach the contrast a reader needs, and
    both were being used to set type."""

    def test_the_line_and_swatch_colours_never_set_type(self):
        css = STYLES.read_text(encoding="utf-8")
        colours = palette(css)
        for name in ("--line-dark", "--gold"):
            self.assertLess(
                contrast(colours[name], colours["--paper"]),
                4.5,
                f"{name} now passes on paper; this guard can be relaxed",
            )
        offenders = [
            selector
            for selector, body in rules(css)
            for match in TEXT_COLOUR.finditer(body)
            if match.group(1) in ("--line-dark", "--gold")
        ]
        self.assertEqual(
            offenders,
            [],
            "a rule or swatch colour is being used as a text colour",
        )

    def test_the_colours_that_do_set_type_carry_enough_contrast(self):
        css = STYLES.read_text(encoding="utf-8")
        colours = palette(css)
        for name in ("--ink", "--ink-soft", "--accent", "--accent-dark", "--blue", "--green", "--warning", "--gold-deep"):
            self.assertIn(name, colours, f"{name} is missing from the palette")
            for background in BACKGROUNDS:
                self.assertGreaterEqual(
                    round(contrast(colours[name], colours[background]), 2),
                    4.5,
                    f"{name} on {background} falls below the readable minimum",
                )


class MapPeriodChannelTests(unittest.TestCase):
    """Precision is drawn in the marker's outline; the period had colour and
    nothing else, and terracotta against green is the pair that closes up under
    the commonest form of colour blindness."""

    def test_each_period_is_drawn_with_a_second_channel(self):
        css = STYLES.read_text(encoding="utf-8")
        european = next(body for selector, body in rules(css) if selector.endswith(".map-place-marker--european"))
        hollywood = next(body for selector, body in rules(css) if selector.endswith(".map-place-marker--hollywood"))
        self.assertIn("radial-gradient", european)
        self.assertIn("linear-gradient", hollywood)
        # Percentages, so the figure holds at every marker size.
        self.assertNotRegex(european + hollywood, r"\d+px")

    def test_the_legend_carries_the_same_fills(self):
        css = STYLES.read_text(encoding="utf-8")
        for period in ("european", "hollywood"):
            selectors = [
                selector
                for selector, body in rules(css)
                if f".map-place-marker--{period}" in selector and "gradient" in body
            ]
            self.assertTrue(
                any(f".map-legend__swatch--{period}" in selector for selector in selectors),
                f"the legend does not show the {period} fill it is meant to explain",
            )


if __name__ == "__main__":
    unittest.main()
