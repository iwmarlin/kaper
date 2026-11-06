import json
import re
import unittest
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data/public/v1"

# Sources that date a different form of the work than the one citing them:
# the French version cites the registration of its German original.
OTHER_FORM = {("W-S205", "SRC0470")}


def table(name):
    return {r["id"]: r for r in json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))["records"]}


class WorkYearTests(unittest.TestCase):
    """A Work's year is the earliest year the work itself is documented:
    a dated manuscript, a copyright registration or register entry, a
    publication, a recording session, or the release of the film it was
    used in. A film's year is its first release. docs/work-years.md states
    the rule."""

    @classmethod
    def setUpClass(cls):
        cls.works, cls.songs = table("works"), table("songs")
        cls.sources, cls.contributions = table("sources"), table("contributions")

    def sources_of(self, work):
        ids = set(work.get("sourceIds") or [])
        for credit in work["contributionIds"]:
            ids |= set(self.contributions[credit]["sourceIds"])
        return [self.sources[s] for s in sorted(ids)]

    def test_no_work_is_dated_after_its_copyright_registration(self):
        # A film is dated by its release; a song registered before it does
        # not date the film.
        for work in self.works.values():
            if work["workType"] == "Film":
                continue
            for source in self.sources_of(work):
                if source["sourceType"] != "copyright_catalogue" or (work["id"], source["id"]) in OTHER_FORM:
                    continue
                match = re.search(r"©[^;]{0,40}?(19\d\d)", source["fullCitation"])
                if match:
                    with self.subTest(work=work["id"], source=source["id"]):
                        self.assertLessEqual(work["year"], int(match.group(1)))

    def test_no_work_is_dated_after_its_dated_manuscript(self):
        for work in self.works.values():
            for source in self.sources_of(work):
                if source["sourceType"] == "archival_manuscript_holding" or (
                    "manuscript" in source["title"].lower() and source["dateRole"] == "creation"
                ):
                    if source.get("dateQualifier") == "confirmed" and not source.get("dateEnd") and source.get("date"):
                        with self.subTest(work=work["id"], source=source["id"]):
                            self.assertLessEqual(work["year"], int(source["date"][:4]))

    def test_the_years_moved_by_the_rule(self):
        expected = {
            "W-S024": 1927, "W-S026": 1929, "W-S084": 1932, "W-S129": 1936, "W-S153": 1936,
            "W-S154": 1936, "W-S155": 1936, "W-S158": 1936, "W-S168": 1936, "W-S170": 1936,
            "W-S011": 1930, "W-S033": 1932, "W-S036": 1932, "W-S050": 1932, "W-S064": 1932,
            "W-S040": 1933, "W-S175": 1939,
        }
        for work_id, year in expected.items():
            with self.subTest(work=work_id):
                self.assertEqual(self.works[work_id]["year"], year)
                self.assertEqual(self.songs[work_id[2:]]["year"], year)


if __name__ == "__main__":
    unittest.main()
