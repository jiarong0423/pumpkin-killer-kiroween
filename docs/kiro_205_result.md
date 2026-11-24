# Kiro task 205 result

## What changed

- `index.html`: consolidated the five top utility controls into the sole 44 by 44 `#settings-btn`; moved sound, restart, language, and help into the one settings sheet; added dialog focus containment and return-to-menu focus; kept the M and H shortcuts.
- `index.html`: set role badges and status chips to 12 CSS px; added a compact landscape start selection with eight cards, avatars, names, role, HP and ATK bars, status chips, and the start action in view. The optional scene, room, seat, and install sections are hidden in this constrained selection layout.
- `index.html`: compacted the settings rows, made `#settings-close` 44 by 44, kept the sheet clear of the countdown board and dock, and provided a narrow-viewport scroll indicator only where internal scrolling is unavoidable.
- `css/dock.css`: placed the single menu target below the HUD board, or in the scenic side margin when that margin is available.
- `assets/i18n/en.json`, `assets/i18n/zh-TW.json`: removed unused language-choice and sound-tip keys after the settings sheet changed to a language toggle. Both dictionaries remain key-identical.
- `scripts/test_phone_layout.js`, `scripts/test_ui_settings.js`: added static guards for the one-button utility menu, compact eight-card selection, 44 px close target, sheet focus behavior, and the updated settings controls.
- `scripts/measure_phone_layout.mjs`: added numeric settings client/scroll-height reporting to the review output.
- `sw.js`: refreshed only through `python3 -B scripts/make_sw_precache.py --apply`.
- `docs/ui_review_20261116.md`: appended the required after table with the measured before and after figures.

No images were opened, decoded, or attached. `scripts/shoot_views.mjs` generated review captures and the work used only its DOM-geometry output.

## Measured before and after

| Item | Before | After |
|---|---|---|
| Utility menu target | Five 28x28 controls and five opponent-HUD intersections per target phone | One 44x44 menu target and zero measured HUD intersections at all five target phones |
| Role / chip text | 10 px roles and 10.5 px chips | 12 px roles and chips; no role or chip wraps over two lines |
| Start selection clipping | 19 to 25 clipped rectangles | Zero clipped rectangles at 873x392, 915x412, 844x390, 932x430, and 667x375 |
| Settings close / contents | 30x30 close and 5 to 17 clipped sheet descendants | 44x44 close; 204x224 client/scroll height, no scroll, and zero clipped settings descendants at all five target phones |

## Commands run and real output tails

Successful final UI checks:

```text
$ node scripts/test_ui_settings.js
... 
test_ui_settings: 7/7 checks passed

$ node scripts/test_phone_layout.js
... 
test_phone_layout: 8/8 checks passed

$ node scripts/test_i18n.js
...
26 passed, 0 failed (263 keys per language)

$ node scripts/test_layout_property.mjs
...
measure_phone_layout: 200/200 viewports passed (seed 19120261116)
test_layout_property: 200 seeded landscape viewports passed

$ node scripts/measure_phone_layout.mjs
...
667x375     666.7×375.0       0.999  0.2     360.0        0
measure_phone_layout: 5/5 viewports passed

$ node scripts/shoot_views.mjs
...
measure_phone_layout: 6/6 viewports passed (review)
shoot_views: saved numeric review captures

$ python3 -B scripts/make_sw_precache.py --apply
OK wrote sw precache and cache name

$ python3 -B scripts/test_pwa_files.py
...
Ran 3 tests in 0.043s

OK

$ node scripts/test_decisions_frozen.js
...
test_decisions_frozen: 10/10 checks passed
```

The full JavaScript sweep was attempted with:

```text
for test_file in scripts/test_*.js; do node "$test_file" || exit 1; done
```

It stopped at an unrelated existing failure in `scripts/test_class_stats.js`:

```text
test_class_stats: 1 of 14 tests FAILED
```

The socket-free Python sweep was run to completion while excluding socket/integration runners (`test_e2e_local.py`, `test_mcp_connect*.py`, `test_pk_relay.py`, `test_relay_reconnect.py`, and `test_smoke_*.py`). It reported existing failures outside this task's files:

```text
FAILED (failures=1)  # scripts/test_mcp_seats.py: referee baseline mismatch
AssertionError: decode mismatch at M case 65 ...  # scripts/test_qr_decode.py
```

`test_pwa_files.py` initially detected the stale precache after the UI files changed. Regenerating `sw.js` through the prescribed script produced the passing result recorded above.

The required transcript command was run but did not pass:

```text
$ node scripts/record_match_transcript.mjs
Error: two recordings differed under the same seeds at byte 1475

An earlier run reached the fixture comparison and reported:
Error: N=1 transcript differs from docs/transcripts/n1_baseline.json
```

I did not rewrite the baseline or alter any game rule, number, timing, or transcript fixture. The frozen-decision check passed after that failure.

## Not verified

- The owner must verify the interaction on a physical phone, including the 44 px targets, sheet focus loop, internal scroll indicator at unusually short landscape heights, and the constrained landscape start layout.
- The N=1 transcript baseline mismatch requires main-line investigation; I did not claim `baseline matches`.
- The three unrelated full-suite failures above remain for their owning workstreams.
