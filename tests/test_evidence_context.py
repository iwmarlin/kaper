import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"


def read_records(name):
    return json.loads((PUBLIC / name).read_text(encoding="utf-8"))["records"]


class EvidenceContextIsInternalTests(unittest.TestCase):
    """`evidenceContext` holds snake_case tokens for the archive's own use. It
    has no display vocabulary of the kind SOURCE_TYPES gives every field a
    reader sees, so it does not belong on a page as it stands."""

    @classmethod
    def setUpClass(cls):
        cls.contributions = read_records("contributions.json")
        cls.pages = {
            path.parent.name: path.read_text(encoding="utf-8")
            for path in (ROOT / "records/work").glob("*/index.html")
        }

    def test_no_internal_token_is_printed_to_a_reader(self):
        # Only the compound tokens are tested: a value without an underscore is
        # an ordinary word that may legitimately appear in a citation.
        tokens = {
            value
            for item in self.contributions
            for value in item.get("evidenceContext") or []
            if "_" in value
        }
        self.assertGreater(len(tokens), 10, "the vocabulary should be sampled")
        for token in sorted(tokens):
            for work_id, text in self.pages.items():
                self.assertNotIn(token, text, f"{work_id} prints {token!r}")


class OriginalCompositionCouplingTests(unittest.TestCase):
    """One `evidenceContext` value carries rendering logic: on an other work,
    `original_composition` is what separates "Music and arrangement" from the
    remaining credits. The field is free text with no controlled vocabulary, so
    renaming that value would silently drop a section from eighteen pages."""

    SECTION = "Music and arrangement"
    VALUE = "original_composition"

    @classmethod
    def setUpClass(cls):
        cls.contributions = read_records("contributions.json")
        cls.works = {item["id"]: item for item in read_records("works.json")}

    def flagged_work_ids(self):
        return {
            work_id
            for item in self.contributions
            if self.VALUE in (item.get("evidenceContext") or [])
            for work_id in item.get("workIds") or []
        }

    def test_the_value_is_still_in_the_data(self):
        self.assertTrue(
            self.flagged_work_ids(),
            f"no contribution carries {self.VALUE!r}; the renderer's test for it is dead",
        )

    def test_the_value_only_appears_where_the_renderer_reads_it(self):
        # The renderer gates the comparison on an other work, so the value
        # would do nothing on a song or a film.
        for work_id in self.flagged_work_ids():
            self.assertEqual(
                self.works[work_id].get("workType"),
                "Other",
                f"{work_id} carries {self.VALUE!r} where the renderer ignores it",
            )

    def test_every_flagged_work_shows_the_section(self):
        for work_id in sorted(self.flagged_work_ids()):
            page = ROOT / "records/work" / work_id / "index.html"
            if not page.is_file():
                continue
            self.assertIn(
                self.SECTION,
                page.read_text(encoding="utf-8"),
                f"{work_id} is flagged {self.VALUE!r} but shows no {self.SECTION!r}",
            )


if __name__ == "__main__":
    unittest.main()
