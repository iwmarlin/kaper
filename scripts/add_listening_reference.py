#!/usr/bin/env python3
"""Register an external listening or viewing reference for a work.

The archive keeps recordings it cannot rehost as external media records: the
file stays where it is, the record carries the citation, the rights note and
the link. Doing that by hand means allocating two identifiers, writing two
records in the house pattern, linking four tables and remembering to bump the
`count` header. This script does all of it from a URL and a work identifier.

    python3 scripts/add_listening_reference.py --url URL --work W-S031
    python3 scripts/add_listening_reference.py --url URL --work W-S031 --person P118
    python3 scripts/add_listening_reference.py --batch references.tsv
    python3 scripts/add_listening_reference.py --url URL --work W-S031 --dry-run

The batch file is tab-separated, one reference per line, comments with `#`:

    https://www.youtube.com/watch?v=…	W-S031	P118
    https://www.youtube.com/watch?v=…	W-S042

Metadata comes from YouTube's oEmbed endpoint (title and channel, no API key)
and, when reachable, from the `uploadDate` in the watch page. Nothing is
invented: if the title cannot be read, the script stops rather than writing a
citation it made up. Pass --title/--channel to supply them by hand, which is
also the route for non-YouTube hosts.

After writing, the site is rebuilt and both validators are run unless
--no-build is given.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "public" / "v1"
YOUTUBE_ORG = "ORG093"
USER_AGENT = "Mozilla/5.0 (compatible; kaper-archive/1.0)"

RIGHTS_STATUS = "permission_needed_or_fair_use_claimed"
RIGHTS_NOTE = (
    "External media is linked for scholarly reference and is not rehosted; "
    "reuse rights are not cleared."
)

BUILD_STEPS = [
    ["scripts/build_site_assets.py", "--root", "."],
    ["scripts/build_record_payloads.py", "--root", "."],
    ["scripts/stamp_assets.py"],
    ["scripts/build_static_records.py", "--root", "."],
    ["scripts/reconcile_manifest.py"],
    ["scripts/reconcile_manifest.py"],
]


# ---------------------------------------------------------------- table access


def load(name: str) -> dict:
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


def save(name: str, table: dict) -> None:
    if "count" in table:
        table["count"] = len(table["records"])
    path = DATA / f"{name}.json"
    path.write_text(
        json.dumps(table, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def by_id(table: dict) -> dict:
    return {record["id"]: record for record in table["records"]}


def next_id(table: dict, prefix: str, width: int) -> str:
    numbers = [
        int(record["id"][len(prefix):])
        for record in table["records"]
        if re.fullmatch(rf"{prefix}\d+", record["id"])
    ]
    return f"{prefix}{max(numbers) + 1:0{width}d}"


def add_link(record: dict, key: str, value: str) -> None:
    record[key] = sorted(set((record.get(key) or []) + [value]))


# ------------------------------------------------------------------- metadata


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def youtube_metadata(url: str) -> dict:
    """Title, channel and upload date, as far as they can be read."""
    meta: dict[str, str] = {}
    oembed = (
        "https://www.youtube.com/oembed?url="
        + urllib.parse.quote(url, safe="")
        + "&format=json"
    )
    try:
        payload = fetch_json(oembed)
        meta["title"] = payload.get("title", "").strip()
        meta["channel"] = payload.get("author_name", "").strip()
    except Exception as error:  # noqa: BLE001 - reported, not swallowed
        print(f"  ! oEmbed unavailable ({error})", file=sys.stderr)
    try:
        html = fetch_text(url)
        match = re.search(r'itemprop="uploadDate"[^>]*content="([^"]+)"', html)
        if not match:
            match = re.search(r'"uploadDate":"([0-9]{4}-[0-9]{2}-[0-9]{2})', html)
        if match:
            meta["uploadDate"] = match.group(1)[:10]
    except Exception:  # noqa: BLE001 - the upload date is optional
        pass
    return meta


def is_topic_channel(channel: str) -> bool:
    return bool(re.search(r"[-–—]\s*(Topic|Temat)$", channel.strip(), re.IGNORECASE))


def human_date(iso: str) -> str:
    try:
        parsed = date.fromisoformat(iso)
    except ValueError:
        return iso
    return f"{parsed.day} {parsed.strftime('%B')} {parsed.year}"


def slugify(text: str, limit: int = 60) -> str:
    ascii_text = (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug[:limit].rstrip("-")


# --------------------------------------------------------------- record making


def build_records(
    *,
    url: str,
    work: dict,
    meta: dict,
    media_id: str,
    source_id: str,
    person_id: str | None,
    media_type: str,
    inherit_organizations: bool,
) -> tuple[dict, dict]:
    title = meta["title"]
    channel = meta.get("channel", "")
    upload = meta.get("uploadDate", "")
    work_title = work["title"]
    period = work.get("period") or "european"
    periods = work.get("periods") or ([period] if period else [])
    today = date.today()
    accessed = human_date(today.isoformat())

    youtube = "youtube.com" in url or "youtu.be" in url
    host = "YouTube" if youtube else urllib.parse.urlparse(url).netloc
    auto_generated = youtube and is_topic_channel(channel)
    channel_label = (
        f"{channel} (auto-generated YouTube channel)" if auto_generated else channel
    )
    where = (
        "an auto-generated YouTube artist channel" if auto_generated
        else host + (f" by {channel}" if channel else "")
    )
    caption = (
        f"Listening reference for “{work_title}”, published as “{title}” on {where}. "
        "The upload carries no discographic detail, so the recording it transfers "
        "is not identified here; it is an access copy, not rights evidence."
    )
    credit = (
        f"YouTube, auto-generated “{channel}” channel; access copy only."
        if auto_generated
        else f"{host} upload by {channel}; access copy only." if channel
        else f"{host} upload; access copy only."
    )

    media = {
        "id": media_id,
        "title": f"{work_title} — listening reference",
        "mediaType": media_type,
        "storageType": "external",
        "period": period,
        "description": f"Recording of “{work_title}” linked as an external listening reference.",
        "externalUrl": url,
        "assetCount": 0,
        "altText": f"Listening reference for “{work_title}”.",
        "rightsStatus": RIGHTS_STATUS,
        "rightsNote": RIGHTS_NOTE,
        "sortOrder": int(media_id[1:]),
        "slug": f"{slugify(work_title)}-{media_id.lower()}",
        "publicCaption": caption,
        "publicCreditLine": credit,
        "category": "audio/video reference",
        "galleryStatus": "external_link_only",
        "sourceIds": [source_id],
        "workIds": [work["id"]],
        "periods": periods,
    }
    if work.get("songIds"):
        media["songIds"] = list(work["songIds"])
    if inherit_organizations and work.get("organizationIds"):
        media["organizationIds"] = list(work["organizationIds"])

    medium = "YouTube video" if youtube else f"Online video, {host}"
    citation_tail = (
        f"{medium}, uploaded {human_date(upload)}. Accessed {accessed}."
        if upload
        else f"{medium}. Accessed {accessed}."
    )
    source = {
        "id": source_id,
        "shortCitation": f"{host}, “{title}”",
        "fullCitation": (
            f"{channel_label}, uploader. “{title}.” {citation_tail}"
            if channel
            else f"“{title}.” {citation_tail}"
        ),
        "sourceType": "online_video_source",
        "title": f"{title} — {host}",
        "creator": channel_label,
        "repository": host,
        "publication": host,
        "accessDate": today.isoformat(),
        "reliability": "low",
        "sourceStatus": "verified",
        "slug": f"{source_id.lower()}-{slugify(host, 20)}-{slugify(title, 50)}",
        "organizationIds": [YOUTUBE_ORG] if youtube else [],
        "mediaIds": [media_id],
        "primaryUrl": url,
    }
    if person_id:
        source["personIds"] = [person_id]
    return media, source


# -------------------------------------------------------------------- the work


def register(
    *,
    url: str,
    work_id: str,
    person_id: str | None,
    title: str | None,
    channel: str | None,
    media_type: str,
    inherit_organizations: bool,
    dry_run: bool,
) -> bool:
    tables = {name: load(name) for name in ("media", "sources", "works", "songs", "people")}
    media_table, source_table = tables["media"], tables["sources"]
    works, people = by_id(tables["works"]), by_id(tables["people"])

    if work_id not in works:
        print(f"  ! no work {work_id}", file=sys.stderr)
        return False
    if person_id and person_id not in people:
        print(f"  ! no person {person_id}", file=sys.stderr)
        return False
    existing = next(
        (r for r in media_table["records"] if (r.get("externalUrl") or "") == url), None
    )
    if existing:
        print(f"  = already registered as {existing['id']}, nothing to do")
        return False

    meta = {"title": title or "", "channel": channel or ""}
    if not title or not channel:
        fetched = youtube_metadata(url)
        meta = {**fetched, **{k: v for k, v in meta.items() if v}}
    if not meta.get("title"):
        print("  ! could not read a title; pass --title and --channel", file=sys.stderr)
        return False

    work = works[work_id]
    media_id = next_id(media_table, "M", 3)
    source_id = next_id(source_table, "SRC", 4)
    media, source = build_records(
        url=url,
        work=work,
        meta=meta,
        media_id=media_id,
        source_id=source_id,
        person_id=person_id,
        media_type=media_type,
        inherit_organizations=inherit_organizations,
    )

    print(f"  {media_id} ← {meta['title']}")
    print(f"  {source_id}   {source['fullCitation']}")
    print(f"  linked to {work_id} “{work['title']}”"
          + (f", {person_id} “{people[person_id]['displayName']}”" if person_id else ""))
    if dry_run:
        print("  (dry run, nothing written)")
        return False

    media_table["records"].append(media)
    source_table["records"].append(source)
    for record in tables["works"]["records"]:
        if record["id"] == work_id:
            add_link(record, "mediaIds", media_id)
            add_link(record, "sourceIds", source_id)
    for record in tables["songs"]["records"]:
        if record["id"] in (work.get("songIds") or []):
            add_link(record, "sourceIds", source_id)
    if person_id:
        for record in tables["people"]["records"]:
            if record["id"] == person_id:
                add_link(record, "sourceIds", source_id)
    for name, table in tables.items():
        save(name, table)
    return True


def run_pipeline() -> int:
    for step in BUILD_STEPS:
        result = subprocess.run([sys.executable, *step], cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            print(f"! {step[0]} failed\n{result.stdout}\n{result.stderr}", file=sys.stderr)
            return result.returncode
    failures = 0
    for validator, args in (
        ("scripts/validate_public_export.py", ["--data", "data/public/v1", "--assets-root", "."]),
        ("scripts/validate_site.py", ["--root", "."]),
    ):
        result = subprocess.run([sys.executable, validator, *args], cwd=ROOT, capture_output=True, text=True)
        try:
            report = json.loads(result.stdout)
            ok = report.get("ok", not report.get("errors"))
            print(f"{validator}: ok={ok} errors={report.get('errors') or []}")
            failures += 0 if ok else 1
        except json.JSONDecodeError:
            print(f"{validator}: {result.stdout.strip() or result.stderr.strip()}")
            failures += result.returncode
    return failures


def parse_batch(path: Path) -> list[tuple[str, str, str | None]]:
    entries = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in re.split(r"\t+|\s{2,}", line) if part.strip()]
        if len(parts) < 2:
            raise SystemExit(f"{path}:{number}: expected at least a URL and a work id")
        entries.append((parts[0], parts[1], parts[2] if len(parts) > 2 else None))
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", help="URL of the recording")
    parser.add_argument("--work", help="work identifier, e.g. W-S031")
    parser.add_argument("--person", help="performer's person identifier, e.g. P118")
    parser.add_argument("--batch", type=Path, help="tab-separated file of url / work / person")
    parser.add_argument("--title", help="upload title, when it cannot be read automatically")
    parser.add_argument("--channel", help="uploader, when it cannot be read automatically")
    parser.add_argument("--media-type", default="video", choices=["video", "audio"])
    parser.add_argument("--no-inherit-organizations", action="store_true",
                        help="do not copy the work's organizations onto the media record")
    parser.add_argument("--no-build", action="store_true", help="write records only")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.batch:
        entries = parse_batch(args.batch)
    elif args.url and args.work:
        entries = [(args.url, args.work, args.person)]
    else:
        parser.error("give either --url and --work, or --batch")

    written = 0
    for url, work_id, person_id in entries:
        print(f"{url}")
        if register(
            url=url,
            work_id=work_id,
            person_id=person_id,
            title=args.title,
            channel=args.channel,
            media_type=args.media_type,
            inherit_organizations=not args.no_inherit_organizations,
            dry_run=args.dry_run,
        ):
            written += 1

    print(f"\n{written} reference{'' if written == 1 else 's'} written")
    if written and not args.no_build and not args.dry_run:
        return run_pipeline()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
