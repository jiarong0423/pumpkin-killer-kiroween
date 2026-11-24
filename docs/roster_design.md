# Roster design: 6 classes, 4 vs 4, clearly different attacks (Kiro task 33)

Status: **design only.** Nothing was run. I read `index.html` (class table, `executeThrow`, the projectile loop, `triggerAITurn`, move/dice code, `ANIM`), `scripts/mcp_game_server.py`, the head of `scripts/mcp_stdio_server.py`, `shared/constants.json`, `docs/game_mode.md`, `docs/airdrop_design.md` (first half), `docs/wind_design.md` (grep only), `docs/dock_asset_requests.md`, and looked at `assets/env/ghost_lantern.png` and `assets/units/unit_knight.png`. Every number in sections 2 and 3 is **my hand arithmetic** (level ground, ignoring the 110 px launch height), a first guess for the balance script in section 5 to correct. Anything about how a thing looks or feels in play is unverified.

Ultimates are **not** designed here (owner: not designed yet). No class below has an ultimate column, trigger or effect. The ricochet idea in `game_mode.md` is a draft ultimate and is not used as a basic attack.

Owner decisions this design needs are collected in section 7. The ones that change confirmed text in `game_mode.md` are marked there.

## 0. Facts from the code

| Fact | Value | Where |
|---|---|---|
| Classes today | skeleton javelin, pumpkin wizard cannon, bat-cat shuriken, pumpkin knight thrown small shield. One unit per side on the field; hero tabs only change which class the single unit plays | `HERO_PROFILES`, `switchHero` |
| Damage per hit in the browser | skeleton 24, wizard 28, bat 20, knight 22. Heavy shot is x1.5 | `HERO_PROFILES`, `executeThrow` |
| HP in the browser | 100 for every class (`player.maxHp`, `ai.maxHp`) | `index.html` |
| HP and damage in the MCP engine | bat 90/16, wizard 85/26, skeleton 100/18, knight 120/20. `speed_scale` 1.15 / 1.0 / 1.25 / 0.85 is defined but **never used** (only the definition matches a search) | `HERO_TEMPLATES` |
| Flight | launch speed = power x 13.8, gravity 980, angle 25..80, default 54. Every class flies the same | `executeThrow`, `GRAVITY` |
| Wind | browser: acceleration, `WIND_ACCEL` 72 px/s^2 per unit. MCP engine and `sample_path`: a **constant velocity offset** of 67.5 px/s per unit. Different models | `index.html`, `mcp_game_server.py`, `mcp_stdio_server.py` |
| Hit test, browser | point projectile vs body box: \|dx\| <= 70 and y in [unit.y - 190, unit.y]. Wizard launches from the muzzle (fwd 70, up 118), others from (58, 110) | projectile loop, `WIZARD_MUZZLE` |
| Hit test, MCP engine | \|dx\| < 45 and \|unit.y - 60 - y\| < 65. Smaller than the browser. Release point (25, 65) | `resolve_round` |
| Power meter | ping-pong 0..100, 1.3 s per sweep | `cycle = (elapsed / 1.3) % 2` |
| Fence | x 895..1025, 250 px tall, 100 HP, -15 per hit | constants, projectile loop |
| Sky shield | one per side, only the Knight controls it, 2 charges, 2 rounds, bar 210 px wide at y about 430 | `shields`, `canControlShield` |
| Move | d6 x 36 px, direction chosen, does not use the throw. Limits: browser 160..850 / 1070..1760, MCP 100..835 / 1085..1820 | `stepDice`, `TEAM_X_LIMITS` |
| Timing | turn timer 12 s (mockup shows 8 s, undecided). Agent turn: 1.0 s wait, 0.6 s wind-up, throw release at 0.36 of 0.62 s, 0.8 s before the next step | `triggerAITurn`, `aiAttackNow`, `ANIM` |
| Agent aim error | uniform +/-14 power units; 1 unit is about 20 px of landing distance | `AI_AIM_ERROR` |
| Engine round | resolves all pending throws in unit-id order at the end of the round, then **re-randomizes every unit's x** (`rng.uniform(220, 640)`) | `GameState.resolve_round` |
| Ghost carrier art | `assets/env/ghost_lantern.png`: a cute white and cyan sheet ghost holding a pumpkin lantern on a rope (the airdrop carrier) | looked at it |

