import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
sys.path.insert(0, str(ROOT / "scripts"))

from authority_sources import (  # noqa: E402
    AUTHORITY_SUBJECT_LINK_FIELDS,
    AUTHORITY_SUBJECTS,
    authority_source_semantic_errors,
)


def read_records(name):
    return json.loads((PUBLIC / name).read_text(encoding="utf-8"))["records"]


class OrganizationAuthoritySubjectTests(unittest.TestCase):
    """An authority record can document a person, a work or a corporate body.
    The third was missing while 86 Organizations carried register identifiers
    and none could cite the register that documents them."""

    def test_the_subject_vocabulary_holds_all_three(self):
        self.assertEqual(
            sorted(AUTHORITY_SUBJECTS), ["organization", "person", "work"]
        )

    def test_an_organization_authority_needs_the_body_it_documents(self):
        errors = authority_source_semantic_errors(
            {"sourceType": "authority_record", "authoritySubject": "organization"}
        )
        self.assertIn("organization authority has no organizationIds", errors)

    def test_an_organization_authority_asserts_no_identity_relation(self):
        # identityRelation answers whether a record is the same person; it has
        # no meaning for a corporate body.
        errors = authority_source_semantic_errors(
            {
                "sourceType": "authority_record",
                "authoritySubject": "organization",
                "organizationIds": ["ORG127"],
                "identityRelation": "same",
            }
        )
        self.assertIn(
            "non-person authority must not carry identityRelation", errors
        )

    def test_every_subject_names_what_the_record_documents(self):
        # The check is the same shape for all three: a record about something
        # must say which something, or it documents nothing.
        for subject, field in AUTHORITY_SUBJECT_LINK_FIELDS.items():
            with self.subTest(subject=subject):
                errors = authority_source_semantic_errors(
                    {"sourceType": "authority_record", "authoritySubject": subject}
                )
                self.assertIn(f"{subject} authority has no {field}", errors)

    def test_a_person_authority_is_unaffected(self):
        errors = authority_source_semantic_errors(
            {"sourceType": "authority_record", "authoritySubject": "person"}
        )
        self.assertIn("person authority has no personIds", errors)
        self.assertIn("person authority requires identityRelation", errors)


class EveryOrganizationIsSourcedTests(unittest.TestCase):
    """ORG127 and ORG141 exist only as the corporate parents of Grammophon,
    Polydor and Victor, and were the only Organizations citing no source at
    all."""

    @classmethod
    def setUpClass(cls):
        cls.organizations = read_records("organizations.json")
        cls.sources = {item["id"]: item for item in read_records("sources.json")}

    def test_no_organization_is_left_without_a_source(self):
        unsourced = [
            item["id"] for item in self.organizations if not item.get("sourceIds")
        ]
        self.assertEqual(unsourced, [])

    def test_the_two_parents_cite_the_register_that_documents_them(self):
        for org_id, source_id, scheme in (
            ("ORG127", "SRC0931", "gnd"),
            ("ORG141", "SRC0932", "lcnaf"),
        ):
            organization = next(
                item for item in self.organizations if item["id"] == org_id
            )
            self.assertIn(source_id, organization.get("sourceIds") or [])
            source = self.sources[source_id]
            self.assertEqual(source["sourceType"], "authority_record")
            self.assertEqual(source["authoritySubject"], "organization")
            self.assertIn(org_id, source["organizationIds"])
            self.assertIn(
                scheme,
                [entry["scheme"] for entry in organization.get("authorities") or []],
                f"{org_id} cites a {scheme} record it does not link as an identifier",
            )


if __name__ == "__main__":
    unittest.main()
