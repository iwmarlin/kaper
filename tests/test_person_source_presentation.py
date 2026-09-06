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
              sourceIds: ["SEVIDENCE", "SDIRECT"]
            }}],
            organizations: [],
            sources: [
              {{ id: "SEVIDENCE", shortCitation: "Credit evidence", date: "1930" }},
              {{ id: "SDIRECT", shortCitation: "Biographical source", date: "1950" }}
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


if __name__ == "__main__":
    unittest.main()
