# Kiro task 51: human-vs-AI matches, AI and balance recommendations

Date: 2026-11-09. Files written: this one only. I did not edit `index.html`, `js/`, `scripts/`, `docs/game_mode.md` or `.kiro/steering/rules.md`. I did not use git, a shell or the web.

**Nothing was run.** This role has no shell, so every number below is a hand calculation from `(not published)` (12 matches, 93 rounds), the first-run table in `docs/human_vs_ai_report.md`, `docs/class_stats_v2.md`, and the code in `index.html` (`aiAttackNow`, `triggerAITurn`, the projectile loop, `executeThrow`, `stepDice`). Models are marked as models. The main line should re-measure before applying anything (section 7).

## 繁體中文摘要

1. **先修正資料**：摘要裡的「我 44%、AI 28%」把中毒、流血的小額傷害（每次 2 或 3 點）當成命中。只算真正的投擲命中：我 36/93 = 38.7%，AI 20/87 = 23%。AI 的紀錄次數把 6 次持續傷害算進去，我的紀錄次數沒有，兩邊算法不一致。
2. **AI 命中率**：實測 23%（95% 區間 15%～33%），低於目標 30%。主因是瞄準誤差 `AI_AIM_ERROR`，不是視野噪音。建議 18 改 16，`AI_VIEW_POS_NOISE` 150、`AI_VIEW_WIND_NOISE` 1.2 不動。
3. **傷害太高嗎**：以現在的 AI 看，不算高。比賽中位數 8 回合，在 8～12 的下緣。但是 82% 的命中是「爆擊」（33 次裡 27 次），因為判定框的頂面很寬，從上方落下的東西都先碰到頭。這不是技巧，而是幾何。建議把頭部判定縮窄（只算中心 ±35 px），保留 1.25 倍，傷害約降 8%，比賽長度約回到 8.5 回合。
4. **圍籬**：AI 要看圍籬，但只在「它自己瞄準的無誤差路徑會撞圍籬」時才拉高角度。不需要任何精確座標。
5. **職業**：巫師每回合傷害是其他三職業的約 1.8 倍，其中有一部分是因為職業表沒算中毒。建議毒傷 3 改 2。骷髏、蝙蝠、盾衛先不動。
6. **盾衛不丟盾**：兩種讀法，建議 A（舉盾格擋）。B（近距離盾擊）在現在的移動範圍內根本打不到：最近距離 400 px，盾擊最遠約 213 px。

---

## 0. Data corrections (read before the numbers)

Row-by-row check of the JSON against the HP of each unit:

| Finding | Evidence |
|---|---|
| The "28 percent" AI figure counts damage-over-time ticks as hits. The "44 percent" human figure does too (it is the count of rounds with any damage, 41/93). The recorded `aiHits` field counts AI ticks, the recorded `myHits` field does not. | AI ticks: m0 `3`, m2 `2`, m7 `3`, m10 `3,3`, m11 `2` (6 ticks, 26 rounds with AI damage, 20 real hits). Human ticks: m0 `2`, m1 `3,3`, m8 `2`, m9 `3` (5 ticks; 41 rounds with damage, 36 real hits, which equals the recorded `myHits`). |
| Ticks sit in the same row as the hit that causes them and one row after. | m5 row 1: `38` = crit 35 + first poison tick 3. m0: `32` = crit 30 + bleed 2, next row `2`. A new hit refreshes the status instead of stacking, so a chain of hits gets one tick per hit plus one trailing tick. |
| Match 4: logged human damage is 64, the bat has 90 HP and `aiHpLeft` is 0. 26 HP is missing, probably the killing blow in the last round. | Human hits in m4 may be 3, not 2 (human total 37/93). |
| Capped values are real hits: `7.4`, `8`, `5`, `11`, `19`, `24` are lethal damage cut to the HP left. | Sums match HP in m0, m1, m2, m5, m9, m10, m11. |
| No row says whether a unit threw. The AI does not throw in the round where the human kills it, and a knight AI may spend a turn on the sky shield. | AI throws are therefore at most 87 (93 minus the 6 rounds the human won on). |

