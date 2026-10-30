"""Guard checked issue dates, visible labels and separate physical issues."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_sources import normalized_source

REVIEWED = ("SRC0005", "SRC0006", "SRC0708", "SRC0743", "SRC0748")


class ElectrolaVictorReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for table in ("sources", "media", "contributions"):
            rows = json.loads((ROOT / "data/public/v1" / f"{table}.json").read_text())["records"]
            setattr(cls, table, {r["id"]: r for r in rows})
        cls.overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())

    def test_electrola_issue_months_are_not_session_dates(self):
        for sid, date in (("SRC0005", "1931-10"), ("SRC0708", "1931-06"),
                          ("SRC0743", "1931-01")):
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                                 (date, "issue", "confirmed"))
                urls = [source["primaryUrl"]] + [x["url"] for x in source.get("additionalLinks", [])]
                self.assertIn("http://musiktiteldb.de/Label/EMI_EG02.html", urls)
        self.assertIn("no recording date", self.sources["SRC0743"]["researchNote"])

    def test_balalaika_caption_no_longer_asserts_the_wrong_year(self):
        caption = self.media["M005"]["publicCaption"]
        self.assertIn("October 1931", caption)
        self.assertNotIn("2392, 1932", caption)
        self.assertIn("60-1717", self.sources["SRC0005"]["researchNote"])
        self.assertIn("00499-1", self.sources["SRC0005"]["researchNote"])

    def test_bolig_supplies_the_exact_victor_issue_date(self):
        source = self.sources["SRC0006"]
        self.assertEqual((source["date"], source["dateRole"], source["dateQualifier"]),
                         ("1935-05-08", "issue", "confirmed"))
        for text in ("29 April 1935", "8 May 1935", "John R. Bolig", "PDF p. 20"):
            self.assertIn(text, source["researchNote"])
        self.assertTrue(source["additionalLinks"][0]["url"].endswith("_v5.pdf#page=20"))
        self.assertIn("DAHR website itself was unavailable", source["researchNote"])
        self.assertIn("copy and take are not independently established", source["researchNote"])

    def test_refrain_conflict_is_between_label_and_catalogue(self):
        source = self.sources["SRC0708"]
        self.assertIn("Tanz-Orchester mit Refraingesang", source["researchNote"])
        self.assertIn("label itself", source["researchNote"])
        self.assertIn("Instr.", source["researchNote"])
        self.assertIn("no refrain singer is identified", source["researchNote"])
        self.assertIn("visible label", self.media["M348"]["publicCaption"])
        self.assertNotIn("with refrain vocal, linked", self.media["M348"]["description"])

    def test_american_jones_label_remains_independent_and_undated(self):
        source = self.sources["SRC0748"]
        self.assertNotIn("date", source)
        self.assertEqual((source["dateRole"], source["dateQualifier"]), ("issue", "unknown"))
        self.assertEqual(source["publication"], "RCA Victor")
        self.assertIn("4381-B", source["fullCitation"])
        self.assertNotIn("1938", source["fullCitation"])
        self.assertFalse(source.get("mediaIds"))
        self.assertFalse(any("SRC0748" in m.get("sourceIds", []) for m in self.media.values()))
        credit = self.contributions["CON-S118-P-P173"]
        self.assertEqual(credit["sourceIds"], ["SRC0748", "SRC0784"])
        self.assertEqual(credit["evidenceContext"], ["recording_label"])
        self.assertIn("separate physical issues", credit["scopeNote"])

    def test_recordings_are_not_used_as_sheet_music_publisher_evidence(self):
        for sid, cid, remaining in (
            ("SRC0005", "CON-S045-PUB-ORG029", "SRC0101"),
            ("SRC0006", "CON-S119-PUB-ORG001", "SRC0228"),
        ):
            with self.subTest(source=sid):
                self.assertEqual(self.contributions[cid]["sourceIds"], [remaining])
                self.assertNotIn(cid, self.sources[sid]["contributionIds"])
                removals = self.overrides["linkRemovals"]
                self.assertIn(cid, removals["Sources"][sid]["fields"]["contributionIds"])
                self.assertIn(sid, removals["Contributions"][cid]["fields"]["sourceIds"])

    def test_review_survives_normalization_and_has_auditable_fields(self):
        for sid in REVIEWED:
            with self.subTest(source=sid):
                source = self.sources[sid]
                self.assertEqual(normalized_source(source), source)
                stale = dict(source, date="1930", dateRole="recording", researchNote="Old note",
                             fullCitation="Old citation")
                self.assertEqual(normalized_source(stale), source)
                fields = self.overrides["records"]["Sources"][sid]["fields"]
                self.assertEqual(fields["researchNote"], source["researchNote"])
        self.assertIn("date", self.overrides["records"]["Sources"]["SRC0748"]["removeFields"])
