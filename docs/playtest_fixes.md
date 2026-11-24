# Playtest fixes and weapon-effect improvements (Kiro task 37)

Status: **review and design only.** I changed no code, art, audio or other document, ran no game and no simulation. Every number marked "calc" is my hand arithmetic from the constants in `index.html` (gravity 980, speed = power x 13.8, launch 110 px above the ground, wind 72 px/s^2 per unit, hit box 140 x 190 px, fence x 895..1025 and 250 px tall). Every number marked "data" is recomputed from `(not published)`. Nothing about how an effect looks or sounds is verified.

Row numbers: R1..R41 is the position of the row in the JSON. Matches start at R1 (m0, skeleton v wizard), R10 (m1, wizard v knight), R15 (m2, cat v skeleton), R20 (m3, knight v cat), R27 (m4, skeleton v cat), R32 (m5, wizard v skeleton), R38 (m6, cat v knight).

Owner rules held: owner log newest rows win. Not available: `docs/review_reconcile.md` (task 36 has not produced it). `docs/roster_design.md` describes a Plague Doctor and a Lantern Warden, not the owner's bride, hunchback and reaper, so I treated it as stale for the new classes. New-class numbers come from `docs/converge_characters.md` (marked INVENTED there) plus the owner log.

---

## 1a. DATA CHECK

### What the file contains

| Check | Main line says | JSON says |
|---|---|---|
| Rounds | 40 | **41 rows.** The report's tables stop before R41 (m6 round 4). I include R41. |
| Result | 4 wins, 3 losses | m0, m1, m4 are kills by the player (R9, R14, R31). m5 ends at R37 with a 28-damage hit and probably is a win. m2 (R19) and m3 (R26) are losses. **m6 has only 4 rows, both units alive (cat dealt 64, took 8.1): unfinished.** Supported: 4 wins, 2 losses, 1 unfinished. |
| Cat numbers | "before the scatter became an ultimate" | Correct, and it makes every cat row obsolete. The new normal attack is one shuriken at 20 damage. Only the knight, skeleton, wizard rows still describe the current rules. |

### Per class, player side (the omniscient bot)

| Class | Throws | Rows with damage | Hit rate (95% interval) | Damage as logged | Avg damage / throw | Damage per damaging throw | Hits to kill seen |
|---|---|---|---|---|---|---|---|
| Skeleton | 14 | 10 | 71% (45 to 88) | 200 | 14.3 | 20.0 (24 per full hit) | 5 in both finished matches (R9, R31) |
| Wizard | 11 | 9 | 82% (52 to 95) | 223.2 | **20.3** | 24.8 | 4 (R14), 5 (R37, after two cursed 19.6 hits) |
| Cat, old 5-shuriken | 9 | 9 | 100% (70 to 100) | 154 | 17.1 | 17.1 | none finished |
| Knight | 7 | 3 | 43% (16 to 75) | 42.3 | **6.0** | 14.1 | none (100 / 6.0 = 16.6 throws extrapolated) |
| All | 41 | 31 | 76% | 619.5 | 15.1 | | |

Differences from the report: wizard average is 20.3 as logged. The report's 18.2 equals 200 / 11, which only works if m5 is capped at 100 damage; the JSON does not cap it (R37 shows 28 when about 4.8 HP could remain). Cat average is 17.1 with R41 (18.3 without). Skeleton, wizard, knight hit rates match the report.

The cat's "100%" means at least one of five shuriken hit. R16, R19, R39, R41 are one-shuriken rounds (6, 6, 8, 8 damage). It is not comparable to a one-projectile class.

### The AI half of the data (the only difficulty data in the file)

The AI never throws in a round where the player killed first (R9, R14, R31, R37), so the denominator is 37 throws, not 40.

| AI class | AI throws | Hits | Rate | Damage | Per throw |
|---|---|---|---|---|---|
| Skeleton (R15..R19, R32..R36) | 10 | 6 | 60% | 172 | 17.2 (12.4 if R15 and R34 were 24, not 48) |
| Cat, old volley | 11 | 6 | 55% | 136 | 12.4 |
| Wizard | 8 | 2 | 25% | 47.6 | 6.0 |
| Knight | 8 | 3 | 38% | 13.6 | 1.7 |
| All | 37 | 17 | **46% (31 to 62)** | 369.2 | **10.0** |

The `AI_AIM_ERROR` comment says 33% at calm wind. 46% is inside the interval, so no change is proven, but the report's "40%" used the wrong denominator.

### Conclusions the data does not support

1. **"AI damage comes mainly from the cat's five shots."** The AI skeleton, which throws one javelin, has the highest damage per throw (17.2). The AI cat is 12.4.
2. **"54 degrees or lower gets blocked by the fence."** Blocked rows by launch angle: 40 deg 0/7, 50 deg 1/6 (R5), 54 deg 3/15 (R3, R10, R25), 60 deg 1/6 (R6), 65 deg 0/7. Up to 54 degrees: 4/28. 60 degrees and above: 1/13. The gap is not significant, and one block happened at 60.
3. **Angle table (40: 86%, 50: 67% ...).** Arithmetic is right (65 deg is 71% with R41). Groups hold 6 to 15 throws, and the bot rotates the angle by round number, so angle is not an independent variable. No conclusion either way.
4. **Wind groups.** Counts are 3, 10, 18, 10 throws. Seven of the 18 in the 2 to 3 group are round 1 of each match, which always has wind 2.4 (`let wind = 2.4`). The bot cancels the wind exactly, so the table says nothing about wind difficulty. The report says this itself; I add that the table also cannot show "big wind is not harder".
5. **Knight "median landing error 231 px".** Arithmetic is right (|errors| 7, 66, 93, 231, 283, 832, 877). For N > 1 the logged x is where the shield finally stopped after bounces, not an aim error. The three N = 1 rows (R23, R24, R25) have 93, 66, 231 px.
6. **"Fill in 3 to 4 rounds."** Third pip comes at round 3, 3, 3, 4, 4, 5, 7 (R17, R29, R40, R13, R35, R24, R7). Mean 4.1, range 3 to 7. This is a bot property (hit rate 71 to 82%). At the AI's 46% the same bar takes about 6.5 throws; at 30% about 10 (calc: 3 / p).
7. **Frost curse is never mentioned, but it is in the numbers.** 19.6 = 28 x 0.7 (R1, R35, R36); 5.6 per shuriken shows as "6" per shuriken in R16, R18, R19. A skeleton that hits every round keeps its target cursed for every throw.

