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


if __name__ == "__main__":
    unittest.main()
