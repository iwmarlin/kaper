#!/usr/bin/env python3
"""Normalize access-date prose in public Source citations.

The date on which an online source was consulted belongs in ``accessDate``.
The citation may still identify an access route (for example KVK or
arthistoricum.net), but it must not repeat the date in prose.
"""

from __future__ import annotations

import re
from typing import Any


MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)"
)
ACCESS_DATE = (
    rf"(?:\d{{1,2}}\s+{MONTH}\s+\d{{4}}|"
    rf"{MONTH}\s+\d{{1,2}},\s+\d{{4}}|"
    r"\d{4}-\d{2}-\d{2})"
)

# A dated parenthesis or subordinate clause can occur before the end of a
# citation, so these patterns deliberately do not assume end-of-string.
PARENTHETICAL_ACCESS_DATE_PATTERN = re.compile(
    rf"\s*\(\s*(?:(?:last\s+)?(?:accessed|retrieved|viewed)|consulted)\s+"
    rf"(?:on\s+)?{ACCESS_DATE}\s*\)\.?,?",
    flags=re.IGNORECASE,
)
COMMA_ACCESS_DATE_PATTERN = re.compile(
    rf",\s*(?:(?:last\s+)?(?:accessed|retrieved|viewed)|consulted)\s+"
    rf"(?:on\s+)?{ACCESS_DATE}\.?,?",
    flags=re.IGNORECASE,
)
SENTENCE_ACCESS_DATE_PATTERN = re.compile(
    rf"\s+(?:(?:last\s+)?(?:accessed|retrieved|viewed)|consulted)\s+"
    rf"(?:on\s+)?{ACCESS_DATE}\.?,?",
    flags=re.IGNORECASE,
)
FINDING_AID_ACCESS_DATE_PATTERN = re.compile(
    rf"\s+Finding\s+aid\s+(?:accessed|consulted|retrieved|viewed)\s+"
    rf"(?:on\s+)?{ACCESS_DATE}\.?,?",
    flags=re.IGNORECASE,
)

# The route is evidence about how the described record was reached. Preserve
# it, but replace the event-like wording with a stable bibliographic phrase.
ACCESS_ROUTE_PATTERN = re.compile(
    rf"\b(?:accessed|retrieved|consulted|viewed)\s+(?:through|via)\s+"
    rf"(?P<route>.+?)(?:\s+(?:on\s+)?{ACCESS_DATE})?\."
    rf"(?=\s|$)",
    flags=re.IGNORECASE,
)

REDUNDANT_ACCESS_DATE_PATTERN = re.compile(
    rf"\b(?:(?:last\s+)?(?:accessed|retrieved|viewed)|consulted)\s+"
    rf"(?:on\s+)?{ACCESS_DATE}\b",
    flags=re.IGNORECASE,
)


def has_redundant_access_date(value: Any) -> bool:
    """Return whether prose repeats a date stored in ``accessDate``."""
    text = str(value or "")
    return bool(
        REDUNDANT_ACCESS_DATE_PATTERN.search(text)
        or FINDING_AID_ACCESS_DATE_PATTERN.search(text)
    )


def normalize_access_citation(value: Any) -> str:
    """Remove access dates while retaining any named access intermediary."""
    original = str(value or "")
    text = original.strip()
    if not text:
        return ""
    if not (
        ACCESS_ROUTE_PATTERN.search(text)
        or has_redundant_access_date(text)
    ):
        return original

    def route_replacement(match: re.Match[str]) -> str:
        route = match.group("route").strip(" ,;")
        return f"available via {route}."

    text = ACCESS_ROUTE_PATTERN.sub(route_replacement, text)
    text = FINDING_AID_ACCESS_DATE_PATTERN.sub("", text)
    text = PARENTHETICAL_ACCESS_DATE_PATTERN.sub("", text)
    text = COMMA_ACCESS_DATE_PATTERN.sub("", text)
    text = SENTENCE_ACCESS_DATE_PATTERN.sub("", text)

    # Repair only punctuation made adjacent by the removal above.
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"([.?!]){2,}", r"\1", text)
    text = re.sub(r"\s{2,}", " ", text).strip(" ,;")
    if text and not re.search(r"[.?!][”’\"']?$", text):
        text += "."
    return text
