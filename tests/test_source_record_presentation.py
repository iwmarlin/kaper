import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
RECORDS = ROOT / "records/source"


def read_records(name):
    return json.loads((PUBLIC / name).read_text(encoding="utf-8"))["records"]


def node_binary():
    node = shutil.which("node")
    if node:
        return node
    bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
    return str(bundled) if bundled.is_file() else None


class SourceAssessmentTests(unittest.TestCase):
    """The archive grades every source it cites. Those grades were recorded and
    never shown, so a YouTube upload and an archival negative were presented on
    identical rows."""

    def test_every_source_card_states_its_assessment(self):
        missing = []
        for source in read_records("sources.json"):
            page = RECORDS / source["id"] / "index.html"
            if not page.is_file():
                continue
            text = page.read_text(encoding="utf-8")
            if "<dt>Reliability</dt>" not in text or "<dt>Verification</dt>" not in text:
                missing.append(source["id"])
        self.assertEqual(missing[:10], [], f"{len(missing)} source cards omit the assessment")

    def test_the_reliability_flag_marks_the_exception_and_only_the_exception(self):
        # A mark carried by three quarters of the rows tells a reader nothing.
        # Only sources the archive declines to treat as independent authority
        # are flagged, so the flag keeps its meaning.
        flagged = set()
        expected = set()
        for source in read_records("sources.json"):
            page = RECORDS / source["id"] / "index.html"
            if not page.is_file():
                continue
            if source.get("reliability") == "low":
                expected.add(source["id"])
            if "badge--reliability-low" in page.read_text(encoding="utf-8"):
                flagged.add(source["id"])
        self.assertTrue(expected, "the fixture must contain low-reliability sources")
        self.assertEqual(flagged, expected)


class SourceApparatusTests(unittest.TestCase):
    """A persistent identifier buried in an href, and an access date recorded but
    never printed, are apparatus the archive holds and the reader cannot use."""

    def test_every_structured_access_date_is_shown(self):
        shown = set()
        expected = set()
        for source in read_records("sources.json"):
            page = RECORDS / source["id"] / "index.html"
            if not page.is_file():
                continue
            if source.get("accessDate"):
                expected.add(source["id"])
            if "<dt>Accessed</dt>" in page.read_text(encoding="utf-8"):
                shown.add(source["id"])
        self.assertTrue(expected, "the fixture must contain online sources")
        self.assertEqual(shown, expected)

    def test_identifiers_are_printed_as_text_and_not_as_a_second_link(self):
        labels = {
            "ark": "ARK",
            "doi": "DOI",
            "naid": "NAID",
            "usco_registration": "U.S. copyright registration",
            "usco_renewal": "U.S. copyright renewal",
        }
        checked = 0
        for source in read_records("sources.json"):
            identifiers = source.get("identifiers") or []
            if not identifiers:
                continue
            page = RECORDS / source["id"] / "index.html"
            if not page.is_file():
                continue
            text = page.read_text(encoding="utf-8")
            for item in identifiers:
                label = labels.get(item.get("scheme"))
                self.assertIsNotNone(label, f"unlabelled identifier scheme: {item.get('scheme')}")
                self.assertIn(f"<dt>{label}</dt><dd>{item['value']}</dd>", text)
                self.assertNotIn(f'href="{item["value"]}"', text)
                checked += 1
        # The count is taken from the data, not fixed here: the archive gains
        # sources, and a hard number turns a growing fixture into a failure.
        registered = sum(len(record.get("identifiers") or []) for record in read_records("sources.json"))
        self.assertEqual(checked, registered, "every registered identifier must be on its card")
        self.assertGreater(registered, 50, "the fixture must exercise identifiers")

    def test_source_header_leads_with_the_citation_and_collapses_metadata(self):
        pages = sorted(RECORDS.glob("*/index.html"))
        self.assertTrue(pages, "the fixture must contain static source pages")
        text = pages[0].read_text(encoding="utf-8")
        self.assertIn('class="record-hero', text)
        self.assertIn("record-hero--source", text)
        self.assertIn('class="source-hero__citation"', text)
        self.assertIn('class="record-facts-disclosure"', text)
        self.assertEqual(text.count("<h2>Citation</h2>"), 1)
        self.assertLess(text.index('class="source-hero__citation"'), text.index('class="record-facts-disclosure"'))


