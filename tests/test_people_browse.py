from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/public/v1"
CORE = (ROOT / "assets/site/core.js").as_uri()

# The descriptive vocabulary a person record may use. It is deliberately a
# closed list: adding a role should be a decision, not a slip of the keyboard,
# and near-duplicates such as "tenor" beside "singer" made the old facet
# unusable.
APPROVED_ROLES = {
    "actor",
    "animator",
    "arranger",
    "bandleader",
    "comedian",
    "composer",
    "conductor",
    "family member",
    "film director",
    "lyricist",
    "performer",
    "pianist",
    "poet",
    "producer",
    "publisher",
    "satirist",
    "screenwriter",
    "singer",
    "studio executive",
    "studio founder",
    "talent agent",
    "teacher",
    "violinist",
    "writer",
}


def records(filename: str) -> list[dict]:
    return json.loads((DATA / filename).read_text(encoding="utf-8"))["records"]


def run_module(script: str) -> dict:
    node = shutil.which("node")
    if not node:
        raise unittest.SkipTest("Node.js is required to exercise the browse index")
    result = subprocess.run(
        [node, "--input-type=module", "--eval", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


class PersonRoleVocabularyTests(unittest.TestCase):
    def test_roles_come_from_the_approved_vocabulary(self) -> None:
        used = {role for person in records("people.json") for role in person.get("roles", [])}
        self.assertEqual(sorted(used - APPROVED_ROLES), [])

    def test_the_primary_role_is_one_of_the_recorded_roles(self) -> None:
        offenders = [
            person["id"]
            for person in records("people.json")
            if person.get("primaryRole")
            and person.get("roles")
            and person["primaryRole"] not in person["roles"]
        ]
        self.assertEqual(offenders, [])


class PersonFunctionFacetTests(unittest.TestCase):
    """People are filtered by what the sources credit them with here."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = run_module(f"""
          import fs from "node:fs";
          import {{
            indexById, indexText, normalizeSearch, personFunctions, PERSON_FUNCTION_ORDER,
          }} from {json.dumps(CORE)};
          const read = (file) => JSON.parse(fs.readFileSync(`data/public/v1/${{file}}`, "utf8")).records;
          const people = read("people.json");
          const contributionsById = indexById(read("contributions.json"));
          const variantsByPerson = new Map();
          for (const variant of read("person-name-variants.json")) {{
            for (const personId of variant.personIds || []) {{
              variantsByPerson.set(personId, [
                ...(variantsByPerson.get(personId) || []),
                variant.variantName,
                variant.attestedWording,
              ]);
            }}
          }}
          const counts = {{}};
          const unplaced = [];
          for (const person of people) {{
            const families = personFunctions(person, contributionsById);
            if (!families.length) unplaced.push(person.id);
            for (const family of families) counts[family] = (counts[family] || 0) + 1;
          }}
          const index = people.map((person) => ({{
            id: person.id,
            text: indexText([
              person.displayName,
              person.sortName,
              person.authorizedName,
              ...(variantsByPerson.get(person.id) || []).filter(Boolean),
              ...(person.roles || []),
            ].join(" ")),
          }}));
          const hits = (query) => index
            .filter((entry) => entry.text.includes(normalizeSearch(query)))
            .map((entry) => entry.id);
          process.stdout.write(JSON.stringify({{
            counts,
            unplaced,
            order: PERSON_FUNCTION_ORDER,
            performersFamily: people.filter((person) => personFunctions(person, contributionsById).includes("performers")).map((person) => person.id),
            filmFamily: people.filter((person) => personFunctions(person, contributionsById).includes("film")).map((person) => person.id),
            pseudonym: hits("Chwast"),
            printedName: hits("Fred Lustig"),
            recordingName: hits("Leo Moll"),
          }}));
        """)

    def test_every_person_lands_in_a_family(self) -> None:
        self.assertEqual(self.payload["unplaced"], [])

    def test_the_working_families_are_large_enough_to_filter_by(self) -> None:
        counts = self.payload["counts"]
        self.assertEqual(sorted(counts), sorted(self.payload["order"]))
        for family in ("creators", "performers", "film"):
            with self.subTest(family=family):
                self.assertGreater(counts[family], 10)

    def test_people_without_credits_are_filed_by_the_role_they_are_given(self) -> None:
        """A pianist known from one concert notice is still a performer.

        Only someone whose record states no working role at all — Kaper's
        mother, documented as family — falls to the residual family, which
        exists so that no filter hides anybody.
        """
        without_credits = [
            person
            for person in records("people.json")
            if not person.get("contributionIds")
        ]
        self.assertGreater(len(without_credits), 0)
        self.assertEqual(self.payload["counts"]["documented"], 1)
        self.assertIn("P131", self.payload["performersFamily"])
        self.assertIn("P161", self.payload["filmFamily"])

    def test_a_person_is_findable_under_the_names_they_worked_with(self) -> None:
        self.assertIn("P009", self.payload["pseudonym"])
        self.assertEqual(self.payload["printedName"], ["P174"])
        self.assertEqual(self.payload["recordingName"], ["P166"])


if __name__ == "__main__":
    unittest.main()