Mismatches to fix first (section 4, step 0): HP table, hit box, release point and wind model differ between browser and engine. The balance script cannot give an answer about the game until both use one set.

## 1. Roster (6 classes)

Six, not more: the new-art cap is 16 images and each new class needs 6 (`roster_asset_requests.md`). Two new classes = 12 images plus 1 shared tombstone.

| Class | Fantasy | Weapon | Silhouette (Colab) | Why pick it |
|---|---|---|---|---|
| **骷髏長矛兵** Skeleton Spearman (existing) | A bone soldier who throws javelins on a line. | Javelin | Tall, thin, vertical; long spear line over the shoulder. Existing art. | Flat fast shot, little wind. Rewards a clean line, and can hit two enemies standing in a row. |
| **南瓜巫師** Pumpkin Wizard (existing) | A pumpkin-headed gunner with a shoulder cannon. | Cannonball | Pumpkin head, hat, cannon on the shoulder. Existing art. | A high lob that damages everything near the landing spot. Forgiving when enemies bunch up. |
| **蝙蝠貓刺客** Bat-Cat Assassin (existing) | A fast cat in a cape. | Shuriken, thrown three at a time | Small, crouched, cape trailing. Existing art. | A fan of three flat shots. Many small hits, strong against the sky shield. |
| **南瓜重裝盾衛** Pumpkin Guard (existing) | An armoured pumpkin knight with a wooden cross shield. | Thrown small shield | Wide, armoured, big shield. Existing art. | Short-range heavy lob that shoves the target back, and the only class that can place the sky shield. |
| **瘟疫醫生** Plague Doctor (new) | A beaked-mask doctor who throws bottles of green plague. | Glass vial | Tall narrow triangle: long coat flaring at the hem, wide flat hat brim, long curved beak sticking out sideways, satchel, a glowing green vial held up. The beak and brim read at small size and differ from the skeleton's vertical spear line. | Poisons from a distance; spreading poison over four targets beats focusing one. Needs a teammate to finish (poison cannot kill). |
| **提燈守墓鬼** Lantern Warden (new) | A hooded grave-warden ghost who lobs cold lanterns that go off a turn later. | Hooked lantern | Wide egg shape with a wavy hem, no legs, floating about 20 px; hood with two hollow glowing eyes; one thin arm holding an iron hook with a cyan flame lantern. Dark violet-grey shroud, not white. | Controls space: the burst lands after the enemy has had one phase to move away. |

Art caution for the Lantern Warden: the airdrop carrier is already a **cute white ghost with a pumpkin lantern**. The Warden must not be mistaken for it. That is why it is dark, hooded, hollow-eyed, with a cyan flame instead of a pumpkin. Unverified until the art exists.

Deferred (not drawn, art cap): Vampire Count (heal-on-hit) and Gravedigger (shield break, double fence damage). Either is a clean 7th class later.

## 2. Attack difference table

### 2a. The model (so the engine can use the numbers)

Per projectile: `v0 = power x 13.8 x speed`, gravity = `980 x gravity_mult`, wind acceleration = `72 x wind x wind_mult`. Hit test: the body box (70 half-width, 190 tall) expanded by `reach` px on every side. Fence and sky shield stay point tests as today.

Three things I worked out that shape the table:

1. **Speed and gravity multipliers alone do not change the arc.** For a given angle and landing distance, every class flies the same parabola; the multipliers change how long it takes. What differs is (a) the angle a class needs, (b) flight time, which drives wind drift, and (c) how much power it takes to reach a spot. So the table keeps `range scale R = speed^2 / gravity_mult` in 0.72 to 1.01 so the power meter stays useful, and uses **gravity and wind multipliers to set flight time and drift**. The visible arc difference comes from the angle each class needs, which is why each row has an angle hint (a hint on the class card, not a limit; the 25..80 limit stays).
2. **The fence decides how flat a flat shot can be.** A shot over distance D needs apex height about `D x tan(angle) / 4`, and the fence top (y 610) is 140 px above the launch point (y 750); I use 160 px for margin. At D = 1000 that means at least about 33 degrees; at D = 900 about 35.5 degrees.
3. **Landing spread is larger for a lower power.** With agent error E power units, spread in px is `4 x E x D / P`. A class that reaches the same spot with less power is harder to place. This is why the Knight (R 0.72) gets a smaller damage number: it needs more power for a given distance, so it is more accurate.