class SourceCreditLedgerTests(unittest.TestCase):
    """A source card used to name only the people linked to the source itself.
    The credits it underwrites live on the contributions, and those named people
    the card never mentioned."""

    def test_a_credited_person_appears_even_without_a_direct_person_link(self):
        node = node_binary()
        if not node:
            self.skipTest("Node.js is required to exercise the public record renderer")
        renderer = (ROOT / "assets/site/record-detail-20260714.js").as_uri()
        script = f"""
          import {{ renderRecordView }} from {json.dumps(renderer)};
          const tables = {{
            people: [
              {{ id: "PDIRECT", displayName: "Aaa Direct", primaryRole: "publisher" }},
              {{ id: "PCREDIT", displayName: "Bbb Credited", primaryRole: "composer" }}
            ],
            organizations: [],
            sources: [{{
              id: "STEST", title: "Test source", shortCitation: "Test source",
              fullCitation: "Test source, 1930.", sourceType: "press_item",
              reliability: "medium", sourceStatus: "verified",
              personIds: ["PDIRECT"], contributionIds: ["CCONF", "CTEST", "CORG"]
            }}],
            media: [],
            works: [
              {{ id: "WCONF", title: "Confirmed Work", year: 1929, workType: "song" }},
              {{ id: "WPROB", title: "Probable Work", year: 1930, workType: "song" }}
            ],
            films: [], songs: [], otherWorks: [], titleVariants: [], workRelations: [],
            timelineEvents: [], places: [], personNameVariants: [],
            contributions: [
              {{ id: "CCONF", role: "lyricist", workIds: ["WCONF"], personIds: ["PCREDIT"],
                 sourceIds: ["STEST"], certainty: "confirmed" }},
              {{ id: "CTEST", role: "lyricist", workIds: ["WPROB"], personIds: ["PCREDIT"],
                 sourceIds: ["STEST"], certainty: "probable" }},
              {{ id: "CORG", role: "publisher", workIds: ["WCONF"], personIds: [],
                 sourceIds: ["STEST"], certainty: "confirmed" }}
            ]
          }};
          const {{ view }} = renderRecordView("source", "STEST", tables);
          process.stdout.write(view.main);
        """
        result = subprocess.run(
            [node, "--input-type=module", "--eval", script],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        markup = result.stdout
        self.assertIn("People and credits", markup)
        # The person the source credits is named, once, with the credit beneath.
        self.assertEqual(markup.count('href="records/person/PCREDIT/"'), 1)
        self.assertIn("Lyricist", markup)
        subject_start = markup.index('href="records/person/PCREDIT/"')
        probable_work_start = markup.index('href="records/work/WPROB/"', subject_start)
        self.assertNotIn("badge--probable", markup[subject_start:probable_work_start])
        probable_work_end = markup.index("</li>", probable_work_start)
        self.assertIn("badge--probable", markup[probable_work_start:probable_work_end])
        self.assertIn("Lyricist", markup[probable_work_start:probable_work_end])
        # A person merely linked to the source keeps their own role.
        self.assertEqual(markup.count('href="records/person/PDIRECT/"'), 1)
        self.assertIn("Publisher", markup)
        # People and credits are one list, not two.
        self.assertNotIn("<h2>People<", markup)

    def test_source_payloads_carry_the_contribution_evidence(self):
        contributions = {item["id"]: item for item in read_records("contributions.json")}
        checked = 0
        for source in read_records("sources.json"):
            linked = [cid for cid in source.get("contributionIds") or [] if cid in contributions]
            if not linked:
                continue
            payload_path = ROOT / "data/site/records/source" / f"{source['id']}.json"
            if not payload_path.is_file():
                continue
            tables = json.loads(payload_path.read_text(encoding="utf-8"))["tables"]
            carried = {item["id"] for item in tables["contributions"]}
            self.assertTrue(
                set(linked) <= carried,
                f"source payload omits contribution evidence: {source['id']}",
            )
            people = {item["id"] for item in tables["people"]}
            for cid in linked:
                for person_id in contributions[cid].get("personIds") or []:
                    self.assertIn(
                        person_id,
                        people,
                        f"source payload omits a credited person: {source['id']} -> {person_id}",
                    )
            checked += 1
        self.assertGreater(checked, 100, "the fixture must exercise many sources")

    def test_mixed_certainty_is_attached_to_the_specific_credit(self):
        contributions = {
            item["id"]: item for item in read_records("contributions.json")
        }
        mixed_groups = 0
        for source in read_records("sources.json"):
            by_person = {}
            for contribution_id in source.get("contributionIds") or []:
                contribution = contributions.get(contribution_id)
                if not contribution:
                    continue
                for person_id in contribution.get("personIds") or []:
                    by_person.setdefault(person_id, []).append(contribution)
            for person_id, credits in by_person.items():
                certainties = {
                    credit.get("certainty") or "confirmed" for credit in credits
                }
                if "confirmed" not in certainties or certainties == {"confirmed"}:
                    continue
                mixed_groups += 1
                page = RECORDS / source["id"] / "index.html"
                text = page.read_text(encoding="utf-8")
                person_link = f'href="records/person/{person_id}/"'
                person_position = text.index(person_link)
                subject_start = text.rfind(
                    '<div class="credit-evidence__subject">', 0, person_position
                )
                subject_end = text.index("</div>", person_position)
                self.assertNotIn(
                    "badge--certainty",
                    text[subject_start:subject_end],
                    f"{source['id']} applies credit certainty to all of {person_id}",
                )
                works_start = text.index(
                    '<ul class="credit-evidence__works"', subject_end
                )
                works_end = text.index("</ul>", works_start)
                works_markup = text[works_start:works_end]
                for credit in credits:
                    certainty = credit.get("certainty") or "confirmed"
                    if certainty == "confirmed":
                        continue
                    for work_id in credit.get("workIds") or []:
                        work_link = f'href="records/work/{work_id}/"'
                        work_position = works_markup.index(work_link)
                        work_end = works_markup.index("</li>", work_position)
                        work_markup = works_markup[work_position:work_end]
                        self.assertIn(
                            f"badge--{certainty.replace(' ', '_')}",
                            work_markup,
                            f"{source['id']} omits {certainty} on {work_id}",
                        )
                        role = str(credit.get("role") or "credit").replace(
                            "_", " "
                        ).title()
                        self.assertIn(role, work_markup)
        self.assertGreater(mixed_groups, 0, "the fixture must exercise mixed certainty")


if __name__ == "__main__":
    unittest.main()
