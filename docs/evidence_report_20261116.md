# Balance and rule evidence report — 2026-11-16

## Scope and verification

**Changed:** created this read-only evidence report. No game code or data changed.

**Verification commands:** none were named by task 171. This task required repository inspection only, so no test command was run.

**Not verified:** browser behaviour was not run. All findings below are source and local-playtest-document evidence, not a new simulation or browser measurement.

## 1. `Math.random` inventory and determinism gap

No file under `js/` directly calls `Math.random()`. `js/audio.js` and `js/ambient_sfx.js` accept an injected random function, and `js/nun_ult.js` accepts an injected `rng`; `index.html` supplies `Math.random` to all three. `js/particles.js` is seeded and does not call it.

| File:line | Function or path | What it decides | State or visual |
|---|---|---|---|
| `index.html:345` | `ensureGameAudio` → `GameAudio.createAudio` | Injects random source for audio variation. | Visual/audio only |
| `index.html:348` | `ensureGameAudio` → `AmbientSfx.createAmbient` | Injects random source for ambient creature-sound timing, pan, and variation. | Visual/audio only |
| `index.html:393` | module initialization | Initial built-in opponent hero from `AI_CLASSES`. `startMatch` redraws it at `:425`. | State |
| `index.html:425` | `startMatch` | Built-in opponent hero for the new match. | State |
| `index.html:736`, `:1609` | `matchSeed` initialization / `resetGame` | New match seed. That seed deterministically selects first-round wind and weather thereafter. | State |
| `index.html:901` | `startDiceRoll` | Final d6 result for either side's move. | State |
| `index.html:958` | `stepDice` while `t < 0.8` | Temporarily displayed tumbling face; the final face was already selected at `:901`. | Visual only |
| `index.html:987-989` | `randomizePositions` | Initial player and AI target positions, rounded to pixels. | State |
| `index.html:1228` | `executeThrow`, bat ultimate | Velocity scale 0.95–1.05 for each of the four added shuriken. This changes landing and hit results. | State |
| `index.html:1289` | `executeThrow`, knight normal attack | d6 collision count and equal per-collision damage. | State |
| `index.html:1527` | `aiAttackNow` | AI's noisy, grid-rounded perception of the player position. | State |
| `index.html:1528` | `aiAttackNow` | AI's noisy perception of effective wind. | State |
| `index.html:1536` | `aiAttackNow` | AI power error, ±`AI_AIM_ERROR` (6 normally). | State |
| `index.html:1566` | `triggerAITurn` | Whether an already-active AI knight re-aims its shield (35%). | State |
| `index.html:1587-1589` | `triggerAITurn` | Whether AI moves first (25%) and its forward/backward direction (75% forward when gap >900, otherwise 35%). The final die still comes from `startDiceRoll`. | State |
| `index.html:1627` | `resolveRound` | Next-round wind, -4.0 to +4.0 in 0.1 steps. | State |
| `index.html:1710-1720` | `spawnParticles` | Angle, speed, radius, and decay of legacy particles. | Visual only |
| `index.html:2028` | direct-hit resolution → `NunUlt.resolve` | The selected stunned target among touched targets. In the current 1v1 page call, both entries are `"opp"`, so the selection does not change the target. | State |
| `index.html:2188` | `updatePhysics` charging aura | 8% chance to emit a rune-halo particle. | Visual only |
| `index.html:3493` | render loop | Camera-shake offset. | Visual only |

### Requested categories that are not random in the current source

| Category | Evidence |
|---|---|
| Supply drop | `scheduleAirdrop` at `index.html:1718-1730` alternates sides with `dropSide`, uses `dropCount`, computes distance as `140 + ((dropCount * 53) % 140)`, and selects `SUPPLY_KEYS[dropCount % SUPPLY_KEYS.length]`. No random call is present. |
| Nun electric-stun pick | The actual random source is the `Math.random` passed at `index.html:2028`; the deterministic module’s choice point is `(not published)`. |
| Seeded particles | `js/particles.js` has no direct `Math.random()` call. The unseeded legacy particles are `index.html:1710-1720`. |

## 2. Player-only rules and the built-in opponent alternative

