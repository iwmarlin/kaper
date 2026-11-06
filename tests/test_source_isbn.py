import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from source_dates import SOURCE_IDENTIFIER_SCHEMES, valid_isbn  # noqa: E402


def read_sources():
    path = ROOT / "data/public/v1/sources.json"
    return json.loads(path.read_text(encoding="utf-8"))["records"]


class IsbnTests(unittest.TestCase):
    """A printed book has no URL to open; its ISBN is how a reader finds it in
    a library, so a wrong digit sends the reader to a different book."""

    def test_the_scheme_is_controlled(self):
        self.assertIn("isbn", SOURCE_IDENTIFIER_SCHEMES)

    def test_the_check_digit_is_verified(self):
        self.assertTrue(valid_isbn("978-3-902494-18-4"))
        self.assertTrue(valid_isbn("9783902494184"))
        self.assertFalse(valid_isbn("978-3-902494-18-5"), "wrong check digit")
        self.assertFalse(valid_isbn("978-3-902494-81-4"), "transposed digits")
        self.assertFalse(valid_isbn("3902494182"), "ISBN-10 is not stored")
        self.assertFalse(valid_isbn(""))

    def test_every_isbn_in_the_data_is_valid(self):
        values = [
            (source["id"], item["value"])
            for source in read_sources()
            for item in source.get("identifiers") or []
            if item.get("scheme") == "isbn"
        ]
        self.assertTrue(values, "the fixture must exercise the scheme")
        for source_id, value in values:
            self.assertTrue(valid_isbn(value), f"{source_id}: {value}")

    def test_the_jurmann_catalogue_is_findable(self):
        # Buxbaum's Jurmann book carries the Sieghardt filmography that 44
        # films cite. It was one of three Sources a reader could not reach.
        source = next(s for s in read_sources() if s["id"] == "SRC0373")
        self.assertIn(
            {"scheme": "isbn", "value": "978-3-902494-18-4"},
            source.get("identifiers") or [],
        )


if __name__ == "__main__":
    unittest.main()