### Inconsistent or unexplained rows (fix the logger before playing more)

| Row | Problem |
|---|---|
| R11 | Wizard, `ground`, error -713, yet damage 28 and the pip rose. A cannonball with no bounce cannot do both. |
| R15, R34 | AI skeleton deals 48 = 2 x 24 in one round. Running totals reach exactly 100 at R19 (48+24+24+4), so the HP loss was real. Either the AI threw twice in one round (harness or game bug) or one javelin hit twice. I cannot tell which. |
| R9, R14, R19, R26, R31 vs R37 | Kill hits are clipped to the remaining HP (4, 16, 4, 28, 4). R37 is not. |
| R1, R38, R2 of other matches | Hits with error -118, -269, -80 while the hit box is 70 px. Round 1 positions are still gliding (`x` eases to `targetX` at 4/s); I suspect the bot used `targetX`. Unverified. |
| Cat and knight rows | `hit_type` is the last projectile's type, not one value per throw. |

---

## 1b. FIXES (ranked)

| Rank | Fix | Why this rank |
|---|---|---|
| 0 | Logger fixes (below) | Cheap, and every later number depends on it |
| 1 | Knight strength | Largest gap (6.0 vs 14 to 20), one function to change |
| 2 | AI: remove the simulator, add a landing ledger | Breaks `product.md`, and drives difficulty |
| 3 | Wind legibility for a human | The owner's open complaint |
| 4 | Time to kill, including the frost curse | Three classes sit outside 4 to 6 hits |
| 5 | Energy pacing and the pip definition | Needs realistic-accuracy bots first |
| 6 | Fence | Mostly geometry; two small fixes |

### Fix 0. Logger (prerequisite)

Problem: see the inconsistent-row table. Change: one record per **projectile** (first contact type, x, damage per unit), one record per **throw** (thrower, round, wind, angle, power, unit x at release, `weak` flag of the thrower, total damage, remaining HP before and after). Damage always clipped to remaining HP and the clip logged. Round 1 wind random, not 2.4. Assertion: exactly one AI throw per round. Verify: automated assert over 100 matches, zero violations; R15 and R34 type events then show up as assertion failures or disappear.

### Fix 1. Knight strength (task item 1)

**Problem.** Average damage 6.0 per throw against 14.3 to 20.3 for peers (R20..R26). Three throws dealt damage: R20 14.8 (4 of 6 collisions on the unit), R22 5.5 (1 of 4), R24 22 (N = 1). Zero-damage throws: R21 and R26 hit the fence first and flew back (errors -832, -877), R25 hit the fence (N = 1), R23 landed short (N = 1).

**Cause in the code.**
- Every collision with the fence, the ground or a unit uses one die count, but only unit collisions deal damage.
- After a unit hit the shield hops with `vx x -0.12`, `vy = -330` and is supposed to land on the same unit. It does so only when the wind or the throw speed does not carry it out of the 70 px half-width. R20 (wind +2.4, tailwind) kept 4 of 6; R22 (wind -1.1, power 83.6) kept 1 of 4.
- A fence hit reverses the shield (`vx x -0.6`) and sends it back to its own side. No other weapon does this, and it is never useful.
- The pip is awarded for a 3.7 or 5.5 chip exactly like a 22 hit.
- Fitting "share of collisions that land on the unit, after a first unit hit" to the three damaging throws gives 0.64 (0.67, 0.25, 1.0). The model "contact rate 3/7 x 22 x 0.645" gives 6.1, which matches the 6.0 seen. n = 3, so treat it as a fit, not a measurement.

**Two options** (damage per throw, calc; q = chance the first contact is the unit; q = 0.43 is the knight's observed 3/7, q = 0.71 is the skeleton's rate; g = chance of a ground-first contact, 0.14 and 0.15; skip-in success s = 0.4 for A, 0.5 for B):

| | Rule | Avg damage at q = 0.43 | at q = 0.71 |
|---|---|---|---|
| Current | all collisions cost; hop-back unreliable | 6.1 | 10.1 |
| **A (recommended)** | Die N = number of **unit hits**. Ground gives one free skip, then the shield ends. Fence ends the shield like every other weapon. After the first unit contact the remaining N-1 hits land on the same unit 0.12 s apart (deterministic, visual hop of 40 px, no physics). Damage 22 / N each, the last hit takes the rounding remainder so the sum is exactly 22. | 10.7 (22 x (q + g s)) | 16.9 |
| B | All collisions still cost. Die minimum 2 (a roll of 1 counts as 2). Hits after the first are guaranteed. Fence still reverses the shield. | 10.5 (22 x (q + g x 0.5 x 0.675)) | 16.7 |

Peer mean at the same bot accuracy is about 15.5 (skeleton 14.3, wizard 18.2 capped, cat single shuriken about 14), band +/-20% = 12.4 to 18.6. A and B land the same. Making the hop-back deterministic is worth +55% on its own (6.1 to 9.5 at q = 0.43). The ground and fence rules add about 0.5.

