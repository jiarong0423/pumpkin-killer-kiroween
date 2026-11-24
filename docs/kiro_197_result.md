# Kiro task 197 result

## What changed

- `index.html`
  - Shield Wall now uses the shared `KNIGHT_ZONE` (70 px), `SHIELD_WALL_COFFIN_HEIGHT` (18 px, the existing drawn coffin slab height), and `SHIELD_WALL_EXPIRES_AFTER_ATTACKS` (3).
  - Enemy trajectories must cross both the stored point's horizontal range and its 18 px-high coffin range. A high trajectory passes over the point.
  - Hunchback axe shots do not receive a Shield Wall block assignment. The runtime block check also tests the same height range and preserves `ultBoom` bypass.
- `shared/constants.json`, `scripts/test_constants_sync.py`, and `scripts/test_decisions_frozen.js`
  - Added and pinned `KNIGHT_ZONE`, `SHIELD_WALL_COFFIN_HEIGHT`, and `SHIELD_WALL_EXPIRES_AFTER_ATTACKS`. The sync test now checks 16 shared constants.
- `scripts/mcp_game_server.py`
  - Added Shield Wall attack counting and `GameState._shield_wall_contains()`.
  - Each opposing projectile throw counts toward the three-attack expiry even if it misses, hits the fence, or is hunchback-bypassing. The third throw receives its normal block opportunity, then unused points expire.
  - The engine checks hunchback bypass before the height-aware Shield Wall intersection.
- `scripts/test_shield_wall.js` and `scripts/test_shield_wall.py`
  - Added matching focused cases for expiry, high-arc pass-over, hunchback bypass, two enemy throws counting separately, and a valid coffin intersection.
- `scripts/test_mcp_skills_ultimates.py`
  - Replaced the non-negative ultimate assertion with fixed-seed exact damages: skeleton 33, bat 36, hag 27.6, hunchback 52.5, reaper 42.9, bride 64.4, wizard 75.
  - The reaper test now pins the full normal resolution order, actual resolved record list, and unchanged skipped-white action count.
- `scripts/test_mutation_smoke.py`
  - Creates a temporary minimal repository copy under the system temporary directory for every mutation. It never edits a project source file.
  - It confirms matching tests reject mutations to the ultimate multiplier, Shield Wall expiry, burn turns, lifesteal share, and reaper hit half-width.
- `scripts/e2e_local.py` and `scripts/test_e2e_local.py`
  - Added a subprocess relay harness that creates a room through the Python relay protocol, starts two `ConnectedRelay` clients (the implementation used by `mcp_stdio_server.py --connect`), sends actions, compares round hashes, and checks seat views for private item-slot fields.

## Commands run and real last lines

```sh
python3 -B scripts/test_mcp_game.py
python3 -B scripts/test_mcp_stdio.py
python3 -B scripts/test_mcp_skills_ultimates.py
python3 -B scripts/test_shield_wall.py
python3 -B scripts/test_constants_sync.py
python3 -B scripts/test_mutation_smoke.py
git diff --check
```

```text
Ran 29 tests in 2.447s

OK

Ran 6 tests in 0.003s

OK

Ran 5 tests in 0.002s

OK
OK: shared/constants.json matches index.html for all 16 constants and adaptive-level tables.
MUTATION FAIL DETECTED: ultimate multiplier
MUTATION FAIL DETECTED: shield wall expiry
MUTATION FAIL DETECTED: burn turns
MUTATION FAIL DETECTED: lifesteal share
MUTATION FAIL DETECTED: reaper hit half-width
test_mutation_smoke: 5/5 mutations detected
```

```sh
node scripts/test_shield_wall.js
node scripts/test_decisions_frozen.js
node scripts/test_knight_ult.js
node scripts/test_ultimate.js
node scripts/test_ultimate_fx.js
node scripts/test_page_parses.js
```

```text
test_shield_wall: all page and rule parity cases passed
test_decisions_frozen: 9/9 checks passed
test_knight_ult: all 13 tests passed
test_ultimate: all 24 tests passed
test_ultimate_fx: all 13 tests passed
test_page_parses: 2 inline scripts and every js/*.js parse
```

```sh
node scripts/test_ui_settings.js
node scripts/test_phone_layout.js
node scripts/test_i18n.js
node scripts/test_layout_property.mjs
```

```text
test_ui_settings: 7/7 checks passed
test_phone_layout: 7/7 checks passed
26 passed, 0 failed (254 keys per language)
test_layout_property: 200 seeded landscape viewports passed
```

## Mutation table

| Temporary mutation | Matching test | Result |
| --- | --- | --- |
| Skeleton ultimate multiplier `1.5 / 3` → `1.4 / 3` | `test_mcp_skills_ultimates.py` | detected |
| Shield Wall expiry 3 → 2 | `test_shield_wall.py` | detected |
| Reaper burn turns 3 → 2 | `test_mcp_game.py` | detected |
| Page lifesteal share 0.05 → 0.06 | `test_decisions_frozen.js` | detected |
| Reaper hit half-width 57 → 58 | `test_mcp_game.py` | detected |

## What I could not verify

`python3 -B scripts/test_e2e_local.py` was run against a real loopback relay subprocess and failed. This is not a sandbox socket denial. The first full red/white exchange completes, but the existing relay increments relay round/phase after a white end-turn while the connected MCP engine remains on its prior round. A later red action is rejected by the relay as `stale_or_out_of_turn`; the harness reports the outstanding action was not acknowledged or judged.

The task's touch list does not allow changing `scripts/pk_relay.py` or `scripts/mcp_stdio_server.py`, which own that round-number/phase mismatch. I left those files unchanged. The owner/main line should run the reproducer in a terminal:

```sh
python3 -B scripts/test_e2e_local.py
```

It currently fails for the protocol mismatch above, so I do not claim the three-round E2E check passed. I also did not run an unrelated full `scripts/test_*.js` / socket-free Python sweep.
