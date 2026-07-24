# Public data export

The website data is generated from the frozen private Airtable snapshot, not from
the legacy data embedded in the current HTML pages. The public scope covers the
documented period from 1902 through 1939.

## Export policy

- `scripts/public_export_config.json` is the explicit field allowlist. A field
  absent from this file cannot enter a table JSON file.
- Only records with `Editorial Status = approved` enter the public graph. Work,
  place, gallery, timeline, contribution and relation publication controls are
  applied in addition to this status.
- `excludedPlaceIds`, `excludedMediaIds`, `excludedSourceIds`, and
  `excludedContributionIds` in the export configuration support explicit
  curation and the removal of confirmed duplicate or superseded records without
  rewriting the frozen private Airtable snapshot.
- People, organizations and sources are included only when approved and reachable
  from the selected public graph.
- Linked Airtable record IDs are replaced with stable project IDs. Links to records
  outside the public graph are dropped and every remaining link is validated.
- Legacy fields, review flags, internal notes, validation fields, attachment
  metadata and Airtable record IDs are not exported.
- `Sources → Evidence Note`, `Sources → Rights Note`, and
  `Work Relations → Evidence / Derivation` are deliberately private. Public rights
  and fair-use information is taken from the corresponding Media record.
- `scripts/public_export_overrides.json` contains documented public-field
  corrections required by the frozen snapshot, including normalized asset paths.
  It may also hold explicitly justified post-snapshot public additions and link
  additions and removals. All keys remain subject to the same allowlist and graph
  validation; existing stable IDs cannot be changed, and every operation requires
  a reason.

## Generate

From the repository root:

```sh
python3 scripts/export_public_data.py \
  --backup ../Kaper-Airtable-Backup-PRIVATE-2026-07-13 \
  --output data/public/v1 \
  --assets-root .
```

The exporter writes atomically. If any validation fails, the existing public export
is left untouched and a diagnostic build is retained in a temporary directory.

After a successful export, rebuild the derived website payloads. These files are
deterministic caches of the canonical public JSON and must not be edited manually:

```sh
python3 scripts/build_site_assets.py --root .
python3 scripts/build_record_payloads.py --root .
python3 scripts/build_static_records.py --root .
```

## Validate without Airtable

```sh
python3 scripts/validate_public_export.py \
  --data data/public/v1 \
  --assets-root .

python3 scripts/build_site_assets.py --check
python3 scripts/build_record_payloads.py --check
python3 scripts/build_static_records.py --check
```

This independent pass verifies the manifest checksums, table counts, schema and
allowlist, required fields, unique IDs and slugs, all graph links, the 1939 scope,
fair-use metadata, local media files, private URLs, known non-public IDs and
workflow wording.

`data/public/v1/manifest.json` records the snapshot timestamp, record counts,
export policy, generator checksum, allowlist checksum, override checksum and the
SHA-256 checksum of every generated data file. `build-report.json` records the
complete table counts, applied overrides, allowlist coverage and warnings.

PNG assets use `.png` filename extensions matching their actual content. The
normalization changes names and public paths only; the image bytes remain intact.
