import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_public_export import (  # noqa: E402
    CLEARED_RIGHTS_STATUSES,
    MEDIA_RIGHTS_STATUSES,
    ExportValidator,
)


def load_media():
    payload = json.loads((ROOT / "data/public/v1/media.json").read_text(encoding="utf-8"))
    return payload["records"]


class MediaRightsStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.media = load_media()
        self.core = (ROOT / "assets/site/core.js").read_text(encoding="utf-8")
        self.gallery = (ROOT / "assets/site/gallery.js").read_text(encoding="utf-8")

    def test_every_medium_uses_a_named_rights_basis(self) -> None:
        for medium in self.media:
            with self.subTest(media_id=medium["id"]):
                self.assertIn(medium["rightsStatus"], MEDIA_RIGHTS_STATUSES)

    def test_every_status_has_a_public_label(self) -> None:
        block = re.search(r"const RIGHTS_LABELS = Object\.freeze\(\{(.*?)\}\);", self.core, re.S)
        labelled = set(re.findall(r"^\s*(\w+):", block.group(1), re.M))
        self.assertEqual(MEDIA_RIGHTS_STATUSES, labelled)

    def test_label_does_not_depend_on_the_note_for_cleared_media(self) -> None:
        body = re.search(r"export function rightsLabel\(.*?\n\}", self.core, re.S).group(0)
        for status in CLEARED_RIGHTS_STATUSES:
            self.assertNotIn(f'key === "{status}"', body)

    def test_gallery_rights_filter_is_built_from_every_status(self) -> None:
        order = re.search(r"const RIGHTS_ORDER = \[(.*?)\];", self.gallery, re.S).group(1)
        self.assertEqual(MEDIA_RIGHTS_STATUSES, set(re.findall(r'"(\w+)"', order)))
        page = (ROOT / "media.html").read_text(encoding="utf-8")
        select = re.search(r'<select id="media-rights">(.*?)</select>', page, re.S).group(1)
        self.assertEqual(re.findall(r'value="([^"]*)"', select), [""])

    def test_validator_rejects_the_retired_catch_all_status(self) -> None:
        validator = object.__new__(ExportValidator)
        validator.errors = []
        validator.warnings = []
        validator.assets_root = None
        validator.config = {"mediaExceptions": {}}
        validator.payloads = {"Media": {"records": [{
            "id": "MTEST",
            "mediaType": "image",
            "storageType": "external",
            "galleryStatus": "external_link_only",
            "externalUrl": "https://example.org/image",
            "sourceIds": ["SRCTEST"],
            "rightsStatus": "ok",
            "rightsNote": "Public domain.",
            "publicCreditLine": "Example.",
        }]}}

        validator._validate_media()

        self.assertIn("Media MTEST: unknown rightsStatus 'ok'", validator.errors)


if __name__ == "__main__":
    unittest.main()
