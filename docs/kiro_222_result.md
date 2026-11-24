# Kiro task 222 result

## What changed

- `index.html`: removed the start-screen left/right/Computer-decides controls and their CSS. A non-relay start now resets the single-player seats to `left: "human"` and `right: "ai"`, assigns the picked hero to `player` on the left, and retains the existing `Determinism.coinToss(matchSeed)` opening toss.
- `index.html`: retained relay seat rows for both sides. Their active button guard rejects the only prohibited built-in-AI pairing, `left: "ai"` with `right: "human"`, while still allowing `left: "human"`, `right: "human"` for host and guest.
- `assets/i18n/en.json`, `assets/i18n/zh-TW.json`: removed the four unused literal side-choice keys in both dictionaries.
- `scripts/test_side_choice.js`: now asserts that no side-choice control or code remains, that solo seats are left-human/right-AI, that the seat-button guard blocks a right-side human against the built-in AI, and that a relay two-human pair and both seat rows remain valid. It continues to protect all 52 `sideDraw` golden vectors and orientation freezing.
- `sw.js`: regenerated with `python3 -B scripts/make_sw_precache.py --apply`.

## Verification commands and last lines

```text
node scripts/test_side_choice.js && node scripts/record_match_transcript.mjs
test_side_choice.js: 52 sideDraw golden vectors passed
test_side_choice.js: solo left-human/right-AI and relay two-human seats passed
test_side_choice.js: no side-choice UI and frozen orientation passed
record_match_transcript: baseline matches (40be5ea22bd157b8da6ed5e0d8c297fc12f31cef2f10daf7354b934ae9911646)
record_match_transcript: two recordings are byte-identical

python3 -B scripts/build_fonts.py && python3 -B scripts/test_fonts.py && python3 -B scripts/make_sw_precache.py --apply && node scripts/test_i18n.js
Ran 36 tests in 0.727s
OK
STALE sw precache: would write 70 files; 20 preload assets; pk-1b9c00a39c
OK wrote sw precache and cache name
26 passed, 0 failed (266 keys per language)

node scripts/test_side_choice.js && node scripts/test_decisions_frozen.js && node scripts/test_page_parses.js && node scripts/record_match_transcript.mjs
test_decisions_frozen: 10/10 checks passed
test_page_parses: 2 inline scripts and every js/*.js parse
record_match_transcript: baseline matches (40be5ea22bd157b8da6ed5e0d8c297fc12f31cef2f10daf7354b934ae9911646)
record_match_transcript: two recordings are byte-identical

for test in scripts/test_*.js; do node "$test" || exit $?; done
test_wind_reach: all passed
(exit 0; the runner completed every matching JavaScript test.)

python3 -B scripts/make_sw_precache.py --apply && python3 -B scripts/test_mcp_game.py && python3 -B scripts/test_mcp_stdio.py && python3 -B scripts/test_constants_sync.py
OK wrote sw precache and cache name
🎉 ALL MCP GAME ENGINE TESTS PASSED!
Ran 29 tests in 1.629s
OK
OK: shared/constants.json matches index.html for all 16 constants and adaptive-level tables.

node scripts/test_ui_settings.js && node scripts/test_phone_layout.js && node scripts/test_i18n.js && node scripts/test_layout_property.mjs
test_ui_settings: 7/7 checks passed
test_phone_layout: 7/7 checks passed
26 passed, 0 failed (266 keys per language)
```

The final transcript is byte-identical to `docs/transcripts/n1_baseline.json`. Its SHA-256 remains `40be5ea22bd157b8da6ed5e0d8c297fc12f31cef2f10daf7354b934ae9911646`.

## What I could not verify

- `node scripts/test_layout_property.mjs` failed at its existing `882x381` geometry case: `opponent-name-plate` intersects the sound, reset, language, settings, and help buttons. This task did not change the HUD layout, and the same failure is recorded in `docs/kiro_208_result.md`; I did not broaden the side-choice task to change it.
- The full Python sweep stopped at the existing relay integration failure in `scripts/test_e2e_local.py`: `red action was not acknowledged and judged` with `bridge=stale_or_out_of_turn`. The task lock excludes the relay files involved, so I did not change them. The core Python engine, stdio, and constants checks above passed.
- `node (not published)` could not run because that file does not exist in this checkout (`MODULE_NOT_FOUND`).
- I did not run a two-device relay session or a physical-phone playthrough. No commit, push, deployment, remote change, or secret access was performed.
