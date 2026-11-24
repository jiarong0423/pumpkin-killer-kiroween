# Ultimates, area attacks and showpiece effects (Kiro task 35)

Status: **design only.** I changed no code and no art. I cannot play the game, see images or hear audio, so every statement about how something looks, sounds or feels is **unverified**. All damage, radius and timing numbers are first guesses for a playtest. The expected-damage figures are my own hand arithmetic from the code constants, not measured runs.

Owner words kept: ultimates are now allowed (owner, 2026-11-09, "like the ultimate", "area attacks", "effects"). The energy bar needs FOUR successful hits, each player counts their own hits, at most 2 ultimates per match, the screen stays clean, Halloween magic like a wizard school, no extra spending, art only from Colab, sounds only real CC0 recordings or code-made.

## 0. What I read, and what is missing

Read: `index.html` (`HERO_PROFILES`, `executeThrow`, the projectile loop with the hit tests, `ANIM`, `screenShake`, `hitStop`, `actionMenuItems`, the dock), `js/particles.js` (all presets), `js/particles_draw.js` (sprite shape), `docs/game_mode.md`, `(not published)`, `docs/airdrop_design.md`, `docs/sound_mapping.md`, `docs/sound_design.md`, `docs/wind_design.md`, `(not published)`, `docs/dock_asset_requests.md`, `docs/airdrop_asset_requests.md`, `scripts/mcp_stdio_server.py` (public state), `docs/mcp_agent_protocol.md`.

**Not in the repo:** `docs/roster_design.md` (task 33) and `docs/richness_plan.md` (task 34). So I designed ultimates for the 4 current classes only and wrote no sketches for new classes. Section 1b ends with a fit-check any future class must pass. Tombstones, camera zoom and slow motion do not exist in the code (searched `index.html`, `js/`, `css/`).

### Facts from the code that the numbers depend on

| Fact | Value | Where |
|---|---|---|
| Hit test on a unit | projectile x within 70 px of the unit centre, y inside a 190 px tall box above the feet | projectile loop, `index.html` |
| Normal damage (browser) | skeleton 24, wizard 28, bat 20, knight 22; all units 100 HP | `HERO_PROFILES`, `player.maxHp` |
| Normal damage and HP (MCP engine, `game_mode.md`) | dmg 18 / 26 / 16 / 20; HP skeleton 100, wizard 85, bat 90, knight 120 | `HERO_TEMPLATES` |
| Fence | x 895..1025, 250 px tall, 100 fence HP, a hit costs 15 | `FENCE_*`, `wallHp` |
| Sky shield | bar 210 px wide, hit band 46 px, 2 charges, one charge lost per block | `shields` |
| Wind | `vx += wind * 72 * dt`, wind range about +/-4 | `WIND_ACCEL` |
| Aim error of the built-in AI | 14 power units, about 20 px of landing distance per unit, measured 33% hit rate against the 140 px window | `AI_AIM_ERROR` comment |
| Typical flight | about 1.4 s; longest (power 100, angle 54) about 2.3 s by my arithmetic | `docs/wind_design.md`, `GRAVITY` 980, speed = power x 13.8 |
| Particle cap | 500 alive in the game system, oldest dropped first | `Particles.createSystem({maxParticles: 500})` |
| Existing hit-stop and shake | hit-stop 0.075 s; shake 0.18 s, up to +/-7 px x and +/-4 px y, only the wizard cannon triggers it | `ANIM.hitStopSec`, `screenShake` |
| Click menu | move, attack, defend (guard only) | `actionMenuItems` |
| Public ultimate field today | `ultimates_remaining` per team (red, white), value 2 | `public_state`, MCP stdio server |

### Findings that change the plan

1. **In the 1 v 1 prototype the 4-hit bar almost never matters.** With 100 HP, a unit needs 5 hits (skeleton 24, bat 20, knight 22) or 4 hits (wizard 28, 112 total) to win. The 4th hit that fills the bar is the hit that nearly or fully kills. The bar only means something in 4 v 4, where there are four enemy HP pools. This design assumes 4 v 4.
2. **`game_mode.md` states two trigger rules.** The later one says 4 hits for every class "until each class is defined". An older list says skeleton 3 hits, bat 3 hits or 3 dodges, wizard 4, knight 3 blocks. The task text says 4 is the confirmed rule, so I use 4 for every class and treat the older list as superseded. **Owner to confirm.**
3. **HP differs between the browser (100 for everyone) and the engine (85 to 120).** Every cap below is written so it holds for both.

## 1a. Energy bar

### Successful hit (definition)

A throw is a **successful hit** when it deals at least 1 damage to at least one enemy unit, either by direct hit (within 70 px) or by splash. Rules that follow from this:

| Case | Counts? |
|---|---|
| Direct hit or splash that deals 1 or more | Yes, **one pip per throw**, even if the throw hits three enemies |
| Hit on a unit with `bone_ward` (half damage, rounded up, so 1 or more) | Yes |
| Block by a sky shield, hit on the fence, ground miss, timeout | No |
| Poison tick, pin, any status damage | No |
| Damage to the thrower's own team | Never happens (no friendly fire in v1, section 1c) |
| The ultimate throw itself, and area shots | An ultimate throw gives **0 pips**. An area shot that damages gives 1 pip like a normal throw |

### Owner questions that were still open (my recommendation first)

| Question | Recommendation | Reason |
|---|---|---|
| Does a block or a miss count? | **No.** Only hits count. | Matches the words "successful hits". A blocking knight earns nothing from the shield itself, which keeps the sky shield a trade (no attack that turn) and not a bar engine. |
| Does the bar reset after use? | **Yes, to 0.** Extra hits while the bar is full are lost. | With a cap of 2 per match there is nothing to save. A full bar gives no reason to hold back. |
| What is a "player" in 4 v 4? | **Each unit has its own bar.** The cap of 2 is **per side** per match. | Same pip count for a lone human controlling four units and for four humans with one unit each. A bar per controller would fill four times faster for the lone human. Per side matches the existing `ultimates_remaining` per team in the MCP server. A dead unit takes its pips with it. |

