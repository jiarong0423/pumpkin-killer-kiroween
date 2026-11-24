# Kiro task 191 result — UI settings inventory and safe settings sheet

## What changed

- `docs/ui_settings_inventory_20261116.md` inventories page controls from the current code, including persistence, i18n keys, 392 px landscape behavior, gaps, and deferred/not-needed settings.
- `.kiro/specs/ui-settings/requirements.md`, `design.md`, and `tasks.md` add the short EARS spec. Tasks 1–4 are checked from real command output.
- `.kiro/steering/ui_settings.md` records the settings-sheet, accessibility, persistence, motion, i18n, and test rules.
- `index.html`
  - Adds `#settings-btn`, one `#settings-sheet`, and `#settings-backdrop` with gear open, Escape close, and outside-tap close behavior.
  - Adds guarded `readSettings()`, `saveSettings()`, `applyAudioSettings()`, `applySettings()`, `reduceMotionEnabled()`, and setting handlers. Effects enablement/volume, music volume, reduced motion, language, and the right built-in AI level use `pk_ui_settings`; language keeps its existing guarded `js/i18n.js` storage.
  - Routes existing quick sound control through the effects preference, applies `GameAudio.setVolumes()` and AmbientSfx levels, and restores the right AI level before a match.
  - Gates shake through `setScreenShake()`, skips hit flash, requests low weather effects, caps procedural bursts at six particles, and caps seeded effect scale while reduced motion is active. Game rules, physics, turn timing, and AI multipliers remain unchanged.
  - Keeps sheet controls at least 44 px and uses a fixed compact landscape placement that the measured script verifies does not cover the countdown board or dock.
- `assets/i18n/en.json` and `assets/i18n/zh-TW.json` add 15 literal `settings.*` keys. The English file has no new CJK text.
- `scripts/test_ui_settings.js` statically checks the sheet, guarded storage, scoped settings, reduced-motion gates, close handlers, literal translations, and 44 px sheet controls.
- `scripts/measure_phone_layout.mjs` now supports `--property`: a fixed-seed, actual-browser 200-viewport loop across widths 560–1000, heights 320–480, and DPR 1.5–3. It opens the settings sheet and checks stage visibility, existing HUD intersections, sheet fit, and no countdown/dock overlap. It prints the seed and first failing viewport.
- `scripts/test_layout_property.mjs` executes the 200-case measured property loop.
- Added Chinese settings labels, so `scripts/build_fonts.py` rebuilt the font subsets and `scripts/make_sw_precache.py --apply` refreshed `sw.js` as required.

## Commands run and final output

```text
node scripts/test_ui_settings.js
…
test_ui_settings: 7/7 checks passed

node scripts/test_phone_layout.js
…
test_phone_layout: 7/7 checks passed

node scripts/test_i18n.js
…
26 passed, 0 failed (254 keys per language)

node scripts/test_layout_property.mjs
…
measure_phone_layout: 200/200 viewports passed (seed 19120261116)
test_layout_property: 200 seeded landscape viewports passed

node scripts/test_opening.js && node scripts/test_ai_levels_page.js && node scripts/test_seats_items.js && node scripts/test_ui_polish.js && node scripts/test_page_parses.js
…
test_ui_polish: 6/6 checks passed
test_page_parses: 2 inline scripts and every js/*.js parse

python3 -B scripts/build_fonts.py && python3 -B scripts/test_fonts.py && python3 -B scripts/make_sw_precache.py --apply
…
Ran 36 tests in 0.550s

OK
STALE sw precache: would write 63 files; 20 preload assets; pk-15b96c0e2
OK wrote sw precache and cache name

python3 -B scripts/test_constants_sync.py && python3 -B scripts/test_mcp_game.py && python3 -B scripts/test_mcp_stdio.py
…
Ran 29 tests in 2.824s

OK
```

The complete JavaScript suite command was attempted but did not start because the permission request was unanswered:

```text
for test_file in scripts/test_*.js; do node "$test_file" || exit 1; done
The permission request failed before it was answered, so this call did not run; the user did not reject it.
```

`python3 -B scripts/test_pwa_files.py` was run after regenerating the service worker. It still fails its existing `manifest["display"] == "standalone"` assertion because task 190 changed the manifest to the required `"fullscreen"`; task 190 documented this existing conflict. Its final lines were:

```text
Ran 3 tests in 0.076s

FAILED (failures=1)
```

## Kiro features used

- **Steering:** added and followed `.kiro/steering/ui_settings.md`.
- **Spec tasks:** wrote a short EARS spec and checked tasks 1–4 only after their evidence commands ran.
- **Static test:** added `scripts/test_ui_settings.js`.
- **Property-based browser test:** added the 200-case fixed-seed layout runner and wrapper. It uses real Chrome DevTools Protocol measurements, not screenshots.
- **Hook and custom agent:** attempted to add `(not published)` and `(not published)`, but both filesystem writes were denied before execution. The requested custom-agent runner check was also denied before execution. Neither file exists, and no hook or custom-agent run is claimed.

## Could not verify

- The denied full JavaScript-suite command did not run, so no claim is made that every `scripts/test_*.js` test passes.
- The PWA file test remains red on its pre-existing fullscreen-versus-standalone assertion.
- I could not create or run the requested hook and custom agent because the relevant write/runner permission requests did not execute.

## Main-line phone checks

1. On a real landscape phone at 392 px-high or similar, open the gear sheet before and during a match. Confirm all rows remain reachable, including by scrolling the compact sheet when necessary, and the countdown board and dock stay visible.
2. Change effects volume, music volume, reduced motion, language, and AI level. Reload. Confirm the retained values restore; test once in a blocked-storage/private context and confirm defaults still leave the page usable.
3. With reduced motion on, trigger a cannon or direct hit. Confirm no camera shake or hit-white flash occurs and only small feedback bursts remain; confirm aiming, charge/release, hits, and rounds behave normally.
4. Confirm the effects quick button reflects its persisted on/off state and music remains independently adjustable.
5. Resolve the task-190 manifest expectation in `scripts/test_pwa_files.py` only under the owner/main-line decision, then rerun it.