| Player-only control | Evidence | Player rule | Built-in opponent behaviour instead |
|---|---|---|---|
| Two free heals | `index.html:666`; `:1002-1015` | Starts with two heal charges. Selecting heal on the player's turn restores 35 HP immediately, consumes one charge, and does not set `turn = "busy"`. | No selectable free heal. `index.html:1762-1764` lets the AI take a landed supply crate only when it is missing at least 20 HP; it then receives the supply heal of 30 HP. |
| Double shot | `index.html:666`, `:1137-1143` | Two charges. The player gets a normal throw and, 260 ms later, a second throw at 1.04× power. | `executeThrow("ai", aiPower)` uses no `selectedSkill` modifier. The only extra AI throws are hero ultimates when the generic automatic condition is met. |
| Heavy shot | `index.html:666`, `:1144-1147`, `:1184-1197` | Two charges. Replaces the selected player's weapon with `proj_pumpkin`, enlarges it, and deals 1.5× profile damage. | No heavy selection or 1.5× normal-shot branch, because all `selectedSkill === "heavy"` checks also require `isPlayer`. |
| Move direction | `index.html:937-953` | Player enters move mode then explicitly chooses forward or backward. The random d6 supplies only distance. | `index.html:1587-1590`: AI moves with 25% probability and randomly chooses direction using gap-dependent probability. |
| Shield placement | `index.html:1028-1072`, `:2233-2258` | Knight player previews, drags, optionally snaps, and locks the floating shield. Fresh placement gives 2 charges for 2 rounds; `actions` starts at 4 and lock consumes one action and the turn. | `index.html:1566-1582`: AI knight selects the first qualifying point of the latest player trajectory. It always places when no shield is active and randomly re-aims an active shield at 35%; it has no player placement UI. |

## 3. Current hero combat rules

All page heroes use the generic direct-hit box at `index.html:2022`: normal weapons have horizontal half-width 70 and 190 px body height; the reaper target uses half-width 57 and height 165; bride wave impacts use horizontal half-width 105 but only the bottom 40 px. A generic airborne shield can block a projectile at `:1985-2007`, except `p.ultBoom`; the knight ultimate can also stop the enemy's predicted projectile at `:2009-2017`.

