from __future__ import annotations

import html
import re
import unittest
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "assets/site/styles.css"
MAX_SOCIAL_BYTES = 600_000
ORIGIN = "https://iwmarlin.github.io/kaper/"


class RecordPrintTests(unittest.TestCase):
    def test_print_view_preserves_complete_record_content(self) -> None:
        css = CSS.read_text(encoding="utf-8")
        self.assertIn("@media print", css)
        self.assertRegex(
            css,
            r"\.progressive-list__panel\[hidden\][\s\S]*?display:\s*block\s*!important",
        )
        self.assertRegex(
            css,
            r"\[data-row-detail\]\[hidden\][\s\S]*?display:\s*block\s*!important",
        )
        self.assertIn(".site-header,", css)
        self.assertIn(".site-footer,", css)
        self.assertIn(".record-contents,", css)
        self.assertIn("break-inside: avoid-page", css)


class LanguageMarkupTests(unittest.TestCase):
    def assert_lang(self, relative: str, language: str, text: str) -> None:
        page = (ROOT / relative).read_text(encoding="utf-8")
        wanted = f'lang="{language}">{html.escape(text)}</span>'
        self.assertIn(wanted, page, f"{relative} does not mark {text!r} as {language}")

    def test_explicit_title_variant_languages_reach_static_html(self) -> None:
        self.assert_lang("records/work/W-F009/index.html", "de", "Führerschein ins Glück")
        self.assert_lang("records/work/W-F030/index.html", "fr", "Le Valet de coeur")
        self.assert_lang("records/work/W-S076/index.html", "pl", "Ninon, ach uśmiechnij się!")

    def test_mixed_language_citation_marks_only_known_title_spans(self) -> None:
        page = (ROOT / "records/source/SRC0633/index.html").read_text(encoding="utf-8")
        self.assertIn('lang="pl">Ninon, ach uśmiechnij się!</span>', page)
        self.assertNotRegex(page, r'<div class="source-hero__citation">[\s\S]*?<p lang="pl">')


class RecordPayloadLanguageEvidenceTests(unittest.TestCase):
    def test_source_payload_carries_its_explicit_title_languages(self) -> None:
        import json

        payload = json.loads(
            (ROOT / "data/site/records/source/SRC0633.json").read_text(encoding="utf-8")
        )
        carried = {
            item["id"]
            for item in payload["tables"]["titleVariants"]
        }
        self.assertTrue(
            {"TV0306", "TV0307", "TV0308"} <= carried,
            "SRC0633 must carry the title variants that identify its Polish title strings",
        )


class SocialImageTests(unittest.TestCase):
    def test_record_social_images_use_small_generated_derivatives(self) -> None:
        pages = list((ROOT / "records").glob("*/*/index.html"))
        self.assertGreater(len(pages), 1000)
        offenders = []
        for page in pages:
            text = page.read_text(encoding="utf-8")
            match = re.search(r'<meta property="og:image" content="([^"]+)">', text)
            if not match:
                offenders.append(f"{page.relative_to(ROOT)}: missing og:image")
                continue
            url = html.unescape(match.group(1))
            if not url.startswith(ORIGIN):
                offenders.append(f"{page.relative_to(ROOT)}: non-local {url}")
                continue
            relative = unquote(url.removeprefix(ORIGIN))
            image = ROOT / relative
            if not image.is_file():
                offenders.append(f"{page.relative_to(ROOT)}: missing {relative}")
                continue
            if relative != "apple-touch-icon.png":
                if not relative.startswith("assets/generated/responsive/"):
                    offenders.append(f"{page.relative_to(ROOT)}: original asset used for social image")
                if image.stat().st_size > MAX_SOCIAL_BYTES:
                    offenders.append(f"{page.relative_to(ROOT)}: {image.stat().st_size} bytes")
            for property_name in ("og:image:type", "og:image:width", "og:image:height"):
                if f'property="{property_name}"' not in text:
                    offenders.append(f"{page.relative_to(ROOT)}: missing {property_name}")
        self.assertEqual(offenders[:20], [], f"{len(offenders)} social-image problems")

    def test_johnny_green_no_longer_exposes_the_15_mb_source_as_og_image(self) -> None:
        source = "assets/images/portraits/johnny-green.jpg"
        offenders = []
        for page in (ROOT / "records").glob("*/*/index.html"):
            text = page.read_text(encoding="utf-8")
            match = re.search(r'<meta property="og:image" content="([^"]+)">', text)
            if match and source in match.group(1):
                offenders.append(page.relative_to(ROOT).as_posix())
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
