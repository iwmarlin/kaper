import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PhilharmonicNacPhotoTests(unittest.TestCase):
    def test_gallery_photo_and_source_are_connected(self):
        def records(table):
            return {r['id']: r for r in json.loads((ROOT / 'data/public/v1' / (table + '.json')).read_text())['records']}

        media, sources, places = records('media'), records('sources'), records('places')
        photo, gallery = media['M463'], media['M030']
        self.assertIn('M463', gallery['galleryMemberIds'])
        self.assertIn(photo['assetPath'], gallery['assetPaths'])
        self.assertEqual(gallery['assetCount'], len(gallery['assetPaths']))
        self.assertTrue((ROOT / photo['assetPath']).is_file())
        self.assertEqual(photo['sourceIds'], ['SRC0014'])
        self.assertIn('M463', sources['SRC0014']['mediaIds'])
        self.assertIn('M463', places['PL017']['mediaIds'])
        self.assertEqual(photo['rightsStatus'], 'public_domain')
