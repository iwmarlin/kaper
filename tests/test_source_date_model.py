from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
sys.path.insert(0, str(ROOT / "scripts"))

from source_dates import (  # noqa: E402
    normalized_source_date_fields,
    source_date_errors,
    usco_identifiers,
)


class SourceDateModelTests(unittest.TestCase):
    def test_copyright_volume_date_and_registration_are_separate(self) -> None:
        source = {
            "id": "STEST",
            "sourceType": "copyright_catalogue",
            "date": "1935; copyright June 3, 1935; E pub. 48561",
            "fullCitation": "Catalogue for 1935; © June 3, 1935; E pub. 48561.",
        }
        self.assertEqual(
            normalized_source_date_fields(source),
            {
                "date": "1935",
                "dateRole": "catalogue_volume",
                "dateQualifier": "confirmed",
            },
        )
        self.assertEqual(
            usco_identifiers(source),
            [{"scheme": "usco_registration", "value": "E pub. 48561"}],
        )

    def test_explicit_upload_date_supersedes_uploader_claim(self) -> None:
        source = {
            "id": "STEST",
            "sourceType": "online_audio_source",
            "date": "1929 [according to the uploader]",
            "fullCitation": "YouTube audio published by Example on 24 June 2011.",
        }
        self.assertEqual(
            normalized_source_date_fields(source),
            {
                "date": "2011-06-24",
                "dateRole": "digital_publication",
                "dateQualifier": "confirmed",
            },
        )

    def test_every_canonical_source_has_a_valid_controlled_date(self) -> None:
        records = json.loads(
            (PUBLIC / "sources.json").read_text(encoding="utf-8")
        )["records"]
        errors = {
            source["id"]: source_date_errors(source)
            for source in records
            if source_date_errors(source)
        }
        self.assertEqual(errors, {})

    def test_unidentified_digital_reissues_are_not_discographic_sources(self) -> None:
        records = json.loads(
            (PUBLIC / "sources.json").read_text(encoding="utf-8")
        )["records"]
        offenders = [
            source["id"]
            for source in records
            if source.get("sourceType") == "recording_discographic_source"
            and "does not identify the label, catalogue number or matrix of the original disc"
            in (source.get("researchNote") or "").casefold()
        ]
        self.assertEqual(
            offenders,
            [],
            "a digital reissue without an identified original disc is classified as discographic",
        )

    def test_source_card_explains_both_date_and_its_role(self) -> None:
        node = shutil.which("node")
        if not node:
            bundled = (
                Path.home()
                / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
            )
            node = str(bundled) if bundled.is_file() else None
        if not node:
            self.skipTest("Node.js is required to exercise the public renderer")

        renderer = (ROOT / "assets/site/record-detail-20260714.js").as_uri()
        script = f"""
          import {{ renderRecordView }} from {json.dumps(renderer)};
          const tables = {{
            people: [], organizations: [], media: [], works: [], films: [], songs: [],
            otherWorks: [], titleVariants: [], workRelations: [], timelineEvents: [],
            places: [], contributions: [], personNameVariants: [],
            sources: [{{
              id: "STEST", title: "Test source", shortCitation: "Test source",
              fullCitation: "Test source.", sourceType: "online_audio_source",
              date: "2011-06-24", dateRole: "digital_publication",
              dateQualifier: "confirmed"
            }}]
          }};
          const {{ view }} = renderRecordView("source", "STEST", tables);
          process.stdout.write(view.facts);
        """
        result = subprocess.run(
            [node, "--input-type=module", "--eval", script],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("24 June 2011", result.stdout)
        self.assertIn("Date represents", result.stdout)
        self.assertIn("Digital publication", result.stdout)


if __name__ == "__main__":
    unittest.main()
