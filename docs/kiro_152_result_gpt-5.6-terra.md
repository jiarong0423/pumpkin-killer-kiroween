# Kiro task 152 result

Changed `manifest.webmanifest`, `sw.js`, `scripts/make_sw_precache.py`, `scripts/make_pwa_icons.py`, `scripts/test_pwa_files.py`, `icons/*`, and `docs/pwa_index_edits.md`; `make_pwa_icons.py --apply` also added the required `icons/` provenance row.
`make_sw_precache.py` generates the 26-page-preload cache list; `sw.js` uses `pk-v1`, network-first HTML, cache-first same-origin static files, and no relay/WebSocket handling.
`make_pwa_icons.py` deterministically derives all icons from `assets/units/unit_skeleton.png` and checks its four recorded SHA-256 values.
`docs/pwa_index_edits.md` gives the main line's exact page/export edits. `index.html` was not changed.
Verification commands run: `python3 -B scripts/make_sw_precache.py --check`; `python3 -B scripts/make_pwa_icons.py`; `python3 -B scripts/test_pwa_files.py`.
Last test output: `Ran 3 tests in 0.030s` then `OK`.
Not verified: browser install/offline behaviour and main-line `index.html`/export-manifest edits were intentionally outside this task.
The manifest retains `orientation: landscape`: the existing 16:9 canvas does not need `any`.
Two earlier ad-hoc inspection commands were not run because their permission requests were unanswered; the final test independently validated the manifest, icons, generated precache, files, and forbidden relay/WebSocket text.
