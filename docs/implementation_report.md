# Implementation report: Kiro task 42

Date: 2026-11-09. Task brief: `docs/kiro_task_42.md`. Four modules were written from the specs and plans, each with a spec folder in `.kiro/specs/`. I did not touch `index.html` or any other file outside the list in the brief, did not use git, and did not create or download images. Everything below was run on this machine unless it says "not run".

## 0. Files

| New or changed | File |
|---|---|
| new | `js/ultimate.js`, `js/class_stats.js`, `scripts/sim_balance.js` |
| new | `scripts/test_ultimate.js`, `scripts/test_class_stats.js`, `scripts/test_sim_balance.js` |
| appended | `js/particles.js` (one block of 7 presets before `var PRESET_NAMES`, nothing else changed) |
| appended | `scripts/test_particles.js` (new properties in front of the runner block, old properties unchanged) |
| new | `.kiro/specs/ultimate-ledger/`, `.kiro/specs/class-stats/`, `.kiro/specs/weapon-effects/`, `.kiro/specs/balance-sim/` (each `requirements.md`, `design.md`, `tasks.md`, all boxes ticked) |
| new | this report |

Commands: the first shell attempts ("ls ...; wc ...", "node --version") and four `node -e ...` attempts returned "The permission request failed before it was answered" and did not run; I recorded that and did not work around it. `node scripts/test_*.js` and `node scripts/sim_balance.js ...` ran. The sha256 of the old `js/particles.js` was therefore taken by a temporary property inside `scripts/test_particles.js` (removed afterwards), before the first edit of `js/particles.js`.

## 1. Test results (the real last line of each run)

| Test file | Last line |
|---|---|
| `node scripts/test_ultimate.js` | `test_ultimate: all 24 tests passed` |
| `node scripts/test_class_stats.js` | `test_class_stats: all 17 tests passed` |
| `node scripts/test_particles.js` | `56/56 properties passed` (was 38; 18 added) |
| `node scripts/test_sim_balance.js` | `test_sim_balance: all 27 tests passed` |
| `node scripts/test_wind_fx.js` (regression, unchanged) | `test_wind_fx: all 19 tests passed` |

Not run: `scripts/test_mcp_game.py`, `test_mcp_stdio.py`, `test_constants_sync.py` and the other Python tests (nothing they test was changed).

## 2. Module 1: `js/ultimate.js` (spec `ultimate-ledger`)

API as implemented:

```
Ultimate.createLedger({ maxPips: 3, maxUses: 2, cooldownRounds: 0, sides: ['player', 'ai'] })
  registerHit(side, throwId)            -> { counted, pips, reason }
  canArm(side, ctx)                     -> { ok, reason }     ctx = { turn, side, round, defendTurn, dead }
  arm(side, ctx)                        -> { ok, reason }
  cancel(side)                          -> { ok, wasArmed, reason }
  consume(side, round, throwId?)        -> { ok, reason, uses, remaining }
  registerKO(side)                      -> { ok, reason }
  getState(side, round?)                -> { ult_pips, ult_ready, ult_armed, ultimates_remaining, ultimates_used, ult_used_this_round } | null
  reset()
Ultimate.splitDamage(normal, strikes)   -> 1.5 x normal / strikes, rounded to 0.1
Ultimate.REASONS, ULT_PIPS 3, ULT_MAX_PER_MATCH 2, ULT_PER_ROUND 1, ULT_COOLDOWN_ROUNDS 0, ULT_MULT 1.5
```

Deviations and additions:
- Added `registerKO` (a KO'd unit loses its pips needs an entry point), the optional third argument of `consume` (the ultimate throw's id, so the ultimate gives 0 pips as `docs/ultimate_rules.md` 2d says; the built cat code gives 1), the optional second argument of `getState`, `splitDamage`, `REASONS`. Nothing from the brief was dropped.
- Pips are per side, as `index.html` counts them (`energy = { player, ai }`). `docs/ultimate_rules.md` wants per-unit counters for 4 v 4; for 1 v 1 the two are the same. One ledger per unit works.
- "Lockout rule exactly as ultimate_rules.md": the document says there is no round-1 lockout and no back-to-back lockout, only one use per side per round, and a published lever `ULT_COOLDOWN_ROUNDS` (default 0). Implemented exactly so, with `cooldownRounds` as the lever.
- `consume` without a prior `arm` is refused (`not_armed`). The built cat branch fires for the AI without arming; the wiring note below says to call `arm` first.

