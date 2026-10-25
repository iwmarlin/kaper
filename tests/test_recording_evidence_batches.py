"""Keep private uploads, official reissues and discography as distinct evidence."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source

REPORTED = {
    "SRC0713": "1932", "SRC0719": "1932", "SRC0729": "1935",
    "SRC0730": "1933", "SRC0735": "1933", "SRC0746": "1932",
    "SRC0755": "1932", "SRC0758": "1930",
}
# The original upload batch remains the scope for its credit-edge checks.
# Later individual verification can refine dates without confirming those edges.
REVIEWED_DATES = {
    "SRC0719": ("1932-05", "reported"),
    "SRC0729": ("1935-05-06", "confirmed"),
    "SRC0755": ("1932-03", "reported"),
}
REISSUE_CREDITS = [
    "CON-S084-P-P164", "CON-S084-CON-P165", "CON-S084-P-ORG119",
    "CON-S058-P-P164", "CON-S058-CON-P165", "CON-S058-P-ORG119",
    "CON-S025-P-ORG125",
]
PUBLISHER_EDGES = {
    "SRC0708": ("CON-S038-PUB-ORG031", ["SRC0093"]),
    "SRC0746": ("CON-S033-PUB-ORG031", ["SRC0184"]),
    "SRC0755": ("CON-S067-PUB-ORG029", ["SRC0105"]),
    "SRC0758": ("CON-S018-PUB-ORG033", ["SRC0204", "SRC0471"]),
}


class RecordingEvidenceBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = cls.load("sources")
        cls.credits = cls.load("contributions")
        cls.media = cls.load("media")
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    @staticmethod
    def load(table):
        return {r["id"]: r for r in json.loads((ROOT / f"data/public/v1/{table}.json").read_text())["records"]}

    def test_upload_dates_preserve_qualifications_or_individual_verification(self):
        for source_id, year in REPORTED.items():
            with self.subTest(source=source_id):
                source = self.sources[source_id]
                date, qualifier = REVIEWED_DATES.get(source_id, (year, "reported"))
                self.assertEqual(source["date"], date)
                self.assertEqual(source["dateQualifier"], qualifier)
                self.assertIn("YouTube", source["fullCitation"])
                self.assertNotIn("label credits", source["fullCitation"])
                self.assertEqual(normalized_source(dict(source, dateQualifier="confirmed", fullCitation="Old citation")), source)

    def test_seven_official_reissue_credits_remain_confirmed(self):
        for credit_id in REISSUE_CREDITS:
            with self.subTest(credit=credit_id):
                credit = self.credits[credit_id]
                self.assertEqual(credit["certainty"], "confirmed")
                self.assertEqual(credit["evidenceContext"], ["online_recording"])
                self.assertIn("reissue", credit["scopeNote"])
        for source_id in ["SRC0701", "SRC0702"]:
            self.assertEqual(self.sources[source_id]["dateQualifier"], "confirmed")
            self.assertEqual(self.sources[source_id]["dateRole"], "digital_publication")
        # Retrieval's 2000 date is the compilation's first issue on CD,
        # not the date of the later YouTube art track.
        self.assertEqual(self.sources["SRC0714"]["dateQualifier"], "confirmed")
        self.assertEqual(self.sources["SRC0714"]["dateRole"], "issue")

    def test_sole_upload_credits_are_qualified_unless_label_now_verified(self):
        credits = [r for r in self.credits.values()
                   if len(r.get("sourceIds", [])) == 1 and r["sourceIds"][0] in REPORTED]
        self.assertEqual(len(credits), 16)
        for credit in credits:
            with self.subTest(credit=credit["id"]):
                fields = self.overrides["records"]["Contributions"][credit["id"]]["fields"]
                # Subsequent inspection found a readable Kristall 3098 label.
                # Only these two credits gained primary label evidence.
                if credit["id"] in {"CON-S018-P-ORG121", "CON-S018-LAB-ORG129"}:
                    self.assertEqual(credit["certainty"], "confirmed")
                    self.assertEqual(credit["evidenceContext"], ["recording_label"])
                    self.assertIn("3098", credit["scopeNote"])
                    self.assertEqual(fields["certainty"], "confirmed")
                    continue
                self.assertEqual(credit["certainty"], "probable")
                self.assertEqual(credit["evidenceContext"], ["online_catalogue"])
                self.assertIn("uploader-level", credit["scopeNote"])
                self.assertEqual(fields["certainty"], "probable")

    def test_four_publisher_edges_are_removed_in_both_directions(self):
        for source_id, (credit_id, independent_sources) in PUBLISHER_EDGES.items():
            with self.subTest(source=source_id):
                credit = self.credits[credit_id]
                self.assertEqual(credit["sourceIds"], independent_sources)
                self.assertEqual(credit["certainty"], "confirmed")
                self.assertNotIn(credit_id, self.sources[source_id]["contributionIds"])
                removals = self.overrides["linkRemovals"]
                self.assertIn(source_id, removals["Contributions"][credit_id]["fields"]["sourceIds"])
                self.assertIn(credit_id, removals["Sources"][source_id]["fields"]["contributionIds"])

    def test_independent_electrola_discography_is_not_downgraded(self):
        self.assertEqual(self.sources["SRC0708"]["dateQualifier"], "confirmed")
        for credit_id in ["CON-S038-CON-P165", "CON-S038-P-ORG119"]:
            credit = self.credits[credit_id]
            self.assertEqual(credit["certainty"], "confirmed")
            self.assertEqual(credit["evidenceContext"], ["discography"])
            self.assertNotIn("reads only Tanz-Orchester", credit["scopeNote"])

    def test_conflicting_electrola_number_is_not_a_verified_disc_identity(self):
        source = self.sources["SRC0713"]
        self.assertEqual(source["sourceType"], "online_audio_source")
        self.assertEqual(source["dateRole"], "recording")
        self.assertEqual(source["researchNoteType"], "identity_assessment")
        self.assertIn("Spanischer Zigeunertanz", source["researchNote"])
        self.assertIn("Die alte Spieluhr", source["researchNote"])
        self.assertNotIn("E.G. 2508", source["title"])
        self.assertIn("EMI_EG02.html", source["additionalLinks"][0]["url"])
        self.assertIn("conflicts with", self.media["M352"]["publicCaption"])
        self.assertEqual(normalized_source(dict(source, sourceType="recording_discographic_source", dateRole="issue")), source)

    def test_media_credit_lines_qualify_upload_identifications(self):
        media = [r for r in self.media.values() if set(r.get("sourceIds", [])) & set(REPORTED)]
        self.assertEqual(len(media), 8)
        for item in media:
            if item["id"] == "M392":
                self.assertIn("Kristall 3098", item["publicCreditLine"])
                self.assertNotIn("as identified in the upload description", item["publicCreditLine"])
                continue
            self.assertIn("as identified in the upload description", item["publicCreditLine"])

    def test_neighbouring_credits_are_not_modified_by_similar_field_layouts(self):
        # S080 was subsequently reviewed individually: its conductor is named
        # by the uploader, not on a consulted label of this performance.
        for credit_id in ["CON-S042-P-ORG119"]:
            credit = self.credits[credit_id]
            self.assertEqual(credit["evidenceContext"], ["recording_label"])
            self.assertEqual(credit["certainty"], "confirmed")
        self.assertEqual(self.credits["CON-S018-L-P020"]["sourceIds"],
                         ["SRC0204", "SRC0471", "SRC0758"])


if __name__ == "__main__":
    unittest.main()
