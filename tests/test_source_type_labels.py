import json
import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "assets/site/core.js"


def curated_forms():
    """Both grammatical numbers for every source type, keyed by type."""
    text = CORE.read_text(encoding="utf-8")
    block = re.search(r"export const SOURCE_TYPES = Object\.freeze\(\{(.*?)\n\}\);", text, re.S)
    assert block, "the core module no longer carries the source-type vocabulary"
    entries = re.findall(
        r'^\s*([a-z_]+): \{ one: "([^"]+)", many: "([^"]+)" \},',
        block.group(1),
        re.M,
    )
    return {key: {"one": one, "many": many} for key, one, many in entries}


def curated_labels():
    return {key: forms["one"] for key, forms in curated_forms().items()}


def source_types():
    records = json.loads((ROOT / "data/public/v1/sources.json").read_text(encoding="utf-8"))["records"]
    return {record["sourceType"] for record in records if record.get("sourceType")}


class SourceTypeLabelTests(unittest.TestCase):
    """One vocabulary names a source type everywhere it is shown: the badge on
    the record card, the catalogue row and filter, and the heading over a group
    of citations in the source ledger. The singular and plural forms lived in
    separate modules until they had drifted apart in more than number — one
    module spelled "Sheet-music catalogue", the other "Sheet music catalogues"
    — so both forms are now held together and checked together."""

    def test_every_kind_of_source_in_the_data_has_a_heading(self):
        missing = sorted(source_types() - set(curated_labels()))
        self.assertEqual(missing, [], "these source types would be shown under a raw technical name")

    def test_the_headings_are_written_the_same_way(self):
        for key, forms in curated_forms().items():
            for number, label in forms.items():
                self.assertTrue(
                    label[:1].isupper(), f"{key}.{number}: {label!r} does not begin with a capital"
                )
                words = label.split()
                titled = [
                    w for w in words[1:]
                    if w[:1].isupper() and w.lower() not in {"wikimedia", "wikipedia", "commons"}
                ]
                self.assertEqual(
                    titled, [], f"{key}.{number}: {label!r} is set in title case, not sentence case"
                )

    def test_no_heading_is_used_for_two_different_kinds(self):
        for number in ("one", "many"):
            seen = {}
            for key, forms in curated_forms().items():
                label = forms[number]
                self.assertNotIn(
                    label, seen, f"{key} and {seen.get(label)} would appear under the same heading"
                )
                seen[label] = key

    def test_both_numbers_are_spelled_consistently(self):
        """A plural may reword its singular, but it may not silently respell it:
        "Sheet-music catalogue" must not become "Sheet music catalogues"."""
        reworded = {"image_or_photograph", "recording_discographic_source"}
        for key, forms in curated_forms().items():
            if key in reworded:
                continue
            stem = forms["one"].removesuffix("s")
            self.assertTrue(
                forms["many"].startswith(stem),
                f"{key}: {forms['many']!r} respells {forms['one']!r} rather than pluralizing it",
            )

    def test_the_vocabulary_is_defined_in_exactly_one_module(self):
        """The drift these labels suffered was possible only because two modules
        each held a copy. A second definition anywhere reopens that door."""
        definitions = []
        for module in sorted((ROOT / "assets/site").glob("*.js")):
            text = module.read_text(encoding="utf-8")
            for name in ("SOURCE_TYPES", "SOURCE_TYPE_LABELS", "SOURCE_DATE_ROLE_LABELS", "DATE_ROLE_LABELS"):
                if re.search(rf"(?:const|let|var)\s+{name}\s*=", text):
                    definitions.append(f"{module.name}:{name}")
        self.assertEqual(
            sorted(definitions),
            ["core.js:SOURCE_DATE_ROLE_LABELS", "core.js:SOURCE_TYPES"],
            "a source vocabulary is defined outside the core module",
        )

    def test_web_article_is_not_a_singleton_category(self):
        self.assertNotIn("web_article", source_types())
        self.assertNotIn("web_article", curated_labels())

    def test_commons_held_file_records_use_the_dedicated_kind(self):
        offenders = []
        for source in json.loads(
            (ROOT / "data/public/v1/sources.json").read_text(encoding="utf-8")
        )["records"]:
            parsed = urlparse(source.get("primaryUrl") or "")
            is_commons_file = (
                parsed.netloc.casefold() == "commons.wikimedia.org"
                and unquote(parsed.path).startswith("/wiki/File:")
            )
            if (
                is_commons_file
                and source.get("repository") == "Wikimedia Commons"
                and source.get("sourceType") != "wikimedia_commons_file"
            ):
                offenders.append(source["id"])
        self.assertEqual(
            offenders,
            [],
            "Commons is the stated repository, but the records are typed as generic images",
        )


if __name__ == "__main__":
    unittest.main()
