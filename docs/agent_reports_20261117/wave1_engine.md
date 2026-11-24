# Wave 1 engine report, 2026-11-17 (engine engineer; no git write, page and shared files untouched)

## What changed (functions)
- `scripts/mcp_game_server.py`
  - `_setup_teams`: max and start hp = `team_tuning_py.team_max_hp(hp, dmg, units_per_side)` (1 unit: the table value, int/float types unchanged).
  - `_apply_hit`: after weather and crit, damage x `ramp_multiplier(self.round_num, n)` rounded to 0.1 (round counter as the engine counts it: the round being resolved); new arg `apply_status`; knockback goes through `clamp_knockback`.
  - `resolve_round`: after the counter increments, if no kill winner and `round_num > round_cap(n)` the match ends, winner from `cap_winner` (left=red, right=white), result carries `winner_reason: "round_cap"` (key absent otherwise, so 1v1 output is unchanged). Cap round = the cap-th resolved round (counter cap+1), same as the page (`roundNum > roundCap` after `roundNum++`).
  - New: `living_teammates`, `step_back_move` (page loop: 20 slices from the target back to the start, first spot >= 120 px from every living teammate, else stay), `clamp_knockback` (stops at the first living teammate in the push direction at 120 px, never passes it, never goes backwards), `wave_multiplier` (steps 40/75/105 = 100/75/50), constants `BLAST_RADIUS 234`, `BLAST_MULTIPLIER 1.5`, `SWARM_*`, `MIN_TEAMMATE_GAP 120`.
  - `_resolve_throw`: wizard ultimate = shell contact hit + flat 1.5 x on every living enemy within 234 px of the impact (no steps, no crit, no poison), nearest first in `hit_target`, living units only (fixes the dead-bystander listing); the blast also fires when the shell stops on the fence, a floating shield or a Shield Wall point (page: `hit && p.ultBlast`). Bride shots (normal and ultimate): touched unit and every other living enemy within 105 px of the wave centre take the stepped 100/75/50 percent of their own distance; ultimate swarm (touched unit alive and centre < 55 px from it) hits every living enemy at 1.3 x, no status.
- `scripts/mcp_stdio_server.py`: `Session.winner_reason` (public state, round summary, relay reset; key only when set); `_do_move` uses `step_back_move`, result adds `blocked_by_teammate` only when it fired, `blocked_by_edge` now means the zone edge only.
- `scripts/sim_team_headless.py`: see Simulation. `scripts/test_mcp_team_rules.py`: new, 21 tests (hp scale, ramp, cap and tie-break order, 1v1 neutral, wave steps/splash/swarm, blast 234/ramp/dead/shield, move step-back/stay/dead mate/1v1, knockback clamp cases).

## Parity decisions taken from the page (index.html read, never edited)
- Wizard blast: page is flat 1.5 x normal inside 234 px (`ultBlast`), no steps. Engine had bands 70/140/210 = 1.5/1.125/0.75 (the bands still sit in shared/heroes.json `ultimate.bands`, now unused by the engine; I cannot edit it).
- Bride/bat "swapped": NOT swapped. The engine bride swarm already equalled the page (precise hit < 55 px calls the swarm on every living enemy at any distance; the round-3 "40 of 40 far units hit" is that rule). The real gap was the page wave (area 105 px, stepped damage) which the engine lacked entirely; added. The bat ultimate (5 shuriken, 1.5 x / 5, touched unit) stays as is: the page throws 5 random-spread projectiles, the engine one deterministic volley on the touched unit.
- Tie rule: page sorts by `abs(p.x - a.x)` (projectile); engine `min(touched, key=abs(cur_x - x))` already did that. Confirmed, no code change.
- Move rule: copied exactly, including that the page loop only checks the end point, so a move can jump over a teammate (the page comment says it prevents swaps; it does not).
- Not aligned, undecided: weather. The page gives blast, swarm and ticks no weather multiplier; the engine passes them through `_weather_damage` (only when `weather_enabled`).

## Pins moved (why)
- `scripts/mcp_referee_baseline_145.json` regenerated: the default Session has 3 units, so hp/max_hp of 6 units and `round_hash` changed (verified by key diff: nothing else differs).
- `test_mcp_skills_ultimates.py`: bride ultimate 78.2 -> 69.7 (the fixture lands 40 to 75 px from the target: 75 percent wave 25.5 + swarm 44.2); heal test: bat max hp is 70 in a 3-unit team, so +52 from 40 heals 30 (the uncapped 52 case kept with max_hp 147).
- `test_mcp_stdio.py`: `test_move_uses_engine_die` accepts the teammate step-back; `test_move_zones_match_the_page` uses `units=1`.

## Tests (last lines, `cd scripts && python3 -B <t>.py`)
test_mcp_game "Eight hero table / status / 1v1 mode Passed!"; test_mcp_units 2 OK; test_mcp_turns 5 OK; test_mcp_seats 6 OK; test_mcp_skills_ultimates 6 OK; test_mcp_allowlist OK; test_mcp_stdio 29 OK; test_mcp_team_rules 21 OK; test_hit_radius 4 OK; test_team_tuning 4 OK. Also green: test_hit_report, test_pk_headless_match, test_shield_wall, test_heroes_sync, test_constants_sync, determinism and flight goldens, test_mutation_smoke. Socket tests (test_pk_relay 14 errors, test_mcp_connect, _weather) fail in the sandbox with "bind ... operation not permitted" (known, not run here).

## Simulation (100 matches per size, seeds 20261117+; moves 35 percent per turn; logs in logs_local/)
Command: `PK_SIM_MATCHES=100 [PK_SIM_NOISE=n] [PK_SIM_LOG=path] python3 -B scripts/sim_team_headless.py`. RESULT PASS, 0 failed checks in all three runs (about 100 s each).
| bot power noise | 2v2 rounds mean / p10 / p90 / max, in 8-13 | 3v3 same | ended by cap |
|---|---|---|---|
| 1.6 (expert, default) | 9.8 / 8 / 12 / 14, 94% | 11.2 / 9 / 13 / 15, 92% | 0 / 0 |
| 5 (decent) | 11.9 / 9 / 14 / 17, 74% | 12.8 / 10 / 15 / 20, 66% | 0 / 1 |
| 9 (sloppy) | 14.2 / 11 / 18 / 18, 43% | 14.9 / 12 / 18 / 20, 25% | 8 / 1 |
Target 8-13 met for expert and decent bots; sloppy play reaches the cap (8 of 100 in 2v2). Checks added: hp_scale, ramp (independent formula, 2,200 ramped hits), wave, cap, cap_len (no match longer than the cap; stronger than cap+1), gap (min teammate gap seen 120.0 px over 5,269 moves and 904 knockbacks), tie_nearest (tie metric now projectile-nearest: 0 wrong of 222 ties over the three runs; the old shooter metric would have flagged 4 to 42 per size and run). Mutation check in a scratch copy: removing the knockback clamp, the move step-back, the ramp, the tie rule, the wave splash or the cap each fails its check.

## Could not decide / for the owner
- Red won 38 of 100 in 2v2 (expert and decent runs), 3v3 55/45: possible first-mover or order effect, not investigated (n small).
- Heal is flat +52: with team max hp 70 (bat, 3v3) that is 74 percent of a unit; designer call.
- heroes.json `ultimate.bands` for the wizard and page help text describe the old bands; owners of those files should align.
- Page and engine agree on cap timing and ramp rounding by reading only; no shared golden yet (round 3 suggestion).
