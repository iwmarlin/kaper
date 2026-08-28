#!/usr/bin/env python3
"""Reconcile manifest.json and build-report.json with the current public data.

Run this after any *manual* edit to data/public/v1/*.json or
scripts/public_export_overrides.json (i.e. when you did not run the full
export_public_data.py). It recomputes directly from the canonical public files:

  - per-table record counts (payload.count + manifest.counts + build-report.counts)
  - per-file byte sizes and sha256 checksums (manifest.files)
  - the overrides checksum and applied/addition/linkAddition counts
  - the generator checksum recorded in the manifest

Then run scripts/validate_public_export.py to confirm everything is consistent.

Usage:
    python3 scripts/reconcile_manifest.py            # apply changes
    python3 scripts/reconcile_manifest.py --check     # report drift, change nothing
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    args = parser.parse_args()

    root: Path = args.root
    data_root = root / "data/public/v1"
    config = read_json(root / "scripts/public_export_config.json")
    overrides_path = root / "scripts/public_export_overrides.json"
    config_path = root / "scripts/public_export_config.json"

    manifest_path = data_root / "manifest.json"
    report_path = data_root / "build-report.json"
    manifest = read_json(manifest_path)
    report = read_json(report_path)

    changes: list[str] = []

    # 1) counts per table (keyed by the public table display name)
    counts = {}
    corrected_payloads: dict[str, bytes] = {}
    for table_name, table_cfg in config["tables"].items():
        file_name = table_cfg["file"]
        payload = read_json(data_root / file_name)
        record_count = len(payload.get("records", []))
        counts[table_name] = record_count
        if payload.get("count") != record_count:
            payload = dict(payload)
            payload["count"] = record_count
            corrected_payloads[file_name] = json_bytes(payload)
            changes.append(f"{file_name}:count")
    if manifest.get("counts") != counts:
        changes.append("manifest.counts")
    if report.get("counts") != counts:
        changes.append("build-report.counts")

    report_new = dict(report)
    report_new["counts"] = counts
    report_new_bytes = json_bytes(report_new)

    # 2) file bytes + checksums
    new_files = []
    for entry in manifest.get("files", []):
        path = data_root / entry["file"]
        new_entry = dict(entry)
        if entry["file"] == "build-report.json":
            new_entry["bytes"] = len(report_new_bytes)
            new_entry["sha256"] = hashlib.sha256(report_new_bytes).hexdigest()
        elif entry["file"] in corrected_payloads:
            payload_bytes = corrected_payloads[entry["file"]]
            new_entry["bytes"] = len(payload_bytes)
            new_entry["sha256"] = hashlib.sha256(payload_bytes).hexdigest()
        else:
            new_entry["bytes"] = path.stat().st_size
            new_entry["sha256"] = sha256(path)
        if new_entry != entry:
            changes.append(f"files:{entry['file']}")
        new_files.append(new_entry)

    # 3) overrides checksum + counts
    overrides = read_json(overrides_path)
    applied = sum(len(v) for v in overrides.get("records", {}).values())
    additions = sum(len(v) for v in overrides.get("additions", {}).values())
    exclusions = sum(len(v) for v in overrides.get("exclusions", {}).values())
    link_additions = sum(len(v) for v in overrides.get("linkAdditions", {}).values())
    link_removals = sum(len(v) for v in overrides.get("linkRemovals", {}).values())
    ov = dict(manifest["publicInputs"]["overrides"])
    ov_new = dict(ov)
    ov_new["sha256"] = sha256(overrides_path)
    ov_new["appliedCount"] = applied
    ov_new["additionCount"] = additions
    ov_new["exclusionCount"] = exclusions
    ov_new["linkAdditionCount"] = link_additions
    ov_new["linkRemovalCount"] = link_removals
    if ov_new != ov:
        changes.append("overrides(sha/counts)")

    # 4) allowlist checksum. The field allowlist is meant to be stable, so this
    # is normally a no-op; it moves only when the public schema itself gains a
    # field. Reconciling it here keeps that a one-command change rather than a
    # hand-edited hash.
    allow = dict(manifest["publicInputs"]["allowlist"])
    allow_new = dict(allow)
    allow_new["sha256"] = sha256(config_path)
    if allow_new != allow:
        changes.append("allowlist(sha)")

    # 5) exporter checksum. Manual public-data corrections may be accompanied
    # by a schema/exporter change, and the manifest must continue to identify
    # the exact generator that will reproduce the next export.
    generator_path = root / "scripts/export_public_data.py"
    generator_new = dict(manifest["generator"])
    generator_new["sha256"] = sha256(generator_path)
    if generator_new != manifest["generator"]:
        changes.append("generator(sha)")

    if args.check:
        print("DRIFT:" if changes else "clean:", ", ".join(changes) or "manifest already consistent")
        return 1 if changes else 0

    for file_name, payload_bytes in corrected_payloads.items():
        (data_root / file_name).write_bytes(payload_bytes)

    manifest["counts"] = counts
    manifest["files"] = new_files
    manifest["publicInputs"]["overrides"] = ov_new
    manifest["publicInputs"]["allowlist"] = allow_new
    manifest["generator"] = generator_new
    write_json(report_path, report_new)
    write_json(manifest_path, manifest)

    print("reconciled:", ", ".join(changes) if changes else "no changes needed")
    print(f"  counts: Places={counts['Places']} Media={counts['Media']} Sources={counts['Sources']}")
    print(f"  overrides: applied={applied} exclusions={exclusions} additions={additions} linkAdditions={link_additions}")
    print("Next: python3 scripts/validate_public_export.py --data data/public/v1 "
          "--config scripts/public_export_config.json --overrides scripts/public_export_overrides.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
