from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "assets/site/record-detail-20260714.js"


class RecordImageMapTests(unittest.TestCase):
    """All 1875 canonical record pages imported the responsive-image map, although
    none of them renders an image in the browser: their content is prerendered."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = RENDERER.read_text(encoding="utf-8")

    def test_the_renderer_does_not_import_the_image_map_statically(self) -> None:
        self.assertIsNone(re.search(r"^import\s[^;]*image-derivatives\.js", self.script, re.MULTILINE))

    def test_the_compatibility_route_loads_the_image_map_when_it_renders(self) -> None:
        self.assertRegex(self.script, r'\bimport\("\./image-derivatives\.js\?v=[A-Za-z0-9._-]+"\)')

    def test_prerendered_record_images_still_carry_their_derivatives(self) -> None:
        pages = sorted((ROOT / "records/media").glob("*/index.html"))
        with_images = [page for page in pages if "<img " in page.read_text(encoding="utf-8")]
        self.assertTrue(with_images, "no prerendered media record carries an image")
        text = with_images[0].read_text(encoding="utf-8")
        self.assertIn('srcset="assets/generated/responsive/', text)


if __name__ == "__main__":
    unittest.main()
