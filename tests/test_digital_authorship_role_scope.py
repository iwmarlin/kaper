"""Qualified uploads and undifferentiated writer fields are not exact roles."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from recording_sources import reviewed_digital_authorship_errors
from normalize_sources import normalized_source


class DigitalAuthorshipRoleScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def records(name):
            return {r["id"]: r for r in json.loads((ROOT / "data/public/v1" /
                    (name + ".json")).read_text())["records"]}
        cls.sources = records("sources")
        cls.credits = records("contributions")
        cls.names = records("person-name-variants")
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    def test_exact_writer_roles_retain_copyright_evidence(self):
        source = self.sources["SRC0815"]
        self.assertIn("both Author and Composer", source["researchNote"])
        self.assertEqual(source["contributionIds"], ["CON-S162-P-P173"])
        self.assertEqual(normalized_source(source), source)
        self.assertEqual(reviewed_digital_authorship_errors(source, self.credits), [])
        for cid in ("CON-S162-C-P009", "CON-S162-C-P077",
                    "CON-S162-L-P025", "CON-S162-L-P071"):
            with self.subTest(credit=cid):
                c = self.credits[cid]
                self.assertEqual(c["sourceIds"], ["SRC0275"])
                self.assertIn(cid, self.sources["SRC0275"]["contributionIds"])
                self.assertEqual(c["certainty"], "confirmed")
                self.assertIn(cid, self.overrides["linkRemovals"]["Sources"]["SRC0815"]["fields"]["contributionIds"])
                self.assertEqual(self.overrides["linkRemovals"]["Contributions"][cid]["fields"]["sourceIds"], ["SRC0815"])
                bad = dict(source, contributionIds=source["contributionIds"] + [cid])
                self.assertTrue(reviewed_digital_authorship_errors(bad, self.credits))
                credits = copy.deepcopy(self.credits)
                credits[cid]["sourceIds"].append("SRC0815")
                self.assertTrue(reviewed_digital_authorship_errors(source, credits))

    def test_pseudonym_attestation_is_not_a_literal_personal_name_credit(self):
        for cid in ("CON-S071-C-P009", "CON-S071-C-P077"):
            c = self.credits[cid]
            self.assertEqual(c["nameAsPrinted"], "Bob Henders")
            self.assertEqual(c["sourceIds"], ["SRC0209", "SRC0790"])
            self.assertEqual(c["certainty"], "confirmed")
            self.assertIn("PNV0005", c["scopeNote"])
            self.assertIn("not an explicit personal-name credit", c["scopeNote"])
            self.assertIn("SRC0878", self.names["PNV0005"]["sourceIds"])
            self.assertEqual(self.overrides["records"]["Contributions"][cid]["fields"]["scopeNote"], c["scopeNote"])

    def test_polish_upload_attributions_remain_probable(self):
        for cid in ("CON-S218-C-P009", "CON-S218-C-P077", "CON-S218-L-P175"):
            c = self.credits[cid]
            self.assertEqual(c["evidenceContext"], ["online_recording"])
            self.assertEqual(c["certainty"], "probable")
            self.assertEqual(c["sourceIds"], ["SRC0759"])
            self.assertIn(cid, self.sources["SRC0759"]["contributionIds"])
            self.assertEqual(self.overrides["records"]["Contributions"][cid]["fields"]["evidenceContext"], c["evidenceContext"])


if __name__ == "__main__":
    unittest.main()
