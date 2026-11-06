from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public/v1"
sys.path.insert(0, str(ROOT / "scripts"))

from source_slugs import canonical_source_slug  # noqa: E402


class SourceSlugTests(unittest.TestCase):
    def test_every_canonical_source_uses_its_id_as_the_slug_prefix(self) -> None:
        records = json.loads(
            (PUBLIC / "sources.json").read_text(encoding="utf-8")
        )["records"]
        offenders = [
            source["id"]
            for source in records
            if source.get("slug") != canonical_source_slug(source)
        ]
        self.assertEqual(offenders, [])

    def test_legacy_trailing_id_is_moved_without_losing_the_description(self) -> None:
        source = {
            "id": "SRC0009",
            "slug": "bronislaw-kaper-papers-early-composition-manuscripts-src0009",
        }
        self.assertEqual(
            canonical_source_slug(source),
            "src0009-bronislaw-kaper-papers-early-composition-manuscripts",
        )

    def test_zero_padded_legacy_prefix_is_not_duplicated(self) -> None:
        source = {"id": "SRC0816", "slug": "src00816-pbm-smidowicz-jozef"}
        self.assertEqual(
            canonical_source_slug(source),
            "src0816-pbm-smidowicz-jozef",
        )


if __name__ == "__main__":
    unittest.main()


class SlugPlatformTests(unittest.TestCase):
    """A slug may name a delivery platform only when the record uses it.

    SRC0212 once carried a ``-bnf`` slug for a record held nowhere near the
    BnF, and SRC0397 named Wikimedia Commons for a file local to English
    Wikipedia.  Both read as provenance to anyone searching the slugs, so the
    token has to be backed by the record's own address or citation.
    """

    PLATFORM_TOKENS = {
        "wikimedia-commons": (("commons.wikimedia.org",), ("wikimedia commons",)),
        "imdb": (("imdb.com", "m.imdb.com", "www.imdb.com"), ("imdb",)),
        "gallica": (("gallica.bnf.fr",), ("gallica",)),
        "picryl": (("picryl.com", "www.picryl.com"), ("picryl",)),
        "youtube": (
            ("youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"),
            ("youtube",),
        ),
        "discogs": (("discogs.com", "www.discogs.com"), ("discogs",)),
        "calisphere": (("calisphere.org", "www.calisphere.org"), ("calisphere",)),
        "archive-org": (("archive.org", "web.archive.org"), ("internet archive",)),
    }

    @staticmethod
    def _unsupported_tokens(source: dict) -> list[str]:
        slug = str(source.get("slug") or "")
        hosts = {urlparse(str(source.get("primaryUrl") or "")).netloc.lower()}
        for link in source.get("additionalLinks") or []:
            hosts.add(urlparse(str(link.get("url") or "")).netloc.lower())
        citation = " ".join(
            str(source.get(field) or "")
            for field in ("repository", "publication", "fullCitation", "shortCitation")
        ).lower()
        unsupported = []
        for token, (allowed_hosts, allowed_words) in (
            SlugPlatformTests.PLATFORM_TOKENS.items()
        ):
            if token not in slug:
                continue
            if hosts & set(allowed_hosts):
                continue
            if any(word in citation for word in allowed_words):
                continue
            unsupported.append(token)
        return unsupported

    def test_no_slug_names_a_platform_the_record_does_not_use(self) -> None:
        records = json.loads(
            (PUBLIC / "sources.json").read_text(encoding="utf-8")
        )["records"]
        offenders = {
            source["id"]: self._unsupported_tokens(source)
            for source in records
            if self._unsupported_tokens(source)
        }
        self.assertEqual(offenders, {})

    def test_the_rule_catches_a_platform_the_record_never_used(self) -> None:
        stale = {
            "id": "SRC0397",
            "slug": "src0397-wikimedia-commons-man-of-the-people-title-lobby-card-1937",
            "repository": "English Wikipedia",
            "primaryUrl": "https://en.wikipedia.org/wiki/File:Man_of_the_People_poster.jpg",
        }
        self.assertEqual(self._unsupported_tokens(stale), ["wikimedia-commons"])
