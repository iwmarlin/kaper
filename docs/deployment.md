# Deployment runbook

## Production origins

- GitHub Pages: `https://iwmarlin.github.io/kaper/`
- Netlify: existing site connected to this repository

GitHub Pages is the canonical origin unless a custom domain is selected before
release. Netlify previews are used for editorial acceptance before merging.

## Required hosting settings

### GitHub Pages

- Source: deploy from a branch
- Branch: `main`
- Folder: `/ (root)`

No Actions workflow or build artifact is required. `.nojekyll` keeps publication
independent of Jekyll processing.

### Netlify

- Production branch: `main`
- Base directory: empty
- Build command: empty
- Publish directory: `.`
- Deploy Previews: enabled for pull requests

`netlify.toml` declares the publish directory, security headers and conservative
cache rules. It does not redirect or change the existing production domain.

## Release sequence

1. Run the public-data exporter, rebuild the derived site payloads and run all
   validators.
2. Start a local static server and test the six public routes.
3. Commit the complete feature branch; do not commit the private Airtable backup.
4. Push the feature branch and open a draft pull request to `main`.
5. Review the Netlify Deploy Preview on desktop and mobile.
6. Confirm catalogue search, timeline filters, map/list, media rights blocks and
   representative linked records.
7. Mark the pull request ready only after editorial acceptance.
8. Merge to `main` explicitly. Do not force-push and do not deploy by editing
   `main` locally.
9. Verify GitHub Pages and Netlify production after their deployments complete.

## Pre-release commands

```sh
python3 scripts/export_public_data.py \
  --backup ../Kaper-Airtable-Backup-PRIVATE-2026-07-13 \
  --output data/public/v1 \
  --assets-root .

python3 scripts/validate_public_export.py \
  --data data/public/v1 \
  --assets-root .

python3 scripts/build_site_assets.py --root .
python3 scripts/build_record_payloads.py --root .
python3 scripts/build_static_records.py --root .
python3 scripts/build_site_assets.py --check
python3 scripts/build_record_payloads.py --check
python3 scripts/build_static_records.py --check
python3 scripts/validate_site.py --root .
```

For local browsing:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Then open `http://127.0.0.1:4173/`.
