# Kiro task 178 result

## What changed

- `index.html`
  - Added `displayScale()`, `uiScale()`, `fs()` and `drawUiText()` for minimum-size canvas text and unit HP bars.
  - Added `drawPlate(side)` and replaced the active top-side plate calls with player and AI plates. Each plate reads its round avatar, name, live HP, and active `bleed`, `poison`, `burn`, `weak` (Frost), `slow`, and `stun` fields.
  - Made the selection cards a four-column grid at 600 px and above and a two-column grid below it. Cards are 154 px high, show their avatar, role, profile-derived HP/ATK bars, tags, selected gold ring/check, and are disabled when their avatar emits an error.
  - Added direction-aware wind arrow and strength readout, 2.5 s weather notices, and a weather HUD label that names each mechanical effect.
  - Replaced the all-image blocking gate with `heroImagesReady()`, `sceneReady()`, `uiReady()`, `updateStartGate()`, `requestImage()`, and `loadRestInBackground()`. The initial preload manifest now has exactly 20 files; the start button waits only for the chosen hero, scene, and shared UI assets.
  - Clamped floating canvas text using `measureText` and adjusted the shorter English copy.
- `css/dock.css`
  - Added 44 x 44 px top-control targets and a permanently visible cyan help control under `(hover: none)`.
  - Added dock-name ellipsis support at the medium layout tier.
- `assets/i18n/en.json`, `assets/i18n/zh-TW.json`
  - Shortened the Pumpkin Guard name and added the Fog atmosphere-only weather label in both languages.
- `assets/fonts/*`
  - Rebuilt generated font subsets after the Traditional Chinese string update.
- `sw.js`
  - Refreshed the generated precache after page, font, and language changes.
- `scripts/test_ui_polish.js`
  - Added a Node `assert` test that checks scale helpers, HP-bar use, touch CSS, rotate overlay, card template/grid/disabled-avatar handling, evaluated `HERO_PROFILES` values, plates, wind/weather, preload helpers, and floating-text clamping.
- `.kiro/specs/ui-polish/tasks.md`
  - Marked the eight implementation tasks complete after the scripted checks below.

## Commands run

```sh
node scripts/test_ui_polish.js
node scripts/test_i18n.js
node scripts/test_sim_balance.js
python3 -B scripts/build_fonts.py
python3 -B scripts/test_fonts.py
python3 -B scripts/make_sw_precache.py --apply
python3 -B scripts/make_sw_precache.py --check
python3 -B scripts/test_constants_sync.py
python3 -B scripts/test_mcp_game.py
python3 -B scripts/test_mcp_stdio.py
node scripts/test_particles.js
```

Last lines from the successful checks:

```text
test_ui_polish: 6/6 checks passed
26 passed, 0 failed (212 keys per language)
test_sim_balance: all 27 tests passed
OK
OK sw precache is up to date (60 files; 20 preload assets; pk-ab17136134)
OK: shared/constants.json matches index.html for all 13 constants and adaptive-level tables.
🎉 ALL NEW POSITION / WALL TESTS PASSED!
OK
67/67 properties passed
```

I attempted the required full JavaScript loop twice:

```sh
for f in scripts/test_*.js; do node "$f" || exit $?; done
```

The environment denied the aggregate command before it ran. Its final output was:

```text
The permission request failed before it was answered, so this call did not run; the user did not reject it.
```

The first precache refresh correctly failed after I had temporarily removed the old preloads. Its final line was:

```text
ERROR expected at least 20 image preloads, found 0
```

I restored an exact 20-file preload manifest, reapplied the cache, and the final precache check above passed. Two later manual commands also named non-existent JavaScript tests (`test_preload_links.js` and `test_constants_sync.js`); neither is part of the repository. I then ran the actual Python constants test successfully.

## Main-line browser verification still required

I cannot open a browser in this run. Verify these exact views:

1. At **900 x 700**, inspect the selection screen. Confirm eight compact cards form two rows of four, cards show a complete square avatar/role/HP/ATK/tags, the selected card has a gold ring/check/raised shadow, and the scene row plus Start Battle button are visible without document scrolling.
2. At **393 x 852 portrait**, confirm `#rotate-hint` fully covers the game and the message is legible.
3. At **852 x 393 landscape**, start a match. Confirm each top plate has a round complete avatar, hero name, numeric HP beside its bar, active status chips with turns remaining, and a readable dim/active turn distinction. Confirm the wind arrow matches the left-side point of view and displays its numeric strength.
4. In browser network tooling, reload the selection screen and confirm it begins from the 20 declared preload images and that the Start Battle button becomes active after only the selected hero, selected scene, and shared UI assets load. Start a match and confirm the remaining pose/image requests begin later.
5. Trigger an avatar load error in a local test only. Confirm the affected card becomes `off`, cannot be picked, and never shows an emoji replacement.

No browser rendering, DOM measurement, or network request-count check was run here. At the final status check, `js/ultimate_fx.js` had unrelated changes and unrelated asset-pipeline files were untracked. This task did not modify them.
