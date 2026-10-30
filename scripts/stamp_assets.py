#!/usr/bin/env python3
"""Stamp a single content-derived cache-busting version on every asset reference.

Why: the site pins CSS/JS with `?v=…` query strings scattered across the HTML
pages, the JS module imports, and the record-page generator. Bumping them by
hand drifts — some pages end up on an old version and serve stale CSS/JS (or a
stale image-derivatives map) to returning visitors.

What this does: computes ONE build id from the *version-stripped* contents of
every CSS/JS file in assets/site (so the id changes only on real content
changes, not on its own stamps — the script is idempotent), then rewrites every
`?v=…` on those assets across:
  - the HTML pages (assets/site/*.css|js references),
  - the JS module imports (./*.js references, incl. core.js + image-derivatives.js),
  - the record-page generator's style_version / record_script_version literals.

Run this after ANY change to assets/site/*.css or *.js, then regenerate the
record pages so they carry the new version:

    python3 scripts/stamp_assets.py
    python3 scripts/build_static_records.py
    python3 scripts/validate_site.py
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "assets" / "site"

REF_RE = re.compile(r'((?:assets/site/|\./)[A-Za-z0-9._/-]+\.(?:css|js))\?v=[A-Za-z0-9._-]+')
STRIP_RE = re.compile(r'\?v=[A-Za-z0-9._-]+')
# The font files are referenced from inside the stylesheet, and they were the
# one asset this script did not stamp. The stylesheet's own URL changes on
# every build, so a reader always received the new CSS — pointing at a font
# URL that had not changed since the first visit. A returning reader therefore
# kept the font that was cached the first time, and no change of typeface
# could ever reach them. The reference is rewritten whether or not it already
# carries a version, since these had none to begin with.
FONT_RE = re.compile(
    r'((?:\.\./fonts/|assets/fonts/)[A-Za-z0-9._-]+\.woff2)(?:\?v=[A-Za-z0-9._-]+)?'
)
FONTS = ROOT / "assets" / "fonts"


def build_id() -> str:
    parts = []
    for path in sorted(SITE.glob("*.css")) + sorted(SITE.glob("*.js")):
        normalized = STRIP_RE.sub("?v=", path.read_text(encoding="utf-8"))
        parts.append(path.name + "\0" + normalized)
    # The fonts are part of the build: changing a typeface without changing a
    # line of CSS must still produce a new id, or the stamp it is written into
    # would not move and the old file would stay cached.
    for path in sorted(FONTS.glob("*.woff2")):
        parts.append(path.name + "\0" + hashlib.sha256(path.read_bytes()).hexdigest())
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:10]


def stamp_text(text: str, version: str) -> str:
    text = REF_RE.sub(rf"\1?v={version}", text)
    return FONT_RE.sub(rf"\1?v={version}", text)


def main() -> int:
    version = build_id()
    changed: list[str] = []

    for html in sorted(ROOT.glob("*.html")):
        text = html.read_text(encoding="utf-8")
        new = stamp_text(text, version)
        if new != text:
            html.write_text(new, encoding="utf-8")
            changed.append(html.name)

    for js in sorted(SITE.glob("*.js")):
        text = js.read_text(encoding="utf-8")
        new = stamp_text(text, version)
        if new != text:
            js.write_text(new, encoding="utf-8")
            changed.append(f"assets/site/{js.name}")

    # The stylesheets were never rewritten, because until the fonts were
    # stamped they held no reference that needed it.
    for css in sorted(SITE.glob("*.css")):
        text = css.read_text(encoding="utf-8")
        new = stamp_text(text, version)
        if new != text:
            css.write_text(new, encoding="utf-8")
            changed.append(f"assets/site/{css.name}")

    gen = ROOT / "scripts" / "build_static_records.py"
    text = gen.read_text(encoding="utf-8")
    new = stamp_text(text, version)
    new = re.sub(r'(style_version = ")[^"]*(")', rf"\g<1>{version}\g<2>", new)
    new = re.sub(r'(record_script_version = ")[^"]*(")', rf"\g<1>{version}\g<2>", new)
    if new != text:
        gen.write_text(new, encoding="utf-8")
        changed.append("scripts/build_static_records.py")

    print(f"build id: {version}")
    print(f"stamped {len(changed)} file(s)")
    if changed:
        print("Next: python3 scripts/build_static_records.py  (so record pages carry the new version)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
