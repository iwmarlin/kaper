from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "assets/site/record-detail-20260714.js"


def node_binary() -> str | None:
    node = shutil.which("node")
    if node:
        return node
    bundled = (
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
    )
    return str(bundled) if bundled.is_file() else None


def render_media(media: dict, derivatives: dict | None = None) -> tuple[dict, str]:
    node = node_binary()
    if not node:
        raise unittest.SkipTest("Node.js is required to exercise the public renderer")
    tables = {
        "people": [],
        "organizations": [],
        "sources": [],
        "media": [media],
        "works": [],
        "films": [],
        "songs": [],
        "otherWorks": [],
        "titleVariants": [],
        "workRelations": [],
        "timelineEvents": [],
        "places": [],
        "contributions": [],
        "personNameVariants": [],
    }
    script = f"""
      import {{ renderRecordMarkup, renderRecordView, registerRecordImageDerivatives }} from {json.dumps(RENDERER.as_uri())};
      registerRecordImageDerivatives({json.dumps(derivatives or {})});
      const tables = {json.dumps(tables)};
      const {{ view }} = renderRecordView("media", {json.dumps(media["id"])}, tables);
      process.stdout.write(JSON.stringify({{ view, markup: renderRecordMarkup(view, {json.dumps(media["id"])}, "media") }}));
    """
    result = subprocess.run(
        [node, "--input-type=module", "--eval", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    return payload["view"], payload["markup"]


def is_local_visual(media: dict) -> bool:
    return bool(
        media.get("assetPath")
        and media.get("storageType") != "external"
        and media.get("mediaType") in {"image", "sheet music"}
    )


def read_image_derivatives() -> dict:
    source = (ROOT / "assets/site/image-derivatives.js").read_text(encoding="utf-8")
    start = source.index("Object.freeze(") + len("Object.freeze(")
    return json.loads(source[start : source.rindex(")")])


class MediaRecordPresentationTests(unittest.TestCase):
    def test_every_canonical_media_card_uses_the_model_for_its_kind(self) -> None:
        records = json.loads(
            (ROOT / "data/public/v1/media.json").read_text(encoding="utf-8")
        )["records"]
        local_visual_count = 0
        for media in records:
            page = ROOT / "records/media" / media["id"] / "index.html"
            markup = page.read_text(encoding="utf-8")
            is_local_visual = bool(
                media.get("assetPath")
                and media.get("storageType") != "external"
                and media.get("mediaType") in {"image", "sheet music"}
            )
            with self.subTest(media_id=media["id"]):
                self.assertEqual(
                    'class="shell record-leading"' in markup,
                    is_local_visual,
                )
                if is_local_visual:
                    local_visual_count += 1
                    self.assertIn("record-media--primary", markup)
                    if 'class="media-lightbox"' in markup:
                        dialog = markup.split('class="media-lightbox"', 1)[1].split(
                            "</dialog>", 1
                        )[0]
                        self.assertIn("assets/generated/responsive/", dialog)
                        self.assertNotIn(media["assetPath"], dialog)
                else:
                    self.assertNotIn("record-media--primary", markup)
        self.assertGreater(local_visual_count, 250)

    def test_local_image_leads_the_record_and_uses_only_a_derivative_for_zoom(self) -> None:
        media = {
            "id": "MTEST",
            "title": "A documented portrait",
            "mediaType": "image",
            "category": "portrait",
            "storageType": "local",
            "assetPath": "assets/images/private-original.jpg",
            "rightsStatus": "copyright_undetermined",
        }
        derivatives = {
            media["assetPath"]: {
                "default": "assets/generated/640.webp",
                "width": 1600,
                "height": 1200,
                "variants": [
                    {"path": "assets/generated/320.webp", "width": 320, "height": 240},
                    {"path": "assets/generated/960.webp", "width": 960, "height": 720},
                ],
            }
        }
        view, markup = render_media(media, derivatives)
        self.assertIn("record-media--primary", view["leading"])
        self.assertNotIn("record-media--primary", view["aside"])
        self.assertIn('src="assets/generated/960.webp"', view["leading"])
        self.assertNotIn('src="assets/images/private-original.jpg"', view["leading"])
        self.assertLess(markup.index("record-leading"), markup.index("record-layout"))
        self.assertIn("data-media-lightbox-open", markup)
        self.assertIn("data-media-lightbox-close", markup)
        self.assertIn("data-media-view-fit", markup)
        self.assertIn("data-media-view-actual", markup)
        self.assertIn("Open viewer", markup)
        self.assertEqual(view["compactFactsLabel"], "Media details")

    def test_sheet_music_uses_the_same_visual_hierarchy(self) -> None:
        media = {
            "id": "MTEST",
            "title": "A score cover",
            "mediaType": "sheet music",
            "category": "sheet music",
            "storageType": "local",
            "assetPath": "assets/images/score.jpg",
            "rightsStatus": "restricted",
        }
        view, _ = render_media(media)
        self.assertIn("record-media--primary", view["leading"])
        self.assertNotIn("record-media", view["aside"])
        self.assertNotIn("data-media-lightbox-open", view["leading"])

    def test_external_audio_keeps_the_compact_aside_presentation(self) -> None:
        media = {
            "id": "MTEST",
            "title": "Listening reference",
            "mediaType": "audio",
            "category": "audio/video reference",
            "storageType": "external",
            "externalUrl": "https://example.org/listen",
            "rightsStatus": "external_content_not_rehosted",
        }
        view, markup = render_media(media)
        self.assertEqual(view["leading"], "")
        self.assertIn("Listen to recording", view["aside"])
        self.assertNotIn("record-leading", markup)
        self.assertNotIn("data-media-lightbox", markup)

    def test_document_gallery_keeps_its_existing_full_width_model(self) -> None:
        media = {
            "id": "MTEST",
            "title": "Document gallery",
            "mediaType": "document_gallery",
            "category": "document gallery",
            "storageType": "multi_local_assets",
            "assetPaths": ["assets/images/one.jpg", "assets/images/two.jpg"],
            "rightsStatus": "mixed_rights",
        }
        view, markup = render_media(media)
        self.assertTrue(view["fullWidth"])
        self.assertNotIn("leading", view)
        self.assertNotIn("record-leading", markup)
        self.assertIn("record-layout--single", markup)

    def test_lightbox_controls_are_initialized_and_hidden_in_print(self) -> None:
        renderer = RENDERER.read_text(encoding="utf-8")
        styles = (ROOT / "assets/site/styles.css").read_text(encoding="utf-8")
        self.assertIn("function initializeMediaLightboxes()", renderer)
        self.assertIn('dialog.addEventListener("cancel"', renderer)
        self.assertIn("opener?.focus()", renderer)
        self.assertIn('dialog.dataset.mediaView = actual ? "actual" : "fit"', renderer)
        self.assertRegex(
            styles,
            r"\.record-media__expand\s*\{[^}]*display:\s*none;",
        )
        self.assertIn(".js .record-media__expand", styles)
        print_block = styles.split("@media print", 1)[1]
        self.assertIn(".record-media__expand", print_block)
        self.assertIn(".media-lightbox", print_block)


    def test_the_lead_image_is_never_shown_wider_than_its_derivative(self) -> None:
        # Two thirds of the archive's scans are smaller than the space this
        # presentation offers, so the figure publishes the width of the largest
        # derivative and the stylesheet stops there. Without it the lead image
        # is enlarged into blur, and the viewer's 100% shows less than the page.
        derivatives = read_image_derivatives()
        records = json.loads(
            (ROOT / "data/public/v1/media.json").read_text(encoding="utf-8")
        )["records"]
        checked = 0
        for media in records:
            if not is_local_visual(media):
                continue
            profile = derivatives.get(media["assetPath"])
            if not profile or not profile.get("variants"):
                continue
            widest = max(int(item["width"]) for item in profile["variants"])
            markup = (ROOT / "records/media" / media["id"] / "index.html").read_text(
                encoding="utf-8"
            )
            with self.subTest(media_id=media["id"]):
                self.assertIn(f"--media-natural-width: {widest}px", markup)
                slot = f"{widest}px" if widest < 1120 else "70rem"
                self.assertIn(
                    f"sizes=\"(max-width: 1180px) calc(100vw - 2.5rem), {slot}\"",
                    markup,
                )
            checked += 1
        self.assertGreater(checked, 250)

    def test_the_fitted_viewer_is_bounded_by_the_panel_row(self) -> None:
        # A fixed allowance for the header, toolbar and caption leaves the
        # fitted image overflowing once the caption wraps, so "Fit to window"
        # scrolls. The row itself is the bound.
        styles = (ROOT / "assets/site/styles.css").read_text(encoding="utf-8")
        viewport = styles.split(".media-lightbox__image {", 1)[1].split("}", 1)[0]
        self.assertIn("display: flex;", viewport)
        image = styles.split(".media-lightbox__image img {", 1)[1].split("}", 1)[0]
        self.assertIn("max-height: 100%;", image)
        self.assertNotIn("100dvh", image)
        actual = styles.split(
            '.media-lightbox[data-media-view="actual"] .media-lightbox__image {', 1
        )[1].split("}", 1)[0]
        # Plain centring would put the left edge of an oversized image out of
        # reach of the scroll origin.
        self.assertIn("justify-content: safe center;", actual)

if __name__ == "__main__":
    unittest.main()
