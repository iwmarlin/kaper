import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_site_assets", ROOT / "scripts/build_site_assets.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ResponsiveImageStateTests(unittest.TestCase):
    def test_content_state_is_not_invalidated_by_checkout_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "portrait.jpg"
            directory = root / "responsive"
            directory.mkdir()
            source.write_bytes(b"exact archival source bytes")
            (directory / "320.webp").write_bytes(b"derived image")

            os.utime(directory / "320.webp", (1, 1))
            os.utime(source, (2, 2))
            digest = MODULE.file_digest(source)

            self.assertTrue(
                MODULE.derivatives_are_current(
                    source,
                    directory,
                    [320],
                    digest,
                    {"sha256": digest, "widths": [320]},
                )
            )

    def test_changed_source_bytes_invalidate_the_derivatives(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "portrait.jpg"
            directory = root / "responsive"
            directory.mkdir()
            source.write_bytes(b"new source bytes")
            (directory / "320.webp").write_bytes(b"old derivative")

            self.assertFalse(
                MODULE.derivatives_are_current(
                    source,
                    directory,
                    [320],
                    MODULE.file_digest(source),
                    {"sha256": "0" * 64, "widths": [320]},
                )
            )

    def test_changed_recipe_invalidates_the_state_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "_state.json"
            state_path.write_text(
                '{"schemaVersion":"1.0.0","buildSignature":"old-recipe","sources":{}}',
                encoding="utf-8",
            )
            self.assertEqual(MODULE.read_derivative_state(state_path), {})


if __name__ == "__main__":
    unittest.main()
