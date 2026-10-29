from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"

#: The date on which the URAA restored United States copyright in foreign works
#: that were still protected in their source country.
RESTORATION_YEAR = 1996

#: "…ran out at the end of 2003", "…expired in 1998", and the like.
TERM_EXPIRY = re.compile(
    r"ran out at the end of (\d{4})|expired (?:on |in |at the end of )?(?:1 January )?(\d{4})",
    re.I,
)


def media_records() -> list[dict]:
    return json.loads((PUBLIC / "media.json").read_text(encoding="utf-8"))["records"]


class RestoredCopyrightTests(unittest.TestCase):
    """The archive states the rule on M292: a work still protected in its source
    country on 1 January 1996 had its United States copyright restored by the
    URAA for ninety-five years from publication. Four public-domain notes
    computed a source-country term that ran past that date and stopped there,
    which is the step that decides the question for a site published from the
    United States. Two of them reached the right answer anyway; two did not,
    and are restricted now."""

    def test_a_term_running_past_the_restoration_date_reaches_the_united_states(self) -> None:
        offenders = []
        for record in media_records():
            if record.get("rightsStatus") != "public_domain":
                continue
            note = record.get("rightsNote") or ""
            if "United States" in note or "URAA" in note:
                continue
            for match in TERM_EXPIRY.finditer(note):
                year = next((int(group) for group in match.groups() if group), None)
                if year and year > RESTORATION_YEAR:
                    offenders.append(f"{record['id']}: term to {year}, no United States position")
                    break
        self.assertEqual(offenders, [], "a public-domain claim stops at the source country")

    def test_the_two_restored_photographs_are_not_offered_for_reuse(self) -> None:
        # Pour vous 1933 and Excelsior 1936: anonymous French works whose terms
        # ran to 2003 and 2006, so the restored United States terms run to 2028
        # and 2031.
        records = {record["id"]: record for record in media_records()}
        for media_id, until in (("M436", "2028"), ("M433", "2031")):
            with self.subTest(media=media_id):
                record = records[media_id]
                self.assertEqual(record["rightsStatus"], "restricted")
                self.assertIn(until, record["rightsNote"])
                # Locally hosted material with unresolved rights stays off the
                # curated gallery; the validator says so and this says why.
                self.assertEqual(record["galleryStatus"], "detail_only")


if __name__ == "__main__":
    unittest.main()
