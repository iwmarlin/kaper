from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from authority_sources import AUTHORITY_REPOSITORY_BY_HOST  # noqa: E402
from repository_names import (  # noqa: E402
    BNF,
    BNF_REPOSITORY_BY_HOST,
    REPOSITORY_ALIASES,
    REPOSITORY_ALIASES_BY_HOST,
    canonical_repository_name,
)
from repository_organizations import (  # noqa: E402
    expected_repository_organization_ids,
)


class RepositoryNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = json.loads(
            (PUBLIC / "sources.json").read_text(encoding="utf-8")
        )["records"]

    def test_no_source_keeps_a_superseded_spelling(self) -> None:
        superseded = set(REPOSITORY_ALIASES)
        for source in self.sources:
            repository = source.get("repository")
            self.assertNotIn(
                repository,
                superseded,
                msg=f"{source['id']} keeps a superseded repository spelling",
            )
            host = urlparse(str(source.get("primaryUrl") or "")).netloc
            self.assertNotIn(
                (repository, host),
                REPOSITORY_ALIASES_BY_HOST,
                msg=f"{source['id']} keeps a superseded repository spelling",
            )

    def test_every_repository_name_is_already_canonical(self) -> None:
        for source in self.sources:
            repository = source.get("repository")
            if not repository:
                continue
            self.assertEqual(
                canonical_repository_name(source),
                repository,
                msg=f"{source['id']} repository is not canonical",
            )

    def test_bnf_records_name_the_resource_they_cite(self) -> None:
        seen = set()
        for source in self.sources:
            repository = str(source.get("repository") or "")
            if not repository.startswith(BNF):
                continue
            host = urlparse(str(source.get("primaryUrl") or "")).netloc
            if source.get("sourceType") == "authority_record":
                expected = AUTHORITY_REPOSITORY_BY_HOST.get(host)
            else:
                expected = BNF_REPOSITORY_BY_HOST.get(host)
            if expected is None:
                continue
            seen.add(expected)
            self.assertEqual(
                repository,
                expected,
                msg=f"{source['id']} ({host}) names the wrong BnF resource",
            )
        self.assertIn(f"{BNF} / Catalogue général", seen)
        self.assertIn(f"{BNF} (BnF)", seen)

    def test_canonical_names_keep_their_organization_relations(self) -> None:
        # Renaming a repository must not cut the curated relation between a
        # Source and the Organization card for the institution that holds it.
        for old, new in REPOSITORY_ALIASES.items():
            self.assertEqual(
                expected_repository_organization_ids({"repository": new}),
                expected_repository_organization_ids({"repository": old}),
                msg=f"renaming {old!r} changed its Organization relations",
            )
        for (old, _host), new in REPOSITORY_ALIASES_BY_HOST.items():
            self.assertEqual(
                expected_repository_organization_ids({"repository": new}),
                expected_repository_organization_ids({"repository": old}),
                msg=f"renaming {old!r} changed its Organization relations",
            )
        for new in BNF_REPOSITORY_BY_HOST.values():
            self.assertIn(
                "ORG062",
                expected_repository_organization_ids({"repository": new}),
                msg=f"{new!r} no longer names the BnF Organization card",
            )


if __name__ == "__main__":
    unittest.main()
