# Public data maintenance

The versioned files in `data/public/v1/` are the canonical public dataset for
the website. They form a self-contained scholarly graph covering the documented
period from 1902 through 1939. Generated page payloads and HTML records are
derived from these files and are never the source of truth.

## Export policy

- `scripts/public_export_config.json` is the explicit field allowlist. A field
  absent from this file cannot enter a table JSON file.
- Only records with `Editorial Status = approved` enter the public graph. Work,
  place, gallery, timeline, contribution and relation publication controls are
  applied in addition to this status.
- `excludedPlaceIds`, `excludedMediaIds`, `excludedSourceIds`,
  `excludedContributionIds`, and `excludedPersonIds` in the configuration support
  explicit curation and the removal of confirmed duplicate or superseded records.
- People, organizations and sources are included only when approved and reachable
  from the selected public graph.
- Relations use stable project IDs. Links to records outside the public graph are
  rejected and every remaining link is validated.
- Place `periods` are the canonical union of periods assigned to linked timeline
  events. They must not be interpreted or labelled as an independently evidenced
  residence period. `mapPrecision` records whether coordinates identify an
  address, venue, approximate historical site, district or city.
- Source dates use a controlled, sortable model. `date` and optional `dateEnd`
  contain only `YYYY`, `YYYY-MM` or `YYYY-MM-DD`; `dateRole` states whether the
  value dates the publication, issue, recording, described item, catalogue
  volume, object creation, catalogue-record creation or update, data currency,
  digitization or digital publication; `dateQualifier`
  records certainty. Unknown dates omit `date` rather than storing `n.d.` in a
  sortable field. Rare wording that cannot be reconstructed from those fields
  is retained in `dateDisplay`.
- U.S. Copyright Office registration and renewal numbers are structured Source
  identifiers (`usco_registration` and `usco_renewal`). The copyright date may
  remain part of the bibliographic citation, while a copyright-catalogue
  Source's `date` identifies the catalogue volume itself.
- Legacy fields, review flags, internal notes, validation fields and attachment
  metadata are excluded from the public schema.
- `Sources → Evidence Note`, `Sources → Rights Note`, and
  `Work Relations → Evidence / Derivation` are deliberately private. Public rights
  and fair-use information is taken from the corresponding Media record.
- `scripts/public_export_overrides.json` records auditable public-field
  corrections, additions and relation changes, including normalized asset paths.
  All keys remain subject to the same allowlist and graph validation; existing
  stable IDs cannot be changed, and every operation requires a reason.

## Update and generate

After an approved change to `data/public/v1/`, reconcile the manifest and build
the derived website files from the current canonical graph:

```sh
python3 scripts/reconcile_manifest.py
python3 scripts/build_site_assets.py --root .
python3 scripts/build_record_payloads.py --root .
python3 scripts/stamp_assets.py
python3 scripts/build_static_records.py --root . --publication-date YYYY-MM-DD
```

The publication date must be the actual date of the prepared release. The build
preserves per-route dates for unchanged content and updates changed records.

## Validate

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

`data/public/v1/manifest.json` records the public-data update date, record counts,
publication policy, generator checksum, allowlist checksum, override checksum and
the SHA-256 checksum of every generated data file. `build-report.json` records
the complete table counts, applied overrides, allowlist coverage and warnings.

PNG assets use `.png` filename extensions matching their actual content. The
normalization changes names and public paths only; the image bytes remain intact.
