#!/usr/bin/env python3
"""Build compact browse payloads and prerender each index's first results."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


INDEX_FILES = {
    "works": "works.json",
    "people": "people.json",
    "media": "media.json",
    "sources": "sources.json",
}
PAGE_CONFIG = {
    "works": ("works.html", "work-results", "work-results-count", None),
    "people": ("people.html", "person-results", "person-results-count", "person-total-label"),
    "media": ("media.html", "media-results", "media-count", None),
    "sources": ("sources.html", "source-results", "source-results-count", "source-total-label"),
}
START_MARKER = "<!-- catalogue-prerender:start -->"
END_MARKER = "<!-- catalogue-prerender:end -->"
PERIOD_ORDER = ("warsaw", "european", "hollywood")
FUNCTION_ORDER = ("creators", "performers", "film", "documented")
FUNCTION_ROLES = {
    "creators": {"composer", "lyricist", "arranger", "music_contributor_role_unresolved"},
    "performers": {"performer", "conductor", "actor"},
    "film": {"film_director", "music_director", "producer", "associate_producer", "dialogue_director"},
}
FUNCTION_DESCRIPTIONS = {
    "creators": {"composer", "lyricist", "arranger", "poet", "satirist", "screenwriter", "writer"},
    "performers": {"performer", "singer", "pianist", "violinist", "conductor", "bandleader", "actor", "comedian"},
    "film": {"film director", "producer", "studio executive", "studio founder", "animator", "talent agent"},
}
FUNCTION_LABELS = {
    "creators": "Creators",
    "performers": "Performers",
    "film": "Film production",
    "documented": "Documented without credits",
}
MEDIA_FIELDS = (
    "id", "title", "mediaType", "category", "publicCaption", "description",
    "publicCreditLine", "period", "periods", "rightsStatus", "rightsNote",
    "galleryStatus", "sortOrder", "assetPath", "assetPaths", "storageType",
    "externalUrl", "altText",
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compact_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def records(data_root: Path, filename: str) -> list[dict]:
    return read_json(data_root / filename).get("records", [])


def periods(record: dict) -> list[str]:
    values = record.get("periods") or ([record.get("period")] if record.get("period") else [])
    found = {str(value).lower().replace(" ", "_") for value in values if value}
    return [value for value in PERIOD_ORDER if value in found]


def joined(values: list[object]) -> str:
    return " ".join(str(value) for value in values if value)


def works_index(data_root: Path, schema_version: str) -> dict:
    works = records(data_root, "works.json")
    people = {item["id"]: item for item in records(data_root, "people.json")}
    contributions = {item["id"]: item for item in records(data_root, "contributions.json")}
    variants = {item["id"]: item for item in records(data_root, "title-variants.json")}
    subtype_by_work: dict[str, dict] = {}
    for filename in ("films.json", "songs.json", "other-works.json"):
        for subtype in records(data_root, filename):
            for work_id in subtype.get("workIds") or []:
                subtype_by_work[work_id] = subtype

    output = []
    for work in works:
        subtype = subtype_by_work.get(work["id"], {})
        variant_ids = [*(work.get("titleVariantIds") or []), *(subtype.get("titleVariantIds") or [])]
        variant_parts: list[object] = []
        search_parts: list[object] = []
        for variant_id in dict.fromkeys(variant_ids):
            variant = variants.get(variant_id, {})
            variant_parts.extend((variant.get("variantTitle"), variant.get("titleAsSource")))
        for contribution_id in work.get("contributionIds") or []:
            contribution = contributions.get(contribution_id, {})
            if not contribution.get("personIds"):
                continue
            search_parts.append(contribution.get("nameAsPrinted"))
            for person_id in contribution.get("personIds") or []:
                person = people.get(person_id, {})
                search_parts.extend((person.get("displayName"), person.get("authorizedName")))
        for person_id in work.get("personIds") or []:
            search_parts.append(people.get(person_id, {}).get("displayName"))
        search_parts.extend((subtype.get("genre"), subtype.get("lyricistAsPrinted")))
        item = {
            "id": work["id"],
            "title": work.get("title"),
            "year": work.get("year"),
            "workType": work.get("workType"),
            "periods": periods(work),
            "searchVariants": joined(variant_parts),
            "searchSupplement": joined(search_parts),
        }
        for key in ("sortTitle", "certainty", "publicScope"):
            if work.get(key):
                item[key] = work[key]
        output.append(item)
    return {"schemaVersion": schema_version, "count": len(output), "records": output}


def person_functions(person: dict, contributions: dict[str, dict]) -> list[str]:
    credited = set()
    for contribution_id in person.get("contributionIds") or []:
        role = contributions.get(contribution_id, {}).get("role")
        for family, roles in FUNCTION_ROLES.items():
            if role in roles:
                credited.add(family)
    if credited:
        return [family for family in FUNCTION_ORDER if family in credited]
    described = set()
    roles = person.get("roles") or ([person.get("primaryRole")] if person.get("primaryRole") else [])
    for role in roles:
        for family, values in FUNCTION_DESCRIPTIONS.items():
            if role in values:
                described.add(family)
    if not described:
        described.add("documented")
    return [family for family in FUNCTION_ORDER if family in described]


def portrait_for(person: dict, sources: dict[str, dict], media: dict[str, dict], root: Path) -> dict | None:
    reachable = []
    for source_id in person.get("sourceIds") or []:
        source = sources.get(source_id, {})
        for media_id in source.get("mediaIds") or []:
            item = media.get(media_id, {})
            asset = item.get("assetPath")
            if item.get("category") == "portrait" and asset and (root / asset).is_file():
                reachable.append((item, source))
    own = next((item for item, _ in reachable if str(item.get("slug") or "").startswith(f"{person.get('slug')}-")), None)
    selected = own or next((item for item, source in reachable if source.get("personIds") == [person["id"]]), None)
    if not selected:
        return None
    return {"assetPath": selected["assetPath"], "altText": selected.get("altText") or person.get("displayName")}


def people_index(root: Path, data_root: Path, schema_version: str) -> dict:
    people = records(data_root, "people.json")
    works = {item["id"]: item for item in records(data_root, "works.json")}
    events = {item["id"]: item for item in records(data_root, "timeline-events.json")}
    sources = {item["id"]: item for item in records(data_root, "sources.json")}
    media = {item["id"]: item for item in records(data_root, "media.json")}
    contributions = {item["id"]: item for item in records(data_root, "contributions.json")}
    variants_by_person: dict[str, list[str]] = {}
    for variant in records(data_root, "person-name-variants.json"):
        for person_id in variant.get("personIds") or []:
            variants_by_person.setdefault(person_id, []).extend(
                value for value in (variant.get("variantName"), variant.get("attestedWording")) if value
            )

    output = []
    for person in people:
        period_set = set()
        for work_id in person.get("workIds") or []:
            period_set.update(periods(works.get(work_id, {})))
        for event_id in person.get("timelineEventIds") or []:
            period_set.update(periods(events.get(event_id, {})))
        person_periods = [period for period in PERIOD_ORDER if period in period_set]
        roles = person.get("roles") or ([person.get("primaryRole")] if person.get("primaryRole") else [])
        functions = person_functions(person, contributions)
        item = {
            "id": person["id"],
            "displayName": person.get("displayName"),
            "roles": roles,
            "functions": functions,
            "periods": person_periods,
            "workCount": len([work_id for work_id in person.get("workIds") or [] if work_id in works]),
            "searchSupplement": joined([
                person.get("sortName"),
                person.get("authorizedName"),
                *(variants_by_person.get(person["id"], [])),
                *roles,
                *(FUNCTION_LABELS[family] for family in functions),
            ]),
        }
        if person.get("sortName"):
            item["sortName"] = person["sortName"]
        portrait = portrait_for(person, sources, media, root)
        if portrait:
            item["portrait"] = portrait
        output.append(item)
    return {"schemaVersion": schema_version, "count": len(output), "records": output}


def sources_index(data_root: Path, schema_version: str) -> dict:
    output = []
    for source in records(data_root, "sources.json"):
        item = {
            "id": source["id"],
            "title": source.get("title") or source.get("shortCitation") or source.get("fullCitation") or source["id"],
            "fullCitation": source.get("fullCitation") or source.get("shortCitation") or "",
            "sourceType": source.get("sourceType"),
            "date": source.get("date"),
            "dateRole": source.get("dateRole"),
            "repository": source.get("repository"),
            "externalUrl": source.get("primaryUrl") or source.get("accessUrl"),
            "searchSupplement": joined([
                source.get("creator"),
                source.get("publication"),
                *[value for identifier in source.get("identifiers") or [] for value in (identifier.get("scheme"), identifier.get("value"))],
            ]),
        }
        for key in ("dateEnd", "dateDisplay", "dateQualifier"):
            if source.get(key):
                item[key] = source[key]
        output.append(item)
    return {"schemaVersion": schema_version, "count": len(output), "records": output}


def media_index(data_root: Path, schema_version: str) -> dict:
    sources = {item["id"]: item for item in records(data_root, "sources.json")}
    output = []
    for media in records(data_root, "media.json"):
        item = {key: media[key] for key in MEDIA_FIELDS if key in media and media[key] not in (None, "", [])}
        item["searchSupplement"] = ""
        source_refs = []
        for source_id in media.get("sourceIds") or []:
            source = sources.get(source_id)
            if not source:
                continue
            ref = {"id": source_id}
            for key in ("primaryUrl", "accessUrl"):
                if source.get(key):
                    ref[key] = source[key]
            source_refs.append(ref)
        if source_refs:
            item["sourceRefs"] = source_refs
        output.append(item)
    return {"schemaVersion": schema_version, "count": len(output), "records": output}


def build_payloads(root: Path) -> dict[str, dict]:
    data_root = root / "data/public/v1"
    schema_version = read_json(data_root / "manifest.json").get("schemaVersion") or "1.0.0"
    return {
        "works": works_index(data_root, schema_version),
        "people": people_index(root, data_root, schema_version),
        "media": media_index(data_root, schema_version),
        "sources": sources_index(data_root, schema_version),
    }


def node_binary() -> str:
    found = shutil.which("node")
    if found:
        return found
    bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
    if bundled.is_file():
        return str(bundled)
    raise RuntimeError("Node.js is required to render catalogue index rows")


def render_pages(root: Path, payloads: dict[str, dict]) -> dict:
    result = subprocess.run(
        [node_binary(), str(root / "scripts/render_catalogue_indexes.mjs"), str(root)],
        input=json.dumps(payloads, ensure_ascii=False, separators=(",", ":")),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def replace_element_text(text: str, element_id: str, value: str) -> str:
    pattern = re.compile(rf'(<[^>]+id="{re.escape(element_id)}"[^>]*>).*?(</[^>]+>)', re.DOTALL)
    if not pattern.search(text):
        raise ValueError(f"Missing text element #{element_id}")
    return pattern.sub(lambda match: f"{match.group(1)}{value}{match.group(2)}", text, count=1)


def inject_prerender(
    text: str,
    target_id: str,
    count_id: str,
    total_id: str | None,
    rendered: dict,
) -> str:
    block = f"{START_MARKER}\n{rendered['markup']}\n{END_MARKER}"
    pattern = re.compile(rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}", re.DOTALL)
    if not pattern.search(text):
        raise ValueError(f"Missing prerender markers for #{target_id}")
    text = pattern.sub(lambda _: block, text, count=1)
    text = replace_element_text(text, count_id, rendered["countText"])
    if total_id:
        noun = ("person", "people") if total_id == "person-total-label" else ("source", "sources")
        total = rendered["total"]
        text = replace_element_text(
            text,
            total_id,
            f"{total} documented {noun[0] if total == 1 else noun[1]}",
        )
    return text


def expected_files(root: Path) -> tuple[dict[Path, bytes], dict[str, dict], dict[str, dict]]:
    payloads = build_payloads(root)
    rendered = render_pages(root, payloads)
    files = {
        root / "data/site/indexes" / INDEX_FILES[name]: compact_json(payload)
        for name, payload in payloads.items()
    }
    for name, (filename, target_id, count_id, total_id) in PAGE_CONFIG.items():
        path = root / filename
        text = inject_prerender(
            path.read_text(encoding="utf-8"), target_id, count_id, total_id, rendered[name]
        )
        files[path] = text.encode("utf-8")
    return files, rendered, payloads


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    expected, rendered, payloads = expected_files(root)
    stale = [path for path, content in expected.items() if not path.is_file() or path.read_bytes() != content]
    if args.check:
        print(json.dumps({"ok": not stale, "stale": [str(path.relative_to(root)) for path in stale]}, indent=2))
        return 1 if stale else 0
    for path, content in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    report = {
        "ok": True,
        "indexes": {
            name: {
                "records": payloads[name]["count"],
                "prerendered": rendered[name]["shown"],
                "bytes": (root / "data/site/indexes" / INDEX_FILES[name]).stat().st_size,
            }
            for name in INDEX_FILES
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