### 2b. Numbers

Common to all six: **HP 100**, body half-width 70, body height 190, angle 25..80.

| Class | Direct damage | Extra route | Full-success damage | Speed x | Gravity x | Range R | Wind x | Reach (px) | Hit window W (px) | Charge sweep (s) | Agent power error |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Skeleton | 26 | **pierce**: second enemy in the path takes 13 | 26 (39 with a pierce) | 1.25 | 1.56 | 1.00 | 0.8 | 6 | 152 | 1.3 | 14.0 |
| Wizard | 24 | **burst**: every other enemy within 150 px of the impact takes 5 (also on a ground miss) | 24 (+5 per neighbour) | 1.00 | 1.00 | 1.00 | 0.7 | 4 | 148 | 1.3 | 14.0 |
| Bat | 3 x 9 | **multi-hit**: three shuriken at -3, 0, +3 degrees | 27 | 1.15 | 1.32 | 1.00 | 0.9 | 8 each | 156 each | 1.2 | 15.2 |
| Knight | 20 | **knockback**: target is pushed 60 px away from the thrower | 20 | 0.85 | 1.00 | 0.72 | 0.5 | 12 | 164 | 1.3 | 14.0 |
| Plague Doctor | 14 | **poison tick**: 3 per round for 3 rounds (9). A ground landing poisons every enemy within 110 px, no direct damage | 23 | 0.95 | 0.90 | 1.00 | 0.9 | 12 | 164 | 1.3 | 14.0 |
| Lantern Warden | 12 on a body hit | **delay**: the lantern stays where it lands and bursts at the start of the thrower's next side phase, 14 to every enemy within 120 px at that moment | 26 (12 + 14) | 0.90 | 0.80 | 1.01 | 1.0 | 16 | 172 | 1.4 | 13.0 |

Notes on the columns:
- Speed x for the existing four is the engine's own unused `speed_scale`. I kept them so the design follows the earlier intent.
- Hit window W = 2 x (70 + reach). The code today is a point projectile, W = 140.
- Agent power error = 14 x 1.3 / sweep. A human's timing jitter is about 0.18 s (14 units at 76.9 units per second, my arithmetic); a faster meter turns the same jitter into more power error, and agents get the same rule. The server adds this noise to agent power (agents cannot turn it off).
- Poison never reduces HP below 1. A new poison hit sets the remaining ticks back to 3 and does not stack, so spreading it over four targets pays more than hitting one target again.
- Pierce works only if the spear hits at 40 degrees or flatter below horizontal and a second enemy box is entered within 220 px of further travel.
- A bat volley is one throw. If any shuriken touches the sky shield bar the volley costs the shield **1 charge in total**, and every shuriken that touches the bar is stopped. Fence damage per throw is at most 15 (5 per shuriken).
- Lantern: one pending lantern per Warden. A dead Warden's lantern still bursts. It hurts enemies only. A body hit also plants the lantern at that spot.
- Knockback is clamped by the side limits and stops 160 px short of the next unit; it never pushes a second unit.

### 2c. What each class does differently

Reference shot: target distance D = 1000 px, sweet angle, calm to wind 4. Knight uses D = 800 because its maximum range at 45 degrees is 1943 x 0.72 = 1404 px and its lob reaches 1075 at 65 degrees.

