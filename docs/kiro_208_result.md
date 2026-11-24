# Kiro task 208 result

## What changed

- `index.html`: added the read-only `?seed=` replay hook through `fixedMatchSeed` and `newMatchSeed`; invalid or absent values retain the ordinary random-match seed.
- `scripts/record_match_transcript.mjs`: added a CDP browser transcript harness. It records three fixed-seed, six-round N=1 scripted matches after each resolved throw and round, including unit coordinates, HP, statuses, turn, wind, weather, round hash, visible combat text, energy, and item counts. The harness records twice per run and rejects a difference.
- `docs/transcripts/n1_baseline.json` and `docs/transcripts/n1_baseline.sha256`: recorded the pre-refactor baseline. SHA-256: `40be5ea22bd157b8da6ed5e0d8c297fc12f31cef2f10daf7354b934ae9911646`.
- `index.html`: represented N=1 as `teams = { left: [player], right: [ai] }`. Added `unitsOf`, `aliveUnits`, `activeUnit`, and per-unit state accessors for angle, item, shield, and energy. Existing `player` and `ai` objects remain the first units in their respective teams. Team-backed state adapters retain existing N=1 reads and writes for ammunition, energy, ultimate state, fire state, and the supply item.
- `js/team_battle.js`: added pure `unitsOf`, `activeUnit`, and `unitState` helpers.
- `scripts/test_team_battle.js`: added N=1 team-accessor assertions.
- `.kiro/specs/team-battle/tasks.md`: checked step 1 because the post-refactor transcript is byte-identical to the baseline.

## Determinism handling

The page has match-affecting `Math.random()` calls for initial hero selection, later wind, dice, AI view/aim/skill/move choices, shield bounce count, and combat random effects. It also has clock reads for charge and presentation effects. The transcript harness installs a seeded `Math.random`, fixed `Date.now` and `Performance.prototype.now`, and disables the animation-frame loop before the page script loads. It then advances only the page's fixed `PHYSICS_STEP` manually. These overrides live in the harness, not the page.

## Verification commands and last lines

```text
node scripts/record_match_transcript.mjs --write-baseline
record_match_transcript: wrote deterministic N=1 baseline (40be5ea22bd157b8da6ed5e0d8c297fc12f31cef2f10daf7354b934ae9911646)
record_match_transcript: two recordings are byte-identical

node scripts/record_match_transcript.mjs && node scripts/test_team_battle.js && node scripts/test_page_parses.js
record_match_transcript: baseline matches (40be5ea22bd157b8da6ed5e0d8c297fc12f31cef2f10daf7354b934ae9911646)
record_match_transcript: two recordings are byte-identical
test_team_battle: rotation, alive lists, winners, N=1..4 slots, and N=1 accessors passed
test_page_parses: 2 inline scripts and every js/*.js parse

for test in scripts/test_*.js; do node "$test" || exit $?; done
All `scripts/test_*.js` runners completed successfully. The sweep included:
test_orientation_frozen: 5/5 checks passed
test_sim_balance: all 29 tests passed
test_team_battle: rotation, alive lists, winners, N=1..4 slots, and N=1 accessors passed
test_ui_settings: 7/7 checks passed

python3 -B scripts/test_mcp_stdio.py && python3 -B scripts/test_constants_sync.py && python3 -B scripts/test_mcp_game.py
Ran 29 tests in 3.093s
OK
OK: shared/constants.json matches index.html for all 16 constants and adaptive-level tables.
🎉 ALL NEW POSITION / WALL TESTS PASSED!

🎉 ALL MCP GAME ENGINE TESTS PASSED!
```

The post-refactor transcript SHA-256 is unchanged:

```text
40be5ea22bd157b8da6ed5e0d8c297fc12f31cef2f10daf7354b934ae9911646
```

## Not verified / failures outside this task

- `node scripts/test_layout_property.mjs` failed at its generated `882x381` viewport because the opponent name plate intersects the right control buttons. The exact last error was: `HUD intersections: opponent-name-plate / sound-btn, opponent-name-plate / reset-btn, opponent-name-plate / lang-btn, opponent-name-plate / settings-btn, opponent-name-plate / help-btn`. This task made no layout or CSS changes, so I did not broaden its scope to fix the existing layout-property failure.
- The socket-free Python sweep stopped at the existing `scripts/test_mcp_seats.py` fixture mismatch: `test_referee_matches_the_pre_seat_baseline` failed. I did not touch MCP files or its baseline fixture because they are outside this task's lock.
- Socket-dependent runners were not run: `scripts/test_e2e_local.py`, `scripts/test_pk_relay.py`, `scripts/test_smoke_deployed.py`, and `scripts/test_smoke_url.py`.
- I did not conduct a physical-phone visual test. The transcript harness ran successfully in headless Chrome.
- The main line must re-run all checks and record independent verification in `docs/kiro_verified.json`.

## Final rerun after the harness clock stub

```text
node scripts/record_match_transcript.mjs && node scripts/record_match_transcript.mjs && node scripts/record_match_transcript.mjs
record_match_transcript: baseline matches (40be5ea22bd157b8da6ed5e0d8c297fc12f31cef2f10daf7354b934ae9911646)
record_match_transcript: two recordings are byte-identical

node scripts/test_team_battle.js && node scripts/test_page_parses.js && git diff --check
test_team_battle: rotation, alive lists, winners, N=1..4 slots, and N=1 accessors passed
test_page_parses: 2 inline scripts and every js/*.js parse
```
