from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
sys.path.insert(0, str(ROOT / "scripts"))

from authority_identifiers import scheme_label  # noqa: E402

# The registers docs/authority-headings.md names in precedence order.  When a
# heading is transcribed from one of them, the record has to link it, so that a
# reader can open what the field claims.  Headings taken from a register outside
# that list — LexM, the Dutch national thesaurus — are named in the field alone
# until an identifier for them is recorded.
LINKED_REGISTERS = {"LCNAF", "GND", "BnF", "BN"}

# Records that still name a register without an identifier for it.  Each was
# left open deliberately and is listed in docs/authority-heading-review.md:
# the BnF catalogue could not be read when the others were resolved.
PROVENANCE_GAPS = {"P069", "ORG030", "ORG032"}


class AuthorityHeadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.people = json.loads(
            (PUBLIC / "people.json").read_text(encoding="utf-8")
        )["records"]
        cls.organizations = json.loads(
            (PUBLIC / "organizations.json").read_text(encoding="utf-8")
        )["records"]

    def registers(self, record: dict) -> list[str]:
        # The register is read back through the one vocabulary that names it,
        # so a test cannot agree with a spelling the data invented.
        return [
            scheme_label(str(entry.get("scheme")))
            for entry in record.get("authorities") or []
        ]

    def test_a_named_register_is_a_linked_register(self) -> None:
        for record in (*self.people, *self.organizations):
            source = record.get("authorizedNameSource")
            if source not in LINKED_REGISTERS or record["id"] in PROVENANCE_GAPS:
                continue
            self.assertIn(
                source,
                self.registers(record),
                msg=f"{record['id']} names {source} as its heading source but links no {source} record",
            )

    def test_a_person_without_a_register_has_a_local_heading(self) -> None:
        for person in self.people:
            if person.get("authorities"):
                continue
            self.assertEqual(
                person.get("authorizedNameSource"),
                "local heading",
                msg=f"{person['id']} has no register and does not say its heading is local",
            )

    def test_registers_are_listed_in_precedence_order(self) -> None:
        order = ["LCNAF", "GND", "BnF", "BN"]
        for record in self.people:
            ranked = [order.index(label) for label in self.registers(record) if label in order]
            self.assertEqual(
                ranked,
                sorted(ranked),
                msg=f"{record['id']} lists its registers out of precedence order",
            )


if __name__ == "__main__":
    unittest.main()
