# Kiro task 193 result

## What changed

- `scripts/mcp_game_server.py`
  - `GameState`, `_hero_choices`, and `seeded_spawn_positions` now accept 1, 2, 3, or 4 units per side.
  - Default hero rosters take the first N entries of `DEFAULT_RED_HEROES` and `DEFAULT_WHITE_HEROES`. A string remains valid only for 1v1; custom team rosters must be lists of exactly N known ids.
  - Spawn positions use `determinism_py.start_x` as their only seeded placement source, then assign a 120 px-clear formation within each page movement zone. The engine CLI and its legacy JSON-RPC `set_match_mode` accept the new unit counts and hero lists.
- `scripts/mcp_stdio_server.py`
  - `TrackedGameState`, `Session`, relay resets, and the stdio CLI carry `units`, `hero_red`, and `hero_white`.
  - `Session._active_team`, `_active_unit`, and `_advance_active_unit` enforce one active unit per team phase, rotate in unit-id order, skip dead units, and freeze the other units.
  - Added read-only `get_roster`, which returns `units_per_side`, the red/white unit ids, and the calling seat’s existing `{kind, team, units[]}` data.
  - Added a public `round_hash` derived without exposing the match seed.
  - Fixed `ConnectedRelay._receive` / `_apply_judge` so an action acknowledgement or judge result arriving in either order cannot leave a pending throw in the round hash.
- `scripts/pk_mcp_health.py` accepts `--units 1|2|3|4` and checks the seven-tool list.
- `scripts/test_mcp_units.py` adds the required 4 × 50 seeded-match matrix. It checks terminal resolution, non-negative damage, 120 px team spacing, frozen/dead-unit behavior, seat roster ownership, common public fields, and round-hash agreement.
- Updated existing MCP engine, stdio, seat, turn, skills/ultimates, health, and allowlist tests for the active-unit turn rule and variable team sizes.
- `scripts/mcp_referee_baseline_145.json` was regenerated. It cannot remain byte-identical because the required deterministic 120 px formation replaces the old random, overlapping 4v4 starts. The resulting launch positions change the fixture’s contacts, wind progression, and round hash. This is the written reason for the baseline update.
- `docs/mcp_tool_allowlist.json` and `scripts/make_mcp_allowlist.py` pin `get_roster` as read-only. The allowlist also repins the already-live `submit_action` description: `git log -3 -- docs/mcp_tool_allowlist.json` showed only the earlier task-161 pin, while the live tool description had later skill/ultimate wording. Updating the one pin document was smaller and safer than reverting live behavior. No configured auto-approval or pk-player permission was widened.

## Verification commands and real last lines

```sh
python3 -B scripts/test_mcp_game.py
```

```text
--- 9. Testing shared eight-hero table, launch offsets, statuses, and 1v1 ---
✅ Eight hero table / status / 1v1 mode Passed!
```

```sh
python3 -B scripts/test_mcp_stdio.py
python3 -B scripts/test_mcp_seats.py
python3 -B scripts/test_mcp_turns.py
python3 -B scripts/test_mcp_skills_ultimates.py
python3 -B scripts/test_mcp_units.py
```

```text
Ran 29 tests in 2.512s

OK

Ran 6 tests in 0.005s

OK

Ran 5 tests in 0.007s

OK

Ran 6 tests in 0.006s

OK

Ran 2 tests in 0.251s

OK
```

```sh
python3 -B scripts/test_mcp_allowlist.py
python3 -B scripts/test_pk_mcp_health.py
```

```text
Ran 4 tests in 1.150s

OK
OK

Ran 4 tests in 10.833s

OK
```

```sh
python3 -B scripts/test_mcp_connect.py
python3 -B scripts/test_mcp_connect_weather.py
python3 -B scripts/test_pk_headless_match.py
```

```text
Ran 5 tests in 0.923s

OK

Ran 1 test in 0.339s

OK

Ran 4 tests in 0.209s

OK
```

```sh
python3 -B scripts/pk_mcp_health.py --units 1
python3 -B scripts/pk_mcp_health.py --units 2
python3 -B scripts/pk_mcp_health.py --units 3
python3 -B scripts/pk_mcp_health.py --units 4
```

Each run ended with:

```text
ok get_public_state
ok stdin close
PASS
```

```sh
python3 -B scripts/test_determinism_golden.py
git diff --check
```

```text
test_determinism_golden.py: 1040 golden vectors passed
test_determinism_golden.py: 10000 seed property cases passed
```

`git diff --check` exited 0 with no output.

## Unit-count matrix

| Units per side | Seeded matches | Result |
| --- | ---: | --- |
| 1 | 50 | passed |
| 2 | 50 | passed |
| 3 | 50 | passed |
| 4 | 50 | passed |

## What I could not complete or verify

- The host denied writes to `.kiro/agents/pk-player.json` and `.kiro/powers/pumpkin-killer-seat/skills/play/SKILL.md`. I therefore could not update their wording from 1v1 to 1–4 units per side. I did not bypass that file-scope denial. Those files keep their existing tool lists, as required by the brief’s “no new tools” rule.
- Local subprocess and loopback-socket checks were available and ran. No socket test needs the owner’s terminal based on this session. The ten-run relay stress command was denied before it started, so I do not claim that stress run passed.
- The main line must still rerun and record these checks in `docs/kiro_verified.json`.
