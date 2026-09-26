import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "assets/site/styles.css"


def stylesheet():
    return CSS.read_text(encoding="utf-8")


class TypeScaleTests(unittest.TestCase):
    """The stylesheet had 153 font-size declarations in fifty different sizes,
    thirty-one of them between 0.58rem and 0.92rem — thirty-one steps inside a
    five-pixel band, which no one chose on purpose. It is what happens when each
    component is tuned by eye and nothing records the decision."""

    def test_every_font_size_comes_from_the_scale(self):
        # A raw rem value is how the drift got in: one component wants a hair
        # smaller than its neighbour, and a year later there are fifty sizes.
        # clamp() is exempt — those are deliberate responsive ranges, and the
        # twenty-five of them are a separate question from this one.
        css = stylesheet()
        offenders = []
        for match in re.finditer(r"font-size:\s*([^;]+);", css):
            value = match.group(1).strip()
            if value.startswith("var(--fs-") or value.startswith("clamp("):
                continue
            if value in ("inherit", "0", "100%"):
                continue
            # em is a different mechanism and is exempt on purpose. The two that
            # use it are the hero's route line, "Warsaw · Berlin · Paris · early
            # Hollywood", set as a proportion of the heading above it — and that
            # heading is a clamp(), so the line has to scale with its parent
            # rather than with the root. A rem step would break that tie.
            if value.endswith("em") and not value.endswith("rem"):
                continue
            line = css[: match.start()].count("\n") + 1
            offenders.append(f"line {line}: {value}")
        self.assertEqual(offenders, [], "a font size is set outside the scale")

    def test_the_scale_is_defined_once_and_is_ordered(self):
        css = stylesheet()
        steps = re.findall(r"--fs-(\d+):\s*([0-9.]+)rem", css)
        self.assertTrue(steps, "the scale is not defined")
        numbers = [int(n) for n, _ in steps]
        self.assertEqual(numbers, sorted(numbers), "the steps are out of order")
        self.assertEqual(numbers, list(range(1, len(numbers) + 1)), "the steps have gaps")
        sizes = [float(v) for _, v in steps]
        self.assertEqual(sizes, sorted(sizes), "a later step is smaller than an earlier one")
        self.assertEqual(len(sizes), len(set(sizes)), "two steps have the same size")

    def test_every_step_is_used(self):
        # A step nobody uses is a step that will collect strays.
        css = stylesheet()
        for name, _ in re.findall(r"--fs-(\d+):\s*([0-9.]+)rem", css):
            self.assertIn(
                f"var(--fs-{name})", css, f"--fs-{name} is defined but never used"
            )


class ItalicFaceCostTests(unittest.TestCase):
    """The archive owns two italic faces of 93KB and 42KB. Nothing renders in
    them for free: an italic word anywhere on a page fetches the whole face, as
    the front page did for two words and one record did for one sentence.

    This is a cost gate, not a ban. Italic remains available, and a page that
    genuinely needs it — a scholarly convention for foreign titles, say — is a
    decision worth making on purpose, by changing this test with it."""

    PAGES = ("index.html", "works.html", "people.html", "life.html",
             "sources.html", "media.html", "map.html", "record.html", "404.html")

    def test_no_page_marks_text_italic(self):
        for name in self.PAGES:
            with self.subTest(page=name):
                page = (ROOT / name).read_text(encoding="utf-8")
                self.assertNotIn("<em>", page)
                self.assertNotIn("<em ", page)
                self.assertNotIn("<i>", page)

    def test_no_rule_asks_for_an_italic_face(self):
        for path in sorted((ROOT / "assets/site").glob("*.css")):
            css = re.sub(r"@font-face\s*\{[^}]*\}", "", path.read_text(encoding="utf-8"))
            with self.subTest(stylesheet=path.name):
                self.assertNotIn("font-style: italic", css)

    def test_the_faces_stay_declared_for_the_day_one_is_needed(self):
        # Removing them would mean a browser synthesising a slope from the
        # upright, which is worse than the file it saves.
        css = stylesheet()
        self.assertIn("kaper-serif-italic.woff2", css)
        self.assertIn("kaper-sans-italic.woff2", css)



if __name__ == "__main__":
    unittest.main()
