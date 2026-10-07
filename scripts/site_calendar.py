"""One publication calendar, independent of the build host's timezone.

The archive's editorial dates use Europe/Warsaw, including daylight saving.
GitHub runners normally use UTC; their local date must not determine whether
a publication date is in the future.
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo


PUBLICATION_TIMEZONE = ZoneInfo("Europe/Warsaw")


def publication_today(instant: datetime | None = None) -> date:
    """Return the Warsaw calendar date for an aware instant (or now).

    Reject naive test/input timestamps rather than interpreting them in the
    host timezone and reintroducing the cross-platform ambiguity.
    """
    if instant is None:
        instant = datetime.now(PUBLICATION_TIMEZONE)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("publication instant must be timezone-aware")
    return instant.astimezone(PUBLICATION_TIMEZONE).date()
