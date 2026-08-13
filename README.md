# Bronisław Kaper Research Archive

A source-based static research site documenting Bronisław Kaper's works,
professional networks, places and career through 1939.

The public website reads versioned JSON from `data/public/v1/`. This canonical
dataset is self-contained and requires neither private credentials nor a runtime
database connection. See `docs/public-data-export.md`, `docs/site-architecture.md` and
`docs/deployment.md` for the data policy, architecture and release procedure.

Run locally:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Validate:

```sh
python3 scripts/build_site_assets.py --check
python3 scripts/build_record_payloads.py --check
python3 scripts/build_static_records.py --check
python3 scripts/validate_public_export.py --data data/public/v1 --assets-root .
python3 scripts/validate_site.py --root .
```

After changing the canonical public data or a published image, rebuild the
compact home payload, responsive WebP derivatives and relation-aware record
payloads:

```sh
python3 -m pip install -r requirements-site.txt
python3 scripts/reconcile_manifest.py
python3 scripts/build_site_assets.py --root .
python3 scripts/build_record_payloads.py --root .
python3 scripts/stamp_assets.py
python3 scripts/build_static_records.py --root .
```

The build preserves the archival source files in `assets/images/`. Browser-sized,
metadata-free derivatives are written to `assets/generated/responsive/`.
Record pages load compact, generated bundles from `data/site/records/`; the
canonical public tables in `data/public/v1/` remain the source of truth.
Crawlable HTML records are generated under `records/`, and the same build writes
their canonical URLs to `sitemap.xml`. Per-route content hashes and publication
dates are retained in `data/site/sitemap-state.json`: unchanged pages keep their
existing `lastmod`, while only new or changed pages receive the build date. For a
dated release prepared on a different day, pass an explicit ISO date, for example
`python3 scripts/build_static_records.py --root . --publication-date 2026-08-09`.
The static-record step requires Node.js 18 or newer because it executes the same renderer as
the browser. This keeps the complete prerendered HTML and the enhanced view
identical; Node is used directly and no package installation or bundling step is
required.
