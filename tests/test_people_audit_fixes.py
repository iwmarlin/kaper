import json
import re
import unittest
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data/public/v1"


def table(name):
    return {r["id"]: r for r in json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))["records"]}


class PeopleAuditFixTests(unittest.TestCase):
    """Fixes from docs/people-audit.md, findings 1 to 5."""

    @classmethod
    def setUpClass(cls):
        cls.people, cls.organizations = table("people"), table("organizations")
        cls.credits, cls.sources = table("contributions"), table("sources")

    def test_an_unpublished_registration_names_a_claimant_not_a_publisher(self):
        for credit in self.credits.values():
            if credit["role"] != "publisher":
                continue
            entries = [self.sources[s] for s in credit["sourceIds"]
                       if self.sources[s]["sourceType"] == "copyright_catalogue"]
            with self.subTest(credit=credit["id"]):
                self.assertFalse(
                    entries and all(re.search(r"E\s*unp\.", s["fullCitation"]) for s in entries),
                    "a publisher credit rests on unpublished registrations alone",
                )

    def test_the_claimant_is_the_firm_the_entry_names(self):
        for song in ("S154", "S168"):
            claimant = self.credits[f"CON-{song}-CC-ORG001"]
            self.assertEqual(claimant["role"], "copyright_claimant")
            self.assertIn("Metro-Goldwyn-Mayer", claimant["nameAsPrinted"])
        self.assertNotIn("CON-S154-PUB-ORG035", self.credits)
        # Sieghardt's catalogue, not the registration, names Robbins.
        self.assertEqual(self.credits["CON-S168-PUB-ORG035"]["sourceIds"], ["SRC0373"])

    def test_the_language_area_register_supplies_the_heading(self):
        for person_id, heading, register in (
            ("P010", "Pothier, Charles-Louis", "BnF"),
            ("P032", "Legrand, H. André", "BnF"),
            ("P033", "Clouzot, Henri-Georges", "BnF"),
            ("P072", "Feral, Roger", "BnF"),
            ("P109", "Lemarchand, Henri", "BnF"),
            ("P111", "Ermend-Bonnal", "BnF"),
            ("P054", "Colpet, Max", "GND"),
            ("P056", "Ophüls, Max", "GND"),
            ("P148", "Wolfes, Helmut", "GND"),
            ("P152", "Weiss, Stephan", "GND"),
            ("P205", "Dajos, Béla", "GND"),
        ):
            person = self.people[person_id]
            with self.subTest(person=person_id):
                self.assertEqual((person["authorizedName"], person["authorizedNameSource"]), (heading, register))
                scheme = register.lower()
                self.assertTrue(any(a["scheme"] == scheme for a in person["authorities"]))

    def test_kolpe_keeps_the_name_his_credits_print(self):
        person = self.people["P054"]
        self.assertEqual(person["displayName"], "Max Kolpe")
        self.assertIn("PNV0079", person["nameVariantIds"])

    def test_identifiers_lead_to_the_right_record(self):
        bonnal = [a["url"] for a in self.people["P111"]["authorities"]]
        self.assertIn("https://catalogue.bnf.fr/ark:/12148/cb14793454j", bonnal)
        self.assertNotIn("https://catalogue.bnf.fr/ark:/12148/cb16557102j", bonnal)
        self.assertNotIn("authorities", self.organizations["ORG048"])

    def test_a_named_register_is_linked(self):
        for record, scheme in ((self.people["P069"], "bnf"), (self.organizations["ORG030"], "bnf")):
            self.assertTrue(any(a["scheme"] == scheme for a in record["authorities"]))
        self.assertEqual(self.organizations["ORG030"]["authorizedName"], "Éditions Coda et Max")
        for org_id in ("ORG032", "ORG048", "ORG246"):
            self.assertEqual(self.organizations[org_id]["authorizedNameSource"], "local heading")

    def test_conflicting_registers_make_dates_disputed(self):
        for person_id, source_id in (("P133", "SRC0968"), ("P032", "SRC0969")):
            person = self.people[person_id]
            with self.subTest(person=person_id):
                self.assertEqual(person["lifeDatesCertainty"], "disputed")
                self.assertEqual(person["lifeDatesSourceIds"], [source_id])

    def test_polish_headings_follow_bn(self):
        for person_id, heading in (("P009", "Kaper, Bronisław"), ("P119", "Gold, Henryk"),
                                   ("P003", "Włast, Andrzej"), ("P117", "Kiepura, Jan"),
                                   ("P131", "Śmidowicz, Józef"), ("P159", "Tuwim, Julian"),
                                   ("P199", "Fitelberg, Jerzy")):
            person = self.people[person_id]
            with self.subTest(person=person_id):
                self.assertEqual((person["authorizedName"], person["authorizedNameSource"]), (heading, "BN"))
                self.assertTrue(any(a["scheme"] == "bn" for a in person["authorities"]))
        self.assertEqual(self.people["P119"]["lifeDatesCertainty"], "disputed")

    def test_register_qualifiers_stay_in_the_heading(self):
        self.assertEqual(self.people["P116"]["authorizedName"], "Mayer, Louis B. (Louis Burt)")
        self.assertEqual(self.organizations["ORG167"]["authorizedName"], "Gaumont British Picture Corp.")
        self.assertEqual(self.organizations["ORG132"]["authorizedNameSource"], "BN")

    def test_landau_is_the_director_bnf_links_to_his_film(self):
        person = self.people["P011"]
        self.assertEqual((person["birthYear"], person["deathYear"]), (1890, 1969))
        self.assertIn("SRC0970", person["sourceIds"])
        self.assertIn("Madame ne veut pas d’enfants", self.sources["SRC0970"]["researchNote"])


if __name__ == "__main__":
    unittest.main()
