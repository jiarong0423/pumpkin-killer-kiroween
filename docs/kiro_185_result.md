# Kiro task 185 result

## What changed

- `scripts/mcp_game_server.py`
  - Extended `GameState.submit_throw()` and added `set_knight_wall()`.
  - Added `_resolve_throw()` so normal, double, heavy, and ultimate projectile resolution share the same fixed-step ballistic path.
  - Added ultimate damage/status paths for skeleton, wizard, bat, reaper, bride, hunchback, and hag; added Shield Wall interception storage for knight.
  - Added deterministic nun stun selection through `determinism_py.nun_stun_pick()`.
  - Added the necromancer skipped-turn status and made `resolve_round()` skip the marked unit.
- `scripts/mcp_stdio_server.py`
  - Added public per-side `skills_remaining`, `ultimate_energy`, and Shield Wall remaining-point metadata.
  - Added `Session._do_skill()` and `Session._do_ultimate()`.
  - `submit_action` now accepts `{type:"skill", skill:"heal"|"double"|"heavy"}` and `{type:"ultimate", ...}`.
  - Heal restores up to 35 HP without using the unit action. Double queues a second 1.04-power throw with `delay_seconds: 0.26`. Heavy applies a 1.5 damage scale. Each skill is once per side per match.
  - Only the Shield Wall owner view includes its point coordinates. Other seats see only `points_left`.
  - Extended the `submit_action` MCP schema and description.
- `shared/heroes.json`
  - Added per-hero ultimate metadata without changing existing hero combat values.
- `scripts/test_mcp_skills_ultimates.py`
  - Added coverage for one use and rejection of a second use of every skill, three direct-hit energy pips, all eight ultimates, private knight points, non-negative damage, necromancer skipped turn, and a seeded full match ending.
- `scripts/test_mcp_seats.py`
  - Kept the pre-skill K1 fixture comparison stable by explicitly removing newly public skill, energy, and Shield Wall metadata before comparing it.
- `docs/mcp_architecture_opus_20261115.md`
  - Updated the tool/action summary to list skills, ultimates, public energy, and private Shield Wall coordinates.

## Verification run

```sh
python3 -B scripts/test_mcp_skills_ultimates.py
```

Last lines:

```text
Ran 6 tests in 0.003s

OK
```

```sh
python3 -B scripts/test_mcp_game.py
```

Last lines:

```text
--- 9. Testing shared eight-hero table, launch offsets, statuses, and 1v1 ---
✅ Eight hero table / status / 1v1 mode Passed!
```

```sh
python3 -B scripts/test_mcp_stdio.py
```

Last lines:

```text
Ran 29 tests in 2.203s

OK
```

```sh
python3 -B scripts/test_mcp_seats.py
python3 -B scripts/test_mcp_turns.py
```

Last lines:

```text
Ran 6 tests in 0.003s

OK

Ran 5 tests in 0.002s

OK
```

```sh
python3 -B scripts/test_constants_sync.py
python3 -B scripts/test_heroes_sync.py
```

Last lines:

```text
OK: shared/constants.json matches index.html for all 13 constants and adaptive-level tables.
OK: shared/heroes.json matches index.html HERO_PROFILES for 8 heroes.
```

```sh
node scripts/test_particles.js
node scripts/test_ultimate.js
node scripts/test_ultimate_fx.js
node scripts/test_nun_ult.js
node scripts/test_boomerang.js
node scripts/test_knight_ult.js
node scripts/test_sound_wave.js
node scripts/test_hallucination.js
node scripts/test_determinism.js
python3 -B scripts/test_determinism_golden.py
```

Last lines:

```text
67/67 properties passed
test_ultimate: all 24 tests passed
test_ultimate_fx: all 13 tests passed
test_nun_ult: all 6 tests passed
test_boomerang: all 6 tests passed
test_knight_ult: all 13 tests passed
test_sound_wave: all 7 tests passed
test_hallucination: all 6 tests passed
test_determinism.js: 10000 seed property cases passed
test_determinism_golden.py: 10000 seed property cases passed
```

```sh
git diff --check
```

The command exited 0 with no output.

## What I could not verify

- I attempted the task-required all non-socket Python `test_*.py` sweep. The terminal permission request failed before it was answered, so that combined sweep did not run. The focused MCP, ultimate, deterministic, hero-sync, constants, and particle checks above did run.
- I did not run every unrelated Node `test_*.js` file; the listed ultimate/status and particle files are the touched-area checks.

## Differences from the page

- The page gives the skeleton trio small velocity variation and a 5-percent next-javelin bonus. The engine resolves three same-path damage contacts at the page total multiplier, without those presentation-dependent variations.
- The page hunchback boomerang pierces every enemy on the full outbound polyline. The engine resolves the first ballistic contact, then its 1.5x return contact. This matches a 1v1 match but not a multi-target outbound pierce.
- The page nun cross can visit up to three targets with two contacts each. The engine resolves two contacts on the first direct target and chooses its stun through the shared deterministic function.
- The page Shield Wall expires after three enemy attacks and displays its short owner-only block reveal. The engine stores three private points and consumes a point on a horizontal crossing, but does not yet apply the page's three-enemy-attack expiry or reveal timing.
- The page’s wizard fire presentation spans a wider visual strip. The engine applies the required 100/75/50 damage bands at 70/140/210 px and preserves the normal shell contact on a direct hit.
