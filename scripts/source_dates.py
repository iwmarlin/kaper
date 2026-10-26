"""Normalize heterogeneous Source dates into a small, explicit public model.

``date`` is always an ISO-like sortable value (YYYY, YYYY-MM or YYYY-MM-DD).
Ranges use ``dateEnd``.  ``dateRole`` states what the value dates, while
``dateQualifier`` carries uncertainty that previously leaked into ``date`` as
free prose.  ``dateDisplay`` is reserved for the few historical expressions
that cannot be reproduced faithfully from those controlled fields alone.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Mapping


DATE_VALUE_PATTERN = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")

DATE_ROLES = {
    "catalogue_volume",
    "creation",
    "data_currency",
    "described_item",
    "digital_publication",
    "digitization",
    "issue",
    "publication",
    "record_creation",
    "record_update",
    "recording",
}

DATE_QUALIFIERS = {
    "after",
    "approximate",
    "before",
    "confirmed",
    "forthcoming",
    "not_before",
    "reported",
    "uncertain",
    "unknown",
}

SOURCE_IDENTIFIER_SCHEMES = {
    "ark",
    "doi",
    "naid",
    "usco_registration",
    "usco_renewal",
}

CREATION_SOURCE_TYPES = {
    "archival_digital_record",
    "archival_document",
    "archival_manuscript_holding",
    "archival_photograph",
    "digital_collection_item",
    "image_or_photograph",
    "visual_document",
    "wikimedia_commons_file",
}

ISSUE_SOURCE_TYPES = {
    "recording_discographic_source",
    "sheet_music",
    "sound_recording_catalogue",
}

CATALOGUE_SOURCE_TYPES = {
    "copyright_catalogue",
    "sheet_music_catalogue",
}

DESCRIBED_ITEM_SOURCE_TYPES = {
    "authority_record",
    "filmographic_database",
    "online_database",
    "soundtrack_database",
}

PUBLICATION_SOURCE_TYPES = {
    "book",
    "periodical_article",
    "press_item",
    "secondary_literature",
    "web_page",
    "wikimedia_article_page",
}

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

USCO_REGISTRATION_PATTERN = re.compile(
    r"\b(?:E\s+(?:unp\.|pub\.|for\.)\s*\d+|EU\s*\d+)\b",
    flags=re.IGNORECASE,
)
USCO_RENEWAL_PATTERN = re.compile(r"\bR\s*\d+\b", flags=re.IGNORECASE)
HMV_R_SERIES_PATTERN = re.compile(
    r"\b(?:HMV|His Master[’']s Voice)\s+"
    r"(?:[A-Z.]+\s*\d+\s*(?:and|/|,)\s*)*"
    r"(?P<number>R\s*\.?\s*\d+)\b",
    flags=re.IGNORECASE,
)

# Individually reviewed cases where the legacy date was empty although the
# citation itself identifies a different, well-defined chronology.  Keeping
# these explicit avoids accidentally treating life dates, collection spans or
# years embedded in catalogue identifiers as Source dates.
REVIEWED_SOURCE_DATES: dict[str, dict[str, str]] = {
    "SRC0314": {
        "dateRole": "digital_publication",
        "dateQualifier": "confirmed",
        "date": "2019-03-29"
    },
    "SRC0693": {
        "dateRole": "digital_publication",
        "dateQualifier": "confirmed",
        "date": "2013-07-02"
    },
    "SRC0761": {
        "dateRole": "issue",
        "dateQualifier": "unknown"
    },
    "SRC0762": {
        "dateRole": "digital_publication",
        "dateQualifier": "confirmed",
        "date": "2012-06-13"
    },
    "SRC0763": {
        "dateRole": "digital_publication",
        "dateQualifier": "confirmed",
        "date": "2007-12-10"
    },
    "SRC0764": {
        "dateRole": "described_item",
        "dateQualifier": "reported",
        "date": "1933-10-03"
    },
    "SRC0765": {
        "dateRole": "digital_publication",
        "dateQualifier": "confirmed",
        "date": "2018-09-27"
    },
    "SRC0766": {
        "dateRole": "digital_publication",
        "dateQualifier": "confirmed",
        "date": "2016-05-01"
    },
    "SRC0796": {
        "date": "2013-02-05",
        "dateRole": "digital_publication",
        "dateQualifier": "confirmed"
    },
    "SRC0797": {
        "date": "2013-02-05",
        "dateRole": "digital_publication",
        "dateQualifier": "confirmed"
    },
    "SRC0883": {
        "dateRole": "digital_publication",
        "dateQualifier": "confirmed",
        "date": "2011-08-15"
    },
    "SRC0005": {
        "date": "1931-10",
        "dateRole": "issue",
        "dateQualifier": "confirmed"
    },
    "SRC0006": {
        "date": "1935-05-08",
        "dateRole": "issue",
        "dateQualifier": "confirmed"
    },
    "SRC0708": {
        "date": "1931-06",
        "dateRole": "issue",
        "dateQualifier": "confirmed"
    },
    "SRC0743": {
        "date": "1931-01",
        "dateRole": "issue",
        "dateQualifier": "confirmed"
    },
    "SRC0748": {
        "dateRole": "issue",
        "dateQualifier": "unknown"
    },
    "SRC0487": {
        "date": "1933-02-11",
        "dateRole": "recording",
        "dateQualifier": "confirmed"
    },
    "SRC0697": {
        "date": "1933-04",
        "dateRole": "issue",
        "dateQualifier": "confirmed"
    },
    "SRC0699": {
        "date": "1933-04",
        "dateRole": "issue",
        "dateQualifier": "confirmed"
    },
    "SRC0790": {
        "date": "1932",
        "dateRole": "recording",
        "dateQualifier": "reported"
    },
    "SRC0783": {
        "date": "1938",
        "dateRole": "issue",
        "dateQualifier": "confirmed"
    },
    "SRC0784": {
        "date": "1938",
        "dateRole": "issue",
        "dateQualifier": "confirmed"
    },
    "SRC0788": {
        "dateRole": "issue",
        "dateQualifier": "unknown"
    },
    "SRC0694": {
        "date": "1930",
        "dateRole": "recording",
        "dateQualifier": "reported"
    },
    "SRC0695": {
        "date": "1929",
        "dateRole": "recording",
        "dateQualifier": "reported"
    },
    "SRC0716": {
        "date": "1930",
        "dateRole": "recording",
        "dateQualifier": "reported"
    },
    "SRC0717": {
        "date": "1931",
        "dateRole": "recording",
        "dateQualifier": "reported"
    },
    "SRC0004": {
        "date": "1930",
        "dateRole": "recording",
        "dateQualifier": "reported"
    },
    "SRC0725": {
        "dateRole": "issue",
        "dateQualifier": "confirmed",
        "date": "1931-05"
    },
    "SRC0782": {
        "dateRole": "issue",
        "dateQualifier": "unknown"
    },
    "SRC0740": {
        "date": "1937",
        "dateRole": "recording",
        "dateQualifier": "reported"
    },
    "SRC0719": {
        "date": "1932-05",
        "dateRole": "recording",
        "dateQualifier": "reported",
        "dateDisplay": "c. May 1932"
    },
    "SRC0729": {
        "date": "1935-05-06",
        "dateRole": "recording",
        "dateQualifier": "confirmed"
    },
    "SRC0746": {
        "date": "1932",
        "dateRole": "described_item",
        "dateQualifier": "reported"
    },
    "SRC0755": {
        "date": "1932-03",
        "dateRole": "recording",
        "dateQualifier": "reported",
        "dateDisplay": "c. March 1932"
    },
    "SRC0758": {
        "date": "1930",
        "dateRole": "recording",
        "dateQualifier": "reported"
    },
    "SRC0633": {
        "date": "1930",
        "dateRole": "issue",
        "dateQualifier": "after",
        "dateDisplay": "[post 1930]"
    },
    "SRC0773": {
        "dateRole": "issue",
        "dateQualifier": "unknown"
    },
    "SRC0785": {
        "date": "1932-06-11",
        "dateRole": "recording",
        "dateQualifier": "confirmed"
    },
    "SRC0829": {
        "dateRole": "issue",
        "dateQualifier": "unknown"
    },
    "SRC0008": {
        "date": "1937-06-08",
        "dateRole": "recording",
        "dateQualifier": "confirmed"
    },
    "SRC0705": {
        "date": "1934-10",
        "dateRole": "recording",
        "dateQualifier": "confirmed"
    },
    "SRC0744": {
        "date": "1931-03-15",
        "dateRole": "recording",
        "dateQualifier": "confirmed"
    },
    "SRC0750": {
        "date": "1935-03-23",
        "dateRole": "recording",
        "dateQualifier": "confirmed"
    },
    "SRC0753": {
        "date": "1931-09-15",
        "dateRole": "recording",
        "dateQualifier": "confirmed"
    },
    "SRC0760": {
        "date": "1931-04-29",
        "dateRole": "recording",
        "dateQualifier": "confirmed"
    },
    "SRC0767": {
        "date": "1930-03",
        "dateRole": "recording",
        "dateQualifier": "confirmed"
    },
    "SRC0115": {
        "date": "1933-11-07",
        "dateRole": "recording",
        "dateQualifier": "confirmed"
    },
    "SRC0707": {
        "date": "1929",
        "dateRole": "described_item",
        "dateQualifier": "reported",
    },
    "SRC0730": {
        "date": "1933",
        "dateRole": "issue",
        "dateQualifier": "reported",
    },
    "SRC0735": {
        "date": "1933",
        "dateRole": "recording",
        "dateQualifier": "reported",
    },
    "SRC0738": {
        "date": "1926",
        "dateRole": "recording",
        "dateQualifier": "reported",
    },
    "SRC0759": {
        "date": "1937",
        "dateRole": "described_item",
        "dateQualifier": "reported",
    },
    "SRC0731": {
        "date": "1932",
        "dateRole": "recording",
        "dateQualifier": "reported",
    },
    "SRC0754": {
        "date": "1932",
        "dateRole": "issue",
        "dateQualifier": "uncertain",
    },
    "SRC0800": {
        "date": "1934",
        "dateRole": "described_item",
        "dateQualifier": "reported",
    },
    "SRC0801": {
        "dateRole": "issue",
        "dateQualifier": "unknown",
    },
    "SRC0803": {
        "date": "1934",
        "dateRole": "described_item",
        "dateQualifier": "reported",
    },
    "SRC0804": {
        "date": "1934",
        "dateRole": "described_item",
        "dateQualifier": "reported",
    },
    "SRC0805": {
        "date": "1934",
        "dateRole": "issue",
        "dateQualifier": "confirmed",
        "dateDisplay": "[1934]",
    },
    "SRC0806": {
        "date": "1934",
        "dateRole": "described_item",
        "dateQualifier": "reported",
    },
    # Reviewed issue, session and reference-publication dates.
    "SRC0710": {
        "date": "1931",
        "dateRole": "issue",
        "dateQualifier": "reported"
    },
    "SRC0712": {
        "date": "1932",
        "dateRole": "recording",
        "dateQualifier": "confirmed"
    },
    "SRC0718": {
        "date": "1931-03-11",
        "dateRole": "recording",
        "dateQualifier": "confirmed"
    },
    "SRC0724": {
        "date": "1930-10",
        "dateRole": "described_item",
        "dateQualifier": "uncertain"
    },
    "SRC0792": {
        "date": "1998",
        "dateRole": "publication",
        "dateQualifier": "confirmed",
    },
    "SRC0807": {
        "date": "1932-08-15",
        "dateRole": "recording",
        "dateQualifier": "confirmed",
    },
    "SRC0535": {
        "date": "1935",
        "dateRole": "issue",
        "dateQualifier": "confirmed"
    },
    "SRC0542": {
        "date": "1937",
        "dateRole": "issue",
        "dateQualifier": "confirmed"
    },
    "SRC0574": {
        "dateRole": "creation",
        "dateQualifier": "unknown",
        "dateDisplay": "20th century (museum dating)"
    },
    "SRC0452": {
        "date": "1932",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
        "dateDisplay": "1932 (production)"
    },
    "SRC0478": {
        "date": "1931",
        "dateEnd": "1932",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
        "dateDisplay": "1931/1932 (film)"
    },
    "SRC0479": {
        "date": "1930",
        "dateRole": "described_item",
        "dateQualifier": "confirmed"
    },
    "SRC0480": {
        "date": "1937",
        "dateRole": "described_item",
        "dateQualifier": "confirmed"
    },
    "SRC0481": {
        "date": "1937",
        "dateRole": "described_item",
        "dateQualifier": "confirmed"
    },
    "SRC0482": {
        "date": "1938",
        "dateRole": "described_item",
        "dateQualifier": "confirmed"
    },
    "SRC0684": {
        "date": "2003-04-25",
        "dateRole": "record_update",
        "dateQualifier": "confirmed",
        "dateDisplay": "25 April 2003 (content update)",
    },
    "SRC0417": {
        "date": "1933",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
        "dateDisplay": "1933 (film)"
    },
    "SRC0432": {
        "date": "1920",
        "dateRole": "publication",
        "dateQualifier": "confirmed",
        "dateDisplay": "[1920]"
    },
    "SRC0443": {
        "date": "1935",
        "dateRole": "issue",
        "dateQualifier": "confirmed"
    },
    "SRC0538": {
        "date": "1933",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
        "dateDisplay": "1933 (film)"
    },
    "SRC0539": {
        "date": "1933",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
        "dateDisplay": "1933 (film)"
    },
    "SRC0540": {
        "date": "1934",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
        "dateDisplay": "1934 (film)"
    },
    "SRC0541": {
        "date": "1933",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
        "dateDisplay": "1933 (film)"
    },
    "SRC0579": {
        "date": "1928",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
        "dateDisplay": "1928 (aerial imagery)"
    },
    "SRC0477": {
        "date": "1927-04-01",
        "dateRole": "data_currency",
        "dateQualifier": "confirmed",
        "dateDisplay": "1 April 1927 (membership list)"
    },
    "SRC0863": {
        "date": "1931",
        "dateRole": "publication",
        "dateQualifier": "confirmed"
    },
    "SRC0174": {
        "date": "1937",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
    },
    "SRC0212": {
        "date": "1932",
        "dateRole": "catalogue_volume",
        "dateQualifier": "confirmed",
    },
    "SRC0299": {
        "date": "1933",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
    },
    "SRC0302": {
        "date": "1934",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
    },
    "SRC0307": {
        "date": "1936",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
    },
    "SRC0330": {
        "date": "1920",
        "dateEnd": "1932",
        "dateRole": "creation",
        "dateQualifier": "confirmed",
    },
    "SRC0332": {
        "date": "1938",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
    },
    "SRC0393": {
        "date": "1935",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
    },
    "SRC0395": {
        "date": "1936",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
    },
    "SRC0397": {
        "date": "1937",
        "dateRole": "creation",
        "dateQualifier": "confirmed",
    },
    "SRC0428": {
        "date": "1933",
        "dateRole": "creation",
        "dateQualifier": "confirmed",
    },
    "SRC0429": {
        "date": "1935",
        "dateRole": "creation",
        "dateQualifier": "confirmed",
    },
    "SRC0448": {
        "date": "1933",
        "dateRole": "publication",
        "dateQualifier": "confirmed",
    },
    "SRC0467": {
        "date": "1930",
        "dateRole": "catalogue_volume",
        "dateQualifier": "confirmed",
    },
    "SRC0533": {
        "date": "1933",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
    },
    "SRC0534": {
        "date": "1937",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
    },
    "SRC0597": {
        "date": "1930",
        "dateRole": "creation",
        "dateQualifier": "approximate",
    },
    "SRC0640": {
        "date": "2014-01-13",
        "dateRole": "digital_publication",
        "dateQualifier": "confirmed",
    },
    "SRC0714": {
        "date": "2000",
        "dateRole": "issue",
        "dateQualifier": "confirmed",
    },
    "SRC0808": {
        "date": "2008-07-10",
        "dateRole": "digital_publication",
        "dateQualifier": "confirmed"
    },
    "SRC0809": {
        "date": "1938",
        "dateRole": "described_item",
        "dateQualifier": "confirmed",
    },
    "SRC0811": {
        "date": "1937",
        "dateRole": "described_item",
        "dateQualifier": "uncertain"
    },
    "SRC0837": {
        "date": "1930",
        "dateEnd": "1939",
        "dateRole": "creation",
        "dateQualifier": "approximate",
        "dateDisplay": "1930s",
    },
}


def valid_date_value(value: Any) -> bool:
    """Return true for a real YYYY, YYYY-MM or YYYY-MM-DD value."""

    text = str(value or "").strip()
    if not DATE_VALUE_PATTERN.fullmatch(text):
        return False
    try:
        if len(text) == 4:
            datetime.strptime(text, "%Y")
        elif len(text) == 7:
            datetime.strptime(text, "%Y-%m")
        else:
            datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def date_sort_key(value: str) -> tuple[int, int, int]:
    """Return a comparable lower-bound key for a validated date value."""

    if not valid_date_value(value):
        raise ValueError(f"Invalid controlled date value: {value!r}")
    parts = [int(part) for part in value.split("-")]
    return (parts[0], parts[1] if len(parts) > 1 else 1, parts[2] if len(parts) > 2 else 1)


def source_date_errors(source: Mapping[str, Any]) -> list[str]:
    """Return model violations for one normalized Source record."""

    errors: list[str] = []
    role = source.get("dateRole")
    qualifier = source.get("dateQualifier")
    date = source.get("date")
    date_end = source.get("dateEnd")
    display = source.get("dateDisplay")

    if role not in DATE_ROLES:
        errors.append(f"dateRole must be one of {sorted(DATE_ROLES)}")
    if qualifier not in DATE_QUALIFIERS:
        errors.append(f"dateQualifier must be one of {sorted(DATE_QUALIFIERS)}")

    if date not in (None, "") and not valid_date_value(date):
        errors.append("date must be YYYY, YYYY-MM or YYYY-MM-DD")
    if date_end not in (None, "") and not valid_date_value(date_end):
        errors.append("dateEnd must be YYYY, YYYY-MM or YYYY-MM-DD")
    if date_end not in (None, "") and date in (None, ""):
        errors.append("dateEnd requires date")
    if valid_date_value(date) and valid_date_value(date_end):
        if date_sort_key(str(date_end)) < date_sort_key(str(date)):
            errors.append("dateEnd precedes date")

    if qualifier == "unknown" and (date not in (None, "") or date_end not in (None, "")):
        errors.append("unknown dates must not carry date or dateEnd")
    if qualifier not in {"unknown", "forthcoming", None, ""} and date in (None, ""):
        errors.append(f"dateQualifier {qualifier!r} requires date")
    if display is not None and (not isinstance(display, str) or not display.strip()):
        errors.append("dateDisplay must be a non-empty string when supplied")

    title = str(source.get("title") or "")
    if (
        source.get("sourceType") == "copyright_catalogue"
        and re.search(r"\bCatalogue? of Copyright Entries\b", title, re.IGNORECASE)
    ):
        if role != "catalogue_volume":
            errors.append(
                "Catalog of Copyright Entries records must date the catalogue volume"
            )
        if date not in (None, "") and len(str(date)) != 4:
            errors.append(
                "Catalog of Copyright Entries volume dates must be a year"
            )
        citation_year = re.search(
            r"^CCE\s+(\d{4})\b",
            str(source.get("shortCitation") or ""),
            re.IGNORECASE,
        )
        if citation_year and str(date or "") != citation_year.group(1):
            errors.append(
                "Catalog of Copyright Entries date must match the cited volume year"
            )
    return errors


def _english_date(value: str) -> str | None:
    cleaned = " ".join(value.replace(",", " ").split())
    for pattern in ("%d %B %Y", "%B %d %Y", "%B %Y"):
        try:
            parsed = datetime.strptime(cleaned, pattern)
        except ValueError:
            continue
        return parsed.strftime("%Y-%m-%d" if "%d" in pattern else "%Y-%m")
    return None


def _explicit_digital_date(source: Mapping[str, Any]) -> tuple[str, str] | None:
    source_type = str(source.get("sourceType") or "")
    if source_type not in {"online_audio_source", "online_video_source"}:
        return None
    citation = str(source.get("fullCitation") or "")
    for match in re.finditer(
        r"\b(?:uploaded|published|released|digital release)\s+"
        r"(?:on\s+)?(\d{1,2}\s+[A-Z][a-z]+\s+\d{4}|"
        r"[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2})",
        citation,
    ):
        raw = match.group(1)
        normalized = raw if valid_date_value(raw) else _english_date(raw)
        if normalized:
            return normalized, "digital_publication"
    # Upload citations often place the account name between the publication
    # verb and the date: "published by X on 24 June 2011".  This is the date of
    # the online surrogate, not the historical recording named in the legacy
    # date field.
    for match in re.finditer(
        r"\b(?:uploaded|published|released)\s+by\b.{0,160}?\bon\s+"
        r"(\d{1,2}\s+[A-Z][a-z]+\s+\d{4}|"
        r"[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2})",
        citation,
        re.IGNORECASE,
    ):
        raw = match.group(1)
        normalized = raw if valid_date_value(raw) else _english_date(raw)
        if normalized:
            return normalized, "digital_publication"
    digitized = re.search(r"\bdigitized in (\d{4})\b", citation, re.IGNORECASE)
    if digitized:
        return digitized.group(1), "digitization"
    return None


def _explicit_record_metadata_date(
    source: Mapping[str, Any],
) -> tuple[str, str] | None:
    citation = str(source.get("fullCitation") or "")
    patterns = (
        (
            r"\b(?:record|page)\s+(?:last\s+)?modified\s+"
            r"(\d{1,2}\s+[A-Z][a-z]+\s+\d{4}|\d{4}-\d{2}-\d{2})",
            "record_update",
        ),
        (
            r"\blast modified\s+"
            r"(\d{1,2}\s+[A-Z][a-z]+\s+\d{4}|\d{4}-\d{2}-\d{2})",
            "record_update",
        ),
        (
            r"\bdata (?:were|was) current as of\s+"
            r"(\d{1,2}\s+[A-Z][a-z]+\s+\d{4}|\d{4}-\d{2}-\d{2})",
            "data_currency",
        ),
        (
            r"\bCreated\s+(\d{4}-\d{2}-\d{2})\b",
            "record_creation",
        ),
    )
    for pattern, role in patterns:
        match = re.search(pattern, citation, re.IGNORECASE)
        if not match:
            continue
        raw = match.group(1)
        normalized = raw if valid_date_value(raw) else _english_date(raw)
        if normalized:
            return normalized, role
    return None


def _access_year_placeholder(source: Mapping[str, Any], raw: str) -> bool:
    """Detect a year copied from accessDate rather than dating the source."""

    if not re.fullmatch(r"20\d{2}", raw):
        return False
    access_date = str(source.get("accessDate") or "")
    if not access_date.startswith(raw):
        return False
    citation = str(source.get("fullCitation") or "")
    without_access = re.sub(
        r"\bAccessed\s+\d{1,2}\s+[A-Z][a-z]+\s+20\d{2}\.?",
        "",
        citation,
        flags=re.IGNORECASE,
    )
    return not re.search(rf"\b{re.escape(raw)}\b", without_access)


def infer_date_role(source: Mapping[str, Any], normalized_date: str | None) -> str:
    source_type = str(source.get("sourceType") or "")
    citation = " ".join(
        str(source.get(key) or "")
        for key in ("fullCitation", "shortCitation", "repository", "publication")
    ).casefold()

    if source_type == "copyright_catalogue" and re.search(
        r"\b(?:sacem|gema|akm)\b|\baustro mechana\b|"
        r"\bfilmtitelliste\b|\bremakerechte\b",
        citation,
    ):
        return "described_item"
    if source_type in CATALOGUE_SOURCE_TYPES:
        return "catalogue_volume"
    if source_type in CREATION_SOURCE_TYPES:
        return "creation"
    if source_type == "sound_recording_catalogue" and "labelliste" in citation:
        return "described_item"
    if source_type in ISSUE_SOURCE_TYPES:
        return "issue"
    if source_type in DESCRIBED_ITEM_SOURCE_TYPES:
        if normalized_date and int(normalized_date[:4]) >= 1950:
            return "publication"
        return "described_item"
    if source_type in PUBLICATION_SOURCE_TYPES:
        return "publication"
    if source_type == "online_audio_source":
        if normalized_date and int(normalized_date[:4]) < 1950:
            return "recording"
        return "digital_publication"
    if source_type == "online_video_source":
        if "digitized" in citation:
            return "digitization"
        if normalized_date and int(normalized_date[:4]) < 1950:
            return "described_item"
        return "digital_publication"
    return "publication"


def _reported_online_date(source: Mapping[str, Any], normalized_date: str | None) -> bool:
    if not normalized_date or int(normalized_date[:4]) >= 1950:
        return False
    if str(source.get("sourceType") or "") not in {
        "online_audio_source",
        "online_video_source",
    }:
        return False
    text = " ".join(
        str(source.get(key) or "")
        for key in ("date", "fullCitation", "researchNote")
    ).casefold()
    return bool(
        re.search(
            r"(?:according to the uploader|uploader-(?:level|supplied)|"
            r"uploader (?:dates|gives|identifies|places))",
            text,
        )
    )


def _result(
    source: Mapping[str, Any],
    *,
    date: str | None = None,
    date_end: str | None = None,
    role: str | None = None,
    qualifier: str = "confirmed",
    display: str | None = None,
) -> dict[str, str]:
    normalized_role = role or infer_date_role(source, date)
    result = {"dateRole": normalized_role, "dateQualifier": qualifier}
    if date:
        result["date"] = date
    if date_end:
        result["dateEnd"] = date_end
    if display:
        result["dateDisplay"] = display
    return result


def normalized_source_date_fields(source: Mapping[str, Any]) -> dict[str, str]:
    """Project a legacy Source date into controlled, lossless fields."""

    raw = " ".join(str(source.get("date") or "").strip().split())

    reviewed = REVIEWED_SOURCE_DATES.get(str(source.get("id") or ""))
    if reviewed:
        return dict(reviewed)

    record_metadata = _explicit_record_metadata_date(source)
    if record_metadata:
        date, role = record_metadata
        return _result(source, date=date, role=role)

    digital = _explicit_digital_date(source)
    if digital:
        date, role = digital
        return _result(source, date=date, role=role)

    if _access_year_placeholder(source, raw):
        return _result(source, role=infer_date_role(source, None), qualifier="unknown")

    source_type = str(source.get("sourceType") or "")
    citation = str(source.get("fullCitation") or "")
    if (
        valid_date_value(raw)
        and len(raw) > 4
        and int(raw[:4]) >= 1950
        and (
            source_type == "authority_record"
            or "authority record" in citation.casefold()
        )
    ):
        return _result(source, date=raw, role="record_creation")

    if (
        source.get("dateRole") == "described_item"
        and valid_date_value(raw)
        and int(raw[:4]) >= 1950
        and source_type in {"filmographic_database", "online_database"}
    ):
        return _result(source, date=raw, role="publication")

    if (
        source_type == "sound_recording_catalogue"
        and valid_date_value(raw)
        and re.search(r"\brecorded\b.*?\bon\b", str(source.get("fullCitation") or ""), re.IGNORECASE)
    ):
        return _result(source, date=raw, role="recording")

    # Early migrations marked every dated YouTube excerpt as "reported".  A
    # film year used as the date of the described item is not thereby an
    # uploader claim; retain "reported" only where the record explicitly says
    # that the uploader supplied the chronology.
    if (
        source.get("dateQualifier") == "reported"
        and source.get("dateRole") == "described_item"
        and not _reported_online_date(source, raw)
    ):
        corrected = dict(source)
        corrected["dateQualifier"] = "confirmed"
        return {
            key: str(corrected[key])
            for key in ("date", "dateEnd", "dateRole", "dateQualifier", "dateDisplay")
            if corrected.get(key) not in (None, "")
        }

    # Already-normalized records remain idempotent on subsequent exports.
    if (
        source.get("dateRole") in DATE_ROLES
        and source.get("dateQualifier") in DATE_QUALIFIERS
        and (not raw or valid_date_value(raw))
        and (not source.get("dateEnd") or valid_date_value(source.get("dateEnd")))
    ):
        return {
            key: str(source[key])
            for key in ("date", "dateEnd", "dateRole", "dateQualifier", "dateDisplay")
            if source.get(key) not in (None, "")
        }

    source_type = str(source.get("sourceType") or "")
    if source_type == "copyright_catalogue" and raw and raw != "n.d.":
        if source.get("id") == "SRC0305":
            return _result(source, date="1964", role="catalogue_volume")
        leading_year = re.match(r"^(\d{4})", raw)
        if leading_year:
            return _result(
                source,
                date=leading_year.group(1),
                role=infer_date_role(source, leading_year.group(1)),
            )

    uploader_year = re.search(
        r"(?:given as|released in|issued(?: in Austria)?(?: about)?|"
        r"recorded in Berlin in|recording of)\s+(\d{4})\s+"
        r"(?:by|according to) the uploader",
        raw,
        re.IGNORECASE,
    )
    if uploader_year:
        return _result(
            source,
            date=uploader_year.group(1),
            role="recording",
            qualifier="reported",
        )

    # A few legacy values state only that a year comes from the uploader, or
    # insert label wording between "issued" and that year.  This fallback is
    # deliberately confined to the date field and runs after explicit digital
    # publication dates have been extracted from the citation.
    uploader_year = re.search(
        r"(?:^|\[).*?\b(19\d{2}|20\d{2})\b.*?according to the uploader",
        raw,
        re.IGNORECASE,
    )
    if uploader_year:
        return _result(
            source,
            date=uploader_year.group(1),
            role="recording",
            qualifier="reported",
        )

    if re.fullmatch(r"n\.d\.\s*\[not before \d{4}\]", raw, re.IGNORECASE):
        year = re.search(r"\d{4}", raw).group(0)
        return _result(
            source,
            date=year,
            role="issue",
            qualifier="not_before",
        )

    reissue = re.fullmatch(
        r"(\d{4})(?:\s+or\s+|[–-])(\d{4})\s*\[reissued \d{4}\]",
        raw,
        re.IGNORECASE,
    )
    if reissue:
        start, end = reissue.groups()
        qualifier = "uncertain" if " or " in raw else "confirmed"
        display = f"{start} or {end}" if qualifier == "uncertain" else None
        return _result(
            source,
            date=start,
            date_end=end,
            role="recording",
            qualifier=qualifier,
            display=display,
        )

    if not raw or raw.casefold() in {"n.d.", "undated"}:
        return _result(source, qualifier="unknown")

    if raw.casefold() == "forthcoming":
        return _result(
            source,
            role="publication",
            qualifier="forthcoming",
            display="forthcoming",
        )
    forthcoming = re.fullmatch(r"(\d{4})\s*/\s* forthcoming", raw, re.IGNORECASE)
    if forthcoming:
        year = forthcoming.group(1)
        return _result(
            source,
            date=year,
            role="publication",
            qualifier="forthcoming",
            display=f"{year} (forthcoming)",
        )

    approximate_range = re.fullmatch(
        r"(?:c\.|ca\.|circa)\s*(\d{4})[–-](\d{4})", raw, re.IGNORECASE
    )
    if approximate_range:
        start, end = approximate_range.groups()
        return _result(
            source,
            date=start,
            date_end=end,
            qualifier="approximate",
        )
    approximate = re.fullmatch(
        r"(?:c\.|ca\.|circa)\s*(\d{4})", raw, re.IGNORECASE
    )
    if approximate:
        return _result(
            source,
            date=approximate.group(1),
            qualifier="approximate",
        )

    bracketed = re.fullmatch(r"\[(\d{4})(?:\?)?\]", raw)
    if bracketed:
        year = bracketed.group(1)
        return _result(
            source,
            date=year,
            qualifier="uncertain",
            display=f"[{year}]",
        )

    bounded = re.fullmatch(r"(before|after)\s+(\d{4})", raw, re.IGNORECASE)
    if bounded:
        relation, year = bounded.groups()
        return _result(
            source,
            date=year,
            qualifier=relation.casefold(),
        )

    if raw.casefold() == "early 20th century":
        return _result(
            source,
            date="1900",
            date_end="1933",
            qualifier="approximate",
            display="early 20th century",
        )

    decade = re.fullmatch(r"(\d{3})0s", raw)
    if decade:
        start = f"{decade.group(1)}0"
        end = f"{decade.group(1)}9"
        return _result(
            source,
            date=start,
            date_end=end,
            qualifier="approximate",
            display=raw,
        )

    if source.get("id") == "SRC0570":
        return _result(
            source,
            date="1938",
            date_end="1948",
            qualifier="uncertain",
            display="[1938?]; between 1938 and 1948",
        )

    month_range = re.fullmatch(
        r"(\d{1,2})\s+([A-Z][a-z]+)[–-](\d{1,2})\s+([A-Z][a-z]+)\s+(\d{4})",
        raw,
    )
    if month_range:
        day1, month1, day2, month2, year = month_range.groups()
        start = _english_date(f"{day1} {month1} {year}")
        end = _english_date(f"{day2} {month2} {year}")
        if start and end:
            return _result(source, date=start, date_end=end)

    parsed_words = _english_date(raw)
    if parsed_words:
        return _result(source, date=parsed_words)

    uncertain_pair = re.fullmatch(r"(\d{4})\s+or\s+(\d{4})", raw)
    if uncertain_pair:
        start, end = uncertain_pair.groups()
        return _result(
            source,
            date=start,
            date_end=end,
            qualifier="uncertain",
            display=raw,
        )

    year_range = re.fullmatch(r"(\d{4})[–-](\d{4})", raw)
    if year_range:
        start, end = year_range.groups()
        return _result(source, date=start, date_end=end)

    if valid_date_value(raw):
        qualifier = "reported" if _reported_online_date(source, raw) else "confirmed"
        return _result(source, date=raw, qualifier=qualifier)

    raise ValueError(f"{source.get('id', 'unknown')}: unsupported Source date {raw!r}")


def record_label_series_numbers(source: Mapping[str, Any]) -> set[str]:
    """Recognize explicit HMV R-series references, not copyright renewals."""
    text = str(source.get("fullCitation") or "")
    return {
        re.sub(r"[\s.]", "", match.group("number")).casefold()
        for match in HMV_R_SERIES_PATTERN.finditer(text)
    }


def usco_identifiers(source: Mapping[str, Any]) -> list[dict[str, str]]:
    """Extract U.S. copyright registration and renewal identifiers."""

    text = " ".join(
        str(source.get(key) or "") for key in ("fullCitation", "date")
    )
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    label_numbers = record_label_series_numbers(source)
    for scheme, pattern in (
        ("usco_registration", USCO_REGISTRATION_PATTERN),
        ("usco_renewal", USCO_RENEWAL_PATTERN),
    ):
        for match in pattern.finditer(text):
            value = " ".join(match.group(0).split())
            if (
                scheme == "usco_renewal"
                and re.sub(r"[\s.]", "", value).casefold() in label_numbers
            ):
                continue
            key = (scheme, value.casefold())
            if key not in seen:
                seen.add(key)
                result.append({"scheme": scheme, "value": value})
    return result