**Recommendation: A.** It keeps the owner's d6 of 1 to 6 (B changes it). It also reads like the owner's picture of a shield bouncing between targets: in 4v4 each paid hit may jump to the nearest other living enemy within 380 px, and ground or fence skips would waste it. Cost to state to the owner: in 1v1 the die no longer changes total damage (22 whenever the shield reaches the unit); it sets how many ticks the damage comes in. It matters in 4v4.

**Exact change.**
- Fence branch: remove the `bouncy && bouncesLeft > 1` rebound. A fence hit ends the shield.
- Ground branch: `p.freeSkips = 1` at launch; first ground contact skips (`vy = -|vy| x 0.55`, `vx x 0.75`) without decrementing `bouncesLeft`; second ends it.
- Unit branch: on first contact schedule `bouncesLeft - 1` extra hits at +0.12 s each on the same unit (1v1) with `bounceDmg = dmg / N`, remainder on the last.
- New constant `ULT_PIP_MIN_DMG = 8`: a throw gives a pip only if its **total** damage is at least 8 (see Fix 5). With A the knight's total is 22 whenever it connects, so the pip is no longer unfair.
- If the knight tests above +20% of the peers, set its damage 22 to 20 (5 hits to kill exactly, 15.4 per throw at q = 0.71).

**Verify (automated).** (1) Property test, 1000 runs, winds -4 to +4, power 40 to 100: first unit contact gives total damage 22.0 +/- 0.05 in every run; no knight projectile ever has `vx` reverse sign after a fence hit. (2) 2000 knight throws against a dummy at the same aim error as 2000 skeleton throws: knight average / mean of the other classes in 0.8 to 1.2. (3) Screenshot of the 6-hit flurry at 1920 x 1080: at most 6 damage numbers merged into one running total.

### Fix 2. AI difficulty without hiding information (task item 2)

**Problem.** `aiAttackNow` calls `estimatePowerForTarget` (`simulateLandingX`), the exact integrator with the exact wind and the exact target x, then adds uniform +/-14 power. That is a trajectory simulator and `product.md` forbids it ("no trajectory simulator, no trial throws"). It is also the owner's open question 5. The AI also always throws at 54 degrees. In the data the AI hits 46% per throw (R-list above) and is perfect from round 1. A human needs several throws to learn range and wind.

**Gap, in numbers (calc).** One wind unit moves a landing 73 to 151 px (40 deg power 70: 73; 54 deg power 65: 94.5; 54 deg power 85: 151). The hit window is about 250 px (140 + 190 / tan of the descent angle, 230 to 300 px). A human who is 1 wind unit off misses about as often as one who is 90 px off. The AI has zero error from round 1, only the +/-14 power jitter (about +/-300 px at 20 to 25 px per unit, window / spread = 40%).

**Change (nothing is hidden).** Replace the simulator with a ledger learner. It reads only public values (wind, target x, its own landings, the published error).
- Round 1 power: `P0 = 0.076 x d` (d = distance in px; calc: power 65 lands 854 px away). Wind ignored.
- Angle: start 54. If the last throw ended on the fence, +6 (max 72). Two overshoots in a row, -3 (min 40).
- After each own throw with long/short error `e` (px along the throw direction): `P_next = P_prev - e / k`, `k` starts 22 px per power unit, refit from the last two throws once they differ by 4 or more power units, clamp 14 to 32.
- Wind: `cw` (px per wind unit) starts 0. After 3 own throws with at least 1.5 units of wind spread, fit the slope of long/short error against wind along the throw direction, clamp 40 to 180. Then add `-cw x (w_next - w_prev) / k` to the power.
- Keep the published jitter `AI_AIM_ERROR = 14` as the single skill constant. Difficulty = the constant: Easy 18, Normal 14, Hard 10. Converged hit rate (calc, window 250, 22 px per unit): 32%, 41%, 57%.

Expected hit rate by round (hand estimate, not measured): round 1 15 to 20%, round 2 20 to 25%, round 3 about 30%, rounds 4 and up 38 to 45%. A six-round match averages about 30%. This makes the match show both sides improving, as `product.md` asks.

**Verify.** (1) Static test: AI code contains no `simulateLandingX`, `estimatePowerForTarget` or call to the physics step. (2) 400 headless matches ledger AI vs a fixed dummy: hit rate round 1 in 10 to 25%, rounds 4 to 6 in 33 to 48%, rounds 4 to 6 at least 12 points above rounds 1 to 2, six-round average 28 to 38%. (3) Same 400 matches with Easy and Hard: converged rates within +/-6 points of 32% and 57%.

### Fix 3. Wind legibility for a human player (task item 4)

**Problem (code, not data).** `drawTopHUD` shows `steps = round(|wind|)` chevrons and a word (calm, breeze, wind, strong). **There is no number.** (The 2026-11-08 frame `(not published)` still shows "+2.4 m/s".) Rounding to an integer leaves +/-0.5 unit = +/-47 to +/-75 px of landing uncertainty (calc), a fifth to a third of the whole 250 px hit window, before any aiming error. The fifth chevron never lights because wind is -4 to +4. Audio normalises by 5 (`Math.abs(wind) / 5`), the scene by 4. Wind is re-rolled over the whole range every round, mean change 2.67 units (252 px), so last round's landing teaches the human almost nothing. A human also has no persistent memory of where past throws landed: the flight ribbon fades in 1.8 s.

**Minimal in-scene cue list.**

