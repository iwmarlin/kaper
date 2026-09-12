import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from visual_sources import is_direct_nac_photograph, normalize_visual_source


class NacVisualSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        payload = json.loads(
            (ROOT / "data/public/v1/sources.json").read_text(encoding="utf-8")
        )
        cls.sources = {record["id"]: record for record in payload["records"]}

    def test_direct_nac_photographs_share_one_source_type(self):
        direct = [source for source in self.sources.values() if is_direct_nac_photograph(source)]
        self.assertTrue(direct)
        self.assertEqual({"archival_photograph"}, {source["sourceType"] for source in direct})

    def test_kazimierzowski_palace_is_the_linked_archival_photograph(self):
        source = self.sources["SRC0435"]
        self.assertEqual(["M094"], source["mediaIds"])
        self.assertEqual("archival_photograph", source["sourceType"])
        self.assertEqual(
            "Uniwersytet Warszawski — Pałac Kazimierzowski przy Krakowskim Przedmieściu",
            source["title"],
        )

    def test_commons_delivery_is_not_reclassified_as_direct_nac(self):
        source = copy.deepcopy(self.sources["SRC0336"])
        normalize_visual_source(source)
        self.assertEqual("wikimedia_commons_file", source["sourceType"])

    def test_normalization_is_idempotent(self):
        source = copy.deepcopy(self.sources["SRC0435"])
        normalize_visual_source(source)
        once = copy.deepcopy(source)
        normalize_visual_source(source)
        self.assertEqual(once, source)


if __name__ == "__main__":
    unittest.main()
