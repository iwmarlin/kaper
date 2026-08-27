import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "assets/site/record-detail-20260714.js"


def curated_labels():
    text = RENDERER.read_text(encoding="utf-8")
    block = re.search(r"const SOURCE_TYPE_LABELS = \{(.*?)\n\};", text, re.S)
    assert block, "the renderer no longer carries a source-type label map"
    return dict(re.findall(r'^\s*([a-z_]+): "([^"]+)",', block.group(1), re.M))


def source_types():
    records = json.loads((ROOT / "data/public/v1/sources.json").read_text(encoding="utf-8"))["records"]
    return {record["sourceType"] for record in records if record.get("sourceType")}


class SourceTypeLabelTests(unittest.TestCase):
    """A source card groups its citations by kind, and the heading of each group
    comes from this map. Eleven kinds were missing from it, so their headings
    were built from the technical name — "Online Audio Source" beside
    "Recordings" and "Online video" — and a real distinction read as an
    arbitrary one."""

    def test_every_kind_of_source_in_the_data_has_a_heading(self):
        missing = sorted(source_types() - set(curated_labels()))
        self.assertEqual(missing, [], "these source types would be shown under a raw technical name")

    def test_the_headings_are_written_the_same_way(self):
        for key, label in curated_labels().items():
            self.assertTrue(label[:1].isupper(), f"{key}: {label!r} does not begin with a capital")
            words = label.split()
            titled = [w for w in words[1:] if w[:1].isupper() and w.lower() not in {"wikimedia", "wikipedia", "commons"}]
            self.assertEqual(titled, [], f"{key}: {label!r} is set in title case, not sentence case")

    def test_no_heading_is_used_for_two_different_kinds(self):
        labels = curated_labels()
        seen = {}
        for key, label in labels.items():
            self.assertNotIn(
                label, seen, f"{key} and {seen.get(label)} would appear under the same heading"
            )
            seen[label] = key


if __name__ == "__main__":
    unittest.main()