| Class | Angle hint | Power at reference | Flight time | Drift at wind 4 | What the player does differently | Counter-play |
|---|---|---|---|---|---|---|
| Skeleton | 33-40 | 72.8 | 1.01 s | 118 px | Threads a flat line just over the fence. Lines the shot so the spear passes through a second target. Steeper than 40 degrees and the pierce is gone. | Fence and sky shield stop a flat line. Units spaced 220 px or more apart give a pierce nothing to hit. Standing close behind the fence forces a steep shot. |
| Wizard | 55-70 | 77.1 | 1.88 s | 356 px | Lobs high and reads the wind; aims for bunched units; a near miss still chips. | Spacing of 150 px or more is outside the burst. Wind makes the long flight the hardest to place. Keep moving after the landing record shows where it falls. |
| Bat | 33-40 | 73.9 | 1.04 s | 140 px | Fires a fan about 38 px apart at landing; picks the angle so two or three shuriken hit one unit. | The sky shield stops the whole volley for one charge. An intact fence clips low volleys. Each hit is only 9: healing undoes a hit in one use. |
| Knight | 60-75 | 86.3 | 1.87 s | 252 px | Moves forward to reach, lobs, shoves a target out of the formation. Can give up the throw to place the sky shield. | Out of range beyond 1404 px. The least wind of the lobs, but the long flight still drifts 252 px. A shoved unit's old landing record no longer matches its new x. Killing the Knight removes the shield. |
| Plague Doctor | 45-60 | 73.9 | 1.80 s | 420 px | Sprays poison across several targets instead of repeating one; needs a finisher because poison stops at 1 HP. | A fresh target takes the full dose, a poisoned target adds little. Poison does nothing in the last rounds of a match. A heal item removes its value (cure rule is undefined; see section 7). |
| Lantern Warden | 50-65 | 73.5 | 1.91 s | 525 px | Places a lantern in front of enemies and predicts where they will be after one phase. The most wind-sensitive weapon, so wind reading pays most. | Move out of the 120 px circle (a die roll of 4 or more clears a unit standing at the centre, 50 percent). Units boxed in by teammates or the side limit cannot flee. Spacing of 240 px keeps it to one target. |

### 2d. Keeping time-to-kill similar