| # | Cue | Numbers | Cost |
|---|---|---|---|
| 1 | Signed number in the existing top gauge | `+2.4`, one decimal, 22 px bold, next to the chevrons. Chevron fill in half steps (fill = round(2|w|) / 2). Resolution 0.1 unit = +/-5 to 8 px. | text only |
| 2 | Pennant on the fence-post lantern | Pole 60 px above the lantern, flag 44 x 22 px. Lean `8.5 deg x w` (34 deg at 4), flutter +/-(2 + |w|) deg at 1.5 Hz. | canvas code, no art |
| 3 | Leaves and dust (already built) | leaf speed 105 px/s per unit, dust 65, fog 22 (`wind_fx.js`). Keep, check they are monotone in |w|. | none |
| 4 | Landing marks | A 20 x 28 px marker on the ground where each of the last 4 throws (2 per side) landed, with a 12 px label `R3 +2.4` (round and wind at the throw). Fade after 2 rounds. This is the same record the agents get from `get_history`. | 4 small objects |
| 5 | Wind change limit | `wind_next = clamp(wind + uniform(-2, 2), -4, 4)`, one decimal. Mean change 1.0 unit (95 px) instead of 2.67. | one line |
| 6 | Sound | wind bed gain `0.015 + 0.105 x |w| / 4` (`docs/wind_design.md`); change the `/5` to `/4`. | one constant |

Do not add an aim line or a landing prediction (owner rule, `product.md`).

**Verify.** Screenshots at wind -4, -1.5, 0, +2.4, +4: number text present (OCR or DOM-less pixel check inside the gauge rectangle), pennant angle within +/-2 deg of `8.5 x w`, marker count at most 4, nothing drawn inside the top bar except the gauge. Simulation: 10,000 wind steps, max |change| at most 2.0. Human check (cannot be automated): 3 testers, 10 throws each; hit rate in throws 6 to 10 is at least 10 points above throws 1 to 5.

### Fix 4. Time to kill per class (task item 6)

Target 4 to 6 hits at 100 HP. Cursed damage = x0.7. Expected curse coverage of a victim is `1 - (1 - p)^2` where p is the skeleton's hit rate (2-throw refresh): 0.91 at p = 0.7, 0.71 at p = 0.46, 0.64 at p = 0.4 (calc).

| Class | Damage per hit | Hits to kill | Cursed (x0.7) | Expected at p = 0.46 (x0.79) | In band? |
|---|---|---|---|---|---|
| Skeleton | 24 | 5 | 6 | 5.3 | yes |
| Wizard | 28 | 4 | 6 | 4.5 | yes |
| Cat (one shuriken) | 20 | 5 | **8** | 6.3 | edge |
| Knight (Fix 1, full 22) | 22 | 5 | 7 | 5.8 | edge |
| Hunchback (INVENTED 22) | 22 | 5 | 7 | 5.8 | edge |
| Reaper (INVENTED 18) | 18 | 6 | **8** | 7.0 | **no** |
| Bride (INVENTED 12) | 12 | **9** | 12 | 10.5 | **no** |

Changes:
- **Bride.** The wave must hit ONE unit (owner rule), so its power cannot come from hitting several. Proposed: window +/-200 px, damage 22 within 60 px of the centre, falling linearly to 8 at 200 px. Average over the window is 17.1 (6 hits), centre hit 22 (5 hits). Expected damage per throw relative to the skeleton: 400 x 17.1 / (250 x 24) = 1.14 (calc), inside +/-20%.
- **Reaper.** Raise the skull to 20 (5 hits). Ultimate follows the owner rule: three slashes of 0.5 x 20 = 10 each, total 30.
- **Frost curse.** The owner fixed "weaker for 2 throws"; the **-30%** is the main line's number. If Fix 4's simulation shows a skeleton win rate above 60%, change to -20% (expected multiplier 0.86 at p = 0.46; cat 5.8, reaper at 20 damage 5.8, bride 6.8 hits).
- Skeleton, wizard, cat, knight stay.

**Verify.** Unit test: `ceil(100 / damage)` between 4 and 6 for every class. 400 matches per class against a neutral dummy at aim error 14: mean hits to kill in 4.0 to 6.5.

### Fix 5. Energy pacing (task item 5)

**Problem.** Bar full in 3 to 7 rounds, mean 4.1 (R7, R13, R17, R24, R29, R35, R40). The six finished matches lasted 5 to 9 rounds (mean 6.2). Second use was never reachable. All of this is bot accuracy: at 71 to 82% hits fill is fast. At the AI's 46% fill takes 6.5 throws, at 30% about 10 (calc). The pip rule also counts a 3.7 knight chip as a full hit.

**Options (calc, expected throws to fill 3 pips).**

| Option | p = 0.7 | p = 0.46 | p = 0.4 |
|---|---|---|---|
| No change | 4.3 | 6.5 | 7.5 |
| **Pip needs at least 8 total damage (`ULT_PIP_MIN_DMG`)** | 4.3 (no effect on full hits) | 6.5 | 7.5 |
| Drain: lose 1 pip after 2 throws in a row with no pip | 4.6 | not computed | 11.1 |

**Recommendation.** Do the damage floor only; do not add the drain. The drain slows weak players by +48% at p = 0.4 and strong ones by +7% at p = 0.7, which punishes the player who needs the ultimate most. Blocked hits already do not count in the code (only `hero` collisions add a pip); the owner's question 1 can be marked answered "no". Re-measure with realistic-accuracy bots before adding anything.

Pacing target: first ultimate ready at 40 to 70% of the median match length; second use reachable in at least 25% of 4v4 matches (cap 2 per side).

**Verify.** 400 matches per aim error 8, 14 and 20: fraction of match length at which the bar fills, per error. Property test, 1000 runs: pips equal the count of throws whose total damage is at least 8.

### Fix 6. Fence (task item 3)

**Problem.** 5 of 41 throws blocked (12%): R3, R5, R6, R10, R25. Targets stood 75 to 245 px beyond the far face of the fence (impact x - error: 895..1025 + 204..375 = about 1100 to 1270).

