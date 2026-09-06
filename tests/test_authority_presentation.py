import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"


def read_records(name):
    return json.loads((PUBLIC / name).read_text(encoding="utf-8"))["records"]


class AuthorityHeadingTests(unittest.TestCase):
    """A heading with no stated register is not an authorized name, and an
    authority record no reader can reach is not authority control."""

    def test_the_authority_stack_reaches_the_page(self):
        for table, folder in (("organizations.json", "organization"), ("people.json", "person")):
            for record in read_records(table):
                page = ROOT / "records" / folder / record["id"] / "index.html"
                if not page.is_file():
                    continue
                text = page.read_text(encoding="utf-8")
                for line in str(record.get("authorityUrl") or "").splitlines():
                    _, _, url = line.strip().partition(": ")
                    if url.startswith("http"):
                        self.assertIn(
                            f'href="{url}"',
                            text,
                            f"{record['id']} holds an authority record the card does not reach",
                        )

    def test_a_name_is_called_authorized_only_where_it_differs_from_the_heading(self):
        for record in read_records("organizations.json"):
            page = ROOT / "records/organization" / record["id"] / "index.html"
            if not page.is_file():
                continue
            differs = (record.get("authorizedName") or "").strip() != (record.get("displayName") or "").strip()
            self.assertEqual(
                "<dt>Authorized name</dt>" in page.read_text(encoding="utf-8"),
                differs,
                f"{record['id']} states an authorized name that only repeats its own title",
            )

    def test_the_type_is_set_once(self):
        # The badge carries it; the fact row that repeated it is gone, as it
        # went from the work card.
        for record in read_records("organizations.json"):
            page = ROOT / "records/organization" / record["id"] / "index.html"
            if page.is_file():
                self.assertNotIn("<dt>Type</dt>", page.read_text(encoding="utf-8"))

    def test_the_vocabularies_have_one_written_form(self):
        types = {item for record in read_records("organizations.json") for item in record.get("types") or []}
        self.assertEqual(
            sorted(item for item in types if item != item.strip().lower().replace(" ", "_")),
            [],
            "organization types must be recorded in one form",
        )
        headings = {
            record.get("authorizedNameSource")
            for table in ("people.json", "organizations.json")
            for record in read_records(table)
            if record.get("authorizedNameSource")
        }
        self.assertNotIn("local", headings, "'local' and 'local heading' name the same thing")


class OrganizationScopeTests(unittest.TestCase):
    """Two kinds of body share the organization table. A card that carries no
    works because a library composes nothing should say so, instead of reading
    as a subject record with its content missing."""

    REPOSITORY_TYPES = {"archive", "database", "library", "digital_library", "museum"}
    NOTE = "A repository consulted by the archive"

    def test_repositories_say_what_they_are_and_subjects_do_not(self):
        for record in read_records("organizations.json"):
            page = ROOT / "records/organization" / record["id"] / "index.html"
            if not page.is_file():
                continue
            is_repository = bool(set(record.get("types") or []) & self.REPOSITORY_TYPES)
            self.assertEqual(
                self.NOTE in page.read_text(encoding="utf-8"),
                is_repository,
                f"{record['id']} is described as the wrong kind of organization",
            )

    def test_the_distinction_is_taken_from_the_type_and_not_from_missing_links(self):
        # The American Heritage Center holds Kaper's manuscripts, so custody
        # gives it work links. It is still a repository, and a rule that read
        # the absence of links would call it a subject.
        record = next(
            item for item in read_records("organizations.json") if item["id"] == "ORG056"
        )
        self.assertTrue(record.get("workIds"), "ORG056 must still carry its custodial links")
        page = ROOT / "records/organization/ORG056/index.html"
        self.assertIn(self.NOTE, page.read_text(encoding="utf-8"))


class ImprintRelationTests(unittest.TestCase):
    """Odeon is kept apart from the Greek company of the same name, Grammophon
    and Polydor are imprints of one Berlin firm, Victor was pressed by RCA.
    Every one of those relations was written into a note and none was in the
    graph, so the companies carried no links at all and read as records nobody
    had finished."""

    def test_the_relation_is_stated_at_both_ends(self):
        records = {item["id"]: item for item in read_records("organizations.json")}
        pairs = 0
        for record in records.values():
            for parent_id in record.get("parentOrganizationIds") or []:
                pairs += 1
                self.assertIn(parent_id, records, f"{record['id']} names a company that is not a record")
                self.assertIn(
                    record["id"],
                    records[parent_id].get("imprintIds") or [],
                    f"{parent_id} does not name {record['id']} back",
                )
            for imprint_id in record.get("imprintIds") or []:
                self.assertIn(
                    record["id"],
                    records[imprint_id].get("parentOrganizationIds") or [],
                    f"{imprint_id} does not name {record['id']} back",
                )
        self.assertGreaterEqual(pairs, 5, "the documented imprint relations must be recorded")

    def test_both_ends_are_reachable_from_the_card(self):
        for record in read_records("organizations.json"):
            page = ROOT / "records/organization" / record["id"] / "index.html"
            if not page.is_file():
                continue
            text = page.read_text(encoding="utf-8")
            for parent_id in record.get("parentOrganizationIds") or []:
                self.assertIn("<dt>Imprint of</dt>", text, f"{record['id']} hides its company")
                self.assertIn(f'href="records/organization/{parent_id}/"', text)
            if record.get("imprintIds"):
                self.assertIn("<h2>Imprints", text, f"{record['id']} hides its labels")

    def test_no_organization_is_left_without_a_single_link(self):
        # This is the check that produced the false alarm: two companies held no
        # links of any kind, and were read as records nobody had finished, when
        # what they lacked was a relation the schema could not express.
        stranded = []
        for record in read_records("organizations.json"):
            linked = any(
                record.get(field)
                for field in (
                    "sourceIds", "workIds", "contributionIds", "timelineEventIds",
                    "placeIds", "parentOrganizationIds", "imprintIds",
                )
            )
            if not linked:
                stranded.append(record["id"])
        self.assertEqual(stranded, [], "an organization sits outside the graph entirely")


if __name__ == "__main__":
    unittest.main()
