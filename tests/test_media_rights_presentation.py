"""Where media with uncleared rights may appear, and at what size.

docs/media-rights-audit.md, findings 5 to 7: restricted, undetermined and
mixed-rights media stay on the records that document them, at no more than
800 px on the long side, and are never featured on the home page, in the
chronology, in a gallery or as a link-preview image.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
SITE = ROOT / "data/site"

FEATURABLE = {"public_domain", "open_licence", "provider_terms", "permission_granted", "own_work"}
UNCLEARED = {"restricted", "copyright_undetermined", "mixed_rights", "permission_needed_or_fair_use_claimed"}
CAP = 800


def media() -> dict[str, dict]:
    payload = json.loads((PUBLIC / "media.json").read_text(encoding="utf-8"))
    return {record["id"]: record for record in payload["records"]}


class MediaRightsPresentationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.media = media()

    def test_uncleared_local_images_are_reduced(self) -> None:
        for item in self.media.values():
            if item.get("mediaType") == "document_gallery" or item.get("rightsStatus") not in UNCLEARED:
                continue
            for asset in dict.fromkeys(item.get("assetPaths") or [item.get("assetPath")]):
                if not asset or not asset.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                with self.subTest(media=item["id"], asset=asset):
                    with Image.open(ROOT / asset) as image:
                        self.assertLessEqual(max(image.size), CAP)

    def test_galleries_gather_only_featurable_members(self) -> None:
        for item in self.media.values():
            for member in item.get("galleryMemberIds") or []:
                with self.subTest(gallery=item["id"], member=member):
                    self.assertIn(self.media[member]["rightsStatus"], FEATURABLE)

    def test_home_cards_feature_only_cleared_images(self) -> None:
        home = json.loads((SITE / "home.json").read_text(encoding="utf-8"))
        for event in home["events"]:
            image = event.get("image")
            if image:
                with self.subTest(event=event["id"]):
                    self.assertIn(self.media[image["id"]]["rightsStatus"], FEATURABLE)

    def test_chronology_features_only_cleared_images(self) -> None:
        timeline = json.loads((SITE / "indexes/timeline.json").read_text(encoding="utf-8"))
        for event in timeline["records"]:
            hero = event.get("hero")
            if hero:
                with self.subTest(event=event["id"]):
                    self.assertIn(self.media[hero["id"]]["rightsStatus"], FEATURABLE)

    def test_kaper_music_pages_are_not_presented_as_public_domain(self) -> None:
        for media_id in ("M125", "M126", "M206"):
            with self.subTest(media=media_id):
                self.assertEqual(self.media[media_id]["rightsStatus"], "mixed_rights")
                self.assertEqual(self.media[media_id]["galleryStatus"], "detail_only")
                self.assertIn("2053", self.media[media_id]["rightsNote"])
        for media_id in ("M199", "M200"):
            with self.subTest(media=media_id):
                self.assertIn("cover", self.media[media_id]["rightsNote"])
                self.assertIn(media_id, self.media["M035"]["galleryMemberIds"])


if __name__ == "__main__":
    unittest.main()