| Hero | Normal attack and status in `index.html` | Ultimate name, factor, and hit count | Blockable? / can miss? | Cross-file difference or qualification |
|---|---|---|---|---|
| Skeleton | Spear, 22 base (`:589-596`). A surviving hit bleeds for 2 damage on each of the next 2 round starts and applies frost: victim attacks at 85% for its next 2 throws (`:2041-2045`, `:2106-2110`). | **Triple Javelin**. Three projectiles, each `1.5 / 3 = 0.5×` normal. Each prior landed volley hit adds 5%; the third landed hit also receives a 1.25× crit (`:1254-1261`, `:2036-2039`). | Yes, ordinary projectile interception applies. Yes, each spear can miss. | `(not published)` also models three javelins at 0.5× each, but does not model the page's +5% ladder or forced third-hit crit. |
| Wizard | Cannonball, 30 base (`:598-605`); surviving cannonball hit poisons for 2 damage at each of 2 round starts (`:762-763`, `:2045`). | **Pumpkin Blast**. The normal shell remains, then a 1.5× base blast (45 with current page profile) affects a unit within 234 px of the impact (`:1263-1269`, `:2131-2145`). | The shell can be blocked or miss. The raw blast is resolved after any impact and has its own 234 px range. | `js/ultimate_fx.js:183-206` presents the blast at 1.5×. The page blast does not apply the weather multiplier. |
| Bat | Shuriken, 22 base (`:607-614`); surviving hit applies `slow = 1`, preventing the target's next move (`:2044`). | **Shuriken Scatter**. Five projectiles; total nominal damage is 1.5× normal, 0.3× each (6.6 at page damage 22). The four added projectiles have random 0.95–1.05 speed scale (`:1209-1229`). | Yes. Yes, each shuriken can miss. | `js/ultimate_fx.js:61-64` agrees on five hits and total 1.5×. Its timeline does not encode random speed scale. |
| Pumpkin Guard / knight | Thrown shield, 26 total base damage (`:649-660`). A random d6 divides it over collision count; no status (`:1288-1290`). | **A/B/C hidden shield points**. Three placed points, zero direct damage, each may stop one relevant enemy projectile. | It blocks rather than attacks. A placed point can fail to intersect, so it can miss as a defence. | Major implementation difference: page points may be freely tapped on an arc and last three enemy attack rounds (`:688-706`, `:1202-1207`); `js/knight_ult.js:133-252` requires remembered-path selection by normalized path distance and only checks the oldest point. Both use 70 px. |
| Necromancer / `reaper` | Flame, 22 base (`:615-623`); surviving hit applies a nonlethal 2-damage burn for 3 round starts (`:1796-1802`, `:2042`). | **Soulfire Volley**. Three flames launch 0.15 s apart. The page uses `UltimateFx.necroVolleyDamage`: `[0.55, 0.65, 0.75]×` normal, i.e. `[12.1, 14.3, 16.5]` with page normal 22; no crit. Any surviving hit applies hallucination, which skips the victim's next turn (`:1272-1286`, `:2076`). | Yes, generic projectile interception applies. Yes, each flame can miss. | The page comment says 1.1/1.3/1.5×, but `(not published)` applies `NECRO_VOLLEY_SCALE = 0.5`, so actual factors are half of that comment. `js/class_stats.js` instead models 105 HP / 23 damage, unlike the page's 95 / 22. |
| Ghost bride | Sound wave, 28 base (`:632-641`). `SoundWave.damageAt` is 100% at ≤40 px, 75% at ≤75 px, 50% at ≤105 px; surviving wave hits poison for 2 damage at each of 2 round starts (`:2025`, `:2045`, `js/sound_wave.js:14-20`). | **Bat Swarm**. A primary wave hit strictly inside 55 px triggers a 1.3× normal swarm, 36.4 with page normal 28, on the opponent (`:1247-1253`, `:2066-2072`). | Primary wave can be blocked or miss. Swarm is explicitly not blockable once triggered and has no separate aim roll. | `(not published)` agrees on normal 28, 55 px strict threshold, and 1.3× = 36.4. The page comment at `:2066` still says 25×1.3=32.5, which is stale. |
| Hunchback | Axe, 21 base (`:642-648`); surviving hit bleeds for 2 damage for 2 round starts and knocks the victim 50 px away (`:2041-2043`, `:2047-2050`). | **Boomerang Axe**. Each outbound contact deals 21; it pierces and returns to the first victim for 31.5 (1.5× 21) (`:1237-1245`; `js/boomerang.js:15-18`). | Explicitly **not blockable** by floating shield (`index.html:1985`) and boomerang contacts mark `blockable: false`. Yes, it can miss: no outbound hit produces no return. | `js/boomerang.js` and `js/ultimate_fx.js:314-361` agree on 21 / 31.5 and unblockability. The return **does** receive `Weather.applyAttack` in current page code at `index.html:1932`. |
| Ghost nun / `hag` | Silver cross, 24 base (`:624-631`); no normal status. | **Cross Dart**. `NunUlt` supports up to 3 targets and up to 2 hits each, at 0.575× normal. The 1v1 page passes `["opp", "opp"]`, so it resolves two 13.8 hits, 27.6 total, then stuns the touched opponent (`:1231-1236`, `:2028`, `:2051-2064`; `(not published)`). | Initial cross can be blocked or miss. The delayed second damage occurs only after initial contact, and it has no separate projectile intercept. | Source comment says “half the normal damage,” but the tested constant is 0.575, not 0.5. The selected stun target draws supplied RNG, although in the current 1v1 page both candidates are the same opponent. |

## 4. Weather and wind paths

`js/weather.js:16-21` defines clear/fog as 1.0 attack, 1.0 move, +0 wind; rain and storm as 0.9 attack; snow as 0.5 move; storm as +1.5 wind. `Weather.forRound` makes a deterministic two-round weather block (`js/weather.js:73-79`).

