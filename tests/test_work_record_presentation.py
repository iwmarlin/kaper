from __future__ import annotations

import glob
import html
import json
import re
import unicodedata
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/public/v1"


def records(filename: str) -> list[dict]:
    return json.loads((DATA / filename).read_text(encoding="utf-8"))["records"]


def normalise(value: str) -> str:
    folded = unicodedata.normalize("NFD", value or "")
    folded = "".join(ch for ch in folded if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", folded.lower()).strip()


class WorkRecordPresentationTests(unittest.TestCase):
    """What a work page states, it states once."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pages = {
            Path(path).parent.name: Path(path).read_text(encoding="utf-8")
            for path in glob.glob(str(ROOT / "records/work/*/index.html"))
        }
        cls.works = {record["id"]: record for record in records("works.json")}
        cls.variants = {record["id"]: record for record in records("title-variants.json")}
        cls.relations = {record["id"]: record for record in records("work-relations.json")}

    def test_pages_were_generated(self) -> None:
        self.assertGreater(len(self.pages), 250)

    def test_the_type_is_not_repeated_beside_the_title(self) -> None:
        """The kicker above the title names the type; a badge would say it twice."""
        offenders = []
        for work_id, text in self.pages.items():
            work = self.works.get(work_id.upper()) or self.works.get(work_id)
            if not work or not work.get("workType"):
                continue
            hero = re.search(r'<p class="record-hero__label">.*?<h1.*?</h1>(.*?)</header>', text, re.S)
            if not hero:
                continue
            if f'>{html.escape(work["workType"])}<' in hero.group(1):
                offenders.append(work_id)
        self.assertEqual(offenders[:5], [])

    def test_absence_of_media_is_not_announced(self) -> None:
        announced = [work_id for work_id, text in self.pages.items()
                     if "No public media are linked to this work" in text]
        self.assertEqual(announced, [])

    def test_a_variant_naming_a_related_work_is_printed_once(self) -> None:
        """The French release is a record of its own; its title is not also a
        line in a list of names."""
        offenders = []
        for work_id, work in self.works.items():
            page = self.pages.get(work_id.lower()) or self.pages.get(work_id)
            if not page:
                continue
            related_titles = set()
            for relation_id in work.get("relationIds") or []:
                relation = self.relations.get(relation_id) or {}
                for other_id in (relation.get("targetWorkIds") or []) + (relation.get("sourceWorkIds") or []):
                    if other_id != work_id and other_id in self.works:
                        related_titles.add(normalise(self.works[other_id]["title"]))
            section = re.search(
                r"<h2>Title variants.*?</section>", page, re.S
            )
            if not section:
                continue
            for variant_id in work.get("titleVariantIds") or []:
                variant = self.variants.get(variant_id) or {}
                title = variant.get("variantTitle") or ""
                if normalise(title) in related_titles and html.escape(title) in section.group(0):
                    offenders.append((work_id, title))
        self.assertEqual(offenders[:5], [])


if __name__ == "__main__":
    unittest.main()
