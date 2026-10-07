import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
RENDERER = ROOT / "assets/site/record-detail-20260714.js"

# `composer` is the plain reading of a music credit on a film. It is left
# unstated on purpose, the way an authorized name is left unstated where it
# matches the title the card carries.
PLAIN_CREDIT = "composer"


def read_records(name):
    return json.loads((PUBLIC / name).read_text(encoding="utf-8"))["records"]


def escape_html(value):
    """Mirror escapeHtml in core.js, which renders the static pages via Node."""
    for needle, replacement in (
        ("&", "&amp;"),
        ("<", "&lt;"),
        (">", "&gt;"),
        ('"', "&quot;"),
        ("'", "&#039;"),
    ):
        value = value.replace(needle, replacement)
    return value


def credit_labels():
    """Read the vocabulary from the renderer, so there is one source of truth."""
    source = RENDERER.read_text(encoding="utf-8")
    block = re.search(
        r"const FILM_CREDIT_LABELS = Object\.freeze\(\{(.*?)\}\);", source, re.S
    )
    assert block, "FILM_CREDIT_LABELS is not in the renderer"
    return dict(re.findall(r"(\w+):\s*\"([^\"]+)\"", block.group(1)))


class FilmCreditAttributionTests(unittest.TestCase):
    """`films.creditType` and `films.attributionNote` were read by no code at
    all, so the qualification that separates a song credit from a score credit
    was recorded and never published. docs/site-architecture.md requires that
    attribution qualifications be displayed rather than hidden."""

    @classmethod
    def setUpClass(cls):
        cls.labels = credit_labels()
        cls.films = read_records("films.json")
        cls.pages = {}
        for film in cls.films:
            for work_id in film.get("workIds") or []:
                page = ROOT / "records/work" / work_id / "index.html"
                if page.is_file():
                    cls.pages[work_id] = page.read_text(encoding="utf-8")

    def films_with_pages(self):
        for film in self.films:
            for work_id in film.get("workIds") or []:
                if work_id in self.pages:
                    yield work_id, film, self.pages[work_id]

    def test_the_vocabulary_covers_every_value_but_the_plain_one(self):
        # A credit type added to the data without a label would be dropped
        # silently, which is how this field came to be invisible in the first
        # place.
        for film in self.films:
            credit = film.get("creditType")
            if not credit or credit == PLAIN_CREDIT:
                continue
            self.assertIn(
                credit,
                self.labels,
                f"{film.get('id')} carries creditType {credit!r} with no display label",
            )

    def test_a_qualified_credit_is_stated_on_the_card(self):
        stated = 0
        for work_id, film, text in self.films_with_pages():
            label = self.labels.get(film.get("creditType"))
            if not label:
                continue
            self.assertIn(
                "<dt>Kaper attribution</dt>",
                text,
                f"{work_id} qualifies its credit as {label!r} and does not say so",
            )
            self.assertIn(f"<dd>{label}</dd>", text, work_id)
            stated += 1
        self.assertGreaterEqual(stated, 25, "the qualified credits must be stated")

    def test_a_plain_composer_credit_says_nothing(self):
        for work_id, film, text in self.films_with_pages():
            if film.get("creditType") != PLAIN_CREDIT:
                continue
            self.assertNotIn(
                "<dt>Kaper attribution</dt>",
                text,
                f"{work_id} states the plain reading as though it qualified something",
            )

    def test_the_attribution_note_reaches_the_page(self):
        shown = 0
        for work_id, film, text in self.films_with_pages():
            note = film.get("attributionNote")
            if not note:
                continue
            self.assertIn(
                escape_html(note),
                text,
                f"{work_id} holds an attribution note the card does not show",
            )
            shown += 1
        self.assertGreaterEqual(shown, 30, "the attribution notes must reach the page")

    def test_the_films_the_gap_was_found_on(self):
        # Mutiny on the Bounty read as a confirmed composer credit; Kaper wrote
        # one song for it. A Night at the Opera names the film's actual
        # composer, and that name appeared in no rendered page.
        bounty = self.pages["W-F034"]
        self.assertIn("<dd>Songwriter</dd>", bounty)
        self.assertIn("Love Song of Tahiti", bounty)
        opera = self.pages["W-F036"]
        self.assertIn("<dd>Songwriter</dd>", opera)
        self.assertIn("score by Herbert Stothart", opera)
        # Reused music is the strongest qualification of the three.
        self.assertIn("<dd>Stock music</dd>", self.pages["W-F049"])


if __name__ == "__main__":
    unittest.main()
