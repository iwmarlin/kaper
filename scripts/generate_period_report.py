#!/usr/bin/env python3
"""
Generate a period report for people records by analysing data/public/v1/people.json,
data/public/v1/works.json and data/public/v1/timeline-events.json.

Writes JSON report to reports/period_report.json and prints a brief summary.

Usage: python3 scripts/generate_period_report.py

Do NOT run this script on untrusted data. It expects the repository layout used by the site.
"""

import json
from pathlib import Path

ROOT = Path("data/public/v1")
OUT_DIR = Path("reports")

def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Could not read {path}: {e}")
        raise

people_payload = load_json(ROOT / "people.json")
works_payload = load_json(ROOT / "works.json")
events_payload = load_json(ROOT / "timeline-events.json")

people = people_payload.get("records", [])
works = {r.get("id"): r for r in works_payload.get("records", [])}
events = {r.get("id"): r for r in events_payload.get("records", [])}


def normalize_period(p):
    if not p:
        return None
    p = str(p).lower()
    if p in ("warsaw", "warsaw") or "warsaw" in p:
        return "warsaw"
    if p in ("european", "europe") or "european" in p or "europe" in p:
        return "european"
    if "hollywood" in p:
        return "hollywood"
    # return raw normalized string for manual review
    return p.replace(" ", "_")


def periods_from_works(work_ids):
    periods = set()
    details = []
    for wid in work_ids or []:
        w = works.get(wid)
        if not w:
            details.append({"workId": wid, "periods": None, "note": "work record missing"})
            continue
        ps = w.get("periods") or ([w.get("period")] if w.get("period") else [])
        ps_norm = [normalize_period(x) for x in ps if x]
        for p in ps_norm:
            if p:
                periods.add(p)
        details.append({"workId": wid, "periods": ps_norm})
    return sorted(periods), details


def periods_from_events(event_ids):
    periods = set()
    details = []
    for eid in event_ids or []:
        ev = events.get(eid)
        if not ev:
            details.append({"eventId": eid, "periods": None, "note": "event record missing"})
            continue
        if ev.get("periods"):
            ps_norm = [normalize_period(x) for x in ev.get("periods")]
            for p in ps_norm:
                if p:
                    periods.add(p)
            details.append({"eventId": eid, "periods": ps_norm, "source": "event.periods"})
            continue
        # fallback: map dateStart year to period ranges
        ds = ev.get("dateStart")
        year = None
        if ds:
            try:
                year = int(str(ds).split("-")[0])
            except Exception:
                year = None
        if year:
            if 1902 <= year <= 1926:
                p = "warsaw"
            elif 1926 <= year <= 1934:
                p = "european"
            elif 1935 <= year <= 1939:
                p = "hollywood"
            else:
                p = None
            if p:
                periods.add(p)
            details.append({"eventId": eid, "periods": [p] if p else [], "source": "dateStart_year_map", "year": year})
        else:
            details.append({"eventId": eid, "periods": [], "note": "no dateStart"})
    return sorted(periods), details


OUT_DIR.mkdir(exist_ok=True)
report = []
no_period_count = 0

for person in people:
    pid = person.get("id")
    name = person.get("displayName") or person.get("slug") or pid
    work_ids = person.get("workIds") or []
    event_ids = person.get("timelineEventIds") or []

    periods, wdetails = periods_from_works(work_ids)
    fallback_periods, edetails = ([], [])
    if not periods:
        fallback_periods, edetails = periods_from_events(event_ids)

    proposed = sorted(set(periods + fallback_periods))
    needs_manual = not bool(proposed)
    if needs_manual:
        no_period_count += 1

    report.append({
        "id": pid,
        "displayName": name,
        "workIds": work_ids,
        "work_periods_found": periods,
        "work_details": wdetails,
        "eventIds": event_ids,
        "event_periods_found": fallback_periods,
        "event_details": edetails,
        "proposed_periods": proposed,
        "needs_manual_review": needs_manual,
    })

out = {
    "summary": {
        "total_people": len(people),
        "without_proposed_periods": no_period_count,
    },
    "report": report,
}

# write JSON
out_path = OUT_DIR / "period_report.json"
out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {out_path} — total people: {len(people)}, without proposed periods: {no_period_count}")
