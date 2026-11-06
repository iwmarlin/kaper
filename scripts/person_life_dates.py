"""Require an explicit, sourced explanation for disputed person life dates."""


def life_date_evidence_errors(person: dict) -> list[str]:
    note = person.get("lifeDatesNote")
    source_ids = person.get("lifeDatesSourceIds", [])
    has_note = isinstance(note, str) and bool(note.strip())
    errors = []
    if person.get("lifeDatesCertainty") == "disputed" and not has_note:
        errors.append("disputed life dates require a public lifeDatesNote")
    if note is not None and not has_note:
        errors.append("lifeDatesNote must be non-empty text")
    if not isinstance(source_ids, list) or not all(
        isinstance(source_id, str) and source_id for source_id in source_ids
    ):
        return errors + ["lifeDatesSourceIds must be an array of source IDs"]
    if has_note and not source_ids:
        errors.append("lifeDatesNote requires lifeDatesSourceIds")
    if source_ids and not has_note:
        errors.append("lifeDatesSourceIds require a public lifeDatesNote")
    if len(source_ids) != len(set(source_ids)):
        errors.append("lifeDatesSourceIds contains duplicates")
    for source_id in source_ids:
        if source_id not in (person.get("sourceIds") or []):
            errors.append(f"life-date evidence {source_id} must also be linked in sourceIds")
    return errors
