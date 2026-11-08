# Bronisław Kaper Research Archive

A source-based research archive of the composer Bronisław Kaper (1902–1983),
covering his life and work from Warsaw through Berlin and Paris to his first
years in Hollywood, to 1939. Every work, credit, person, place and event is
tied to the documents that support it, and every document is described as a
Source with a citation a reader can follow.

**Site:** https://iwmarlin.github.io/kaper/ ·
**How to cite and reuse:** https://iwmarlin.github.io/kaper/cite.html ·
**Corrections:** [open an issue](https://github.com/iwmarlin/kaper/issues)

## What is in the repository

| Path | What it holds |
| --- | --- |
| `data/public/v1/` | The canonical dataset: fourteen JSON tables, a manifest and a build report. The source of truth for everything else. |
| `assets/images/`, `assets/audio/` | The archival image and sound files the archive holds. |
| `assets/site/` | The site's scripts, styles and fonts. |
| `*.html` | The top-level pages: home, works, people, timeline, map, media, sources, cite and reuse. |
| `records/`, `data/site/`, `assets/generated/` | Generated: one HTML page per record, compact per-record data bundles, responsive image derivatives. Never edited by hand. |
| `scripts/` | The build, normalization and validation tools. |
| `tests/` | The test suite, which also holds the editorial decisions that must not quietly come undone. |
| `docs/` | Editorial rules, audits and reviews (below). |

The site is static. It needs no database and no server-side code, and runs
unchanged on GitHub Pages, on Netlify and from a local folder.

## Working on the data

Edit the tables in `data/public/v1/` directly, then rebuild and test:

```sh
python3 -m pip install -r requirements-site.txt   # once
python3 scripts/rebuild_site.py --root .
python3 -m unittest discover --start-directory tests
```

`rebuild_site.py` runs every step in order — manifest reconciliation, checks
that the authority and source normalizers find nothing to change,
responsive images and home data,
per-record bundles, cache versions, the static record pages and the sitemap —
and then every freshness and relation validator. It stops at the first
failure, so a partial rebuild is never reported as ready. Commit everything it
changes, generated files included; the quality gate fails a commit whose
generated layers are stale.

Links between records are kept in both directions. After adding one side of a
link, `python3 scripts/reconcile_symmetric_links.py --data data/public/v1
--write` adds the other.

Requirements: Python 3.11 or newer, and Node.js 18 or newer, which the
static-record step uses to run the same renderer as the browser. No package
installation or bundling is involved.

To browse the site locally:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

and open http://127.0.0.1:4173/.

Responsive images are built incrementally; `--full-images` re-encodes every
derivative. For a release dated other than today, pass `--publication-date
YYYY-MM-DD` to `rebuild_site.py`, which sets the sitemap's dates for changed
pages; unchanged pages keep theirs.

## Publishing

Work happens on a branch. Merging it into `main` publishes it:

1. The **Quality gate** workflow rebuilds the site, checks that nothing
   generated is stale, and runs every validator and the test suite.
2. Only if it passes does **Deploy to GitHub Pages** publish that same commit.
   It uploads the site alone, without `tests/`, `scripts/` or `docs/`.

The repository's Pages source must be set to *GitHub Actions* for this. The
full procedure, including Netlify previews, is in
[`docs/deployment.md`](docs/deployment.md).

## Editorial rules and audits

**Rules the data follows**

- [`work-years.md`](docs/work-years.md) — a Work is dated by the earliest year
  it is documented; a film by its first release.
- [`contribution-certainty.md`](docs/contribution-certainty.md) — what
  *confirmed* and *probable* mean on a credit.
- [`contribution-evidence-context.md`](docs/contribution-evidence-context.md) —
  the internal field recording what kind of evidence a credit rests on.
- [`authority-headings.md`](docs/authority-headings.md) and
  [`authority-identifiers.md`](docs/authority-identifiers.md) — authorized
  names, authority records and contextual references for people and
  organizations.
- [`public-data-export.md`](docs/public-data-export.md) — how the public
  dataset is maintained, and why the original exporter must not be re-run.
- [`site-architecture.md`](docs/site-architecture.md) and
  [`historical-basemap.md`](docs/historical-basemap.md) — how the site and its
  map are built.

**Audits**, each with its findings, what was done about them and what was left
open

- [`sources-audit.md`](docs/sources-audit.md) — every Source: links, page-level
  citations, records resting on Wikipedia alone.
- [`records-audit.md`](docs/records-audit.md) — people, works, credits,
  relations, events, places and media.
- [`works-audit.md`](docs/works-audit.md) — every Work's title, identity,
  credits and dates.
- [`people-audit.md`](docs/people-audit.md) — headings, register
  identifiers and life dates of people and organizations.
- [`sieghardt-comparison.md`](docs/sieghardt-comparison.md) — the archive
  against Sieghardt's catalogue of Jurmann's works, entry by entry.
- [`public-data-audit.md`](docs/public-data-audit.md) — the dataset against
  its own checks.

**Reviews** of particular groups of records, dated, in `docs/`: the Kaper Papers
manuscripts, recording catalogues and performers, video sources, archival
witnesses, authority headings and life dates.
