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
    "SRC0713": (None, "unknown"),
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
                self.assertEqual(source.get("date"), date)
                self.assertEqual(source["dateQualifier"], qualifier)
                self.assertIn("YouTube", source["fullCitation"])
                if source_id not in {"SRC0713", "SRC0730", "SRC0735", "SRC0746"}:
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
                if credit["id"] in {"CON-S064-P-ORG124", "CON-S064-LAB-ORG155", "CON-S076-P-ORG120", "CON-S076-LAB-ORG128", "CON-S074-P-ORG121", "CON-S074-LAB-ORG138", "CON-S033-P-ORG140", "CON-S033-LAB-ORG138"}:
                    self.assertEqual(credit["certainty"], "confirmed")
                    self.assertEqual(credit["evidenceContext"], ["recording_label"])
                    self.assertEqual(fields["scopeNote"], credit["scopeNote"])
                    continue
                if credit["id"] in {"CON-S070-P-ORG119", "CON-S070-LAB-ORG126", "CON-S070-CON-P165"}:
                    self.assertEqual(credit["certainty"], "probable" if credit["role"] == "conductor" else "confirmed")
                    self.assertEqual(credit["evidenceContext"], ["recording_label"])
                    self.assertEqual(fields["scopeNote"], credit["scopeNote"])
                    continue
                # Subsequent inspection found a readable Kristall 3098 label.
                # Only these two credits gained primary label evidence.
                if credit["id"] in {"CON-S018-P-ORG121", "CON-S018-LAB-ORG129"}:
                    self.assertEqual(credit["certainty"], "confirmed")
                    self.assertEqual(credit["evidenceContext"], ["recording_label"])
                    self.assertIn("3098", credit["scopeNote"])
                    self.assertEqual(fields["certainty"], "confirmed")
                    continue
                self.assertEqual(credit["certainty"], "probable")
                self.assertEqual(credit["evidenceContext"], ["online_recording"])
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
            self.assertEqual(credit["evidenceContext"], ["recording_label", "discography"])
            self.assertNotIn("reads only Tanz-Orchester", credit["scopeNote"])

    def test_performance_notes_distinguish_labels_discography_and_uploads(self):
        orchestra = self.credits["CON-S038-P-ORG119"]
        self.assertIn("mit Refraingesang", orchestra["scopeNote"])
        self.assertIn("instrumental", orchestra["scopeNote"])
        self.assertIn("unresolved", orchestra["scopeNote"])
        conductor = self.credits["CON-S038-CON-P165"]
        self.assertIn("not separately printed", conductor["scopeNote"])
        weber = self.credits["CON-S009-CON-P165"]
        self.assertIn("label is not shown", weber["scopeNote"])
        self.assertIn("uploader-supplied", weber["scopeNote"])
        ette = self.credits["CON-S182-P-ORG121"]
        self.assertEqual(ette["nameAsPrinted"], "Orch. Bernard Etté")
        self.assertEqual(ette["evidenceContext"], ["discography"])
        self.assertIn("not an examined disc label", ette["scopeNote"])
        moll = self.credits["CON-S049-P-P166"]
        self.assertIn("uploader identifies", moll["scopeNote"])
        gauty = self.credits["CON-S098-P-P203"]
        self.assertIn("source disc and take have not been independently established", gauty["scopeNote"])
        for credit in [orchestra, conductor, weber, ette, moll, gauty]:
            fields = self.overrides["records"]["Contributions"][credit["id"]]["fields"]
            for field, value in fields.items():
                self.assertEqual(credit[field], value, (credit["id"], field))

    def test_electrola_label_is_distinguished_from_unverified_details(self):
        source = self.sources["SRC0713"]
        self.assertEqual(source["sourceType"], "recording_discographic_source")
        self.assertEqual(source["dateRole"], "recording")
        self.assertEqual(source["dateQualifier"], "unknown")
        self.assertIsNone(source.get("date"))
        self.assertEqual(source["researchNoteType"], "discographic_note")
        self.assertIn("60-1903", source["researchNote"])
        self.assertIn("does not name the singer", source["researchNote"])
        self.assertIn("require independent verification", source["researchNote"])
        self.assertIn("E.G. 2508", source["title"])
        self.assertIn("EMI_EG02.html", source["additionalLinks"][0]["url"])
        self.assertIn("shows the Electrola E.G. 2508 label", self.media["M352"]["publicCaption"])
        self.assertEqual(normalized_source(dict(source, sourceType="online_audio_source", dateRole="issue")), source)

    def test_media_credit_lines_qualify_upload_identifications(self):
        media = [r for r in self.media.values() if set(r.get("sourceIds", [])) & set(REPORTED)]
        self.assertEqual(len(media), 8)
        for item in media:
            if item["id"] in {"M358", "M368", "M372", "M381"}:
                self.assertIn("YouTube upload", item["publicCreditLine"])
                continue
            if item["id"] == "M352":
                self.assertIn("as identified by the uploader", item["publicCreditLine"])
                self.assertIn("60-1903", item["publicCreditLine"])
                continue
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
