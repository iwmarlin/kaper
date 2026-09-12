from __future__ import annotations

import base64
import glob
import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# The libraries the map needs are kept in the repository, at the exact bytes
# the project reviewed: these are the sub-resource hashes the page carried
# while it still loaded them from a package host.
VENDORED = {
    "assets/vendor/leaflet-1.9.4.css": "sha384-sHL9NAb7lN7rfvG5lfHpm643Xkcjzp4jFvuavGOndn6pjVqS6ny56CAt3nsEVT4H",
    "assets/vendor/leaflet-1.9.4.js": "sha384-cxOPjt7s7Iz04uaHJceBmS+qpjv2JkIHNVcuOrM+YHwZOmJGBXI00mdUXEq65HTH",
    "assets/vendor/markercluster-1.5.3.css": "sha384-pmjIAcz2bAn0xukfxADbZIb3t8oRT9Sv0rvO+BR5Csr6Dhqq+nZs59P0pPKQJkEV",
    "assets/vendor/markercluster-1.5.3.js": "sha384-eXVCORTRlv4FUUgS/xmOyr66XBVraen8ATNLMESp92FKXLAMiKkerixTiBvXriZr",
}


class MapDependencyTests(unittest.TestCase):
    def test_the_vendored_libraries_are_the_reviewed_bytes(self) -> None:
        for relative, expected in VENDORED.items():
            path = ROOT / relative
            with self.subTest(file=relative):
                self.assertTrue(path.is_file(), "the library is missing from the repository")
                digest = hashlib.sha384(path.read_bytes()).digest()
                self.assertEqual("sha384-" + base64.b64encode(digest).decode(), expected)

    def test_their_licences_travel_with_them(self) -> None:
        for name in ("LICENSE-leaflet.txt", "LICENSE-markercluster.txt"):
            with self.subTest(file=name):
                self.assertTrue((ROOT / "assets/vendor" / name).is_file())

    def test_no_page_loads_a_third_party_script_or_stylesheet(self) -> None:
        offenders = []
        for path in glob.glob(str(ROOT / "*.html")) + glob.glob(str(ROOT / "records/**/index.html"), recursive=True):
            text = Path(path).read_text(encoding="utf-8")
            # Canonical, preconnect and social metadata may name other
            # origins; what matters is code and style the browser executes.
            for match in re.finditer(r'<script[^>]+src="(https?://[^"]+)"', text):
                offenders.append((Path(path).name, match.group(1)))
            for match in re.finditer(r'<link[^>]+rel="stylesheet"[^>]*href="(https?://[^"]+)"', text):
                offenders.append((Path(path).name, match.group(1)))
            for match in re.finditer(r'<link[^>]+href="(https?://[^"]+)"[^>]*rel="stylesheet"', text):
                offenders.append((Path(path).name, match.group(1)))
        self.assertEqual(offenders[:5], [])

    def test_the_content_policy_names_no_package_host(self) -> None:
        for path in glob.glob(str(ROOT / "*.html")):
            text = Path(path).read_text(encoding="utf-8")
            policy = re.search(r'Content-Security-Policy" content="([^"]+)"', text)
            if not policy:
                continue
            with self.subTest(page=Path(path).name):
                self.assertNotIn("unpkg", policy.group(1))
                self.assertIn("script-src 'self';", policy.group(1))


if __name__ == "__main__":
    unittest.main()


class MapZoomContractTests(unittest.TestCase):
    """The clustering plugin refuses to run on a map without a zoom ceiling."""

    def test_the_map_declares_its_own_zoom_range(self) -> None:
        source = (ROOT / "assets/site/map-explorer-20260714.js").read_text(encoding="utf-8")
        options = re.search(r'window\.L\.map\("research-map",\s*\{(.*?)\}\)', source, re.S)
        self.assertIsNotNone(options, "the map is no longer created here")
        self.assertIn("maxZoom", options.group(1))
        self.assertIn("minZoom", options.group(1))
