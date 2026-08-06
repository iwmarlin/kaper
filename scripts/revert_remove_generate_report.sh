#!/bin/bash
# Revert the commit that added scripts/generate_period_report.py on branch prepare-airtable-export
set -e

# Ensure we are on the right branch
git fetch origin
git checkout prepare-airtable-export
git pull origin prepare-airtable-export

# Revert the commit by its SHA (the commit that added the script)
COMMIT_SHA=021635fdea25b9bc796d65b7e2cc3bd6308c4ede

git revert --no-edit ${COMMIT_SHA} || {
  echo "Revert failed (possibly already reverted). Attempting to remove file directly."
  git rm -f scripts/generate_period_report.py
  git commit -m "Remove generate_period_report.py (cleanup)" || true
}

git push origin prepare-airtable-export

echo "Cleanup complete: script removed and branch updated."