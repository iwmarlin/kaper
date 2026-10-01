import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
sys.path.insert(0, str(ROOT / "scripts"))

from authority_identifiers import (  # noqa: E402
    AUTHORITY_SCHEMES,
    authority_scheme_for_url,
)
from organization_authorities import (  # noqa: E402
    organization_authority_errors,
)


def records(name):
    return json.loads((PUBLIC / name).read_text(encoding="utf-8"))["records"]


class OrganizationAuthorityNormalizationTests(unittest.TestCase):
    """Organizations were never given the separation People had, so registers
    and institutional homepages shared one field."""

    @classmethod
    def setUpClass(cls):
        cls.organizations = records("organizations.json")
        cls.by_id = {item["id"]: item for item in cls.organizations}

    def test_every_organization_authority_list_is_canonical(self):
        errors = [
            f"{organization['id']}: {error}"
            for organization in self.organizations
            for error in organization_authority_errors(organization)
        ]
        self.assertEqual(errors, [])

    def test_the_packed_field_is_gone(self):
        for organization in self.organizations:
            for legacy in ("authorityUrl", "referenceUrl"):
                self.assertNotIn(legacy, organization, organization["id"])

    def test_one_register_is_one_scheme(self):
        # The Library of Congress provider register arrived as both
        # "LC Providers" and "Library of Congress Providers", and the Polish
        # national library as both "BN" and "Biblioteka Narodowa". A scheme read
        # from the URL cannot split that way.
        self.assertEqual(
            [entry["scheme"] for entry in self.by_id["ORG038"]["authorities"]],
            ["lc_providers"],
        )
        self.assertIn(
            "lc_providers",
            [entry["scheme"] for entry in self.by_id["ORG036"]["authorities"]],
        )
        self.assertEqual(
            [entry["scheme"] for entry in self.by_id["ORG115"]["authorities"]],
            ["bn"],
        )
        self.assertEqual(self.by_id["ORG038"]["authorizedNameSource"], "LC Providers")
        self.assertEqual(self.by_id["ORG115"]["authorizedNameSource"], "BN")

    def test_a_contextual_page_is_not_an_identifier(self):
        # A cooperation agreement PDF and an institutional homepage were filed
        # as authority identifiers on this record.
        organization = self.by_id["ORG077"]
        self.assertNotIn("authorities", organization)
        self.assertEqual(
            sorted(entry["label"] for entry in organization["references"]),
            ["Cooperation agreement", "Official website"],
        )
        for organization in self.organizations:
            for entry in organization.get("references") or []:
                self.assertIsNone(
                    authority_scheme_for_url(entry["url"]),
                    f"{organization['id']} files a register as a reference",
                )

    def test_the_vocabulary_is_closed(self):
        for organization in self.organizations:
            for entry in organization.get("authorities") or []:
                self.assertIn(entry["scheme"], AUTHORITY_SCHEMES, organization["id"])


class AuthoritySchemeDerivationTests(unittest.TestCase):
    """The scheme states which register holds a record, so it is read from the
    URL rather than taken from whatever label the data carried."""

    def test_the_register_is_recognized_from_its_route(self):
        for url, expected in (
            ("https://id.loc.gov/authorities/names/n50049756", "lcnaf"),
            ("https://id.loc.gov/entities/providers/798d6723", "lc_providers"),
            ("https://d-nb.info/gnd/11880300X", "gnd"),
            ("https://catalogue.bnf.fr/ark:/12148/cb12037457t", "bnf"),
            ("https://dbn.bn.org.pl/descriptor-details/9810671370505606", "bn"),
            ("https://data.bn.org.pl/institutions/authorities/1941077", "bn"),
            ("https://viaf.org/viaf/46777365", "viaf"),
            ("https://isni.org/isni/0000000110260840", "isni"),
            ("https://www.wikidata.org/wiki/Q376278", "wikidata"),
        ):
            self.assertEqual(authority_scheme_for_url(url), expected, url)

    def test_a_page_that_is_not_a_register_has_no_scheme(self):
        for url in (
            "https://sbc.org.pl/dlibra",
            "https://www.nypl.org/locations/lpa",
            "https://en.wikipedia.org/wiki/Louis_B._Mayer",
            # The Library of Congress serves more than its name authority file.
            "https://id.loc.gov/vocabulary/languages/pol",
        ):
            self.assertIsNone(authority_scheme_for_url(url), url)

    def test_a_mislabelled_identifier_is_rejected(self):
        errors = organization_authority_errors(
            {
                "id": "ORGTEST",
                "authorities": [
                    {"scheme": "gnd", "url": "https://viaf.org/viaf/46777365"}
                ],
            }
        )
        self.assertTrue(
            any("does not match the register" in error for error in errors), errors
        )

    def test_an_uncontrolled_scheme_is_rejected(self):
        errors = organization_authority_errors(
            {
                "id": "ORGTEST",
                "authorities": [
                    {"scheme": "Official website", "url": "https://example.org/"}
                ],
            }
        )
        self.assertTrue(
            any("is not controlled" in error for error in errors), errors
        )

    def test_registers_out_of_precedence_order_are_rejected(self):
        errors = organization_authority_errors(
            {
                "id": "ORGTEST",
                "authorities": [
                    {"scheme": "viaf", "url": "https://viaf.org/viaf/46777365"},
                    {"scheme": "lcnaf", "url": "https://id.loc.gov/authorities/names/n50049756"},
                ],
            }
        )
        self.assertTrue(
            any("precedence order" in error for error in errors), errors
        )


if __name__ == "__main__":
    unittest.main()
