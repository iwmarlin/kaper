import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FONT_REF = re.compile(r'(?:\.\./fonts/|assets/fonts/)[A-Za-z0-9._-]+\.woff2(\?v=[A-Za-z0-9._-]+)?')


def files_that_reference_fonts():
    for path in sorted(ROOT.glob("*.html")):
        yield path
    for path in sorted((ROOT / "assets/site").glob("*.css")):
        yield path
    for path in sorted((ROOT / "records").rglob("index.html")):
        yield path


class FontVersioningTests(unittest.TestCase):
    """The stylesheet's own URL changed on every build, so a reader always
    received the new CSS — pointing at a font URL that had not changed since
    their first visit. They kept the typeface they were first served, and no
    change of face could reach them."""

    def test_every_font_reference_carries_a_version(self):
        unstamped = []
        checked = 0
        for path in files_that_reference_fonts():
            text = path.read_text(encoding="utf-8")
            for match in FONT_REF.finditer(text):
                checked += 1
                if not match.group(1):
                    unstamped.append(f"{path.relative_to(ROOT)}: {match.group(0)}")
        self.assertGreater(checked, 0, "the fixture must reference the fonts")
        self.assertEqual(unstamped[:10], [], f"{len(unstamped)} font references can serve a cached file")

    def test_replacing_a_font_moves_the_build_id(self):
        # A typeface can change without a line of CSS changing. If the id were
        # derived from the stylesheets alone it would not move, the stamp
        # written into every page would not move, and the new file would never
        # be requested.
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import stamp_assets
        finally:
            sys.path.pop(0)
        font = ROOT / "assets/fonts/kaper-serif.woff2"
        before = stamp_assets.build_id()
        original = font.read_bytes()
        try:
            font.write_bytes(original + b"\0")
            self.assertNotEqual(stamp_assets.build_id(), before)
        finally:
            font.write_bytes(original)
        self.assertEqual(stamp_assets.build_id(), before)

    def test_the_stamp_is_idempotent(self):
        first = subprocess.run(
            [sys.executable, "scripts/stamp_assets.py"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
        second = subprocess.run(
            [sys.executable, "scripts/stamp_assets.py"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
        self.assertIn("stamped 0 file(s)", second, f"a second run still rewrote files:\n{first}\n{second}")


if __name__ == "__main__":
    unittest.main()
