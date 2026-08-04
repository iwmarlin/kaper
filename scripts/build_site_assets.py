#!/usr/bin/env python3
"""Build responsive public images and the compact home-page payload.

Archival source files remain untouched. Screen derivatives are normalized to
sRGB, stripped of EXIF metadata and encoded as responsive WebP files.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
from pathlib import Path

from PIL import Image, ImageCms, ImageOps


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
TARGET_WIDTHS = (320, 640, 960, 1440)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def local_image_paths(media_payload: dict, root: Path) -> list[str]:
    paths: set[str] = set()
    for record in media_payload.get("records", []):
        if record.get("storageType") == "external":
            continue
        candidates = [record.get("assetPath"), *record.get("assetPaths", [])]
        for value in candidates:
            if not value:
                continue
            relative = str(value).strip()
            if Path(relative).suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            if (root / relative).is_file():
                paths.add(relative)
    return sorted(paths)


def normalized_image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        source.load()
        image = ImageOps.exif_transpose(source)
        has_alpha = image.mode in {"RGBA", "LA"} or "transparency" in image.info
        if has_alpha:
            return image.convert("RGBA")
        icc_profile = image.info.get("icc_profile")
        if icc_profile:
            try:
                input_profile = ImageCms.ImageCmsProfile(io.BytesIO(icc_profile))
                output_profile = ImageCms.createProfile("sRGB")
                return ImageCms.profileToProfile(
                    image,
                    input_profile,
                    output_profile,
                    outputMode="RGB",
                )
            except (ImageCms.PyCMSError, OSError, ValueError):
                pass
        return image.convert("RGB")


def derivative_widths(source_width: int) -> list[int]:
    maximum = min(source_width, TARGET_WIDTHS[-1])
    return sorted({width for width in TARGET_WIDTHS if width < maximum} | {maximum})


def derivative_directory(output_root: Path, relative: str) -> Path:
    digest = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:12]
    stem = re.sub(r"[^a-z0-9]+", "-", Path(relative).stem.lower()).strip("-")[:44] or "image"
    return output_root / f"{stem}-{digest}"


def derivatives_are_current(source_path: Path, directory: Path, widths: list[int]) -> bool:
    """True when every expected derivative exists and is newer than the source."""
    if not directory.is_dir():
        return False
    source_mtime = source_path.stat().st_mtime
    for width in widths:
        target = directory / f"{width}.webp"
        if not target.is_file() or target.stat().st_mtime < source_mtime:
            return False
    return True


def build_images(
    root: Path, paths: list[str], output_root: Path, incremental: bool = False
) -> tuple[dict, dict]:
    # Derivative directories are keyed by the source path, so a full rebuild
    # re-encodes every image even when one was added. --incremental keeps the
    # derivatives that are still newer than their source and encodes the rest.
    if output_root.exists() and not incremental:
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, dict] = {}
    original_bytes = 0
    derivative_bytes = 0
    largest_derivative = {"path": "", "bytes": 0}
    encoded = 0
    reused = 0

    for relative in paths:
        source_path = root / relative
        original_bytes += source_path.stat().st_size
        directory = derivative_directory(output_root, relative)
        with Image.open(source_path) as probe:
            source_width, source_height = probe.size
        widths = derivative_widths(source_width)
        image = None
        if incremental and derivatives_are_current(source_path, directory, widths):
            reused += 1
        else:
            image = normalized_image(source_path)
            source_width, source_height = image.size
            widths = derivative_widths(source_width)
            encoded += 1
        directory.mkdir(parents=True, exist_ok=True)
        variants = []
        for width in widths:
            height = max(1, round(source_height * width / source_width))
            target = directory / f"{width}.webp"
            if image is not None:
                resized = image if width == source_width else image.resize((width, height), Image.Resampling.LANCZOS)
                resized.save(target, "WEBP", quality=80, method=6, exact=True)
            size = target.stat().st_size
            derivative_bytes += size
            if size > largest_derivative["bytes"]:
                largest_derivative = {"path": target.relative_to(root).as_posix(), "bytes": size}
            variants.append({
                "path": target.relative_to(root).as_posix(),
                "width": width,
                "height": height,
                "bytes": size,
            })
        default = next((item for item in variants if item["width"] >= 960), variants[-1])
        mapping[relative] = {
            "width": source_width,
            "height": source_height,
            "default": default["path"],
            "variants": variants,
        }

    stale = 0
    if incremental:
        keep = {derivative_directory(output_root, relative).name for relative in paths}
        for child in output_root.iterdir():
            if child.is_dir() and child.name not in keep:
                shutil.rmtree(child)
                stale += 1

    report = {
        "sourceImages": len(paths),
        "derivativeFiles": sum(len(item["variants"]) for item in mapping.values()),
        "sourceBytes": original_bytes,
        "derivativeBytes": derivative_bytes,
        "largestDerivative": largest_derivative,
    }
    if incremental:
        report["incremental"] = {"encoded": encoded, "reused": reused, "removedStaleDirectories": stale}
    return mapping, report


def write_javascript_mapping(path: Path, mapping: dict) -> None:
    payload = json.dumps(mapping, ensure_ascii=False, separators=(",", ":"))
    path.write_text(
        "// Generated by scripts/build_site_assets.py. Do not edit manually.\n"
        f"export const IMAGE_DERIVATIVES = Object.freeze({payload});\n",
        encoding="utf-8",
    )


def home_payload(data_root: Path) -> dict:
    manifest = read_json(data_root / "manifest.json")
    events = read_json(data_root / "timeline-events.json").get("records", [])
    media = read_json(data_root / "media.json").get("records", [])
    counts = manifest["counts"]

    def event_sort_key(item: dict) -> str:
        return str(item.get("sortDate") or item.get("dateStart") or "")

    events_by_id = {item["id"]: item for item in events}
    media_by_id = {item["id"]: item for item in media}
    # Curated signature moments — one per era, chosen for narrative strength, so the
    # home teaser spans the whole career (Warsaw → Europe → Hollywood):
    # first published songs → the Jurmann partnership → the Hollywood debut.
    pinned = [events_by_id.get(event_id) for event_id in ("TE0014", "TE0026", "TE0037")]
    featured = sorted((item for item in events if item.get("featured")), key=event_sort_key)
    if all(pinned):
        event_selection = sorted(pinned, key=event_sort_key)[:3]
    elif len(featured) >= 3:
        # Fallback: one featured moment per era so the teaser still spans the career.
        selection: list[dict] = []
        chosen: set = set()
        for era in ("warsaw", "european", "hollywood"):
            pick = next((item for item in featured if item.get("period") == era), None)
            if pick and pick["id"] not in chosen:
                selection.append(pick)
                chosen.add(pick["id"])
        for item in featured:
            if len(selection) >= 3:
                break
            if item["id"] not in chosen:
                selection.append(item)
                chosen.add(item["id"])
        event_selection = sorted(selection, key=event_sort_key)[:3]
    else:
        candidates = sorted(
            (item for item in events if item.get("shortDescription")),
            key=lambda item: int(item.get("sortOrder") or 999),
        )
        indexes = sorted({0, len(candidates) // 2, max(0, len(candidates) - 1)})
        event_selection = [candidates[index] for index in indexes if candidates][:3]
    journey_media_ids = {
        "TE0014": "M080",
        "TE0026": "M046",
        "TE0037": "M074",
    }
    journey = []
    for event in event_selection:
        chapter = dict(event)
        image_id = journey_media_ids.get(event["id"])
        if image_id and image_id in media_by_id:
            chapter["image"] = media_by_id[image_id]
        journey.append(chapter)

    portrait = media_by_id.get("M048")
    if portrait is None:
        portrait = next(
            (item for item in media if item.get("category") == "portrait" and item.get("assetPath")),
            None,
        )
    curated_highlight_ids = ("M227", "M037", "M115")
    highlights = [media_by_id[item_id] for item_id in curated_highlight_ids if item_id in media_by_id]
    fallback_highlights = sorted(
        (
            item for item in media
            if item.get("galleryStatus") == "selected"
            and item.get("storageType") == "local"
            and item.get("assetPath")
            and item.get("mediaType") != "audio"
        ),
        key=lambda item: int(item.get("sortOrder") or 99999),
    )
    portrait_id = portrait.get("id") if portrait else None
    highlight_ids = {entry.get("id") for entry in highlights}
    for item in fallback_highlights:
        if len(highlights) >= 3:
            break
        if item.get("id") != portrait_id and item.get("id") not in highlight_ids:
            highlights.append(item)
            highlight_ids.add(item.get("id"))
    return {
        "schemaVersion": manifest.get("schemaVersion", "1.0.0"),
        "stats": [counts["Works"], counts["Timeline Events"], counts["Places"], counts["Sources"]],
        "portrait": portrait,
        "journey": journey,
        "highlights": highlights,
    }


def validate(root: Path, public_data_root: Path, site_data_root: Path, mapping_path: Path, report_path: Path) -> list[str]:
    errors: list[str] = []
    media = read_json(public_data_root / "media.json")
    expected = set(local_image_paths(media, root))
    if not mapping_path.is_file():
        return [f"Missing responsive-image mapping: {mapping_path}"]
    text = mapping_path.read_text(encoding="utf-8")
    match = re.search(r"Object\.freeze\((\{.*\})\);\s*$", text, re.DOTALL)
    if not match:
        return [f"Invalid responsive-image mapping: {mapping_path}"]
    mapping = json.loads(match.group(1))
    if set(mapping) != expected:
        errors.append("Responsive-image mapping does not match public local image paths")
    for source, entry in mapping.items():
        for variant in entry.get("variants", []):
            target = root / variant["path"]
            if not target.is_file():
                errors.append(f"Missing derivative for {source}: {variant['path']}")
            elif target.stat().st_size != variant["bytes"]:
                errors.append(f"Derivative size mismatch: {variant['path']}")
    if not (site_data_root / "home.json").is_file():
        errors.append("Missing compact home-page payload")
    if not report_path.is_file():
        errors.append("Missing image performance report")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Reuse derivatives that are still newer than their source image instead of "
             "re-encoding everything. Use this after adding or replacing a few images; a "
             "full rebuild takes minutes, this takes seconds.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    public_data_root = root / "data/public/v1"
    site_data_root = root / "data/site"
    output_root = root / "assets/generated/responsive"
    mapping_path = root / "assets/site/image-derivatives.js"
    report_path = site_data_root / "performance-report.json"
    if args.check:
        errors = validate(root, public_data_root, site_data_root, mapping_path, report_path)
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        return 0 if not errors else 1

    media_payload = read_json(public_data_root / "media.json")
    paths = local_image_paths(media_payload, root)
    mapping, report = build_images(root, paths, output_root, incremental=args.incremental)
    write_javascript_mapping(mapping_path, mapping)
    home = home_payload(public_data_root)
    write_json(site_data_root / "home.json", home)
    report["homePayloadBytes"] = (site_data_root / "home.json").stat().st_size
    portrait_path = home.get("portrait", {}).get("assetPath") if home.get("portrait") else None
    if portrait_path in mapping:
        report["homePortrait"] = mapping[portrait_path]
    write_json(report_path, report)
    print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
