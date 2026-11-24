# Kiro task 180 result

## What changed

- Added `.kiro/steering/art_pipeline.md`: always-on palette, character and face locks, keying and naming rules, the queue-derived avatar prompt template, and the required Qwen disclosure wording.
- Added `.kiro/specs/asset-pipeline/requirements.md`, `design.md`, and `tasks.md`: required hero files, Pillow acceptance checks, literal-reference coverage, manifest and hook behavior, and the limits of automated visual validation.
- Added `scripts/check_asset_pipeline.py`: `main`, `page_data`, `required_files`, `check_picture`, `check_references`, `manifest_data`, and `write_log`. It supports `--hero`, `--path`, `--json`, `--manifest`, and `--manifest --check`; reads `shared/heroes.json` and `index.html` `POSE_SETS`; logs to `(not published)`; and generated `docs/ASSET_MANIFEST.json`.
- Added `scripts/test_asset_pipeline.py`: temporary-Pillow fixtures intended to cover accepted assets, file/property failures, one-file mode, and stale-manifest detection.
- Generated `docs/ASSET_MANIFEST.json` from the current repository.

The requested `(not published)` could not be written. Three `fs_write` requests for that file returned `The permission request failed before it was answered, so this call did not run; the user did not reject it.` No other method was used to bypass that denied write.

## Commands run

```text
python3 -B scripts/check_asset_pipeline.py --manifest
```

Output and exit status: exit 1.

```text
ERROR assets/env/bg_abandoned_school.png not-rgba
ERROR assets/env/bg_belltower.png not-rgba
ERROR assets/env/bg_ruined_church.png not-rgba
ERROR assets/portraits/bat_front.png missing-file
ERROR assets/portraits/bat_front.png required-hero-picture-missing
ERROR assets/units/unit_bat_raw.png not-rgba
ERROR assets/units/unit_knight_raw.png not-rgba
ERROR assets/units/unit_skeleton_raw.png not-rgba
ERROR assets/units/unit_wizard_raw.png not-rgba
SUMMARY checked=210 errors=9
```

```text
python3 -B scripts/test_asset_pipeline.py
```

Output and exit status: exit 5. The command did not execute fixture tests, so it is not claimed as passing. Its last lines were:

```text
----------------------------------------------------------------------
Ran 0 tests in 0.226s

NO TESTS RAN
```

```text
python3 -B scripts/test_check_asset_refs.py
```

Output and exit status: exit 0. Last lines:

```text
----------------------------------------------------------------------
Ran 6 tests in 0.236s

OK
```

```text
node scripts/test_audio.js
```

Output and exit status: exit 0. Last line:

```text
test_audio: 32 passed, 0 failed
```

```text
python3 -B scripts/check_asset_pipeline.py --manifest --check
```

Output and exit status: exit 1 because the nine repository asset errors above remain. It did not report `manifest-stale`, so the generated manifest itself matches the current checked data.

## Not verified

- The new fixture test command was intercepted or otherwise returned `NO TESTS RAN`; its behavior has not been verified by a passing test run.
- The image-save hook was not created because the filesystem write request was not granted.
- The checker cannot prove visual composition, identity, face locks, complete head margins, limb count, or whether an avatar was generated rather than cropped. Those require the owner/main-line image review and the provenance record.
- I did not fix or alter any picture. The current blocking asset result is the missing Bat front portrait. The three background files and four `*_raw.png` unit files also fail the new RGBA rule.
