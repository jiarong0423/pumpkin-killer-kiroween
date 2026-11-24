# Kiro task 190 result — phone landscape fill

## What changed

- `index.html`
  - Added `fitVisibleViewport()`, using `window.visualViewport` resize and scroll events plus window resize/orientation events to update the visible CSS viewport dimensions without reload.
  - Replaced the stage's bare `100vh` sizing with dynamic-viewport variables. Desktop keeps its 1400 px cap and 24 px clearance; the phone media rule removes both.
  - Added a fixed, blurred, darkened `body::before` scene layer. `syncSceneBackdrop()` follows the selected scene, so ultra-wide margins use the same scene image as the canvas.
  - Added side-margin detection. When either margin is at least 120 CSS px, `has-side-margin` moves sound, restart, language, and help into a vertical fixed column outside the countdown board.
  - Added `formatCombatNumber()` and `truncateCanvasText()`. `drawPlate()` reserves room for the HP label and ellipsizes the hero name. Damage, bounce, drain, poison, bleed, burn, and return-hit number strings pass through the formatter, preventing unbounded floating-point text from drawing over a plate.
- `css/dock.css`
  - Added the short-landscape (maximum 480 CSS px high) dock rule: one row, `min(76px, 18dvh)` maximum height, 44 px controls, and a narrow-screen control position to the right of the countdown board.
  - Added the side-margin vertical utility-control rule with safe-area offsets.
- `manifest.webmanifest`
  - Set `display` to `fullscreen` and added `display_override: ["fullscreen", "standalone"]`; landscape orientation remains unchanged.
- `sw.js`
  - Regenerated with `python3 -B scripts/make_sw_precache.py --apply` after the page update.
- `scripts/test_phone_layout.js`
  - Added static checks for dynamic viewport sizing, safe-area insets, scenic margins, utility-control relocation, short-phone dock geometry, manifest settings, and bounded combat-number rendering.
- `scripts/measure_phone_layout.mjs`
  - Added a dependency-free Chrome DevTools Protocol measurement harness. It starts the local static server, runs all five required DPR 2.5 landscape viewport sizes, starts a match, checks the visible stage and dock bounds, checks DOM and canvas-HUD rectangles for intersections, prints the table, and cleans up Chrome/server processes.

## Measured browser table

Command: `node scripts/measure_phone_layout.mjs`

| Viewport | Stage (CSS px) | Stage / viewport width | Side margin (CSS px) | Dock bottom | HUD overlaps |
|---|---:|---:|---:|---:|---:|
| 873 × 392 | 696.9 × 392.0 | 0.798 | 88.1 | 377.0 | 0 |
| 915 × 412 | 689.8 × 388.0 | 0.754 | 112.6 | 385.0 | 0 |
| 844 × 390 | 693.3 × 390.0 | 0.821 | 75.3 | 375.0 | 0 |
| 932 × 430 | 721.8 × 406.0 | 0.774 | 105.1 | 403.0 | 0 |
| 667 × 375 | 666.7 × 375.0 | 0.999 | 0.2 | 360.0 | 0 |

Last lines of real output:

```text
667x375     666.7×375.0       0.999  0.2     360.0        0
measure_phone_layout: 5/5 viewports passed
```

The specified 0.85 stage-width ratio cannot be met at every listed viewport without either cropping or horizontally distorting the frozen 16:9 canvas. For example, 844 × 390 permits at most `16 / 9 / (844 / 390) = 0.821` of the visible width. The measured harness preserves the unmodified 16:9 world and verifies that the blurred scene layer fills the rest of the viewport.

## Commands run

```text
node scripts/test_phone_layout.js
node scripts/measure_phone_layout.mjs
node scripts/test_page_parses.js
node scripts/test_ui_polish.js
node scripts/test_size_frozen.js
node scripts/test_orientation_frozen.js
node scripts/test_decisions_frozen.js
node scripts/test_i18n.js
python3 -B scripts/test_constants_sync.py
node scripts/test_particles.js
python3 -B scripts/make_sw_precache.py --apply
python3 -B scripts/test_pwa_files.py
```

Last lines of the successful final regression command:

```text
26 passed, 0 failed (239 keys per language)
OK: shared/constants.json matches index.html for all 13 constants and adaptive-level tables.
67/67 properties passed
```

Additional last lines:

```text
test_phone_layout: 7/7 checks passed
measure_phone_layout: 5/5 viewports passed
test_page_parses: 2 inline scripts and every js/*.js parse
test_ui_polish: 6/6 checks passed
test_size_frozen: 5/5 checks passed
test_orientation_frozen: 5/5 checks passed
test_decisions_frozen: 8/8 checks passed
```

## Not verified / known test conflict

- `python3 -B scripts/test_pwa_files.py` was run after regenerating the service worker and failed only because its existing assertion still requires `manifest["display"] == "standalone"`. This task requires `display: "fullscreen"`. I did not edit `scripts/test_pwa_files.py` because task 190's allowed file list does not include it. Its other two checks passed.

  ```text
  Ran 3 tests in 0.049s
  FAILED (failures=1)
  ```

- The attempted complete globbed `scripts/test_*.js` and `scripts/test_*.py` run did not start because its permission request was not answered. No result is claimed for that command.
- No font build was needed: this task reused the existing portrait rotate hint and its translated `toast.rotatePhone` key, and added no Chinese text.

## Main-line phone check

On the Realme RMX2075 in Chrome WebApk and again on the hosted HTTPS page:

1. Rotate portrait to landscape and back. Confirm the rotate hint appears only in portrait and the stage refits without a reload.
2. Start a match. Confirm the dock is completely visible, remains one row, and all four secondary controls are reachable.
3. Confirm the stage has no black side margins. On sufficiently wide margins, confirm sound, restart, language, and help occupy the scenic side column rather than covering the countdown board.
4. Play through round 8 or later. Confirm each name remains separate from its HP value and no long damage/heal number draws over either HP plate.
