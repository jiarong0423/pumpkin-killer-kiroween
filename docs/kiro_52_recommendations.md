# Kiro task 52: sky target that heals the hitter's whole side

Date: 2026-11-09. Files written: this one only. I did not edit `index.html`, `js/`, `scripts/`, `docs/game_mode.md` or `.kiro/steering/rules.md`.

**Nothing was run.** This role has no shell. Every number is a hand calculation from the code constants (`GRAVITY 980`, `V0_PER_POWER 13.8`, `WIND_ACCEL 72`, ground 860, fence 895..1025 x 250 tall), `docs/kiro_51_recommendations.md` (hit rates, match-length model) and `docs/class_stats_v2.md`. Models are marked as models. The main line should re-measure (section 9) before accepting anything.

## 繁體中文摘要

1. **預設的高度 250～520 px 剛好在一般投擲的拋物線中段。** 手算：54 度、距離 1000 px 的一發，經過隨機放置的目標的機率約 50%。也就是說「任何投射物都算」會讓雙方幾乎每回合白白回血，比賽會拉到 13 回合以上，而且先手的人類佔大便宜。建議把目標中心高度改成 **560～680 px**（高於 54 度一般投擲的最高點，約 430～500 px）。
2. **預設的 x 範圍 160～1760 有 59% 的機率讓至少一方「目標在自己身後」。** 建議改成：目標出現在兩個單位之間（中點 ±150 px），避開圍籬。
3. **回血量**：每個存活單位回 **最大血量的 12%（四捨五入成整數）**，不超過最大血量，死者不回，不清除中毒與流血。依 kiro 51 的模型，比賽長度約 8.5 回合變成約 11 回合，人類勝率約 60% 變成約 61%。
4. **AI**：只透過一樣的隨機視野（x ±150 px、風 ±1.2、高度 ±36 px），沒有彈道模擬。血量低於 60% 且目標在可達範圍時才改打目標，約 10% 的投擲。
5. **能量**：打中目標**不算**三下大招的命中。
6. **綠色治療雨**：新預設 `heal_rain`，約 1.2 秒，綠色，沿用現有 `heal` 音效事件與 `#2ecc71` 浮字。
7. 要你回答的只有 5 題，第 10 節。

## 1. What I read, and the gaps

Read: `owner_feedback_log.md` (last row: sky targets, not built), `kiro_51_recommendations.md`, `class_stats_v2.md`, `ultimate_rules.md`, `audio_event_map.json`, `art_style_guide.md`, `wind_design.md`, `js/particles.js` (presets), and `index.html` (projectile loop, `selectSkill('heal')`, `aiAttackNow`, `resolveRound`).

| Fact | Value | Source |
|---|---|---|
| Wind range, effect | -4..+4, reroll every round, `vx += wind * 72 * dt` | `index.html` (`WIND_ACCEL`) |
| Unit box | 140 x 190, centre inside box = hit | projectile loop, step 3 |
| Fence | x 895..1025, top at y 610 (250 above ground) | `shared/constants.json` |
| Hand height | 110 px above ground | `aiAttackNow` launch point |
| Existing heal (potion) | +35 HP, float text `🧪 生命恢復 +35 HP!` colour `#2ecc71`, `sprite_stardust` at y-150, `spawnParticles(... "#2ecc71", 25)`, sound `sfx.heal()` | `selectSkill` |
| Match length target | 8..12 rounds; package from kiro 51 gives 8.5 | kiro 51 section 2 and 7 |
| Hit rates | human 38.7% on units, AI 23% now, 30% after `AI_AIM_ERROR` 16 | kiro 51 section 0 and 1 |

Gap: the potion skill (+35, free, 2 charges) may stay (owner log section 4, item 6 is open). I did not model it. If it stays, matches get longer than in section 4.

## 2. Spawn (question 1)

### 2a. Height: default 250..520 is inside the shot corridor

Model (hand calculation, 54 degrees, hand 110 px up): a throw that lands on an enemy 1000 px away peaks 429 px above the ground; at 600 px the peak is 292; at 800 px it is 360; at 1200 px it is 497; at 1400 px it is 566. The path height above ground at 100, 200, ... 900 px from the hand (range 1000): 233, 326, 389, 423, 427, 401, 345, 260, 145.

