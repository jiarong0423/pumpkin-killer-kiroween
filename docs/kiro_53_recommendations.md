# Kiro task 53: the necromancer (internal id `reaper`) as the fire thrower

Date: 2026-11-09. File written: this one only. I did not edit `index.html`, `js/`, `scripts/`, `colab/`, `docs/game_mode.md` or `.kiro/steering/rules.md`. I did not use git.

**Nothing was run.** This role has no shell, so I could not execute `node scripts/sim_balance.js`. Every number below is a hand calculation (models are marked). Section 7 says what the simulator can and cannot do for this class.

Naming (owner 2026-11-09): player-facing name is the NECROMANCER (死靈法師). Code, files and public-state ids keep `reaper`. Same black-robed hooded skull figure, no scythe.

## 繁體中文摘要

1. **普攻**：「幽冥火」(Soulflame) 一發綠色鬼火，傷害 **23**（沿用 class_stats_v2，不變），物理與巫師的砲彈完全相同（重力、風、判定框 140 x 190 都一樣）。落地不留地面火，地面火仍屬於巫師。
2. **特色（我推薦的一個）：黏人的燃燒。** 被打中的單位身上著火：**每個回合開始 2 點，共 3 次**（最多 6 點），再被打中只會重置成 3 次，不疊加，不會致死（最低剩 1 HP）。走位躲不掉，補血也不清除。巫師是「地面與範圍」，死靈法師是「單體、黏在身上」。
3. **大招「三魂火葬」**：空手、手指朝前，背後三團鬼火（綠變紫）飛出。是**一次出手、三團火球**，沿同一個瞄準角度與力度，各差 ±1.2 力度（約 ±36 px），**不是追蹤**。每團 11.5，三團全中 = 34.5 = 1.5 x 23。**取代**舊的三鐮斬（鐮刀被 owner 說無聊）。
4. **血量 105 不變**，移動不變。手算強度比其他六職業平均高約 +3%，比賽長度幾乎不變（約 8.5 回合，變動小於 0.1 回合）。
5. **美術**：先等 owner 選一頭版 idle。新圖 8 張：火球、命中閃光、燃燒身體火舌、4 張空手姿勢（蓄力、出手、受擊、大招）、頭像。**所有姿勢的手都是空的**，火球由程式畫在手心，所以不需要「無武器版」。
6. 要 owner 回答 6 題，第 10 節。

## 1. What I read, and what I could not find

Read: `owner_feedback_log.md` (rows "Reaper redesign", "Circling ghost fires", "Ghost fires and the ultimate", "Ghost fire colours", "Ghost fires belong to the REAPER", "Ghost fires go BEHIND the back"), `class_stats_v2.md`, `ultimate_rules.md`, `ultimate_mapping.md` (row 7), `kiro_51_recommendations.md`, `kiro_52_recommendations.md`, `art_style_guide.md`, `js/class_stats.js`, `scripts/sim_balance.js` (grep), and the status code in `index.html` (`applyPoison`, `applyBleed`, `tickPoison`, `tickBleed`, constants).

| Fact | Value | Source |
|---|---|---|
| Physics | `GRAVITY 980`, launch speed = power x 13.8, `WIND_ACCEL 72` px/s^2 per wind unit, wind -4..+4 | `index.html` |
| Hit test | projectile centre inside a 140 x 190 box; head = top quarter (47.5 px) | `index.html`, `HEAD_FRACTION 0.25` |
| Per-class physics | **none**: the client has one global gravity and one global wind constant; `speedScale`, `gravityScale`, `windScale` exist only in `js/class_stats.js` and `sim_balance.js` | grep of `index.html` |
| Statuses in the client | poison and bleed: 2-damage-class ticks at round start, refresh with `Math.max`, never kill (leave 1 HP). `POISON_DMG` is 3 in this checkout (kiro 51 asked for 2); `BLEED_DMG` is 2 | `index.html` lines 544 to 545, 1441 to 1457 |
| Reaper in class tables | HP 105, damage 23, skull, execute x1.5 at 30% HP, three scythe slashes of 11.5 | `class_stats_v2.md` |
| Wizard (what it keeps) | cannonball 28 + poison; chance of burning ground; ultimate = large explosion + molotov bottles; working fire widths 5 steps (shell) and 13 steps (ultimate) | owner log; kiro task 44 addenda 8 to 8e |
| Bleed owners | the owner log lists hunchback, **reaper (skulls)** and skeleton as bleeders | owner log |

