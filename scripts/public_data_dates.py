#!/usr/bin/env python3
"""Resolve the publication date of the canonical public dataset."""

from __future__ import annotations

import re
from datetime import date


ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validated_public_data_date(value: str) -> str:
    """Return a strict ISO calendar date or raise ``ValueError``."""
    if not isinstance(value, str) or not ISO_DATE_PATTERN.fullmatch(value):
        raise ValueError("public data date must use YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("public data date must be a valid calendar date") from error
    return parsed.isoformat()


def resolve_public_data_updated_at(
    current_value: str | None,
    *,
    data_changed: bool,
    requested_value: str | None = None,
    today: date | None = None,
) -> str:
    """Resolve the manifest date without coupling it to a source-package date.

    An explicit date always wins. Otherwise a change to a canonical public
    table advances the value to the local build date, while code-only and
    derived-file rebuilds preserve the existing dataset date.
    """
    if requested_value is not None:
        return validated_public_data_date(requested_value)
    if data_changed:
        return (today or date.today()).isoformat()
    if current_value is None:
        raise ValueError("public data date is missing")
    return validated_public_data_date(current_value)
