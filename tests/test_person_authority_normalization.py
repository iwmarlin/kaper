import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
sys.path.insert(0, str(ROOT / "scripts"))

from authority_sources import authority_source_semantic_errors  # noqa: E402
from authority_identifiers import authority_urls  # noqa: E402
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
                entry
                for entry in person.get("authorities") or []
                if entry.get("scheme") == "bnf"
            ]
            self.assertLessEqual(len(bnf_links), 1, person["id"])

    def test_every_authorized_person_heading_identifies_its_source(self):
        missing = [
            person["id"]
            for person in self.people
            if person.get("authorizedName") and not person.get("authorizedNameSource")
        ]
        self.assertEqual(missing, [])

    def test_jesse_greer_has_lcnaf_supported_life_dates(self):
        greer = self.people_by_id["P187"]
        self.assertEqual(greer.get("birthYear"), 1896)
        self.assertEqual(greer.get("deathYear"), 1970)
        self.assertEqual(greer.get("lifeDatesCertainty"), "confirmed")
        self.assertIn("SRC0936", greer.get("sourceIds", []))
        source = self.sources_by_id["SRC0936"]
        self.assertEqual(source.get("authoritySubject"), "person")
        self.assertEqual(source.get("identityRelation"), "same")
        self.assertEqual(source.get("personIds"), ["P187"])
        self.assertIn("26 August 1896", source.get("researchNote", ""))
        self.assertIn("4 October 1970", source.get("researchNote", ""))

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

    def test_redundant_authority_sources_do_not_duplicate_person_badges(self):
        self.assertNotIn("SRC0589", self.sources_by_id)
        self.assertNotIn("SRC0590", self.sources_by_id)
        self.assertNotIn("SRC0589", self.people_by_id["P006"].get("sourceIds", []))
        self.assertNotIn("SRC0590", self.people_by_id["P031"].get("sourceIds", []))
        self.assertIn(
            "https://data.bnf.fr/fr/ark:/12148/cb148356206",
            authority_urls(self.people_by_id["P006"]),
        )
        self.assertIn(
            "https://data.bnf.fr/fr/ark:/12148/cb14785637s",
            authority_urls(self.people_by_id["P031"]),
        )

    def test_work_authority_is_not_presented_as_person_identity_evidence(self):
        source = self.sources_by_id["SRC0532"]
        self.assertEqual(source["authoritySubject"], "work")
        self.assertNotIn("P124", source.get("personIds", []))
        self.assertNotIn("SRC0532", self.people_by_id["P124"].get("sourceIds", []))
        self.assertIn("CON-F056-D-P124", source.get("contributionIds", []))

    def test_work_authority_rejects_a_direct_person_link(self):
        errors = authority_source_semantic_errors(
            {
                "sourceType": "authority_record",
                "authoritySubject": "work",
                "workIds": ["W-TEST"],
                "personIds": ["P-TEST"],
                "contributionIds": ["CON-TEST"],
            }
        )
        self.assertIn(
            "work authority must not carry direct personIds; "
            "link person credits through contributionIds",
            errors,
        )

    def test_paul_mann_date_note_compares_the_two_documented_authorities(self):
        note = self.sources_by_id["SRC0627"]["researchNote"]
        self.assertIn("LexM gives 3 September 1910", note)
        self.assertIn("GND gives 3 October 1910", note)
        self.assertNotIn("Wikipedia", note)

    def test_confirmed_life_date_sources_use_the_life_date_section(self):
        for person_id, source_id in (("P126", "SRC0548"), ("P178", "SRC0845")):
            person = self.people_by_id[person_id]
            self.assertIn(source_id, person.get("lifeDatesSourceIds", []))
            self.assertTrue(person.get("lifeDatesNote"))
        self.assertEqual(
            self.sources_by_id["SRC0856"]["researchNoteType"],
            "authority_note",
        )

    def test_only_accepted_person_authorities_reach_the_fact_block(self):
        self.assertEqual(
            authority_source_alignment_errors(self.people, self.sources),
            [],
        )
        macdonald = self.people_by_id["P139"]
        self.assertIn(
            "https://catalogue.bnf.fr/ark:/12148/cb13757145r",
            authority_urls(macdonald),
        )
        self.assertEqual(macdonald.get("authorizedNameSource"), "LCNAF")
        self.assertNotIn(
            self.sources_by_id["SRC0632"]["primaryUrl"],
            authority_urls(self.people_by_id["P079"]),
        )
        self.assertNotIn(
            self.sources_by_id["SRC0686"]["primaryUrl"],
            authority_urls(self.people_by_id["P111"]),
        )

    def test_rejected_identity_and_viaf_heading_claims_do_not_return(self):
        self.assertNotIn(
            "https://www.wikidata.org/wiki/Q95678216",
            authority_urls(self.people_by_id["P156"]),
        )
        for person in self.people:
            self.assertNotIn(
                str(person.get("authorizedNameSource") or "").casefold(),
                {"viaf", "viaf main heading"},
                person["id"],
            )
        self.assertEqual(self.people_by_id["P004"]["authorizedNameSource"], "local heading")
        self.assertEqual(self.people_by_id["P014"]["authorizedNameSource"], "local heading")
        # Groener's heading now has a contributing register: the BnF notice.
        self.assertEqual(self.people_by_id["P021"]["authorizedNameSource"], "BnF")
        self.assertIn("Dutch National Thesaurus", self.people_by_id["P096"]["authorizedNameSource"])


if __name__ == "__main__":
    unittest.main()