Could not find or verify:
- **The wizard's burning-ground numbers** (chance, damage, duration). Kiro task 44 addendum 8 asks for them but no `docs/` file holds an answer. I only use the working widths from the owner log.
- **The circling-fire code.** The log says `drawBackFires`, `ORBIT_FIRE_CLASSES` and the `ult_fires` preset are built, but none of those names exist in `index.html` or `js/particles.js` in this checkout. I treat them as built on the main line and unchecked.
- How anything looks on screen. No image was viewed.

## 2. Normal attack: one flame at one unit (question 1)

| Item | Value | Note |
|---|---|---|
| Weapon | 幽冥火 Soulflame, sprite id `proj_flame` | A ghost fire ball, green (same green as the circling fires) |
| Damage | **23** to one unit | Unchanged from `class_stats_v2.md`. Band 21 to 30, still unique per class. Head crit x1.25 applies to this number only (28.75) |
| Status | burn on every hit (section 4) | Any contact point, head or body |
| Speed, gravity, wind | **1.0, 1.0, 1.0** | Identical to the wizard's cannonball and every other class. Max range at power 100, 54 degrees is about 1925 px (v2 table) |
| Wind effect | Flight of about 1.84 s at the opening distance (1162 px, power 78) gives a drift of 36 x t^2 = **about 122 px per wind unit**, so +-4 wind moves it +-488 px, exactly as for the wizard | The 36 is half of 72 px/s^2 |
| Hit box | 140 x 190 (half width 70), tested on the flame's centre; the drawn flame (about 64 px) does not widen it | Same as the cannonball |
| Launch point | hand offset 58 px forward, 110 px up | Placeholder `{fwd: 58, up: 110}` as in `class_stats.js`. Re-measure when the owner picks the one-head idle |
| On a unit | flash `fx_flame_impact`, the body catches ghost fire for the burn duration | |
| On the ground | green flare 0.6 s, three rising `sprite_ghostfire` for 0.8 s, then nothing | **No burning ground.** No state is created |
| On the fence | splutters out; fence costs 15 like any projectile; the fence does not burn | |
| On the sky shield | the flame dies on the bar; the shield loses one charge as for any projectile | |

Why the reaper gets no ground fire: the wizard already owns it (chance patch on the shell, molotov patches on the ultimate), the richness plan allows two ground patches at a time, and the owner wants a clean screen. Two classes filling that cap would also make the second player's patch fail to appear.

Why identical physics: `class_stats_v2.md` section 1 sets every wind and gravity factor to 1.0 on purpose, the client has no per-class physics, and the AI aims with the same integrator as the projectiles. Any other value needs new code in the client, in the engine (whose wind is the approximate constant `WIND_PUSH 67.5`) and in the AI.

## 3. A distinct niche (question 2)

Three candidates from the brief, compared:

| | A. Sticky burn (recommended) | B. Ghost fire ignores the wind | C. Low, fast flame |
|---|---|---|---|
| What changes | A status on the unit: 2 damage at each of 3 round starts | Flame uses wind factor 0 | Flame uses a higher speed and gravity factor |
| New physics code | **none** | per-class wind factor in client, engine and AI | per-class speed and gravity in client, engine and AI |
| Effect on hit rate (my variance estimate) | none | about +5% for the AI (its aim error dominates) to +9% for a careful human | same-shaped arc, flight time x0.82, wind drift x0.67 at gravity x1.5 and speed x1.22, so about +5% |
| Owner's wind wishes (wind should matter more; `WIND_ACCEL` was raised 48 to 72) | untouched | opposes them: the wind gauge becomes irrelevant for this class | halves the effect of the gauge for this class |
| Overlap with wizard | low | low | low |
| Fair information | counter visible on the unit | wind not needed | none |
| Cost to balance | Power +2.7% (section 6) | needs a new table | needs a new table |