HP is **100 for every class** (the browser already uses 100; the engine's 85/90/100/120 is the outlier). Two measures, both checkable:

1. **Clean throws to kill** = `ceil(100 / full-success damage)`: Skeleton 4 (26), Bat 4 (27), Warden 4 (26), Wizard 5 (24), Knight 5 (20), Doctor 5 (23). Full-success damage is 20 to 27, mean 24.3; four classes within 3 of each other, the Knight lowest at 20 because it is the most accurate at its range. Today's browser values are 20 to 28, so the spread is no wider than it already is.
2. **Expected damage per throw (EDT)** at the published agent error, one target, reference shot. Formula: hit window / spread x damage, summed over routes. By my arithmetic: Skeleton 5.14, Wizard 5.93, Bat 5.13, Knight 6.31, Doctor 5.64, Warden 5.30 (Warden assumes the target stays in the circle half the time). Mean 5.58; range -8 to +13 percent.

Routes: single clean hit (Skeleton), chip plus area (Wizard), many small hits (Bat), shove plus the shield option (Knight), attrition (Doctor), area denial (Warden).

At that EDT a lone full-HP unit takes about 16 to 20 throws to kill at agent-level aim. In 4v4 the enemies stand in a row, so a throw connects far more often (about 0.5 to 0.75 by my estimate, against 0.2 for one target). I did not simulate it; section 5 measures it.

## 3. 4 vs 4 rules

| Question | Rule | Reason |
|---|---|---|
| Line-up | Each side picks **4 of the 6 classes, no duplicates within a team**. Both sides may pick the same classes. Picks are blind and revealed together; agents pick from the public class cards with a seeded draw. | One Knight per team means one sky shield per team, as `shields` has today. Six distinct silhouettes stay readable. 15 line-ups per side. |
| Slots | Slot 1 is nearest the fence, slot 4 is rearmost, on both sides. Marker 1-4 for the human team, A-D for agents (as in the mockup). | Matches the mockup markers. |
| Start positions | Human team x = 760, 560, 360, 160 (slot 1 to 4). Agent team x = 1160, 1360, 1560, 1760. | Inside 100..835 and 1085..1820. Spacing 200. Front units are 135 px from the fence edge; the 220 px sprites do not touch it. |
| Spacing rule | Centre distance between living units of the same team is **at least 160 px** (140 px box + 20 px gap). A Move or a knockback stops at 160 px from the next unit. Units never swap order. A dead unit's spot is free and does not block. | Hit boxes never overlap. The engine's current spawns are 120 px apart, which overlap. |
| Field fit | 4 units need at least 480 px between the outer ones; one side is 735 px wide, so 255 px of slack. | |
| Controllers | Every unit has a `controller`, human or agent (the engine already has this field). In the default match **the human controls all four units of the human team, one at a time**; the four agent units are the opponents. With several humans, each unit has one human owner and a human can only click their own. | See section 7: I read "the others are agents" as the opposing four. If the owner meant the human's three teammates, only the controller flags change. |
| Turn order | A round has two side phases, **human phase first, then agent phase** (confirmed in `game_mode.md`). In a phase **each living unit of that side acts once, one after another.** In the human phase the next unit in slot order is pre-selected and the player may **click another unit that has not acted** to act with it instead. Agents act in slot order, one decision each. | One unit per turn keeps the single-throw feel. Free order gives the human a real choice (shield first, lantern first, wizard last). |
| Action per turn | Move (optional, once, does not end the turn), then Attack. The Knight may instead Defend (sky shield). | As confirmed. |
| Turn timer | **8 s** per unit (the mockup value; today 12 s). Out of time = forfeit; a throw already charging is released at its current power. | 12 s x 4 units is too slow for the 8 minute target. |
| Dead unit | Removed from the queue at once, even mid-round. The other units do not move to close the gap. Poison stops, pending Warden lanterns stay and burst. If the Knight dies its sky shield disappears. The tombstone image (asset request 5) marks the spot. | |
| Win condition | All four enemy units dead. Round cap **7**: then more total HP wins, then more living units, then draw. | A cap guarantees the 8 minute target (below). |
| Fence | Unchanged: shared, 100 HP, -15 per hit, can break. With 8 throwers a round it will probably break around the middle of the match, which opens flat lines. | Flat classes get stronger late; the sim must show whether that is fine. |
| Sky shield | One per team, Knight only, as today. A volley costs one charge. Possible lever if the shield proves too strong against 4 enemy throws a round: charges 2 to 1. | Unverified. |
| Wind | One value per round, -4 to +4, public, the same for all 8 throws of the round. | The side that acts second sees four fresh landings under the same wind. See section 7. |
| Airdrops | Rules from `docs/airdrop_design.md` apply. Replace its placeholder "reference unit": use the favoured team's **living unit with the lowest HP** (public), tie to the one nearest the fence. Each unit has its own slot. With a 7 round cap expect 2 drops (round 3 and round 6). `shield_patch` only when the favoured team has a living Knight. | The doc's "unit nearest the fence" was marked a placeholder for 4v4. |
| Skills (double, heavy, heal buttons) | Hidden in the 4v4 first version; heal and heavy arrive as airdrop items. | `game_mode.md` says double needs an energy bar, not decided. |

### Match length

Timing model, from the code constants: human turn about 7.5 s (aim and charge 4.5 s, release 0.22 s, flight 1.7 s, result 0.8 s); worst case 8 + 0.22 + 2.0 + 0.8 = 11 s; agent turn about 4.0 s (1.0 + 0.6 + 0.22 + 1.6 + 0.8, plus a dice move a quarter of the time); 1.5 s at round start.

| | Human phase | Agent phase | Start | Round (full roster) |
|---|---|---|---|---|
| Typical | 4 x 7.5 = 30 s | 4 x 4.0 = 16 s | 1.5 s | **47.5 s** |
| Worst | 4 x 11 = 44 s | 16 s | 1.5 s | **61.5 s** |

With a cap of 7 rounds: typical 332 s (5.5 min), worst 430 s (**7.2 min**), under 8. Dead units shorten later rounds. Turns: at most 8 per round, so at most **56 turns** in a match (fewer with deaths; about 35 to 45 expected if one team is wiped in rounds 5 to 6, an unmeasured guess). Wiping 16 hits-to-kill from a side at 2 to 3 connects a round takes 5 to 8 rounds, so the cap may end some matches: section 5 measures it, with levers listed in section 7.

## 4. Engine needs

Order matters: each step must pass before the next. Small steps, each with a pass condition. Names only for protocol fields.

**Step 0. Make browser and engine agree (no gameplay change).** Engine: HP 100 for all; hit box 70 x 190; release point (58, 110); wind as acceleration 72. Browser: move limits 100..835 and 1085..1820. Pass: extend `scripts/test_constants_sync.py` so a table of 50 (angle, power, wind, class baseline) cases gives the same landing x in the browser integrator (run in node) and the engine within 2 px; HP and hit box constants equal.

**Step 1. One class table.** New `(not published)` with the section 2b columns. Pass: schema test (6 classes, all keys, `ceil(100 / full-success)` is 4 or 5, R between 0.7 and 1.1); the browser `HERO_PROFILES` and engine `HERO_TEMPLATES` are built from or checked against it.

**Step 2. Per-class flight.** Engine integrator takes speed, gravity and wind multipliers. Pass: a class with all multipliers 1 reproduces step 0 landings exactly; property tests (fast-check or Python equivalent): same seed and inputs give the same result, landing x rises with power, damage never negative, HP never above max.

**Step 3. Per-class hit test.** Box expanded by reach; the first unit along the path wins. Pass: unit tests at the edges (dx 70 + reach hits, 71 + reach misses; same for y).

**Step 4. Special properties, one function and test each.** Order: burst, volley, knockback, pierce, poison, lantern. Pass per property: burst radius edge (150 hits, 151 does not), the thrower's team never hurt; volley gives 3 independent hits and 1 shield charge; knockback never breaks the 160 px rule or the side limits; pierce only at 40 degrees or flatter and only once; poison floor 1 HP, no stacking, 3 ticks; lantern bursts at the start of the thrower's next side phase, enemies only, after the owner dies too.

**Step 5. 4v4 state.** `units` array in the engine; remove the per-round x shuffle; spawn and spacing function; the round has two side phases; queue, timer, forfeit, round cap, win rules. Pass: 100 seeded random matches in which every living unit acts exactly once per round, dead units are skipped, no two living teammates ever closer than 160 px (checked after 10 000 random Moves and knockbacks), matches always end.

**Step 6. Line-up pick.** Blind, seeded for agents. Pass: duplicates rejected inside a team; same seed gives the same agent line-up; the pick is hidden until both sides picked.

**Step 7. MCP server.** `scripts/mcp_game_server.py` and `scripts/mcp_stdio_server.py`. Public fields only, names only:
- `get_public_state`, per unit: `class`, `slot`, `team`, `controller`, `x`, `hp`, `max_hp`, `alive`, `acted_this_round`, `poison_ticks_left`. Global: `phase`, `active_side`, `acting_unit`, `queue`, `turn_seconds_left`, `round`, `round_cap`, `wind`, `lanterns` (each with `owner_unit`, `x`, `radius`, `bursts_at_round`), and `classes` (the public card: `weapon`, `damage`, `projectiles`, `burst_radius`, `pierce_damage`, `knockback_px`, `poison_per_tick`, `poison_ticks`, `lantern_radius`, `lantern_damage`, `angle_hint`).
- Never serialized: `speed_mult`, `gravity_mult`, `wind_mult`, `reach`, the seed. Agents learn the feel of each class from `get_history`, as a human learns it by playing.
- `get_history`, per throw: `class`, `volley_landings`, `events` (type: direct, burst, pierce, poison_apply, poison_tick, lantern_plant, lantern_burst, knockback; each with `unit` and `amount`).
- New tool `pick_lineup` (argument `classes`). `submit_action` already takes `unit`; it is rejected when the unit is not in the active side's queue or already acted. `use_item` as in the airdrop doc.
- The server adds the per-class agent power error to agent throws.
Pass: a test that serialises `get_public_state` and `get_history` and finds none of the private keys; every rejected call (wrong phase, wrong side, already acted, dead unit, duplicate class, unknown class) has a unit test.

**Step 8. `index.html`.** Sub-steps, each leaving the game playable:
8a. `units[]` with one unit per side, `player`/`ai` still working through the array. Pass: grep finds no `player.` or `ai.` left; a one-versus-one playthrough behaves as before.
8b. Draw loop, projectile owner, hit test over all enemy units. Pass: a projectile hits the front unit first; a ground miss does not hit a unit behind the fence.
8c. Turn queue and phases from the engine, timer 8 s, click to pick an unacted unit. Pass: click on an unacted own unit switches; click on an acted or enemy unit does nothing.
8d. Agent turns per unit through the same public state. The current in-page AI uses a ballistic solver (`estimatePowerForTarget`); product principle says agents get no simulator. Keep it only as a stand-in and mark it; the MCP agents are the real ones.
8e. HUD and dock: top bar with 4 + 4 small portraits, HP bars, markers 1-4 and A-D, active unit highlight; bottom dock shows the active unit and its card; hero tabs removed; status icons for poison; lantern marker with its radius ring; tombstone. Pass: at 1920 x 1080 all 8 HP bars are visible without overlap with 4 living and 4 dead units; the dock shows the right class art for each clicked unit.
8f. Sky shield and fence rules for 4v4 (volley cost, shield tied to the living Knight). Pass: killing the Knight removes the shield on the same frame.

**Step 9. Sound and art hookups.** New event names for the sound line to provide: `throw_vial`, `throw_lantern`, `lantern_burst`, `poison_tick`. Until then reuse `throw_cannon` and `impact_unit` (unverified how they sound). Art from `docs/roster_asset_requests.md`; the game keeps placeholders until files exist.

**Step 10. Balance script** (section 5).

## 5. Balance test plan

New `(not published)`, stdlib only, in the style of `scripts/eval_agent_learning.py`. Seeds start at 1 (the engine does `seed or random...`, so seed 0 would be random).

**The bot.** A fixed-seed test bot, the same for both sides and every class. It uses the engine's own ballistic solver (a test-only function; it is **not** what MCP agents get), picks a target by one rule (lowest HP in range, tie to the nearest), solves power for the target at the class angle hint's middle, and adds the class's published power error from a seeded RNG. It moves away from a pending lantern with a fixed probability `FLEE` (run the whole suite at 0.25, 0.5 and 0.75).

**Tests.**

| # | Test | Method | Pass band |
|---|---|---|---|
| T1 | Pair win rate, 1 unit vs 1 unit | Every pair of the 6 classes (15 pairs), 200 matches each, seeds 1..200, 100 matches with A on each side. A draw counts half. | A wins **40 to 60 percent**. Calibration: with true 50 percent, the standard deviation of 200 matches is 3.5 points, so the band is 2.8 deviations wide each side; about 0.5 percent per pair and about 7 percent for at least one false alarm across 15 pairs. A failing pair is rerun on 400 other seeds before anything is tuned. |
| T2 | Pair win rate, 4 copies vs 4 copies (test flag allows duplicates) | Same 15 pairs, 200 matches. | 40 to 60 percent |
| T3 | Class average | Each class's mean win rate over T1 against the other 5 (1000 matches). | **45 to 55 percent** |
| T4 | Line-ups | All 15 line-ups against all 15 (225 pairs, 40 matches each, so 600 per line-up), random slot order. | Every line-up **40 to 60 percent**. A line-up outside the band is a sign that a combination (for example Doctor plus a finisher) is too strong |
| T5 | Same damage, different route: damage per connecting throw | In T2 logs, mean damage per throw that connected, per class. | Each class **within 25 percent** of the roster mean |
| T6 | Same damage, different route: expected damage per throw | Lone full-HP target at the reference shot, 2000 throws per class. | Each class within **20 percent** of the roster mean (hand model says -8 to +13 percent) |
| T7 | Route share | Share of each class's total damage from its special route, from `events`. | Skeleton pierce 5 to 30 percent; Wizard burst 15 to 50; Bat shuriken beyond the first of each volley 40 to 70; Knight knockback moves a unit at least 30 px in 20 percent or more of hits; Doctor poison ticks 25 to 50; Warden lantern burst 30 to 60. A route under the low bound is cosmetic, over the high bound the base attack is. |
| T8 | Clean throws to kill | From `(not published)`. | 4 or 5 for every class (static) |
| T9 | Match length | T4 matches, using the timing model of section 3. | Mean 5 to 6.5 rounds; 95th percentile at most 7; at least 60 percent of matches end by wipe before the cap; every match at most 8 minutes |
| T10 | Phase order | Same bot, same seeds, human-side phase first vs agent-side phase first. | Win rate difference at most 10 points. Over that, alternating first phase is needed (owner decision) |
| T11 | Connect rate | 4v4 throws that touch at least one unit. | 0.30 to 0.70 per throw. Over 0.70, apply the levers in section 7 |
| T12 | Determinism | Same seed twice. | Identical match logs |

Order of tuning if a test fails: reach (plus or minus 4 px), then damage (plus or minus 2), then wind multiplier, then the special number. Change one value, rerun the failing test only, then the whole suite.

## 6. Comparison with team artillery games

Opened: [Worms World Wiki, Classes](https://worms.miraheze.org/wiki/Scientist), [Steam guide, Improved Worms Class Explanations](https://steamcommunity.com/sharedfiles/filedetails/?id=166660179), [Wikipedia, Gunbound](https://en.wikipedia.org/wiki/Gunbound), [UnknownCheats, Gunbound Boomer Guide](https://www.unknowncheats.me/wiki/Gunbound:Boomer_Guide). **Could not open (HTTP 403):** `https://wormsrevolution.fandom.com/wiki/Classes`, `https://strategywiki.org/wiki/GunBound_Classic/Mobiles`, `https://strategywiki.org/wiki/GunBound_Classic/Mobile_Delay_Stats`, `https://strategywiki.org/wiki/Gunbound/Mobiles`. Claims from search snippets only are marked.

| | Worms (team rosters) | GunBound (distinct mobiles) | This design |
|---|---|---|---|
| Unit | Four worm classes (Soldier, Scout, Heavy, Scientist) mixed in any order within a team; classes appeared in Worms Revolution. Wiki | Each mobile has three shots ("1", "2", "SS") and differs in defense, attack, health, delay, angle range and movement. Wikipedia | Six classes, one basic attack each, one special property each. No second shot yet (no ultimate designed) |
| How they differ | Mostly stats and utility around a shared weapon set: Scout moves far and deals less (shotgun 20 against 25), Heavy is slow and hits harder, Scientist gives each teammate 5 HP per turn. Wiki. The Steam guide gives the damage order Heavy, Soldier, Scientist, Scout. | Different weapons with different shapes: Boomer's shot 2 fires four clustered projectiles, its SS turns into a boomerang after enough airtime, and wind affects it strongly. UnknownCheats guide (the guide's airtime figure is hedged by its author) | Differences are in **what the shot does** (pierce, burst, fan, shove, poison, delayed burst), with damage held to 20 to 27 |
| Balance lever | Rough damage ranking plus movement and support. Clan Wars rebalanced classes to differentiate them further and to limit Scientist healing while hiding. Wiki | A "delay" turn system: stronger shots and item use make the next turn come later. Wikipedia. Delay values per shot (for example 720 base, 960 for shot 2, 1320 for SS for Armor) appear **in a search snippet only** (StrategyWiki, page could not open). The Boomer guide gives 730 / 880 / 1280 for its three shots. | No delay; every unit acts once a round. The equal-EDT table and the win-rate bands do the same job |
| Glass cannons | The Scout is weakest in attack and defence | Boomer has strong attack and very low HP, "can die in two duals" (guide) | All classes have 100 HP, so no class is the target of choice. Durability comes only from the Knight's shield action |
| Team recommendation | The Steam guide advises variety of classes in a formation | Tag mode: two mobiles per player, the second starts with half health (Wikipedia) | Four of six, no duplicates, blind pick |

Lessons applied: keep a small spread in damage (Worms' Scout 20 versus 25 is a 20 percent gap, ours is 20 to 27); give each class a non-damage identity (Worms movement and healing, GunBound shot shape); pay for the stronger options with a cost (GunBound delay; ours is accuracy, range and wind exposure). Lessons not applied: Worms' team-wide healing aura (it caused hiding behaviour, per the Clan Wars note) and GunBound's glass cannon HP.

## 7. Decisions for the owner, and risks

Needs the owner (each can be reversed by changing one number or flag):
1. **HP 100 for every class.** `game_mode.md` lists 85 to 120. Chosen so that time-to-kill does not depend on the victim's class. Alternative: keep the old HP and divide damage taken by HP / 100 (same result, harder to read).
2. **Who the human controls.** I read "the others are agents" as the four opposing units, and gave the human all four of their own units.
3. **Human phase first** is confirmed text, but the second phase sees four fresh landings under the same wind. T10 measures it; the fix would be alternating the first phase each round.
4. **Timer 8 s** (mockup) instead of 12 s, and **round cap 7**.
5. **Double, heavy and heal skills** hidden in the 4v4 first version.
6. **Names and fantasy of the two new classes.** Deferred: Vampire Count, Gravedigger.
7. **Poison cure.** The airdrop doc does not say whether `candy_heal` cures poison. The Doctor's counter-play assumes it should; the airdrop line must decide.
8. **Angle hints** are shown on the class card only; the 25..80 limit is unchanged.

Risks (unmeasured): 4v4 connect rate may be 3 to 4 times the one-target rate, which shortens matches and hides what agents learn; the cap may end too many matches; the sky shield may be too strong when 4 enemies fire at it. Levers, in this order: widen default spacing to 220 px, reduce damage 10 percent (if matches end too early) or raise it 15 percent (if too many hit the cap), shield charges 2 to 1.