**Check this choice with bot matches before locking it** (section 1e, check C3). With 4 pips per unit and a hit rate of p, a unit needs about 4 / p throws: 12 at p = 0.33, 8 at p = 0.5, 5.7 at p = 0.7 (my arithmetic). If matches are shorter than about 8 rounds, per-unit bars rarely fill. The fallback is a bar per controller, which I rank second because it makes the fill speed depend on how many humans sit down.

### Where it is shown

| Place | What | Size |
|---|---|---|
| Dock (`#bottom-dock`), new `#dock-ult` under the HP bar of the selected unit | Four round rune sockets in a row. Empty = dark socket. Lit = ghost-fire fills it. | 4 x 22 px, one row |
| Over every unit with at least 1 pip | A row of 4 dots (8 px each) under the unit's HP bar. Hidden at 0 pips. | 4 x 8 px |
| Enemy units | Same dots, because bars are public (see below) | same |

Sockets use one Colab image (`ult_pip_socket`); the lit state reuses the existing `fx_ghostfire` sprite, so no second image is needed.

### Ready cue (when the 4th pip fills)

1. The four pips turn gold and pulse once (0.3 s).
2. Sound: the existing event `ultimate_ready` (rising bell arpeggio, 1.5 s, priority 5).
3. `sprite_rune_circle` flat on the ground at the unit's feet, two pulses (0.6 s each), then a slow breathing ring at alpha 0.25 until used. Only units that are ready get a ring. The cap of 2 per side keeps this to 4 rings on screen at most.
4. The moon glow gets a short boost (effect E7).
5. For the owner's side, the click menu gains a gold entry (below). For the enemy side, only the pips and the ring show, so the player can read the threat.

### How it is used

