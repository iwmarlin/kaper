#!/usr/bin/env python3
"""Normalize public People authority and contextual reference link stacks."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from person_authorities import synchronize_person_authority_sources


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_payload(people_path: Path, sources_path: Path) -> dict:
    payload = read_json(people_path)
    synchronize_person_authority_sources(
        payload.get("records", []),
        read_json(sources_path).get("records", []),
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "people",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data/public/v1/people.json",
    )
    parser.add_argument("--sources", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    people_path = args.people.resolve()
    sources_path = (
        args.sources.resolve()
        if args.sources
        else people_path.with_name("sources.json")
    )
    original = read_json(people_path)
    normalized = normalized_payload(people_path, sources_path)
    if original == normalized:
        print("Person authority normalization: no drift")
        return 0
    if not args.write:
        print("Person authority normalization: drift detected")
        return 1

    serialized = json.dumps(normalized, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=people_path.parent,
        prefix=f".{people_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(serialized)
        temporary = Path(handle.name)
    temporary.replace(people_path)
    print("Person authority normalization: updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
