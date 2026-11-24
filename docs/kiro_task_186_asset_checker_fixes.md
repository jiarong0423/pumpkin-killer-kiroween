# Kiro task 186 — fix the asset checker findings (checker, its tests, steering/spec text only)

Read `docs/kiro_180_result.md`, `scripts/check_asset_pipeline.py`, `scripts/test_asset_pipeline.py`, `.kiro/specs/asset-pipeline/*`. Today `python3 -B scripts/check_asset_pipeline.py` reports 9 errors and one test fails (`test_manifest_check_detects_changed_picture`: `--manifest --check` returns 0 after a changed picture).
1. Fix `--manifest --check`: it must exit 3 with `ERROR docs/ASSET_MANIFEST.json manifest-stale` when any listed picture's size or sha256 differs, or a picture is added or removed; make the test pass without weakening it.
2. The bat's front picture: the page uses `assets/ui/portrait_bat.png`; read the paths from `DOCK_PORTRAIT` in `index.html` (read only) instead of assuming `(not published)`.
3. Scene backgrounds (`assets/env/bg_*.png`) and raw sources (`assets/units/*_raw.png`) need no alpha: exempt them from `not-rgba` (backgrounds may be RGB; say so in the spec requirements).
4. Re-run the checker on the repository and write the remaining ERROR lines (should be none or real problems) into `docs/kiro_186_result.md`; regenerate `docs/ASSET_MANIFEST.json` with `--manifest`.
5. Run `python3 -B scripts/test_asset_pipeline.py`, `python3 -B scripts/test_check_asset_refs.py`; paste the last lines.
Touch only: `scripts/check_asset_pipeline.py`, `scripts/test_asset_pipeline.py`, `.kiro/specs/asset-pipeline/*`, `docs/ASSET_MANIFEST.json`, `docs/kiro_186_result.md`. No push.
