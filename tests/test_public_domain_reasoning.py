from __future__ import annotations

import datetime
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



class StatedTermTests(unittest.TestCase):
    """Once a note says which year a restored term ends, the claim has a date on
    it and the calendar will overtake it. Fourteen Illustrierter Film-Kurier
    covers were decided by the same German term and the same URAA restoration,
    and the three published in 1931 come free at the start of 2027. These tests
    fail on the day a stated term runs out, which is the notice that the status
    has to be rewritten, not a fault in the data."""

    #: "…to the end of 2027", "…ran out at the end of 2006".
    TERM_END = re.compile(r"the end of (\d{4})")

    @classmethod
    def setUpClass(cls) -> None:
        cls.media = media_records()
        cls.this_year = datetime.date.today().year

    def united_states_years(self, note: str) -> list[int]:
        """Years stated in the sentences that speak about United States law.

        A note may compute several terms — M125 prints an edition free in the
        United States since 2022 whose composition is protected in the European
        Union until 2053 — so the sentence decides which year is operative.
        """
        years: list[int] = []
        for sentence in re.split(r"(?<=[.])\s+", note):
            if "United States" in sentence or "URAA" in sentence:
                years += [int(year) for year in self.TERM_END.findall(sentence)]
        return years

    def test_a_stated_term_agrees_with_the_calendar(self) -> None:
        offenders = []
        checked = 0
        for record in self.media:
            status = record.get("rightsStatus")
            if status not in {"public_domain", "restricted"}:
                continue
            years = self.united_states_years(record.get("rightsNote") or "")
            if not years:
                continue
            checked += 1
            ends = years[-1]
            if status == "restricted" and ends < self.this_year:
                offenders.append(f"{record['id']}: restricted, term ran out in {ends}")
            if status == "public_domain" and ends >= self.this_year:
                offenders.append(f"{record['id']}: public domain, term runs to {ends}")
        self.assertGreater(checked, 25, "no stated terms were checked")
        self.assertEqual(offenders, [], "a stated term no longer matches the status")

    def test_a_computed_term_says_where_it_leaves_the_united_states(self) -> None:
        offenders = []
        for record in self.media:
            if record.get("rightsStatus") not in {"public_domain", "restricted",
                                                  "provider_terms"}:
                continue
            note = record.get("rightsNote") or ""
            if not self.TERM_END.search(note):
                continue
            if "United States" not in note and "URAA" not in note:
                offenders.append(f"{record['id']}: a term is computed, none of it ours")
        self.assertEqual(offenders, [], "a note computes a term and stops abroad")


class ProviderTermsTests(unittest.TestCase):
    """A digitising library licenses its scan, not the work on the page. Gallica
    grants free non-commercial reuse under conditions governed by French law,
    which exclude documents protected by a third party and leave reuse abroad to
    the user; ANNO says the Österreichische Nationalbibliothek asserts no
    exploitation right of its own and that third-party rights must be cleared
    individually. Nineteen records rested on those terms alone, and thirteen of
    them carried a 1925-1952 press photograph, advertisement or article whose
    restored United States term had not been looked at. A provider's permission
    is an answer about the scan; the note has to answer about the work too."""

    #: Either the note reaches United States law, or it says no work arises.
    REACHES_THE_WORK = re.compile(r"United States|URAA|no protected work|rather than a work",
                                  re.I)

    def test_provider_terms_also_answer_for_the_underlying_work(self) -> None:
        offenders = []
        checked = 0
        for record in media_records():
            if record.get("rightsStatus") != "provider_terms":
                continue
            checked += 1
            if not self.REACHES_THE_WORK.search(record.get("rightsNote") or ""):
                offenders.append(f"{record['id']}: rests on the provider alone")
        self.assertGreater(checked, 3, "no provider-terms records were checked")
        self.assertEqual(offenders, [], "a provider's terms are offered as the whole answer")


class GalleryRightsTests(unittest.TestCase):
    """A gallery container carries a rights status of its own, and two of them
    said public domain over members that were not. M032 gathered five items
    served under provider terms and one in the public domain; M030 gathered
    nine and a tenth under provider terms. M031 and M033 had the same mixture
    and said mixed_rights, which is the answer."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.media = media_records()
        cls.by_id = {record["id"]: record for record in cls.media}

    def members(self, gallery: dict) -> list[dict]:
        paths = {path for path in (gallery.get("assetPaths") or []) if path}
        names = {path.split("/")[-1] for path in paths}
        out = []
        for record in self.media:
            if record["id"] == gallery["id"] or record.get("mediaType") == "document_gallery":
                continue
            own = [record.get("assetPath"), *(record.get("assetPaths") or [])]
            if any(p in paths or str(p).split("/")[-1] in names for p in own if p):
                out.append(record)
        return out

    def test_a_gallery_does_not_claim_more_than_its_members(self) -> None:
        offenders = []
        checked = 0
        for gallery in self.media:
            if gallery.get("mediaType") != "document_gallery":
                continue
            statuses = {record.get("rightsStatus") for record in self.members(gallery)}
            if not statuses:
                continue
            checked += 1
            claimed = gallery.get("rightsStatus")
            if len(statuses) > 1:
                if claimed != "mixed_rights":
                    offenders.append(f"{gallery['id']}: claims {claimed} over {sorted(statuses)}")
            elif claimed != statuses.pop() and claimed != "mixed_rights":
                offenders.append(f"{gallery['id']}: claims {claimed} over its members")
        self.assertGreater(checked, 3, "no galleries were checked")
        self.assertEqual(offenders, [], "a gallery claims rights its members do not have")

if __name__ == "__main__":
    unittest.main()
