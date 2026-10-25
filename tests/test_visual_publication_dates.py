"""Printed portrait dates must not silently become photography dates."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from normalize_sources import normalized_source
from visual_sources import normalize_visual_source


EXPECTED_DATES = {
    "SRC0448": "1933",
    "SRC0620": "1961",
    "SRC0403": "1933",
    "SRC0412": "1931",
    "SRC0413": "1933",
    "SRC0414": "1932",
    "SRC0573": "1912",
    "SRC0366": "1908",
    "SRC0648": "1916",
    "SRC0664": "1908",
    "SRC0752": "1945",
    "SRC0777": "1928-02-04",
    "SRC0704": "1930",
    "SRC0577": "1916-04-30",
    "SRC0619": "1932",
    "SRC0622": "1929",
    "SRC0352": "2024",
    "SRC0368": "1928",
    "SRC0812": "1912-12-07",
    "SRC0642": "1922-12",
    "SRC0649": "1930",
    "SRC0650": "1955-07",
    "SRC0651": "1937",
    "SRC0652": "1937",
    "SRC0653": "1937",
    "SRC0654": "1941-07-20",
    "SRC0661": "1930-07-17",
    "SRC0778": "1920-05-01",
    "SRC0813": "1929-06-19",
}


class VisualPublicationDatesTests(unittest.TestCase):
    def test_portrait_decades_are_not_confirmed_single_years(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        by_id = {record["id"]: record for record in records}
        for source_id, start, end, display in [("SRC0596", "1950", "1959", "1950s"),
                                               ("SRC0608", "1930", "1939", "1930s")]:
            with self.subTest(source=source_id):
                source = by_id[source_id]
                self.assertEqual((source["date"], source["dateEnd"], source["dateDisplay"]), (start, end, display))
                self.assertEqual(source["dateQualifier"], "approximate")
                changed = dict(source, dateQualifier="confirmed")
                changed.pop("dateEnd")
                changed.pop("dateDisplay")
                self.assertEqual(normalized_source(changed), source)

    def test_koster_publisher_is_not_assigned_as_photographer(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        source = next(record for record in records if record["id"] == "SRC0620")
        self.assertEqual(source["creator"], "Photographer unidentified")
        self.assertEqual(source["publication"], "Universal-International")
        self.assertIn("published by Universal-International in 1961", source["fullCitation"])
        self.assertEqual(normalized_source(dict(source, creator="Universal-International")), source)

    def test_schlechter_note_does_not_claim_an_assigned_decade(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        source = next(record for record in records if record["id"] == "SRC0839")
        self.assertNotIn("date", source)
        self.assertEqual(source["dateQualifier"], "unknown")
        self.assertIn("The date remains unknown", source["researchNote"])
        self.assertNotIn("dated here by decade", source["researchNote"])

    def test_madame_programme_identifies_the_original_publication(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        source = next(record for record in records if record["id"] == "SRC0448")
        self.assertEqual(source["publication"], "Illustrierter Film-Kurier")
        self.assertEqual(source["repository"], "English Wikipedia")
        self.assertIn("Illustrierter Film-Kurier cover", source["title"])

    def test_wikipedia_file_host_preserves_original_publication_and_date_role(self):
        source = {"id": "TEST", "primaryUrl": "https://en.wikipedia.org/wiki/File:Example.jpg",
                  "sourceType": "image_or_photograph", "publication": "Original programme",
                  "dateRole": "publication"}
        normalize_visual_source(source)
        self.assertEqual(source["repository"], "English Wikipedia")
        self.assertEqual(source["publication"], "Original programme")
        self.assertEqual(source["dateRole"], "publication")
        unknown = {"id": "TEST", "primaryUrl": source["primaryUrl"]}
        normalize_visual_source(unknown)
        self.assertNotIn("publication", unknown)
        self.assertNotIn("dateRole", unknown)

    def test_programme_covers_separate_publication_from_access_platform(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        by_id = {record["id"]: record for record in records}
        for source_id, number in [("SRC0403", "677"), ("SRC0412", "214"),
                                  ("SRC0413", "1946"), ("SRC0414", "524")]:
            with self.subTest(source=source_id):
                source = by_id[source_id]
                self.assertEqual(source["publication"], "Illustrierter Film-Kurier, no. " + number)
                self.assertEqual(source["repository"], "English Wikipedia")
                self.assertEqual(normalized_source(dict(source, publication="English Wikipedia", dateRole="creation")), source)

    def test_varna_collection_year_is_not_a_portrait_creation_date(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        source = next(record for record in records if record["id"] == "SRC0593")
        self.assertEqual(source["dateRole"], "described_item")
        self.assertEqual(source["dateDisplay"], "1937 (revue documentation)")
        self.assertIn("not an independently established date", source["researchNote"])
        self.assertEqual(normalized_source(dict(source, dateRole="creation")), source)

    def test_bluethner_notice_reported_date_stays_qualified(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        source = next(record for record in records if record["id"] == "SRC0573")
        self.assertEqual(source["dateQualifier"], "reported")
        self.assertEqual(source["dateDisplay"], "1912 (reported)")
        media = json.loads((ROOT / "data/public/v1/media.json").read_text())["records"]
        image = next(record for record in media if record["id"] == "M276")
        self.assertIn("(reported)", image["title"])
        self.assertIn("not independently established", image["publicCaption"])
        self.assertIn("grammophon-platten.de", image["publicCaption"])

    def test_jones_issuing_agency_is_not_the_photographer(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        source = next(record for record in records if record["id"] == "SRC0752")
        self.assertEqual(source["creator"], "Photographer unidentified")
        self.assertEqual(source["publication"], "Frederick Brothers Agency")
        self.assertIn("23 April 1945", source["fullCitation"])
        self.assertIn("Photographer not credited", source["fullCitation"])
        self.assertEqual(normalized_source(dict(source, creator="Frederick Brothers Agency", dateRole="creation")), source)

    def test_lubitsch_metadata_year_is_not_an_established_photography_date(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        source = next(record for record in records if record["id"] == "SRC0537")
        self.assertNotIn("date", source)
        self.assertEqual(source["dateQualifier"], "unknown")
        self.assertIn("1949", source["researchNote"])
        self.assertIn("1947", source["researchNote"])
        self.assertIn("27 September 2018", source["researchNote"])
        self.assertNotIn("1949", source["fullCitation"])
        self.assertEqual(normalized_source(dict(source, date="1949", dateQualifier="confirmed")), source)

    def test_tchaikovsky_attribution_remains_qualified_in_creator_field(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        source = next(record for record in records if record["id"] == "SRC0840")
        self.assertEqual(source["creator"], "Attributed to Émile Reutlinger")
        self.assertEqual(normalized_source(dict(source, creator="Émile Reutlinger")), source)

    def test_graben_postcard_date_represents_use_not_creation(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        source = next(record for record in records if record["id"] == "SRC0439")
        self.assertEqual(source["date"], "1922")
        self.assertEqual(source["dateRole"], "described_item")
        self.assertEqual(source["dateDisplay"], "1922 (use)")
        self.assertIn("1922 (Gebrauch)", source["researchNote"])
        self.assertEqual(normalized_source(dict(source, dateRole="creation")), source)
        media = json.loads((ROOT / "data/public/v1/media.json").read_text())["records"]
        postcard = next(record for record in media if record["id"] == "M095")
        self.assertIn("used in 1922", postcard["title"])
        self.assertIn("used in 1922", postcard["publicCaption"])

    def test_badet_programme_retains_performance_date_without_redating_portrait(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        source = next(record for record in records if record["id"] == "SRC0618")
        self.assertEqual(source["date"], "1941-10-04")
        self.assertEqual(source["dateRole"], "described_item")
        self.assertEqual(source["dateDisplay"], "4 October 1941 (performance)")
        self.assertIn("not an established creation date", source["researchNote"])
        changed = dict(source, dateRole="creation")
        self.assertEqual(normalized_source(changed), source)

    def test_grothe_card_keeps_approximate_decade_and_qualified_note(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        source = next(record for record in records if record["id"] == "SRC0704")
        self.assertEqual(source["dateRole"], "publication")
        self.assertEqual(source["date"], "1930")
        self.assertEqual(source["dateEnd"], "1939")
        self.assertEqual(source["dateQualifier"], "approximate")
        self.assertEqual(source["dateDisplay"], "1930s")
        self.assertIn("not to the underlying photograph", source["researchNote"])
        self.assertIn("card 215", source["additionalLinks"][0]["label"])

    def test_export_corrects_roles_without_changing_dates(self):
        records = json.loads((ROOT / "data/public/v1/sources.json").read_text())["records"]
        by_id = {record["id"]: record for record in records}
        for source_id, expected_date in EXPECTED_DATES.items():
            with self.subTest(source=source_id):
                record = dict(by_id[source_id])
                self.assertEqual(record["dateRole"], "publication")
                self.assertEqual(record["date"], expected_date)
                record["dateRole"] = "creation"
                normalized = normalized_source(record)
                self.assertEqual(normalized["dateRole"], "publication")
                self.assertEqual(normalized["date"], expected_date)
                self.assertEqual(normalized_source(normalized), normalized)

    def test_other_documented_creation_dates_are_preserved(self):
        record = {"id": "SRC0795", "sourceType": "archival_photograph", "date": "1929", "dateRole": "creation"}
        normalize_visual_source(record)
        self.assertEqual(record["dateRole"], "creation")
        self.assertEqual(record["date"], "1929")


if __name__ == "__main__":
    unittest.main()
