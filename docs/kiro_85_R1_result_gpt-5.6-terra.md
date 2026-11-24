# Task 85a R1 result — gpt-5.6-terra

## What changed
- Created `scripts/release/check_asset_refs.py`: `scan(root)` and `missing(root)` scan literal page, JavaScript, and CSS asset paths, report `REF`, `MISSING`, and case-sensitive `CASE` failures.
- Created `scripts/release/export_tree.py`: validates ordered first-match manifest rules, skips `.git` and symlinks, supports dry run and guarded `--apply`, limits assets to literal references, applies the four named transforms, and creates deterministic export notes.
- Created `scripts/test_check_asset_refs.py` and `scripts/test_export_tree.py`: stdlib `unittest` toy-tree coverage for the R1 cases.
- Kept `scripts/release/export_manifest.json` unchanged.

## Commands run
- `python3 -B scripts/test_check_asset_refs.py`
  - Last line: `OK`
- `python3 -B scripts/test_export_tree.py`
  - Last line: `OK`
- `python3 -B scripts/release/export_tree.py --source . --manifest scripts/release/export_manifest.json`
  - Last line: `DRY RUN: wrote nothing`

## Not run / not verified
- I did not run `--apply` on the real repository, create `(not published)`, run the later privacy gate, use git, GitHub, remotes, or network access.
- The real-tree dry run reported `SUMMARY selected=548 skipped_symlinks=0`; it does not apply transforms or verify later-stage privacy-gate requirements.
