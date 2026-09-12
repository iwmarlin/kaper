from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from export_public_data import PublicExporter  # noqa: E402


class PublicExportTemporaryDirectoryTests(unittest.TestCase):
    def exporter(
        self,
        parent: Path,
        *,
        keep_failed_output: bool,
        validation_error: bool = True,
    ) -> PublicExporter:
        exporter = PublicExporter.__new__(PublicExporter)
        exporter.output_root = parent / "v1"
        exporter.keep_failed_output = keep_failed_output
        exporter.errors = []
        exporter.warnings = []
        exporter.output_records = {}
        exporter.select_public_graph = lambda: None
        exporter.build_records = lambda: None
        exporter.validate = (
            (lambda: exporter.errors.append("expected failure"))
            if validation_error
            else (lambda: None)
        )
        exporter._write_export = lambda root: (root / "partial.json").write_text(
            "{}", encoding="utf-8"
        )
        return exporter

    def test_failed_export_is_removed_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            exporter = self.exporter(
                parent,
                keep_failed_output=False,
            )
            with contextlib.redirect_stdout(io.StringIO()):
                result = exporter.run()

            self.assertFalse(result["ok"])
            self.assertIsNone(result["temporaryOutput"])
            self.assertEqual(list(parent.glob(".public-export-*")), [])

    def test_failed_export_can_be_preserved_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            exporter = self.exporter(
                parent,
                keep_failed_output=True,
            )
            with contextlib.redirect_stdout(io.StringIO()):
                result = exporter.run()

            preserved = Path(result["temporaryOutput"])
            self.assertTrue(preserved.is_dir())
            self.assertTrue((preserved / "partial.json").is_file())

    def test_successful_export_is_moved_without_leaving_a_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            exporter = self.exporter(
                parent,
                keep_failed_output=False,
                validation_error=False,
            )
            with contextlib.redirect_stdout(io.StringIO()):
                result = exporter.run()

            self.assertTrue(result["ok"])
            self.assertTrue((parent / "v1" / "partial.json").is_file())
            self.assertEqual(list(parent.glob(".public-export-*")), [])

    def test_exception_during_write_removes_workspace_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            exporter = self.exporter(
                parent,
                keep_failed_output=False,
                validation_error=False,
            )

            def fail_during_write(root: Path) -> None:
                (root / "partial.json").write_text("{}", encoding="utf-8")
                raise RuntimeError("interrupted export")

            exporter._write_export = fail_during_write
            with self.assertRaisesRegex(RuntimeError, "interrupted export"):
                exporter.run()

            self.assertEqual(list(parent.glob(".public-export-*")), [])


if __name__ == "__main__":
    unittest.main()