| Rule / API | Code path | Effect |
|---|---|---|
| `windBonus` → `effWind` | `index.html:740-745` caches `Weather.forRound(matchSeed, roundNum, scene)` then adds signed `windBonus` to non-zero base wind. | Storm strengthens wind magnitude without changing its direction. |
| `effWind` in projectile / prediction physics | `index.html:707-710` `predictPath`; `:1959-1962` projectile integration; `:1487-1500` AI's perceived wind and aim; `:1858` weather effects; `:1862` ambient wind intensity. | The knight prediction and live projectile use effective wind. AI applies perception noise to effective wind. Weather visual/audio use does not change combat state. |
| `moveMult` | `js/weather.js:107-111` is called at `index.html:968`. | `stepDice` multiplies d6 distance by weather movement multiplier; snow halves it. |
| generic direct-impact `applyAttack` | `index.html:2024-2030`. | After sound-wave falloff or bounce share, every generic direct impact applies weather; rain/storm reduce it to 90%, minimum 1. This includes ordinary attacks, normal portions of ultimates, and knight bounce-contact damage. |
| Nun's first direct hit | `index.html:2028`, then generic `:2029`. | `NunUlt` first-hit damage is passed through `applyAttack` once in the nun branch and again in the generic branch. Thus rain/storm apply 0.9 twice to this first hit. |
| Nun's delayed second hit | `index.html:2051-2064`. | One `applyAttack` call before delayed HP subtraction. |
| Hunchback boomerang return | `index.html:1929-1938`. | Return damage is `Weather.applyAttack(currentWeather(), 31.5)`. |

### Damage paths that do **not** apply the weather multiplier

| Damage source | Evidence | Finding |
|---|---|---|
| Bride swarm | `index.html:2066-2072` directly subtracts `round(HERO_PROFILES.bride.dmg * 1.3)`. | No `Weather.applyAttack`. |
| Wizard blast | `index.html:2131-2145` directly subtracts `p.ultBlast`. | No `Weather.applyAttack`. The original cannonball direct hit did use the generic path. |
| Poison, bleed, and burn ticks | `index.html:1798-1819`. | All subtract fixed nonlethal 2-damage values without `Weather.applyAttack`. |
| Hunchback boomerang return | `index.html:1932`. | **Contrary to the task examples, it does apply weather.** |
| Knight bounce contact | `index.html:2024,2029`. | **Contrary to the task examples, it does apply weather** because `bounceDmg` becomes `dmgNow` before the generic multiplier. |

## 5. Tests that pin balance numbers

The repository has no test that parses every current `index.html:HERO_PROFILES` HP/damage literal. The closest page-source assertion is `scripts/test_sim_balance.js:28-50`, which checks world constants, hit-box text, wind reroll, movement bounds, and knight bounce mechanics. Most exact hero-value tests assert the separate `js/class_stats.js` model, whose values differ from the current page for seven of the eight heroes.

| Hero | Current page HP / normal damage / width | Tests that assert the same current-page number | Tests that pin a related but different model number |
|---|---|---|---|
| Skeleton | 100 / 22 / 70 (`index.html:591-595`, `:2022`) | Width 70: `test_sim_balance.js:39`. No direct assertion of 100 / 22. | `test_sim_balance.js` frost test expects 24 damage; `test_class_stats.js` matrix uses the 24-damage model. |
| Wizard | 75 / 30 / 70 (`:600-604`, `:2022`) | Width 70: `test_sim_balance.js:39`. No direct assertion of 75 / 30. | `test_sim_balance.js:154-158` expects model wizard 28; `test_class_stats.js:91` asserts model wizard HP 85 / attack 28. |
| Bat | 95 / 22 / 70 (`:609-613`, `:2022`) | Width 70: `test_sim_balance.js:39`. No direct assertion of 95 / 22. | `test_sim_balance.js` cat-volley case uses model normal 26; `test_ultimate.js` pins generic 1.5× split; `test_ultimate_fx.js:39-41` pins five effect projectiles. |
| Knight | 140 / 26 total / 70 (`:651-659`, `:2022`) | Width 70: `test_sim_balance.js:39`. No direct assertion of 140 / 26. | `test_sim_balance.js` knight cases pin model total 30 and bounce behaviour. `test_knight_ult.js:95-115` pins 70 px A/B/C zone, three points, and 1.4 s reveal. |
| Reaper | 95 / 22 / target width 57 (`:616-622`, `:2022`) | Target width 57: `test_sim_balance.js:39`. No direct assertion of 95 / 22. | `test_class_stats.js:14-33` pins model 105 HP, 23 damage, width 70, burn 2×3, and 3 flames; `test_ultimate_fx.js:54-65` pins scaled volley outputs. |
| Bride | 70 / 28 / wave width 105 (`:633-640`, `:2022`, `:2503-2505`) | `test_sound_wave.js:31-45` pins width 105 and 40/75/105 bands. `test_ultimate_fx.js:170-178` pins normal 28, 55 px trigger, 1.3×, and 36.4 swarm. No direct HP-70 assertion. | `test_sim_balance.js` bride cases use model 75 HP / 27 damage and a different linear falloff. |
| Hunchback | 115 / 21 / 70 (`:643-647`, `:2022`) | `test_boomerang.js:25-42` and `test_ultimate_fx.js:113-124` pin 21 outbound and 31.5 return. No direct HP-115 assertion. | `test_sim_balance.js` uses a different class-stat model for general pairings. |
| Hag / nun | 105 / 24 / 70 (`:625-630`, `:2022`) | `test_nun_ult.js:25-45` pins factor 0.575, max three targets, and at most two hits per target. No direct profile HP / normal-damage / width assertion. | No hag row exists in `js/class_stats.js`; it is absent from the seven-class model. |

