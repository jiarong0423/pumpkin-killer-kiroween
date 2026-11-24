# Kiro task 94 result (claude-sonnet-5.5)

## What changed
- `css/fonts.css`: removed the three `.woff` fallback `src` entries (`pk-display-cjk-900.woff`, `pk-body-400.woff`, `pk-body-700.woff`). Each face keeps its `.woff2` entry, and nothing else in the file was touched. `scripts/build_fonts.py` writes `.woff` only when brotli is missing, so a machine without brotli would now have to rebuild and re-add the fallback.
- New `docs/audio_gap_options_20261115.md`: options for `move_step.ogg`, `item_pickup.ogg` and `ultimate_ready_chime.ogg`, and the missing-file behaviour of `js/audio.js`.
- Recommendations: drop the file reference for `move_step` (`step_leaf.ogg` already plays as a variant) and for `ultimate_ready_chime` (no verified source, nothing fires it). For `item_pickup`, add Kenney `confirmation_001.ogg` only after the owner has listened to it. I changed no sound file, map or JS.

## Commands to verify (run from the repo root)
```
python3 -B scripts/test_fonts.py
python3 -B scripts/test_preload_links.py
python3 -B scripts/release/check_asset_refs.py
```
Expected: the first two print OK, and the third no longer lists the three `.woff` files. Three sound names should remain, unless the owner changes the map.

## What I could NOT verify
- The three commands above were NOT run. The shell tool returned "The permission request failed before it was answered" on every call, so there is no output to quote. I do not claim any test passed.
- By grep, `scripts/test_fonts.py` and `scripts/build_fonts.py` use `.woff` only as an accepted file extension, not as a required CSS entry. That is a reading of the code, not a test result.
- The durations and fit of the candidate sounds, and whether the loader in `index.html` logs a 404 per missing file.
- Whether `scripts/test_preload_links.py` reads `css/fonts.css`. I did not open it.