**Geometry (calc).** A shot aimed at the ground centre of a target clears the fence only if it is higher than 250 px at x = 1025, so the target must be at least `250 / tan(descent)` past the far face: 145 px at 60 deg, 181 at 54, 210 at 50, 117 at 65. That fits the blocked rows (angles 50, 54, 60). A human who aims at the top of the body box (190 px) instead needs `x_c >= 1095 + 60 / tan(descent)` = 1123 (65 deg), 1130 (60), 1138 (54), 1155 (45). Units at x = 1070 to about 1130 can only be hit by almost vertical shots. Mirror for the human: AI shots at x_c > about 765 to 790 cannot hit. The AI's fixed 54 deg (see `executeThrow`: `angleDeg = isPlayer ? playerAngle : 54.0`) makes this worse: it never raises its angle.

**Changes.**
1. Knight shield stops at the fence (Fix 1).
2. Move limits: human `160..850` becomes `160..760`, AI `1070..1760` becomes `1160..1760`. These are also the slot 1 and slot 4 positions in the 4v4 layout of `roster_design.md` (760/160 and 1160/1760). It removes the dead zone.
3. AI raises its angle after a fence block (Fix 2).
4. Keep fence height 250, HP 100, -15 per hit. With 0.12 blocks per throw and two throws per round, a 1v1 fence loses about 3.6 HP per round; in 4v4 (8 throws) about 14 per round, so it breaks around round 7, which the roster design expects.

**Verify.** Reachability test with the real integrator: for every target x in the allowed range (step 10), angles 45, 50, 54, 60, 65, 70 and wind -4, 0, +4, find the power interval that hits the box without touching the fence. Pass: width of at least 3 power units (about 65 px) for all angles of 50 and up. Bot test: 2000 throws with a bot that raises the angle after a fence hit: blocked share at most 5%. Old limits fail the first test at x = 1070 to 1130 (record it before changing).

---

## 1c. WEAPON EFFECTS

### What exists (code facts)

- Trails: `weapon_trail_spear`, `weapon_trail_dart` (used for the shuriken), `weapon_trail_cannon`, `weapon_trail_shield` are emitted every 1/60 s step. On top there is the additive ribbon of `drawProjectile` (22 points, two passes), the dotted path of `drawThrownPaths` (fades 1.8 s) and `weapon_enchant_stardust` every 4th step. The cannon trail keeps about 60 particles alive (calc).
- Impact is the same for every weapon: legacy `spawnParticles` 55 red dots, `impact_burst` (scale 1.5, 41 particles), `hit_sparks` (20), `sprite_impact_flash`, `fx_impact_burst` 300 px, damage text. About **117 particles** per unit hit (calc). Palette comes only from the team (amber or violet).
- The knight's shield repeats the whole stack for **every** collision: a 6-bounce throw is about 700 particles, 6 hit-stops of 75 ms (450 ms frozen) and 6 numbers.
- `particles.js` rings are circles only (no ellipse), so a flat ground ring needs one new field (`squash`) in the record and in `particles_draw.js`. Sprite particles are square images (`size` is the half side).
- Shake exists only for the cannon release: 0.18 s, up to +/-7 px x and +/-4 px y. Hit-stop is a fixed 75 ms.
- The 2026-11-08 frame shows a bright blue sky with a near-white moon disc at about x 1050 to 1485, y 80 to 435 on the 1920 x 1080 canvas (converted from the 1280 x 720 frame; I did not open `assets/env/bg_graveyard.png`) and large cyan ghost flames beside both units. A power-85, 54-degree lob peaks at about y 291 and x 1070 (calc), so strong lobs cross the moon.

### Global rules and budget

| Item | Budget |
|---|---|
| Particles alive in `fxSys` | 500 (unchanged): trails 100, hits 120, aftermath and ultimates 200, ambient and face 60, reserve 20 |
| Legacy `particles[]` | cap 80 alive. Cuts: unit hit 55 to 14, shield block 45 to 14, fence 20 to 8, ground 12 to 6 |
| Particles per single unit hit (all sources) | at most 70 (now about 117) |
| Sprite particles on screen | 14. `fxList` flash sprites at most 2; skip a new one if the last is under 0.15 s old |
| Damage numbers alive | 6, hits on one unit within 0.3 s merge into a running total |
| Hit-stop | per weapon below; total at most 250 ms in any rolling 1 s |
| Shake | peak +/-10 px x, +/-6 px y, at most 0.30 s, at least 0.5 s between shakes |
| Flashes | at most 2 per second, none above alpha 0.25 over 40% of the screen |

**Readability rules.**
1. Under every projectile ribbon add one non-additive dark pass (`rgba(8,4,24,0.45)`, width +4 px). Additive light cannot show on the near-white moon.
2. Every projectile head has a 2 px outline `#0c0618` and an additive halo.
3. No two weapons share a hue: spear ice-white and pale cyan, cannon fire-orange with grey smoke, shuriken violet, shield gold, sound wave lilac, bell bronze, skull soul-green. Avoid trail tails in saturated blue (the sky) and plain cyan near the units (the ghost flames).
4. Test: screenshot each weapon mid-flight at three points (over the moon, mid sky, near the ground). Contrast ratio between the projectile pixels and a 40 px ring around them must be at least 3.0 (relative luminance, WCAG formula).

**Existing presets to change** (names stay, so tests keep working):
- `impact_burst`, `hit_sparks`, `muzzle_flash`: accept optional `hot`, `mid`, `dark` hex colours (validated by `isHexColor`), default to the team palette.
- `weapon_trail_dart` (now the shuriken trail): glow `#cdbbff` to `#4c1d95`, glints white to `#b8c4ff`, size 10 to 16, life 0.18 to 0.30. Darts are retired.
- `weapon_trail_spear`: `colorEnd` `#6aa6ff` to `#a9dcff`.
- `weapon_trail_cannon`: smoke `#8a8a99` to `#2a2a38`, life 0.4 to 0.7 (was 0.5 to 0.9), smoke on every 2nd step. Alive about 45 instead of 60.
- `weapon_trail_shield`: colours `#ffe9a3` to `#e67e22` (gold, away from the cyan flames), ring width 3.5, size 24 to 38.
- `landing_ring_dust`: accept `tint`.

