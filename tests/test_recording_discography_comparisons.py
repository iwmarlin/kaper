"""Catalogue comparisons must not identify unlabelled listening copies."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source


class RecordingDiscographyComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {r["id"]: r for r in json.loads(
            (ROOT / "data/public/v1/sources.json").read_text())["records"]}
        cls.media = {r["id"]: r for r in json.loads(
            (ROOT / "data/public/v1/media.json").read_text())["records"]}
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    def test_comparisons_keep_uploads_and_unknown_carriers(self):
        for sid, mid in (("SRC0728", "M366"), ("SRC0732", "M370"), ("SRC0790", "M411")):
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual(source["sourceType"], "online_audio_source")
                self.assertIn(mid, source["mediaIds"])
                self.assertIn(sid, self.media[mid]["sourceIds"])
                self.assertEqual(source["primaryUrl"], self.media[mid]["externalUrl"])
                self.assertEqual(normalized_source(source), source)
                for field in ("researchNote", "additionalLinks"):
                    self.assertEqual(self.overrides["records"]["Sources"][sid]["fields"][field],
                                     source[field])

    def test_discography_evidence_is_explicitly_qualified(self):
        geczy = self.sources["SRC0728"]["researchNote"]
        self.assertIn("133049", geczy)
        self.assertIn("do not establish the pressing or take", geczy)
        bird = self.sources["SRC0732"]["researchNote"]
        self.assertIn("HO 4382", bird)
        self.assertIn("does not name its singers", bird)
        self.assertIn("does not establish", bird)
        bela = self.sources["SRC0790"]["researchNote"]
        self.assertIn("Be 9946", bela)
        self.assertIn("Be 9947", bela)
        self.assertIn("sources therefore differ", bela)
        self.assertIn("without a verified match", bela)


if __name__ == "__main__":
    unittest.main()
