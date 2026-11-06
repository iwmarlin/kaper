# Fonts

Two variable typefaces, both served from this origin. They have to be: the
site's Content-Security-Policy is `default-src 'self'`, so a font requested
from a third-party CDN is refused before it is fetched.

| File | Family | Axes | Size |
|---|---|---|---|
| `kaper-serif.woff2` | Fraunces | `wght` 100–900, `opsz` 9–144 | 78 KB |
| `kaper-serif-italic.woff2` | Fraunces Italic | `wght` 100–900, `opsz` 9–144 | 93 KB |
| `kaper-sans.woff2` | Archivo | `wght` 100–900 | 38 KB |
| `kaper-sans-italic.woff2` | Archivo Italic | `wght` 100–900 | 42 KB |

Fraunces sets the headings, the lead paragraphs and the display numerals.
Archivo sets everything that is read closely — every citation, every credit
line, every field label. That is the larger job, and the sans was chosen on
measurement rather than on character: against Inter it is 5.8% narrower and
has the highest ratio of x-height to cap height of the faces tried, so the
small labels hold up better.

Both are subsets of the variable sources in `src/`, cut to Latin and Latin
Extended-A plus the punctuation the citations use. Latin Extended-B is left
out on purpose: nothing in the archive reaches it and it is a third of the
file. Regenerate with `python3 scripts/build_fonts.py`.

Fraunces ships two axes beyond weight and optical size — `SOFT` and `WONK` —
and arrives with `WONK` switched on and weight at 900. Both are pinned at
zero before subsetting, so the swashed display forms cannot appear by
accident and the file is smaller for their absence. Archivo's `wdth` axis is
pinned at 100 for the same reason.

The italics are built although the archive barely uses them: the generated
pages contain no `<em>` at all, because citations distinguish titles with
quotation marks rather than with slope. They are here so that a later move to
italic journal titles — which is what CMOS asks for — does not fall back on a
browser's synthetic slant.

Variable rather than static because the stylesheet asks for eleven distinct
weights — 400, 500, 600, 640, 650, 680, 700, 720, 740, 750, 760. Against
static faces those collapse to the nearest of 400 and 700.

## Licence

Both families are released under the SIL Open Font License 1.1, which permits
redistribution, embedding and modification, including subsetting, provided the
licence travels with the files.

- Fraunces — Copyright 2020 The Fraunces Project Authors.
  https://github.com/undercasetype/Fraunces
- Archivo — Copyright 2020 The Archivo Project Authors.
  https://github.com/Omnibus-Type/Archivo

The full licence text as distributed with each family is in `OFL-fraunces.txt`
and `OFL-archivo.txt`.