Generic ultimate factor 1.5 is pinned by `scripts/test_ultimate.js:43-46` and its split cases. It does not pin each page hero's profile damage. The special modules additionally pin their own values: `test_boomerang.js`, `test_sound_wave.js`, `test_nun_ult.js`, `test_knight_ult.js`, and `test_ultimate_fx.js`.

## 6. Playtest evidence

### Match table

“HP left” preserves the documents’ side and denominator. “Hits” is direct-hit evidence when supplied. Round 1 and the *original* first run of round 2 used a harness that did not set `turn = "busy"`; their old results are marked affected and must not be used for balance conclusions. The eight numbered round-2 reruns set it correctly.

| Source / match | Rounds | HP left | Hits | Harness status |
|---|---:|---|---|---|
| R1 #1 skeleton vs wizard | 4 | player 66/100; enemy 0/75 | enemy 1/3, 34 including poison | Affected: round-1 harness |
| R1 #2 wizard vs bat | 5 | player 26/75; enemy 0/95 | enemy 2/4, 27.5 and 22 | Affected: round-1 harness |
| R1 #3 bat vs knight | 10 | player 80/95; enemy 0/140 | enemy 1/9, 15 | Affected: round-1 harness |
| R1 #4 knight vs reaper | 14 | player 40/140; enemy 0/95 | enemy 4/13, 24.8, 24.8, 22, 12.9 | Affected: round-1 harness |
| R1 #5 reaper vs bride | 4 | player 65/95; enemy 0/70 | enemy 1/3, 28 | Affected: round-1 harness |
| R1 #6 bride vs hunchback | 4 | player 0/70; enemy 7/115 | enemy 4/4, 18.9×3 and 11.3 | Affected: round-1 harness |
| R1 #7 hunchback vs hag | 7 | player 67/115; enemy 0/105 | enemy 2/6, 24 and 24 | Affected: round-1 harness |
| R1 #8 hag vs skeleton | 5 | player 52/105; enemy 0/100 | enemy 2/4, 22 and 27.5 | Affected: round-1 harness |
| R1 aggregate | — | — | AI 17/43 = 40% | Affected: round-1 harness |
| R2 #1 skeleton vs knight | 9 | player 95/100; enemy 0 | enemy 1/4, 5.1; five AI turns spent shielding | Corrected rerun |
| R2 #2 wizard vs necromancer | 4 | player 20/75; enemy 0 | enemy 2/3, 27.5 critical + 22 | Corrected rerun |
| R2 #3 bat vs bride | 4 | player 51/95; enemy 0 | enemy 2/3, 12.6 + 25.2 | Corrected rerun |
| R2 #4 knight vs hunchback | 11 | player 69/140; enemy 0 | enemy 3/10; six shots blocked by hidden points | Corrected rerun |
| R2 #5 necromancer vs hag | 5 | player 65/95; enemy 0 | enemy 1/3, 30 critical | Corrected rerun |
| R2 #6 bride vs skeleton | 4 | player 44/70; enemy 0 | enemy 1/3, 22 | Corrected rerun |
| R2 #7 hunchback vs wizard | 5 | player 81/115; enemy 0 | enemy 1/4, 30 | Corrected rerun |
| R2 #8 hag vs bat | 4 | player 39/105; enemy 0 | enemy 3/3, 22×3 | Corrected rerun |
| R2 original knight vs hunchback | 13 | player lost; HP not reported | shield hit fence 10/13 shots | **Affected original run; exclude** |
| R2 original bride match | 3 | bride died from 70 HP; enemy HP not reported | 3 enemy hits after two fence impacts | **Affected original run; exclude** |
| Review designer: bride vs knight | 11 | player 65; enemy HP not reported | per-match hits not reported; aggregate range 0–3 | Declared valid; first swarm missed, enemy HP 61→59 |
| Review designer: hunchback vs wizard | 7 | player 76 | per-match hits not reported; aggregate range 0–3 | Declared valid |
| Review designer: nun vs necromancer | 8 | player 95, never hit | per-match hits not reported; aggregate range 0–3 | Declared valid |
| Review veteran: skeleton vs hunchback | 5 | player 36 | per-match hits not reported; aggregate range 0–3 | Declared valid |
| Review veteran: bat vs bride | 4 | player 66 | per-match hits not reported; aggregate range 0–3 | Declared valid |
| Review veteran: knight vs nun | 11 | player 120, never hit | per-match hits not reported; aggregate range 0–3 | Declared valid |
| Review judge: wizard vs skeleton | 15 | player 7 | per-match hits not reported; aggregate range 0–3 | Declared valid |
| Review judge: necromancer vs knight | 15 | player 105, never hit | per-match hits not reported; aggregate range 0–3 | Declared valid |
| Review judge: bride vs nun | 8 | player 55 | per-match hits not reported; aggregate range 0–3 | Declared valid |
| Review aggregate | 9 player wins / 9 | — | built-in opponent 0–3 hits per match | Declared valid |

