import json
import re
import unicodedata
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
# A related work is this work under another title only when the relation says
# so. A song and the film it belongs to are two different works whose titles
# may coincide.
MERGEABLE = {"language_version_of", "remake_of"}


def read(name):
    return json.loads((PUBLIC / name).read_text(encoding="utf-8"))["records"]


def normalize(value):
    text = unicodedata.normalize("NFD", str(value or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text.replace("'", "")).strip()


class RelationLanguageTests(unittest.TestCase):
    """A title variant was merged into a relation row whenever its text matched
    the related work's title. On a language version that is right — the variant
    and the related record describe one thing. On a song and its film it is not:
    the film's alternative German release title was printed on the row of a song
    of nearly the same name, and a song's Polish title on the row of the film."""

    def test_a_language_is_only_claimed_where_the_relation_is_one(self):
        works = {item["id"]: item for item in read("works.json")}
        relations = {item["id"]: item for item in read("work-relations.json")}
        variants = {item["id"]: item for item in read("title-variants.json")}
        wrong = []
        for work in works.values():
            by_title = {
                normalize(variants[v]["variantTitle"]): variants[v]
                for v in work.get("titleVariantIds") or []
                if v in variants
            }
            if not by_title:
                continue
            page = ROOT / "records/work" / work["id"] / "index.html"
            if not page.is_file():
                continue
            section = re.search(
                r'id="section-related-works-and-versions".*?</section>',
                page.read_text(encoding="utf-8"),
                re.S,
            )
            if not section:
                continue
            marks = len(re.findall(r"badge--language", section.group(0)))
            expected = 0
            for relation_id in work.get("relationIds") or []:
                relation = relations.get(relation_id)
                if not relation or relation["relationType"] not in MERGEABLE:
                    continue
                others = [
                    other
                    for other in (relation.get("sourceWorkIds") or []) + (relation.get("targetWorkIds") or [])
                    if other != work["id"]
                ]
                for other in others:
                    target = works.get(other)
                    variant = by_title.get(normalize(target["title"])) if target else None
                    if variant and variant.get("language"):
                        expected += 1
            if marks != expected:
                wrong.append(f"{work['id']}: {marks} language marks, {expected} relations that carry one")
        self.assertEqual(wrong, [], "a language is claimed on a relation that is not a version of this work")

    def test_the_language_is_named_and_not_abbreviated(self):
        core = (ROOT / "assets/site/core.js").read_text(encoding="utf-8")
        self.assertIn("export function languageBadge", core)
        self.assertNotIn("periodBadge(variant.language)", (ROOT / "assets/site/record-detail-20260714.js").read_text(encoding="utf-8"))
        for page in list((ROOT / "records/work").glob("*/index.html"))[:400]:
            for label in re.findall(r'badge--language[^>]*>([^<]+)<', page.read_text(encoding="utf-8")):
                self.assertGreater(len(label), 3, f"{page.parent.name}: language shown as {label!r}")


class TitleVariantVisibilityTests(unittest.TestCase):
    """A variant is taken out of the list of names only because it is shown on a
    relation row instead. When the merge was narrowed to versions and remakes
    and this filter was not, the alternative German release title of Der
    Korvettenkapitän fell out of both places at once and appeared nowhere."""

    def test_every_variant_is_shown_somewhere_on_its_work(self):
        works = {item["id"]: item for item in read("works.json")}
        variants = {item["id"]: item for item in read("title-variants.json")}
        invisible = []
        for work in works.values():
            page = ROOT / "records/work" / work["id"] / "index.html"
            if not page.is_file():
                continue
            text = page.read_text(encoding="utf-8")
            shown = ""
            for pattern in (
                r'id="section-title-variants".*?</section>',
                r'id="section-related-works-and-versions".*?</section>',
            ):
                found = re.search(pattern, text, re.S)
                if found:
                    shown += found.group(0)
            for variant_id in work.get("titleVariantIds") or []:
                variant = variants.get(variant_id)
                if not variant:
                    continue
                # The merge shows the related work's own spelling, which can
                # differ from the variant's in capitalisation alone — "L'homme"
                # against "L'Homme". They are the same name, so the comparison
                # is made on the normalised form.
                wanted = normalize(variant["variantTitle"])
                if wanted and wanted not in normalize(re.sub(r"<[^>]+>", " ", shown)):
                    invisible.append(f"{work['id']}/{variant_id}: {variant['variantTitle']!r}")
        self.assertEqual(invisible, [], "a recorded title variant is shown on no part of its work's card")


class OrganizationCreditEvidenceTests(unittest.TestCase):
    """The works section named what an organization stood behind and stopped
    there, while the evidence for each link sat on the contribution. Aafa-Film
    AG showed two films and one source, when the production credit for Der
    Korvettenkapitän alone rests on two more."""

    def test_the_citations_behind_each_credit_are_on_the_card(self):
        organizations = read("organizations.json")
        contributions = {item["id"]: item for item in read("contributions.json")}
        checked = 0
        for organization in organizations:
            page = ROOT / "records/organization" / organization["id"] / "index.html"
            if not page.is_file():
                continue
            text = page.read_text(encoding="utf-8")
            for contribution_id in organization.get("contributionIds") or []:
                contribution = contributions.get(contribution_id)
                if not contribution:
                    continue
                for source_id in contribution.get("sourceIds") or []:
                    self.assertIn(
                        source_id,
                        text,
                        f"{organization['id']} does not show {source_id}, which documents one of its credits",
                    )
                    checked += 1
        self.assertGreater(checked, 50, "the fixture must exercise organization credits")

    def test_aafa_film_shows_all_three_of_its_citations(self):
        text = (ROOT / "records/organization/ORG021/index.html").read_text(encoding="utf-8")
        for source_id in ("SRC0122", "SRC0164", "SRC0479"):
            self.assertIn(source_id, text)


if __name__ == "__main__":
    unittest.main()