A shot crosses a 120 x 120 box when `|path height - box height| <= 60 * (1 + slope)`. For a target at a random height in 250..520, the share of heights that a 1000 px shot crosses, by distance from the hand:

| x from hand | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 |
|---|---|---|---|---|---|---|---|---|---|
| share of heights crossed | 40% | 68% | 66% | 53% | 50% | 62% | 73% | 48% | 12% |

About 52% on average. A shot aimed at the enemy would heal its own side about every other throw, with no decision involved.

Whole-match effect with the default height (kiro 51 model, below): about 13 to 15 rounds and a human win rate of 70% to 80%, because the human shoots first each round.

**Recommendation: centre height 560..680 px above the ground (uniform, snapped to 20 px).** It is above the peak of a 54 degree throw to any enemy up to about 1200 px away, so the target needs a deliberate high lob. Box top stays at y 120 or lower on screen, below the top bar (keep-out to y 100). Fence top is 250, so the box never overlaps the fence.

| Throw type | Share of such throws that cross a target in 560..680 | Note |
|---|---|---|
| 54 degrees, enemy up to 1200 px | 0% to 1% | peak 497 plus tolerance 66 |
| 54 degrees, enemy 1400 px | about 40% | about 3% of starts have a gap this long |
| 65 degrees or steeper, enemy 1000 px | about 45% | peak about 646 |
| Mixed (assumption: 15% of throws are 65 degrees or steeper) | **about 8%** | `c = 0.08` in section 4 |

Reach at 54 degrees with power <= 100: the top of the band (680) is reachable for horizontal distance 627..1222 px; the bottom (560) for about 470..1250 px. Humans can steepen the angle. **The AI is fixed at 54 degrees in the code, so it needs the angle choice from kiro 51 item 4 (60, 66, 72, 78) before it can use targets at all.** Without that, it cannot reach targets closer than about 630 px.

### 2b. Horizontal position

Default (x uniform in 160..1760 outside the fence): with unit start zones 160..760 and 1160..1760 and a 108 px minimum distance in front of the hand, a target is in front of the human in 70.7% of spawns and in front of the AI in 70.7%. In 58.7% of spawns at least one side cannot shoot it without moving. (Calculation: left segment 160..855, reachable share rises linearly from 0 at x 268 to 1 at x 868, integral 287 of 695; the right segment is the mirror.)

**Recommendation:**
1. `x = (human.x + ai.x) / 2 + uniform(-150, +150)`, snapped to the 36 px grid. This keeps the horizontal distance of both shooters within about 100 px of each other.
2. Keep the box clear of the fence: if `|x - 960| < 125` move x to the nearer edge of 835 or 1085. The side alternates (first spawn goes to the human side, as for the airdrop).
3. Clamp to 160..1760.

Public positions only, so an agent can reproduce the choice. The engine draws it from the match seed.

### 2c. Drift with the wind

Wind units to px/s: **10 px/s per wind unit, applied for 4 s at the start of each round (the gust), then the target hovers.** That is 40 px per wind unit, so a target moves at most 160 px per round (wind 4), standard deviation about 92 px (wind is uniform in -4..4, sd 2.31). Over its two later rounds the cumulative sd is about 130 px, the maximum 320 px.

Why not continuous: the engine is turn based and an agent reads the target once per round. A target that moves while the shooter aims makes timing part of the aim, which the owner did not ask for. Engine rule: `x += 40 * wind` at the start of rounds 2 and 3 of the target's life, then clamp as in 2b (it never crosses the fence band). The browser eases that move over 4 s. A bob of +-6 px at 0.5 Hz is cosmetic and is not in the hit box.

For scale: wind_fx leaves move at up to 420 px/s, dust at 260 px/s, so 40 px/s reads as a heavy lantern.

### 2d. Lifetime and cadence

- Lives 3 rounds (rounds r, r+1, r+2), removed after the agent phase of the third. Never two at once. A new one appears at the next round start after it is hit or removed.
- Spawn index 1, 3, 5... is available to the human first; 2, 4, 6... is locked for the human until the agent phase of the spawn round (it fades in during the human phase). Reason: with equal hit chance p the side that shoots first gets the target with probability 1/(2-p): 56% at p 0.2, 59% at p 0.3. Alternating cancels it.
- Optional safety valve: no new target from round 11. It only trims the long tail. Not used in the numbers below.

