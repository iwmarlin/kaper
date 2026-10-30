import json
import unittest
from pathlib import Path

from scripts.build_record_payloads import RecordPayloadBuilder, record_ids


ROOT = Path(__file__).resolve().parents[1]


class PersonPayloadPerformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = RecordPayloadBuilder(ROOT / "data/public/v1")

    def test_large_person_payload_projects_credit_only_relations(self):
        payload = self.builder.build("person", "P009")
        tables = payload["tables"]
        person = tables["people"][0]

        evidence_source_ids = {
            source_id
            for contribution in tables["contributions"]
            if record_ids(contribution, "workIds")
            for source_id in record_ids(contribution, "sourceIds")
        }
        direct_only_ids = set(record_ids(person, "sourceIds")) - evidence_source_ids
        credit_only_ids = evidence_source_ids - set(record_ids(person, "sourceIds"))
        sources = {source["id"]: source for source in tables["sources"]}

        self.assertTrue(direct_only_ids)
        self.assertTrue(credit_only_ids)
        direct_id = sorted(direct_only_ids)[0]
        credit_id = sorted(credit_only_ids)[0]
        self.assertEqual(sources[direct_id], self.builder.indexes["sources"][direct_id])
        self.assertNotIn("fullCitation", sources[credit_id])
        self.assertLessEqual(
            set(tables["works"][0]),
            {"id", "title", "year", "workType"},
        )
        self.assertTrue({"id", "title"}.issubset(tables["works"][0]))
        self.assertLess(
            len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
            250_000,
            "P009 should not regress to carrying complete copies of hundreds of related records",
        )

    def test_search_index_is_derived_from_rendered_text(self):
        script = (ROOT / "assets/site/record-detail-20260714.js").read_text(encoding="utf-8")
        self.assertNotIn('data-search="', script)
        self.assertIn("normalizeSearch(row.textContent)", script)
        self.assertIn("normalizeSearch(item.textContent)", script)


if __name__ == "__main__":
    unittest.main()
