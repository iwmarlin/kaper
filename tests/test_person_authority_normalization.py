import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
sys.path.insert(0, str(ROOT / "scripts"))

from authority_sources import authority_source_semantic_errors  # noqa: E402
from person_authorities import (  # noqa: E402
    authority_source_alignment_errors,
    person_authority_errors,
)


def records(name):
    return json.loads((PUBLIC / name).read_text(encoding="utf-8"))["records"]


class PersonAuthorityNormalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.people = records("people.json")
        cls.sources = records("sources.json")
        cls.people_by_id = {item["id"]: item for item in cls.people}
        cls.sources_by_id = {item["id"]: item for item in cls.sources}

    def test_every_person_authority_stack_is_canonical(self):
        errors = [
            f"{person['id']}: {error}"
            for person in self.people
            for error in person_authority_errors(person)
        ]
        self.assertEqual(errors, [])
        for person in self.people:
            bnf_links = [
                line for line in str(person.get("authorityUrl") or "").splitlines()
                if line.startswith("BnF: ")
            ]
            self.assertLessEqual(len(bnf_links), 1, person["id"])

    def test_authority_source_semantics_are_explicit(self):
        errors = [
            f"{source['id']}: {error}"
            for source in self.sources
            for error in authority_source_semantic_errors(source)
        ]
        self.assertEqual(errors, [])
        self.assertEqual(self.sources_by_id["SRC0532"]["authoritySubject"], "work")
        self.assertNotIn("identityRelation", self.sources_by_id["SRC0532"])
        self.assertEqual(self.sources_by_id["SRC0632"]["identityRelation"], "candidate")
        self.assertEqual(self.sources_by_id["SRC0686"]["identityRelation"], "alternate")

    def test_only_accepted_person_authorities_reach_the_fact_block(self):
        self.assertEqual(
            authority_source_alignment_errors(self.people, self.sources),
            [],
        )
        macdonald = self.people_by_id["P139"]
        self.assertIn("https://catalogue.bnf.fr/ark:/12148/cb13757145r", macdonald["authorityUrl"])
        self.assertEqual(macdonald.get("authorizedNameSource"), "BnF")
        self.assertNotIn(
            self.sources_by_id["SRC0632"]["primaryUrl"],
            self.people_by_id["P079"].get("authorityUrl", ""),
        )
        self.assertNotIn(
            self.sources_by_id["SRC0686"]["primaryUrl"],
            self.people_by_id["P111"].get("authorityUrl", ""),
        )

    def test_rejected_identity_and_viaf_heading_claims_do_not_return(self):
        self.assertNotIn("Q95678216", self.people_by_id["P156"].get("authorityUrl", ""))
        for person in self.people:
            self.assertNotIn(
                str(person.get("authorizedNameSource") or "").casefold(),
                {"viaf", "viaf main heading"},
                person["id"],
            )
        self.assertEqual(self.people_by_id["P004"]["authorizedNameSource"], "local heading")
        self.assertEqual(self.people_by_id["P014"]["authorizedNameSource"], "local heading")
        self.assertEqual(self.people_by_id["P021"]["authorizedNameSource"], "local heading")
        self.assertIn("Dutch National Thesaurus", self.people_by_id["P096"]["authorizedNameSource"])


if __name__ == "__main__":
    unittest.main()
