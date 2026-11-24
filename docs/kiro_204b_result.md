# Kiro task 204b result

## What changed

- `scripts/measure_phone_layout.mjs`: added `--review`, reliable page-readiness
  waiting, start/battle/result/settings capture, and DOM/computed-style numeric
  measurement. It checks visible DOM text font sizes in CSS/device px, target
  rectangles, stage coverage, clipping, button/chip line boxes, solid-colour
  contrast, named HUD intersections, and focus order. It saves screenshots but
  never reads or decodes them.
- `scripts/shoot_views.mjs`: added the review command wrapper.
- `(not published)`: wrote start, battle, result, and settings PNG captures at
  the six requested viewports. No PNG was opened, read, or attached.
- `docs/ui_review_20261116.md`: recorded six ranked, measured defects and the
  numerical method.
- `scripts/release/export_manifest.json`: no edit was needed because it already
  contains the required first-match exclusion for `(not published)`.

No files outside the brief's allow-list were edited. I did not edit `index.html`,
CSS, assets, or JavaScript game modules. I did not push, deploy, commit, or read
secret values.

## Commands run

```text
node scripts/shoot_views.mjs
```

This ran the numeric review and wrote captures. It deliberately returned status
1 because the existing geometry assertion found five HUD intersections at every
listed phone viewport. Its last lines were:

```text
measure_phone_layout: 5 geometry failures during review
  873x392: HUD intersections: opponent-name-plate / sound-btn, opponent-name-plate / reset-btn, opponent-name-plate / lang-btn, opponent-name-plate / settings-btn, opponent-name-plate / help-btn
  915x412: HUD intersections: opponent-name-plate / sound-btn, opponent-name-plate / reset-btn, opponent-name-plate / lang-btn, opponent-name-plate / settings-btn, opponent-name-plate / help-btn
  844x390: HUD intersections: opponent-name-plate / sound-btn, opponent-name-plate / reset-btn, opponent-name-plate / lang-btn, opponent-name-plate / settings-btn, opponent-name-plate / help-btn
  932x430: HUD intersections: opponent-name-plate / sound-btn, opponent-name-plate / reset-btn, opponent-name-plate / lang-btn, opponent-name-plate / settings-btn, opponent-name-plate / help-btn
  667x375: HUD intersections: opponent-name-plate / sound-btn, opponent-name-plate / reset-btn, opponent-name-plate / lang-btn, opponent-name-plate / settings-btn, opponent-name-plate / help-btn
```

```text
node scripts/test_phone_layout.js
```

```text
ok   - manifest requests fullscreen landscape presentation
ok   - combat and HP labels reject invalid or unbounded numeric output
test_phone_layout: 7/7 checks passed
```

```text
node scripts/test_ui_settings.js
```

```text
ok   - settings sheet uses literal i18n keys in both dictionaries
ok   - settings controls keep 44 px phone targets and a compact sheet
test_ui_settings: 7/7 checks passed
```

```text
node scripts/test_i18n.js
```

```text
ok   - every translation key used in index.html exists in both dictionaries
ok   - every key in the dictionaries is used in index.html

26 passed, 0 failed (270 keys per language)
```

```text
node scripts/test_layout_property.mjs
```

This returned status 1 at its first seeded viewport, exposing the same existing
HUD collision rather than a sandbox socket denial. Its last lines were:

```text
Error: 882x381: HUD intersections: opponent-name-plate / sound-btn, opponent-name-plate / reset-btn, opponent-name-plate / lang-btn, opponent-name-plate / settings-btn, opponent-name-plate / help-btn
    at assertGeometry (file://<home>/Developer/pumpkin-killer/scripts/measure_phone_layout.mjs:167:30)
    at file://<home>/Developer/pumpkin-killer/scripts/measure_phone_layout.mjs:258:22

Node.js v26.13.0
```

## Not verified

- I did not inspect any screenshot or other image file, by task requirement.
- Canvas-drawn HUD and result text cannot be measured through the DOM; the
  review explicitly does not claim font size or gradient/translucent-background
  contrast for that content.
- This harness emulates the requested viewport and DPR in headless Chrome. The
  main line should rerun `node scripts/shoot_views.mjs` and test the P0 target
  and HUD-collision fixes on a physical no-hover phone before accepting them.
- The local server socket was available in this run, so no owner-only fallback
  command is needed. If the sandbox blocks it later, the owner can run the same
  command from the repository root: `node scripts/shoot_views.mjs`.
