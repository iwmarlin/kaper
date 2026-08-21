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
        self.assertEqual(media["mediaType"], "audio")
        self.assertEqual(media["rightsStatus"], "external_content_not_rehosted")
        self.assertIn("no local copy is hosted", media["rightsNote"])

    def test_discographic_assessment_is_separate_from_citation(self) -> None:
        works = json.loads(
            (ROOT / "data/public/v1/works.json").read_text(encoding="utf-8")
        )["records"]
        work = next(record for record in works if record["id"] == "W-S002")
        _, source = build_records(
            url="https://www.youtube.com/watch?v=example",
            work=work,
            meta={"title": "Test transfer", "channel": "Test archive"},
            media_id="M999",
            source_id="SRC9999",
            person_id=None,
            performer=None,
            media_type="audio",
            inherit_organizations=False,
            disc={
                "label": "Test label",
                "catalogue": "123",
                "date": "1931",
                "performer_credit": "Test orchestra",
                "uploader_note": "The uploader gives Berlin as the recording place",
                "from_description": True,
            },
        )

        self.assertNotIn("uploader", source["fullCitation"].casefold())
        self.assertEqual(source["researchNoteType"], "discographic_note")
        self.assertIn("not transcribed from the disc label", source["researchNote"])
        self.assertIn("label is not shown", source["researchNote"])

    def test_record_labels_and_recording_notes_use_canonical_fields(self) -> None:
        organizations = json.loads(
            (ROOT / "data/public/v1/organizations.json").read_text(encoding="utf-8")
        )["records"]
        sources = json.loads(
            (ROOT / "data/public/v1/sources.json").read_text(encoding="utf-8")
        )["records"]
        organizations_by_id = {record["id"]: record for record in organizations}
        sources_by_id = {record["id"]: record for record in sources}

        self.assertFalse(any(
            "record label" in (record.get("types") or [])
            for record in organizations
        ))
        for organization_id in ("ORG133", "ORG136", "ORG138"):
            organization = organizations_by_id[organization_id]
            self.assertTrue(organization.get("publicNote"))
            self.assertNotRegex(
                organization.get("nameVariants", ""),
                r"\b(?:The record business|The company|Described by)\b",
            )

        for source_id in ("SRC0694", "SRC0698", "SRC0753", "SRC0754"):
            source = sources_by_id[source_id]
            self.assertTrue(source.get("researchNote"))
            self.assertTrue(source.get("researchNoteType"))
        self.assertNotIn("zusamm'?.", sources_by_id["SRC0753"]["fullCitation"])

        for source_id in ("SRC0693", "SRC0698", "SRC0715", "SRC0726", "SRC0761"):
            self.assertTrue(sources_by_id[source_id].get("date"))

    def test_validator_rejects_fair_use_status_for_external_recording(self) -> None:
        validator = object.__new__(ExportValidator)
        validator.errors = []
        validator.warnings = []
        validator.assets_root = None
        validator.config = {"mediaExceptions": {}}
        validator.payloads = {
            "Media": {
                "records": [{
                    "id": "MTEST",
                    "mediaType": "audio",
                    "storageType": "external",
                    "galleryStatus": "external_link_only",
                    "externalUrl": "https://example.org/recording",
                    "sourceIds": ["SRCTEST"],
                    "rightsStatus": "permission_needed_or_fair_use_claimed",
                    "rightsNote": "Reuse rights are not cleared.",
                    "publicCreditLine": "External recording.",
                }]
            }
        }

        validator._validate_media()

        self.assertTrue(any(
            "external audio/video must use rightsStatus external_content_not_rehosted" in error
            for error in validator.errors
        ))

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
