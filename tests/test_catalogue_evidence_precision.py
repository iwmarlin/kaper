"""Keep source links within the evidence provided by the cited catalogue."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def table(name):
    data = json.loads((ROOT / "data/public/v1" / f"{name}.json").read_text())
    return {record["id"]: record for record in data["records"]}


class CatalogueEvidencePrecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = table("sources")
        cls.works = table("works")
        cls.songs = table("songs")
        cls.people = table("people")
        cls.contributions = table("contributions")

    def test_jazz_drops_points_directly_to_the_described_volume(self):
        source = self.sources["SRC0154"]
        self.assertEqual(source["primaryUrl"], "https://stabikat.de/Record/1916426948")
        self.assertIn("DMS 266613", source["fullCitation"])
        self.assertIn("1916426948", source["fullCitation"])
        self.assertNotIn("524465657", source["fullCitation"])

    def test_bnf_two_song_notice_is_not_evidence_for_title_song(self):
        source = self.sources["SRC0525"]
        self.assertEqual(source["workIds"], ["W-S104", "W-S106"])
        self.assertEqual(source["songIds"], ["S104", "S106"])
        self.assertNotIn("SRC0525", self.works["W-S105"]["sourceIds"])
        self.assertNotIn("SRC0525", self.songs["S105"]["sourceIds"])
        for cid in ("CON-S105-C-P009", "CON-S105-C-P077", "CON-S105-PUB-ORG030"):
            self.assertNotIn(cid, source["contributionIds"])
            self.assertNotIn("SRC0525", self.contributions[cid]["sourceIds"])
            self.assertIn("SRC0074", self.contributions[cid]["sourceIds"])
        for work in ("W-S104", "W-S106"):
            self.assertIn("SRC0525", self.works[work]["sourceIds"])

    def test_filmportal_source_does_not_directly_name_kaper(self):
        self.assertNotIn("P009", self.sources["SRC0117"]["personIds"])
        self.assertNotIn("SRC0117", self.people["P009"]["sourceIds"])
        self.assertEqual(self.contributions["CON-F004-MRU-P009"]["sourceIds"], ["SRC0520"])

    def test_bnf_addresses_match_the_two_distinct_titles(self):
        for sid, title, ark, notice in (
            ("SRC0063", "La Chanson du pays", "cb430708952", "FRBNF43070895"),
            ("SRC0064", "La vie et l’amour", "cb430696092", "FRBNF43069609"),
        ):
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual(source["title"], title)
                self.assertEqual(source["primaryUrl"], f"https://catalogue.bnf.fr/ark:/12148/{ark}")
                self.assertEqual(source["identifiers"], [{"scheme": "ark", "value": f"ark:/12148/{ark}"}])
                self.assertIn(ark, source["fullCitation"])
                self.assertIn(notice, source["fullCitation"])

    def test_laisse_moi_citation_uses_bnf_genre(self):
        citation = self.sources["SRC0061"]["fullCitation"]
        self.assertIn("tango chanté", citation)
        self.assertNotIn("slow-fox-trot", citation)

    def test_collective_bnf_notice_is_not_individual_lyricist_evidence(self):
        source = self.sources["SRC0065"]
        for work, people, individual in (
            ("112", ("P031", "P052"), "SRC0057"),
            ("113", ("P031", "P051", "P052"), "SRC0058"),
            ("114", ("P031", "P049"), "SRC0059"),
            ("115", ("P031", "P051", "P052"), "SRC0060"),
        ):
            for person in people:
                cid = f"CON-S{work}-L-{person}"
                with self.subTest(contribution=cid):
                    self.assertNotIn(cid, source["contributionIds"])
                    self.assertNotIn("SRC0065", self.contributions[cid]["sourceIds"])
                    self.assertIn(individual, self.contributions[cid]["sourceIds"])
            self.assertIn(f"W-S{work}", source["workIds"])
        self.assertNotIn("P051", source.get("personIds", []))
        self.assertNotIn("SRC0065", self.people["P051"]["sourceIds"])

    def test_shared_bnf_holding_has_one_source_and_both_catalogue_notices(self):
        self.assertNotIn("SRC0526", self.sources)
        source = self.sources["SRC0074"]
        self.assertEqual(source["workIds"], ["W-S105", "W-S107"])
        self.assertEqual(source["songIds"], ["S105", "S107"])
        self.assertIn("SRC0074", self.works["W-S107"]["sourceIds"])
        self.assertIn("SRC0074", self.songs["S107"]["sourceIds"])
        for cid in ("CON-S107-C-P009", "CON-S107-C-P077", "CON-S107-L-P006", "CON-S107-PUB-ORG030"):
            self.assertIn(cid, source["contributionIds"])
            self.assertIn("SRC0074", self.contributions[cid]["sourceIds"])
        self.assertIn("FOL-VM7-29245", source["researchNote"])
        self.assertIn("https://catalogue.bnf.fr/ark:/12148/cb43069617p",
                      [link["url"] for link in source["additionalLinks"]])
        self.assertEqual({identifier["value"] for identifier in source["identifiers"]},
                         {"ark:/12148/cb43070896d", "ark:/12148/cb43069617p"})

    def test_orchestral_notices_do_not_attest_unlisted_lyricists(self):
        for sid, cid, remaining in (
            ("SRC0072", "CON-S111-L-P065", "SRC0540"),
            ("SRC0073", "CON-S036-L-P005", "SRC0373"),
        ):
            with self.subTest(source=sid):
                self.assertNotIn(cid, self.sources[sid]["contributionIds"])
                self.assertNotIn(sid, self.contributions[cid]["sourceIds"])
                self.assertIn(remaining, self.contributions[cid]["sourceIds"])
        self.assertIn("CON-S111-C-P009", self.sources["SRC0072"]["contributionIds"])
        self.assertIn("SRC0072", self.contributions["CON-S111-C-P009"]["sourceIds"])

    def test_orchestral_edition_is_not_conflated_with_vocal_edition(self):
        source = self.sources["SRC0495"]
        self.assertNotIn("BnF also records", source["fullCitation"])
        self.assertIn("1930", source["fullCitation"])
        self.assertIn("1931 orchestral arrangement", source["researchNote"])
        self.assertIn("https://catalogue.bnf.fr/ark:/12148/cb43244705p",
                      [link["url"] for link in source["additionalLinks"]])

    def test_legacy_source_url_is_regenerated_but_not_indexed(self):
        page = (ROOT / "records/source/SRC0526/index.html").read_text()
        self.assertIn('url=../SRC0074/', page)
        self.assertIn('name="robots" content="noindex"', page)
        sitemap = (ROOT / "sitemap.xml").read_text()
        self.assertNotIn("/records/source/SRC0526/", sitemap)
        self.assertIn("/records/source/SRC0074/", sitemap)


if __name__ == "__main__":
    unittest.main()
