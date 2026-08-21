from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from add_listening_reference import build_records, canonical_external_url  # noqa: E402
from validate_public_export import ExportValidator  # noqa: E402


TABLE_NAMES = (
    "People",
    "Organizations",
    "Sources",
    "Media",
    "Works",
    "Films",
    "Songs",
    "Other Works",
    "Title Variants",
    "Work Relations",
    "Timeline Events",
    "Places",
    "Contributions",
    "Person Name Variants",
)


class RecordingGraphTests(unittest.TestCase):
    def test_youtube_variants_have_one_canonical_url(self) -> None:
        expected = "https://www.youtube.com/watch?v=MylHacBQYXE"
        self.assertEqual(
            canonical_external_url(
                "https://www.youtube.com/watch?v=MylHacBQYXE&t=3s&list=RDtest"
            ),
            expected,
        )
        self.assertEqual(
            canonical_external_url(
                "https://youtu.be/MylHacBQYXE?utm_source=example&t=99"
            ),
            expected,
        )

    def test_generated_source_carries_explicit_graph_endpoints(self) -> None:
        works = json.loads(
            (ROOT / "data/public/v1/works.json").read_text(encoding="utf-8")
        )["records"]
        work = next(record for record in works if record["id"] == "W-S002")
        media, source = build_records(
            url="https://www.youtube.com/watch?v=example",
            work=work,
            meta={"title": "Test recording", "channel": "Test archive"},
            media_id="M999",
            source_id="SRC9999",
            person_id="P009",
            performer="Bronisław Kaper",
            media_type="audio",
            inherit_organizations=False,
            source_organization_ids=["ORG034"],
            contribution_ids=["CON-S002-C-P009"],
        )

        self.assertEqual(media["workIds"], ["W-S002"])
        self.assertEqual(source["workIds"], ["W-S002"])
        self.assertEqual(source["songIds"], work["songIds"])
        self.assertEqual(source["mediaIds"], ["M999"])
        self.assertEqual(source["personIds"], ["P009"])
        self.assertEqual(source["contributionIds"], ["CON-S002-C-P009"])
        self.assertEqual(source["organizationIds"], ["ORG034", "ORG093"])

    def test_validator_rejects_one_sided_links(self) -> None:
        validator = object.__new__(ExportValidator)
        validator.errors = []
        validator.payloads = {
            name: {"records": []}
            for name in TABLE_NAMES
        }
        validator.payloads["People"]["records"] = [
            {"id": "PTEST", "sourceIds": ["SRCTEST"]}
        ]
        validator.payloads["Sources"]["records"] = [{"id": "SRCTEST"}]

        validator._validate_symmetric_links()

        self.assertEqual(len(validator.errors), 1)
        self.assertIn("Sources SRCTEST.personIds omits PTEST", validator.errors[0])

    def test_validator_preserves_directional_work_relations(self) -> None:
        validator = object.__new__(ExportValidator)
        validator.errors = []
        validator.payloads = {
            name: {"records": []}
            for name in TABLE_NAMES
        }
        validator.payloads["Works"]["records"] = [{"id": "W-TEST"}]
        validator.payloads["Work Relations"]["records"] = [
            {"id": "WR-TEST", "sourceWorkIds": ["W-TEST"]}
        ]

        validator._validate_symmetric_links()

        self.assertTrue(
            any("relationIds omits WR-TEST" in error for error in validator.errors)
        )


if __name__ == "__main__":
    unittest.main()
