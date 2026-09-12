import html
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
sys.path.insert(0, str(ROOT / "scripts"))

from person_life_dates import life_date_evidence_errors


class PersonLifeDateTests(unittest.TestCase):
    def test_disputed_dates_cannot_be_published_without_an_explanation(self):
        person = {"lifeDatesCertainty": "disputed", "sourceIds": ["S1"]}
        self.assertTrue(life_date_evidence_errors(person))
        person["lifeDatesNote"] = "Two authority records disagree on the birth year."
        self.assertTrue(life_date_evidence_errors(person))
        person["lifeDatesSourceIds"] = ["S1"]
        self.assertEqual(life_date_evidence_errors(person), [])

    def test_evidence_must_be_a_valid_subset_of_person_sources(self):
        person = {
            "lifeDatesNote": "The authority records disagree.",
            "sourceIds": ["S1"],
        }
        for invalid in ("S1", None, [None], ["S2"], ["S1", "S1"]):
            with self.subTest(invalid=invalid):
                self.assertTrue(life_date_evidence_errors({
                    **person, "lifeDatesSourceIds": invalid,
                }))
        self.assertTrue(life_date_evidence_errors({
            "lifeDatesSourceIds": ["S1"], "sourceIds": ["S1"],
        }))
        self.assertEqual(life_date_evidence_errors({"lifeDatesCertainty": "confirmed"}), [])

    def test_reviewed_dates_and_unresolved_conflicts_are_preserved(self):
        people = {p["id"]: p for p in json.loads((PUBLIC / "people.json").read_text())["records"]}
        expected = {
            "P003": (1895, 1943, "disputed"),
            "P065": (1878, 1942, "disputed"),
            "P090": (1900, 1996, "disputed"),
            "P110": (1904, 1981, "confirmed"),
            "P139": (1903, 1965, "disputed"),
            "P162": (1902, 1988, "disputed"),
        }
        for person_id, dates in expected.items():
            person = people[person_id]
            self.assertEqual(tuple(person[k] for k in (
                "birthYear", "deathYear", "lifeDatesCertainty",
            )), dates)
            self.assertTrue(person.get("lifeDatesNote"), person_id)
        for person in people.values():
            self.assertEqual(life_date_evidence_errors(person), [], person["id"])

    def test_review_survives_export_and_all_evidence_links_are_bidirectional(self):
        people = json.loads((PUBLIC / "people.json").read_text())["records"]
        sources = {s["id"]: s for s in json.loads((PUBLIC / "sources.json").read_text())["records"]}
        overrides = json.loads((ROOT / "scripts/public_export_overrides.json").read_text())
        for person in people:
            if not person.get("lifeDatesNote"):
                continue
            person_id = person["id"]
            override = (overrides["records"]["People"].get(person_id)
                        or overrides["additions"]["People"][person_id])["fields"]
            for field in ("lifeDatesNote", "lifeDatesSourceIds"):
                self.assertEqual(person[field], override[field])
            for source_id in person["lifeDatesSourceIds"]:
                self.assertIn(person_id, sources[source_id].get("personIds", []))

    def test_explanation_and_source_links_reach_every_reviewed_static_card(self):
        for person in json.loads((PUBLIC / "people.json").read_text())["records"]:
            if not person.get("lifeDatesNote"):
                continue
            page = (ROOT / "records/person" / person["id"] / "index.html").read_text()
            self.assertIn('id="section-life-dates-and-evidence"', page)
            self.assertIn(html.escape(person["lifeDatesNote"], quote=False), page)
            for source_id in person["lifeDatesSourceIds"]:
                self.assertIn(f'href="records/source/{source_id}/"', page)

    def test_renderer_escapes_the_note_and_omits_empty_sections(self):
        node = shutil.which("node")
        if not node:
            bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
            node = str(bundled) if bundled.is_file() else None
        if not node:
            self.skipTest("Node.js is required for record-renderer tests")
        renderer = (ROOT / "assets/site/record-detail-20260714.js").as_uri()
        script = f"""
          import {{ renderRecordView }} from {json.dumps(renderer)};
          const person = {{ id: 'PTEST', displayName: 'Test', birthYear: 1900,
            deathYear: 1980, lifeDatesCertainty: 'disputed',
            lifeDatesNote: '<script>unsafe & untrusted</script>',
            lifeDatesSourceIds: ['S1'], sourceIds: ['S1'] }};
          const tables = {{ people: [person], sources: [{{ id: 'S1', title: 'Evidence' }}],
            organizations: [], media: [], works: [], films: [], songs: [], otherWorks: [],
            titleVariants: [], workRelations: [], timelineEvents: [], places: [],
            contributions: [], personNameVariants: [] }};
          const withNote = renderRecordView('person', 'PTEST', tables).view.main;
          delete person.lifeDatesNote;
          delete person.lifeDatesSourceIds;
          const withoutNote = renderRecordView('person', 'PTEST', tables).view.main;
          process.stdout.write(JSON.stringify({{ withNote, withoutNote }}));
        """
        output = json.loads(subprocess.run(
            [node, "--input-type=module", "--eval", script], cwd=ROOT,
            check=True, capture_output=True, text=True,
        ).stdout)
        self.assertIn("&lt;script&gt;unsafe &amp; untrusted&lt;/script&gt;", output["withNote"])
        self.assertNotIn("<script>", output["withNote"])
        self.assertNotIn("Life dates and evidence", output["withoutNote"])


if __name__ == "__main__":
    unittest.main()
