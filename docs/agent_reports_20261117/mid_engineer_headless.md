# mid_engineer_headless (2026-11-17)

New file only: scripts/sim_team_headless.py (stdlib, `python3 -B`, log logs_local/sim_team_headless.log, exit 1 on any failed check). No existing file touched, nothing committed.

## Driving the engine without sockets
`mcp_stdio_server.Session(seed, units, hero_red, hero_white, clock=lambda: 0.0, human_turn_seconds=0, turn_seconds=100)`, then `session.call("submit_action"/"end_turn", ..., session.seats["red"|"white"])`; red = human phase, white = agent phase. Active unit via `session._active_unit(team)` (same as test_mcp_units.py). Reference re-trace of every projectile is independent of the engine's target selection.

## Commands (last lines)
- `python3 -B scripts/sim_team_headless.py` -> exit 1, `failures 84`, `RESULT FAIL` (50 s). 2v2 all checks pass; 3v3 rotation fails.
- `cd scripts; python3 -B test_mcp_game.py` -> exit 0, "Eight hero table / status / 1v1 mode Passed!"
- `python3 -B test_mcp_units.py` -> exit 0, Ran 2 tests OK. `test_mcp_turns.py` -> exit 0, Ran 5 tests OK.
- `python3 -B test_hit_radius.py` -> exit 0, Ran 4 tests OK (19 s, uses node).

## Stats (50 seeded matches each, seeds 20263117.. / 20264117.., random heroes per seed, plain throws, noisy bisection aim)
| size | rounds min/mean/max | throws | hero hits/throw | wall/throw | paths crossing 2+ enemies | wins red/white/draw |
|---|---|---|---|---|---|---|
| 2v2 | 11 / 17.3 / 26 | 1670 | 0.708 | 0.119 | 3 | 24 / 26 / 0 |
| 3v3 | 17 / 24.2 / 32 | 2340 | 0.757 | 0.080 | 250 | 30 / 20 / 0 |
Guard (150 rounds) never hit. Checks: first_hit 11228 pass / 0 fail; crossing (constructed, 80 shots per N and side, nearest alive and nearest dead variants) 1284 / 0; winner 4442 / 0; frozen 2867 / 0; throw_log 8152 / 0; rotation 8234 / 50 fail; no_repeat 2833 / 34 fail. All failures are 3v3 only.

## Mismatch with the page rules (R2.1 "fixed id order, skip dead")
1. scripts/mcp_stdio_server.py:400-407 `_active_unit` picks `eligible[active_unit_index % len(eligible)]` over the LIVING list, and `_advance_active_unit` (409-411) only adds 1. When a unit dies the list shrinks and the modulus shifts, so the order breaks: 3v3 had 50 off-order turns of 2416 (34 with the previous unit still alive, 16 with it dead) and 34 turns where the same unit acts twice in a row while a teammate lives (e.g. seed 20264118 round 9: red_1 dead, red_2 acts, then red_2 again, red_3 skipped). 2v2 is unaffected (one survivor). Likely fix (not applied): store the last active unit id per team and take the next living id after it, as js/team_battle.js:11-16 `nextActive` does.
2. js/team_battle.js:11-16 itself: if the current unit is dead (index -1) it returns the FIRST living unit, not the next after the dead one; the engine and the page differ again in that case. Spec text is ambiguous; the sim uses "next living id after the previous active id".
3. Simultaneous-step ties: mcp_game_server.py:463-465 takes the first candidate in id order (page index.html:3220 `foes.find` does the same). In 26 3v3 throws two boxes were first touched in the same 1/60 s step; in 6 the engine picked the farther one (log WARNING "tie at one step"). Same in page and engine, so reported only, not counted as failure.

## Not verified
- Page (index.html) behaviour itself was not run; only its code was read.
- Only plain throws: no ultimates, skills, defend, move, shields, weather, relay mode, human timers. Reaper `skip` turns never occurred (skipped turns 0).
- The sim's flight reference copies the engine's step formula (wind push 0.9375 x page values), so a physics error shared by both would not show.
- `GameState.resolve_round` (not Session) auto-throws for every "subagent" unit (mcp_game_server.py:553-554); I used TrackedGameState for the constructed shots to avoid that.
- Draw outcome never occurred, so only the "winner set iff a team is down" check covers it.
