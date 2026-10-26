"""Keep catalogue, photographed label and digital-transfer evidence distinct."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source


class PrimaryLabelReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = {
            name: {r["id"]: r for r in json.loads(
                (ROOT / f"data/public/v1/{name}.json").read_text())["records"]}
            for name in ("sources", "media", "contributions", "works", "songs")
        }

    def test_catalogue_does_not_supply_unprinted_lyricist_or_publisher(self):
        source = self.tables["sources"]["SRC0001"]
        for cid in ("CON-S002-L-P003", "CON-S002-PUB-ORG034"):
            self.assertNotIn(cid, source["contributionIds"])
            self.assertNotIn("SRC0001", self.tables["contributions"][cid]["sourceIds"])
            self.assertIn("SRC0054", self.tables["contributions"][cid]["sourceIds"])

    def test_coupled_catalogue_sides_have_reciprocal_song_links(self):
        source = self.tables["sources"]["SRC0001"]
        for wid, sid in (("W-S001", "S001"), ("W-S002", "S002")):
            self.assertIn(wid, source["workIds"])
            self.assertIn(sid, source["songIds"])
            self.assertIn("SRC0001", self.tables["works"][wid]["sourceIds"])
            self.assertIn("SRC0001", self.tables["songs"][sid]["sourceIds"])

    def test_syrena_side_number_is_not_automatically_a_verified_matrix(self):
        for sid in ("SRC0001", "SRC0736", "SRC0737"):
            source = self.tables["sources"][sid]
            self.assertEqual(source["dateQualifier"], "reported")
            self.assertNotIn("matrix 179", source["fullCitation"])
            self.assertIn("matrix", source["researchNote"])
        self.assertEqual(self.tables["media"]["M001"]["sourceIds"],
                         ["SRC0001", "SRC0737"])

    def test_label_confirms_wiehler_credit_on_the_transfer(self):
        cid = "CON-S002-CON-P169"
        self.assertIn(cid, self.tables["sources"]["SRC0737"]["contributionIds"])
        self.assertIn("SRC0737", self.tables["contributions"][cid]["sourceIds"])

    def test_unknown_issue_dates_do_not_inherit_song_or_upload_years(self):
        for sid in ("SRC0002", "SRC0493", "SRC0553"):
            source = self.tables["sources"][sid]
            self.assertEqual((source["dateRole"], source["dateQualifier"]),
                             ("issue", "unknown"))
            self.assertNotIn("date", source)
            self.assertNotIn("dateDisplay", source)

    def test_livschakoff_year_is_a_reported_session_not_an_issue(self):
        source = self.tables["sources"]["SRC0003"]
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1930", "recording", "reported"))

    def test_silvester_label_does_not_support_feist_or_kahn(self):
        source = self.tables["sources"]["SRC0007"]
        self.assertEqual(source["dateQualifier"], "reported")
        for cid in ("CON-S133-L-P025", "CON-S133-PUB-ORG040"):
            self.assertNotIn(cid, source["contributionIds"])
            self.assertNotIn("SRC0007", self.tables["contributions"][cid]["sourceIds"])
            self.assertIn("SRC0254", self.tables["contributions"][cid]["sourceIds"])

    def test_adler_documents_both_sides_without_gloria_or_youtube(self):
        source = self.tables["sources"]["SRC0493"]
        self.assertEqual(source["repository"], "Discogs")
        self.assertEqual(source["publication"], "Adler Electro")
        self.assertNotIn("ORG093", source["organizationIds"])
        for wid, sid in (("W-S038", "S038"), ("W-S039", "S039")):
            self.assertIn(wid, source["workIds"])
            self.assertIn(sid, source["songIds"])
            self.assertIn("SRC0493", self.tables["works"][wid]["sourceIds"])
            self.assertIn("SRC0493", self.tables["songs"][sid]["sourceIds"])
        for cid in ("CON-S038-C-P009", "CON-S038-C-P105", "CON-S038-L-P020"):
            self.assertIn(cid, source["contributionIds"])
            self.assertIn("SRC0493", self.tables["contributions"][cid]["sourceIds"])

    def test_label_still_remains_an_image_not_a_new_listening_reference(self):
        source = self.tables["sources"]["SRC0553"]
        self.assertEqual(source["sourceType"], "recording_discographic_source")
        self.assertEqual(source["mediaIds"], ["M231"])
        self.assertEqual(self.tables["media"]["M231"]["mediaType"], "image")
        self.assertEqual(self.tables["media"]["M231"]["storageType"], "local")

    def test_arno_upload_does_not_identify_a_unique_take(self):
        source = self.tables["sources"]["SRC0745"]
        self.assertIn("does not identify the pressing or take", source["researchNote"])
        self.assertNotIn("records a single", source["researchNote"])
        media = self.tables["media"]["M380"]
        self.assertIn("transferred copy is unverified", media["publicCreditLine"])

    def test_reviewed_sources_are_idempotent_and_stale_dates_are_removed(self):
        for sid in ("SRC0001", "SRC0002", "SRC0003", "SRC0007", "SRC0493",
                    "SRC0553", "SRC0736", "SRC0737", "SRC0745"):
            source = self.tables["sources"][sid]
            self.assertEqual(normalized_source(source), source, sid)
        for sid in ("SRC0002", "SRC0493", "SRC0553"):
            stale = dict(self.tables["sources"][sid], date="1931", dateDisplay="1931")
            self.assertNotIn("date", normalized_source(stale))
            self.assertNotIn("dateDisplay", normalized_source(stale))


if __name__ == "__main__":
    unittest.main()
