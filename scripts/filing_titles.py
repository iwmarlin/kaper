#!/usr/bin/env python3
"""The filing form of a Work title.

``sortTitle`` is the form the catalogue files under, and the only thing it
does is move a title past its leading article: “Die lustigen Musikanten”
files under L, “The Magic of Maytime” under M.  Everything else — accents,
apostrophes, punctuation, parentheses, capitalisation — stays exactly as the
title prints it, because the index sorts with a locale collator and the field
is read as text, not as a machine key.
"""

from __future__ import annotations

import re


# The articles the catalogue files past.  A word is only skipped here when it
# is an article: “À Paris tiguidiguidi” files under À, not under Paris.
ARTICLES = (
    "The", "A", "An",
    "Der", "Die", "Das", "Ein", "Eine", "Einen",
    "Le", "La", "Les", "L’", "Un", "Une",
)

_LEADING_ARTICLE = re.compile(
    r"^(?:" + "|".join(re.escape(article) for article in ARTICLES) + r")(?:\s+|(?<=’))"
)


def filing_title(title: str | None) -> str:
    """Return ``title`` without its leading article."""

    return _LEADING_ARTICLE.sub("", str(title or ""), count=1).strip()
