# Bronisław Kaper Research Archive

A source-based static research site documenting Bronisław Kaper's works,
professional networks, places and career through 1939.

The public website reads versioned JSON from `data/public/v1/`. It has no runtime
connection to Airtable, no private credentials and no required build process. See
`docs/public-data-export.md`, `docs/site-architecture.md` and
`docs/deployment.md` for the data policy, architecture and release procedure.

Run locally:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Validate:

```sh
python3 scripts/build_site_assets.py --check
python3 scripts/build_record_payloads.py --check
python3 scripts/validate_public_export.py --data data/public/v1 --assets-root .
python3 scripts/validate_site.py --root .
```

After regenerating the public Airtable export or changing a published image,
rebuild the compact home payload, responsive WebP derivatives and relation-aware
record payloads:

```sh
python3 -m pip install -r requirements-site.txt
python3 scripts/build_site_assets.py --root .
python3 scripts/build_record_payloads.py --root .
```

The build preserves the archival source files in `assets/images/`. Browser-sized,
metadata-free derivatives are written to `assets/generated/responsive/`.
Record pages load compact, generated bundles from `data/site/records/`; the
canonical public tables in `data/public/v1/` remain the source of truth.
