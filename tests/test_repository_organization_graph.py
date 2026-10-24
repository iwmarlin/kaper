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
    def test_newly_audited_repository_markers_are_recognized(self) -> None:
        for repository, expected in (
            ("Biblioteka Narodowa / Polona", ("ORG063",)),
            ("Library of Congress, Music Division", ("ORG066",)),
            ("Wikimedia Commons / Library of Congress", ("ORG066",)),
            ("Billy Rose Theatre Division, The New York Public Library for the Performing Arts", ("ORG164",)),
        ):
            with self.subTest(repository=repository):
                self.assertEqual(expected_repository_organization_ids({"repository": repository}), expected)

    def test_copyright_catalogue_creator_is_distinct_from_access_repository(self) -> None:
        source = next(record for record in read_records("sources.json") if record["id"] == "SRC0689")
        self.assertEqual(source["repository"], "Internet Archive")
        self.assertEqual(source["creator"], "United States Copyright Office")
        self.assertIn("ORG067", source["organizationIds"])
        self.assertIn("ORG068", source["organizationIds"])
        self.assertIn("ORG118", source["organizationIds"])
        self.assertEqual(expected_repository_organization_ids(source), ("ORG067", "ORG068"))

    def test_jurmann_finding_aid_is_not_assigned_to_berkeley(self) -> None:
        sources = {record["id"]: record for record in read_records("sources.json")}
        organizations = {record["id"]: record for record in read_records("organizations.json")}
        source = sources["SRC0890"]
        self.assertEqual(source["repository"], "UCLA Library, Performing Arts Special Collections")
        self.assertNotIn("ORG079", source.get("organizationIds", []))
        self.assertNotIn("SRC0890", organizations["ORG079"]["sourceIds"])
        self.assertIn("SRC0485", organizations["ORG079"]["sourceIds"])
        self.assertEqual(source["workIds"], ["W-S168"])
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        self.assertIn("ORG079", overrides["linkRemovals"]["Sources"]["SRC0890"]["fields"]["organizationIds"])
        self.assertIn("SRC0890", overrides["linkRemovals"]["Organizations"]["ORG079"]["fields"]["sourceIds"])

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
