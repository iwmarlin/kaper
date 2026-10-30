#!/usr/bin/env python3
"""Normalize public Organization authority and contextual reference lists."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from organization_authorities import normalize_organization_authorities


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_payload(organizations_path: Path) -> dict:
    payload = read_json(organizations_path)
    normalize_organization_authorities(payload.get("records", []))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "organizations",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "data/public/v1/organizations.json",
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    organizations_path = args.organizations.resolve()
    original = read_json(organizations_path)
    normalized = normalized_payload(organizations_path)
    if original == normalized:
        print("Organization authority normalization: no drift")
        return 0
    if not args.write:
        print("Organization authority normalization: drift detected")
        return 1

    serialized = json.dumps(normalized, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=organizations_path.parent,
        prefix=f".{organizations_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(serialized)
        temporary = Path(handle.name)
    temporary.replace(organizations_path)
    print("Organization authority normalization: updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
