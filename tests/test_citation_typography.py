import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
CITATION_FIELDS = ("fullCitation", "shortCitation")
LIFE_DATES = re.compile(r"\(\d{4}-\d{4}\)")


def sources():
    return json.loads((PUBLIC / "sources.json").read_text(encoding="utf-8"))["records"]


class CitationTypographyTests(unittest.TestCase):
    """A citation written two ways is the same record twice. Sixty-four sources
    had drifted onto straight quotation marks while the rest used typographic
    ones, and two wrote a life-date range with a hyphen."""

    def test_citations_use_typographic_quotation_marks(self):
        offenders = [
            f"{record['id']}.{field}"
            for record in sources()
            for field in CITATION_FIELDS
            if '"' in (record.get(field) or "")
        ]
        self.assertEqual(offenders, [], "a citation uses a straight quotation mark")

    def test_a_date_range_uses_an_en_dash(self):
        offenders = [
            f"{record['id']}.{field}"
            for record in sources()
            for field in CITATION_FIELDS
            if LIFE_DATES.search(record.get(field) or "")
        ]
        self.assertEqual(offenders, [], "a date range is written with a hyphen")

    def test_a_nested_quotation_takes_the_single_form(self):
        # A title that contains a quotation is set inside the citation's own
        # quotation marks; the inner pair has to differ from the outer or the
        # reader cannot tell where the title ends.
        #
        # German quoting is exempt and has to be, because „…“ closes with the
        # same glyph that opens an English quotation: a citation that quotes a
        # German title inside an English one reads „Odeon“ inside “…”, and the
        # inner pair is already distinct. Only strings with no German opener are
        # tested, which is where a repeated outer mark is unambiguous.
        offenders = [
            f"{record['id']}.{field}"
            for record in sources()
            for field in CITATION_FIELDS
            if "„" not in (record.get(field) or "")
            and re.search(r"“[^”]*“", record.get(field) or "")
        ]
        self.assertEqual(offenders, [], "a nested quotation repeats the outer mark")

    def test_the_identifiers_that_are_literal_strings_are_left_alone(self):
        # One title is a Wikimedia file name, where a straight mark is part of
        # the identifier. Titles are outside the rule for that reason, and this
        # test records why rather than leaving it to be rediscovered.
        titles = [record.get("title") or "" for record in sources()]
        self.assertTrue(
            any("File:" in title and '"' in title for title in titles),
            "the exemption exists for a file name that no longer occurs; the rule may now cover titles",
        )


class TitleAndCitationTests(unittest.TestCase):
    """Where a source's title is its short citation, the title field carries
    citation apparatus rather than the name of the thing. Seven records do, and
    what their titles should be is an editorial question, not a mechanical one."""

    KNOWN = {
        "SRC0023", "SRC0110", "SRC0333", "SRC0337", "SRC0407", "SRC0409", "SRC0424",
    }

    def test_no_new_source_repeats_its_citation_as_its_title(self):
        offenders = {
            record["id"]
            for record in sources()
            if (record.get("title") or "").strip() == (record.get("shortCitation") or "").strip()
        }
        self.assertEqual(
            sorted(offenders - self.KNOWN), [],
            "a new source repeats its short citation as its title",
        )
        self.assertTrue(
            offenders <= self.KNOWN,
            "the known list must not grow",
        )


if __name__ == "__main__":
    unittest.main()
