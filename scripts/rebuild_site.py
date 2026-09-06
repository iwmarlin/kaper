#!/usr/bin/env python3
"""Rebuild and validate every derived public layer in the required order.

This is the canonical command after editing public JSON, export overrides, or a
published image. It prevents a valid canonical dataset from being committed
alongside stale record payloads, static pages, responsive images, or cache
versions.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Step:
    label: str
    command: tuple[str, ...]


def run_step(step: Step, root: Path) -> None:
    print(f"\n==> {step.label}", flush=True)
    try:
        subprocess.run(step.command, cwd=root, check=True)
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"{step.label} failed with exit status {error.returncode}"
        ) from error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--full-images",
        action="store_true",
        help="re-encode every responsive image instead of reusing current derivatives",
    )
    parser.add_argument(
        "--publication-date",
        help="YYYY-MM-DD assigned to routes whose public HTML changed (default: today)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    scripts = root / "scripts"
    python = sys.executable

    image_command = [python, str(scripts / "build_site_assets.py"), "--root", str(root)]
    if not args.full_images:
        image_command.append("--incremental")

    static_command = [
        python,
        str(scripts / "build_static_records.py"),
        "--root",
        str(root),
    ]
    if args.publication_date:
        static_command.extend(["--publication-date", args.publication_date])

    build_steps = (
        Step(
            "Reconcile public manifest and build report",
            (python, str(scripts / "reconcile_manifest.py"), "--root", str(root)),
        ),
        Step("Build responsive images and home payload", tuple(image_command)),
        Step(
            "Build compact catalogue indexes and prerender first results",
            (python, str(scripts / "build_catalogue_indexes.py"), "--root", str(root)),
        ),
        Step(
            "Build per-record payloads",
            (python, str(scripts / "build_record_payloads.py"), "--root", str(root)),
        ),
        Step(
            "Stamp content-derived CSS and JavaScript versions",
            (python, str(scripts / "stamp_assets.py")),
        ),
        Step("Build complete static record pages and sitemap", tuple(static_command)),
    )

    check_steps = (
        Step(
            "Check manifest freshness",
            (python, str(scripts / "reconcile_manifest.py"), "--root", str(root), "--check"),
        ),
        Step(
            "Check responsive assets and home payload",
            (python, str(scripts / "build_site_assets.py"), "--root", str(root), "--check"),
        ),
        Step(
            "Check compact catalogue indexes and prerendered results",
            (
                python,
                str(scripts / "build_catalogue_indexes.py"),
                "--root",
                str(root),
                "--check",
            ),
        ),
        Step(
            "Check per-record payloads",
            (python, str(scripts / "build_record_payloads.py"), "--root", str(root), "--check"),
        ),
        Step(
            "Check static records and sitemap",
            (python, str(scripts / "build_static_records.py"), "--root", str(root), "--check"),
        ),
        Step(
            "Validate public data and graph relations",
            (
                python,
                str(scripts / "validate_public_export.py"),
                "--data",
                str(root / "data/public/v1"),
                "--assets-root",
                str(root),
            ),
        ),
        Step(
            "Validate the complete site",
            (python, str(scripts / "validate_site.py"), "--root", str(root)),
        ),
    )

    try:
        for step in (*build_steps, *check_steps):
            run_step(step, root)
    except RuntimeError as error:
        print(f"\nREBUILD FAILED: {error}", file=sys.stderr)
        return 1

    print("\nREBUILD COMPLETE: all generated layers and validations are current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