### Other measured playtest numbers

| Source | Measured number | Qualification |
|---|---|---|
| R1 hero summaries | Player damage/throw: skeleton 18.8; wizard 19; bat 14; knight 8.4; reaper 17.5; bride 27; hunchback 15; hag 20. | All are from affected round-1 harness runs. |
| R1 duration | Knight match 14 rounds / 62 s; other listed durations 14–35 s. | Affected round-1 harness runs. |
| R2 knight | m4 11 shots for 115 damage, 10.5 average; separate 12-shot sample average 7.4; 6/10 shots blocked by knight ultimate. | Corrected rerun / additional sampling as described. |
| R2 bride | Centre-rule hits: 6/8 inside 55 px; sample landing distances 22, 21, 22, and 90 px; old run saw 4 px. | Corrected rerun except the explicitly old 4 px observation. |
| R2 hunchback | 21 damage and 50 px knockback, 4/5 player shots hit. | Corrected rerun. |
| R2 wizard | 30 base, 3/4 hits, ultimate blast -45; wizard ended at 20/75. | Corrected rerun. |
| R2 necromancer | Burn 2 damage for 4 ticks in m5; player burn 2–3 with 3 ticks in m2. | Corrected rerun. This differs from source burn's nominal 3 turns and merits a harness/source check. |
| R2 bat | 22 normal; observed ultimate 6.6×3 = 19.8. | Corrected rerun. |
| R2 skeleton | 22 normal; 8/9 player shots hit; knight shield blocked 2 ultimate spears. | Corrected rerun. |
| R2 hag | 24 normal, 4/4 player shots hit; ultimate first part 13.8 and second part about 23. | Corrected rerun. |
| R2 wind | Player first throw hit 8/8. First wind magnitudes ranged 0.9–2.9 with both signs; reported examples: tailwind power 56 and headwind -3.5 needing power 90. | Corrected rerun. |
| R2 weather | Rain changed 22→19.8 and 28→25.2. | Corrected rerun. Fog reported as no rules effect. |
| Review veteran | Knight about 8.6 damage per round across 11 rounds; first-round wind +2.4 in every reviewed match. | Review document’s own result. |
| R2 pose audit | Skeleton pose differences 0.66/0.65/0.59; bride windup 0.00; hag charge 0.01/0.00; wizard windup about 0.05; hag hit 0.17. | Presentation measurement, not combat balance. |

## Findings requiring follow-up, not silent rule changes

1. The playable page and the model/tests disagree on nearly all hero HP and damage values. For example, page wizard is 75 HP / 30 damage, while tested `ClassStats` wizard is 85 / 28; page knight is 140 / 26, while the tested model is 120 / 30.
2. The current page is non-deterministic in state-affecting ways, including seed creation, wind rerolls, positions, dice, knight bounces, AI decisions, and bat-ultimate projectile velocity. The seeded helper modules do not close that page-level gap.
3. The page applies rain/storm twice to the nun ultimate's first cross hit, while the wizard blast, bride swarm, and status ticks receive no weather multiplier. The task examples for boomerang return and knight bounces are stale: current code does apply weather to both.
