import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PersonSourcePresentationTests(unittest.TestCase):
    def test_credit_evidence_is_not_repeated_as_a_direct_person_source(self):
        node = shutil.which("node")
        if not node:
            bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
            node = str(bundled) if bundled.is_file() else None
        if not node:
            self.skipTest("Node.js is required to exercise the public record renderer")

        renderer = (ROOT / "assets/site/record-detail-20260714.js").as_uri()
        script = f"""
          import {{ renderRecordView }} from {json.dumps(renderer)};
          const tables = {{
            people: [{{
              id: "PTEST", displayName: "Test Person", primaryRole: "composer",
              roles: ["composer"], workIds: ["WTEST"], contributionIds: ["CTEST"],
              sourceIds: ["SEVIDENCE", "SDIRECT", "SAUTH", "SDATE"],
              lifeDatesSourceIds: ["SDATE"],
              lifeDatesNote: "The two authority records disagree on the birth year.",
              birthYear: 1900, deathYear: 1970, lifeDatesCertainty: "disputed"
            }}],
            organizations: [],
            sources: [
              {{ id: "SEVIDENCE", shortCitation: "Credit evidence", date: "1930" }},
              {{ id: "SDIRECT", shortCitation: "Biographical source", date: "1950" }},
              {{
                id: "SAUTH", shortCitation: "Authority evidence",
                sourceType: "authority_record", authoritySubject: "person",
                identityRelation: "candidate"
              }},
              {{ id: "SDATE", shortCitation: "Date evidence", sourceType: "authority_record" }}
            ],
            media: [],
            works: [{{ id: "WTEST", title: "Test Work", year: 1930, workType: "Song" }}],
            films: [], songs: [], otherWorks: [], titleVariants: [], workRelations: [],
            timelineEvents: [], places: [], personNameVariants: [],
            contributions: [{{
              id: "CTEST", role: "composer", workIds: ["WTEST"],
              personIds: ["PTEST"], sourceIds: ["SEVIDENCE"], certainty: "confirmed"
            }}]
          }};
          const {{ view }} = renderRecordView("person", "PTEST", tables);
          process.stdout.write(view.main);
        """
        result = subprocess.run(
            [node, "--input-type=module", "--eval", script],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.stdout.count('href="records/source/SEVIDENCE/"'), 1)
        self.assertNotIn('id="source-SEVIDENCE"', result.stdout)
        # The work is stated once, with its evidence beneath it. Two sections
        # naming the same works — one bare, one with citations — made the
        # reader check whether the second list said anything new; on 161 of the
        # 163 people who carried both, it did not.
        self.assertEqual(result.stdout.count('href="records/work/WTEST/"'), 1)
        self.assertIn("Documented works and their evidence", result.stdout)
        self.assertNotIn("Evidence for documented credits", result.stdout)
        self.assertIn("Sources linked directly to this person", result.stdout)
        self.assertIn("SDIRECT", result.stdout)
        self.assertIn("Authority and identity evidence", result.stdout)
        self.assertEqual(result.stdout.count('href="records/source/SAUTH/"'), 1)
        self.assertEqual(result.stdout.count('href="records/source/SDATE/"'), 1)
        direct_section = result.stdout.split("Sources linked directly to this person", 1)[1]
        self.assertNotIn("SAUTH", direct_section)
        self.assertNotIn("SDATE", direct_section)


if __name__ == "__main__":
    unittest.main()
