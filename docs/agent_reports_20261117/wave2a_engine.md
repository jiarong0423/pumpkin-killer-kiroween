# Wave 2a engine report, 2026-11-17 (comeback pack B1 B2 B3 with the 2.3 cap; team matches only; no git write)

## What changed
- `scripts/mcp_game_server.py`: new `pity` per-team counters (start 0; a relay reset builds a new engine). `_apply_hit` for 2 or 3 units: damage = `comeback_py.final_damage(base x weather x ramp, own_share, enemy_share, pity)`, one rounding at the end; shares are read at the moment of each hit, so the second victim of one blast sees the first victim's loss. `final_damage` already holds the cap `min(2.3, underdog x (1 + pity))`; the engine never multiplies the two itself, so direct hits, blast, wave splash, swarm and ultimates all go through it. `_resolve_throw` snapshots the team's pity at throw start (all hits of one throw share it) and at the end sets it to 0 on a direct hit (`hit_type == "hero"`) or adds 1 on every other throw (plain miss, near miss, fence or shield stop). New: `team_share`, `underdog_bonus`, `hit_multiplier` (the real combined factor after the cap), `_near_miss`.
- B1 near miss: ground landing, no direct hit: the nearest living enemy by box-edge distance (`max(0, |x - ux| - halfWidth)`, 70, reaper 57) takes `near_miss_damage(base, e)`; no crit, no status, no pip (hit_type stays "ground", so Session energy is untouched). Throw record gets `near_miss {target, damage, edge}` (also in `get_history` and the round summary) only in team matches.
- `scripts/mcp_stdio_server.py`: `Session.comeback_view()` adds to `get_public_state` and the round summary, team matches only: `pity {team: {misses, bonus}}`, `underdog_bonus {team: fraction}` (underdog alone), `comeback_multiplier {team: real factor of its next hit after the 2.3 cap}`; `public_throw` and the throw log carry `near_miss`.
- `scripts/sim_team_headless.py`: checks `near_miss`, `pity`, `underdog` (independent formula with the cap, factor never below 1 nor above 2.3, state keys), `one_unit` (PK_SIM_ONE=20 1v1 matches: no team keys, no near miss, table hp, no ramp, no cap); `PK_SIM_MODE=gap` prints the skill-gap table (same seeds, sides swapped). Mutants tried in a scratch copy (pity never reset, underdog off by 0.05) fail their checks.
- `scripts/test_mcp_team_rules.py`: 11 new tests (near miss value, 450 px limit, dead units, kill without pip, none on a direct hit, pity growth/reset/cap, blocked throw = miss, underdog both ways and cap 2x, area effects with the 2.3 cap, N = 1 untouched, public keys incl. `comeback_multiplier` 2.3).

## Tests (last lines, `cd scripts && python3 -B <t>.py`)
test_mcp_game "1v1 mode Passed!"; test_mcp_units 2 OK; test_mcp_turns 5 OK; test_mcp_seats 6 OK; test_mcp_skills_ultimates 6 OK; test_mcp_allowlist OK; test_mcp_stdio 29 OK; test_mcp_team_rules 32 OK; test_hit_radius 4 OK; test_team_tuning 4 OK; also test_hit_report, test_pk_headless_match, test_shield_wall OK. Sim, 100 matches per size, 0 failed checks at noise 1.6, 5 and 9.

## Skill gap (`PK_SIM_MODE=gap PK_SIM_MATCHES=300 python3 -B scripts/sim_team_headless.py`, with the 2.3 cap; 300 seeds x 2 sides = 600 matches per row)
| size | pair | weaker team wins | rounds mean / p10 / p90 | matches in 8-13 |
|---|---|---|---|---|
| 2v2 | expert 1.6 vs sloppy 9 | 26.8% | 10.7 / 9 / 13 | 98% |
| 2v2 | decent 5 vs sloppy 9 | 35.2% | 11.1 / 9 / 13 | 92% |
| 2v2 | expert 1.6 vs decent 5 | 41.5% | 10.5 / 8 / 12 | 97% |
| 3v3 | expert 1.6 vs sloppy 9 | 25.0% | 11.3 / 10 / 13 | 95% |
| 3v3 | decent 5 vs sloppy 9 | 33.7% | 11.7 / 10 / 14 | 88% |
| 3v3 | expert 1.6 vs decent 5 | 39.8% | 11.1 / 9 / 13 | 98% |
Sloppy-vs-expert 26.8 and 25.0 percent sit inside the 25 to 32 target with the cap; no match reached the round cap; 88 to 98 percent of matches end in 8 to 13 rounds (target 64 to 89). Before the cap (200-match run) it was 31.0 and 26.0. Standalone length (noise 1.6 / 5 / 9, 2v2 and 3v3 mean): 10.3/10.9, 10.9/11.2, 11.8/12.5 rounds; the 2.3 cap cut 45 to 156 hit stacks per 100 matches.

## Pins moved (why)
- `mcp_referee_baseline_145.json` regenerated twice: hp_scale now 0.80 / 0.55 (max_hp, hp, round_hash), then the new throw key `near_miss` and state keys `pity`, `underdog_bonus`, `comeback_multiplier` (the default Session has 3 units).
- `test_mcp_skills_ultimates.py` heal test: bat max hp in 3 units is 81 (147 x 0.55), +52 from 40 heals 41.

