"""Withdraw only SRC0638; keep the hotel, media and independent evidence."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WithdrawnMexicaliSourceTests(unittest.TestCase):
    def test_source_withdrawal_preserves_hotel_and_independent_witnesses(self):
        def records(name):
            return {r["id"]: r for r in json.loads((ROOT / "data/public/v1" /
                    (name + ".json")).read_text())["records"]}
        sources, places, media = records("sources"), records("places"), records("media")
        self.assertNotIn("SRC0638", sources)
        place = places["PL039"]
        self.assertEqual(place["sourceIds"], ["SRC0039", "SRC0637", "SRC0639", "SRC0640"])
        self.assertEqual(place["mediaIds"], ["M287", "M124"])
        self.assertEqual(place["timelineEventIds"], ["TE0036"])
        self.assertEqual((place["latitude"], place["longitude"]), (32.66450519, -115.49328652))
        self.assertEqual(place["publicScope"], "map_and_detail")
        self.assertNotIn("301", place["publicNote"])
        for sid in place["sourceIds"]:
            self.assertIn("PL039", sources[sid]["placeIds"])
        for mid in place["mediaIds"]:
            self.assertIn(mid, media)
        for path in (ROOT / "data/public/v1").glob("*.json"):
            payload = json.loads(path.read_text())
            for rec in payload.get("records", []):
                self.assertNotIn("SRC0638", rec.get("sourceIds", []), str(path))
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        self.assertIn("SRC0638", overrides["exclusions"]["Sources"])
        self.assertNotIn("SRC0638", overrides["additions"]["Sources"])
        fields = overrides["records"]["Places"]["PL039"]["fields"]
        self.assertEqual(fields["sourceIds"], place["sourceIds"])
        self.assertEqual(fields["publicNote"], place["publicNote"])

    def test_withdrawn_source_has_no_generated_card_or_payload(self):
        self.assertFalse((ROOT / "records/source/SRC0638").exists())
        self.assertFalse((ROOT / "data/site/records/source/SRC0638.json").exists())
        self.assertTrue((ROOT / "records/place/PL039/index.html").is_file())


if __name__ == "__main__":
    unittest.main()
