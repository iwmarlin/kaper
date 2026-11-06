import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_records(name):
    path = ROOT / "data/public/v1" / name
    return json.loads(path.read_text(encoding="utf-8"))["records"]


class ShelfmarkMeaningTests(unittest.TestCase):
    """A shelfmark says where a unique object is held. A manuscript has one;
    a printed edition does not, because it exists in many copies and the
    shelfmark of any one of them would describe that library, not the work.

    The audit once counted 23 of 30 Other Works without a shelfmark as a gap.
    All 23 are printed or known only from the press, and every manuscript
    carries its box in the Kaper Papers, so the count measured the field's
    meaning, not missing data. These tests hold that meaning."""

    @classmethod
    def setUpClass(cls):
        cls.other_works = read_records("other-works.json")

    def test_every_manuscript_says_where_it_is_held(self):
        manuscripts = [o for o in self.other_works if o.get("materialStatus") == "manuscript"]
        self.assertTrue(manuscripts, "the fixture must contain manuscripts")
        for item in manuscripts:
            self.assertTrue((item.get("shelfmark") or "").strip(), item["id"])

    def test_no_printed_edition_borrows_a_copys_shelfmark(self):
        for item in self.other_works:
            if item.get("materialStatus") == "manuscript":
                continue
            self.assertFalse(
                (item.get("shelfmark") or "").strip(),
                f"{item['id']} is {item.get('materialStatus')} and should not carry a shelfmark",
            )


if __name__ == "__main__":
    unittest.main()