## Differs from, or not fixed by, the rule text in shared/comeback.json
- Near miss takes only `near_miss_damage(base, e)`: no weather, ramp, underdog or pity (literal reading; a near miss is not a direct hit). `base` = hero dmg x 0.85 if weak x the skill's damage scale; ultimates use the plain hero dmg.
- A wizard ground blast that damages someone counts as a direct hit for pity (engine `hit_type` "hero") and uses the charge; a blast that hits nobody can still produce a near miss. A shell stopped by the fence, a shield or a Shield Wall point is a miss with no near miss.
- Pity is read once per throw; the second throw of the double skill reads the updated counter.
- Underdog uses the shares at each hit, so within one area effect the later victims get a smaller bonus.
- Page and engine agree by reading only; there is no shared golden for near miss or pity yet.

## Update: 7-minute tuning (hp_scale 0.90 / 0.95, ramp from round 13, cap 24 / 28)
- `test_mcp_team_rules.py` and the heal test now read ramp start, per-round step, cap and hp scale through `team_tuning_py` (no hard-coded 8/9/18/20/81); the cap-winner test derives hp from `max_hp`. `mcp_referee_baseline_145.json` regenerated (hp, max_hp, round_hash, comeback values only, verified by key diff).
- Tests (`cd scripts`): test_mcp_game "1v1 mode Passed!"; test_mcp_units, _turns, _seats, _skills_ultimates, _allowlist, _stdio (29), _team_rules (32), test_hit_radius (4), test_team_tuning (4), test_hit_report, test_pk_headless_match, test_shield_wall all OK.
- Sim: the 8 to 13 target is informational now, band 0.5 x to 1.5 x of `EXPECTED_ROUNDS` (2v2 12.5, 3v3 17.0; edit in the sim when retuned); hard checks unchanged. `PK_SIM_MATCHES=100`, 0 failed checks: noise 1.6: 2v2 mean 11.7 rounds (p10 9, p90 14, max 15), 3v3 17.0 (15, 19, 21); noise 9: 13.5 (max 19) and 19.0 (max 25); no match hit the cap (24 / 28), 99 to 100 percent inside the band.
- Skill gap (100 seeds x 2 sides, sides swapped, 2.3 cap): sloppy beats expert 22.5% (2v2) and 22.5% (3v3), now below the 25 to 32 target (was 26.8 / 25.0 at the old hp scale); decent vs sloppy: weaker 36.5 / 33.0; expert vs decent: weaker 38.0 / 41.0. Rounds: 2v2 12.1 to 12.8, 3v3 17.2 to 18.1. Higher hp makes the weaker side less able to catch up; to bring it back toward 25 the underdog or pity strength would need to rise (not changed).

## Update: page and MCP bridge hash the same round (bridge side only; page and shared files untouched)
- `ConnectedRelay._hash_state` (`scripts/mcp_stdio_server.py`) now builds the page's `currentRoundHash` input. One unit per team: ids `left`/`right`, world x, y, hp, alive, public status words, wall hp, the round that just ended, phase `"throws:"` (in a room the page calls it from `resolveRound` after emptying `roundThrowNumbers`, so the throws part is empty), the match seed; wind is not in the canonical text. 2 or 3 units: every unit of both teams (dead kept), ids `left_i`/`right_i` via `world_unit_id`, `teamSize`, phase `round_end` (hooks doc item 4). The old inputs (`red_1`, relay team as phase) could never match a page.
- Also changed: `Session.reset_for_relay(seed, scene, units)`: on the relay `start` the bridge adopts the room's team size (the relay omits it for 1v1), so a default 3-unit `--units` bridge no longer meets a page at N = 1; heroes that do not fit are reset to defaults.
- New `scripts/test_mcp_hash_parity.py` (6 tests): it cuts the page's real `publicStatusWords` and `currentRoundHash` out of `index.html` and runs them in node with the real `js/round_hash.js` and `js/perspective.js`; 40 random states per size (N = 1, 2, 3, uneven hp, statuses, dead units, wall hp) from the red and the mirrored white seat give the same 8 hex as the bridge; mutating the bridge phase fails 4 of 6. Also an in-process relay check and a REAL-socket test (relay + bridge on red + page device on white, 1v1, bridge starts with 3 units): hashes equal, no `out_of_sync`.
- Last lines: test_mcp_hash_parity "Ran 6 tests ... OK"; test_mcp_connect, _connect_weather, test_e2e_local, test_pk_relay, test_round_hash (33 goldens) OK. I did not edit `scripts/e2e_local.py` (not my file); owner command for the socket check: `cd scripts && python3 -B test_mcp_hash_parity.py && python3 -B e2e_local.py`.
- Not proven: live status-tick timing. The page ticks poison/bleed/burn at round end before hashing, the engine ticks at each team's turn start, so a poisoned unit can still differ in a real match even though the recipe is equal; the first live page + MCP room with statuses will show it.
