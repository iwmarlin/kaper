from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from filing_titles import filing_title  # noqa: E402


class FilingTitleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.works = json.loads(
            (PUBLIC / "works.json").read_text(encoding="utf-8")
        )["records"]

    def test_leading_articles_are_filed_past(self) -> None:
        self.assertEqual(filing_title("Die lustigen Musikanten"), "lustigen Musikanten")
        self.assertEqual(filing_title("The Magic of Maytime"), "Magic of Maytime")
        self.assertEqual(filing_title("L’Homme qui ne sait pas dire non"), "Homme qui ne sait pas dire non")

    def test_nothing_else_is_touched(self) -> None:
        # Not an article, and not a machine key: accents, apostrophes and
        # punctuation belong in the filing title exactly as the title has them.
        self.assertEqual(filing_title("À Paris tiguidiguidi"), "À Paris tiguidiguidi")
        self.assertEqual(filing_title("Singin’ in the Rain"), "Singin’ in the Rain")
        self.assertEqual(filing_title("How Am I to Know?"), "How Am I to Know?")
        self.assertEqual(
            filing_title("Mein kleines Fräulein, Sie sind nervös! (Ain’t Misbehavin’)"),
            "Mein kleines Fräulein, Sie sind nervös! (Ain’t Misbehavin’)",
        )

    def test_every_work_files_under_its_title(self) -> None:
        for work in self.works:
            self.assertEqual(
                work.get("sortTitle"),
                filing_title(work.get("title")),
                msg=f"{work['id']} has a filing title that is not its own title",
            )


if __name__ == "__main__":
    unittest.main()
