"""Archival object descriptions must match the inspected witnesses."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from archival_sources import REVIEWED_ARCHIVAL_FIELDS
from normalize_sources import normalized_source


class ArchivalSourceWitnessReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def records(name):
            return {r["id"]: r for r in json.loads((ROOT / "data/public/v1" /
                    (name + ".json")).read_text())["records"]}
        cls.sources, cls.media = records("sources"), records("media")
        cls.events = records("timeline-events")
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    def test_baptism_number_and_specific_scan_are_not_filename_guesses(self):
        s, m = self.sources["SRC0012"], self.media["M205"]
        self.assertIn("482", s["fullCitation"])
        self.assertIn("479–482", s["fullCitation"])
        self.assertIn("plik=479-482.jpg", s["primaryUrl"])
        self.assertEqual(m["externalUrl"], s["primaryUrl"])
        self.assertIn("adult baptism", m["publicCaption"])
        self.assertEqual(s["date"], "1920")
        self.assertEqual(self.events["TE0005"]["dateStart"], "1920-07-17")
        self.assertEqual(m["assetPath"], "assets/images/timeline/metryka-kapera-150-u-920.png")
        self.assertEqual(m["rightsStatus"], "provider_terms")

    def test_marriage_witness_is_an_index_not_a_full_act_or_foreign_registry(self):
        s = self.sources["SRC0313"]
        self.assertIn("Namensverzeichnis", s["fullCitation"])
        self.assertIn("273", s["fullCitation"])
        self.assertNotIn("foreign registry office", s["fullCitation"])
        self.assertIn("not the full marriage act", s["researchNote"])
        self.assertIn("former Berlin I district registry", s["researchNote"])
        self.assertEqual((s["date"], s["dateRole"]), ("1927-06-30", "described_item"))
        self.assertTrue(s["primaryUrl"].endswith("#page=15"))
        self.assertEqual(self.events["TE0017"]["dateStart"], "1927-06-30")
        for mid, page in (("M060", 15), ("M061", 28)):
            m = self.media[mid]
            self.assertIn("index", m["title"])
            self.assertIn("273", m["publicCaption"])
            self.assertIn(f"PDF p. {page}", m["publicCreditLine"])
            self.assertEqual(m["sourceIds"], ["SRC0313"])
            self.assertEqual(m["rightsStatus"], "public_domain")

    def test_student_file_citation_is_separate_from_aggregate_evidence_note(self):
        s = self.sources["SRC0110"]
        self.assertIn("RP 6854", s["fullCitation"])
        self.assertNotIn("religion", s["fullCitation"])
        self.assertIn("21 April 1920", s["researchNote"])
        self.assertIn("Mosaic", s["researchNote"])
        self.assertIn("38–39", s["researchNote"])
        self.assertNotIn("accessDate", s)

    def test_donor_dates_are_reporting_period_not_creation(self):
        s = self.sources["SRC0678"]
        self.assertEqual((s["date"], s["dateEnd"], s["dateRole"]),
                         ("1941-05-01", "1942-04-30", "described_item"))
        self.assertIn("donation period", s["dateDisplay"])
        self.assertIn("not a separately established creation date", s["researchNote"])
        self.assertIn("$120", s["researchNote"])
        self.assertIn("$213", s["researchNote"])
        self.assertIn("__blob=zoom", s["additionalLinks"][0]["url"])
        self.assertEqual(s["additionalLinks"][1]["url"],
                         "https://kuenste-im-exil.de/KIE/Content/DE/Themen/european-film-fund.html")

    def test_repositories_are_distinct_from_access_platforms(self):
        for sid in ("SRC0037", "SRC0038", "SRC0566"):
            self.assertEqual(self.sources[sid]["repository"],
                             "U.S. National Archives and Records Administration")
            self.assertEqual(self.sources[sid]["publication"], "National Archives Catalog")
        self.assertEqual(self.sources["SRC0009"]["repository"], "American Heritage Center, University of Wyoming")
        self.assertEqual(self.sources["SRC0009"]["publication"], "Archives West")
        self.assertEqual(self.sources["SRC0880"]["repository"], "UCLA Library, Performing Arts Special Collections")
        self.assertEqual(self.sources["SRC0880"]["publication"], "Online Archive of California")
        self.assertIn("displays one scan", self.sources["SRC0014"]["researchNote"])

    def test_normalization_and_export_preserve_all_reviewed_fields(self):
        for sid, fields in REVIEWED_ARCHIVAL_FIELDS.items():
            s = self.sources[sid]
            self.assertEqual(normalized_source(s), s)
            stale = dict(s, **{key: "legacy text" for key in fields
                               if key in {"fullCitation", "researchNote"}})
            self.assertEqual(normalized_source(stale), s)
            for key, value in fields.items():
                self.assertEqual(s[key], value)
                self.assertEqual(self.overrides["records"]["Sources"][sid]["fields"][key], value)
        for mid in ("M060", "M061", "M205"):
            fields = self.overrides["records"]["Media"][mid]["fields"]
            for key, value in fields.items():
                self.assertEqual(self.media[mid][key], value)


if __name__ == "__main__":
    unittest.main()