**New presets** (7): `weapon_trail_wave`, `impact_wave`, `weapon_trail_bell`, `weapon_trail_skull`, `scythe_slash_fx`, `frost_shatter`, `bounce_ring` (needs `squash`). All new sound events below are also new entries for the sound line; I list the files they should reuse, and none needs a download.

### Per weapon

**1. Javelin (skeleton)** `proj_spear`
- Trail: `weapon_trail_spear` (streak 26 to 44 px, white `#f4fbff` to pale cyan `#a9dcff`, life 0.12 to 0.20 s) plus the dark pass. Alive about 14.
- Flight: rotates with velocity; `drawTipGlow` ghost-fire pulse every 90 ms stays; no wobble (it flies true).
- Impact: `sprite_impact_flash` 1.0, `hit_sparks` ice palette (`#ffffff`, `#9fd8ff`, `#3b6fe0`) 0.9, `impact_burst` 0.8, new `frost_shatter` (8 square shards, life 0.4 to 0.7, gravity 600) when the curse lands, `sprite_stardust` kept. Sound: `impact_unit`; curse mark `chime_single` file at volume 0.25 as new event `curse_apply`.
- Screen: hit-stop 75 ms, shake 0.
- Readability: dark pass and 2 px outline on the head.

**2. Cannon shell (wizard)** code-drawn ball
- Trail: `weapon_trail_cannon` (changed). Smoke 12 to 20 px growing to 36, ember 8 to 15 px `#ffd06a` to `#c2410c`, life 0.2 to 0.4.
- Flight: ball radius 27, no spin; orange outline widened to 3.5 px; additive halo radius 40, alpha 0.35, pulsing fuse.
- Impact: unit: `impact_burst` 1.5 (fire palette), `hit_sparks` 1.1, `sprite_impact_flash` 1.3, `fx_impact_burst` 300 px; ground: `landing_ring_dust` 1.2 and `smoke_puff` 0.8. Sound: `impact_unit_heavy`, ground `impact_ground_heavy`, fence `impact_fence`.
- Screen: release shake stays (0.18 s, +/-7 and +/-4). Unit hit: hit-stop 100 ms, shake +/-6 and +/-3 for 0.16 s. Ground: shake +/-3 and +/-2 for 0.10 s. Release and impact are more than 0.5 s apart.
- Readability: the ball's dark edge `#111827` disappears on dark cloud, so the halo and outline are required.

**3. Single shuriken (cat)** `proj_shuriken`, 58 px
- Trail: `weapon_trail_dart` (changed, violet). Alive about 16.
- Flight: flat spin at `performance.now() / 45` rad (about 3.5 turns per second), keep; add a violet halo radius 22, alpha 0.25; no wobble.
- Impact: `hit_sparks` steel palette (`#ffffff`, `#c0c8d8`, `#6b7280`) 0.8, `sprite_impact_flash` 0.7, no `impact_burst`. Sound: `impact_unit`.
- Screen: hit-stop 55 ms, shake 0.
- Readability: violet on blue sky is the weakest pair, so the white glints and dark pass are mandatory.

**4. Shuriken volley (ultimate, 5 shuriken at 6 each)**
- Trail: same preset at scale 1.2, `weapon_enchant_stardust` on every 4th step for the centre one only. Five trails alive about 80, inside the trail budget.
- Flight: sprite `ult_shuriken_shadow` (already requested in `ultimates_asset_requests.md`, item 7) at 48 px; until it exists use `proj_shuriken` at 48 px. Fan is +/-8 deg (code), so landing spread is about 70 px.
- Impact: first shuriken: `sprite_impact_flash` 0.8 and `hit_sparks` 0.5; the rest `hit_sparks` 0.35 only. One merged damage number. Sound: `throw_shuriken` once (not 5 times: the 3-per-band-in-150 ms rule), `impact_unit` for the first, `metal_bing` at 0.25 for each later hit 60 ms apart.
- Screen: first hit 75 ms, others 0; no shake.
- Rule check: each shuriken carries 1.5 x 20 / 5 = 6, so one unit hit by all five takes 30 = 1.5 x normal. Units hit by fewer take less. Confirm with the owner whether "each unit takes 1.5 x" means up to 30 per unit (current) or a flat 30 per unit hit.

**5. Bouncing shield (knight)** `proj_shield`, 62 x 92
- Trail: `weapon_trail_shield` (changed, gold). After the first collision add `weapon_rune_halo` at 0.4 on each bounce (10 particles).
- Flight: sideways coin flip kept (`|cos(t / 95 ms)|`). **Change the minimum width from 0.14 to 0.30** (edge-on width falls from 9 px to 19 px) so the shield does not vanish a third of each turn. Draw a 2 px bright rim line when the scale is under 0.4.
- Impact (per collision, `f` = damage share = bounceDmg / 22): `hit_sparks` gold palette at `0.35 + 0.6 f`, legacy dots `max(6, 55 f)`, `sprite_impact_flash` only on the first and last collision, numbers merged into a running total.
- Bounce: ground or fence contact: `shield_ricochet_sparks` 0.5 (11 particles) and `landing_ring_dust` 0.5; new `bounce_ring` (flat gold ellipse, radius 6 to 54, life 0.35 s, `#ffe9a3` to `#b45309`, width 3). Until `squash` exists use two `landing_ring_dust` calls at 0.4. Sound: unit hits `impact_unit`, ground `impact_ground`, with pitch 0.98, 1.00, 1.02, 1.04, 1.06 over the collisions (inside the 0.94 to 1.06 clamp) and `metal_bing` at 0.25 on skips.
- Screen: hit-stop 60 ms on the first collision, 30 ms on the middle ones, 90 ms on the last, stop adding once 250 ms is used in the last second. Shake only on the last: +/-4 and +/-2 for 0.12 s.
- Readability: gold on blue has good contrast; keep the dark pass.