Corrected rates, hits that are not ticks:

| | Hits | Throws (upper bound) | Rate | 95% Wilson interval |
|---|---|---|---|---|
| Human | 36 | 93 | **38.7%** | 29% to 49% |
| AI | 20 | 87 | **23.0%** | 15% to 33% |

Damage per real hit (rows contain the embedded first tick): human 955.8 / 36 = **26.6**, AI 599.3 / 20 = **30.0** (the summary's 23.6 / 23.7 divides by tick rows too). Total damage dealt per round: human 968.8 / 93 = 10.4, AI 615.3 / 93 = 6.6.

Per match (HP% left at the end; "cap" = 10-round limit):

| m | Human vs AI | Rounds | Result | Human hits | AI hits (real, recorded) |
|---|---|---|---|---|---|
| 0 | skeleton vs wizard | 8 | human win (33% vs 0%) | 3 | 2, 3 |
| 1 | wizard vs knight | 9 | **AI win** (0% vs 32%) | 2 | 3, 3 |
| 2 | bat vs skeleton | 7 | human win (62% vs 0%) | 4 | 1, 2 |
| 3 | knight vs bat | 10 | cap, human ahead (24% vs 2%) | 4 | 3, 3 |
| 4 | skeleton vs bat | 7 | human win (68% vs 0%) | 2 (3?) | 1, 1 |
| 5 | wizard vs skeleton | 3 | human win (62% vs 0%) | 3 | 1, 1 |
| 6 | bat vs knight | 10 | cap, human ahead (50% vs 19%) | 3 | 2, 2 |
| 7 | knight vs wizard | 10 | cap, human ahead (34% vs 4%) | 4 | 2, 3 |
| 8 | skeleton vs knight | 10 | cap, human ahead (100% vs 52%) | 1 | 0, 0 |
| 9 | wizard vs bat | 4 | human win (69% vs 0%) | 3 | 1, 1 |
| 10 | bat vs wizard | 5 | **AI win** (0% vs 39%) | 2 | 3, 5 |
| 11 | knight vs skeleton | 10 | human win in round 10 (72% vs 0%) | 5 | 1, 2 |

The human leads or wins in 10 of 12 matches and wins 6 of 8 finished ones (75%, interval 41% to 93%).

## 1. Is the AI's hit rate acceptable? Values for the three constants

**Answer.** A 30% AI against a 40 to 45% human is a good target. It gives a human win rate of about 60% (model below), not a coin flip and not a walkover. The AI is not there yet: it hits **23%** (interval 15% to 33%), and the human wins 75% to 83%, which the same model reproduces (76%). So raise the AI a little.

**Why the aim error is the knob and the view noise is not.**
- The hit window is wide and lopsided. A thrown object counts as a hit when its centre enters the 140 x 190 box (`|dx| <= 70`, `y` from `oy-190` to `oy`). A shot descends at a slope of about 1.6 (power 70, hand 110 px above ground). Measured along the ground landing point of the undisturbed path, relative to the unit centre, hits happen for landings from about **-70 to +190 px**, a 260 px window centred 60 px beyond the unit.
- The aim error is uniform in power. With about 26 to 28 px of landing per power unit, `AI_AIM_ERROR 18` spreads landings over about ±490 px, so the hit chance is about 260 / 980 = 26%, minus the effect of the stun penalty below.
- The view noise (±150 px) and wind noise (±1.2 units, about ±125 px at 104 px per unit) are small against ±490, so they sit on the flat top of the combined distribution and barely change the density at the window. Check against the main line's own numbers: exact view with error 14 gave 39%, random view with error 18 gave 30%, and 39 x 14 / 18 = 30.3%. The whole drop is explained by the error ratio; the noise contributed about 0 points.
- Stun: 82% of hits are head crits (section 2), so the AI is stunned and aims with error 18 x 1.6 on about 31% of its turns. That lowers its realised rate to about 0.88 of nominal.

**Predicted AI hit rate (hit rate = k / E).** Two calibrations, because the two sources disagree (the in-code comment says 30% measured in 1200 shots at E = 18; the 12 matches say 23%, interval 15% to 33%, so the data cannot reject 30%):

| `AI_AIM_ERROR` | Data-calibrated (k = 4.1) | Sim-calibrated (k = 5.4) | Mean |
|---|---|---|---|
| 18 (now) | 23% | 30% | 26% |
| 17 | 24% | 32% | 28% |
| **16** | 26% | 34% | **30%** |
| 15 | 27% | 36% | 31% |
| 14 | 29% | 39% | 34% |

**Recommendation.**

| Constant | Now | Recommended | Reason |
|---|---|---|---|
| `AI_AIM_ERROR` | 18 | **16** | Middle of both calibrations is 30%. If the head-hit change in section 2 is not applied, use 15, because stuns stay frequent and cost the AI about 12% of its rate. |
| `AI_VIEW_POS_NOISE` | 150 | **150** | No measurable effect on hit rate; it is the owner's "random view" rule. |
| `AI_VIEW_WIND_NOISE` | 1.2 | **1.2** | Same. A human reads an integer gauge (±0.5), so 1.2 is already less information than a human has. |
| `AI_STUN_ERROR_MULT` | 1.6 | 1.6 | Keep. |

**Win-rate model** (normal approximation, damage per round from the data, time to kill = HP / damage per round with a coefficient of variation of 0.4, which is what about 4 hits at a 39% hit rate gives):

| AI hit rate | AI damage/round | Mean match length (rounds) | Human wins |
|---|---|---|---|
| 23% (now) | 6.9 | 8.5 | 76% (observed 6/8 and 10/12) |
| 28% | 8.4 | 8.0 | 65% |
| 30% | 9.0 | 7.9 | 60% |

If the AI is raised and damage is not trimmed, the model puts the mean length just under 8 rounds. That is why section 2 belongs to the same package.

Side note for the product: the in-page AI keeps no memory between rounds (`aiAttackNow` has no history), so it does not "get better round by round" as `product.md` wants. That is a feature gap, not a tuning problem.

## 2. Is the damage too high? (owner question)

**Answer.** At today's AI strength, no. Kaplan-Meier on the 12 matches (8 finished at rounds 3, 4, 5, 7, 7, 8, 9, 10; 4 stopped at the cap) gives a median of **8 rounds**, a mean up to the cap of 7.75, and 33% of matches lasting past 10. The human needs HP 98.75 / 10.4 per round = 9.5 rounds on average. That is the low end of the 8 to 12 target, not above it. The finished-match average of 6.6 rounds is biased low because the four slowest matches were cut off.

Two things push the real hits-to-kill below the 4 to 6 band in `class_stats_v2.md`:

1. **The crit is not a head shot; it is the top of the box.** 27 of 33 clean single-hit damages (bat, skeleton, wizard, both sides, lethal-capped hits left out) are crits, **82%**. Geometry predicts about 65%: a descending object enters the box through its 140 px wide top face and that face is inside the "head" band (`HEAD_FRACTION 0.25`). Only shots that enter through the front face below the head band are body hits. So the average hit does 1 + 0.25 x 0.82 = **1.20 x** base, not the 1.0 the class table assumed, and 82% of hits stun. The main line's "skill-based head crit" is not what the code does.
2. **Poison and bleed are not in the class table.** A hit refreshes the status; at a 40% hit rate one hit costs about 1.6 ticks: wizard +4.8, skeleton +3.2. Wizard hits are therefore 28 x 1.2 + 4.8 = 38.4 on average, 37% above the nominal 28.

**Recommendation R2 (needs owner confirmation of the crit definition).** Make the head a head: count a crit only when the contact point is in the top quarter **and** within ±35 px of the unit centre. Keep `CRIT_MULT 1.25` and the 7 s stun. One-line change in the unit collision:
`const headHit = p.y <= opp.y - 190 * (1 - HEAD_FRACTION) && Math.abs(p.x - opp.x) <= 35 && !p.critDone;`
By geometry the crit share falls from about 65% (82% observed) to about **27%** (70 px of the 260 px window). Average hit damage falls from 1.20 x to 1.075 x base, about 8% less damage per hit once the flat poison and bleed ticks are included. Stun falls from about 80% of hits to about 27%. This makes the crit depend on aim, which is what the owner asked for.

Package effect (model, section 1 table method): AI at 30%, damage x 0.92 gives a mean match length of **8.5 rounds**, human wins about **60%**. Without R2 the mean length is 7.9.

If the owner prefers not to change the head definition, the alternative is `CRIT_MULT 1.25` to **1.15**, which gives about the same damage cut but keeps stun on 80% of hits. I do not recommend it: the stun stays a coin flip on every hit.

## 3. The fence (Question 2)

**Answer.** Yes, the AI should see the fence, but only for its aimed shot. It should not try to dodge the fence when its own aim error sends a shot into it; a human does that too.

- The fence is a fixed, visible object, not hidden state. Using its position and size is the same as a human seeing it. The rule needs no exact coordinates of any moving thing.
- The AI throws at a fixed 54 degrees. Humans may use 25 to 80. For a player standing at x of about 690 or more, the aimed path at 54 degrees still passes below the fence top (y 610) over x 895 to 1025:
  - AI 1300, player 700: path at x 895 is y 623, clips by 13 px.
  - AI 1160, player 760: apex y 655, clips.
  - AI 1700, player 760: y 672 at x 895, clips by 62 px.
  Those cases are the player standing in the last 70 px of the zone (160 to 760), about 12% of positions.
- Effect on hit rate: the window loses 35% to 57% in those positions, so about **-1.5 to -2 points** overall. Small, but the AI visibly lobs into the fence there, and the first recorded run had 5 of 21 landings on the fence (exact view, error 14).

**Fair rule (recommended).**
1. Build the aim as now with the seen (noisy, snapped) target and seen wind.
2. Test that aimed, error-free path against the fence: clear if its `y` is below 570 (40 px margin above the 610 fence top) everywhere in `x` 895 to 1025.
3. If it clips and `wallHp > 0`, try angles 60, 66, 72, 78 in turn, re-solve power, take the first that clears. If none clears, use 54.
4. Add the error afterwards, as now.
5. Pass the chosen angle into `executeThrow` (currently hard-coded 54.0 for the AI).

Check by hand: AI 1300 to player 700 clears at 66 degrees by 95 px; AI 1160 to player 760 clears at 74 degrees (minimum margin 63 px, at x 1025). 66 degrees does **not** clear the second case (y 621 at x 1025).

This step uses the same path predictor as the aim, so it depends on the open owner question about the simulator (Question 3, item 3). If the owner says "no simulator", use a crude rule instead: raise the angle to 66 when the seen target x is above 640 and 74 when it is above 720. I hand-checked only four position pairs for that rule, so treat it as a fallback.

## 4. Exact information left in the AI (Question 3)

Current state of the report's section 6, against the code as it stands now:

| # | Where | What it reads | Status | Minimal fix (public information only) |
|---|---|---|---|---|
| 1 | `aiAttackNow`, `seenTargetX` | `player.x` plus uniform ±150 px, then snapped to 36 px | Fixed since the report. Fair. | None. |
| 2 | `aiAttackNow`, `seenWindAi` | exact `wind` plus uniform ±1.2 | Fair. A human sees `Math.round(wind)`; noise ±1.2 is coarser than the gauge. | None. Optional strict parity: `Math.round(wind)` with no noise, and add 1 to `AI_AIM_ERROR` to compensate. |
| 3 | `estimatePowerForTarget` and `simulateLandingX` | the real integrator constants (`GRAVITY`, 13.8, `WIND_ACCEL`), 40 bisection steps | **Open.** This is a ballistic simulator; `product.md` says agents get none. The owner's open question 5 ("does the AI simulate, or not?") is unanswered, and `game_mode.md` says it does. Do not change until the owner answers. | If the answer is "no simulator": replace with a coarse flat-ground prior `power0 = 2.3 * sqrt(gap)` (ignores wind and hand height, so about 10% off) and correct it after each of the AI's own throws using where that throw landed (the AI sees its own landing, as a human does): `power += landingError / 28`. Expect the AI to be weak in rounds 1 to 3 (I estimate about 10% hit rate), so `AI_AIM_ERROR` must be re-tuned after. This is online adaptation from history, not machine learning. |
| 4 | `aiAttackNow`, launch point `ai.x - 58, ai.y - 110` | the AI's own state | Not a fairness issue. It is wrong for the knight (hand is 51 px forward, 73 px up, so shots land about 30 px short) and the wizard (70, 118, about 17 px long). Hit rate barely changes because the hit window is flat in that range. | Read the same per-class hand offsets `executeThrow` uses. Low priority. |
| 5 | `triggerAITurn`, knight shield | `historyTrajectories`, the recorded points of the last up to 4 player shots | **Public by rule.** `game_mode.md` says the last 4 enemy paths are remembered and the human snaps the shield to them exactly. The AI reads the same set. | None. It only reads the latest shot, already inside the 4. The AI never reads the human's shield (invisible to it, not used). |
| 6 | `triggerAITurn`, dice-move decision | `gap = Math.abs(ai.x - player.x)`, exact, used for the 900 px threshold | **Open (small).** | One helper `seenPlayerX()` (the noisy, snapped read from item 1) used here and in `aiAttackNow`, so the move decision uses the same random view. |
| 7 | AI ultimate | own `energy`, own `ultUsed` | Own state. Fair. | None. |
| 8 | Airdrop pickup | own `hp` | Own state. Fair. | None. |

Nothing in the 12-match data shows an exact-information effect (it has no seen-versus-true values to compare). The three items worth doing are 6 (cheap), 3 (after the owner decides) and 4 (cosmetic).

## 5. Class balance (Question 4)

**What the data can say.** Each class appears 3 times as human and 3 times as AI. Individual class win rates are not measurable at this size, and human-versus-AI skill is mixed into every result. What is measurable is damage output.

| Class | Human: hits / rounds, damage per round | AI: hits / throws, damage per round | Per round, both sides |
|---|---|---|---|
| wizard | 8/16 (50%), 17.0 | 7/22 (32%), 10.3 | **13.0** |
| bat | 9/22 (41%), 11.3 | 5/19 (26%), 7.1 | 9.3 |
| knight | 13/30 (43%), 9.0 | 5/29 (17% or more, shield turns unknown), 4.5 | 6.8 |
| skeleton | 6/25 (24%), 7.1 (8.1 with m4's missing 26) | 3/17 (18%), 5.0 | 6.2 |

- The wizard deals about **1.8 x** the damage per round of the other three together (13.0 against 7.3). Its hit rate (39% pooled against 29%) is not significant (p about 0.2). Its damage per hit is: wizard hits are 38 (crit + one tick), 31, 32.8, against 26 to 32.5 for bat and skeleton, and its 11 clean crits out of 12 hits is above the 82% overall figure. The model in section 2 gives the same direction (+7% over the four-class mean once poison is counted), so I treat the wizard as the one class to act on.
- The skeleton hits least (9/42, 21%, against 34% for the rest; p about 0.17). That is a weak signal and it is the opposite of the model, which puts the skeleton +14% (bleed and the frost curse). Do not change the skeleton on this data.
- Bat (-8% in the model) and knight (-13%) are low in the model and nothing in the data contradicts it, but the knight's real strength is the hidden sky shield, which neither this data nor the model covers. No change.
- The earlier "AI wizard 48%" was ticks: real 7/22 = 32%.

**Model power, hit chance equal for all, by class** (HP x damage per hit with crit factor and ticks, frost curse counted for the skeleton; hand model, ±15%):

| Class | HP | now (crit 1.20 x) | after R2 (crit 1.075 x) | after R2 + poison 2 |
|---|---|---|---|---|
| skeleton | 100 | 3490 (+14%) | 3160 (+15%) | 3160 (+16%) |
| wizard | 85 | 3264 (+7%) | 2967 (+8%) | 2830 (+4%) |
| bat | 90 | 2808 (-8%) | 2516 (-9%) | 2516 (-8%) |
| knight | 120 | 2664 (-13%) | 2388 (-13%) | 2388 (-12%) |

**Numbers to change in `js/class_stats.js`** (only after the main line applies the matching change in `index.html`; `scripts/test_class_stats.js` checks `CLASSES`, not `CURRENT`, so it will not catch a mismatch for you):

| Where | Now | Recommended | Why |
|---|---|---|---|
| `POISON_DMG` in `index.html` (wizard, later bride) | 3 | **2** | Cuts wizard ticks from 4.8 to 3.2 per hit. Only the wizard applies poison today. |
| `CURRENT.wizard.dmg`, `dTyp` | 28 | keep 28 | Hold; see below. |
| `CURRENT.skeleton.*`, `CURRENT.bat.*`, `CURRENT.knight.*` | as is | keep | See bullets above. |
| `CLASSES.*.special` | no `poison`, `bleed`, `crit` | add `special.poison = {tick: 2, ticks: 2}` to the wizard, `special.bleed = {tick: 2, ticks: 2}` to the skeleton, and a global `CRIT = {mult: 1.25, shareOfHits: 0.27}` once R2 is in | So `expectedDamage` and `powerTable` include them. Without these the table keeps reporting the wizard at -6% when it is at +7%. |

If the wizard still deals more than 1.3 x the other classes per round after R2, poison 2 and a re-measure, then cut `wizard.dmg` 28 to **26** (model parity). I do not recommend doing that blind.

`scripts/sim_balance.js` has no crit, stun, poison, bleed, slow, view noise or `AI_AIM_ERROR` in the page sense. Its results cannot confirm any of the numbers above.

## 6. A knight action where the shield is not thrown (Question 5)

Owner decision pending: list both, I recommend A.

**Reading A: Guard (舉盾格擋). A held-up block turn.**
- The knight keeps the shield in hand and raises it. It replaces the throw (a throw needs the shield), so it uses the turn. Move is still free before it. It cannot be combined with the sky shield (which takes the shield out of the hand).
- Effect: until the enemy's next throw resolves, any hit whose contact point is above the middle of the body box (`y <= unit.y - 95`) is blocked completely: 0 damage, no crit, no stun, no poison, bleed, slow or frost curse. Hits below the middle take full damage. By geometry that is about 75% of hits (82% of today's observed hits are head-band hits). If R2 narrows the head, the guard must still use the "upper half of the box" rule, otherwise it blocks about a quarter of hits and is useless.
- Limit: one enemy throw. It cannot be used two rounds in a row (visible "tired" mark). That stops turtling.
- Value (hand model, enemy hit rate 30% for the AI and 45% for a good human, 30 damage per hit including crit mix): saves 6.8 HP against the AI and 10.1 against a good human. The knight gives up one throw, worth about 0.40 x 20.8 = 8.3 HP (its measured hit rate and damage per hit). Net -1.5 against the AI, +1.8 against a good human, plus stun and tick prevention that I did not price at all. Close to break-even, not dominant.
- Energy and ultimate: a blocked hit is not a hit. Under the owner's latest rule (three successful hits, own hits only) the guard gives **no pip**. If the owner's open question 1 is answered "blocks count", give one pip per guard turn at most. The knight's ultimate is not designed, so nothing else interacts.
- Fair information: the raised shield is public (a visible pose and a state flag), unlike the invisible sky shield. The enemy AI may read the flag and aim a little short to land on the lower half; that is an aim offset of about 40 px using public information. The AI knight may choose Guard from public information only: its own HP below 50% and the last enemy landing (public record) within 200 px of its seen position, no more often than every other round. Nobody reads the enemy's plan.

**Reading B: Shield bash (盾擊). Close, shield stays in hand, 50 px knockback.**
- Damage: a flat 22 (the knight's measured average per hit is 20.8). Knockback: the shared 50 px rule from `class_stats_v2.md` section 3 (direct hit only, clamped to the zone, none on a lethal hit, no extra on ultimates). It counts as a successful hit: +1 pip. Block numbers: none.
- **Blocker.** It cannot be used in the current game. The closest legal centre-to-centre distance is 400 px (zones end at 760 and 1160), the fence is 130 px wide at 895 to 1025, and the knight's reach is about 143 px (shield hand 51 px forward plus the 92 px shield) plus the enemy's 70 px half-width: **213 px**. Even without the fence, the nearest the zones allow is 400. At the starting positions the gap is 660 to 1460 (triangular around 1060), and 3% of starts are within 760.
- Making it reachable means either moving the zones inward (a rule change for all classes, still not enough: the fence sets a floor of about 270) or turning the bash into a ground shock wave with a reach of 420 px. The wave is then a second ranged attack that cannot miss, and it is only available when both sides have walked to the middle. A guaranteed 22 plus knockback beats the throw's expected 8.3 by a wide margin, so it would need a strict gate.
- Fair information: all public (positions are read through the same noisy view by the AI).

**Recommendation: A.** It fits the existing zones, needs no rule change for other classes, costs the knight a throw, and is public where the sky shield is hidden, so the two do not duplicate each other. B only makes sense together with a change to the move zones that the owner has not asked for.

## 7. Package and what to measure

| # | Change | File | From | To | Needs owner |
|---|---|---|---|---|---|
| 1 | AI aim error | `index.html` `AI_AIM_ERROR` | 18 | 16 | no |
| 2 | Head hit narrower | `index.html` projectile loop | top quarter of the whole box | top quarter and `|dx| <= 35` | yes (changes how crit works) |
| 3 | Poison per tick | `index.html` `POISON_DMG` | 3 | 2 | no |
| 4 | Fence lob | `index.html` `aiAttackNow`, `executeThrow` | fixed 54 degrees | first of 54, 60, 66, 72, 78 that clears | after question 3 item 3 |
| 5 | Shared seen position | `index.html` `triggerAITurn` | exact gap | `seenPlayerX()` | no |
| 6 | Class table fields | `js/class_stats.js` | none | `poison`, `bleed`, `CRIT` | no |
| 7 | Knight action | none yet | none | Reading A or B | **yes** |

Expected after 1 + 2 + 3 (model): AI hit rate about 30% (26% to 34%), mean match length about 8.5 rounds, human wins about 60%, no class outside ±16% in the power table.

**Re-measure before accepting.** Log one line per throw: unit class, side, round, power, angle, seen x, seen wind, true x, true wind, contact type (`hero`, `wall`, `ground`, `shield_blocked`), contact height, base damage before ticks, crit flag. Then 300 AI throws against a still human-like target will settle the 23% against 30% question (interval ±5 points) and give the real crit share. Accept 1 if the AI projectile-hit rate, ticks excluded, is 27% to 33%; each step of 1 in `AI_AIM_ERROR` moves it about 2 points. Accept 2 if the crit share is 20% to 35%.

## 8. What I did not verify

- No script or page was run. Hit rates, intervals and the match-length model are hand calculations (normal approximation, coefficient of variation 0.4 assumed).
- The slope of 1.6, the 260 px window and the 27% crit share are my geometry at power 70 and 54 degrees. They shift with power and wind. The observed 82% crit share suggests the true window leans further beyond the unit than the model says.
- The k values 4.1 and 5.4 in section 1 come from one data set (87 throws) and one remark in a code comment (1200 shots, protocol unknown). Whether that sim counted ticks or stuns is not stated.
- The 12-match file has no landing positions, no powers, no stun flags and no throw/skip flags. Whether the AI knights spent turns on the shield is unknown, so the knight AI's 17% is a lower bound.
- Match 4's missing 26 HP is explained by guess only.
- The 82% crit count excludes knight hits (bounce splitting) and lethal-capped hits. 27 of 33 is a small sample (p about 0.03 against 65%).
- The fence examples cover four position pairs.
- The hand reach of 143 px for the knight is from `executeThrow` offsets and the shield size, not from the art.
- I did not look at `scripts/mcp_game_server.py`, so I do not know whether the engine's numbers match the page after these changes.
