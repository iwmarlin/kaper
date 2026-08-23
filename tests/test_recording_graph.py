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
        self.assertEqual(media["songIds"], work["songIds"])
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

    def test_validator_rejects_one_sided_media_song_links(self) -> None:
        validator = object.__new__(ExportValidator)
        validator.errors = []
        validator.payloads = {
            name: {"records": []}
            for name in TABLE_NAMES
        }
        validator.payloads["Media"]["records"] = [
            {"id": "MTEST", "songIds": ["STEST"]}
        ]
        validator.payloads["Songs"]["records"] = [{"id": "STEST"}]

        validator._validate_symmetric_links()

        self.assertEqual(len(validator.errors), 1)
        self.assertIn("Songs STEST.mediaIds omits MTEST", validator.errors[0])

    def test_public_media_song_links_are_fully_symmetric(self) -> None:
        media = json.loads(
            (ROOT / "data/public/v1/media.json").read_text(encoding="utf-8")
        )["records"]
        songs = json.loads(
            (ROOT / "data/public/v1/songs.json").read_text(encoding="utf-8")
        )["records"]
        media_by_id = {record["id"]: record for record in media}
        songs_by_id = {record["id"]: record for record in songs}

        for media_id, medium in media_by_id.items():
            for song_id in medium.get("songIds", []):
                self.assertIn(media_id, songs_by_id[song_id].get("mediaIds", []))
        for song_id, song in songs_by_id.items():
            for media_id in song.get("mediaIds", []):
                self.assertIn(song_id, media_by_id[media_id].get("songIds", []))

    def test_validator_rejects_media_work_not_supported_by_its_sources(self) -> None:
        validator = object.__new__(ExportValidator)
        validator.errors = []
        validator.payloads = {
            name: {"records": []}
            for name in TABLE_NAMES
        }
        validator.payloads["Media"]["records"] = [{
            "id": "MTEST",
            "mediaType": "audio",
            "storageType": "external",
            "sourceIds": ["SRCTEST"],
            "workIds": ["W-WRONG", "W-RIGHT"],
        }]
        validator.payloads["Sources"]["records"] = [{
            "id": "SRCTEST",
            "workIds": ["W-RIGHT"],
        }]

        validator._validate_media_source_work_support()

        self.assertEqual(len(validator.errors), 1)
        self.assertIn("W-WRONG", validator.errors[0])

    def test_miss_annabelle_lee_is_linked_to_cocktails_not_jazz_drops(self) -> None:
        media = json.loads(
            (ROOT / "data/public/v1/media.json").read_text(encoding="utf-8")
        )["records"]
        works = json.loads(
            (ROOT / "data/public/v1/works.json").read_text(encoding="utf-8")
        )["records"]
        relations = json.loads(
            (ROOT / "data/public/v1/work-relations.json").read_text(encoding="utf-8")
        )["records"]
        media_by_id = {record["id"]: record for record in media}
        works_by_id = {record["id"]: record for record in works}
        relations_by_id = {record["id"]: record for record in relations}

        self.assertEqual(media_by_id["M002"]["workIds"], ["W-O019"])
        self.assertEqual(media_by_id["M002"]["otherWorkIds"], ["O019"])
        self.assertNotIn("mediaIds", works_by_id["W-O008"])
        self.assertIn("M002", works_by_id["W-O019"]["mediaIds"])
        self.assertEqual(relations_by_id["REL0185"]["sourceWorkIds"], ["W-O019"])
        self.assertEqual(relations_by_id["REL0185"]["targetWorkIds"], ["W-O007"])

    def test_jazz_drops_first_five_are_distinct_item_level_works(self) -> None:
        works = json.loads(
            (ROOT / "data/public/v1/works.json").read_text(encoding="utf-8")
        )["records"]
        sources = json.loads(
            (ROOT / "data/public/v1/sources.json").read_text(encoding="utf-8")
        )["records"]
        relations = json.loads(
            (ROOT / "data/public/v1/work-relations.json").read_text(encoding="utf-8")
        )["records"]
        works_by_id = {record["id"]: record for record in works}
        sources_by_id = {record["id"]: record for record in sources}
        relations_by_id = {record["id"]: record for record in relations}

        item_ids = ["W-O023", "W-O024", "W-O025", "W-O026", "W-O027"]
        relation_ids = ["REL0203", "REL0204", "REL0205", "REL0206", "REL0207"]
        source_ids = ["SRC0768", "SRC0769", "SRC0770", "SRC0771", "SRC0772"]

        self.assertEqual(works_by_id["W-O008"]["relationIds"], relation_ids)
        for work_id, relation_id, source_id in zip(item_ids, relation_ids, source_ids):
            work = works_by_id[work_id]
            relation = relations_by_id[relation_id]
            source = sources_by_id[source_id]
            self.assertEqual(work["relationIds"], [relation_id])
            self.assertEqual(relation["sourceWorkIds"], [work_id])
            self.assertEqual(relation["targetWorkIds"], ["W-O008"])
            self.assertEqual(source["workIds"], [work_id])
            self.assertEqual(source["workRelationIds"], [relation_id])
            self.assertIn("Hofmeisters Musikalisch-literarischer Monatsbericht", source["fullCitation"])

        self.assertNotEqual(works_by_id["W-O023"]["slug"], works_by_id["W-O014"]["slug"])
        self.assertNotEqual(works_by_id["W-O026"]["id"], "W-O013")

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