**Recommendation: A.** It needs no change to the integrator, so `simulateLandingX`, the engine drift and the AI aim stay as they are. It is also the most readable difference on screen: the wizard's fire is a place (a patch you walk out of), the necromancer's is a mark on the unit (moving does not shake it off).

| Axis | Wizard (stays with the wizard) | Necromancer |
|---|---|---|
| Shot | iron cannonball with smoke, recoil, camera shake | ghost flame with a thin tail |
| Direct damage | 28 | 23 |
| Status | poison 2 x 2 (provisional: 3 in the checkout) | burn 2 x 3 |
| Ground fire | chance on the shell, molotov patches on the ultimate, area damage | none |
| Ultimate | large explosion + molotov bottles, multi-target, area | three-flame volley, single target |
| Colours | orange, purple hat | ghost green, purple when armed |

"Spreads to the next hit": I read it as "carries over": the next flame that hits refreshes the burn to 3. Real spreading to neighbours exists only in 4 v 4, which the owner has not confirmed. If wanted later: a flame hit also gives burn (no damage) to the nearest other enemy within 160 px. I do not recommend building it now, and the wizard's area role would start to overlap.

## 4. Burn status (question 3)

| Rule | Value |
|---|---|
| Constants | `BURN_DMG = 2`, `BURN_TURNS = 3` (round starts) |
| Application | any flame hit: `u.burn = Math.max(u.burn || 0, BURN_TURNS)` (same helper pattern as `applyPoison`) |
| Stacking | refresh, do not stack. A unit never has two burns |
| Tick | at each round start, 2 damage, `min(2, hp - 1)`: **never kills** (leaves 1 HP), like poison and bleed. The finishing blow must be a direct hit |
| Order at round start | poison, bleed, burn, one float number each. Worst case on one unit is 6 per round start |
| Not scaled by | the head crit, the frost curse, the heal (ticks are flat constants, as for poison and bleed) |
| Head crit | x1.25 applies to the direct 23 only. Burn is applied for a head hit and a body hit alike |
| Stun | a head hit still stuns (7 s next turn). Burn and stun are independent. A stunned unit still takes its ticks at the round start |
| Heal rain (sky target, 12% of max HP) and the potion | **do not clear burn.** Reason: the burn is at most 6 HP; a cleanse would add up to 6 HP to a 13 HP heal (about +45%) and remove the class's identity. Same ruling as poison and bleed in `kiro_52_recommendations.md` |
| Movement | not blocked, not slowed |
| Wizard burning ground | the wizard's patch uses patch rules and does not set this counter. Only the necromancer's flame sets `burn` |
| Burn totals | 0, 2, 4 or 6 extra damage per hit. Expected ticks per hit with refresh: 1 + (1-p) + (1-p)^2, so 1.82 at the 47% hit rate (3.6 HP), 2.11 at 33% (4.2 HP), 1.39 at 70% (2.8 HP) |

The tick is small and long on purpose. A weaker player gets more of the class's damage from the burn (4.2 HP per hit at 33%), a strong one less (2.8 HP at 70%), because a repeat hit refreshes instead of adding. That makes the class forgiving without raising its ceiling.

Consequence for the bleed assignment: the owner log gave the reaper's skulls the bleed. With the skull gone, bleed stays with the hunchback and the skeleton, and the necromancer has burn instead. Question 5 below asks to confirm.

Public state (agents and the human UI): `statuses` gets `{id: "burn", ticks_left, tick_damage}`. Burn is drawn as ghost-fire tongues licking up the body plus the float text "🔥 燃燒" on application and "-2" on each tick, and a small 3-2-1 counter beside the head. Poison drips and bubbles downward; burn flames rise, so the two are told apart by direction as well as by icon.

