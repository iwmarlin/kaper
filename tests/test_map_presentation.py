from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "map.html"
STYLES = ROOT / "assets/site/styles.css"
EXPLORER = ROOT / "assets/site/map-explorer-20260714.js"
PLACES = ROOT / "assets/site/map-places.js"


def rule_body(css: str, selector: str, *, within: str | None = None) -> str:
    text = css
    if within:
        start = css.index(within)
        depth = 0
        for index in range(start, len(css)):
            if css[index] == "{":
                depth += 1
            elif css[index] == "}":
                depth -= 1
                if depth == 0:
                    text = css[start:index]
                    break
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", text)
    if not match:
        raise AssertionError(f"no rule for {selector}")
    return match.group(1)


class ExplorerFitsTheScreenTests(unittest.TestCase):
    """The explorer is the page's instrument and had a fixed 44rem height, so
    on the screens most people use it opened under the fold: at 1366x768, 267
    of its 704px showed on arrival and the rest took a 436px scroll — while
    scrolling the page is also how one reaches the map to use it."""

    def test_the_explorer_is_bounded_by_the_window(self) -> None:
        body = rule_body(STYLES.read_text(encoding="utf-8"), ".map-explorer")
        self.assertRegex(body, r"height:\s*min\(44rem,\s*calc\(100svh\s*-\s*[\d.]+rem\)\)")

    def test_the_map_hero_takes_the_compact_measure(self) -> None:
        page = PAGE.read_text(encoding="utf-8")
        self.assertIn('class="page-hero page-hero--compact map-hero"', page)
        # Its own padding would win over the compact rule, being written later
        # in the same stylesheet. The narrow-screen rules are a separate matter
        # and keep theirs, so this looks only at the top-level declaration.
        self.assertNotIn("\n.map-hero {\n  padding:", STYLES.read_text(encoding="utf-8"))

    def test_the_phone_toolbar_keeps_its_two_controls_on_one_row(self) -> None:
        # Two full-width fields stacked made a 218px toolbar above a map that
        # already began 732px down the page.
        css = STYLES.read_text(encoding="utf-8")
        bodies = re.findall(r"\.map-toolbar__controls\s*\{([^}]*)\}", css)
        self.assertTrue(
            any("grid-template-columns: minmax(0, 1fr) auto" in body for body in bodies),
            bodies,
        )
        self.assertFalse(any("grid-template-columns: 1fr;" in body for body in bodies), bodies)


class ChoosingAPlaceIsAnsweredWhereTheReaderLooksTests(unittest.TestCase):
    """On a wide screen the place list sits below the details panel in the same
    column, so reaching any entry scrolls that panel off the top. Choosing a
    place then answered 193px above the window — name, precision, periods, note
    and the link to the record, all out of sight — on a map two thirds in view,
    with the chosen place 280px below its centre. Clicking appeared to do
    nothing."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = EXPLORER.read_text(encoding="utf-8")
        cls.reveal = cls.script.split("function revealMap()", 1)[1].split("\n  }", 1)[0]
        cls.centre = cls.script.split("function centreOnMarker(marker)", 1)[1].split("\n}", 1)[0]

    def test_the_whole_explorer_is_brought_back_on_a_wide_screen(self) -> None:
        self.assertIn('document.querySelector(".map-explorer")', self.reveal)
        # A phone keeps the canvas, which is what sits above its list.
        self.assertIn('document.querySelector(".map-canvas")', self.reveal)
        self.assertIn("compactMapLayout?.matches", self.reveal)

    def test_a_view_that_is_already_whole_is_left_alone(self) -> None:
        self.assertIn("alreadyInView", self.reveal)
        self.assertIn("if (alreadyInView) return;", self.reveal)

    def test_the_chosen_place_is_centred_where_the_card_does_not_cover_it(self) -> None:
        self.assertIn("map.panTo(marker.getLatLng()", self.centre)
        self.assertIn("compactMapLayout?.matches) return;", self.centre)
        # Both ways of revealing a marker end in the same place.
        self.assertEqual(self.script.count("centreOnMarker(marker);"), 2)


class ClusterNameTests(unittest.TestCase):
    """Every place marker carries its own name. A cluster carried a numeral,
    and the plugin makes its shell role="button" and tabbable, so a screen
    reader announced "12, button"."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = EXPLORER.read_text(encoding="utf-8")

    def test_the_shell_is_named_and_the_numeral_is_not_read_twice(self) -> None:
        self.assertIn("function nameClusters()", self.script)
        self.assertIn('shell.setAttribute("aria-label"', self.script)
        self.assertIn('<span class="map-cluster" aria-hidden="true">', self.script)

    def test_the_names_are_renewed_whenever_the_shells_are(self) -> None:
        # The plugin rebuilds cluster shells on every move and on every redraw,
        # and builds them a frame after the layer is added.
        self.assertIn('for (const event of ["zoomend", "moveend"]) map.on(event, nameClusters);', self.script)
        self.assertIn("requestAnimationFrame(nameClusters)", self.script)
        # The layer has to exist before anything is bound to it.
        self.assertLess(
            self.script.index("markerLayer = window.L.markerClusterGroup"),
            self.script.index('markerLayer.on?.("animationend"'),
        )


