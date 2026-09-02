from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from add_listening_reference import (  # noqa: E402
    build_records,
    canonical_external_url,
    external_audio_media_for_work,
)
from validate_public_export import ExportValidator  # noqa: E402
from recording_organizations import expected_audio_organization_ids  # noqa: E402


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

    def test_existing_external_audio_is_detected_per_work(self) -> None:
        records = [
            {
                "id": "M-AUDIO",
                "mediaType": "audio",
                "storageType": "external",
                "workIds": ["W-ONE"],
            },
            {
                "id": "M-VIDEO",
                "mediaType": "video",
                "storageType": "external",
                "workIds": ["W-ONE"],
            },
            {
                "id": "M-LOCAL",
                "mediaType": "audio",
                "storageType": "local",
                "workIds": ["W-ONE"],
            },
        ]

        self.assertEqual(
            [record["id"] for record in external_audio_media_for_work(records, "W-ONE")],
            ["M-AUDIO"],
        )

    def test_work_organizations_require_explicit_opt_in(self) -> None:
        work = {
            "id": "W-TEST",
            "title": "Test work",
            "period": "european",
            "organizationIds": ["ORG-WORK"],
        }
        media, _ = build_records(
            url="https://example.org/recording",
            work=work,
            meta={"title": "Test recording", "channel": "Test archive"},
            media_id="M999",
            source_id="SRC9999",
            person_id=None,
            performer=None,
            media_type="audio",
            inherit_organizations=False,
        )

        self.assertNotIn("organizationIds", media)

    def test_validator_requires_explicit_exception_for_multiple_audio(self) -> None:
        validator = object.__new__(ExportValidator)
        validator.errors = []
        validator.warnings = []
        validator.assets_root = None
        validator.config = {"mediaExceptions": {}}
        validator.payloads = {
            "Works": {"records": [{"id": "W-TEST"}]},
            "Sources": {"records": []},
            "Media": {
                "records": [
                    {
                        "id": media_id,
                        "mediaType": "audio",
                        "storageType": "external",
                        "assetCount": 0,
                        "galleryStatus": "external_link_only",
                        "externalUrl": f"https://example.org/{media_id}",
                        "sourceIds": [f"SRC-{media_id}"],
                        "rightsStatus": "external_content_not_rehosted",
                        "rightsNote": "External content; no local copy is hosted.",
                        "workIds": ["W-TEST"],
                    }
                    for media_id in ("M-ONE", "M-TWO")
                ]
            },
        }

        validator._validate_media()

        self.assertTrue(
            any(
                "multiple external audio references" in error
                for error in validator.errors
            )
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

    def test_disc_citation_keeps_one_stop_and_the_supplied_date(self) -> None:
        works = json.loads(
            (ROOT / "data/public/v1/works.json").read_text(encoding="utf-8")
        )["records"]
        work = next(record for record in works if record["id"] == "W-S002")

        def citation(date_value: str | None) -> str:
            disc = {"label": "Parlophone", "catalogue": "A3436"}
            if date_value is not None:
                disc["date"] = date_value
            _, source = build_records(
                url="https://archive.org/details/example",
                work=work,
                meta={"title": "Test transfer", "channel": "Great 78 Project"},
                media_id="M999",
                source_id="SRC9999",
                person_id=None,
                performer=None,
                media_type="audio",
                inherit_organizations=False,
                disc=disc,
            )
            return source["fullCitation"]

        undated = citation(None)
        self.assertIn("Parlophone, Katalog-Nr. A3436, n.d.", undated)
        self.assertNotIn("..", undated)
        self.assertIn("A3436, 1931.", citation("1931"))
        self.assertIn(
            "A3436, n.d. [recorded 1929].", citation("n.d. [recorded 1929]")
        )

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
            source = sources_by_id[source_id]
            self.assertTrue(source.get("dateRole"))
            self.assertTrue(source.get("dateQualifier"))
            if source["dateQualifier"] == "unknown":
                self.assertNotIn("date", source)
            else:
                self.assertTrue(source.get("date"))

    def test_lindstrom_odeon_and_parlophone_are_distinct_entities(self) -> None:
        organizations = json.loads(
            (ROOT / "data/public/v1/organizations.json").read_text(encoding="utf-8")
        )["records"]
        organizations_by_id = {record["id"]: record for record in organizations}

        self.assertEqual(organizations_by_id["ORG128"]["types"], ["record_company"])
        self.assertEqual(organizations_by_id["ORG146"]["types"], ["record_label"])
        self.assertEqual(organizations_by_id["ORG150"]["types"], ["record_label"])
        self.assertNotIn(
            "Parlophone", organizations_by_id["ORG128"].get("nameVariants", "")
        )
        self.assertNotIn(
            "Odeon;", organizations_by_id["ORG128"].get("nameVariants", "")
        )

    def test_specific_parlophone_media_exclude_other_issues_and_publishers(self) -> None:
        media = json.loads(
            (ROOT / "data/public/v1/media.json").read_text(encoding="utf-8")
        )["records"]
        media_by_id = {record["id"]: record for record in media}

        self.assertEqual(media_by_id["M406"]["organizationIds"], ["ORG146", "ORG149"])
        self.assertEqual(media_by_id["M410"]["organizationIds"], ["ORG146"])

    def test_audio_organization_rule_excludes_platforms_and_work_publishers(self) -> None:
        media = {"id": "MTEST", "sourceIds": ["SRCTEST"]}
        sources = {
            "SRCTEST": {
                "id": "SRCTEST",
                "organizationIds": ["ORG-LABEL", "ORG-ENSEMBLE", "ORG-PLATFORM"],
            }
        }
        organizations = {
            "ORG-LABEL": {"id": "ORG-LABEL", "types": ["record_label"]},
            "ORG-ENSEMBLE": {"id": "ORG-ENSEMBLE", "types": ["ensemble"]},
            "ORG-PLATFORM": {"id": "ORG-PLATFORM", "types": ["database"]},
            "ORG-PUBLISHER": {"id": "ORG-PUBLISHER", "types": ["publisher"]},
        }

        self.assertEqual(
            expected_audio_organization_ids(
                media,
                sources_by_id=sources,
                organizations_by_id=organizations,
            ),
            ["ORG-ENSEMBLE", "ORG-LABEL"],
        )

    def test_validator_rejects_inherited_audio_organizations(self) -> None:
        validator = object.__new__(ExportValidator)
        validator.errors = []
        validator.payloads = {
            name: {"records": []}
            for name in TABLE_NAMES
        }
        validator.payloads["Organizations"]["records"] = [
            {"id": "ORG-PUBLISHER", "types": ["publisher"]},
            {"id": "ORG-LABEL", "types": ["record_label"]},
        ]
        validator.payloads["Sources"]["records"] = [{
            "id": "SRCTEST",
            "organizationIds": ["ORG-LABEL"],
        }]
        validator.payloads["Media"]["records"] = [{
            "id": "MTEST",
            "mediaType": "audio",
            "storageType": "external",
            "sourceIds": ["SRCTEST"],
            "organizationIds": ["ORG-PUBLISHER"],
        }]

        validator._validate_audio_organization_support()

        self.assertEqual(len(validator.errors), 1)
        self.assertIn("ORG-PUBLISHER", validator.errors[0])
        self.assertIn("ORG-LABEL", validator.errors[0])

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

    def test_jazz_drops_numbers_are_distinct_item_level_works(self) -> None:
        """Every documented number of the series is a work of its own.

        The series grows as further prints are identified, so the test reads the
        membership from the series record rather than naming the numbers: each
        relation must point one item-level work at Jazz Drops, and each item must
        rest on the print that carries its own number.
        """
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

        relation_ids = works_by_id["W-O008"]["relationIds"]
        self.assertGreaterEqual(len(relation_ids), 5)
        self.assertEqual(len(relation_ids), len(set(relation_ids)))

        item_ids: list[str] = []
        slugs: set[str] = set()
        for number, relation_id in enumerate(relation_ids, start=1):
            relation = relations_by_id[relation_id]
            self.assertEqual(relation["relationType"], "part_of_series")
            self.assertEqual(relation["targetWorkIds"], ["W-O008"])
            self.assertEqual(len(relation["sourceWorkIds"]), 1)
            work_id = relation["sourceWorkIds"][0]
            work = works_by_id[work_id]
            self.assertEqual(work["relationIds"], [relation_id])

            carrying = [
                sources_by_id[source_id]
                for source_id in work["sourceIds"]
                if relation_id in (sources_by_id[source_id].get("workRelationIds") or [])
            ]
            self.assertEqual(len(carrying), 1)
            source = carrying[0]
            self.assertEqual(source["sourceType"], "sheet_music")
            self.assertIn(work_id, source["workIds"])
            self.assertIn(f"Jazz Drops, no. {number}", source["fullCitation"])

            item_ids.append(work_id)
            slugs.add(work["slug"])

        self.assertEqual(len(slugs), len(item_ids))
        self.assertNotIn(works_by_id["W-O014"]["slug"], slugs)
        self.assertNotIn("W-O013", item_ids)

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