## 3. Hit box and interactions (question 2)

| Item | Rule |
|---|---|
| Box | 120 x 120 px centred on the target. Sprite drawn 128 x 128. |
| Hit test | Swept: the segment from the projectile's previous to its current position intersects the box. At power 100 a step is 23 px; a point test would still work for a 120 box, but the sweep makes the result independent of step size, which the engine needs. |
| What counts | Any projectile of either side, any weapon. |
| Ultimates and multi-hit | One heal per target. The target is removed on the first hit. A multi-projectile ultimate (cat's 5 shuriken, skeleton triple shot) hits once: the first projectile removes it. The knight's bouncing shield heals once, on the first pass. |
| Unit hit after passing through | **Both count.** The projectile is not absorbed. The heal is applied at the moment of the pass, then flight continues and the normal unit hit, crit, status and energy rules apply. A pass-through is rare with the new height band (about 8% of throws cross it), so it is a bonus and not a way to farm. |
| Fence | The fence stops the projectile first if the path reaches it earlier. The target box (bottom at y 340 or higher) is far above the fence top (610), so they never overlap. |
| Floating shield | Whatever the path meets first wins. If the shield bar (y about 430) blocks the projectile before it reaches the target, the target is untouched. A path that reaches the target first heals, then may be blocked. The sky shield does not protect the target. |
| Ground | Not relevant. |
| Own side | Friendly fire does not apply: a bride swarm that passes the target heals the caster's side, no change. |

Hit chance (model): window in power units for a 120 box is `60 * (1 + slope) * P / K0` where `K0 = D*tan(angle) - h` (px), `P` the needed power, `D` the horizontal distance. At 54 degrees and a target 450 px above the hand: D 654 gives 11.2 units, D 800 gives 9.9, D 1000 gives 8.6, D 1200 gives 7.7. A unit's window is about 9.6 units. So **a 120 box makes the target about as easy as a unit** at middle distances. With the human's error (uniform +-12.4 units, calibrated to 38.7%) that is `p_h` about 0.40; with the AI (+-16 units plus view noise) `p_a` is about 0.27 before the height noise of section 5 and 0.25 after (the value used in section 4).

Box sizes by the same formula: 100 gives 0.83 x those windows (human 0.33), 140 gives 1.17 x (0.47). I keep 120.

## 4. Heal, statuses and match length (question 3)

**Rule: every living unit of the hitter's side is healed by `round(0.12 * maxHp)`, never above `maxHp`. Dead units get nothing. Poison and bleed are not cleared and keep ticking.**

| Class | Max HP | Heal |
|---|---|---|
| bride | 75 | 9 |
| wizard | 85 | 10 |
| bat | 90 | 11 |
| skeleton | 100 | 12 |
| reaper | 105 | 13 |
| hunchback | 110 | 13 |
| knight | 120 | 14 |

Percent, not flat: `class_stats_v2` balanced classes by HP x damage. A percent heal multiplies every class's effective HP by the same factor and keeps that balance; a flat 12 would give the bride +16% and the knight +10%.

Statuses: do not clear. Poison and bleed are 2 damage for 2 round starts (4 HP). Clearing them adds a rule, removes identity from the poisoning classes, and is worth only about 2 HP on average. The tick at the next round start applies after the heal, and a heal never revives (hp 0 stays 0).

### Match-length model

Same model as kiro 51 (time to kill = HP / damage per round, coefficient of variation 0.4, normal approximation). Package baseline: human damage 9.59/round, AI 8.30/round, average HP 98.75, giving 8.5 rounds and a 60% human win rate.

Assumptions (all mine, unverified): the human shoots the target in `u_h` of rounds when hurt, the AI in `u_a`; a diverted throw deals no damage; a deliberate heal wastes 10% to the cap, an accidental one 40%; accidental crossing `c = 0.08`; `p_h = 0.40`, `p_a = 0.25`.

| Case | Heal | u_h / u_a | Mean length | Human win |
|---|---|---|---|---|
| Baseline, no targets | | | 8.5 | 60.0% |
| Diversion only, no healing | 0 | 0.15 / 0.10 | 9.8 | 58% |
| Recommended | **12%** | 0.15 / 0.10 | **11.0** | **61.3%** |
| Lower heal | 10% | 0.15 / 0.10 | 10.8 | 60.3% |
| Higher heal | 15% | 0.15 / 0.10 | 11.3 | 62.8% |
| Default height band (c = 0.5 human, 0.4 AI), 12% | 12% | 0.15 / 0.10 | 13.4 | 81% |
| Stress: both sides enthusiastic, 12% | 12% | 0.30 / 0.30 | 15.2 | 71% |

Reading: diversion costs about 1.3 rounds, healing about 1.2. The recommended setting sits 1 round under the upper limit, with 2.5 rounds of margin over the lower one. The stress row breaks the limit; it needs the re-measure in section 9 and the safety valve of 2d if real play looks like that. At 12% a deliberate shot at the target is worth about half of a shot at the enemy for the human (0.40 x 10.7 x 1.15 / 9.59 = 0.51) and 0.28 for the AI, so rational play uses it mostly when hurt.

4 v 4 (flow unconfirmed): one hit heals up to four units, so the same 12% is worth about 2 x a normal throw when everyone is hurt. For parity use about 8%. I do not recommend building that number before the owner confirms 4 v 4.

## 5. Fair information and the AI (question 4)

**Human:** sees the target sprite, its position, its remaining rounds (a small number on it, 3, 2, 1) and the wind. Nothing hidden.

**Public state (agents), new block `sky_target`:** `present`, `x`, `y_above_ground`, `rounds_left`, `box` (120 x 120), `first_shooter` (`player` or `ai`), `locked_for` (side that cannot hit it yet, or null). Not exposed: the seed, a landing predictor, a trial throw. History records each throw's `target_hit` (true or false).

**AI view (same random mapping the owner taught for units):**
- target x: true x plus uniform +-150 px, snapped to the 36 px grid (as built for the player's position);
- wind: true wind plus uniform +-1.2 (as built);
- target height: true height plus uniform **+-36 px** (one grid cell). I use less than 150 because the band is only 120 px tall (560..680): +-150 would hide it completely. For the x axis, 150 px is 9% of the 1600 px range; 36 px is 30% of the 120 px band, which is already more relative noise than x. This is my choice; the owner may want 150 on both.

Effect on the AI's hit chance (model, needed power about 90, window about 8.6 units, aim error +-16 units, needed-power sensitivity to a height misreading about 0.07 units per px):

| Height noise | Extra power error | AI hit chance on the target |
|---|---|---|
| 0 | 0 | 27% |
| +-36 px | +-2.5 units | 25% |
| +-75 px | +-5 units | 22% |
| +-150 px | +-10 units | 15% |

(At +-150 the AI hits the target 15% of the time instead of 25%, which moves the share of heals about 4 points toward the human.)

No simulator: the AI uses the closed form that the owner-approved flat prior already uses, extended by the visible height: equivalent flat range `R = D / (1 - h / (D * tan(angle)))`, then `power = 2.32 * sqrt(R)` at 54 degrees, then corrected by its own last landing offset (public). That formula is the same kind of rule as `power0 = 2.32 * sqrt(gap)` in kiro 51 section 4 item 3. It needs the angle choice (kiro 51 item 4). If the owner decides even this is a simulator, the AI does not shoot targets and the heal goes only to the human; I would then lower the heal to 8% (human only).

**When the AI shoots the target instead of the unit** (all public information, checked at the start of its turn; rules 1, 2 and 3 must all hold):
1. A target is present, not locked for the AI, and its seen distance is inside the reach window (seen D between 630 and 1200 px at 54 degrees, or the matching window for the chosen lob angle).
2. Its own side HP, summed, is at or below 60% of the side's max HP (so the heal is not mostly wasted at the cap).
3. And at least one of: the enemy's last landing was within 150 px of the AI's unit (it is under pressure, from the public record); or the target has 1 round left and the AI's own last throw missed the unit by more than 200 px (the attack is not dialled in).

Otherwise it attacks the unit. Expected `u_a` about 0.10 (my estimate from the HP distribution in the 12 matches: the losing side is under 60% for roughly the last 40% of a match, and rule 3 trims that to about a quarter). The knight AI never spends a defend turn on this.

## 6. Energy (question 5)

**Recommendation: a target hit does not count as a successful hit for the three-hit ultimate.**

- The log says "three successful hits" and `ultimate_rules.md` section 0 counts a hit on a unit once per throw. A heal is not damage and is not on a unit.
- Counting it would add 0.15 x 0.40 = 0.06 pips per round for the human and make heals feed the ultimate, so the side that heals also gets its ultimate sooner. With the shot already giving a heal, that is a second reward.
- If a throw passes the target and then hits a unit, the unit hit counts once as always, and the target adds nothing.
- Cost of the other answer: the ultimate (max 2 per match, 1.5 x damage per unit) would arrive about 1 round earlier for a side that likes targets.

The target hit also does not count toward the cat's "3 dodged shots" or the knight's "3 sky-shield blocks".

## 7. Green healing rain (6a)

### 7a. Preset `heal_rain` (new, to be written in `js/particles.js` by the particle owner; names and numbers below)

One call per healed unit, `(x, y)` = the unit's foot point, `scale` default 1.

| Layer | Count | Shape | Start | Motion | Size | Life | Colour | Blend |
|---|---|---|---|---|---|---|---|---|
| Drops | 28 (`cnt(28, s)`) | `streak`, length 18..30 px x scale | x uniform in unit foot +-70 px, y = foot - 190 - uniform(240, 420) x scale | `vy` uniform 380..460 px/s, `vx` 0, drag 0 | length constant | `(distance to head height + 60) / vy`, about 0.9..1.2 s | `#c8ffd9` to `#2ecc71`, alpha 0.9, fade 0.25 | GLOW |
| Motes | 8 | `circle` | same band, start at head height | `vy` -10..-40 (rise), gravity -20 | 2.5..4.5 px to 0.5 | 0.8..1.2 s | `#9dffb8` to `#2ecc71` | GLOW |
| Ground ring | 1 | `ring` | foot | none | 6 px to 70 px x scale | 0.6 s, alpha 0.6, lineWidth 3 | `#c8ffd9` to `#168a4a` | GLOW |
| Glow on the body | 1 | `glow` | unit centre (foot - 95) | none | 60 px to 90 px | 0.5 s, alpha 0.35 | `#9dffb8` | GLOW |
| Stardust | 1 | `sprite_stardust` (existing) | foot - 150 | existing | `scale 1.0` | existing | existing | GLOW |

- Total length about 1.2 s (the longest drop). 4 healed units: 4 x (28 + 8 + 3) = 156 particles, well under the 1500 cap. Draw order after units, before float text.
- Fall speed 380..460 px/s. For comparison `dart_rain` uses 950..1350 px/s; slower reads as gentle rain.
- Palette: the potion uses `#2ecc71`. The poison presets use yellow-greens (`#3fbf3f`, `#9dff7a`). Heal rain is cooler and lighter (mint `#c8ffd9` core, `#2ecc71` body, dark `#168a4a` end) so the two statuses are not confused.
- Wind: add `wind * 6` px/s to `vx` of the drops, so the rain leans a little with the wind (about 24 px/s at wind 4, 28 px over its life). Optional.
- Fairness for readability: rain falls on every healed unit of the hitter's side at once, so with 4 v 4 the screen shows four columns. The 28-drop count is per unit and capped at 112 drops in total.
- Reduced motion or a clutter setting: halve the counts, keep the ring.

### 7b. Float text

One text per healed unit, same style as the potion: `{ text: "+N HP", color: "#2ecc71" }` above the head (`unit.y - 200`), using `damage_number` (amount N, colour `#2ecc71`, 30 px, 1.1 s). One shared line above the target when it is hit, `🌿 全隊回復！` colour `#2ecc71`, at the target position. Full heal reached: `滿血`, colour `#c8ffd9`, instead of `+0`.

### 7c. Sound

Reuse the event **`heal`** from `docs/audio_event_map.json` (`heal_chime`, file `heal_harp.ogg`, synth `chime_two`, sparkle `shimmer`, volume 0.55, priority 3, duration 1.0 s, no cooldown, with the 200 ms `chime_single` layer). Trigger it **once per hit**, not once per healed unit, so four units do not stack four chimes. Keep this one sound only. A synthesized fallback already exists (`oldSfx.heal`). If the owner wants a distinct cue later, add a new event `sky_target_hit` instead of editing `heal`.

Spawn cue: none. `ultimate_ready` would be misread as the player's own ultimate, and `shield_place` would blur with the shield. The owner wants a clean sound scene.

## 8. Art list for Colab (question 6)

Style per `docs/art_style_guide.md` section 二 (objects): thick near-black outline, flat three-tone cel shading, warm candle key light from upper left with a cool cyan rim, one centred object, 12% margin, flat magenta #FF00FF background, no ground, no shadow, no text, no magenta tones inside the subject. Object prompt block from section 四 applies.

| # | File (proposed) | Content | Size | Notes |
|---|---|---|---|---|
| 1 | `(not published)` | A floating jack-o-lantern balloon: small pumpkin lantern hanging from a bat-wing balloon or a ghost orb with a green flame inside, dark body, one saturated accent: **soft green** glow (so it reads as "heal" and is different from the orange of pumpkins and the cyan of the shield) | 1024 px, drawn 128 px | Facing front, symmetric (no mirror needed). Strong silhouette against the night sky. |
| 2 | `(not published)` | The same lantern, one frame, 40% opacity with a rune ring (materialising) | 1024 px | Used while the target is locked for one side. Can be produced from #1 by the engine at alpha 0.4 with `sprite_rune_circle`, so this one is optional. |
| 3 | `(not published)` | Hit flash: a round burst of green light with six short rays and a few leaf-like sparks | 1024 px, drawn about 200 px | Replaces `fx_impact_flash` for this hit only. |
| 4 | `(not published)` | One soft green rain streak with a bright core, vertical | 256 px | Optional picture for the rain; the plain `streak` shape already works, so only if the owner wants more texture. |
| 5 | `(not published)` | A flat green rune ring for the ground under each healed unit | 1024 px | Optional; `sprite_rune_circle` exists in other colours. |

Minimum for the first build: #1 only. The rest can be drawn by presets. All art by Colab; none by Kiro or code. No third-party assets.

## 9. How to measure it (main line)

1. Log one line per round: `target_present`, `target_x`, `target_h`, who shot, `target_hit`, `crossed_by_unit_throw` (target hit by a throw aimed at a unit), heal per unit, HP before and after.
2. Run 300 matches of human-like bot against the current AI, with and without targets.
3. Accept if: mean length 9.5 to 12; human win rate 55% to 66%; accidental share (`crossed_by_unit_throw`, of all target hits) under 25%; the first-shooter side gets 50% +- 5% of the targets after alternation.
4. If length is over 12: lower the heal to 10% first (costs 0.2 rounds), then set the optional round-11 cutoff, then reduce `u` by lowering the AI rule threshold from 60% to 50%.
5. If accidental hits are over 25%: raise the band bottom from 560 to 600.

## 10. Questions for the owner (one word each, my recommendation first)

1. Move the target height band to 560..680 (above normal throws)? **Yes.** (Otherwise about half of ordinary throws heal by accident.)
2. Spawn between the two units and alternate who may shoot first? **Yes.**
3. Heal 12% of max HP per living unit, no cleanse? **Yes.**
4. A target hit does not charge the ultimate? **Yes.**
5. AI may choose its throw angle (60..78) to reach high targets? **Yes**, same as the fence-lob item in kiro 51; without it the AI cannot use targets.

## 11. What I did not verify

- No script, game or browser was run. No hit rate here was measured.
- The path-crossing shares (52%, 45%, 40%) come from a single geometry (54 degrees, range 1000, hand 110 px high, no wind). Wind and other angles shift them.
- `c = 0.08` depends on my assumption that 15% of human throws are 65 degrees or steeper. No angle log exists in the 12-match data.
- `u_h = 0.15` and `u_a = 0.10` are assumptions about behaviour, not measurements. The stress row shows what happens if they are double.
- The effect of the potion skill (+35, free) on length was not modelled.
- The AI height-noise table assumes a sensitivity of 0.07 power units per px from one geometry (D 800, height 450 above the hand).
- The 4 v 4 figure (8% for parity) is a one-line estimate and rests on an unconfirmed flow.
- I did not read `scripts/mcp_game_server.py`, so I do not know whether the engine can hold a persistent object like the target without changes to `TrackedGameState`.
- No image or sound was seen or heard; art and sound statements are design only.
- `heal_rain` does not exist in `js/particles.js`; the values above are a specification for the code owner.