**6. Bride's sound wave** (rules not final; owner: normal attack hits ONE unit)
- Projectile: no sprite. New `weapon_trail_wave` every 6th step: one ring (size 10 to 56 px, life 0.45 s, width 3, lilac `#e8d8ff` to `#9b7bff`, alpha 0.8), one soft glow 30 px, and with 40% chance one `text` particle (a note glyph, 18 px, life 0.9 s). Alive about 9. The wave follows the normal parabola; the ring centre jitters +/-3 px at 12 Hz to read as vibration.
- Impact: new `impact_wave`: three rings (radius 10 to 110, life 0.5, 0.6, 0.7 s, 80 ms apart), `sprite_impact_flash` 0.8. Effect scale = damage share (22 at centre to 8 at 200 px). Sound: new `throw_wave` (code-made sine glide 440 to 880 Hz, 0.5 s, 6 Hz vibrato, gain 0.25) and `impact_wave` (140 to 60 Hz thump 0.25 s plus `chime_single` at 0.3).
- Screen: hit-stop 60 ms, no shake.
- Readability: rings are pale and thin, so the dark pass is drawn under the ring particle's centre path; check the moon crossing in the contrast test.

**7. Hunchback bell** `proj_bell` (name provisional)
- Trail: new `weapon_trail_bell`: bronze dust (10 to 16 px, `#e6b450` to `#6b4a1a`, life 0.3 to 0.5 s, gravity 80) every step, and one ring (radius 14 to 40, life 0.3 s, `#ffe9a3`) every 0.25 s. Alive about 24.
- Flight: slow arc (speed x0.85, as proposed in `converge_characters.md`); sprite 90 px swings like a pendulum: rotation = 0.3 x velocity angle + 0.35 rad x sin(14 t); warm additive halo radius 36, alpha 0.3.
- Impact: `impact_burst` 1.4 bronze palette, `hit_sparks` 1.0, `sprite_impact_flash` 1.2, `landing_ring_dust` 0.8 at the feet, `smoke_puff` 0.7 three times along the 100 px knockback slide. Sound: `impact_unit_heavy` plus `bell_round` (cut at 1.0 s, 400 ms fade, volume 0.5, pitch 0.94 to 0.96) as event `impact_bell`; new `throw_bell` (low filtered-noise whoomp).
- Screen: hit-stop 120 ms, shake +/-9 and +/-5 for 0.25 s (the largest in the game, inside the peak).
- Readability: bronze on night is bright enough; the sprite needs the 2 px outline.

**8. Reaper skull** `proj_skull`
- Trail: new `weapon_trail_skull`: soul-green glow (10 to 16 px, `#d6ffe6` to `#3ddc97`, life 0.3 to 0.5 s, vy -20) every step and `sprite_ghostfire` every 3rd step. Alive about 26.
- Flight: slow tumble 6 rad/s (about 1 turn per second); soul-green halo radius 30, alpha 0.35; no wobble.
- Impact: `sprite_ghostfire` burst of 3 upward, `hit_sparks` soul-green 0.9, `sprite_impact_flash` 1.0, `sprite_mist` 0.6. Sound: new `throw_skull` (reuse the `throw_spear` file for now), `impact_unit`.
- Screen: hit-stop 75 ms, shake 0.
- Readability: soul-green differs from the skeleton's cyan and the wizard's poison green (`#5dff4a`); unverified by eye.

**9. Reaper scythe slashes** (ultimate, three slashes after a skull hit)
- Visual: three crescent sprites `reaper_slash_1..3` drawn on the target 0.25 s apart, each 0.18 s, scale 0.8 to 1.2, rotation -35, +25, -10 degrees, additive, alpha fading. New `scythe_slash_fx` adds `hit_sparks` 0.7 (soul-green, alternating direction) per slash.
- Flight: none (the slash appears at the target).
- Impact: white unit flash 0.1 s (existing hit pose), one `-10` number per slash (spacing 0.25 s so they do not merge).
- Sound: new `scythe_slash` x3 (code-made band-passed noise sweep 2 kHz to 600 Hz, 0.18 s, pitch 1.00, 1.03, 0.97, gain 0.35) with `impact_unit` at 0.3 under each.
- Screen: hit-stop 50 ms each (skull 75 + 150 = 225 ms in one second), shake only after the third: +/-3 and +/-2 for 0.10 s. Peak alive about 36 particles.
- Readability: slashes are drawn above the HP bar region only if they stay inside the unit's 220 px box.

### Colab requests (new sprites)

Conventions as in `docs/ultimates_asset_requests.md`: flat magenta `#FF00FF` background, no text, no watermark, thick clean outline, dark-fantasy 2D cartoon style. **All square canvases**, because sprite particles draw square. Already requested elsewhere and needed here: `proj_bell`, `proj_skull`, `reaper_scythe`, `reaper_slash_1..3` (`converge_characters.md` 3c). Make the three slashes 512 x 512 squares with the crescent inside.

| Name | Size | Prompt (one sentence) | Used by |
|---|---|---|---|
| `fx_frost_burst` | 256 x 256 | A burst of pale blue ice crystals radiating from a centre with a soft white glow, flat magenta background. | Javelin curse mark and impact |
| `fx_note_burst` | 256 x 256 | Four glowing lilac musical notes flying outward from a centre with small sparkles, flat magenta background. | Bride impact |
| `fx_soulfire` | 192 x 192 | A single wisp of soul-green ghost flame with a pale core and a curling tail, flat magenta background. | Reaper trail and impact |
| `fx_bronze_shock` | 384 x 384 | A flat radial burst of bronze-gold shock lines with a bright centre, flat magenta background. | Bell impact |

Priority: `proj_bell` and `proj_skull` first (without them those classes cannot ship). The four new effect sprites are optional; each effect has a code-made fallback (`sprite_stardust`, rings, glows) and the game must keep working without them.

