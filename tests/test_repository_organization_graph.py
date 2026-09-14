from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
sys.path.insert(0, str(ROOT / "scripts"))

from repository_organizations import (  # noqa: E402
    expected_repository_organization_ids,
)


def read_records(filename: str) -> list[dict]:
    return json.loads((PUBLIC / filename).read_text(encoding="utf-8"))["records"]


class RepositoryOrganizationGraphTests(unittest.TestCase):
    def test_controlled_repository_markers_are_recognized(self) -> None:
        self.assertEqual(
            expected_repository_organization_ids(
                {"repository": "Media History Digital Library / Internet Archive"}
            ),
            ("ORG067",),
        )
        self.assertEqual(
            expected_repository_organization_ids(
                {"repository": "Bibliothèque nationale de France (BnF)"}
            ),
            ("ORG062",),
        )
        self.assertEqual(
            expected_repository_organization_ids(
                {"repository": "SACEM repertoire database"}
            ),
            ("ORG085",),
        )

    def test_citation_prose_and_urls_do_not_create_repository_links(self) -> None:
        source = {
            "repository": "Private collection",
            "fullCitation": "A copy was later uploaded to Internet Archive.",
            "primaryUrl": "https://archive.org/details/example",
        }
        self.assertEqual(expected_repository_organization_ids(source), ())

    def test_every_controlled_repository_relation_is_bidirectional(self) -> None:
        sources = read_records("sources.json")
        organizations = {
            record["id"]: record for record in read_records("organizations.json")
        }

        checked = 0
        for source in sources:
            for organization_id in expected_repository_organization_ids(source):
                checked += 1
                self.assertIn(
                    organization_id,
                    source.get("organizationIds") or [],
                    f"{source['id']} omits {organization_id}",
                )
                self.assertIn(
                    source["id"],
                    organizations[organization_id].get("sourceIds") or [],
                    f"{organization_id} does not link back to {source['id']}",
                )

        self.assertGreater(checked, 0, "the controlled rule did not inspect any source")


if __name__ == "__main__":
    unittest.main()
