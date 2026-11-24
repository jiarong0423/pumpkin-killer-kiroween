# Kiro task 203 result

## What changed

- `index.html`: added the start-screen left, right, and `Computer decides` controls; `chooseHumanSide`, `sideForChoice`, and `applyHumanSideChoice` assign exactly one local human seat and the built-in AI to the other side. `startMatch` assigns the selected hero to the human's physical side. `triggerLeftAiTurn` lets the built-in AI take the mirrored left-side turn when the human selected the right side.
- `index.html`: accepts `host_side_choice` when a relay `start` message arrives. `docs/relay_protocol_20261115.md` records that compatible `start` field and its seeded computer-resolution rule.
- `assets/i18n/en.json` and `assets/i18n/zh-TW.json`: added literal `start.pickSide`, `sideChoice.left`, `sideChoice.right`, and `sideChoice.computer` keys.
- `scripts/test_side_choice.js`: verifies the 52 existing side-draw golden vectors, a 10,000-seed 50/50 check, local opposite-side AI assignment, independent coin-toss use, literal i18n keys, relay-start field consumption, and the frozen-orientation test.
- `js/determinism.js`, `scripts/determinism_py.py`, `scripts/make_determinism_golden.js`, and `shared/determinism_golden.json` already contained the required independent `sideDraw` domain and 52 vectors. I regenerated and verified them without changing prior vectors.
- The required font build updated its generated font artifacts under `assets/fonts/`; the required service-worker precache command updated `sw.js`.

## Commands run

```text
node scripts/test_side_choice.js
# test_side_choice.js: 52 golden vectors passed
# test_side_choice.js: 10000 deterministic draws are 4958/10000 right (within 2 percent)
# test_side_choice.js: local opposite-side AI and frozen orientation passed

node scripts/test_determinism.js
# test_determinism.js: 1092 golden vectors passed
# test_determinism.js: 10000 seed property cases passed

python3 -B scripts/test_determinism_golden.py
# test_determinism_golden.py: 1092 golden vectors passed
# test_determinism_golden.py: 10000 seed property cases passed

node scripts/test_i18n.js
# 26 passed, 0 failed (269 keys per language)

node scripts/test_page_parses.js
# test_page_parses: 2 inline scripts and every js/*.js parse

node scripts/test_opening.js
# opening coin toss, seat levels, and agent option: ok

node scripts/test_orientation_frozen.js
# test_orientation_frozen: 5/5 checks passed

python3 -B scripts/build_fonts.py
# built assets/fonts/pk-display-cjk-900.woff2  405.8 KB
# total font bytes: 1130392 (1.08 MB)

python3 -B scripts/test_fonts.py
# Ran 36 tests in 0.634s
# OK

python3 -B scripts/make_sw_precache.py --apply
# STALE sw precache: would write 69 files; 20 preload assets; pk-f59e49af4f
# OK wrote sw precache and cache name

python3 -B scripts/test_pwa_files.py
# Ran 3 tests in 0.047s
# OK

node scripts/test_phone_layout.js
# test_phone_layout: 7/7 checks passed

node scripts/test_layout_property.mjs
# measure_phone_layout: 200/200 viewports passed (seed 19120261116)
# test_layout_property: 200 seeded landscape viewports passed

node scripts/test_ui_settings.js
# test_ui_settings: 7/7 checks passed

node scripts/test_join_flow.js
# join flow fake socket and QR wiring: ok

python3 -B scripts/test_pk_relay.py
# Ran 9 tests in 3.191s
# OK

node scripts/test_decisions_frozen.js
# test_decisions_frozen: 9/9 checks passed

git diff --check
# exit 0; no output
```

## Could not verify

- I did not perform a browser playthrough or a two-device relay session.
- The brief permits only its listed lock files, which exclude `scripts/pk_relay.py` and its test. The protocol and page receiver now define `host_side_choice`, but this task could not add the relay-server emission of that field. The main line must add or verify that compatible relay transport before treating host side choice as end-to-end verified.
- I made no commit, push, deployment, remote change, or secret access.
