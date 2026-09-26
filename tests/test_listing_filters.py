from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Works, People, Media and Sources each list a collection and each carries more controls
# than fit a narrow screen. They share one pattern: the search field stays in
# reach, the facets fold behind a labelled toggle, and the choices in force are
# shown as chips that remove themselves.
LISTINGS = {
    "works.html": ("work", "assets/site/works.js"),
    "people.html": ("person", "assets/site/people.js"),
    "media.html": ("media", "assets/site/gallery.js"),
    "sources.html": ("source", "assets/site/sources.js"),
}


class ListingFilterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pages = {name: (ROOT / name).read_text(encoding="utf-8") for name in LISTINGS}
        cls.scripts = {
            name: (ROOT / script).read_text(encoding="utf-8")
            for name, (_, script) in LISTINGS.items()
        }
        cls.shared = (ROOT / "assets/site/catalogue-filters.js").read_text(encoding="utf-8")

    def test_each_listing_uses_the_shared_filter_shell(self) -> None:
        for name, text in self.pages.items():
            with self.subTest(page=name):
                self.assertIn('class="filters filters--catalogue"', text)
                self.assertIn("filters__shell", text)
                self.assertIn("filters__search", text)

    def test_each_listing_can_fold_its_facets(self) -> None:
        for name, (prefix, _) in LISTINGS.items():
            text = self.pages[name]
            with self.subTest(page=name):
                self.assertIn(f'id="{prefix}-filter-toggle"', text)
                self.assertIn(f'id="{prefix}-filter-options"', text)
                self.assertIn(f'aria-controls="{prefix}-filter-options"', text)
                self.assertIn(f'id="{prefix}-active-filters"', text)

    def test_the_reset_button_starts_hidden(self) -> None:
        for name, text in self.pages.items():
            with self.subTest(page=name):
                match = re.search(r'<button[^>]*id="[a-z-]*reset[a-z-]*"[^>]*>', text)
                self.assertIsNotNone(match, "the listing has no reset control")
                self.assertIn("hidden", match.group(0))

    def test_the_search_field_is_the_first_control(self) -> None:
        for name, text in self.pages.items():
            with self.subTest(page=name):
                shell = re.search(r'filters__shell.*?</section>', text, re.S).group(0)
                self.assertLess(shell.index("filters__search"), shell.index("filters__toggle"))

    def test_listing_behaviour_is_owned_by_one_shared_component(self) -> None:
        for name, source in self.scripts.items():
            with self.subTest(page=name):
                self.assertIn("createCatalogueFilters", source)
                self.assertNotIn("function syncQuery", source)
                self.assertNotIn('filterToggle.addEventListener("click"', source)

    def test_shared_component_has_the_accessibility_and_url_contract(self) -> None:
        self.assertIn('event.key !== "Escape"', self.shared)
        self.assertIn('close({ returnFocus: true })', self.shared)
        self.assertIn('window.addEventListener("popstate"', self.shared)
        self.assertIn("window.history.replaceState", self.shared)
        self.assertIn("url.searchParams.delete", self.shared)
        self.assertIn("fieldValue(field) !== requestedValue", self.shared)
        self.assertIn('"(max-width: 900px)"', self.shared)

    def test_timeline_and_map_share_the_same_query_state_layer(self) -> None:
        for script in ("timeline-20260714.js", "map-explorer-20260714.js"):
            source = (ROOT / "assets/site" / script).read_text(encoding="utf-8")
            with self.subTest(script=script):
                self.assertIn("createQueryState", source)
                self.assertNotIn("new URLSearchParams", source)


