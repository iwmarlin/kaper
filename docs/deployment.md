# Deployment runbook

## Production origins

- GitHub Pages: `https://iwmarlin.github.io/kaper/`
- Netlify: existing site connected to this repository

GitHub Pages is the canonical origin unless a custom domain is selected before
release. Netlify previews are used for editorial acceptance before merging.

## Required hosting settings

### GitHub Pages

- Source: GitHub Actions

`.github/workflows/pages.yml` publishes the site after the quality gate has
passed on `main`, from the same commit. It stages the site without `tests/`,
`scripts/`, `docs/` and the repository's own tooling files, and uploads it as a
Pages artifact. It can also be run by hand from the Actions tab (*Deploy to
GitHub Pages*, *Run workflow*).

GitHub's deploy action gives a deployment at most ten minutes, whatever
timeout it is asked for. A change to the stylesheet or a site script writes a
new version string into every page, some 2,500 files, and GitHub can take
longer than that to take them in. A second attempt then finishes in seconds,
because the files are already there, so the workflow tries a timed-out
deployment twice more with the same artifact. If all three fail, re-run the
workflow from the Actions tab.

Deploying straight from the branch was the earlier setting. It copied the
whole repository under the same ten-minute limit, and in November 2026 it
began to time out on every other merge.

### Netlify

- Production branch: `main`
- Base directory: empty
- Build command: empty
- Publish directory: `.`
- Deploy Previews: enabled for pull requests

`netlify.toml` declares the publish directory, security headers and conservative
cache rules. It does not redirect or change the existing production domain.

## Release sequence

1. Reconcile the canonical public dataset, rebuild the derived site payloads and
   run all validators.
2. Start a local static server and test the seven public routes: the home page,
   works, people, timeline, map, media and sources.
3. Commit the complete feature branch without private research files.
4. Push the feature branch and open a draft pull request to `main`.
5. Review the Netlify Deploy Preview on desktop and mobile.
6. Confirm catalogue search, timeline filters, map/list, media rights blocks and
   representative linked records.
7. Mark the pull request ready only after editorial acceptance.
8. Merge to `main` explicitly. Do not force-push and do not deploy by editing
   `main` locally.
9. Verify GitHub Pages and Netlify production after their deployments complete;
   the Pages deployment starts only once the quality gate on `main` is green.

## Pre-release commands

```sh
python3 scripts/reconcile_manifest.py
python3 scripts/validate_public_export.py \
  --data data/public/v1 \
  --assets-root .

python3 scripts/build_site_assets.py --root .
python3 scripts/build_record_payloads.py --root .
python3 scripts/stamp_assets.py
python3 scripts/build_static_records.py --root . --publication-date YYYY-MM-DD
python3 scripts/build_site_assets.py --check
python3 scripts/build_record_payloads.py --check
python3 scripts/build_static_records.py --check
python3 scripts/validate_site.py --root .
```

`publicDataUpdatedAt` is maintained from changes to the canonical public JSON
tables, not from a source-package timestamp. `reconcile_manifest.py` advances it
when those tables change. For a deliberately dated release, pass
`--public-data-date YYYY-MM-DD` (or use the same option with `rebuild_site.py`).

For local browsing:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Then open `http://127.0.0.1:4173/`.
