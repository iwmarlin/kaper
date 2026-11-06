"""Video copies, historical films and songs are distinct evidential objects."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source
from validate_public_export import ExportValidator
from video_sources import AUDITED_VIDEO_SOURCE_FIELDS


YOUTUBE_DATES = {
    "SRC0314": "2019-03-29", "SRC0315": "2025-01-23",
    "SRC0316": "2013-08-23", "SRC0317": "2021-11-21",
    "SRC0318": "2013-07-27", "SRC0319": "2014-05-31",
    "SRC0320": "2024-12-29", "SRC0321": "2013-04-14",
    "SRC0555": "2010-06-03", "SRC0733": "2017-10-29",
    "SRC0791": "2015-03-20", "SRC0809": "2022-02-13",
}


class VideoSourceReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = {
            table: {r["id"]: r for r in json.loads(
                (ROOT / f"data/public/v1/{table}.json").read_text())["records"]}
            for table in ("sources", "media", "works", "songs", "films", "organizations")
        }

    def test_reviewed_family_remains_video_without_new_source_categories(self):
        self.assertEqual(len(AUDITED_VIDEO_SOURCE_FIELDS), 21)
        for sid in AUDITED_VIDEO_SOURCE_FIELDS:
            source = self.tables["sources"][sid]
            self.assertEqual(source["sourceType"], "online_video_source")
            for mid in source.get("mediaIds", []):
                self.assertEqual(self.tables["media"][mid]["mediaType"], "video")
                self.assertEqual(self.tables["media"][mid]["rightsStatus"],
                                 "external_content_not_rehosted")

    def test_youtube_dates_identify_the_digital_publication(self):
        for sid, date in YOUTUBE_DATES.items():
            source = self.tables["sources"][sid]
            self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                             (date, "digital_publication", "confirmed"))

    def test_filmportal_digitization_is_not_its_later_posting_date(self):
        for sid, year, posted in (("SRC0322", "2021", "2023-02-17"),
                                  ("SRC0323", "2023", "2025-10-16"),
                                  ("SRC0324", "2024", "2025-12-12"),
                                  ("SRC0325", "2022", "2024-05-10")):
            source = self.tables["sources"][sid]
            self.assertEqual((source["date"], source["dateRole"]), (year, "digitization"))
            self.assertIn(posted, source["researchNote"])
            self.assertFalse(source.get("songIds"))
        for mid, runtime in (("M016", "06:58"), ("M018", "08:49"),
                             ("M019", "08:31"), ("M020", "07:02")):
            self.assertIn(runtime, self.tables["media"][mid]["description"])

    def test_every_video_work_has_source_support_and_reciprocal_links(self):
        for sid in AUDITED_VIDEO_SOURCE_FIELDS:
            source = self.tables["sources"][sid]
            for wid in source.get("workIds", []):
                self.assertIn(sid, self.tables["works"][wid]["sourceIds"])
            for song in source.get("songIds", []):
                self.assertIn(sid, self.tables["songs"][song]["sourceIds"])
            for film in source.get("filmIds", []):
                self.assertIn(sid, self.tables["films"][film]["sourceIds"])
            for mid in source.get("mediaIds", []):
                medium = self.tables["media"][mid]
                self.assertTrue(set(medium.get("workIds", [])) <= set(source.get("workIds", [])))
                for wid in medium.get("workIds", []):
                    self.assertIn(mid, self.tables["works"][wid]["mediaIds"])

    def test_modern_stage_video_is_not_a_kind_lady_film_copy(self):
        self.assertEqual(self.tables["sources"]["SRC0314"]["workIds"], ["W-S120"])
        self.assertEqual(self.tables["media"]["M009"]["workIds"], ["W-S120"])
        self.assertIn("modern staged performance", self.tables["sources"]["SRC0314"]["researchNote"])

    def test_french_moscow_nights_copy_is_not_the_english_film(self):
        for item in (self.tables["sources"]["SRC0317"], self.tables["media"]["M022"]):
            self.assertIn("W-F031", item["workIds"])
            self.assertNotIn("W-F032", item["workIds"])
        self.assertIn("feature-length", self.tables["media"]["M022"]["title"])
        self.assertIn("uncut", self.tables["sources"]["SRC0317"]["researchNote"])

    def test_video_does_not_inherit_sheet_music_publishers(self):
        for mid, oid in (("M015", "ORG033"), ("M017", "ORG036"),
                         ("M022", "ORG030"), ("M025", "ORG035"),
                         ("M028", "ORG035"), ("M412", "ORG036")):
            self.assertNotIn(oid, self.tables["media"][mid].get("organizationIds", []))
        self.assertIn("ORG033", self.tables["works"]["W-S015"]["organizationIds"])

    def test_validator_rejects_a_video_without_source_level_work_evidence(self):
        validator = ExportValidator.__new__(ExportValidator)
        validator.errors = []
        source = copy.deepcopy(self.tables["sources"]["SRC0316"])
        source["workIds"] = []
        validator.payloads = {"Sources": {"records": [source]},
                              "Media": {"records": [self.tables["media"]["M017"]]}}
        validator._validate_media_source_work_support()
        self.assertTrue(validator.errors)
        self.assertIn("W-F012", validator.errors[0])

    def test_validator_rejects_inherited_publisher_but_allows_explicit_production(self):
        validator = ExportValidator.__new__(ExportValidator)
        validator.errors = []
        medium = copy.deepcopy(self.tables["media"]["M017"])
        medium["organizationIds"] = ["ORG036"]
        validator.payloads = {
            "Media": {"records": [medium]},
            "Sources": {"records": [self.tables["sources"]["SRC0316"]]},
            "Organizations": {"records": [self.tables["organizations"]["ORG036"]]},
            "Contributions": {"records": []},
        }
        validator._validate_audio_organization_support()
        self.assertTrue(validator.errors)
        validator.errors = []
        validator.payloads["Contributions"]["records"] = [{
            "id": "TEST", "role": "production_company", "sourceIds": ["SRC0316"],
            "organizationIds": ["ORG036"],
        }]
        validator._validate_audio_organization_support()
        self.assertEqual(validator.errors, [])

    def test_contextual_and_region_limited_items_do_not_gain_new_listening_media(self):
        self.assertFalse(self.tables["sources"]["SRC0327"].get("mediaIds"))
        self.assertIn("regional", self.tables["sources"]["SRC0327"]["researchNote"])
        self.assertFalse(self.tables["media"]["M024"].get("workIds"))
        self.assertIn("not evidence for Kaper", self.tables["sources"]["SRC0555"]["researchNote"])

    def test_unavailable_bundesarchiv_record_is_not_falsely_reaccessed(self):
        source = self.tables["sources"]["SRC0683"]
        self.assertNotIn("accessDate", AUDITED_VIDEO_SOURCE_FIELDS["SRC0683"])
        # A future, genuine consultation must remain possible without a
        # normalizer restoring either the old date or this review's date.
        later = dict(source, accessDate="2026-10-27")
        self.assertEqual(normalized_source(later)["accessDate"], "2026-10-27")
        self.assertEqual((source["date"], source["dateRole"]), ("1931", "described_item"))

    def test_all_reviewed_source_metadata_is_idempotent(self):
        for sid in AUDITED_VIDEO_SOURCE_FIELDS:
            source = self.tables["sources"][sid]
            self.assertEqual(normalized_source(source), source, sid)
            stale = dict(source, dateRole="issue")
            self.assertEqual(normalized_source(stale), source, sid)


if __name__ == "__main__":
    unittest.main()
