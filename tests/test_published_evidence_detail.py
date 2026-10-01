import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
RENDERER = ROOT / "assets/site/record-detail-20260714.js"

# A record identifier is how the archive addresses itself. It means nothing to
# a reader, so it must not reach a field the card prints.
RECORD_ID = re.compile(r"\b(SRC\d{4}|W-[A-Z]\d+|CON-[A-Z0-9-]+|ORG\d{3}|P\d{3}|S\d{3}|F\d{3})\b")


def read_records(name):
    return json.loads((PUBLIC / name).read_text(encoding="utf-8"))["records"]


def escape_html(value):
    for needle, replacement in (
        ("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ('"', "&quot;"), ("'", "&#039;"),
    ):
        value = value.replace(needle, replacement)
    return value


class EvidenceLocatorTests(unittest.TestCase):
    """`evidenceLocator` says where in a cited document a credit is attested —
    the most precise citation data the archive holds. It was exported and never
    shown."""

    @classmethod
    def setUpClass(cls):
        cls.contributions = read_records("contributions.json")
        cls.works = {item["id"]: item for item in read_records("works.json")}

    # The work card shows authorship credits, not recording ones:
    # workLevelContributions drops these three roles. Four locators sit on
    # performer credits of W-O011 and are therefore not on any page — the whole
    # credit is withheld, not just its locator, which is a separate decision.
    RECORDING_ROLES = {"performer", "conductor", "record_label"}

    def carried(self, displayed_only=True):
        return [
            (item, work_id)
            for item in self.contributions
            if (item.get("evidenceLocator") or "").strip()
            and not (displayed_only and item.get("role") in self.RECORDING_ROLES)
            for work_id in item.get("workIds") or []
        ]

    def test_the_locator_is_prose_and_names_no_record(self):
        for item, _ in self.carried(displayed_only=False):
            self.assertIsNone(
                RECORD_ID.search(item["evidenceLocator"]),
                f"{item['id']} names a record by id in a field the card prints:"
                f" {item['evidenceLocator']!r}",
            )

    def test_every_locator_reaches_its_page(self):
        shown = 0
        for item, work_id in self.carried():
            page = ROOT / "records/work" / work_id / "index.html"
            if not page.is_file():
                continue
            self.assertIn(
                escape_html(item["evidenceLocator"]),
                page.read_text(encoding="utf-8"),
                f"{work_id} does not show the locator of {item['id']}",
            )
            shown += 1
        self.assertGreaterEqual(shown, 30, "the locators must reach the pages")

    def test_the_withheld_locators_are_only_the_recording_credits(self):
        # If this count moves, a locator has been added to a role the card does
        # not show, and it will be published nowhere.
        withheld = {
            item["id"]
            for item in self.contributions
            if (item.get("evidenceLocator") or "").strip()
            and item.get("role") in self.RECORDING_ROLES
        }
        self.assertEqual(
            withheld,
            {
                "CON-O011-P-P009",
                "CON-O011-P-P088",
                "CON-O011-P-P089",
                "CON-O011-P-P090",
            },
        )


class SongUseTests(unittest.TestCase):
    """A song written for a film and left out of it is a fact about the work."""

    @classmethod
    def setUpClass(cls):
        cls.songs = read_records("songs.json")
        cls.labels = dict(
            re.findall(
                r"(\w+):\s*\"([^\"]+)\"",
                re.search(
                    r"const SONG_USE_LABELS = Object\.freeze\(\{(.*?)\}\);",
                    RENDERER.read_text(encoding="utf-8"),
                    re.S,
                ).group(1),
            )
        )

    def test_the_vocabulary_covers_every_value(self):
        for song in self.songs:
            value = song.get("useStatus")
            if value:
                self.assertIn(value, self.labels, song["id"])

    def test_every_marked_song_says_so_on_its_card(self):
        marked = 0
        for song in self.songs:
            label = self.labels.get(song.get("useStatus"))
            if not label:
                continue
            for work_id in song.get("workIds") or []:
                page = ROOT / "records/work" / work_id / "index.html"
                if not page.is_file():
                    continue
                text = page.read_text(encoding="utf-8")
                self.assertIn("<dt>Film use</dt>", text, work_id)
                self.assertIn(f"<dd>{label}</dd>", text, work_id)
                marked += 1
        self.assertGreaterEqual(marked, 6, "the unused cues must be stated")

    def test_a_song_without_the_field_says_nothing(self):
        for song in self.songs:
            if song.get("useStatus"):
                continue
            for work_id in song.get("workIds") or []:
                page = ROOT / "records/work" / work_id / "index.html"
                if page.is_file():
                    self.assertNotIn("<dt>Film use</dt>", page.read_text(encoding="utf-8"), work_id)


if __name__ == "__main__":
    unittest.main()
