#!/usr/bin/env python3
"""Register an external listening or viewing reference for a work.

The archive keeps recordings it cannot rehost as external media records: the
file stays where it is, the record carries the citation, the rights note and
the link. Doing that by hand means allocating two identifiers, writing two
records in the house pattern, updating every reciprocal endpoint and
remembering to bump the `count` header. This script does all of it from a URL
and a work identifier.

    python3 scripts/add_listening_reference.py --url URL --work W-S031
    python3 scripts/add_listening_reference.py --url URL --work W-S031 --person P118
    python3 scripts/add_listening_reference.py --batch references.tsv
    python3 scripts/add_listening_reference.py --url URL --work W-S031 --dry-run

The batch file is tab-separated, one reference per line, comments with `#`:

    https://www.youtube.com/watch?v=…	W-S031	P118
    https://www.youtube.com/watch?v=…	W-S042

One external audio reference is allowed per work. The script refuses a second
one so that alternate performances do not accumulate without an editorial
decision. Exceptional multiplicity must be documented explicitly in
``public_export_config.json`` and is checked by the public-export validator.

Organizations are never inferred from the work for audio references. Pass a
precise ``--source-organization`` for a label or ensemble documented by this
recording. ``--publisher-org`` describes a sheet-music publisher printed on a
disc label and therefore stays on the Source rather than the audio Media.

When the upload films the disc label — as the Radiomuseum Hardthausen uploads do
— pass what the label prints. The record then becomes a discographic source of
high reliability, because the evidence is the disc and the video only the way to
it. Link only the individual contributions that the label actually corroborates:

    python3 scripts/add_listening_reference.py --url URL --work W-S007 \
        --label Grammophon --catalogue "B 50959" --order-number 22222 --side 2 \
        --electrical --genre "Fox-trot" \
        --performer-credit "Ben Berlin und sein Orchester" \
        --credit "(Kaper – Rotter)" \
        --publisher-credit "(Verlag: Roehr A.-G., Berlin)" --publisher-org ORG118 \
        --uploader-note "The uploader gives Berlin, 1929 as the recording" \
        --contribution CON-S007-C-P009 \
        --contribution CON-S007-L-P020

Transcribe those values from the label itself. Anything only the uploader
asserts belongs in --uploader-note, so that the citation keeps the two apart.

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
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from recording_organizations import (
    RECORDING_CONTRIBUTION_ROLES,
    is_recording_label_or_ensemble,
)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "public" / "v1"
YOUTUBE_ORG = "ORG093"
RADIOMUSEUM_ORG = "ORG104"
RADIOMUSEUM_CHANNEL = "Radiomuseum Hardthausen"
RADIOMUSEUM_REPOSITORY = "Radiomuseum Hardthausen / Schallarchiv"
USER_AGENT = "Mozilla/5.0 (compatible; kaper-archive/1.0)"

RIGHTS_STATUS = "external_content_not_rehosted"
RIGHTS_NOTE = (
    "External content remains on the provider's website; no local copy is hosted. "
    "Copyright and access conditions are governed by the provider."
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
    """Replace one JSON table without exposing a partial file."""
    if "count" in table:
        table["count"] = len(table["records"])
    path = DATA / f"{name}.json"
    text = json.dumps(table, ensure_ascii=False, indent=2) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


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


def canonical_external_url(value: str) -> str:
    """Return a stable URL for duplicate detection and public storage.

    YouTube playlist, radio and timestamp parameters identify a viewing state,
    not a different recording.  Removing them prevents duplicate Media records
    such as the same video with and without ``&t=3s``.
    """
    parsed = urllib.parse.urlparse(value.strip())
    host = parsed.netloc.casefold().removeprefix("www.")
    if host in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
        video_id = urllib.parse.parse_qs(parsed.query).get("v", [""])[0]
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/", 1)[0]
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
    query = urllib.parse.urlencode(
        [
            (key, item)
            for key, item in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
            if not key.casefold().startswith("utm_")
        ]
    )
    return urllib.parse.urlunparse(
        (parsed.scheme.casefold(), parsed.netloc.casefold(), parsed.path, "", query, "")
    )


def external_audio_media_for_work(records: list[dict], work_id: str) -> list[dict]:
    """Return external listening references already attached to one work."""
    return [
        record
        for record in records
        if record.get("storageType") == "external"
        and record.get("mediaType") == "audio"
        and work_id in (record.get("workIds") or [])
    ]


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


def apply_disc(media: dict, source: dict, *, disc: dict, work_title: str, host: str) -> None:
    """Turn a plain listening reference into a discographic record.

    When the upload films the label, the disc is the evidence and the video only
    the way to it. Such a record is a recording_discographic_source of high
    reliability, and what the label prints belongs in the citation: performer,
    catalogue and order numbers, side, series, and the printed credits, which
    are what makes the source worth having.
    """
    label = disc.get("label") or "Grammophon"
    disc_title = disc.get("disc_title") or work_title
    catalogue = disc.get("catalogue") or ""
    order = disc.get("order_number") or ""
    performer = disc.get("performer_credit") or ""
    from_description = bool(disc.get("from_description"))
    # A digitising library that catalogues the disc it transfers — the Great 78
    # Project and its like — reads the label for us. The evidence is still the
    # disc, but the recording shows nothing, so the records must not claim a
    # label in view.
    catalogued_by = (disc.get("catalogued_by") or "").strip()
    repository = disc.get("repository") or (
        "" if (from_description or catalogued_by) else RADIOMUSEUM_REPOSITORY
    )

    numbers = ", ".join(
        part for part in (
            f"Katalog-Nr. {catalogue}" if catalogue else "",
            f"Bestell-Nr. {order}" if order else "",
            f"side marked {disc['side']}" if disc.get("side") else "",
        ) if part
    )
    printed = " and ".join(
        f"“{value}”" for value in (disc.get("credit"), disc.get("publisher_credit")) if value
    )
    physical = ", ".join(
        part for part in (
            label,
            "elektrische Aufnahme" if disc.get("electrical") else "",
            f"Serie {disc['series']}" if disc.get("series") else "",
            numbers,
        ) if part
    )
    # A supplied date is printed as given — "1931", but also "n.d. [recorded
    # 1929]" — and loses its own final stop so that the sentence keeps exactly
    # one.
    dated = (str(disc.get("date") or "").strip() or "n.d.").rstrip(".")
    citation_sentences = [
        f"{performer}." if performer else "",
        f"“{disc_title}.”",
        f"{disc['genre']};" if disc.get("genre") else "",
        f"label credit{'s' if ' and ' in printed else ''} {printed}." if printed else "",
        f"{physical}, {dated}.",
        (f"Digital transfer published on {host} by {disc.get('channel')}."
         if disc.get("channel") else f"Digital transfer published on {host}."),
        f"Accessed {human_date(source['accessDate'])}.",
    ]
    research_notes = []
    if disc.get("uploader_note"):
        statement = str(disc["uploader_note"]).strip().rstrip(".")
        research_notes.append(
            "Uploader-supplied information, not transcribed from the disc label: "
            f"{statement}."
        )
    if from_description:
        research_notes.append(
            "The discographic details are taken from the uploader's description; "
            "the label is not shown in the external recording."
        )
    elif catalogued_by:
        research_notes.append(
            f"The discographic details were catalogued from the disc by {catalogued_by}; "
            "the transfer carries sound alone, so the label is not shown in the external recording."
        )
    catalogued = f"{label} {catalogue}".strip()
    separator = " / " if catalogue else ", "
    reference = separator.join(
        part for part in (catalogued, f"Bestell-Nr. {order}" if order else "") if part
    )

    source["shortCitation"] = f"{reference}, “{disc_title}”"
    source["fullCitation"] = " ".join(part for part in citation_sentences if part)
    if research_notes:
        source["researchNote"] = " ".join(research_notes)
        source["researchNoteType"] = "discographic_note"
    source["sourceType"] = "recording_discographic_source"
    source["title"] = f"{disc_title} — {catalogued}"
    source["creator"] = performer or source.get("creator", "")
    if repository:
        source["repository"] = repository
    source["publication"] = label
    source["date"] = disc.get("date") or "n.d."
    source["reliability"] = "medium" if from_description else "high"
    if from_description:
        source["sourceStatus"] = "verified_with_attribution_note"
    source["slug"] = f"{source['id'].lower()}-{slugify(catalogued or label, 30)}-{slugify(disc_title, 40)}"
    organizations = list(source.get("organizationIds") or [])
    if RADIOMUSEUM_CHANNEL.lower() in (disc.get("channel") or "").lower():
        organizations.append(RADIOMUSEUM_ORG)
    if disc.get("publisher_org"):
        organizations.append(disc["publisher_org"])
    source["organizationIds"] = sorted(set(organizations))

    media["title"] = f"{work_title} — {reference.split(' / ')[0]}, listening reference"
    if from_description:
        media["description"] = (
            f"Recording of “{disc_title}”"
            + (f" by {performer}" if performer else "")
            + f", issued on {label}, linked as an external listening reference."
        )
        media["altText"] = f"Listening reference for “{work_title}”."
        media["publicCaption"] = (
            f"Listening reference for “{work_title}”"
            + (f" in the recording by {performer}" if performer else "")
            + f". The upload identifies the disc as {reference} in its description, without showing the label."
        )
    elif catalogued_by:
        media["description"] = (
            f"Recording of “{disc_title}”"
            + (f" by {performer}" if performer else "")
            + f", issued on {label}, in a digital transfer of the disc linked as an external listening reference."
        )
        media["altText"] = f"Listening reference for “{work_title}”."
        media["publicCaption"] = (
            f"Listening reference for “{work_title}”"
            + (f" in the recording by {performer}" if performer else "")
            + f". {catalogued_by} transferred the disc and catalogued it from the label as {reference}"
            + (f", which prints the credit{'s' if ' and ' in printed else ''} {printed}" if printed else "")
            + "; the transfer carries sound alone."
        )
    else:
        media["description"] = (
            f"Recording of “{disc_title}”"
            + (f" by {performer}" if performer else "")
            + f", filmed in play with the {label} label in view."
        )
        media["altText"] = (
            f"Listening reference for “{work_title}”, showing the {label} disc label."
        )
        media["publicCaption"] = (
            f"Listening reference for “{work_title}”"
            + (f" in the recording by {performer}" if performer else "")
            + f". The video shows the {reference} disc label"
            + (f", which prints the credit{'s' if ' and ' in printed else ''} {printed}." if printed else ".")
        )
    media["publicCreditLine"] = (
        f"{host} / {disc.get('channel') or repository} listening link; {reference}."
    )


def build_records(
    *,
    url: str,
    work: dict,
    meta: dict,
    media_id: str,
    source_id: str,
    person_id: str | None,
    performer: str | None,
    media_type: str,
    inherit_organizations: bool,
    source_organization_ids: list[str] | None = None,
    contribution_ids: list[str] | None = None,
    disc: dict | None = None,
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
    sung_by = f" sung by {performer}" if performer else ""
    caption = (
        f"Listening reference for “{work_title}”{sung_by}, published as “{title}” on {where}. "
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
        "title": f"{work_title} — {performer + ', ' if performer else ''}listening reference",
        "mediaType": media_type,
        "storageType": "external",
        "period": period,
        "description": f"Recording of “{work_title}”{sung_by}, linked as an external listening reference.",
        "externalUrl": url,
        "assetCount": 0,
        "altText": f"Listening reference for “{work_title}”{sung_by}.",
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

    medium_kind = "audio reference" if media_type == "audio" else "video"
    medium = f"YouTube {medium_kind}" if youtube else f"Online {medium_kind}, {host}"
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
        "sourceType": (
            "online_audio_source"
            if media_type == "audio"
            else "online_video_source"
        ),
        "title": f"{title} — {performer + ', ' if performer else ''}{host}",
        "creator": channel_label,
        "repository": host,
        "publication": host,
        "accessDate": today.isoformat(),
        "reliability": "low",
        "sourceStatus": "verified",
        "slug": f"{source_id.lower()}-{slugify(host, 20)}-{slugify(title, 50)}",
        "organizationIds": sorted(
            set(([YOUTUBE_ORG] if youtube else []) + (source_organization_ids or []))
        ),
        "mediaIds": [media_id],
        "workIds": [work["id"]],
        "primaryUrl": url,
    }
    for subtype_key in ("filmIds", "songIds", "otherWorkIds"):
        if work.get(subtype_key):
            source[subtype_key] = list(work[subtype_key])
    if person_id:
        source["personIds"] = [person_id]
    if contribution_ids:
        source["contributionIds"] = sorted(set(contribution_ids))
    if disc:
        apply_disc(media, source, disc={**disc, "channel": channel}, work_title=work_title, host=host)
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
    disc: dict | None = None,
    contribution_ids: list[str] | None = None,
    source_organization_ids: list[str] | None = None,
) -> str:
    table_names = (
        "media",
        "sources",
        "works",
        "films",
        "songs",
        "other-works",
        "people",
        "organizations",
        "contributions",
    )
    tables = {name: load(name) for name in table_names}
    media_table, source_table = tables["media"], tables["sources"]
    works = by_id(tables["works"])
    people = by_id(tables["people"])
    organizations = by_id(tables["organizations"])
    contributions = by_id(tables["contributions"])

    if work_id not in works:
        print(f"  ! no work {work_id}", file=sys.stderr)
        return "error"
    if person_id and person_id not in people:
        print(f"  ! no person {person_id}", file=sys.stderr)
        return "error"
    requested_contributions = sorted(set(contribution_ids or []))
    for contribution_id in requested_contributions:
        contribution = contributions.get(contribution_id)
        if not contribution:
            print(f"  ! no contribution {contribution_id}", file=sys.stderr)
            return "error"
        if work_id not in (contribution.get("workIds") or []):
            print(
                f"  ! contribution {contribution_id} is not linked to {work_id}",
                file=sys.stderr,
            )
            return "error"
    requested_organizations = sorted(set(source_organization_ids or []))
    for organization_id in requested_organizations:
        if organization_id not in organizations:
            print(f"  ! no organization {organization_id}", file=sys.stderr)
            return "error"
    if media_type == "audio" and inherit_organizations:
        print(
            "  ! audio media cannot inherit organizations from the work; "
            "use --source-organization for the exact label or ensemble",
            file=sys.stderr,
        )
        return "error"

    # A selected source-specific recording contribution is also evidence that
    # its organization belongs on the Source.  Person contributions add no
    # organization here.
    for contribution_id in requested_contributions:
        contribution = contributions[contribution_id]
        if contribution.get("role") not in RECORDING_CONTRIBUTION_ROLES:
            continue
        requested_organizations.extend(contribution.get("organizationIds") or [])
    requested_organizations = sorted(set(requested_organizations))
    canonical_url = canonical_external_url(url)
    parsed_url = urllib.parse.urlparse(canonical_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        print(f"  ! invalid external URL: {url}", file=sys.stderr)
        return "error"
    existing = next(
        (
            record
            for record in media_table["records"]
            if record.get("externalUrl")
            and canonical_external_url(record["externalUrl"]) == canonical_url
        ),
        None,
    )
    if existing:
        print(
            f"  = already registered as {existing['id']} (canonical URL {canonical_url}), "
            "nothing to do"
        )
        return "skipped"

    if media_type == "audio":
        existing_audio = external_audio_media_for_work(media_table["records"], work_id)
        if existing_audio:
            identifiers = ", ".join(record["id"] for record in existing_audio)
            print(
                f"  ! {work_id} already has an external listening reference "
                f"({identifiers}); the archive permits one external audio reference "
                "per work. Review the existing reference before replacing it.",
                file=sys.stderr,
            )
            return "error"

    meta = {"title": title or "", "channel": channel or ""}
    if not title or not channel:
        fetched = youtube_metadata(canonical_url)
        meta = {**fetched, **{k: v for k, v in meta.items() if v}}
    if not meta.get("title"):
        print("  ! could not read a title; pass --title and --channel", file=sys.stderr)
        return "error"

    work = works[work_id]
    media_id = next_id(media_table, "M", 3)
    source_id = next_id(source_table, "SRC", 4)
    media, source = build_records(
        url=canonical_url,
        work=work,
        meta=meta,
        media_id=media_id,
        source_id=source_id,
        person_id=person_id,
        performer=people[person_id]["displayName"] if person_id else None,
        media_type=media_type,
        inherit_organizations=inherit_organizations,
        source_organization_ids=requested_organizations,
        contribution_ids=requested_contributions,
        disc=disc,
    )

    unknown_source_organizations = sorted(
        set(source.get("organizationIds") or []) - set(organizations)
    )
    if unknown_source_organizations:
        print(
            f"  ! source refers to unknown organizations: {', '.join(unknown_source_organizations)}",
            file=sys.stderr,
        )
        return "error"

    if media_type == "audio":
        recording_organizations = sorted(
            organization_id
            for organization_id in requested_organizations
            if is_recording_label_or_ensemble(organizations[organization_id])
        )
        if recording_organizations:
            media["organizationIds"] = recording_organizations
        else:
            media.pop("organizationIds", None)

    print(f"  {media_id} ← {meta['title']}")
    print(f"  {source_id}   {source['fullCitation']}")
    print(f"  linked to {work_id} “{work['title']}”"
          + (f", {person_id} “{people[person_id]['displayName']}”" if person_id else "")
          + (f", contributions {', '.join(requested_contributions)}" if requested_contributions else ""))
    if dry_run:
        print("  (dry run, nothing written)")
        return "dry-run"

    media_table["records"].append(media)
    source_table["records"].append(source)
    for record in tables["works"]["records"]:
        if record["id"] == work_id:
            add_link(record, "mediaIds", media_id)
            add_link(record, "sourceIds", source_id)
    for record in tables["songs"]["records"]:
        if record["id"] in (work.get("songIds") or []):
            add_link(record, "sourceIds", source_id)
            add_link(record, "mediaIds", media_id)
    for table_name, subtype_key in (
        ("films", "filmIds"),
        ("other-works", "otherWorkIds"),
    ):
        for record in tables[table_name]["records"]:
            if record["id"] in (work.get(subtype_key) or []):
                add_link(record, "sourceIds", source_id)
    if person_id:
        for record in tables["people"]["records"]:
            if record["id"] == person_id:
                add_link(record, "sourceIds", source_id)
    for record in tables["organizations"]["records"]:
        if record["id"] in (source.get("organizationIds") or []):
            add_link(record, "sourceIds", source_id)
    for record in tables["contributions"]["records"]:
        if record["id"] in requested_contributions:
            add_link(record, "sourceIds", source_id)
    for name, table in tables.items():
        save(name, table)
    return "written"


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
    parser.add_argument("--person", help="performer's person identifier, e.g. P118; the name is "
                        "carried into the title, caption and alt text, and the source is linked to them")
    parser.add_argument("--batch", type=Path, help="tab-separated file of url / work / person")
    parser.add_argument("--title", help="upload title, when it cannot be read automatically")
    parser.add_argument("--channel", help="uploader, when it cannot be read automatically")
    parser.add_argument(
        "--media-type",
        default="audio",
        choices=["video", "audio"],
        help="public media kind; audio is the safe default for listening references",
    )
    parser.add_argument(
        "--contribution",
        action="append",
        default=[],
        help="contribution ID explicitly corroborated by this source; repeat as needed",
    )
    parser.add_argument(
        "--source-organization",
        action="append",
        default=[],
        help="organization directly represented by or responsible for the source; repeat as needed",
    )
    organization_inheritance = parser.add_mutually_exclusive_group()
    organization_inheritance.add_argument(
        "--inherit-work-organizations",
        action="store_true",
        help=(
            "video-only exception: copy organizations linked to the work onto the media; "
            "audio references reject this option"
        ),
    )
    organization_inheritance.add_argument(
        "--no-inherit-organizations",
        dest="inherit_work_organizations",
        action="store_false",
        help=argparse.SUPPRESS,
    )
    parser.set_defaults(inherit_work_organizations=False)
    parser.add_argument("--no-build", action="store_true", help="write records only")
    parser.add_argument("--dry-run", action="store_true")

    disc = parser.add_argument_group(
        "disc label",
        "For uploads that film the label — Radiomuseum Hardthausen and the like. Giving any of "
        "these makes the source a recording_discographic_source of high reliability, because the "
        "evidence is then the disc, not the video. Transcribe from the label, not from the "
        "uploader's description; what only the description says goes in --uploader-note.",
    )
    disc.add_argument("--label", help="record label as printed, e.g. Grammophon")
    disc.add_argument("--catalogue", help="Katalog-Nr., e.g. “B 50959”")
    disc.add_argument("--order-number", help="Bestell-Nr., e.g. “22222”")
    disc.add_argument("--side", help="side number printed on the label")
    disc.add_argument("--series", help="series line, e.g. “Polyfar „R“ Orchester”")
    disc.add_argument("--electrical", action="store_true", help="label says elektrische Aufnahme")
    disc.add_argument("--genre", help="genre as printed, e.g. Fox-trot")
    disc.add_argument("--performer-credit", help="performer as printed, e.g. “Ben Berlin und sein Orchester”")
    disc.add_argument("--credit", help="authorship credit as printed, e.g. “(Kaper – Rotter)”")
    disc.add_argument("--publisher-credit", help="publisher line as printed, e.g. “(Verlag: Roehr A.-G., Berlin)”")
    disc.add_argument("--publisher-org", help="organization identifier for that publisher, e.g. ORG118")
    disc.add_argument("--disc-title", help="title as printed, when it differs from the work title")
    disc.add_argument("--date", help="date field, e.g. “n.d. [recorded 1929 according to the uploader]”")
    disc.add_argument("--uploader-note", help="what the uploader states but the label does not print")
    disc.add_argument("--repository", help=f"holding archive; defaults to “{RADIOMUSEUM_REPOSITORY}”")
    disc.add_argument("--from-description", action="store_true",
                      help="the label is not shown in the upload and the numbers come from its "
                           "description: reliability drops to medium and the record says so")
    disc.add_argument("--catalogued-by",
                      help="digitising library that transferred the disc and catalogued it from the "
                           "label, e.g. “the Great 78 Project”: the evidence stays the disc, but the "
                           "records say that the transfer carries sound alone")
    disc.add_argument(
        "--link-contributions",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    disc_fields = {
        "label": args.label, "catalogue": args.catalogue, "order_number": args.order_number,
        "side": args.side, "series": args.series, "electrical": args.electrical,
        "genre": args.genre, "performer_credit": args.performer_credit, "credit": args.credit,
        "publisher_credit": args.publisher_credit, "publisher_org": args.publisher_org,
        "disc_title": args.disc_title, "date": args.date, "uploader_note": args.uploader_note,
        "repository": args.repository, "from_description": args.from_description,
        "catalogued_by": args.catalogued_by,
    }
    disc_details = disc_fields if any(
        value for key, value in disc_fields.items()
        if key not in ("electrical", "from_description")
    ) or args.electrical or args.from_description else None
    if disc_details and args.batch:
        parser.error("disc label details describe one disc; give them with --url, not --batch")
    if args.link_contributions:
        parser.error(
            "--link-contributions was removed because it linked unverified credits; "
            "use one --contribution ID for each credit explicitly supported by the source"
        )
    if args.batch and (args.contribution or args.source_organization):
        parser.error(
            "--contribution and --source-organization describe one source; "
            "use them with --url, not --batch"
        )

    if args.batch:
        entries = parse_batch(args.batch)
    elif args.url and args.work:
        entries = [(args.url, args.work, args.person)]
    else:
        parser.error("give either --url and --work, or --batch")

    written = 0
    failures = 0
    for url, work_id, person_id in entries:
        print(f"{url}")
        outcome = register(
            url=url,
            work_id=work_id,
            person_id=person_id,
            title=args.title,
            channel=args.channel,
            media_type=args.media_type,
            inherit_organizations=args.inherit_work_organizations,
            dry_run=args.dry_run,
            disc=disc_details,
            contribution_ids=args.contribution,
            source_organization_ids=args.source_organization,
        )
        if outcome == "written":
            written += 1
        elif outcome == "error":
            failures += 1

    print(f"\n{written} reference{'' if written == 1 else 's'} written")
    if written and not args.no_build and not args.dry_run:
        pipeline_status = run_pipeline()
        if pipeline_status:
            return pipeline_status
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