class HistoricalPlateTests(unittest.TestCase):
    """The 1926 sheet is 2200px and was sent whole to every device: 633KB of it
    to a 353px phone canvas, on a site that puts every other image through a
    derivative pipeline."""

    def test_the_plate_is_built_like_every_other_image(self) -> None:
        # It always was: a media record holds it, so the derivative pipeline
        # has been making its sizes all along. Only the map ignored them.
        builder = (ROOT / "scripts/build_site_assets.py").read_text(encoding="utf-8")
        self.assertIn("MAP_PLATE_PATH = ", builder)
        self.assertIn("def write_map_plate_module(", builder)
        media = json.loads((ROOT / "data/public/v1/media.json").read_text(encoding="utf-8"))["records"]
        self.assertTrue(any("world-1926" in str(record.get("assetPath", "")) for record in media))

    def test_the_page_carries_only_that_image_s_sizes(self) -> None:
        module = (ROOT / "assets/site/map-plate.js").read_text(encoding="utf-8")
        variants = json.loads(re.search(r"Object\.freeze\((\[.*\])\);", module).group(1))
        self.assertGreaterEqual(len(variants), 3)
        self.assertTrue(all("world-1926" in variant["path"] for variant in variants))
        script = EXPLORER.read_text(encoding="utf-8")
        self.assertIn("HISTORICAL_PLATE_VARIANTS", script)
        # Importing the whole mapping for one image cost the map page 143KB of
        # every other image in the archive.
        self.assertNotIn("image-derivatives.js", script)

    def test_the_plate_is_chosen_for_the_canvas_it_is_drawn_on(self) -> None:
        script = EXPLORER.read_text(encoding="utf-8")
        chooser = script.split("function historicalPlateUrl", 1)[1].split("\n}", 1)[0]
        self.assertIn("devicePixelRatio", chooser)
        self.assertIn("clientWidth", chooser)


class EvidenceWordingTests(unittest.TestCase):
    """Forty-four of the forty-five places carry dated events. The forty-fifth
    is on the map because a song of Kaper's was sung there, which three sources
    attest and no timeline event records."""

    def test_a_place_without_events_states_what_it_has(self) -> None:
        places = PLACES.read_text(encoding="utf-8")
        self.assertIn("export function evidenceSummary(place)", places)
        self.assertIn("linked ${sources === 1 ? \"source\" : \"sources\"}", places)
        explorer = EXPLORER.read_text(encoding="utf-8")
        self.assertIn("evidenceSummary(place)", explorer)
        for text in (places, explorer):
            self.assertNotIn("${linkedEvents} linked ${linkedEvents === 1", text)

    def test_the_map_data_still_holds_one_such_place(self) -> None:
        records = json.loads((ROOT / "data/public/v1/places.json").read_text(encoding="utf-8"))["records"]
        without = [place for place in records if not place.get("timelineEventIds")]
        self.assertTrue(all(place.get("sourceIds") for place in without))

    def test_the_scope_note_covers_what_is_on_the_map(self) -> None:
        page = PAGE.read_text(encoding="utf-8")
        note = re.search(r'<div class="scope-note">(.*?)</div>', page, re.S).group(1)
        self.assertIn("dated event", note)
        self.assertIn("work documented", note)

    def test_the_method_note_is_read_in_parts(self) -> None:
        page = PAGE.read_text(encoding="utf-8")
        block = re.search(r'<div class="map-method-note">(.*?)</div>', page, re.S).group(1)
        self.assertEqual(block.count("<p>"), 3)
        longest = max(len(paragraph) for paragraph in re.findall(r"<p>(.*?)</p>", block, re.S))
        self.assertLess(longest, 420)


if __name__ == "__main__":
    unittest.main()
