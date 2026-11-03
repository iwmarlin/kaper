"""Listening references must not overstate identification of their source discs."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from recording_organizations import expected_audio_organization_ids


class ListeningDiscIdentificationScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        media = json.loads((ROOT / "data/public/v1/media.json").read_text())
        cls.media = {record["id"]: record for record in media["records"]}
        cls.overrides = json.loads(
            (ROOT / "scripts/public_export_overrides.json").read_text()
        )["records"]["Media"]

    def test_unidentified_discs_do_not_make_the_performances_unidentified(self):
        for media_id in ("M354", "M364"):
            with self.subTest(media_id=media_id):
                caption = self.media[media_id]["publicCaption"]
                self.assertIn("source disc", caption)
                self.assertNotIn("recording it transfers is", caption)
                self.assertEqual(self.overrides[media_id]["fields"]["publicCaption"], caption)
        self.assertIn("upload description", self.media["M364"]["publicCreditLine"])

    def test_spotify_release_is_not_asserted_to_come_from_catalogued_gloria_disc(self):
        media = self.media["M413"]
        self.assertIn("Pfau lists", media["publicCaption"])
        self.assertIn("does not identify its source disc", media["publicCaption"])
        self.assertNotIn("original issue", media["publicCreditLine"])
        self.assertNotIn("ORG138", media.get("organizationIds", []))
        for field in ("publicCaption", "publicCreditLine"):
            self.assertEqual(self.overrides["M413"]["fields"][field], media[field])
        self.assertEqual(self.overrides["M413"]["fields"]["organizationIds"], [])

    def test_rossi_date_is_attributed_to_upload_not_bnf(self):
        caption = self.media["M419"]["publicCaption"]
        self.assertIn("uploader identifies it as a Columbia recording from 1934", caption)
        self.assertIn("BnF independently catalogues", caption)
        self.assertEqual(self.overrides["M419"]["fields"]["publicCaption"], caption)

    def test_comparison_source_does_not_assign_its_label_to_spotify_release(self):
        sources = json.loads((ROOT / "data/public/v1/sources.json").read_text())
        organizations = json.loads((ROOT / "data/public/v1/organizations.json").read_text())
        contributions = json.loads((ROOT / "data/public/v1/contributions.json").read_text())
        kwargs = {
            "sources_by_id": {record["id"]: record for record in sources["records"]},
            "organizations_by_id": {record["id"]: record for record in organizations["records"]},
            "contributions": contributions["records"],
        }
        self.assertEqual(expected_audio_organization_ids(self.media["M413"], **kwargs), [])
        # The exception is scoped to this source and this medium only.
        self.assertIn("ORG138", expected_audio_organization_ids(
            {"id": "M-OTHER", "sourceIds": ["SRC0792"]}, **kwargs
        ))


if __name__ == "__main__":
    unittest.main()
