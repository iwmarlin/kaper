from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE = (ROOT / "assets/site/core.js").as_uri()


def run_module(script: str) -> dict:
    node = shutil.which("node")
    if not node:
        raise unittest.SkipTest("Node.js is required to exercise the browse index")
    result = subprocess.run(
        [node, "--input-type=module", "--eval", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


class SearchNormalizationTests(unittest.TestCase):
    def test_punctuation_and_diacritics_do_not_hide_a_record(self) -> None:
        payload = run_module(f"""
          import {{ normalizeSearch, indexText }} from {json.dumps(CORE)};
          process.stdout.write(JSON.stringify({{
            comma: normalizeSearch("Così, cosa"),
            apostrophe: normalizeSearch("All God’s Chillun Got Rhythm"),
            guillemets: normalizeSearch("Quand les jeunes filles disent « non »"),
            sharpS: indexText("Vergißmeinnicht"),
            umlaut: indexText("Mühlhardt"),
            plain: indexText("Balalaika"),
          }}));
        """)

        self.assertEqual(payload["comma"], "cosi cosa")
        self.assertEqual(payload["apostrophe"], "all gods chillun got rhythm")
        self.assertEqual(payload["guillemets"], "quand les jeunes filles disent non")
        # The index carries both spellings; a reader may type either.
        self.assertIn("vergissmeinnicht", payload["sharpS"])
        self.assertIn("vergißmeinnicht", payload["sharpS"])
        self.assertIn("muehlhardt", payload["umlaut"])
        self.assertEqual(payload["plain"], "balalaika")


class WorkSearchIndexTests(unittest.TestCase):
    """The Works index answers for the record as the reader sees it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = run_module(f"""
          import fs from "node:fs";
          import {{ workSearchText, normalizeSearch, indexById }} from {json.dumps(CORE)};
          const read = (file) => JSON.parse(fs.readFileSync(`data/public/v1/${{file}}`, "utf8")).records;
          const works = read("works.json").filter((work) => work.displayOnSite !== false);
          const subtypeByWorkId = new Map();
          for (const subtype of [...read("films.json"), ...read("songs.json"), ...read("other-works.json")]) {{
            for (const id of subtype.workIds || []) subtypeByWorkId.set(id, subtype);
          }}
          const lookup = {{
            peopleById: indexById(read("people.json")),
            contributionsById: indexById(read("contributions.json")),
            titleVariantsById: indexById(read("title-variants.json")),
            subtypeByWorkId,
          }};
          const index = works.map((work) => ({{ id: work.id, text: workSearchText(work, lookup) }}));
          const hits = (query) => index
            .filter((entry) => entry.text.includes(normalizeSearch(query)))
            .map((entry) => entry.id);
          process.stdout.write(JSON.stringify({{
            performer: hits("Richard Tauber"),
            printedPseudonym: hits("Fred Lustig"),
            titleVariant: hits("Love Is a Fairy Tale"),
            exportTitle: hits("Moonlight at Sanssouci"),
            punctuatedTitle: hits("cosi cosa"),
            filmCompany: hits("Metro-Goldwyn"),
            recordLabel: hits("Odeon"),
            sheetPublisher: hits("Alrobi"),
          }}));
        """)

    def test_performing_credits_are_searchable(self) -> None:
        self.assertIn("W-S059", self.payload["performer"])

    def test_a_credit_is_searchable_under_the_name_it_was_printed_with(self) -> None:
        self.assertEqual(self.payload["printedPseudonym"], ["W-S057"])

    def test_recorded_title_variants_are_searchable(self) -> None:
        self.assertEqual(self.payload["titleVariant"], ["W-S059"])
        self.assertEqual(self.payload["exportTitle"], ["W-S047"])

    def test_punctuation_in_a_title_does_not_block_the_query(self) -> None:
        self.assertIn("W-S118", self.payload["punctuatedTitle"])

    def test_organizations_do_not_answer_for_their_works(self) -> None:
        """Labels, studios and publishers have records of their own.

        Indexing them here would return a third of the catalogue for a single
        house name and duplicate what the organization page already gathers.
        """
        self.assertEqual(self.payload["filmCompany"], [])
        self.assertEqual(self.payload["recordLabel"], [])
        self.assertEqual(self.payload["sheetPublisher"], [])


if __name__ == "__main__":
    unittest.main()
