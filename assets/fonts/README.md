# Fonts

Two variable typefaces, both served from this origin. They have to be: the
site's Content-Security-Policy is `default-src 'self'`, so a font requested
from a third-party CDN is refused before it is fetched.

| File | Family | Axes | Size |
|---|---|---|---|
| `kaper-serif.woff2` | Source Serif 4 | `wght` 200–900, `opsz` 8–60 | 131 KB |
| `kaper-sans.woff2` | Inter | `wght` 100–900, `opsz` 14–32 | 66 KB |

Both are subsets of the variable sources in `src/`, cut to Latin and Latin
Extended-A plus the punctuation the citations use. Latin Extended-B is left
out on purpose: nothing in the archive reaches it and it is a third of the
file. Regenerate with `python3 scripts/build_fonts.py`.

Variable rather than static because the stylesheet asks for eleven distinct
weights — 400, 500, 600, 640, 650, 680, 700, 720, 740, 750, 760. Against
static faces those collapse to the nearest of 400 and 700.

## Licence

Both families are released under the SIL Open Font License 1.1, which permits
redistribution, embedding and modification, including subsetting, provided the
licence travels with the files.

- Source Serif 4 — Copyright 2014–2023 Adobe (http://www.adobe.com/), with
  Reserved Font Name 'Source'. https://github.com/adobe-fonts/source-serif
- Inter — Copyright 2016–2024 The Inter Project Authors.
  https://github.com/rsms/inter

The full licence text as distributed with each family is in `OFL-SourceSerif4.txt`
and `OFL-Inter.txt`.