---

## 1d. TEST PLAN

Quick smoke = 100 matches or 400 throws. Full = the number below. Matches are headless (no rendering), seeded, same physics as the game. A 95% interval on a rate near 0.4 is about +/-5 points at 370 throws; for a win rate near 50% it is about +/-5 points at 385 matches.

| Fix | Metric | Pass band | Sample |
|---|---|---|---|
| 0 Logger | one AI throw per round; every kill clipped; wind random in round 1 | 0 violations | 100 matches |
| 1 Knight | total damage after first unit contact; shield reversal after fence | 22.0 +/- 0.05 always; reversal never | 1000 property runs |
| 1 Knight | knight avg damage / mean of other classes (same aim error) | 0.8 to 1.2 | 2000 throws per class |
| 1 Knight | hit-stop sum in 1 s; particles of a 6-bounce throw | at most 250 ms; at most 250 particles | 20 scripted throws |
| 2 AI | no simulator calls in AI code | static grep, 0 hits | 1 |
| 2 AI | hit rate by round, ledger AI | R1 10 to 25%; R4 to R6 33 to 48%; R4 to R6 minus R1 to R2 at least 12 points; 6-round mean 28 to 38% | 400 matches |
| 2 AI | Easy, Hard converged rate | 32% and 57%, each +/-6 points | 400 matches each |
| 3 Wind | HUD number present, pennant angle, marker count, leaf speed monotone | angle within 2 deg; at most 4 markers; speed rises with |w| | 5 screenshots |
| 3 Wind | wind change per round | at most 2.0, mean 0.9 to 1.0 | 10,000 rounds |
| 3 Wind | human learning check | throws 6 to 10 hit rate at least 10 points above throws 1 to 5 | 3 testers, 10 throws each |
| 4 TTK | `ceil(100 / damage)`; simulated hits to kill | 4 to 6; mean 4.0 to 6.5 | static; 400 matches per class |
| 4 TTK | skeleton win rate vs each class | 40 to 60% (if above 60, apply curse -20%) | 400 matches per pair |
| 5 Energy | bar fills at this fraction of match length; first ultimate used | 40 to 70%; used in at least 70% of matches | 400 matches per aim error 8, 14, 20 |
| 5 Energy | pip count vs hits with total damage at least 8 | equal | 1000 property runs |
| 6 Fence | reachability map, all x in range, angles 50 and up | feasible power width at least 3 units | 1 grid run |
| 6 Fence | blocked share with an angle-raising bot | at most 5% | 2000 throws |
| 6 Fence | AI hit rate vs human x in 50 px bins | no bin below half the overall rate | 400 matches |
| Effects | peak particles alive; legacy array; sprites; hit stack | fxSys at most 500; legacy at most 80; sprites at most 14; one unit hit at most 70 | 3 scripted scenes per weapon x 10 |
| Effects | hit-stop and shake limits | 250 ms per second; shake within +/-10 and +/-6, 0.30 s, 0.5 s apart | same scenes |
| Effects | projectile contrast | at least 3.0 over the moon, mid sky and near ground | 9 screenshots per weapon |
| Effects | HUD occlusion | at most 5% of pixels changed inside the top bar and dock, effects on vs off | 1 screenshot per weapon impact |

Run order: Fix 0, then Fix 1 and Fix 6 (rules), then Fix 2, then the effects, then the human check for Fix 3.

---

## Owner decisions needed

1. Knight option A: in 1v1 the die sets the number of ticks, not the total damage. Yes or no.
2. AI without a simulator (owner question 5, `product.md` says yes). Yes or no.
3. Wind changes by at most 2 units per round. Yes or no.
4. If the skeleton tests above 60%: curse -30% becomes -20%. Yes or no.
5. Volley rule: each unit takes up to 30 (1.5 x), or exactly 30 per unit hit.

## Summary (6 lines)

1. The data is 41 rows, not 40; m6 is unfinished (4 wins, 2 losses, 1 unfinished); wizard average is 20.3 and the AI hits 46% of 37 throws; the cat-scatter explanation and the angle claim are not supported.
2. R15 and R34 show 48 damage from one AI javelin and R11 shows damage with a 713 px miss: fix the logger before more playtests.
3. Knight 6.0 per throw comes from unreliable hop-back hits, fence rebounds and paid ground skips; option A (free skip, fence ends the shield, deterministic flurry) gives about 11 to 17.
4. The AI is a perfect simulator from round 1; replace it with a ledger learner (jitter stays 14) and give humans a wind number, a pennant, landing marks and smaller wind steps.
5. Fence blocks are geometry (centre-aimed shots within 145 to 210 px of the far face); limit moves to 160..760 and 1160..1760, and stop the knight rebounding. Ultimate pacing is a bot artifact; add only an 8-damage pip floor.
6. Weapon effects: one palette per weapon, a dark pass under every ribbon for the moon, a 117-particle hit stack cut to 70, per-collision scaling for the shield, 7 new presets and 4 optional sprites.

## What I could not verify

- Nothing was run: no game, test or simulation. All "calc" numbers are hand arithmetic and may be off by a few percent.
- I did not open `assets/env/bg_graveyard.png` or the current build. Moon position and sky colour come from a 2026-11-08 frame. How any effect looks or sounds is unverified.
- Why R15 and R34 show 48 damage, why R11 shows damage with a -713 error, and whether round 1 positions were still gliding.
- Whether `assets/audio` holds `bell_round`, `chime_single` and `metal_bing` (`sound_mapping.md` says they are missing from some checkouts).
- Bride, hunchback and reaper numbers are the main line's INVENTED values or my proposals. `docs/roster_design.md` lists other new classes and `docs/review_reconcile.md` does not exist.
- Human wind difficulty: no data exists. The ledger AI's per-round hit rates are hand estimates.
