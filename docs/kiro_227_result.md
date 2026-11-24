# Kiro task 227 result

## What changed

- `index.html`: moved the short-landscape battle dock to a fixed 52 px strip below the 16:9 stage when its scenic side margins are under 120 px. The stage height now uses the paired `min()` width/height calculation so it remains 16:9. Units' logical world coordinates, ground position, and physics were not changed.
- `index.html`: when the full-height stage would leave at least 120 px on each side, made `#bottom-dock` a layout-only container. The skill buttons use a 2-column 44 px grid in the left margin; the angle and hold-to-charge power meter use matching 44 px readouts in the right margin. The power meter remains the original canvas pointer control.
- `index.html`: replaced the cramped eight-card start grid with a fixed, no-scroll start-screen carousel. It has previous/next buttons, pointer-swipe handling, Left/Right keyboard handling, eight 44 px thumbnail targets in a compact two-row strip, a selected-hero card sourced from `HERO_PROFILES`, four 2×2 scene tiles, and the visible Start Battle action.
- `index.html`: rebuilt the settings sheet as a centred translucent panel with an opaque 44 px control family and 52 px aligned rows. Effects and music each have a mute, slider, and value readout. Language, reduced motion, AI level, How to play, and Restart each have an explicit row. The menu button is kept in the upper-right clear area in battle and the start-screen top bar.
- `index.html`: combined the round/distance and weather lines, then exposes their canvas bounds plus the countdown and board bounds as read-only `window.__pkHud` data for measured checks.
- `assets/i18n/en.json`, `assets/i18n/zh-TW.json`: added literal carousel and settings keys in both dictionaries and removed no-longer-used keys, preserving key identity and the English CJK rule.
- `scripts/measure_phone_layout.mjs`: added the five 16:9 and five browser-bar viewports, 300–480 px seeded property heights, dock-foot clearance, HUD bounds, and start-screen geometry checks.
- `scripts/test_start_screen_fit.js`: added the required CDP wrapper for the carousel, viewport containment, target size, title clearance, card/chip containment, and eight-step cycle checks.
- `scripts/test_phone_layout.js`, `scripts/test_ui_settings.js`: updated the static contracts for the side bars, 52 px dock strip, carousel, HUD debug data, and settings-sheet geometry.
- `sw.js`: regenerated only with `python3 -B scripts/make_sw_precache.py --apply`.

No images were viewed or attached. `scripts/shoot_views.mjs` ran its required numeric review capture; its generated captures were not opened.

## Measured before and after

| Viewport / condition | Before | After |
|---|---:|---:|
| 873×330 browser bar | stage 587×330; dock 552×59 (17.9% stage height); dock top 77.6% of stage, covering the 79.6% ground line | full-height stage 586.7×330; side margin 143.2 px; dock has no stage rectangle (`display: contents`) and controls are in the two margins |
| 873×392 fullscreen phone | stage 697×392; dock 656×71 (18.1% stage height) | stage 604.4×340; fixed 52 px strip is entirely below the stage; 134.3 px side margin from the paired 16:9 calculation |
| 720×405 16:9 | stage filled viewport; dock 678×73 (18.0% stage height) | stage 627.5×353; 52 px strip begins at stage bottom, so it is outside the stage and clear of the units |
| Fixed required viewport suite | original suite did not include the five 16:9 and browser-bar sizes | 15/15 viewports: zero named HUD overlaps, visible stage/settings sheet, valid 16:9 stage |
| Seeded landscape property suite | previous 320–480 px height range | 200/200 viewports passed with the expanded 300–480 px range |
| Start screen | eight-card grid could clip rows and cards/chips | 15/15 viewports: no document scroll, all tested controls in viewport, 44 px interactive targets, no card/chip/title intersections, and eight next presses wrap to the original hero |

The settings panel uses `rgba(20,12,38,0.78)`, a 1.5 px cyan border, 6 px backdrop blur where supported, and a `rgba(5,2,10,0.33)` backdrop. Its modal width is `clamp(360px, 58vw, 640px)` capped at 70% of viewport width. It is capped at 85% of viewport height. All action controls are 44 px high inside 52 px rows.

## Commands run and output tails

```text
$ node scripts/test_i18n.js
...
26 passed, 0 failed (266 keys per language)

$ node scripts/test_phone_layout.js
...
test_phone_layout: 9/9 checks passed

$ node scripts/test_ui_settings.js
...
test_ui_settings: 7/7 checks passed

$ node scripts/test_start_screen_fit.js
...
measure_phone_layout: 15/15 viewports passed
test_start_screen_fit: 15 landscape viewports passed

$ node scripts/measure_phone_layout.mjs
...
667x300     440.9×248.0       0.661  113.1   300.0        0
measure_phone_layout: 15/15 viewports passed

$ node scripts/test_layout_property.mjs
...
measure_phone_layout: 200/200 viewports passed (seed 19120261116)
test_layout_property: 200 seeded landscape viewports passed

$ node scripts/test_decisions_frozen.js
...
test_decisions_frozen: 10/10 checks passed

$ node scripts/shoot_views.mjs
...
measure_phone_layout: 15/15 viewports passed (review)
shoot_views: saved numeric review captures

$ python3 -B scripts/build_fonts.py && python3 -B scripts/test_fonts.py
...
Ran 36 tests in 0.328s

OK

$ python3 -B scripts/make_sw_precache.py --apply
STALE sw precache: would write 71 files; 20 preload assets; pk-601e9e6c24
OK wrote sw precache and cache name

$ for test_file in scripts/test_*.py; do ...; python3 -B "$test_file" || exit 1; done
...
test_weather_golden.py: 800 cases passed
```

The required transcript command did not pass. This is the same pre-existing failure recorded by task 205; no baseline or game rule was rewritten:

```text
$ node scripts/record_match_transcript.mjs
Error: N=1 transcript differs from docs/transcripts/n1_baseline.json
```

The full JavaScript loop was attempted:

```text
$ for test_file in scripts/test_*.js; do node "$test_file" || exit 1; done
...
test_ui_polish: 4/6 checks passed
```

`test_ui_polish.js` still pins the replaced 4×2 start-card grid and its old `buildStartScreen()` variable names. Task 227 explicitly supersedes that grid with the carousel, but `scripts/test_ui_polish.js` is not in this task's allowed-file lock, so I did not modify it or add compatibility-only dead code.

## Not verified

- The owner must test the touch targets, swipe threshold, side-margin control reachability, settings glass contrast against real scene art, and the browser address-bar behavior on a physical phone.
- `node scripts/record_match_transcript.mjs` does not report `baseline matches`; main line investigation is required before that frozen gate can be claimed.
- The full JavaScript loop remains blocked by the stale task-205 card-grid assertions in `scripts/test_ui_polish.js`. I did not change an unassigned test file to hide that mismatch.
- The main line must rerun and independently record all checks in `docs/kiro_verified.json`.