## 3. Module 2: `js/class_stats.js` (spec `class-stats`)

API as implemented: `CLASS_KEYS`, `CLASSES` (= `RECOMMENDED`), `PROVISIONAL`, `BAND`, `AIM`, `hitsToKill(att, def, {table, damage, execute})`, `expectedDamage(att, assumptions)`, `expectedDamageDetail`, `power`, `powerTable`, `matrix({table})`, `matrixStats`, `validate({table})`, `waveDamage`, `waveMeanDamage`, `ultimatePerUnit`, `ultimateOneTarget`, `oneShotRisks`, `compareTables`, `cloneTable`, `formatMatrix`. Tables are deep-frozen.

- `expectedDamage` includes the knight's die 1 to 6 and the ground skip: rule `current` (the hand tables of the judgement, basis `hand` / `measured` / `mid`) and rule `A` (`docs/playtest_fixes.md` Fix 1).
- The recommended matrix equals the document's 7 x 7 table cell for cell (min 3, max 7, 45 of 49 in 4 to 6, mean 4.86). `validate()` returns `[]` for it.
- The provisional table is read back from `index.html` by the test (hp, dmg, weapon of four classes, frost 0.7 and 2 throws, the volley, `WIND_ACCEL`), so it cannot drift. The bride, hunchback and reaper are not in `index.html`; their provisional numbers are the INVENTED ones of `docs/converge_characters.md` with HP 100 (`docs/review_reconcile.md` C1).

Difference provisional -> recommended (printed by the test): 19 changed fields, 28 of 49 matrix cells change.

```
provisional (index.html today)                     recommended
                skeleton wizard bat knight bride hunch reaper                skeleton wizard bat knight bride hunch reaper
skeleton            5      4     4    5      5     5     5      skeleton        5      4     4    5      4     6     5
wizard              4      4     4    5      4     4     4      wizard          4      4     4    5      3     5     4
bat                 5      5     5    6      5     5     5      bat             4      4     4    5      3     5     5
knight              5      5     5    6      5     5     5      knight          5      5     5    6      4     7     6
bride               9      8     8   10      9     9     9      bride           5      4     5    6      4     6     5
hunchback           5      4     5    6      5     5     5      hunchback       5      5     5    6      4     7     6
reaper              6      5     5    7      6     6     6      reaper          5      4     5    6      4     6     5
band: 6 violations (bride 8 to 10 hits)  min/max 4/10  41 in 4..6     band: 0 violations  min/max 3/7  45 in 4..6
```

Changes: skeleton frost 30% -> 20%; bat damage 20 -> 26; bride, hunchback, reaper from invented numbers to the judgement's (HP 75 / 130 / 110, damage 27 / 20 / 22, bride width 105 and speed 0.9, hunchback speed 0.8 and knockback 50 px). Wizard and knight unchanged.

## 4. Module 3: weapon effects in `js/particles.js` (spec `weapon-effects`)

Seven presets, appended in this order after the 27 old ones: `weapon_trail_wave`, `impact_wave`, `weapon_trail_bell`, `weapon_trail_skull`, `scythe_slash_fx`, `frost_shatter`, `bounce_ring`. Particle counts at the default options: 2 to 3, 8, 1 to 2, 1 to 2, 11, 9, 3.

