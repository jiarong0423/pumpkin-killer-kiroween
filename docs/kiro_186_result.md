# Kiro task 186 result

## What changed

- `scripts/check_asset_pipeline.py`: `page_data` now parses `DOCK_PORTRAIT`; `required_files` resolves each hero's front portrait from that page mapping. This records the Bat's actual `assets/ui/portrait_bat.png` instead of requiring the nonexistent `assets/portraits/bat_front.png`.
- `scripts/check_asset_pipeline.py`: `requires_rgba` exempts RGB scene backgrounds at `assets/env/bg_*.png` and RGB raw unit sources at `assets/units/*_raw.png`. Other managed images still require RGBA.
- `scripts/check_asset_pipeline.py`: generated manifests now include a `pictures` record for every checked managed image. `--manifest --check` reports `ERROR docs/ASSET_MANIFEST.json manifest-stale` and exits 3 whenever the generated content differs, including changed metadata or managed-picture additions and removals.
- `scripts/test_asset_pipeline.py`: the fixture resolves its front portrait through `DOCK_PORTRAIT`; it verifies that custom path, stale manifests after a changed, added, or removed picture, and the RGB exemptions.
- `.kiro/specs/asset-pipeline/requirements.md` and `design.md`: document dock-portrait resolution, the RGB exemptions, and full managed-picture manifest coverage. `docs/ASSET_MANIFEST.json` was regenerated.

## Commands run

```text
python3 -B scripts/check_asset_pipeline.py --manifest
SUMMARY checked=209 errors=0

python3 -B scripts/check_asset_pipeline.py --manifest --check
SUMMARY checked=209 errors=0

python3 -B scripts/test_asset_pipeline.py
......
----------------------------------------------------------------------
Ran 6 tests in 0.340s

OK

python3 -B scripts/test_check_asset_refs.py
......
----------------------------------------------------------------------
Ran 6 tests in 2.260s

OK

python3 -B scripts/check_asset_pipeline.py
SUMMARY checked=209 errors=0
```

Remaining `ERROR` lines from the repository checker: none.

## Not verified

- The main line has not independently rerun these commands or recorded them in `docs/kiro_verified.json`.
- Automated checks do not verify visual composition, identity, complete head margins, or art provenance.
