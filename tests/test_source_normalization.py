from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from normalize_sources import normalize_payload  # noqa: E402
from visual_sources import (  # noqa: E402
    VISUAL_SOURCE_TYPES,
    is_wikipedia_article_page,
    is_wikipedia_file_page,
    normalize_unidentified_photographer_wording,
)


class SourceNormalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(
            (PUBLIC / "sources.json").read_text(encoding="utf-8")
        )
        cls.sources = {
            source["id"]: source for source in cls.payload["records"]
        }
        cls.media = {
            media["id"]: media
            for media in json.loads(
                (PUBLIC / "media.json").read_text(encoding="utf-8")
            )["records"]
        }
        cls.people = {
            person["id"]: person
            for person in json.loads(
                (PUBLIC / "people.json").read_text(encoding="utf-8")
            )["records"]
        }
        cls.events = {
            event["id"]: event
            for event in json.loads(
                (PUBLIC / "timeline-events.json").read_text(encoding="utf-8")
            )["records"]
        }

    def test_canonical_sources_are_idempotent_under_every_normalizer(self) -> None:
        normalized, changed_ids = normalize_payload(self.payload)
        self.assertEqual(changed_ids, [])
        self.assertEqual(normalized, self.payload)

    def test_gnd_and_bnf_person_notices_use_authority_semantics(self) -> None:
        expected = {
            "SRC0548": ("Deutsche Nationalbibliothek (GND)", "VIAF 61733693"),
            "SRC0549": (
                "Bibliothèque nationale de France (BnF)",
                "pseudonym of Didier Bloch",
            ),
        }
        for source_id, (repository, evidence) in expected.items():
            with self.subTest(source_id=source_id):
                source = self.sources[source_id]
                self.assertEqual(source["sourceType"], "authority_record")
                self.assertEqual(source["repository"], repository)
                self.assertEqual(source["researchNoteType"], "authority_note")
                self.assertIn(evidence, source["researchNote"])
                self.assertNotIn(evidence, source["fullCitation"])

    def test_wikipedia_file_and_article_pages_are_not_conflated(self) -> None:
        file_pages = [
            source for source in self.sources.values() if is_wikipedia_file_page(source)
        ]
        article_pages = [
            source
            for source in self.sources.values()
            if is_wikipedia_article_page(source)
        ]
        self.assertTrue(file_pages)
        self.assertTrue(article_pages)
        self.assertEqual(
            {"image_or_photograph"},
            {source["sourceType"] for source in file_pages},
        )
        self.assertEqual(
            {"wikimedia_article_page"},
            {source["sourceType"] for source in article_pages},
        )

    def test_corrected_visual_records_preserve_item_level_provenance(self) -> None:
        self.assertEqual(
            "Becker & Maass / Marie Boehm",
            self.sources["SRC0330"]["creator"],
        )
        self.assertEqual("1933", self.sources["SRC0351"]["date"])
        self.assertNotRegex(self.sources["SRC0351"]["title"], r"\.jpg$")

        poster = self.sources["SRC0362"]
        self.assertEqual("1931", poster["date"])
        self.assertIn("Paris qui brille", poster["title"])
        self.assertNotIn("La Parade de France", poster["title"])

        postcard = self.sources["SRC0366"]
        self.assertEqual("1908", postcard["date"])
        self.assertEqual("Photographer unidentified", postcard["creator"])
        self.assertIn("Manskopf", postcard["repository"])

        morskie_oko = self.sources["SRC0523"]
        self.assertEqual(
            "https://pl.wikipedia.org/wiki/Morskie_Oko_(teatr)",
            morskie_oko["primaryUrl"],
        )
        self.assertNotIn("accessUrl", morskie_oko)

        self.assertEqual(
            "Photographer unidentified",
            self.sources["SRC0571"]["creator"],
        )
        self.assertEqual(
            "Samuel Herman Gottscho",
            self.sources["SRC0572"]["creator"],
        )
        self.assertEqual(
            "Photographer unidentified",
            self.sources["SRC0604"]["creator"],
        )

    def test_uploader_claim_is_not_presented_as_established_photographer(self) -> None:
        source = self.sources["SRC0595"]
        self.assertEqual("Azeisler (file-page attribution)", source["creator"])
        self.assertEqual("object_context", source["researchNoteType"])
        self.assertIn("does not identify the photographer", source["researchNote"])

    def test_visual_creator_labels_use_public_house_style(self) -> None:
        expected = {
            "SRC0350": "Burton Frasher Sr.",
            "SRC0570": "William P. Gottlieb",
            "SRC0586": "Photographer unidentified",
            "SRC0649": "Photographer unidentified",
            "SRC0654": "Photographer unidentified",
            "SRC0655": "Photographer unidentified",
            "SRC0711": "Jacob Merkelbach",
            "SRC0795": "Stanisław Brzozowski",
            "SRC0812": "Photographer unidentified",
            "SRC0814": "Photographer unidentified",
        }
        for source_id, creator in expected.items():
            with self.subTest(source_id=source_id):
                self.assertEqual(self.sources[source_id]["creator"], creator)

    def test_visual_citations_do_not_use_legacy_unknown_photographer_labels(self) -> None:
        legacy = re.compile(
            r"\b(?:Unknown photographer|Photographer (?:unknown|unnamed))\b"
        )
        for source in self.sources.values():
            if source["sourceType"] not in VISUAL_SOURCE_TYPES:
                continue
            with self.subTest(source_id=source["id"]):
                self.assertNotRegex(source.get("shortCitation", ""), legacy)
                self.assertNotRegex(source.get("fullCitation", ""), legacy)

    def test_corrected_visual_sources_and_linked_records_agree(self) -> None:
        mayer_source = self.sources["SRC0366"]
        mayer_media = self.media["M079"]
        self.assertIn("Moritz Mayer-Mahr", mayer_source["title"])
        self.assertIn("Moritz Mayer-Mahr", mayer_media["title"])
        self.assertNotIn("Moriz Mayer-Mahr", mayer_media["description"])
        self.assertEqual("Mayer-Mahr, Moritz", self.people["P122"]["sortName"])
        self.assertNotIn("Moriz Mayer-Mahr", self.events["TE0016"]["longDescription"])

        self.assertIn("Marie Boehm", self.media["M043"]["publicCreditLine"])
        self.assertIn("paris-qui-brille", self.media["M111"]["slug"])
        self.assertTrue(
            self.media["M243"]["publicCreditLine"].startswith(
                "Photographer unidentified"
            )
        )
        self.assertTrue(
            self.media["M255"]["publicCreditLine"].startswith(
                "Photographer unidentified"
            )
        )

    def test_media_prose_uses_controlled_unidentified_photographer_label(self) -> None:
        legacy = re.compile(
            r"\b(?:Unknown photographer|Photographer (?:unknown|unnamed))\b"
        )
        public_fields = (
            "description",
            "publicCaption",
            "publicCreditLine",
            "rightsNote",
        )
        for media in self.media.values():
            for field_name in public_fields:
                with self.subTest(media_id=media["id"], field=field_name):
                    self.assertNotRegex(media.get(field_name, ""), legacy)

    def test_photographer_wording_normalizer_does_not_reclassify_unknown_authors(self) -> None:
        self.assertEqual(
            "Photographer unidentified; source institution.",
            normalize_unidentified_photographer_wording(
                "Unknown photographer; source institution."
            ),
        )
        self.assertEqual(
            "Unknown author; source institution.",
            normalize_unidentified_photographer_wording(
                "Unknown author; source institution."
            ),
        )


if __name__ == "__main__":
    unittest.main()