- Old presets are byte-identical: the test hashes the file text before and after the new block (`12806d0e...`, `abedba6d...`, taken from the unedited file) and the old names and particle counts (`71863200...`). 38 old properties still pass.
- Budget: javelin hit stack 57, bride 9, reaper skull 25, three slashes 33, shield bounce 24, bell (reduced) 66; all at most 70.
- Finding: the bell stack as written in `docs/playtest_fixes.md` (`impact_burst` 1.4, `hit_sparks` 1.0, flash, `landing_ring_dust` 0.8, three `smoke_puff` 0.7) is 95 particles with the old presets, over the 70 budget. The old presets cannot be lowered in this task; the reduced stack above fits.
- Deviations: `bounce_ring` is a circle, not the flat ellipse of the design (no `squash` field in the particle record or drawer, both existing code); `impact_wave` rings start at different radii instead of 80 ms apart (no start delay in the system); `scythe_slash_fx` makes sparks only (the crescent pictures are the game's). The new properties sit in front of the runner block of `test_particles.js`, because the runner ends with `process.exit`.
- Not verified: how anything looks. The note glyphs (U+266A, U+266B) depend on the canvas font.

## 5. Module 4: `scripts/sim_balance.js` (spec `balance-sim`)

API as implemented: `simulateMatch({ a, b, seed, maxRounds, aimError, angle, table, shieldRule, waveRule, ultimates })`, `runPairings({ classes, matchesPerPairing, seed, ...same options })`, `simulateLandingX`, `solvePower`, `formatReport`, and `internals` for the tests. Command line:

```
node scripts/sim_balance.js --matches 200 --seed 7
   [--table recommended|provisional] [--aim-error 9] [--max-rounds 60] [--classes a,b] [--shield-rule current|A] [--wave-rule first_contact|centre] [--json]
```

Exit code 1 if a band is violated (a pairing outside 40 to 60% or a class average outside 45 to 55%), 0 otherwise, 2 for a bad option. The match length band (8 to 14 rounds) is reported but does not decide the exit code.

Physics are the ones of `index.html`, and the test reads `index.html` and fails if any of these lines moves (gravity, wind acceleration 72, 13.8, ground, fence, hit box 70 / 190, fence damage, wind reroll, move limits, start ranges, the knight's hop numbers, muzzle offsets).

Deviations from the brief and why:
- The bot knows the wind and target exactly and moves forward (once, with the die) only when full power falls short; no other tactics. Needed because the hunchback (speed 0.8) and bride (0.9) cannot cross the field otherwise.
- Only the cat's volley is played (as the brief lists). The ledger is the real `js/ultimate.js`. The other classes' pips are counted and never spent.
- Default `aimError` is 9 power units. It gives a 55% hit rate for a point weapon; the comment in `index.html` says 52%. The brief did not give a number.
- "The rules you recommended" for the knight: the default is `current` (the judgement says do not touch the knight before this run). `shieldRule A` (`docs/playtest_fixes.md` Fix 1) is available.
- Added `waveRule centre` (not in the brief) because the first run showed the bride's damage per hit at 18, not 22.4 (see finding 2).

### 5a. The real matrix, provisional values (index.html today), 200 matches per pairing, seed 7, aim error 9

```
Balance simulation (provisional values, aim error 9, shield rule current): 200 matches per pairing, 5600 matches, seed 7

Win rate of the ROW class against the COLUMN class (%, a draw counts half):
           skeleton   wizard     bat        knight     bride      hunchback  reaper
skeleton   -          68.0       82.5       69.0       98.0       54.0       87.5
wizard     32.0       -          63.5       33.5       94.0       37.5       74.0
bat        17.5       36.5       -          18.5       84.5       28.5       45.5
knight     31.0       66.5       81.5       -          96.5       52.0       82.0
bride      2.0        6.0        15.5       3.5        -          0.5        23.5
hunchback  46.0       62.5       71.5       48.0       99.5       -          80.5
reaper     12.5       26.0       54.5       18.0       76.5       19.5       -

overall 8.08 rounds (band 8 to 14: inside), timeouts 0

class      avg win %  hits to kill  dmg/hit throw  hit rate %  fence %  moves/throw  ults/match
skeleton   76.5       4.86          20.9           53.7        11.6     0.01         0.00
wizard     55.8       4.13          24.9           54.1        10.1     0.01         0.00
bat        38.5       5.32          18.7           55.8        12.2     0.01         0.60
knight     68.3       5.97          16.8           69.8        15.0     0.02         0.00
bride      8.5        8.89          11.5           60.1        10.4     0.01         0.00
hunchback  68.0       5.07          20.1           60.7        4.1      0.15         0.00
reaper     34.5       5.84          17.1           53.1        10.9     0.01         0.00

BANDS: 25 violation(s)    exit code 1
```

### 5b. The real matrix, recommended values, 200 matches per pairing, seed 7, aim error 9

```
Balance simulation (recommended values, aim error 9, shield rule current): 200 matches per pairing, 5600 matches, seed 7

Win rate of the ROW class against the COLUMN class (%, a draw counts half):
           skeleton   wizard     bat        knight     bride      hunchback  reaper
skeleton   -          61.5       63.5       63.0       73.5       53.0       53.5
wizard     38.5       -          41.5       33.5       76.5       49.0       52.5
bat        36.5       58.5       -          35.5       76.0       44.5       40.0
knight     37.0       66.5       64.5       -          76.0       39.5       45.5
bride      26.5       23.5       24.0       24.0       -          13.5       38.5
hunchback  47.0       51.0       55.5       60.5       86.5       -          55.5
reaper     46.5       47.5       60.0       54.5       61.5       44.5       -

overall 7.35 rounds (band 8 to 14: outside), timeouts 0

class      avg win %  hits to kill  dmg/hit throw  hit rate %  fence %  moves/throw  ults/match
skeleton   61.3       4.69          21.9           53.1        13.1     0.01         0.00
wizard     48.6       4.05          25.7           53.7        12.2     0.01         0.00
bat        48.5       4.27          23.9           55.4        13.6     0.01         0.49
knight     54.8       5.79          17.0           68.8        16.6     0.01         0.00
bride      25.0       5.14          18.3           68.8        12.5     0.07         0.00
hunchback  59.3       5.61          18.8           52.6        17.2     0.22         0.00
reaper     52.4       4.70          21.5           52.2        12.9     0.01         0.00

BANDS: 15 violation(s)    exit code 1
  12 pairings outside 40 to 60 (skeleton vs wizard / bat / knight / bride, wizard vs knight / bride, bat vs knight / bride,
  knight vs bride / hunchback, bride vs hunchback / reaper); class averages outside 45 to 55: skeleton, bride, hunchback
```

### 5c. Other runs (class average win %, 200 matches per pairing, seed 7)

| Run | skeleton | wizard | bat | knight | bride | hunchback | reaper | violations | avg rounds |
|---|---|---|---|---|---|---|---|---|---|
| provisional, aim error 9 | 76.5 | 55.8 | 38.5 | 68.3 | 8.5 | 68.0 | 34.5 | 25 | 8.08 |
| **recommended, aim error 9** | 61.3 | 48.6 | 48.5 | 54.8 | 25.0 | 59.3 | 52.4 | 15 | 7.35 |
| recommended, aim error 5 | 72.3 | 54.7 | 50.9 | 41.5 | 13.5 | 57.3 | 59.9 | 18 | 6.14 |
| recommended, aim error 14 | 50.9 | 45.8 | 42.5 | 56.1 | 35.3 | 70.4 | 49.0 | 15 | 10.04 |
| recommended, aim error 9, wave rule centre | 61.9 | 48.8 | 48.6 | 55.3 | 23.2 | 59.5 | 52.8 | 16 | 7.36 |
| recommended, aim error 9, knight rule A (total 30) | 52.8 | 43.8 | 43.3 | 91.9 | 21.5 | 51.7 | 44.9 | 18 | 6.64 |

With 200 matches the standard deviation of one pairing is about 3.5 points, so a rate within 3 points of 40 or 60 is a coin flip about the band.

## 6. Findings for the main line and the owner (all from the runs above; none is a decision I made)

1. **The recommended table does not pass the band.** 12 of 21 pairings and 3 of 7 class averages are outside, at the default aim error; it is still better than the provisional table (25 violations). The cat is fixed by 20 -> 26 (38.5% -> 48.5%, as the judgement predicted). The Pumpkin Guard sits at 55% at error 9.
2. **The bride is far weaker than the hand model said** (25% average, 13.5% against the hunchback). The judgement put her power at -1% (AI-type) and -4% (bot-type) of the mean. In play her damage per hitting throw is 18.3, not 22.4, and she hits 69% of her throws, not the 100% the bot-type model gives her (window 210 against a spread of 200). Part of the damage loss is the rule "distance at first touch": the body box is 190 px tall, so the wave first touches near its edge. Measuring at body-centre height (`--wave-rule centre`) lifts her damage per hit to 20.0 but her average only to 23%, so the main cause is 75 HP with an ordinary damage per throw. Lever to test: HP or damage, not the falloff.
3. **The skeleton's strength depends on the player's accuracy**: 72% at error 5, 61% at 9, 51% at 14. The frost curse is worth more to an accurate player. The judgement's fallback (damage 24 -> 23) is the next step; I did not apply it.
4. **The hunchback is strong at every accuracy** (57 to 70%) and moves forward in 22% of its throws. A likely cause (not verified): a slow weapon needs more power for the same distance, so the same error in power units moves the landing less in pixels. It would help human players equally, since the meter error is also in power units.
5. **Hits to kill from play match the hand table**: skeleton 4.69 against 4.71, wizard 4.05 / 4.14, bat 4.27 / 4.29, bride 5.14 / 5.00, hunchback 5.61 / 5.43, reaper 4.70 / 5.00. The knight needs 5.79 against 5.43: its damage per hitting throw is 17.0, not the hand estimate 20 (the judgement converts the 65-round playtest to about 10 per throw, at a lower hit rate).
6. **Knight rule A with a total of 30 is far too strong** (91.9% average): it was designed around 22 (`docs/playtest_fixes.md` Fix 1). It needs its own total if adopted.
7. **One ultimate can kill a full-HP unit**: knight (trigger 30 + follow-up 45) against the bride (75 HP). `docs/ultimate_mapping.md` assumed a knight trigger of 22 and no one-shot.
8. **Match length** is 7.35 rounds at error 9 (below the 8 to 14 band) and 10.0 at error 14.
9. The bot's hit rate at error 9 (55%) is close to the 52% quoted in `index.html`, so the simulator's physics agree with the game on at least this number.

## 7. WIRING NOTE for the main line (index.html was not edited; line numbers are from this checkout and move)

### 7a. `js/ultimate.js` (ledger)

| Where | Change |
|---|---|
| script tags (L246 to L250) | add `<script src="js/ultimate.js"></script>` before the big inline script |
| L509 to L513 (`energy`, `ultUsed`, `countedThrows`, `throwSeq`, `ultArmed`) | replace by `const ult = Ultimate.createLedger({ maxPips: 3, maxUses: 2, sides: ["player", "ai"] });` and keep `throwSeq` |
| `toggleUltimate()` L514 and the `KeyU` handler | arm: `ult.arm("player", { turn, side: "player", round: roundNum, defendTurn: defendMode, dead: player.hp <= 0 })`; on `ok:false` show a text for `reason` (`ultimate_not_ready`: 能量未滿, `no_ultimates_left`: 大招已用完, `ultimate_used_this_round`: 本回合已用, `ultimate_with_defend`, `wrong_phase`, `unit_dead`). If armed: `ult.cancel("player")` |
| `actionMenuItems()` L668 and `chooseMenuItem()` L674 | add the gold entry `✨ 大招` when `ult.canArm("player", ctx).ok` (grey with the reason otherwise); Move, Attack and Defend choices, `Escape`, a heavy or double skill, `cancelDefendMode` and the 12 s timeout without a throw all call `ult.cancel("player")` |
| `executeThrow()` L885, volley branch L937 | the condition becomes `ult.getState(who).ult_armed` (for the AI: `ult.arm("ai", ctx)` first, using its own rule); then `ult.consume(who, roundNum, pj.throwId)` replaces `energy[who] = 0; ultUsed[who]++; ultArmed[who] = false;`. Consume at release, also when the throw later misses |
| hero collision L1577 (`countedThrows.has ... energy[who] + 1`) | `ult.registerHit(who, p.throwId)` (it does the once-per-throw and the max-2 checks); the ultimate throw's own hits give no pip because its id was passed to `consume` |
| KO at L1578 | `ult.registerKO(opp is player ? "player" : "ai")` |
| `resetGame()` (about L1259; the line that clears `energy`, `ultUsed`, `countedThrows`, `ultArmed`) | `ult.reset()` |
| pips drawing and the top plate | read `ult.getState(side, roundNum)` (`ult_pips`, `ult_ready`, `ult_armed`, `ultimates_used`) |
| MCP (`scripts/mcp_stdio_server.py`) | the field names of `getState` are the public names of `docs/ultimate_rules.md` 2g; the six reasons are the rejection codes. The Python server needs its own port of the same rules (this module is JavaScript) |

### 7b. `js/class_stats.js`

| Where | Change |
|---|---|
| `HERO_PROFILES` L464 | after the owner decides, copy `hp`, `dmg` from `ClassStats.CLASSES` (bat 20 -> 26, skeleton frost 0.7 -> 0.8 at `weak > 0 ? 0.7 : 1` in `executeThrow` and the text at `opp.weak = 2` in the hero collision); until then this module is a calculator only |
| `(not published)` (planned in `docs/review_reconcile.md`) | when it exists, generate the table from it and keep `ClassStats` as the test fixture |
| a test hook | run `node scripts/test_class_stats.js` after any change of `HERO_PROFILES`; it reads the file and fails on drift |

### 7c. Weapon effects (presets)

| Where | Call |
|---|---|
| trail choice in the projectile loop (L1510 to L1513) | `proj_bell` -> `weapon_trail_bell` every step; `proj_skull` -> `weapon_trail_skull` every step; the bride's wave -> `weapon_trail_wave` every 6th step (`recordedPath.length % 6 === 0`) |
| hero collision (L1572 to L1600) | bride: `fxEmit("impact_wave", p.x, p.y, { scale: share })` with `share` = damage / 22; javelin curse (the `opp.weak = 2` block): `fxEmit("frost_shatter", opp.x, opp.y - 120, { scale: 1 })`; reaper slash i (0, 1, 2): `fxEmit("scythe_slash_fx", opp.x, opp.y - 100, { index: i, dirX })` 0.25 s apart |
| knight ground and fence bounce | `fxEmit("bounce_ring", p.x, GROUND_Y, { scale: 0.8 })` |
| stack size | do not emit the old `impact_burst` 1.2 + `hit_sparks` 1.1 + legacy dots on top of these; the budget is 70 particles per unit hit (see section 4) |

### 7d. `scripts/sim_balance.js`

| Where | Change |
|---|---|
| test hook | run `node scripts/test_sim_balance.js` (fast, 27 tests) with the other tests; run `node scripts/sim_balance.js --matches 200 --seed 7` by hand after changing any class number, and read the class-average column first |
| `index.html` constants | the test fails if a physics line of `index.html` changes (it matches the source text); update the simulator and the regex together |

## 8. Summary

1. Four modules, four spec folders, 16 + 23 + 15 + 22 numbered, checkable requirements; all tasks ticked; `index.html` and every file outside the brief untouched.
2. Test results: ultimate 24 passed, class stats 17 passed, particles 56/56 passed (38 old unchanged), simulator 27 passed, wind regression 19 passed.
3. Old particle presets are proven byte-identical by sha256; the seven new presets fit the 70-particle hit budget, except that the bell stack written in the doc counts 95.
4. The simulator plays the game's physics and the six class rules; with 200 matches per pairing neither table passes the band (provisional: 25 violations, recommended: 15). The recommendation fixes the cat and does not fix the bride (25%), the skeleton (61%) or the hunchback (59%).
5. Hits to kill from play match the hand table within one hit for every class; the bride's win rate does not match the hand model.
6. Could not verify: how anything looks or sounds; human play (the bot knows wind and target exactly); the 4 v 4 flow; the other classes' ultimates; the Python tests (not run); `index.html` behaviour in a browser; whether the note glyphs render.