- The click menu above the unit gets a fourth entry, `✨ 大招` (gold), shown only when the unit is ready, the side has ultimates left, and the unit may throw this turn. A knight whose sky shield is active has an empty hand, so the entry is hidden for him (the bar keeps its pips).
- Choosing it arms the ultimate. The next hold and release is the ultimate throw. Angle follows the pointer, hold charges, release throws. **No confirm step and no preview.** To cancel before holding, click the unit again and pick `🎯 攻擊`.
- Optional keyboard key `U` to arm. No new dock button (the owner's question 6 about the old skill buttons is still open, so I do not add to them).
- The ultimate replaces the unit's one throw for that turn. The 12 s timer is unchanged.

### Public state (field names only)

| Where | Field |
|---|---|
| `get_public_state`, per unit | `ult_pips` (0 to 4), `ult_ready` (true or false), `ult_kind` (class rule id, for example `triple_javelin`), `statuses` (list of `id`, `rounds_left`; ids `poison`, `pinned`) |
| `get_public_state`, per side | `ultimates_remaining` (exists), `ultimates_used` |
| `get_public_state`, world | `ground_effects` (list of `id`, `x`, `radius`, `rounds_left`, `owner_team`; id `poison_cloud`) |
| `submit_action` (throw) / `submit_throw` | new optional argument `ultimate` (true or false); the knight's die is rolled by the engine, the agent never picks it (same rule as Move) |
| `get_history`, per throw | `ultimate`, `ult_kind`, `area_kind`, `hits` (list of `unit`, `damage`), `blocked_by` (`fence`, `shield` or null), `bounces_rolled`, `pips_after` |
| Rejection reasons | `ultimate_not_ready`, `no_ultimates_left`, `ultimate_while_defending`, `unit_dead`, `wrong_phase` |

Enemy pips and statuses are public because the human sees them too. Nothing here exposes the seed, the future die roll, the rain slot positions or a landing prediction. All spread constants (offsets, radii) are published rules in `shared/constants.json`, like `WIND_ACCEL`. The agent's aim error is drawn **once per ultimate** on the base power, then the offsets are applied.

## 1b. One ultimate per class

Common sequence (all four). Times are from the moment the player releases the throw, for a typical 1.4 s flight. The flight is real physics, so beats after the release are anchored to events, not a fixed clock.

| Time | Beat |
|---|---|
| 0.00 to 0.45 s | **Cut-in.** The unit's portrait (shout expression) slides along a diagonal band at y 140 to 380 (clear of the top bar, the units and the shield height). Edges dim to 30%. Name in gold on the band. A click skips it. |
| 0.45 to 0.75 s | **Charge.** The unit winds up with class effects. |
| 0.75 s | **Release.** The projectile(s) leave. |
| about 0.75 to 2.15 s | **Flight.** The normal path, trail on. |
| about 2.15 s | **Impact.** Class effect, one hit-stop (0.12 s), one shake. |
| about 2.15 to 3.0 s | **Aftermath.** Status marks, numbers, then control returns. |

Longest flight adds about 0.9 s (about 3.9 s total). Calm mode (section 1d) shortens the whole thing to about 1.2 s.

Shared rules for every ultimate:

- **Per-target cap: 40 HP per ultimate.** That is 40% of the browser's 100 HP and under half of the smallest engine HP (85 x 0.5 = 42.5). So **no ultimate kills a unit from full HP** in either build.
- **Team cap: 25% of the target team's total max HP.** My largest total is the wizard's, about 58 across two units 170 px apart (about 15% of a 400 HP team).
- **One shield charge per ultimate.** A sky shield blocks every projectile of the ultimate that crosses its bar, but loses only one charge for the whole throw.
- Fence and sky shield are **never ignored** unless a line says so. Nothing here ignores either.
- All random draws (rain slots, the knight's die) come from the injected seeded RNG.
- Ultimates do not add pips, and a unit that is KO'd loses its bar.

Expected-damage model used below: the landing x is uniform within +/-210 px of the target centre. That is the same as the measured 33% hit rate of the built-in AI (140 px window / 420 px range). "E" is the average damage per throw against one target under that model, and "ratio" is E divided by the same class's normal throw (normal E: skeleton 8.0, wizard 9.3, bat 6.7, knight 7.3).

### 1. Skeleton spearman: 三連亡靈長矛 / Triple Spectral Javelin

- **Fantasy.** The skeleton throws his spear and two ghost copies follow it, a wizard-school spell cast through a bone arm.
- **Effect.** Three javelins in one throw, released 0.20 s apart (0.75, 0.95, 1.15 s). Power offsets of -2, 0, +2 power units (about -40, 0, +40 px of landing distance, **measure with the AI constant**), same angle, same wind. 13 damage each. The first javelin is the real spear, the other two are ghost copies. Targets: any enemy unit within 70 px of a javelin. Max on one unit: 39. A single unit takes 1 javelin in most hits (all three only if it stands within about 10 px of the aim point).
- **Aiming.** The ordinary pointer, hold and release controls. The aim point is the middle javelin.
- **Numbers.** Window for at least one javelin: 140 + 80 = 220 px (52% under the model, against 33% for a normal throw). E = 13.0, ratio 1.63.
- **Counter-play.** One sky shield pass stops all three and costs one charge. Moving away (up to 216 px with a die) or standing at a spot the spread does not cover. The fence stops javelins that reach it; each deals 5 to the fence (a normal hit deals 15), at most 15 in total.
- **Cannot.** Kill from full HP (39 max). Pierce the shield or the fence. Hit twice with one javelin. Add pips.
- **Beats.** Cut-in with the cyan band. Charge: eye flames flare, two ghost spears fade in beside the real one (alpha 0 to 0.7). Release x3 with a spin of the arm each time. Impact: the first javelin gets the hit-stop, the others only a small spark. Aftermath: javelins stand in the ground with ghost-fire for 1 s, bones rattle.
- **Effects, existing presets.** `weapon_charge_aura`, `face_glow_skeleton` (x4 burst), `sprite_ghostfire`, `weapon_rune_halo` (scale 0.6, per release), `weapon_trail_spear`, `weapon_enchant_stardust`, `impact_burst` (scale 0.75), `hit_sparks` (scale 0.7), `sprite_impact_flash`, `landing_ring_dust`, `sprite_mist`, `damage_number`.
- **New effects.** `ult_cutin_sparks`, `spear_afterimage` (a fading copy of the spear every 0.05 s, drawn by code from the existing spear picture), `ground_crack_decal` (uses `fx_ground_crack`), `lightning_accent` (cyan).
- **Sprites (Colab).** `ult_spectral_spear`, `ult_cutin_band`, `fx_ground_crack`, `fx_lightning_strike`.
- **Sound.** Existing: `charge` (loop), 3 x `throw_spear`, `impact_unit_heavy` on the first hit and `impact_unit` for the others, file `bones_rattle` for the aftermath (already planned as the KO layer). New code-made event: `ult_cutin`.
- **Engine work: M.** Spawn three projectiles with a start delay and a power offset; resolve the shield rule "one charge per throw".

### 2. Pumpkin wizard cannon: 瘟疫南瓜炮 / Plague Pumpkin Shell

- **Fantasy.** The cannon swallows a rotten pumpkin and fires it. It bursts into a green plague that stays on the people it touched.
- **Effect.** One shell on the normal path, 1.4 x the cannonball's size (like the heavy shot). It bursts on the first contact with a unit or the ground. Burst area: units whose centre is within **120 px** of the impact x. Direct zone (within 70 px): **24** damage. From 70 to 120 px the damage falls in a straight line from 24 to **10**. Every unit in the 120 px area is **poisoned for 3 of its own turns: 3 damage at the start of each, 9 in total**. A second poison refreshes the timer and never stacks. **Poison cannot reduce a unit below 1 HP.** Max on one unit: 24 + 9 = **33**. Poisoned units show a green tint (35%) and drips.
- **Aiming.** Same controls. The aim point is the burst centre.
- **Numbers.** E = 17.2, ratio 1.84 (centre zone 33 x 33%, ring zone 26 x 24%). Up to 2 units are in the area when neighbours stand 170 px apart (for example one at 70 px left of the impact and one at 100 px right: 33 + 25), so the team total is at most about 58.
- **Counter-play.** Spread out (the area is 240 px wide). Sky shield (the shell bursts at the bar about 400 px above the bodies, so nobody is hit; one charge lost). Fence: the shell bursts on the near face at x 895, and the nearest enemy can stand at 1070 (browser) or 1085 (engine), 175 or 190 px away, so a normal enemy is out of range. An enemy that hugs the fence is not safe from a short throw. The `candy_heal` item removes poison (recommendation, one line in the airdrop item).
- **Cannot.** Kill from full HP. Kill with poison. Stack poison. Pass the shield or the fence. Add pips. The fence loses 30 (double a normal hit).
- **Beats.** Cut-in with the green band. Charge: barrel glows green, steam, `poison` bubbles at the muzzle. Release: big muzzle flash, recoil, shake. Flight: at the top of the arc the shell flashes and swells 30% for 0.15 s (a readable "arming" beat, borrowed from GunBound, section 1f). Impact: ring and green burst, hit-stop, short cloud (1.2 s, visual only). Aftermath: poisoned units tint green, drips, one summed number per unit.
- **Effects, existing presets.** `weapon_charge_aura`, `sprite_poison`, `smoke_puff`, `muzzle_flash` (scale 1.8), `weapon_trail_cannon`, `impact_burst` (scale 1.3), `hit_sparks` (scale 1.1), `sprite_impact_flash`, `poison_cloud` (radius 120, duration 1.2 s), `poison_drip`, `landing_ring_dust`, `damage_number`.
- **New effects.** `poison_burst` (expanding green ring plus about 24 droplets), `shock_ring`, `ground_rune_spread` (green), `poison_tint` (a canvas tint of the unit's own picture, 35% green; this is a draw-time tint, not new art, and the main line should confirm the owner accepts it), `lightning_accent` (green).
- **Sprites (Colab).** `ult_poison_shell`, `ult_cutin_band`, `fx_poison_puddle`, `fx_lightning_strike`.
- **Sound.** Existing: `charge`, `throw_cannon`, `impact_ground_heavy`, file `rock_break` layer (planned in `sound_mapping.md`), `poison_tick` (also for each tick at turn start). New code-made events: `ult_cutin`, `ult_poison_burst` (a 0.7 s filtered-noise hiss plus three bubble ticks). Music ducks on `impact_ground_heavy` already.
- **Engine work: M.** Needs the shared area-damage function and the poison status (both shared with the area attacks).

### 3. Cat-bat assassin: 影縫手裏劍雨 / Shadow-Stitch Shuriken Rain

- **Fantasy.** One shuriken flies out as a marker. Where it lands, a rain of shadow shuriken falls and stitches enemies to the ground.
- **Effect.** The marker flies the normal path. On its first contact with the ground or a unit (`dart_rain` already exists for this look), **10 shuriken fall** in a zone **300 px wide** centred on the contact x. Slots are 30 px wide; each shuriken lands at a seeded random x inside its own slot (so the cover is even). Each deals **4**; a unit is hit by every shuriken that falls within 70 px of its centre. A 140 px wide body can hold at most 5 slots, so one unit takes at most 5 shuriken (20); the engine also caps it at 8 for other geometry. Fall time is fixed at 0.6 s, so wind shifts the whole zone by 0.5 x 72 x 0.36 = **13 px per wind unit** (52 px at wind 4). A unit hit by **3 or more** shuriken is **pinned**: it cannot use Move on its next turn (it may still attack or defend).
- **Aiming.** Same controls. The aim point is the zone centre.
- **Numbers.** E about 12.9 (10 x 4 / 3 minus a small edge loss), ratio about 1.9. A centred unit takes 4 or 5 shuriken (16 to 20). With 170 px spacing a neighbour gets 1 to 2 shuriken (4 to 8). Pinned chance: about 62% under the model.
- **Counter-play.** The marker is stopped by the sky shield (the ultimate ends, one charge lost, no rain). If the marker hits the fence, the rain falls at the fence and normally hits nobody. A sky shield above the zone also stops falling shuriken (they start above y 300). Moving away. A pinned unit can still throw, so the pin is not a stun.
- **Cannot.** Kill from full HP. Pass the shield or the fence. Pin for more than 1 turn. Add pips.
- **Beats.** Cut-in with the violet band. Charge: a ring of shadow motes spins around the cat, the cape flares. Release: one quick whirr. Flight: the marker leaves a violet afterimage. Impact: the sky above the zone darkens by 20% for 0.4 s, then the rain falls (0.6 s). Aftermath: pinned units get a violet rune on the ground under their feet.
- **Effects, existing presets.** `weapon_charge_aura`, `weapon_trail_dart`, `dart_rain` (width 300, height 380), `hit_sparks` (scale 0.4, only for the units hit), `sprite_stardust`, `landing_ring_dust`, `damage_number`.
- **New effects.** `shadow_swirl` (orbiting dark-violet motes, about 16 particles), `shuriken_stick` (3 particles per shuriken that lands), `pin_rune_spread` (uses `fx_pin_rune`), `lightning_accent` (violet).
- **Sprites (Colab).** `ult_shuriken_shadow`, `fx_pin_rune`, `ult_cutin_band`, `fx_lightning_strike`.
- **Sound.** Existing: `throw_shuriken`, the file `metal_bing` played 10 times, 60 ms apart (the 3-per-band-in-150-ms rule is respected by the spacing), volume 0.25 to 0.4, pitch within +/-6%. New code-made events: `ult_cutin`, `ult_rain_hiss` (soft filtered noise, 0.8 s). Pin: existing file `spell_magic` at volume 0.3.
- **Engine work: M.** Seeded stratified rain, the pin status, the marker-contact rule.

### 4. Pumpkin knight: 迴旋盾輪 / Ricochet Aegis

- **Fantasy.** The thrown shield becomes a spinning rune wheel that bounces from enemy to enemy.
- **Effect.** The normal path. At release the engine rolls a d6 (shown above the unit with the existing dice sounds): **1 to 2 = 1 extra bounce, 3 to 4 = 2, 5 to 6 = 3.** First contact: a direct hit (within 70 px) is collision 1. If the shield lands on the ground, it skips once, 100 px forward, and hits a unit within 70 px of the skip point (so units from 70 px behind to 170 px ahead of the landing x are in reach). After collision 1, each extra bounce goes to the nearest other living enemy unit within 380 px (a 0.35 s low hop on the enemy side; the fence is not in the way). If only one enemy is alive or in range, it bounces off the ground behind the unit and hits it again. A unit can be hit at most twice per ultimate. **12 damage per collision.** Max on one unit 24. Max in total 4 collisions = 48 across at least two units.
- **Aiming.** Same controls. The aim point is the first contact.
- **Numbers.** E about 13.7, ratio 1.87 (direct 33% x 24, skip-only 24% x 24). Perfect hit 24, a little above a normal 22.
- **Counter-play.** The sky shield stops the first flight (one charge, the ultimate ends). The fence stops it too (fence loses 10). Enemies spaced more than 380 px apart cut the chain. The hops are low, so a sky shield does not stop them.
- **Cannot.** Kill from full HP. Hop across the fence. Heal. Be used on a turn when his sky shield is up (empty hand). Hit one unit three times. Add pips.
- **Beats.** Cut-in with the gold band. Charge: the shield spins up in the hand, a rune ring opens, the die rolls. Release: sideways spin (like a coin, per the owner). Each collision: spark burst and ring, pitch of the ping rises a little each time. Aftermath: the shield falls, fades in stardust, the hand is re-supplied after 0.55 s (existing).
- **Effects, existing presets.** `weapon_trail_shield`, `shield_materialize_ripple` (at the hand), `weapon_rune_halo`, `shield_ricochet_sparks`, `impact_burst` (scale 0.7), `hit_sparks`, `sprite_impact_flash`, `sprite_stardust`, `damage_number`.
- **New effects.** `ricochet_arc_trail` (a gold ribbon along each hop), `lightning_accent` (gold), `ground_rune_spread` (gold) at the last collision.
- **Sprites (Colab).** `ult_ricochet_shield`, `ult_cutin_band`, `fx_lightning_strike`.
- **Sound.** Existing: `dice_rattle`, `dice_result`, `throw_shield`, `impact_unit` per collision, the file `metal_bing` as the ping, pitch stepping 0.98, 1.00, 1.02, 1.04 (inside the +/-6% clamp). New code-made event: `ult_cutin`.
- **Engine work: L.** Target selection for the chain, the skip, the die, the per-unit limit, and the case with one enemy.

### Fit-check for any future class (no `roster_design.md` yet)

A new class's ultimate is acceptable if: at most 40 HP per target, at most 25% of the target team's max HP in total, single-target ratio between 1.5 and 2.1 under the model above, no kill from full HP, at most one new status, the same aim controls, a typical length of 3 s, and the shield and the fence are not ignored.

### Summary table

| Class | Ultimate | Max on one unit | E ratio | Area width | Status | Engine |
|---|---|---|---|---|---|---|
| Skeleton | Triple Spectral Javelin | 39 | 1.63 | 220 px reach | none | M |
| Wizard | Plague Pumpkin Shell | 33 | 1.84 | 240 px | poison 3 turns | M |
| Bat | Shadow-Stitch Shuriken Rain | 20 (4 or 5 shuriken is typical: 16 to 20) | about 1.9 | 300 px | pinned 1 turn | M |
| Knight | Ricochet Aegis | 24 | 1.87 | up to 380 px hops | none | L |

## 1c. Area attacks for normal play (not ultimates)

**How a player gets one.** Through the airdrop crate system (`docs/airdrop_design.md`), so they use its slot, replace rule, 3-turn life and cap of 6 drops, and stay rare. Two new crate items:

| Item | Effect |
|---|---|
| `area_charge` (範圍彈) | The holder's next throw becomes the area shot of its class (list below). One use. |
| `poison_jar` (毒霧罐) | Any class throws a jar that leaves a poison cloud. One use. |

Suggested pool weights for the seeded draw (guess): `area_charge` 2, `poison_jar` 1. An alternative with no items is a per-class cooldown (one area shot every 3 rounds). I did not choose it because it adds a second clock next to the ultimate bar.

**Design rule for area shots.** They are safer, not stronger: expected damage against one target between 0.7 and 1.4 times the class's normal throw, per-target maximum at or under the class's normal hit plus 10, and always below the ultimate's total. They give 1 pip when they damage, like any throw.

**Common rules**

- **Friendly fire: none in version 1.** Area damage and clouds affect only the enemy team of the thrower. A shot that lands short next to your own units does nothing to them. (A toggle `AREA_FRIENDLY_FIRE` can come after a playtest.)
- **Sky shield:** the thrown item is stopped in mid-air at the bar like any projectile, bursts there, and costs one charge. At that height (y about 430) every unit body is more than 240 px away, so nobody is hurt.
- **Fence:** the item bursts on the fence face. The fence loses 15 (area bomb 25). The blast is measured from the impact point, so units that stand at least the radius away from the near face (x 895) are safe: the nearest enemy can stand at 1070 (browser) or 1085 (engine), which is 175 or 190 px.
- **Wind:** affects only the flight of the thrown item. Ground effects (wave, shockwave) ignore wind. The poison cloud drifts.
- **Tombstones:** not in the code today. If they are added (task 34 idea): a tombstone between the impact and a unit halves splash damage (cover), stops the bone wave and breaks, blocks projectiles like any solid, and does not affect the cloud.

| # | Area shot | Class | Radius / size | Damage and falloff | Special | E ratio |
|---|---|---|---|---|---|---|
| 1 | 爆裂南瓜彈 Splash Pumpkin Bomb | Wizard | radius 130 px | 24 within 70 px, straight line down to 10 at 130 px | none | 1.38 |
| 2 | 骨浪 Bone Wave | Skeleton | ground wave, 260 px long, 800 px/s (0.33 s) | 10 flat to every unit whose centre is from 70 px behind the landing to 330 px ahead | stops at the fence (fence loses 5); a unit reachable only through the fence is safe | 0.83 |
| 3 | 手裏劍錐雨 Shuriken Cone | Bat | 5 shuriken at launch angles -8, -4, 0, +4, +8 degrees (landing spread about +/-73 px at angle 54, by my arithmetic) | 4 each, no falloff, at most 20 on one unit | each shuriken follows normal physics; one shield charge per throw | 1.0 |
| 4 | 盾擊震波 Shield Shockwave | Knight | radius 110 px | 14 within 70 px, down to 7 at 110 px | pushes the enemy 40 px away from the impact (clamped to the move limits and 60 px from the fence); this spoils the target's learned aim | 0.9 |
| 5 | 毒霧罐 Poison Cloud Jar | any (item `poison_jar`) | cloud radius 100 px on the ground | no direct damage; a unit inside at the start of its own turn takes **5** (never below 1 HP); cloud lasts **2 rounds** | the cloud drifts 15 px per wind unit at each round start (at most 60 px), clipped at the fence and kept 60 px away from it; affects enemies only | n/a (max 10 per unit) |

**Art and sound for area shots.** Colab images (in `docs/ultimates_asset_requests.md`): `fx_bone_wave` (shot 2), `proj_poison_jar` (shot 5), `icon_area_charge` (the crate item). Shots 1, 3 and 4 reuse existing art: `proj_pumpkin` for the bomb, the bat's shuriken for the cone, the small shield for the shockwave. Existing presets: `impact_burst`, `landing_ring_dust`, `shield_ricochet_sparks`, `dart_rain`, `poison_cloud` (radius 100, 2 rounds), `poison_drip`, `sprite_mist`. Sounds reuse the throw and impact events of the thrower's class, plus `impact_ground_heavy` for the bomb and `poison_tick` for the cloud. No new sound events.

Expected-damage ratio uses the same model as section 1b (hand arithmetic). Item 1: 24 x 33% + 17 x 29% = 12.9 against 9.3. Item 2: 10 x 67% = 6.7 against 8.0. Item 3: 5 x 4 x 33% = 6.7 against 6.7. Item 4: 14 x 33% + 10.5 x 19% = 6.7 against 7.3.

## 1d. Effect showpieces

### Global effects budget

| Budget | Normal | Calm mode |
|---|---|---|
| Particles alive (game system cap, today 500) | 500: ambient and trails 120, normal hits 120, one ultimate 200, reserve 60 | 250 |
| Wind scene items (`wind_fx`, designed at 64 default, 96 max) | 64 | 32 |
| Sprite particles on screen at once | 14 | 7 |
| Ground decals | 6 | 0 |
| Full-screen overlays at once | 1 (the vignette) | 0 |
| Floating numbers alive | 6 | 4 |
| Screen shake | peak +/-10 px x, +/-6 px y, 0.30 s max, 0.5 s between shakes | off |
| Hit-stop | 0.075 s hit, 0.12 s ultimate, 0.16 s KO; at most 0.25 s in any 1 s | 0.05 s max |
| Flashes | no more than 2 in any 1 s, no flash above alpha 0.25 over more than 40% of the screen | no flashes |
| Cut-in | 0.45 s + sequence about 3 s | 0.2 s, no dim, sequence about 1.2 s |

Reason for the flash limits: the W3C success criterion 2.3.1 allows at most three flashes in any one second unless the flash is small or below thresholds ([W3C Understanding SC 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold), page opened). I use 2 to stay under it.

Hand counts of the particles one ultimate keeps alive at its peak, from `particles.js` (`cnt()` grows with the square root of scale, and `fxEmit` multiplies scale by 1.25). Not measured:

| Ultimate | Largest peak (about) | Inside 200? |
|---|---|---|
| Wizard | `poison_cloud` 51, `impact_burst` 43, two `hit_sparks` 40, `poison_burst` 28, rest 5: about 167 | yes |
| Skeleton | three `impact_burst` 87, three `hit_sparks` 48, rest 20: about 155 | yes |
| Bat | `dart_rain` 47, 10 sticks 30, shadow swirl 16, rest 10: about 103 | yes |
| Knight | about 3 collisions alive at once, each `impact_burst` 33 + sparks 17: about 150 | yes |

Ongoing poison drips: `poison_drip` every 0.2 s per poisoned unit is 5 particles per call, about 23 alive per unit, so two poisoned units add about 46 to the "ambient and trails" share. Use a 0.2 s call interval, not the 0.1 s the preset comment suggests.

**Calm mode switch.** One toggle in the settings, default on when the browser reports `prefers-reduced-motion` (a standard media query; I did not test it here), and offered automatically when the average frame time is over 24 ms for 2 s. It applies the right-hand column above and the lighter effect versions named per effect. The engine and the rules do not change in calm mode, only the look.

### The 14 showpieces

| # | Effect | Trigger | Duration | Layers | Budget | Readability rule | Colab sprite |
|---|---|---|---|---|---|---|---|
| E1 | **Hit-stop** | A unit takes damage | 0.075 s hit, 0.12 s ultimate (first hit only), 0.16 s KO | Logic freeze (existing `hitStop`) | 0 particles | Never during the cut-in; cap 0.25 s per 1 s; calm 0.05 s | none |
| E2 | **Screen shake** | Cannon (existing), ultimate impact (0.25 s), KO (0.30 s) | 0.18 to 0.30 s, linear decay | Canvas translate only; the dock and top bar are not on the canvas and do not move | 0 | Never while the human is charging; 0.5 s between shakes; calm off | none |
| E3 | **Floating damage numbers** | Any damage or heal | 1.1 s (preset) | `damage_number`: normal 30 px, ultimate 44 px with gold, poison 22 px green, heal green | at most 6 alive | Hits from one throw within 0.3 s on one unit merge into one summed number | none |
| E4 | **Streak counter** | A side lands 3 or more successful hits in a row | 1.2 s fade | Text below the wind readout, not over units | 1 text | Display only. It is not the energy bar and shows only from 3 on, so the two counters are not mixed. Drop it first if the owner finds it confusing. | none |
| E5 | **Ground rune that spreads** | Ultimate ready (gold), wizard burst (green), knight last collision (gold), bat pin (violet) | 0.6 s spread, then fade | `sprite_rune_circle` squashed to a ground ellipse (height 35% of width), additive | 3 sprites + 3 particles | Only on the ground band y 850 to 900; alpha at most 0.6; never above a body | none (existing sprite) |
| E6 | **Lightning accent** | Ultimate cut-in (one bolt at the thrower's screen edge, class colour), match-deciding KO (white) | 0.18 s bolt + 0.25 s glow | Back glow, bolt sprite, flash overlay | 1 bolt sprite, 12 sparks | Not in the middle 30% of the screen; never over an HP bar; at most 1 bolt per 1.5 s; at most 2 flashes per 1 s; calm off | `fx_lightning_strike` |
| E7 | **Moon glow** | Always; boost when an ultimate becomes ready | 6 s breathing (alpha 0.10 to 0.18), +0.10 for 2 s on ready | One soft additive halo behind the moon in the background | 1 sprite or gradient | Never drawn over the top bar, behind everything else; the moon position must be measured in `bg_graveyard.png` (I did not look at the image) | `fx_moon_halo` (lowest priority; a code gradient is the fallback) |
| E8 | **Kill-cam** | The KO that ends the match, once per match | about 0.9 s real time: ease in 0.15, hold 0.5, ease out 0.25; time scale 0.35 during the hold; world zoom 1.00 to 1.12 on the victim | World scale, `ko_wisps`, `fx_soul_ghost`, vignette | 24 particles + 1 sprite | The zoom stays inside the 1920 x 1080 world (clamp the centre x to 86..1834); the dock and top bar are outside the canvas and do not scale; click skips; calm off | `fx_soul_ghost` (shared with E14) |
| E9 | **Ultimate cut-in band** | Ultimate release | 0.45 s | Dim edges, band sprite, portrait (`portrait_cutin_<class>_shout` from the dock request, fallback `portrait_<class>`, fallback the emoji glyph), name text, 20 sparks (`ult_cutin_sparks`) | 1 band + 1 portrait + 20 particles | Band at y 140 to 380 only, so it never covers the top bar, a unit or the shield height; dim at most 30% at the edges; a click skips; at most 4 per match (2 per side) | `ult_cutin_band` |
| E10 | **Ready ring and pip glow** | A unit is ready | until used | `sprite_rune_circle` breathing at alpha 0.25 + pips gold | at most 4 rings; 1 mote per 0.4 s per ring | Flat on the ground; no motes above the HP bar; calm static ring | `ult_pip_socket` |
| E11 | **Shock ring** | Wizard burst, knight shockwave, area bomb, KO | 0.45 s | One thin ring drawn as a ground ellipse (`shock_ring`) | 2 ring particles | Line width 3 px; never a full-screen circle | none (the Colab `fx_shockwave_ring` is optional texture) |
| E12 | **Ground decals** | Crack from the skeleton ultimate, puddle from the wizard ultimate, pin rune from the bat | until round end, then fade 0.5 s | Drawn under units, over the ground strip | at most 6 | Alpha at most 0.7; never under an HP bar; oldest removed first; calm off | `fx_ground_crack`, `fx_poison_puddle`, `fx_pin_rune` |
| E13 | **Focus vignette** | Cut-in, kill-cam | 0.45 to 0.9 s | A radial gradient from clear to dark violet at the edges (a code gradient, not art) | 1 overlay | At most 30% alpha at the edge, clear in the middle where the units stand | none |
| E14 | **Soul rising** | Any KO (also in 4 v 4) | 1.2 s | `ko_wisps` (existing) + a small ghost sprite floating up | 1 sprite, at most 2 alive | Rises beside the HP bar, never over the next target's body; calm uses `ko_wisps` only | `fx_soul_ghost` |

Lightning, moon and rune effects are tied to the thrower's side colours: player blue-gold, agent violet (same as the shield slabs).

## 1e. Balance

### Tuning rules

| Rule | Value | Check |
|---|---|---|
| Per-target cap | 40 HP per ultimate; no kill from full HP in the browser build (100 HP) and the engine build (85 to 120 HP) | Property test over class, positions, wind, angle, power |
| Poison floor | Poison never reduces a unit below 1 HP | Property test |
| Team cap | One ultimate deals at most 25% of the target team's total max HP | Property test on 4 v 4 line-ups |
| Single-target value | Ultimate E between 1.5 and 2.1 times the normal throw; area shots between 0.7 and 1.4 | Monte Carlo with the model from section 1b |
| Cap per side | 2 ultimates per match (engine: `ultimates_remaining`) | Unit test |
| Bar | 4 hits, reset to 0, ultimate gives 0 pips | Unit test |
| No hidden rules | Spread offsets, radii and bounce counts are published constants | Review of `shared/constants.json` |

Hand values (to be reproduced by the Monte Carlo test): skeleton 1.63, wizard 1.84, bat about 1.9, knight 1.87.

### Automated check plan

Fixed seeds, the injected seeded RNG, the published-error bot (aim error 14 units, same as the built-in AI), no real time.

| Check | What it does | Pass band |
|---|---|---|
| C1 Property tests (fast-check, 1000 runs per class) | Damage never negative. HP never above max. Same seed and same inputs give the same result. Ultimate damage on any unit at most 40. No kill from full HP. Poison never kills. At most 2 ultimates per side. Pips 0 to 4. Ultimate throw gives 0 pips. | 0 failures |
| C2 Tool tests | `submit_action` with `ultimate`: rejected when not ready, when none left, when the knight defends, when the unit is dead, in the wrong phase. A rejected call does not use the turn. | all rejected with the listed reason |
| C3 Ultimate adoption (4 v 4, seeds 1 to 400) | Bot B uses an ultimate as soon as it is ready; bot A never does. Count matches with at least 1 ultimate used and the round of the first "ready". | At least 70% of matches see an ultimate; median first-ready round between 35% and 70% of the match length. If it fails, report it to the owner (fallback: bar per controller). |
| C4 Ultimate edge (same class, 400 matches, sides swapped) | Win rate of B against A | 52% to 65% (an edge, not a decider). 400 matches give a 95% margin of about 4.9 points; 200 would give 6.9, too wide for these bands. |
| C5 Ultimate damage share | Damage from ultimates divided by all damage dealt by the side | 10% to 35% |
| C6 Class vs class (with ultimates, both bots using them) | Win rate of each class against each other, 400 matches | 40% to 60% (same band as task 33) |
| C7 Single-ultimate dominance | Largest single-ultimate damage divided by the target team's total max HP, over all matches | At most 25% (by construction) and, in the matches the ultimate user wins, at most 5% of those wins have the loser's final HP deficit explained by one ultimate alone (loser's HP lost to that ultimate at least 50% of its total HP lost) |
| C8 Single-target E | 10,000 seeded throws per ultimate and per area shot with the uniform +/-210 px error | Within 15% of the hand values above |
| C9 Effects budget (headless, scripted scenes for 4 ultimates and 5 area shots) | Peak alive particles, sprites, decals, numbers | At most the budget table, calm mode at most 50% of normal |
| C10 HUD occlusion (screenshots at the beats) | Pixels changed inside the top bar, the dock and every HP bar rectangle, effects on versus effects off | At most 5% changed |
| C11 Determinism | Same seed gives the same rain slots, die and hits | identical event list |

In 1 v 1 report only: expected adoption near 0 (finding 1).

## 1f. Comparison with other games

Method: I searched, then opened pages. **Could not open (HTTP 403 or 404):** `strategywiki.org/wiki/Gunbound/Gameplay` and `/Mobiles` (403), `liquipedia.net/hearthstone/Hero_Power` (403), `worms2d.info/Armageddon_(weapon)` (404; `worms2d.info/Armageddon` opened instead). **Snippet only** (search result text, page not read): the StrategyWiki line that GunBound's second shot and "SS" differ only a little in delay. I watched no gameplay, so how any of this looks or sounds is not claimed.

| Game | Charge-up | Readability | Fairness | What we copy | What we avoid |
|---|---|---|---|---|---|
| **Hearthstone hero power** ([hearthstone.wiki.gg/Hero_Power](https://hearthstone.wiki.gg/wiki/Hero_Power), opened) | A mana cost (usually 2) and one use per turn. No hold or aim time. | The power icon is face up when available and flips to a grey, empty state after use, and either player can hover over it at any time to read it. | Both sides pay the same cost and get one use per turn, so the rule is symmetric. | A public state icon for the bar, readable by both sides (our pips and ring). Clear "used" state (the bar resets at once). | A repeatable power every turn; ours is rare and earned. |
| **Hearthstone feedback structure** ([Boger article](https://jboger.substack.com/p/hearthstone), opened) | The article describes preparation, emphasis, aftermath, and the player regains control while the animation ends. | Several layers (animation, sound, text) so nothing depends on one cue. | n/a | The three beats in our cinematic; the cut-in is skippable; control returns during the aftermath. | A long blocking animation. |
| **Worms super weapons** ([Super Weapons](https://worms2d.info/Super_Weapons), [Crate probability](https://worms2d.info/Crate_probability), [Armageddon](https://worms2d.info/Armageddon), [Concrete Donkey](https://worms2d.info/Concrete_Donkey), [Holy Hand Grenade](https://worms2d.info/Holy_Hand_Grenade), all opened) | No charge-up for the player. Super weapons come only from crates, and the crate rules are strict: the scheme must allow them, at least 5 times as many ordinary weapon crates as super crates must have appeared, at least 3 minutes must have passed since the last one, then a 1 in 8 chance per weapon crate. | The Armageddon drops about 100 meteors on random spots; the page calls it a last resort that can end a match as a draw and says using it is blind luck. The Concrete Donkey is placed with the mouse and the page says it beats a Freeze defence. The Holy Hand Grenade page says its large blast is hard to keep off your own team. | Fairness comes from rarity and a cooldown, not from skill. | A hard cap and a gap between uses (our 2 per side per match, and 4 hits to refill). | A weapon that can wipe a whole team (our 40 HP and 25% caps). Friendly fire from a huge blast (no friendly fire in version 1). |
| **GunBound special shot** ([Wikipedia](https://en.wikipedia.org/wiki/Gunbound), [Boomer guide](https://www.unknowncheats.me/wiki/Gunbound:Boomer_Guide), both opened) | Each mobile has shots "1", "2" and "SS". The guide says one SS only transforms after about 1.8 s of airtime (stated with "I think"), otherwise it deals little. Stronger shots add delay before the next turn: that guide lists SS delay 1280 against 730 for shot 1, and typical damage 450+ against 150. | The transformation is a visible mid-flight event (it stops, flashes and changes shape, per the guide). | The price is tempo (a longer wait for the next turn), not a one-time resource. Wikipedia says delay depends on the mobile, the weapon and the items used. | A visible "arming" beat in mid-flight (the wizard shell swells at the top of the arc). Making the strong shot cost something even though it is allowed every time. | A bar-free special that needs a long airtime to work (our ultimate always works; the cost is the 4 hits). |

How the three differ from ours: Hearthstone pays with a symmetric resource, Worms with luck-gated crates, GunBound with tempo. We pay with skill (4 hits, per unit), cap the count, and cap the damage. That is closest to Worms' cap and gap, with the earned-by-skill change the owner asked for.

## 1g. Owner questions (one word each, my recommendation first)

1. Is a "player" each **unit**? Yes.
2. Only hits fill the bar (not blocks or misses)? Yes.
3. Reset to 0 after use? Yes.
4. Use 4 hits for every class and drop the older per-class triggers? Yes.
5. Cap of 2 per **side**? Yes.
6. Accept the green draw-time tint for poisoned units (no new art)? Yes.
7. Area shots come from airdrop crates (`area_charge`, `poison_jar`)? Yes.
8. No friendly fire in version 1? Yes.

## 2. Engine work, in order

| Step | Work | Size | Pass condition |
|---|---|---|---|
| 1 | Pip counter, ready flag, reset, per-side cap, public fields | S | C1, C2 pass for pips and cap |
| 2 | `ultimate` argument on the throw action with validation | S | C2 passes |
| 3 | Shared area-damage function with falloff; per-throw shield charge rule; no friendly fire | M | Unit tests for falloff and charge rule |
| 4 | Multi-projectile spawn with delay and offsets | M | Skeleton ultimate and bat cone match hand values (C8) |
| 5 | Status system: poison (with floor), pinned | M | Poison never kills; pinned blocks Move |
| 6 | Wizard ultimate, then bat ultimate | M each | C1, C8 for each |
| 7 | Knight ultimate (chain, skip, die) | L | C1, C8; chain tests with 1, 2, 4 enemies |
| 8 | Cut-in sequencer in the client | M | Screenshot at each beat (C10) |
| 9 | Effects budget manager and calm mode | M | C9 |
| 10 | Area shots and the two crate items | M | C8 for each, airdrop tests from `airdrop_design.md` |
| 11 | Bot match harness and bands | M | C3 to C7 |

Sizes are my estimates (S under half a day, M one to two days, L three days or more), not measured.

## 3. What I could not verify

- Nothing was run: no tests, no bot matches, no game. All E values and particle counts are hand arithmetic.
- How anything looks or sounds, including whether the cut-in band hides anything on a real screen, whether the poison tint reads as green on each unit, and whether the metal ping rain sounds like rain.
- The moon's position in `bg_graveyard.png`, and the real power-to-pixel ratio (I used the 20 px per power unit from a code comment).
- The 4 v 4 layout, spacing and match length (`roster_design.md` is missing). The spacing of 170 px is an assumption, and the pip fill speed depends on match length.
- Whether `prefers-reduced-motion` and the frame-time trigger behave as I describe in the target browsers.
- The GunBound claim about 1.8 s of airtime comes from one community guide that hedges it. The StrategyWiki GunBound pages and the Liquipedia Hearthstone page could not be opened.
