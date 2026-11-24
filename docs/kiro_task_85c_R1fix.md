# Kiro task 85c — fix a false positive in check_asset_refs.py (stage R1 follow-up)

The main line reran your R1 tests (both OK) and ran `python3 -B scripts/release/check_asset_refs.py` on the real tree: `SUMMARY refs=124 missing=16`. Eight of the 16 lines are false positives, because they are directory prefixes written as strings in code, not files: `assets/fonts`, `assets/audio`, `assets/units`, `assets/i18n`, `(not published)`, `assets/ui` (and similar). The other eight are real missing files and must keep being reported: `assets/env/bg_belltower.png`, `(not published)`, `assets/fx/sprites/fx_feet_chain.png`, `assets/units/unit_knight_unarmed.png`, three `assets/audio/sfx/*.ogg`, and the CSS fallbacks `(not published)`.

Change only `scripts/release/check_asset_refs.py` and `scripts/test_check_asset_refs.py`:
1. A matched path counts as a file reference only when its last path segment has a file extension (a dot followed by letters or digits). A path with no extension, or ending in `/`, is a directory prefix: it is not listed as REF and never as MISSING. If such a prefix names an existing directory, print one `DIR` line instead; if it does not exist, print `DIR_MISSING` (does not change the exit code).
2. Keep case-sensitive checking and exit 1 when any file reference is missing or has a case mismatch.
3. Add test cases: a directory prefix string is not reported as MISSING; an existing directory prints `DIR`; a missing file with an extension still exits 1.

Run `python3 -B scripts/test_check_asset_refs.py` and `python3 -B scripts/release/check_asset_refs.py` (the real tree; exit 1 is expected because of the eight real gaps). Write `(not published)` (max 30 lines) with the exact `SUMMARY` line and the list of remaining MISSING files, what you did not run, and nothing else. Touch no other file. Python stdlib only. No network, no git.
