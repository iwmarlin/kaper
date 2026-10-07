from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_static_records import structured_data  # noqa: E402


class StaticSourceSchemaTests(unittest.TestCase):
    def schema(self, record: dict) -> dict:
        markup = structured_data(
            "source",
            record,
            "https://example.test/records/source/STEST/",
            "Test source",
            "Test source description",
            {},
        )
        return json.loads(markup.partition(">")[2].rpartition("</script>")[0])

    def test_issue_date_is_published_date(self) -> None:
        data = self.schema(
            {
                "date": "1935",
                "dateRole": "issue",
                "dateQualifier": "confirmed",
            }
        )
        self.assertEqual(data["datePublished"], "1935")
        self.assertNotIn("dateCreated", data)

    def test_record_update_is_not_published_date(self) -> None:
        data = self.schema(
            {
                "date": "2026-04-14",
                "dateRole": "record_update",
                "dateQualifier": "confirmed",
            }
        )
        self.assertEqual(data["dateModified"], "2026-04-14")
        self.assertNotIn("datePublished", data)

    def test_uncertain_date_is_not_asserted_as_exact_schema_date(self) -> None:
        data = self.schema(
            {
                "date": "1938",
                "dateEnd": "1948",
                "dateRole": "creation",
                "dateQualifier": "uncertain",
            }
        )
        self.assertNotIn("dateCreated", data)
        self.assertNotIn("datePublished", data)
        self.assertNotIn("temporalCoverage", data)


if __name__ == "__main__":
    unittest.main()
