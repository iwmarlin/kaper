#!/usr/bin/env python3
"""Subset the variable source fonts to the characters this archive actually
uses and write them as woff2.

The site's Content-Security-Policy is default-src 'self', so a font served from
a third-party CDN would be blocked outright — the families named in the
stylesheet before this script existed were never going to load anywhere.
Everything therefore ships from assets/fonts/.

Drop the variable .ttf files into assets/fonts/src/ and run this. Static
weights are deliberately not used: the stylesheet asks for eleven distinct
weights, among them 640, 720, 740 and 750, which only a variable axis can
answer honestly.
"""
from __future__ import annotations
import sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options, parse_unicodes

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "fonts" / "src"
OUT = ROOT / "assets" / "fonts"

# Latin and Latin Extended-A/B carry the Polish, French, German and Czech forms
# in the data — Bronisław, Śmidowicz, Włast, Schünzel, Székely, Ophüls — plus
# the punctuation the citations rely on: en and em dashes, curly quotes, the
# arrow on external links.
# Latin and Latin Extended-A carry every accented form the data actually uses —
# Bronisław, Śmidowicz, Włast, Schünzel, Székely, Ophüls, Garassu — together
# with the punctuation the citations rely on: en and em dashes, curly quotes,
# the ellipsis, and the arrow that marks an external link. Latin Extended-B is
# excluded deliberately; nothing in the archive reaches it, and it is a third
# of the file. The zero-width joiner at U+200D is excluded too: subsetting a
# variable font that still carries it trips a fontTools bug in gvar.
UNICODES = (
    "U+0020-007E,U+00A0-017F,U+2010-2015,U+2018-201E,U+2020-2022,U+2026,"
    "U+2030,U+2039-203A,U+20AC,U+2122,U+2197,U+2212,U+FEFF,U+FFFD"
)

TARGETS = {
    "SourceSerif4": "kaper-serif",
    "Inter": "kaper-sans",
}


def pick(prefix: str) -> Path | None:
    candidates = sorted(
        p for p in SRC.glob("*.ttf")
        if p.stem.replace("-", "").replace("_", "").lower().startswith(prefix.lower())
        and "italic" not in p.stem.lower()
    )
    return candidates[0] if candidates else None


def build(source: Path, stem: str) -> dict:
    font = TTFont(source)
    options = Options()
    options.flavor = "woff2"
    # The default feature set is kept on purpose: it includes ccmp, mark and
    # mkmk, which position the Polish and Czech diacritics. Forcing a hand-
    # picked list drops them and the ogonki drift off their letters.
    options.notdef_outline = True
    options.recalc_bounds = True
    subsetter = Subsetter(options=options)
    subsetter.populate(unicodes=parse_unicodes(UNICODES))
    subsetter.subset(font)
    target = OUT / f"{stem}.woff2"
    font.flavor = "woff2"
    font.save(target)
    axes = {a.axisTag: (a.minValue, a.maxValue) for a in font["fvar"].axes} if "fvar" in font else {}
    return {
        "source": source.name,
        "output": target.name,
        "bytes": target.stat().st_size,
        "sourceBytes": source.stat().st_size,
        "axes": axes,
    }


def main() -> int:
    if not SRC.is_dir():
        print(f"missing {SRC}", file=sys.stderr)
        return 1
    results = []
    for prefix, stem in TARGETS.items():
        source = pick(prefix)
        if not source:
            print(f"no variable .ttf found for {prefix} in {SRC}", file=sys.stderr)
            return 1
        results.append(build(source, stem))
    for item in results:
        print(
            f"{item['source']} -> {item['output']}  "
            f"{item['sourceBytes'] / 1024:.0f} KB -> {item['bytes'] / 1024:.0f} KB  "
            f"axes {item['axes']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
