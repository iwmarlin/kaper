#!/usr/bin/env python3
"""List media whose stated copyright term runs out, for the yearly rights review.

Restricted and undetermined media state in their rights note the year a term
ends ("to the end of 2027"). Run this each January: every record listed for a
past year is due for reclassification (docs/media-rights-audit.md, finding 8).

    python3 scripts/rights_expiry.py            # all years
    python3 scripts/rights_expiry.py --due      # only terms already ended
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

UNCLEARED = {"restricted", "copyright_undetermined", "mixed_rights", "permission_needed_or_fair_use_claimed"}
END_PATTERN = re.compile(r"(?:to|until|through) the end of (\d{4})|to 1 January (\d{4})")


def expiries(data_root: Path) -> dict[int, list[str]]:
    payload = json.loads((data_root / "media.json").read_text(encoding="utf-8"))
    by_year: dict[int, list[str]] = {}
    for item in payload["records"]:
        if item.get("rightsStatus") not in UNCLEARED:
            continue
        years = [
            int(end) if end else int(first_free) - 1
            for end, first_free in END_PATTERN.findall(item.get("rightsNote") or "")
        ]
        if years:
            by_year.setdefault(max(years), []).append(item["id"])
    return dict(sorted(by_year.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", default="data/public/v1", type=Path)
    parser.add_argument("--due", action="store_true", help="only terms that have already ended")
    args = parser.parse_args()
    this_year = date.today().year
    for year, ids in expiries(args.data).items():
        if args.due and year >= this_year:
            continue
        marker = "DUE  " if year < this_year else "     "
        print(f"{marker}term ends {year}, free from 1 January {year + 1}: {', '.join(ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
