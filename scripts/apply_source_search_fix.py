#!/usr/bin/env python3
"""Safely apply the Sources compact-index search parity fix.

Run from the repository root:
    python3 apply_source_search_fix.py

The script:
1. verifies the expected pre-fix source snippets,
2. edits only the builder and its regression test,
3. regenerates compact catalogue indexes/prerender,
4. runs the catalogue-index regression tests and freshness check,
5. restores every touched file if any step fails.

It does not commit or push anything.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()

BUILDER = ROOT / "scripts" / "build_catalogue_indexes.py"
TEST = ROOT / "tests" / "test_catalogue_indexes.py"

GENERATED = [
    ROOT / "data/site/indexes/works.json",
    ROOT / "data/site/indexes/people.json",
    ROOT / "data/site/indexes/media.json",
    ROOT / "data/site/indexes/sources.json",
    ROOT / "works.html",
    ROOT / "people.html",
    ROOT / "media.html",
    ROOT / "sources.html",
]

OLD_BUILDER = '''            "searchSupplement": joined([
                source.get("creator"),
                source.get("publication"),
                *[value for identifier in source.get("identifiers") or [] for value in (identifier.get("scheme"), identifier.get("value"))],
            ]),'''

NEW_BUILDER = '''            # shortCitation is deliberately retained as search-only material.
            # It often contains the form a researcher actually types (archive
            # acronyms, catalogue abbreviations, shelfmarks) even when the
            # longer display citation expands or omits that wording.
            "searchSupplement": joined([
                source.get("shortCitation"),
                source.get("creator"),
                source.get("publication"),
                *[value for identifier in source.get("identifiers") or [] for value in (identifier.get("scheme"), identifier.get("value"))],
            ]),'''

OLD_TEST = '''    def test_people_and_works_keep_search_material_out_of_relational_payloads(self) -> None:
        works = {item["id"]: item for item in read(INDEXES / "works.json")["records"]}
        people = {item["id"]: item for item in read(INDEXES / "people.json")["records"]}
        self.assertIn("Richard Tauber", works["W-S059"]["searchSupplement"])
        self.assertIn("Chwast", people["P009"]["searchSupplement"])'''

NEW_TEST = '''    def test_compact_indexes_keep_search_material_needed_for_browse_queries(self) -> None:
        works = {item["id"]: item for item in read(INDEXES / "works.json")["records"]}
        people = {item["id"]: item for item in read(INDEXES / "people.json")["records"]}
        sources = {item["id"]: item for item in read(INDEXES / "sources.json")["records"]}
        canonical_sources = {item["id"]: item for item in read(PUBLIC / "sources.json")["records"]}

        self.assertIn("Richard Tauber", works["W-S059"]["searchSupplement"])
        self.assertIn("Chwast", people["P009"]["searchSupplement"])

        # A source's short citation is not merely a display abbreviation: it
        # carries common research queries such as archive acronyms, catalogue
        # shorthands and shelfmarks. Every one must remain searchable after
        # replacing the full relational Sources payload with the compact index.
        for source_id, source in canonical_sources.items():
            short_citation = source.get("shortCitation")
            if short_citation:
                with self.subTest(source=source_id):
                    self.assertIn(short_citation, sources[source_id]["searchSupplement"])'''


def read(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Missing expected file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def run(*args: str) -> None:
    print("+", " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    builder_text = read(BUILDER)
    test_text = read(TEST)

    if OLD_BUILDER not in builder_text:
        raise RuntimeError(
            "Builder does not match the expected pre-fix state. No files were changed."
        )
    if OLD_TEST not in test_text:
        raise RuntimeError(
            "Regression-test file does not match the expected pre-fix state. No files were changed."
        )

    touched = [BUILDER, TEST, *GENERATED]
    backups = {path: path.read_bytes() if path.exists() else None for path in touched}

    try:
        BUILDER.write_text(builder_text.replace(OLD_BUILDER, NEW_BUILDER), encoding="utf-8")
        TEST.write_text(test_text.replace(OLD_TEST, NEW_TEST), encoding="utf-8")

        run(sys.executable, "scripts/build_catalogue_indexes.py", "--root", ".")
        run(sys.executable, "-m", "unittest", "tests.test_catalogue_indexes")
        run(sys.executable, "scripts/build_catalogue_indexes.py", "--root", ".", "--check")

    except Exception:
        print("\nValidation failed. Restoring the exact pre-fix files...", file=sys.stderr)
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        print("Rollback complete. Repository returned to its pre-fix state.", file=sys.stderr)
        raise

    print("\nFix applied and validated.")
    print("No commit or push was made. Review the changes in GitHub Desktop before committing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
