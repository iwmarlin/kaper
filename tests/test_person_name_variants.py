from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"


def records(name: str) -> list[dict]:
    return json.loads((PUBLIC / name).read_text(encoding="utf-8"))["records"]


class EvidenceContextVocabularyTests(unittest.TestCase):
    """The field says where a variant form is attested, and it had two words
    for one thing: authority_file on six records and authority_record on
    eight, used interchangeably. It is the fault that film_song and film_songs
    were, in a table where the reader is being told what the evidence is."""

    #: Closed on purpose. A new context is a decision about what counts as
    #: evidence for a name, so it is made here and not by typing it into a
    #: record. authority_record matches the sourceType of the same name.
    VOCABULARY = frozenset({
        "archival_document",
        "authority_record",
        "biographical_database",
        "copyright_or_registration",
        "filmographic_database",
        "newspaper_or_periodical",
        "other",
        "recording_label",
        "secondary_literature",
        "sheet_music_or_printed_credit",
    })

    @classmethod
    def setUpClass(cls) -> None:
        cls.variants = records("person-name-variants.json")
        cls.sources = {record["id"]: record for record in records("sources.json")}

    def test_every_context_is_one_of_the_declared_ones(self) -> None:
        used = {record.get("evidenceContext") for record in self.variants}
        self.assertEqual(used - self.VOCABULARY, set())

    def test_the_superseded_spelling_is_gone(self) -> None:
        offenders = [
            record["id"] for record in self.variants
            if record.get("evidenceContext") == "authority_file"
        ]
        self.assertEqual(offenders, [])

    def test_a_variant_that_cites_an_authority_links_one(self) -> None:
        """Four records said their evidence was an authority record while
        linking a press item, a filmographic database or a sheet-music
        catalogue instead, and two of those — the birth names of Deanna Durbin
        and Judy Garland — linked nothing that carried the name at all."""
        offenders = []
        for record in self.variants:
            if record.get("evidenceContext") != "authority_record":
                continue
            kinds = {
                self.sources[source].get("sourceType")
                for source in (record.get("sourceIds") or [])
                if source in self.sources
            }
            if "authority_record" not in kinds:
                offenders.append(f"{record['id']}: {sorted(kinds)}")
        self.assertEqual(offenders, [], "a variant cites an authority it does not link")


class AuthorizedHeadingTests(unittest.TestCase):
    """A variant recording a catalogue heading has to spell it as the
    catalogue does. PNV0023 dropped the comma before the life dates, which
    neither the Staatsbibliothek record it cites nor LCNAF n79075647 does."""

    def test_the_kaper_catalogue_heading_matches_both_catalogues(self) -> None:
        variant = next(
            record for record in records("person-name-variants.json")
            if record["id"] == "PNV0023"
        )
        self.assertEqual(variant["variantName"], "Kaper, Bronislaw, 1902-1983")
        self.assertEqual(variant["attestedWording"], variant["variantName"])

    def test_an_lcnaf_heading_keeps_the_archive_s_own_date_convention(self) -> None:
        # All 133 people whose authorized name comes from LCNAF carry it
        # without the authority's date qualifier. The convention is what makes
        # PNV0023 worth recording separately, so it is worth holding.
        offenders = [
            person["id"] for person in records("people.json")
            if person.get("authorizedNameSource") == "LCNAF"
            and any(character.isdigit() for character in person.get("authorizedName", ""))
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
