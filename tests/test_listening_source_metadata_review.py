"""Twelve reviewed references must distinguish performances, carriers and uploads."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source
from recording_sources import RECORDING_FIELDS

PAIRS = {
    "SRC0314": "M009", "SRC0693": "M334", "SRC0761": "M394",
    "SRC0762": "M007", "SRC0763": "M373", "SRC0764": "M374",
    "SRC0765": "M397", "SRC0766": "M398", "SRC0796": "M416",
    "SRC0797": "M417", "SRC0808": "M423", "SRC0883": "M450",
}


class ListeningSourceMetadataReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for table in ("sources", "media", "contributions", "works", "songs", "organizations"):
            rows = json.loads((ROOT / "data/public/v1" / f"{table}.json").read_text())["records"]
            setattr(cls, table, {r["id"]: r for r in rows})
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    def test_modern_stage_performance_is_video_not_an_anonymous_1935_recording(self):
        source, medium = self.sources["SRC0314"], self.media["M009"]
        self.assertEqual(source["sourceType"], "online_video_source")
        self.assertEqual(medium["mediaType"], "video")
        self.assertEqual(source["date"], "2019-03-29")
        self.assertIn("Christoph Wagner-Trenkwitz", source["fullCitation"])
        self.assertIn("2014", source["researchNote"])
        self.assertIn("not a historical film excerpt", source["researchNote"])
        self.assertNotIn("does not identify the performers", medium["description"])

    def test_modern_performance_has_reciprocal_work_and_song_links(self):
        self.assertEqual(self.sources["SRC0314"]["workIds"], ["W-S120"])
        self.assertEqual(self.sources["SRC0314"]["songIds"], ["S120"])
        self.assertIn("SRC0314", self.works["W-S120"]["sourceIds"])
        self.assertIn("SRC0314", self.songs["S120"]["sourceIds"])

    def test_digital_issue_dates_are_not_later_youtube_publication_dates(self):
        for sid, issue, upload in (
            ("SRC0693", "2013-07-02", "11 February 2015"),
            ("SRC0762", "2012-06-13", "20 November 2014"),
            ("SRC0796", "2013-02-05", "11 February 2015"),
            ("SRC0797", "2013-02-05", "11 February 2015"),
            ("SRC0808", "2008-07-10", "19 January 2015"),
        ):
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                                 (issue, "digital_publication", "confirmed"))
                self.assertIn(upload, source["researchNote"])
                self.assertRegex(source["researchNote"],
                                 r"no (?:historical|original)|does not identify an original")
                self.assertIn("matrix", source["researchNote"])

    def test_private_upload_dates_do_not_date_historical_sessions(self):
        for sid, date in (("SRC0763", "2007-12-10"), ("SRC0765", "2018-09-27"),
                          ("SRC0766", "2016-05-01"), ("SRC0883", "2011-08-15")):
            source = self.sources[sid]
            self.assertEqual((source["date"], source["dateRole"]), (date, "digital_publication"))
            self.assertEqual(source["sourceType"], "online_audio_source")
        self.assertIn("does not independently date", self.sources["SRC0763"]["researchNote"])
        self.assertIn("has not been matched", self.media["M397"]["publicCaption"])

    def test_polish_signorina_is_identified_by_the_visible_label(self):
        source = self.sources["SRC0761"]
        self.assertEqual(source["sourceType"], "recording_discographic_source")
        self.assertEqual(source["dateQualifier"], "unknown")
        self.assertNotIn("date", source)
        for text in ("O.236842 b", "137013", "M. Halicz", "Polish"):
            self.assertIn(text, source["fullCitation"])
        self.assertIn("SRC0633", source["researchNote"])
        self.assertIn("O.236842 b", self.media["M394"]["publicCreditLine"])

    def test_salabert_label_does_not_prove_an_exact_issue_date_or_same_copy(self):
        source = self.sources["SRC0764"]
        self.assertEqual(source["sourceType"], "recording_discographic_source")
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1933-10-03", "described_item", "reported"))
        self.assertIn("S.S.1728", source["fullCitation"])
        self.assertIn("[1934]", source["researchNote"])
        self.assertIn("same physical pressing", source["researchNote"])
        self.assertIn("Éditions Echo", source["researchNote"])

    def test_eleven_label_credits_and_label_organizations_are_linked_both_ways(self):
        for sid, oid, mid in (("SRC0761", "ORG150", "M394"),
                              ("SRC0764", "ORG039", "M374")):
            source = self.sources[sid]
            for cid in source["contributionIds"]:
                credit = self.contributions[cid]
                self.assertIn(sid, credit["sourceIds"])
                self.assertIn("recording_label", credit["evidenceContext"])
                self.assertIn(sid, self.overrides["linkAdditions"]["Contributions"][cid]["fields"]["sourceIds"])
            self.assertIn(oid, source["organizationIds"])
            self.assertIn(sid, self.organizations[oid]["sourceIds"])
            self.assertIn(oid, self.media[mid]["organizationIds"])
            # The established schema stores Media -> Organizations only;
            # Organization.mediaIds is not an allowed canonical field.
            self.assertNotIn("mediaIds", self.organizations[oid])
        self.assertEqual(sum(len(self.sources[sid]["contributionIds"])
                             for sid in ("SRC0761", "SRC0764")), 11)
        self.assertIn("not the order of names alone", self.sources["SRC0761"]["researchNote"])
        # O.236842 also couples Ninon (S214), but the inspected photo is only
        # Signorina (S215). Identical neighbouring fields must not shift links.
        for cid in ("CON-S214-C-P009", "CON-S214-C-P077", "CON-S214-L-P156",
                    "CON-S214-P-P117", "CON-S214-LAB-ORG128"):
            self.assertNotIn("SRC0761", self.contributions[cid]["sourceIds"])

    def test_dobbri_and_gauty_uploads_do_not_gain_unverified_master_identifications(self):
        source = self.sources["SRC0766"]
        self.assertIn("not independently transcribed", source["researchNote"])
        self.assertNotIn("B 4502", source["fullCitation"])
        credit = self.contributions["CON-S008-P-ORG134"]
        self.assertEqual(credit["certainty"], "probable")
        self.assertEqual(credit["evidenceContext"], ["online_catalogue"])
        self.assertIn("1444 WPP", self.sources["SRC0883"]["researchNote"])
        self.assertNotIn("522987", self.sources["SRC0883"]["fullCitation"])

    def test_all_twelve_media_keep_external_rights_and_their_access_sources(self):
        for sid, mid in PAIRS.items():
            with self.subTest(source=sid):
                source, medium = self.sources[sid], self.media[mid]
                self.assertIn(sid, medium["sourceIds"])
                self.assertEqual(medium["externalUrl"], source["primaryUrl"])
                self.assertEqual(medium["storageType"], "external")
                self.assertEqual(medium["rightsStatus"], "external_content_not_rehosted")
                self.assertTrue(source["researchNote"])

    def test_metadata_normalization_preserves_review_without_freezing_graph_links(self):
        for sid in PAIRS:
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual(normalized_source(source), source)
                self.assertEqual(normalized_source(dict(source, fullCitation="Old citation",
                                                        researchNote="Old note", date="1930")), source)
                self.assertFalse(set(RECORDING_FIELDS[sid]) &
                                 {"workIds", "songIds", "contributionIds", "organizationIds"})
                extended = dict(source, workIds=source.get("workIds", []) + ["W-FUTURE"])
                self.assertIn("W-FUTURE", normalized_source(extended)["workIds"])
                self.assertEqual(self.overrides["records"]["Sources"][sid]["fields"]["researchNote"],
                                 source["researchNote"])
