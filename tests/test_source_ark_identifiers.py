"""An ark that is already in the address belongs in the identifiers."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARK = re.compile(r"(ark:/\d+/[^/?#\s]+)")


def sources() -> list[dict]:
    path = ROOT / "data/public/v1/sources.json"
    return json.loads(path.read_text(encoding="utf-8"))["records"]


class SourceArkIdentifierTests(unittest.TestCase):
    """Seventy-seven sources carry an ark in their primary address and
    fifty-six recorded it in identifiers, which is where a structured export
    reads it from. The other twenty-one left it in the URL alone, so the same
    fact was machine-readable for some BnF, Gallica, OAC and UCLA records and
    not for others. Nothing had to be looked up to close that: the ark is in
    the address, character for character."""

    def test_an_ark_in_the_address_is_recorded_as_an_identifier(self) -> None:
        offenders = []
        checked = 0
        for source in sources():
            match = ARK.search(str(source.get("primaryUrl") or ""))
            if not match:
                continue
            checked += 1
            arks = [identifier.get("value")
                    for identifier in (source.get("identifiers") or [])
                    if identifier.get("scheme") == "ark"]
            if not arks:
                offenders.append(f"{source['id']}: {match.group(1)} only in the URL")
            elif match.group(1) not in arks:
                offenders.append(f"{source['id']}: URL says {match.group(1)}, identifiers say {arks}")
        self.assertGreater(checked, 50, "no ark addresses were checked")
        self.assertEqual(offenders, [], "an ark is in the address but not in the identifiers")

    def test_a_recorded_ark_is_well_formed(self) -> None:
        offenders = [f"{source['id']}: {identifier.get('value')!r}"
                     for source in sources()
                     for identifier in (source.get("identifiers") or [])
                     if identifier.get("scheme") == "ark"
                     and not re.fullmatch(r"ark:/\d+/[A-Za-z0-9._-]+", str(identifier.get("value")))]
        self.assertEqual(offenders, [], "an ark identifier is not an ark")


if __name__ == "__main__":
    unittest.main()
