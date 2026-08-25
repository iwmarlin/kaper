from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/public/v1"

# Articles that the filing title drops, so that "Le chant du destin" files
# under C and "Der Korvettenkapitän" under K.
LEADING_ARTICLES = re.compile(
    r"^(?:der|die|das|ein|eine|einen|le|la|les|un|une|the|a|an|il|lo|el)\s",
    re.IGNORECASE,
)


def records(filename: str) -> list[dict]:
    return json.loads((DATA / filename).read_text(encoding="utf-8"))["records"]


class BrowseSortingTests(unittest.TestCase):
    def test_every_public_work_has_a_filing_title(self) -> None:
        missing = [
            record["id"]
            for record in records("works.json")
            if record.get("displayOnSite", True) and not record.get("sortTitle")
        ]
        self.assertEqual(missing, [])

    def test_filing_titles_drop_leading_articles(self) -> None:
        offenders = [
            (record["id"], record["sortTitle"])
            for record in records("works.json")
            if record.get("sortTitle") and LEADING_ARTICLES.match(record["sortTitle"])
        ]
        self.assertEqual(offenders, [])

    def test_every_person_has_a_filing_name(self) -> None:
        missing = [
            record["id"]
            for record in records("people.json")
            if not record.get("sortName")
        ]
        self.assertEqual(missing, [])

    def test_browsing_lists_share_one_comparator(self) -> None:
        """Works and People must not each fall back to their own collation."""
        for name in ("works.js", "people.js"):
            source = (ROOT / "assets/site" / name).read_text(encoding="utf-8")
            with self.subTest(script=name):
                self.assertIn("compareText", source)
                self.assertNotIn("localeCompare", source)

    def test_comparator_files_titles_and_names_as_expected(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is required to exercise the shared comparator")

        core = (ROOT / "assets/site/core.js").as_uri()
        script = f"""
          import {{ compareText, sortKey, nameKey }} from {json.dumps(core)};
          const titles = [
            {{ title: "Die lustigen Musikanten", sortTitle: "lustigen Musikanten" }},
            {{ title: "Ach, Otto, Otto...!" }},
            {{ title: "La Femme aime à verser des larmes", sortTitle: "Femme aime à verser des larmes" }},
            {{ title: "Balalaika" }},
          ];
          const filed = titles
            .sort((a, b) => compareText(sortKey(a), sortKey(b)))
            .map((item) => item.title);
          const people = [
            {{ displayName: "Allan Jones", sortName: "Jones, Allan" }},
            {{ displayName: "Andrzej Włast", sortName: "Włast, Andrzej" }},
            {{ displayName: "Sam Wood", sortName: "Wood, Sam" }},
          ];
          const named = people
            .sort((a, b) => compareText(nameKey(a), nameKey(b)))
            .map((item) => item.sortName);
          process.stdout.write(JSON.stringify({{ filed, named }}));
        """
        result = subprocess.run(
            [node, "--input-type=module", "--eval", script],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)

        self.assertEqual(
            payload["filed"],
            [
                "Ach, Otto, Otto...!",
                "Balalaika",
                "La Femme aime à verser des larmes",
                "Die lustigen Musikanten",
            ],
        )
        self.assertEqual(
            payload["named"], ["Jones, Allan", "Włast, Andrzej", "Wood, Sam"]
        )


if __name__ == "__main__":
    unittest.main()