Colour risk, to the owner: ghost fire green, poison green and the heal rain green now share the screen. I keep the green because the owner asked for it. Separation by shape: rain falls as thin streaks, poison drips and bubbles, burn rises in tongues; the burn core is pale cyan-white.

## 5. Ultimate: the three ghost fires fly out (question 4)

Owner rule: the hand turns EMPTY with fingers pointing forward; the three ghost fires behind the back change colour (green to purple) and fly out. It is not a hand-held flame throw.

**Decision: one attack with three flames from one aim, not three seeking flames.**

| | One volley, one aim (recommended) | Three seeking flames |
|---|---|---|
| Aim | normal hold and release: angle follows the pointer, power from the hold | none; flames steer themselves |
| Fair information | the three paths come from the same integrator as every projectile; a published fan constant is the only extra number | needs a homing solver. That is a ballistic simulator in the engine, and an agent calling it gets a free hit |
| Feel first (product principle) | kept | removed: no correction loop |
| Cost | small: three projectiles instead of one, a fixed offset | a new steering rule in client, engine and AI |

| Item | Value |
|---|---|
| Name | 三魂火葬 Three-Soul Pyre; `ult_kind = soulfire_volley` (replaces `reaper_combo`) |
| Gate | the existing gate from `ultimate_rules.md`: three lit pips, own turn, armed from the menu, one per side per round, **max 2 per match**, spent at release (hit or miss), the throw gives 0 pips |
| Arming look | the three circling fires turn purple (existing hue-rotate), the label "大招 已備". The opponent never sees it armed, only the three green fires that mean "ready" |
| Release | pose `pose_reaper_ult`: empty hand, fingers pointing forward. The three fires lift from their back slots (the 92 x 40 px ellipse), glide to the hand point in 0.18 s as a cosmetic lead-in, then fly |
| Launch | flame 1 at +0.00 s, flame 2 at +0.15 s, flame 3 at +0.30 s, all with the pointer's angle. Wind is constant within a round, so the stagger changes nothing about where they land |
| Fan | power offsets **-1.2, 0, +1.2** (a fixed, public constant `ULT_FAN_POWER = 1.2`). At 1162 px range one power unit is about 30 px of landing (dx/dP = 2x/P), so the fan is about **+-36 px**, one move step. At 700 px it is about +-28 px |
| Hit box | each flame 140 x 190, tested separately; the fan is narrower than the box, so one aim can land 1, 2 or 3 flames on the same unit |
| Damage | **11.5 per flame, 34.5 for three** = 1.5 x 23. No extra bonus, no all-three crit (that is the skeleton's rule, not the owner's rule for this class) |
| Crit inside the ultimate | no x1.25 on the flames, so the total never exceeds 1.5 x. A head contact still stuns, once per unit per ultimate |
| Burn | applied once, on the first flame that hits; ticks are extra and not counted in the 1.5 x (as for the skeleton's bleed) |
| Frost curse | the 15% cut applies to the 11.5 per flame (it applies to the class's normal damage first, as in `ultimate_rules.md`) |
| Sky shield | each flame is a projectile: it costs the shield one charge per block. A 2-charge shield stops two of the three flames |
| Fence | each flame that reaches it costs the fence 15 (up to 45 of 100) |
| Replaces the scythe slashes? | **Yes, assumed** (the owner called the scythe boring). There is no skull trigger hit any more and no follow-up. The 3 x 11.5 split of the old slashes is kept as 3 x 11.5 flames |

Hits and damage by skill (model: a shared aim error e, uniform +-A px; flame i hits if |e + offset_i| is at most 70 with offsets -36, 0, +36; the box is simplified to 140 px wide, as in `class_stats_v2.md`):

| Skill (A) | P(0 hits) | P(1) | P(2) | P(3) | Mean hits | Mean direct damage |
|---|---|---|---|---|---|---|
| 210 (AI type, p 0.33) | 0.50 | 0.17 | 0.17 | 0.17 | 1.0 | 11.5 |
| 150 (observed, p 0.47) | 0.30 | 0.23 | 0.23 | 0.23 | 1.4 | 16.1 |
| 100 (bot, p 0.70) | 0.00 | 0.30 | 0.35 | 0.35 | 2.05 | 23.6 |

The mean is about 1.5 x the normal throw's direct expectation (exactly so at A = 210 and 150; 23.6 against 24.2 at A = 100, where the window is clipped by the aim range). It is a high-variance attack: at A = 150 there is a 30% chance of nothing and a 23% chance of the full 34.5. That fits an ultimate that is "spent even if it misses". If the owner finds a 30% total miss too harsh, widen the fan to +-54 px (power offsets +-1.8): in the same model P(0) falls to 0.17 and P(3) falls to 0.11, so it becomes steadier and rarely reaches the full 34.5. Narrowing to +-18 px does the opposite (P(0) 0.41, P(3) 0.35). I recommend keeping 36.

4 v 4 (flow unconfirmed): the owner said an ultimate hits MULTIPLE units, but also kept the reaper's combo single target "for now" and confirmed 1.5 x per unit hit. A fan of +-36 px cannot reach a neighbour at the 160 px minimum spacing, so the volley stays single target. A wider fan of +-160 px would let each flame catch a different unit, but then each unit takes only 11.5, which breaks "each unit hit takes 1.5 x". I do not propose it until the owner decides.

Sequence for the screen, in beats: arm (green to purple), release pose (empty hand, fingers forward), three purple flames lift and leave 0.15 s apart, three trails (the real flight path stays and fades as for any throw), impacts, burn flames on the target. No full-screen cut-in (owner wants a clean screen).

## 6. HP, movement and match length (question 5)

**HP 105 (provisional) stays. Movement stays:** zones 160 to 760 (human) and 1160 to 1760 (AI), dice 36 px per pip, one move per turn, moving does not use the turn, no knockback, no special movement. Burn does not slow or pin the unit.

### Power model (the method of `class_stats_v2.md` section 4, plus status ticks)

Power = HP x expected damage per throw. p = 140 / (2A). A status that refreshes delivers on average T_n(p) = sum over i = 1..n of (1-p)^(i-1) ticks per hit. All hand arithmetic.

Per class at A = 150 (p 0.467; bride 0.778, hunchback 0.549 from the speed factors), v2 expected damage plus the status ticks:

| Class | HP | v2 EDT | + status | EDT | Power | vs mean of 7 |
|---|---|---|---|---|---|---|
| skeleton (bleed 2 x 2, frost -15%) | 100 | 12.55 | +1.43 | 13.98 | 1398 | +9.6% |
| wizard (poison 2 x 2) | 85 | 13.07 | +1.43 | 14.50 | 1233 | -3.3% |
| bat | 90 | 12.13 | 0 | 12.13 | 1092 | -14.4% |
| knight | 120 | 9.20 | 0 | 9.20 | 1104 | -13.4% |
| bride (poison 2 x 2) | 75 | 16.14 | +1.90 | 18.04 | 1353 | +6.1% |
| hunchback (bleed 2 x 2) | 110 | 11.53 | +1.59 | 13.12 | 1443 | +13.1% |
| **necromancer (23, burn 2 x 3, no execute)** | 105 | 10.73 | +1.70 | **12.43** | **1305** | **+2.3%** |

(The necromancer's v2 value 11.59 included the execute factor 1.08; without it, 0.467 x 23 = 10.73, and burn adds 0.467 x 3.64 = 1.70.)

At the other two skill levels the necromancer is +3.1% (A = 210, Power 953 against 924 for the other six) and +3.0% (A = 100, 1895 against 1839). It stays within +3% at all three, which is the benchmark of the v2 table (+-12%).

Side finding, not part of this task: once poison and bleed ticks are counted, the hunchback is +13%, the bat -14% and the knight -13% at A = 150. That is outside the +-12% of the v2 table and agrees with `kiro_51_recommendations.md` (bat -8%, knight -13%).

Burn options I tried (A = 150):

| Option | Power vs the other six | Verdict |
|---|---|---|
| 23 + burn 2 x 2 | +0.5% | identical to poison and bleed, no identity |
| **23 + burn 2 x 3** | **+2.7%** | recommended |
| 22 + burn 2 x 3 | -1.1% | moves the damage off the v2 table for no gain |
| 22 + burn 3 x 3 | +5.9% | a tick of 3 is a new number to defend and the class gets stronger |
| 20 + burn 3 x 3 | -1.8% | 20 is below the v2 band (21 to 30) |

Levers if a later test shows the class above 58% wins: burn turns 3 to 2 (Power -2.1%), then HP 105 to 100 (-4.8%). If below 42%: HP to 110.

### Hits to kill (the v2 7 x 7 row for the necromancer)

Columns: skeleton 100, wizard 85, bat 90, knight 120, bride 75, hunchback 110, necromancer 105.

| Counting | Skeleton | Wizard | Bat | Knight | Bride | Hunchback | Necro | Sum |
|---|---|---|---|---|---|---|---|---|
| direct 23 only | 5 | 4 | 4 | 6 | 4 | 5 | 5 | 33 |
| with the expected burn (26.6 per hit) | 4 | 4 | 4 | 5 | 3 | 5 | 4 | 29 |

All cells are between 3 and 6, inside the hard band 3 to 8. `class_stats_v2.md` says the execute turned the knight cell from 6 to 5; without the execute the direct-only value is 6.

### Match length (the model of `kiro_51_recommendations.md` section 1 and `kiro_52_recommendations.md` section 4)

Baseline of the package: human 9.59 damage per round, AI 8.30, mean HP 98.75, mean length 8.5 rounds.
- Necromancer as the human: 9.59 x 1.027 = 9.85 per round. Time to kill 98.75 / 9.85 = 10.0 rounds against 10.3 (a one-sided figure; the mean of both sides stays near 8.5).
- Necromancer as the AI: 8.30 x 1.027 = 8.52 per round.
- Effect on the mean length: **under 0.1 round.** Burn does not create a stall: a unit at 1 HP still needs the same direct hit it would have needed without burn.
- The ultimate adds the same expected value as any other class (1.5 x a normal throw, twice per match at most), so it does not move the 8 to 12 target. Its variance is higher than the cat's volley because the three flames are correlated (section 5).

I did not use the sim. `node scripts/sim_balance.js --classes ...` accepts the key `reaper`, but its `reaper` is the old skull class with the execute, and the simulator has no status ticks at all (no poison, bleed or burn; the header says so), so it cannot show this design. To simulate it, the simulator needs a `special.burn` entry in `js/class_stats.js`, a tick step at round start, and a three-projectile ultimate. That is about 30 lines I did not write (outside the files this task names).

## 7. Fair information

| Item | What a human sees | What an agent gets |
|---|---|---|
| Pips | three ghost fires behind the back, one per lit pip | `ult_pips`, `ult_ready` |
| Armed | purple fires, only during the owner's own turn | `ult_armed` (never true when an agent decides) |
| Burn | flames on the body, 3-2-1 counter, float text | `statuses: [{id: "burn", ticks_left, tick_damage: 2}]` |
| Ultimate type | gold "✨ 大招：三魂火葬" text at release | `ult_kind: "soulfire_volley"`; history lists each flame as `strike` 1 to 3 with its landing x and damage |
| Fan | visible as three trails | published constants `ULT_FAN_POWER = 1.2`, `BURN_DMG = 2`, `BURN_TURNS = 3`, `ULT_MULT = 1.5` |
| Not exposed | seed, any landing predictor, trial throws | |

The AI necromancer aims with the same noisy view (position +-150 px, wind +-1.2) and the same aim error, and uses its ultimate by the public rule list in `ultimate_rules.md` section 2h. In 1 v 1 the "crowd" rule never fires. No homing, no simulator.

Recommendation on the screen: for the necromancer, hide the three pip dots above the head, since the circling fires are the pips. Otherwise two displays show the same number. Question 4.

## 8. Changes the main line must make (not done here)

| Where | Change |
|---|---|
| `HERO_PROFILES` (new entry) | `reaper`: hp 105, dmg 23, weapon `proj_flame`, launch `{fwd: 58, up: 110}` (placeholder) |
| status code | add `burn`, `BURN_DMG = 2`, `BURN_TURNS = 3`, `applyBurn`, `tickBurn` next to poison and bleed; reset in `resetGame`; tick order poison, bleed, burn |
| ultimate code | three projectiles, power offsets -1.2, 0, +1.2, stagger 0.15 s, 11.5 each, no crit multiplier, burn once; remove the skull-then-slash branch |
| `js/class_stats.js` and `colab/class_stats_v2.json` | reaper: `weapon 'proj_flame'`, `special: {burn: {dmg: 2, turns: 3}}` instead of `execute`, `ultKind 'soulfire_volley'`, `ultStrikes 3`, name 死靈法師 |
| `docs/ultimate_mapping.md` row 7 and `docs/ultimate_rules.md` `ult_kind` list | `reaper_combo` becomes `soulfire_volley` |
| Start screen, dock, top bar | player-facing name 死靈法師 / Necromancer; the id stays `reaper` |
| Colab | stop the `proj_skull` job; the scythe trail and any scythe slash art are no longer needed |
| `shared/constants.json` | not changed: all numbers here are class-level, not shared |

## 9. Art list for Colab (question 6)

Blocker: the owner has not picked a one-head idle (r8 had two heads and was rejected; r9 is the redraw). Nothing below is generated before that idle exists, because every pose must match it ("same character as the reference, same style and framing").

Style per `docs/art_style_guide.md`. Character images: chibi two-heads-tall, thick near-black outline plus a thin warm orange outer glow, flat three-tone cel shading, dark outfit with ONE saturated accent colour (deep indigo robe, violet-blue eye glow), large expressive eyes, small simplified hands, flat magenta `#FF00FF` background, no ground, no shadow, no text, no magenta or pink tones inside the subject. Poses: strictly side view facing LEFT. Objects: the object block (candle key light from the upper left, cool cyan rim, 12% margin).

Design decision behind the list: **every pose has an EMPTY hand.** The flame is the code-drawn sprite `proj_flame` placed at the hand point during wind-up and removed at release (resupplied 0.55 s later). This matches the owner's empty-hand ultimate, avoids painting a flame into the poses, and needs no `_unarmed` variant (no OpenCV step).

| # | File | Size | Content | Prompt core (English, appended to the style block) |
|---|---|---|---|---|
| 0 | `assets/units/unit_reaper_idle.png` | 1024 | Gate: the owner's chosen one-head idle, no scythe, empty hand | already in progress (r9, exactly one head) |
| 1 | `(not published)` | 256 | Thrown ghost flame: teardrop green flame ball, bright pale cyan-white core, dark green rim, one wispy curved tail, pointing right (rotated by velocity in game). Readable at about 64 px | "A single ghostly green flame ball with a pale cyan-white core, a dark green outline and one curved wispy tail pointing right, thick outline, flat magenta background." |
| 2 | `(not published)` | 512 | Hit flash: round burst of ghost fire with six curled tongues and a few sparks | "A round burst of ghostly green fire with six curled flame tongues and small sparks, bright white-cyan centre, thick outline, flat magenta background." |
| 3 | `(not published)` | 512 x 256 | Burn overlay: a row of three upright ghost-flame tongues of different heights, to be tiled along the body edge and flickered in code | "Three small upright ghostly green flame tongues of different heights side by side, pale core, thick outline, flat magenta background." |
| 4 | `(not published)` | 1536 x 1024 | Arm drawn back, **empty open palm facing up**, hood tilted, other hand in the sleeve | "The same hooded skull sorcerer as the idle reference, arm pulled back with an empty open palm turned up, facing left, same style and framing, no scythe, no weapon, flat magenta background." |
| 5 | `(not published)` | 1536 x 1024 | Arm thrown forward, fingers spread, empty hand, robe trailing back | same wording, "arm thrown forward with an empty hand and spread fingers just after releasing" |
| 6 | `(not published)` | 1536 x 1024 | Flinch: hood slipping, one arm raised, skull eyes squeezed | same wording, "flinching backwards after being hit" |
| 7 | `(not published)` | 1536 x 1024 | **Added for the owner's ultimate rule.** Arm extended forward, empty hand, fingers pointing straight ahead; robe flaring behind. No flames painted in: the three fires are drawn in code behind the back | "arm stretched straight forward with an empty hand and the fingers pointing at the viewer's left, robe flaring behind, no flames, no weapon" |
| 8 | `(not published)` | 512 | Head-and-shoulders portrait facing right, hood, **one** skull head, violet-blue eye glow, dark vignette corners | "A head-and-shoulders portrait of the same hooded skull sorcerer facing right, exactly one head, confident look, dark background." |

Not requested:
- **Burning ground patch.** The task lists it, but this design has no reaper ground fire. If the owner overrides, recolour the wizard's patch in code (the same hue-rotate already used for the circling fires). Colab art for it would be a duplicate.
- **Purple flame art.** The purple of the armed and flying fires is produced in code from the green sprite. This also avoids art in a violet that sits close to the magenta key (`scripts/key_magenta_items.py` could eat it). Keep the eye glow blue-leaning violet for the same reason.
- **Orbiting fire sprite.** The existing `fx_ghostfire` is used.
- **Flame tail and trail.** The `sprite_ghostfire` preset in `js/particles.js` already makes rising ghost-fire wisps.
- **Big-head reaction faces** (charge, shout, smirk, hit): not part of this task.

Sound: no new sound is designed here. Needed event names to map later: `flame_throw`, `flame_hit`, `burn_tick`, `soulfire_volley`.

## 10. Questions for the owner (one word each, my recommendation first)

1. Burn 2 damage x 3 rounds, sticks to the unit, no ground fire for the necromancer? **Yes.**
2. Ultimate = one volley of three flames from one aim (not seeking)? **Yes.**
3. It replaces the three scythe slashes, and the 30%-HP execute is dropped? **Yes.**
4. Hide the three pip dots above the necromancer's head, because the circling fires are the pips? **Yes.**
5. Bleed no longer belongs to the necromancer (burn replaces it)? **Yes.**
6. Keep green for the ghost fire although poison and the heal rain are also green (told apart by shape)? **Yes.**

## 11. What I did not verify

- No script, game or browser was run. All power values, hit chances, probabilities and match-length figures are hand arithmetic from the v2 model; they carry the same uncertainty as that model (I did not re-check the knight's range).
- The ticks-per-hit formula assumes the attacker throws every round with the same hit chance; it reproduces the 1.6 ticks per hit that `kiro_51_recommendations.md` gives for n = 2 at 40%.
- The 122 px per wind unit comes from 36 x t^2 at t = 1.84 s; wind also changes the flight time, which I ignored.
- The wind-ignoring (+5% / +9%) and fast-flame (+5%) hit-rate changes come from a variance model with guessed wind-reading errors (+-146 px for the AI, +-61 px for a human); they only rank the options.
- The three-flame hit table uses the simplified 140 px wide window; the real window is lopsided (kiro 51 section 1 gives roughly -70 to +190 px) and depends on power and wind.
- The fan width (30 px of landing per power unit at 1162 px, so 36 px for 1.2 units) is from dx/dP = 2x/P, not from `simulateLandingX`.
- Whether the circling-fire code exists: the log says yes, this checkout says no.
- The wizard's burning-ground numbers could not be found, so the "what stays with the wizard" column uses only the owner-log description.
- No image was viewed; the art list is a specification, and the reaper's real hand point is unknown until the idle exists.
- I did not read `scripts/mcp_game_server.py` or `mcp_stdio_server.py` beyond the wind constants, so I do not know how the engine would carry a three-projectile ultimate.
