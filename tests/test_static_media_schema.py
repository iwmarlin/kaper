from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_static_records import media_schema_type, structured_data  # noqa: E402


class StaticMediaSchemaTests(unittest.TestCase):
    def test_controlled_media_types_have_distinct_schema_classes(self) -> None:
        expected = {
            "audio": "AudioObject",
            "video": "VideoObject",
            "image": "ImageObject",
            "sheet music": "ImageObject",
            "document_gallery": "CollectionPage",
        }
        for media_type, schema_type in expected.items():
            with self.subTest(media_type=media_type):
                self.assertEqual(
                    media_schema_type({"mediaType": media_type}), schema_type
                )

    def test_external_audio_uses_audio_object_and_same_as(self) -> None:
        markup = structured_data(
            "media",
            {
                "id": "MTEST",
                "mediaType": "audio",
                "externalUrl": "https://example.org/listen",
            },
            "https://example.org/records/media/MTEST/",
            "Listening reference",
            "A documented recording.",
        )
        payload = json.loads(markup.split(">", 1)[1].rsplit("<", 1)[0])
        self.assertEqual(payload["@type"], "AudioObject")
        self.assertEqual(payload["sameAs"], "https://example.org/listen")
        self.assertNotIn("contentUrl", payload)

    def test_gallery_is_a_collection_of_image_objects(self) -> None:
        markup = structured_data(
            "media",
            {
                "id": "MTEST",
                "mediaType": "document_gallery",
                "assetPath": "assets/images/one.jpg",
                "assetPaths": ["assets/images/one.jpg", "assets/images/two.jpg"],
            },
            "https://example.org/records/media/MTEST/",
            "Document gallery",
            "A curated document gallery.",
        )
        payload = json.loads(markup.split(">", 1)[1].rsplit("<", 1)[0])
        self.assertEqual(payload["@type"], "CollectionPage")
        self.assertEqual(len(payload["hasPart"]), 2)
        self.assertTrue(
            all(item["@type"] == "ImageObject" for item in payload["hasPart"])
        )
        self.assertNotIn("contentUrl", payload)


if __name__ == "__main__":
    unittest.main()
