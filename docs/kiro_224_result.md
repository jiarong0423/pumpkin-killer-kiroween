# Kiro task 224 result

## What changed

- `.kiro/specs/team-battle/requirements.md` and `tasks.md`: capped the documented product at 1v1 through 3v3, made N = 3 the final stage, retained the 2026-11-25 checkpoint, and recorded that the engine formerly accepted four units per side. No `design.md` existed in `.kiro/specs/team-battle/` at task start, so I did not create an otherwise empty specification file.
- `(not published)`, `.kiro/powers/pumpkin-killer-seat/skills/play/SKILL.md`, `.kiro/agents/pk-player.json`, `docs/relay_protocol_20261115.md`, `docs/mcp_architecture_opus_20261115.md`, `docs/OFFICIAL_VS_GAP_20261116.md`, and `docs/TASK_QUEUE_20261116.md`: replaced active 4v4 and 1-to-4 wording with 3v3 and 1-to-3 wording. Each relevant document states that the engine formerly accepted four units per side.
- `scripts/mcp_game_server.py`: `GameState` now defaults to and accepts only 1, 2, or 3 units. Invalid values, including 4, raise exactly `ValueError("units must be 1, 2 or 3")`. The default red and white hero rosters now have three entries. The CLI defaults to 3 and passes invalid values to this validation.
- `scripts/mcp_stdio_server.py`: `TrackedGameState`, `Session`, and the `--units` CLI default now use 3. The stdio CLI passes 4 to the engine validation, which raises the same clear `ValueError`.
- `scripts/pk_mcp_health.py`: health-check command construction and its CLI now default to 3 units and expose only 1, 2, and 3.
- `scripts/pk_relay.py`: added `MAX_UNITS_PER_TEAM = 3`; `_parse_units` rejects a four-element list through the existing `invalid_units` error path. `MAX_TEAM_SEATS` remains 4 because it counts connected seats, not units in a team.
- `js/team_battle.js`: `slots` accepts only N = 1 through 3 and raises `RangeError("count must be 1..3")` otherwise.
- `scripts/test_mcp_game.py`, `test_mcp_stdio.py`, `test_mcp_units.py`, `test_mcp_turns.py`, `test_team_battle.js`, `test_pk_relay.py`, and `eval_agent_learning.py`: changed fourth-unit fixtures to `red_3` or the last unit of the N = 3 team. `test_mcp_units.py` verifies engine and stdio-session rejection of 4. `test_pk_relay.py` sends a four-item unit list over a real local socket and expects `invalid_units`.
- `scripts/pk_headless_match.py`: changed the short-match fixture from `red_4` to `red_3`. This was necessary for the existing headless regression test to remain runnable after the cap.
- `scripts/mcp_referee_baseline_145.json`: regenerated because its default-seed match formerly used four units per side. The seed, actions, and baseline-generation procedure are unchanged; only the three-unit roster and the resulting deterministic state changed.

## Referee baseline start positions

The prior fixture was a four-unit match:

```text
red_1=533.3333333333333, red_2=386.66666666666663, red_3=240.0, red_4=680.0
white_1=1240.0, white_2=1386.6666666666667, white_3=1680.0, white_4=1533.3333333333333
```

The regenerated seed-145 three-unit match is:

```text
red_1=680.0, red_2=460.0, red_3=240.0
white_1=1240.0, white_2=1460.0, white_3=1680.0
```

The baseline was generated with the existing `test_mcp_seats.make_session()` and `play_round()` functions, the same seed 145, and the same two actions. `scripts/test_mcp_seats.py` now passes all six checks. The source diff changes only unit-count validation/defaults, default roster length, and unit-ID fixtures; it does not change ballistic integration, wind, wall, shield, or round-resolution code. The changed `red_1` starting position naturally changes that baseline throw from a hero hit to a central-wall hit.

## Verification commands and last lines

Pre-change count: `scripts/test_mcp_game.py` completed its nine printed checks; `test_mcp_units.py` ran 2 tests and `test_mcp_stdio.py` ran 29 tests. The initial chain then reached `test_mcp_seats.py`, where 5 of 6 tests passed and the pre-seat baseline mismatch failed. `node scripts/test_team_battle.js` passed separately. The initial chain stopped at that known baseline mismatch, so it did not yield a complete pre-change suite total.

Post-change count: 78 of 78 named unittest cases passed: 2 units, 29 stdio, 6 seats, 5 turns, 6 skills/ultimates, 6 agent levels, 4 allowlist, 4 headless, 4 health, and 12 relay cases. In addition, the nine `test_mcp_game.py` checks, the history-only evaluation, and the TeamBattle Node test passed.

```text
python3 -B scripts/mcp_game_server.py --cli --units 4
ValueError: units must be 1, 2 or 3
(exit 1 expected)

python3 -B scripts/mcp_stdio_server.py --units 4
ValueError: units must be 1, 2 or 3
(exit 1 expected)

python3 -B scripts/test_mcp_game.py && python3 -B scripts/test_mcp_units.py && python3 -B scripts/test_mcp_stdio.py && python3 -B scripts/test_mcp_seats.py && python3 -B scripts/test_mcp_turns.py && python3 -B scripts/test_mcp_skills_ultimates.py && python3 -B scripts/test_agent_levels.py && python3 -B scripts/test_mcp_allowlist.py && python3 -B scripts/eval_agent_learning.py && node scripts/test_team_battle.js
Ran 4 tests in 0.310s
OK
OK
OK: error fell by 60%
test_team_battle: rotation, alive lists, winners, N=1..3 slots, and N=1 accessors passed

python3 -B scripts/test_pk_headless_match.py && python3 -B scripts/test_pk_mcp_health.py
Ran 4 tests in 10.405s
OK

python3 -B scripts/test_pk_relay.py
Ran 12 tests in 2.518s
OK

git diff --check && python3 -B -m json.tool .kiro/agents/pk-player.json >/dev/null && python3 -B -m json.tool scripts/mcp_referee_baseline_145.json >/dev/null
(exit 0)
```

## What I could not verify

- I did not run a real browser host-and-guest relay session. The local socket integration test ran successfully. For an owner-device check, run `python3 -B scripts/test_pk_relay.py`; then run `python3 -B scripts/dev_server.py --with-relay`, join one room from two devices, and confirm normal 1v1 through 3v3 room behavior.
- I did not modify `index.html`, CSS, or assets, as required by the task lock. The main line must rerun the checks and record independent verification in `docs/kiro_verified.json`.
- I did not commit, push, deploy, access secrets, or change remotes.