class WorksYearFacetTests(unittest.TestCase):
    """A reader looking for 1933 had to type it into the search box, which also
    matched the word elsewhere in a record. The catalogue now filters by the
    year it already prints beside every row, and the choice survives in the URL,
    so "works.html?year=1933" is an address a footnote can carry."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (ROOT / "works.html").read_text(encoding="utf-8")
        cls.script = (ROOT / "assets/site/works.js").read_text(encoding="utf-8")

    def test_the_control_sits_in_the_shared_facet_panel(self) -> None:
        panel = re.search(
            r'id="work-filter-options".*?</div>\s*<div class="active-filters"',
            self.page,
            re.S,
        ).group(0)
        self.assertIn('<label for="work-year">Year</label>', panel)
        self.assertIn('<select id="work-year"><option value="">All years</option></select>', panel)

    def test_the_facet_is_registered_like_every_other(self) -> None:
        # Registration is what gives it a chip, the filter count, the reset
        # button and its key in the query string; the shared controller does
        # the rest.
        self.assertIn('year: document.querySelector("#work-year")', self.script)
        self.assertIn('{ key: "year", label: "Year", defaultValue: "" }', self.script)
        self.assertIn("controls.year", self.script)
        self.assertIn('controls.year.value = ""', self.script)

    def test_the_years_offered_are_the_years_documented(self) -> None:
        # The options are built from the records, so a year nothing was
        # documented in cannot be offered: 1924 has no works and must not be a
        # choice that returns an empty list.
        works = json.loads(
            (ROOT / "data/public/v1/works.json").read_text(encoding="utf-8")
        )["records"]
        years = {str(work["year"])[:4] for work in works if work.get("year")}
        self.assertNotIn("1924", years)
        self.assertIn("1933", years)
        self.assertIn("addOptions(\n    controls.year,", self.script)


class ResetControlTests(unittest.TestCase):
    """Four listings hide their reset until a filter is in force. The timeline
    showed one on every visit with nothing to reset, and the map — which also
    carries its search and its chosen place in the address — had none at all."""

    def test_every_page_that_filters_offers_a_reset(self) -> None:
        for name, control in (
            ("works.html", "reset-filters"),
            ("people.html", "reset-filters"),
            ("media.html", "media-reset"),
            ("sources.html", "source-reset"),
            ("life.html", "timeline-reset"),
            ("map.html", "map-reset"),
        ):
            page = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(page=name):
                match = re.search(rf'<button[^>]*id="{control}"[^>]*>', page)
                self.assertIsNotNone(match, "the page has no reset control")
                self.assertIn("button--ghost", match.group(0))
                self.assertIn("hidden", match.group(0))

    def test_the_timeline_and_the_map_reveal_it_the_same_way(self) -> None:
        timeline = (ROOT / "assets/site/timeline-20260714.js").read_text(encoding="utf-8")
        self.assertIn("resetButton.hidden = !controls.search.value.trim()", timeline)
        map_script = (ROOT / "assets/site/map-explorer-20260714.js").read_text(encoding="utf-8")
        self.assertIn("resetButton.hidden = !search.value.trim() && !selectedId", map_script)
        self.assertIn("resetSelection();", map_script)


class TimelinePeriodFacetTests(unittest.TestCase):
    """The chronology is organised by era: it opens with an era strip, breaks
    into three chapters and prints a period badge on every entry. Until now the
    strip only jumped, and the page could not be narrowed to one era — the one
    index on the site without the period facet that works, media and people all
    have. "life.html?period=hollywood" is now an address a footnote can carry."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (ROOT / "life.html").read_text(encoding="utf-8")
        cls.script = (ROOT / "assets/site/timeline-20260714.js").read_text(encoding="utf-8")
        cls.shared = (ROOT / "assets/site/catalogue-filters.js").read_text(encoding="utf-8")

    def test_the_control_sits_beside_the_other_two(self) -> None:
        grid = re.search(
            r'filters__grid--timeline.*?</section>', self.page, re.S
        ).group(0)
        self.assertIn('<label for="timeline-period">Period</label>', grid)
        self.assertIn(
            '<select id="timeline-period"><option value="">All periods</option></select>',
            grid,
        )

    def test_the_facet_filters_and_survives_in_the_url(self) -> None:
        self.assertIn('period: document.querySelector("#timeline-period")', self.script)
        self.assertIn("matchesPeriod(event, controls.period.value)", self.script)
        self.assertIn(
            'defaults: { search: "", category: "", period: "", view: "highlights" }',
            self.script,
        )
        # Without this the return link from an event record would call a
        # period-filtered chronology unfiltered.
        self.assertIn('filterKeys: ["search", "category", "period"]', self.shared)

    def test_the_eras_offered_are_the_eras_documented(self) -> None:
        events = json.loads(
            (ROOT / "data/public/v1/timeline-events.json").read_text(encoding="utf-8")
        )["records"]
        documented = {period for event in events for period in event.get("periods", [])}
        self.assertEqual(documented, {"warsaw", "european", "hollywood"})
        self.assertIn("addOptions(\n    controls.period,", self.script)

    def test_the_panel_declares_room_for_three_controls(self) -> None:
        styles = (ROOT / "assets/site/styles.css").read_text(encoding="utf-8")
        rule = styles.split(".filters__grid--timeline {", 1)[1].split("}", 1)[0]
        columns = re.search(r"grid-template-columns:([^;]+);", rule).group(1)
        self.assertEqual(columns.count("minmax("), 3)


class FacetPanelTrackTests(unittest.TestCase):
    """Each panel declares its own columns in one place, and a facet added
    without touching that rule makes every control narrower. Two ways out are
    legitimate: as many tracks as there are fields, or a track that wraps. What
    is not legitimate is a fixed row too short for what it holds — that silently
    cut "Hollywood · 1935–1939" on three pages."""

    def test_each_panel_declares_a_row_that_holds_its_fields(self) -> None:
        css = (ROOT / "assets/site/styles.css").read_text(encoding="utf-8")
        for page, key in (
            ("works.html", "works"),
            ("people.html", "people"),
            ("media.html", "media"),
            ("sources.html", "sources"),
        ):
            with self.subTest(page=page):
                text = (ROOT / page).read_text(encoding="utf-8")
                panel = re.search(
                    r'id="[a-z]+-filter-options".*?</div>\s*<div class="active-filters"',
                    text,
                    re.S,
                ).group(0)
                fields = len(re.findall(r'<div class="field">', panel))
                rule = re.search(
                    rf"\.filters__advanced--{key}\s*\{{[^}}]*grid-template-columns:\s*([^;]+);",
                    css,
                ).group(1).strip()
                if "auto-fit" in rule or "auto-fill" in rule:
                    continue  # the fields wrap; the row cannot be too short
                repeated = re.match(r"repeat\((\d+),", rule)
                tracks = int(repeated.group(1)) if repeated else len(rule.split())
                self.assertEqual(tracks, fields, f"{key}: {rule!r}")


if __name__ == "__main__":
    unittest.main()
