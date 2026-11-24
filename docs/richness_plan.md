# Richness plan: 16 content additions for Pumpkin Killer (Kiro task 34)

Status: **design only.** I wrote no code, made no images and ran nothing. Every statement about how something looks, sounds or feels is **unverified**. Numbers are first guesses for a playtest unless they are arithmetic on constants I read.

Owner words this answers: "What I want is something RICHER", at least 6 classes, 4 v 4, attacks that differ, wizard-school Halloween magic, a clean screen, no extra spending, Colab makes the art. Ultimates are **not** designed here and nothing below depends on one.

## 0. What I read, and what is missing

Read: `docs/kiro_task_34.md`, `docs/game_mode.md`, `(not published)`, `docs/airdrop_design.md`, `docs/airdrop_asset_requests.md`, `docs/sound_mapping.md`, `docs/wind_design.md`, `docs/kiro_task_33.md`, and the constants and particle presets in `index.html`, `js/particles.js`, `assets/`.

Facts I rely on:

| Fact | Value | Where |
|---|---|---|
| Field, ground, fence | 1920 x 1080, ground y 860, fence x 895..1025, 250 px tall | `index.html` |
| Fence strength | `wallHp` 100, 15 per projectile hit, so about 7 hits; 3 damage states | `index.html`, `game_mode.md` |
| Wind | range about +/-4, `WIND_ACCEL` 72 px/s^2 per unit | `index.html` |
| Hit damage, HP | 20..28 per hit (browser), HP 85..120 | `HERO_PROFILES`, `game_mode.md` |
| Turn | 12 s timer, humans first then agents, one throw per unit | `TURN_SECONDS` |
| Particle presets that already exist | `muzzle_flash`, `smoke_puff`, `sprite_impact_flash`, `sprite_ghostfire`, `sprite_rune_circle`, `damage_number`, `impact_burst` | `js/particles.js` |
| Sprites that already exist | `fx_ghostfire`, `fx_rune_circle`, `fx_impact_burst`, `fx_hit_spark`, `fx_charge_glow`, `ui_target_ring`, `ghost_lantern`, `drop_ghost`, `crate_fire` | `assets/fx`, `assets/env` |
| Drop zones, no-go band | player 200..835, agents 1085..1720, fence band 835..1085 | `airdrop_design.md` |

**Missing from this checkout:** `docs/roster_design.md` (task 33 output) does not exist. I therefore treat the roster as the **four classes that exist** (skeleton javelin, pumpkin wizard cannon, bat-cat shuriken, pumpkin knight thrown shield) and mark everything that needs more classes or 4 v 4 as **NEEDS 4v4**. `docs/experience_design.md` and `(not published)` also do not exist; I did not rely on them.

Size key (main-line time, my guess): **S** under half a day, **M** about one day, **L** two days or more.

## 1. Rules every item must obey

### 1a. Clean-screen budget (the owner's "screen must stay clean")

| Layer | Hard limit at any moment | Why |
|---|---|---|
| Weather | **1** event (fog, rain, or storm). Never two at once; 3 rounds quiet between events | Weather is the biggest screen change |
| Neutral roamer | **1** (ghost or bat swarm), never in a fog or storm round | One extra moving thing is the most the eye follows |
| Airdrop | 1 (already the rule) | `airdrop_design.md` |
| Ground patches | **2** on the whole field, none within 150 px of a unit at spawn | Patches sit where units stand |
| Tombstones | **2** per side | They are cover, not decoration |
| Status icons | **2** per unit, 32 px, next to the HP bar | A third status replaces the oldest |
| Floating text | **1** at a time (damage numbers count; combo text replaces the number for 1 s) | Hearthstone-style three beats need space |
| New HUD widgets | **0**. Reuse the wind arrow, HP bar, timer. Weather is shown in the scene | Owner: not messy |
| Screen flash | Overlay alpha at most 0.25 for at most 100 ms, at least 1.5 s between flashes | Photosensitivity safety (my rule, not from a source) |
| Keep-out rectangles | Fog, rain, roamers and patches never draw over the top bar, timer, wind readout, dock or any HP bar (reuse the `avoid` list from `js/wind_fx.js`) | Readability |

If a budget is exceeded in a playtest screenshot, remove in this order: roamer, rain streak count, patch glow, ring marks.

### 1b. Fairness rules (product principle: the AI cannot cheat)

1. **Everything new is public state:** stage, weather, fog rectangle, moon, patches, tombstones with HP, roamer position, every unit's statuses. Hidden: the seed and future schedule only.
2. **Same rules for humans and sub-agents.** No effect reads a side flag. Anything an agent cannot see on screen it cannot see in `get_public_state`.
3. **Fog hides the same thing from both sides** (section 3, item 2). Agents lose precision in their landing record exactly as humans lose the ring.
4. **No trial throws, no simulator.** Hazards and roamers are static during a round, so an agent can reason from positions and its landing record the way a human does.
5. **Deterministic.** Every event is scheduled from the match seed with a fixed draw order. Same seed and same inputs give the same match.
6. **Nothing here touches the ultimate bar.** Status ticks, combos, lightning and hazard damage are **not** "successful hits" (assumed; open question 4). No ultimate effect, sound or art is added.
7. **Everything costs nothing:** programmatic effects, existing sprites, synthesized or already-verified CC0 sounds, Colab art. No paid service.

### 1c. Time-to-kill guard

A hit is 20..28 damage on 85..120 HP. Two caps keep every route to a kill a throw:

- **Status application** (burn, poison): at most about 9 damage in total per application, under half of the smallest hit.
- **One-off event damage** (lightning plus combo): at most 18 in total, under the smallest hit (20).
- A status tick may not reduce a unit below **1 HP** (my design choice, no source), so the last point of damage always comes from a throw and the kill-cam always has a throw to show.

## 2. Ranked list

Score = wow per effort, 1 (poor) to 5 (best). Ranked by score, then by smaller effort, then by lower clean-screen risk.

| Rank | Item | Family | Score | Engine | Clean-screen risk | Build on |
|---|---|---|---|---|---|---|
| 1 | Turn cue, damage numbers and combo text | f | 5 | S | Low | NOW |
| 2 | Fog bank | b | 5 | S | Medium | NOW |
| 3 | Kill-cam | f | 4 | S | Low | NOW |
| 4 | Rain shifts the wind | b | 4 | S | Low | NOW |
| 5 | Status core: Burn, Chill, Curse, Pin (Poison scaffold) | c | 4 | M | Medium | NOW |
| 6 | Elemental combos (Steam, Shock, Flare) | c | 4 | S after 5 | Low | NOW |
| 7 | Thunderstorm with lightning strikes | b | 4 | M | Medium (flash) | NOW |
| 8 | Ground hazards: ghost-fire patch, quicksand | a | 4 | M | Medium | NOW |
| 9 | Destructible tombstones | a | 4 | M | Medium | NOW |
| 10 | Stage set, first slice of 2 extra stages (4 total later) | a | 4 | M for 2, L for 4 | Low | NOW |
| 11 | Full moon boosts a class | b | 3 | S | Low | NOW |
| 12 | Practice range | h | 3 | S | Low | NOW |
| 13 | Neutral roamers: lantern ghost, bat swarm | e | 3 | M | Medium | NOW |
| 14 | Class passives (one pro, one con) | d | 3 | M | Low | NOW for 4 classes, **NEEDS 4v4 roster** for the rest |
| 15 | Daily Haunting: daily seed, achievements, unlock order | g | 3 | S to M | Low | NOW |
| 16 | Survival waves against ghosts | h | 2 | L | Medium | **NEEDS 4v4** (units array) |

4 v 4 skirmish itself is the task 33 deliverable, not a content item here. Section 6 shows how each item behaves once it exists.

## 3. The 16 items

Format: fantasy, how it plays, art (Colab), sound, engine, risk, score. "Fallback" is what the main line can show if the Colab art has not arrived, using only art and effects that already exist.

### 1. Turn cue, damage numbers and combo text (family f) - score 5, engine S, NOW
- **Fantasy:** the graveyard tells you whose turn it is and what just happened, in one glance.
- **Plays:** at the start of each unit's turn a rune ring pulses once (0.6 s) under that unit in its team colour (blue for players, purple for agents, as for the shields), and the unit's HP bar flashes once. After a hit, one damage number rises from the target (size grows with percent of max HP, leans with wind as `wind_design.md` already specifies). When a combo fires (item 6) its 1 to 2 word label replaces the number for 1 s. The Hearthstone feedback article ([Boger](https://jboger.substack.com/p/hearthstone)) describes three beats: preparation, emphasis, aftermath, with control returned to the player during the aftermath. I did not re-open it for this task; the summary comes from `docs/airdrop_design.md`, where it was opened. No input is blocked.
- **Art:** `turn_marker_ring` (new). Fallback: existing `fx_rune_circle`, tinted.
- **Sound:** new event `turn_start` = the already-planned `chime_single` at gain 0.2 (file unverified in this checkout, `sound_mapping.md` section 0), fallback `ui_hover`. Combo text reuses `shield_place`. Damage numbers are silent.
- **Engine:** event queue entry per turn start; `damage_number` preset already exists. Labels are data.
- **Risk:** low. Rule: one text at a time. Remove the HP-bar flash first if it feels busy.
- **Wow per effort:** 5. Cheap, and every second of play shows it.

### 2. Fog bank (family b) - score 5, engine S, NOW
- **Fantasy:** a graveyard mist rolls in and swallows the place your shot lands.
- **Plays:** from round 3, a 360 px wide bank appears at a seeded x inside one side's zone and drifts with the public wind (`x += wind * 60` px per round, clamped to the zones, never over the fence band). It lasts 2 rounds. A throw that lands inside the bank shows **no landing ring, no trail tail and no impact marker**; the sound still plays, but low-passed (about 1.2 kHz, -4 dB). A **hit** is still visible because HP bars and damage numbers stay above the fog. The throw record for both sides stores `landing: {hidden: true, zone: floor(x / 240)}` and the hit flag, **not** the exact x. The throw's own wind value stays recorded. Skill: you correct from a coarse zone and from sound pan, like a human would in real fog. Fog drift also tells the player which way the wind blows.
- **Art:** `fog_bank` (new). Fallback: the procedural fog puffs from `js/wind_fx.js`, drawn as one clustered bank.
- **Sound:** one scripted ghost cue at arrival (existing synthesized `ghost` through `ambientSfx.trigger('ghost')`, as `airdrop_design.md` does). The low-pass on impacts is a bus filter, no new file.
- **Engine S:** `weather = {kind:'fog', x0, x1, rounds_left}` in public state; one rule in the history writer. The hidden-record rule must be tested for human and agent views alike.
- **Risk:** medium. Fog must not cover HUD rectangles (keep-out list). It slightly hurts the product line "learn from the record"; that is the point, and both sides lose the same detail.
- **Wow per effort:** 5. It changes how the same throw feels, for almost no engine work.

### 3. Kill-cam (family f) - score 4, engine S, NOW
- **Fantasy:** the last hit gets a movie moment.
- **Plays:** on a KO the camera pushes in to 1.25x on the victim for 0.9 s, time runs at 0.35x for the first 0.4 s, the K.O. plaque drops in, then control returns at once. Only a KO triggers it (not a status tick, by rule 1c). Skip with any click. It is rendering only, so game state is unchanged and tests stay valid.
- **Art:** `ko_plate` (new). Fallback: existing `fx_impact_burst` plus a code-drawn vignette (an effect, not art).
- **Sound:** existing `ko` event with its planned `bones_rattle` layer; music ducks for 0.4 s (the duck mechanism for heavy hits exists per `sound_mapping.md` rule 9).
- **Engine S:** camera transform and time scale in the renderer only.
- **Risk:** low. In 4 v 4 a KO may happen every few turns, so the cam is shorter there (0.6 s) and skipped for the second KO in the same round.
- **Wow per effort:** 4.

### 4. Rain shifts the wind (family b) - score 4, engine S, NOW
- **Fantasy:** the storm front pushes the wind around while you aim.
- **Plays:** rain lasts 3 rounds. After **each side's phase** (humans, then agents) the wind changes by exactly +1 or -1 (seeded, clamped to +/-4). Both sides therefore get the same number of changes and see the current wind before they throw. `wind_at_throw` is already recorded in history, so learning stays possible, and `wind_design.md` open question 4 (limit change between rounds) is respected: no change above 1 per phase. Rain also douses Burn (item 6). Wind sound and scene reaction follow the new value as already designed.
- **Art:** `rain_sheet` (new, streaks and splashes). Fallback: code-drawn streaks (a particle effect).
- **Sound:** `rain_bed`, a synthesized filtered-noise bed (same method as the wind bed in `wind_design.md` section 4), replaces `wind_bed` while it rains; the wind-follows-volume rule is unchanged. One bed at a time, per `sound_mapping.md`.
- **Engine S:** a weather kind with a wind hook between phases.
- **Risk:** low. Cap 60 streaks; none over keep-out rectangles.
- **Wow per effort:** 4.

### 5. Status core: Burn, Chill, Curse, Pin (Poison scaffold) (family c) - score 4, engine M, NOW
- **Fantasy:** each weapon leaves a mark on its target that you can read at a glance.
- **Plays:** see section 4 for the full table. Each class's weapon applies one status on a **direct hit** (the existing 70 px hit test), never on splash and never by chance, so tests and play are exact. Rules: one of each status per unit, reapplying refreshes the duration, at most 2 statuses per unit, ticks never reduce a unit below 1 HP.
- **Art:** `status_icons_sheet` (new, five 96 px icons shown at 32 px). Fallback: coloured dots with a letter.
- **Sound:** reuse the existing `poison_tick`; add small synthesized cues `burn_tick`, `chill_apply`, `curse_apply`, `pin_apply` (each under 0.5 s, from the existing synth recipe set; no new files).
- **Engine M:** a `statuses` list per unit in public state, a tick hook at turn start, an aim-error hook (Chill), an effective-wind hook (Curse), a move-block hook (Pin). Poison is built as a data entry but has no weapon source (section 4).
- **Risk:** medium. Icons are 32 px and must differ by colour and silhouette. The screen shows at most 2 per unit.
- **Wow per effort:** 4.

### 6. Elemental combos: Steam, Shock, Flare (family c) - score 4, engine S after item 5, NOW
- **Fantasy:** wizard-school elements that react with each other.
- **Plays:** three recipes only (section 4). Each shows its label (蒸氣, 感電, 閃焰) as combo text for 1 s plus one effect.
- **Art:** `steam_puff_sheet` (new). Fallback: existing `smoke_puff` preset tinted light.
- **Sound:** new synthesized `steam_hiss` (noise burst, 0.6 s); `shield_place` for the label.
- **Engine S:** a lookup table keyed by (status or patch, weather or hit) to an outcome, with a test per row.
- **Risk:** low. One label at a time.
- **Wow per effort:** 4. Combos are what players describe afterwards.

### 7. Thunderstorm with lightning strikes (family b) - score 4, engine M, NOW
- **Fantasy:** the sky itself picks a spot to hit and you decide whether to stand there.
- **Plays:** storm = rain (item 4) plus lightning, one weather slot. At the start of each round a flickering **warning ring** (the existing `ui_target_ring` look, gold) marks where lightning will strike at the **end** of that round. A strike deals 12 damage to any unit within 60 px, knocks one fence damage state (15 wall damage, same as a projectile) if it lands on the fence, and destroys a tombstone (item 9). The ring is public, so a unit can Move away (costing its learned aim, as with crates) and an agent can do the same from state. A strike on a unit in rain adds the Shock combo (item 6). Max one strike per round, 3 rounds per storm.
- **Art:** `lightning_bolt_sheet` (new, three bolt variants). Fallback: code-drawn jagged line plus `fx_impact_burst`.
- **Sound:** the planned `thunder` ambient kind (`sound_mapping.md` 2b) played as a **scripted** cue about 0.4 s after the flash; blocked from firing within 6 s of a heavy hit by the existing rule 9. Verified-by-ear status: unverified.
- **Engine M:** strike schedule from seed, warning ring in public state (`strike_x`, `strike_round`), damage and tombstone hooks.
- **Risk:** medium, from the flash. Flash limits in section 1a are mandatory, and the flash covers only the sky and field, never the HUD.
- **Wow per effort:** 4. The best single "that was cool" moment in the demo.

### 8. Ground hazards: ghost-fire patch and quicksand (family a) - score 4, engine M, NOW
- **Fantasy:** the graveyard floor fights back.
- **Plays:** up to 2 patches, each 120 px wide, spawned at round start at a seeded x inside a side's zone, at least 150 px from any unit, lasting 3 rounds, with a one-round flicker before they become active (the flicker is public as `active_from_round`). A unit that **ends its Move** on a patch (x within half the width + 40 px) gets Burn (ghost-fire) or **Mired** (quicksand: its next Move die is halved, rounded up). Ghost-fire flames lean with the wind, like the Worms oil drum fire that the Worms Knowledge Base says follows the wind ([worms2d.info Oil Drum](https://worms2d.info/Oil_Drum), opened). Rain removes a ghost-fire patch after 1 round. A cannonball that lands within 60 px of a fire patch triggers Flare (item 6).
- **Art:** `hazard_patch_sheet` (new, two patches). Fallback: existing `sprite_ghostfire` preset on the ground for fire; a darker ground strip tint for sand.
- **Sound:** existing `step`/`move_step` plus `burn_tick` on entry; quicksand uses `step_leaf` pitched down (inside the +/-6% clamp, so the effect is small; accept it).
- **Engine M:** patch list in public state, a check at the end of Move, the patch-spawn rule (the airdrop zone logic is reusable).
- **Risk:** medium. Patches sit on the same strip as crates and units; the cap of 2 and the spawn distance keep it readable.
- **Wow per effort:** 4.

### 9. Destructible tombstones (family a) - score 4, engine M, NOW
- **Fantasy:** old gravestones you can hide behind until someone smashes them.
- **Plays:** 1 to 2 tombstones per side, each 70 x 90 px with 40 HP, placed 180..300 px from the fence's near edge and at least 160 px from any unit. A projectile that touches a tombstone box stops and deals the normal damage to it, so **flat shots are stopped and lobs pass over** (the unit hit box is 190 px tall, so low arcs are partly covered). Two hits destroy one; it leaves a rubble sprite that no longer blocks, and a small ghost wisp rises. This gives the flat-versus-lob choice that task 33 wants for different classes.
- **Art:** `tombstone_set` and `rubble` (not in the first 8 requests; see the Notes in `richness_asset_requests.md`). Fallback: reuse a platform sprite or skip the item.
- **Sound:** `impact_fence` for a hit and `rock_break` layer on `impact_ground_heavy` for the break (both exist or are planned).
- **Engine M:** a props list in public state, a collision check before the unit hit test, a rubble state.
- **Risk:** medium. Cap at 2 per side. They are always the same colour family as the ground.
- **Wow per effort:** 4.

### 10. Stage set: 4 graveyards, first slice of 2 (family a) - score 4 for the slice, engine M for 2, L for 4, NOW
- **Fantasy:** the same duel in a different corner of the haunted village.
- **Plays:** a stage is a **data row**: background image, fence type (position, width, height, HP, number of damage states), ground strip, a hazard preset, an ambient preset (leaf, dust and fog counts from `wind_fx`). The match seed picks the stage; the lobby shows it. Proposed four (names are working names):

| Stage | Fence | Terrain and hazards | Mood |
|---|---|---|---|
| Haunted Hollow (the current one) | black-iron picket, 130 x 250, HP 100 | flat; ghost-fire patches | baseline |
| Pumpkin Patch | low wooden fence, 150 x 190, HP 70 | pumpkins as cover (tombstone rule, 20 HP); mist default | friendly, flat shots matter |
| Crypt Court | stone wall with arch, 120 x 330, HP 160 | high wall forces lobs; torch light that leans with wind | steep arcs |
| Bone Marsh | broken bone fence, 200 x 160, HP 60 | quicksand and (later) toadstool poison; fog default | slow, hazard-heavy |

  Build the slice with Pumpkin Patch and Crypt Court first (they change arcs, not just looks). The existing assets `fence_black_intact.png`, `ground_strip.png` and `bg_graveyard.png` stay for Hollow.
- **Art:** per stage one background, one fence set in 3 damage states, one ground strip: 4 to 5 Colab images per stage. Not in the first 8 requests.
- **Sound:** `night_bed` for all; a stage may override the bed volume only.
- **Engine M for 2:** replace the fence constants and the `wallHp` rule with a stage table; spawn ranges and the airdrop zones must read the stage table, not fixed numbers (zones come from `airdrop_design.md`).
- **Risk:** low. One stage per match.
- **Wow per effort:** 4 for the slice; 3 if all four are built at once.

### 11. Full moon boosts a class (family b) - score 3, engine S, NOW
- **Fantasy:** the moon favours the creature that hunts at night.
- **Plays:** once per match, from round 4, a moon rises for 3 rounds. The class with the moon affinity gets **+15% damage, rounded** (e.g. 24 becomes 28), and a rune aura (small ring) shows under each boosted unit. The boosted class is chosen from classes that are **on the field** (public), so the moon is never wasted and never sides with an absent class; both teams benefit if both have that class. Cap: the boost is below a third of a hit.
- **Art:** `moon_disc` (not in the first 8). Fallback: reuse `fx_rune_circle` as the aura and skip the moon image.
- **Sound:** a bell (`round_start` with the planned `bell_round`) at moonrise. The wolf howl suggested in `docs/sound_mapping.md` section 4 is **not** used until the owner picks a file.
- **Engine S:** a table class to modifier in public state `sky: {moon, boosted_class, rounds_left}`.
- **Risk:** low.
- **Wow per effort:** 3.

### 12. Practice range (family h) - score 3, engine S, NOW
- **Fantasy:** a quiet corner of the graveyard to learn the wind.
- **Plays:** no opponent turns and no turn timer. Three straw ghost targets (HP 1) at seeded distances on the opposite side; free throws with the real wind rules and the thrown-path trail kept. The wind changes by seed after every throw (cycling through -4..+4), so there is no button, counter or panel (the HUD rule allows no new widget); the existing trail and damage numbers do the teaching, which fits "feel first". It also gives a calm place to show the wind learning loop without an opponent.
- **Art:** `target_dummy` (not in the first 8). Fallback: existing `ui_target_ring` on the ground.
- **Sound:** all existing throw and impact events.
- **Engine S:** a mode flag that disables AI turns and ends nothing.
- **Risk:** low.
- **Wow per effort:** 3.

### 13. Neutral roamers: lantern ghost and bat swarm (family e) - score 3, engine M, NOW
- **Fantasy:** the graveyard has residents who do not care who is winning.
- **Plays:** from round 3, at most one roamer per round, never in a fog or storm round, never within 2 rounds of an airdrop ghost leaving. It is **parked for the whole round** at a public (x, y) in the central lane (x 700..1220, y 300..500) and moves only between rounds. This keeps it exact for an agent that gets one decision per round, and for a human who sees it before the throw.
  - **Lantern ghost:** a pale ghost with a lantern (visually unlike the airdrop ghost, which carries a crate at y about 170). The first projectile that touches its 160 x 200 box vanishes in a puff and the ghost leaves. It blocks one shot for whoever throws first, so the cost falls on whoever commits first; a lob over it (y above 520 at its x) passes. Hitting it does no damage.
  - **Bat swarm:** a flock 220 x 140. A projectile passing through gains a fixed 120 px/s sideways push in the swarm's drift direction (shown by the swarm's lean); nothing disappears.
- **Art:** `roamer_lantern_ghost`, `roamer_bat_swarm` (not in the first 8). Fallback: the existing `ghost_lantern.png` for the ghost; skip the swarm.
- **Sound:** existing `ghost_real` or `ghost_moan1` once at arrival, bats from the existing synthesized `bat` kind.
- **Engine M:** a collision test along the flight path and a roamer schedule from the seed.
- **Risk:** medium. A lost shot can feel unfair. Turn order is a confirmed rule, so I do not change it; the only mitigations are that the roamer is visible before the first throw and that there is at most one per round. Cut the lantern ghost first if playtests show frustration.
- **Wow per effort:** 3.

### 14. Class passives, one pro and one con (family d) - score 3, engine M, NOW for the 4 existing classes
- **Fantasy:** each creature is a little different even before it throws.
- **Plays:** see section 5. Passives are small, visible, tied to the world events above, and **not** ultimates (nothing here changes an energy bar, a hit counter or a special shot).
- **Art:** none beyond the status icons; a passive is shown by a one-line tooltip on the portrait.
- **Sound:** none.
- **Engine M:** a per-class modifier table consulted by the status, hazard, weather and roamer code. It also means classes added by task 33 only need one row each.
- **Risk:** low.
- **Wow per effort:** 3. The player learns them by playing.
- **NEEDS 4v4 roster:** passives for classes 5 to 8 cannot be written until `docs/roster_design.md` exists.

### 15. Daily Haunting: daily seed, achievements, unlock order (family g) - score 3, engine S to M, NOW
- **Fantasy:** the graveyard is different every day, and everyone who plays that day sees the same one.
- **Plays:** the seed is a hash of the local date (`YYYY-MM-DD`). It picks the stage, the weather schedule, the roamer schedule and **one daily modifier** from six: Gale (wind never below 2), Mist Night (fog every other round), Wisp Rain (airdrop every second round), Tough Bones (+10% HP), Glass Cannons (+20% damage, -20% HP), Silent Night (no wind, no weather). The title shows the seed code (6 characters) so two players can compare. **No leaderboard**: product non-goals exclude accounts and cloud persistence, so records stay in the browser (`localStorage`: best round count, achievements). The date is read once at the edge (the client), not inside the engine, so the engine stays pure.
  - **Achievements (8, all computed from the event log, so each is testable):** First Blood, Wind Reader (3 hits in a row with |wind| at least 3), Steam Punk (trigger Steam), Out of the Fog (hit a target inside fog), Lightning Dodger (move out of a strike ring and survive the round), Crate Raider, Fence Breaker, Clean Sweep (win without losing a unit).
  - **Unlock order for a short demo:** start with Knight and Skeleton (the most readable), unlock Wizard after the first win, Bat-cat after any 3 achievements, and the task 33 classes after that. **The contest build ships with a "show all" switch ON by default** so judges are never locked out in 90 seconds; the unlock order is the path for a first-time player.
- **Art:** none required. Achievement toasts reuse the combo-text plate.
- **Sound:** `chime_single` (planned) for a toast.
- **Engine S to M:** seed derivation, a modifier table, an event-log reader.
- **Risk:** low.
- **Wow per effort:** 3.

### 16. Survival waves against ghosts (family h) - score 2, engine L, **NEEDS 4v4**
- **Fantasy:** hold the graveyard against the night.
- **Plays:** humans (up to 4 units) throw at ghost targets that drift in from the right side, 8 waves with 2, 3, 3, 4, 4, 5, 5 and a boss ghost with 3x HP. A ghost that reaches the fence band removes one shared life (5 lives). No hidden information. The ghosts are scripted targets, **not** sub-agents, so this mode is a side attraction, not the showcase (the showcase is humans against agents).
- **Art:** `ghost_target_set` (not in the first 8).
- **Sound:** existing ghost kinds; wave start reuses `round_start`.
- **Engine L:** needs the `units` array and a target list; do not start before task 33's first step passes.
- **Risk:** medium.
- **Wow per effort:** 2.

## 4. Status effects and combos in detail (family c)

### 4a. Statuses

All numbers are guesses. Totals stay under 1c's cap of about 9 damage.

| Status (label) | Icon colour | Effect | Duration | Total harm | Source (weapon or field) | Cleared by |
|---|---|---|---|---|---|---|
| Burn (灼燒) | orange | 4 damage at the start of that unit's turn | 2 rounds | 8 | **Wizard cannonball direct hit**; ghost-fire patch; lightning on a unit | Rain, Chill (Steam) |
| Chill (寒凍) | cyan | The unit's next throw has aim error x1.5: the human's power meter runs 25% faster, the agent's published error is x1.5. Its next Move die is -1 | 1 round | 0 damage, a tempo cost | **Skeleton javelin direct hit** | Burn (Steam), time |
| Curse (詛咒) | violet | The wind counts reversed for that unit's next throw. The wind arrow in the HUD flips and turns violet for that unit's turn, and `wind_at_throw` records the effective value | next throw | 0 damage | **Bat-cat shuriken direct hit** | Calm wind item (airdrop), time |
| Pin (定身) | grey-white | The unit cannot Move next turn (it can still throw) | 1 round | 0 damage | **Knight shield direct hit** | time |
| Poison (中毒) | green | 3 damage at the start of its turn | 3 rounds | 9 | **No weapon source in this plan.** Field only, from the future Bone Marsh toadstool (stage 4) | Heal item |

Rules: one of each per unit; reapplying refreshes its duration; at most 2 statuses per unit (a third replaces the oldest); ticks never go below 1 HP; a status never counts as a "successful hit" for the ultimate bar (assumed).

**Poison note:** `docs/game_mode.md` drafts a wizard ultimate that poisons everyone in a blast and turns them green. The owner has **not** approved that. This plan gives Poison no weapon source, so it cannot collide with the future ultimate design. If the owner wants a poison weapon, it will be added after the ultimates are designed.

**Why each class gets one native status:** the statuses are the "what must a player do differently" difference that task 33 wants: Burn punishes standing still, Chill punishes the next shot, Curse changes how the wind must be read, Pin keeps a unit in a hazard or a strike ring.

### 4b. Combos

| Label | Trigger | Outcome | Cap |
|---|---|---|---|
| 蒸氣 Steam | Burn meets rain, or Burn meets Chill on the same unit | Both removed, a steam puff, no damage | benefits the target; one per unit per round |
| 感電 Shock | Lightning strikes a unit in rain | +6 damage on top of the 12, and Pin | total 18, below the smallest hit (20) |
| 閃焰 Flare | A cannonball lands within 60 px of a ghost-fire patch | The patch lasts 1 more round and grows by 40 px | no damage; a patch never exceeds 200 px |

## 5. Per-class passives (family d)

One pro, one con, tied to the world events. None changes the damage table, the HP or any ultimate.

| Class (HP) | Passive | Pro | Con |
|---|---|---|---|
| Skeleton spearman (100) | Hollow Bones | Immune to Poison and Curse | Chill lasts 1 round longer (brittle bones) |
| Pumpkin wizard (85) | Owl Scout | His own throws keep the exact landing x in the record and the ring on screen inside fog, for whoever controls him (human or agent) | A lightning warning ring that appears within 120 px of him snaps onto him (lightning-rod hat) |
| Bat-cat assassin (90) | Cat Feet | Ignores ground patches (no Burn, no Mired) | Wet fur: during rain her Move die is -1 |
| Pumpkin knight (120) | Iron Pumpkin | All statuses last 1 round shorter (minimum 0) | Heavy plate: Mired lasts 2 rounds on him |
| Classes 5 to 8 | reserved | **NEEDS 4v4** (`docs/roster_design.md` not found) | |

The moon boost (item 11) is separate: it goes to whichever class is on the field and has the moon affinity, and is not a passive.

## 6. How the items change in 4 v 4

| Item | 4 v 4 change |
|---|---|
| 1 Turn cue | One ring per active unit; with 4 units per side the ring is the only mark of whose turn it is. Highest value in 4 v 4 |
| 2, 4, 7 Weather | Unchanged, one at a time. Fog may cover several units; HP bars stay above the fog |
| 3 Kill-cam | Shorter (0.6 s), skipped for a second KO in one round |
| 5, 6 Statuses | The cap of 2 per unit still holds; with 8 units on the field icons are 28 px |
| 8, 9 Patches, tombstones | Counts stay at 2 patches and 2 tombstones per side; spawn distance 150 px from **every** unit |
| 13 Roamers | Still one per round |
| 14 Passives | Rows for the new classes needed |
| 16 Survival | Needs the units array (task 33, step 1) |

## 7. Game modes (family h)

| Mode | Status | Notes |
|---|---|---|
| 1 v 1 duel | exists | Baseline for everything above |
| Practice range | item 12, NOW | No AI turns |
| 4 v 4 skirmish | task 33 | Needs the units array and turn queue; all of this plan applies |
| Survival waves | item 16, NEEDS 4v4 | Ghosts are targets, not agents |

## 8. Recommended 3-step build order for the next 7 days

Every effect in steps 1 to 3 has an art-optional fallback (section 3), so a late Colab batch never blocks a pass condition. Send the Colab requests on **day 0** (`docs/richness_asset_requests.md`).

### Step 1 (days 1 to 2): "Weather you can see, and a game that tells you what happened"
Items 1, 2, 3 and 4: turn cue and damage numbers, fog bank, kill-cam, rain.
**Pass conditions (verifiable by the main line):**
1. Automated `test_weather_schedule`: same seed gives the same list of (round, kind, x0, x1) on two runs; at least 19 of 20 seeds differ; no weather before round 3; never two at once; at least 3 quiet rounds between events.
2. Automated `test_fog_redaction`: for 10,000 random throws that land inside a bank, the human-view and the agent-view history both contain the zone and the hit flag and **no** exact landing x; outside fog the record is unchanged.
3. Automated `test_rain_wind`: during rain the wind changes by exactly 1 after each side's phase, stays in -4..+4, and `wind_at_throw` equals the wind the integrator used.
4. Automated `test_killcam`: it fires only on a KO, lasts at most 0.9 s and returns control in the same tick.
5. Screenshot, forced seed: a fog round with the turn ring under the active unit and at most one floating text. The check: render fog in a debug colour and assert zero overlap with the keep-out rectangles (top bar, timer, wind readout, dock, HP bars).

### Step 2 (days 3 to 5): "Fire, frost, hex"
Items 5, 6 and 8: statuses, combos, ghost-fire and quicksand patches.
**Pass conditions:**
1. Automated property tests (fast-check, as the tech rule asks): HP never above max or below 0; damage never negative; one application never deals more than 9 in total; at most 2 statuses per unit; ticks never reduce below 1 HP.
2. Automated `test_status_sources`: each class applies exactly its own status on a direct hit and none on splash or miss; Poison has no weapon source.
3. Automated `test_combos`: one assertion per row of section 4b, including "Burn plus rain removes Burn".
4. Automated `test_public_state`: agent view and human view of every status and patch are equal; the key set has no seed or schedule.
5. Automated balance run from task 33's plan: bot versus bot over 200 matches per class pair with statuses on; win rate stays within 40 to 60 percent (the band task 33 proposed). If that script does not exist yet, run a simplified 4-class round robin and report the band.
6. Screenshot: a unit with two status icons, a ghost-fire patch, a rain round and the 蒸氣 label.

### Step 3 (days 6 to 7): "Storm night, a daily seed, a practice corner"
Items 7, 12 and 15: thunderstorm, practice range, Daily Haunting (seed, daily modifier, 3 of the 8 achievements).
**Pass conditions:**
1. Automated `test_lightning`: strike x equals the announced warning ring one round earlier; 12 damage only within 60 px; Shock adds 6 and Pin; flash overlay alpha at most 0.25, at most 100 ms, at least 1.5 s apart (checked on the effect timeline).
2. Automated `test_daily_seed`: same date string gives the same stage, weather schedule, roamer schedule and modifier; different dates differ.
3. Automated `test_practice`: no AI turn is ever taken; targets spawn at seeded distances.
4. Automated **demo replay**: with `DEMO_SEED` (tuned by the main line) and two scripted bots, the log within 20 rounds contains at least one each of fog, rain, a Steam combo, a lightning strike and a KO.
5. Screenshot contact sheet: six frames, one per event above, each passing the keep-out check.

Deferred to week 2: stage set (item 10), tombstones (9), moon (11), roamers (13), passives (14), survival (16).

### Demo script: what a judge sees in the first 90 seconds
Built from steps 1 to 3 only. Each line names the item it shows.

| Time | Judge sees | Item |
|---|---|---|
| 0:00 to 0:10 | Title shows today's seed code and its daily modifier. The match opens in the graveyard with leaves drifting with the wind; a rune ring pulses under the player's cat | 15, 1 |
| 0:10 to 0:25 | First throw: hold, release, trail, a damage number. The agent answers with a visibly different aim from its record | existing, 1 |
| 0:25 to 0:40 | A fog bank rolls in along the wind. The player's next shot vanishes in the mist; a muffled thud; the HP bar drops, so the hit is clear | 2 |
| 0:40 to 0:55 | The ghost drops a crate (already built). The wizard's cannonball hits: Burn icon, 4 damage ticks | 5 |
| 0:55 to 1:10 | Rain starts. The wind arrow shifts by 1 after each phase. Rain douses the burn: 蒸氣 | 4, 6 |
| 1:10 to 1:20 | A gold warning ring flickers on the ground. The player moves away, lightning strikes the empty spot, one flash, thunder | 7 |
| 1:20 to 1:30 | The final hit: kill-cam push-in, K.O. plaque, music ducks; control returns at once | 3 |

## 9. Comparison with reference games

Method: I opened the pages marked "opened". Claims marked **snippet only** come from search snippets and I could not open the page. Content was rephrased for compliance with licensing restrictions. I did not watch gameplay video; how any of these games looks or sounds is not claimed. I do not copy art or names.

| Game | How its content is rich | What this plan takes | What this plan avoids |
|---|---|---|---|
| **Worms series** ([Wikipedia](https://en.wikipedia.org/wiki/Worms_(series)), opened, first part only; [Oil Drum](https://worms2d.info/Oil_Drum), opened; [Sudden Death scheme](https://worms2d.info/Sudden_Death_(scheme)), opened) | A deformable landscape; 50+ weapons and tools with a saved "scheme" per game; optional crates and Sudden Death. The oil drum is a map element: when hit it explodes into flames that follow the wind and die out; it can also heat up through 3 stages, and drums can chain. Variety comes from a **scheme** (a rule set), not from new engines | Hazards that react to wind (item 8); a pre-set "modifier" bundle (item 15); a chain reaction as a table, not free physics (item 6) | 50 weapons; permanent terrain destruction; the player picks the scheme |
| **Scorched Earth** ([Wikipedia](https://en.wikipedia.org/wiki/Scorched_Earth_(video_game)), opened) | Many weapon types and power-ups; options for gravity, wind and meteorite showers; walls that bounce or wrap; shields and parachutes make single-hit kills rarer | Weather-like random events (items 4, 7) and defensive items (the airdrop plan) | A money shop (the owner allows no spending; also a different genre loop); huge option lists |
| **Pocket Tanks** ([Wikipedia](https://en.wikipedia.org/wiki/Pocket_Tanks), opened) | A short match (10 volleys) scored by points; a destructible environment; a small move allowance; hundreds of weapons added through packs (385 on mobile as of its page) | A **short match** that fits a demo; terrain that you can use as cover (item 9) | 385 weapons; paid packs |
| **GunBound** ([Wikipedia](https://en.wikipedia.org/wiki/Gunbound), opened) | Each "mobile" has 3 weapons (1, 2, SS); terrain, wind and elemental phenomena force new aim; a "delay" system makes strong actions cost time; modes: Solo, Tag, Score, Jewel, Powerball. In Solo, a dead player gets to change the wind or drop items | **Mode variety on one engine** (items 12, 16); a dead player still doing something is a possible week-2 idea for 4 v 4 | Stacking power-ups; one hit dealing 100 damage |
| **Slay the Spire** (Daily Climb; [Custom Mode page](https://slaythespire.wiki.gg/wiki/Custom_Mode), opened) | The Daily Climb picks 3 modifiers for the day at random; Custom Mode lets a player pick any modifiers and the seed; achievements and leaderboards are off in Custom Mode. That all players share one seed per day is **snippet only** ([wiki.gg search result](https://slaythespire.wiki.gg/wiki/Weekly_Patch_14_-_Bullet_Time) and the [Fandom page](https://slay-the-spire.fandom.com/wiki/Daily_Challenge), which returned HTTP 403 when I opened it) | A daily seed with a small modifier set (item 15); one modifier stays readable | A leaderboard (no cloud); 20 modifiers |

**What the comparison says:** these games reach "rich" through **a small number of rule bundles you can swap** (a scheme, a mode, a modifier) and **hazards that interact with the core mechanic** (wind), not through a large count of unrelated features. That is the shape of items 8, 9, 15 and the weather set here.

## 10. Open questions for the owner (one word each, my recommendation first)

1. Weather: one event at a time, from round 3, with 3 quiet rounds between events? **Yes.**
2. Curse flips the wind for the cursed unit's next throw? **Yes.**
3. Can a status tick bring a unit to 1 HP but never kill? **Yes.**
4. Do status ticks, hazards, lightning and combos count as "successful hits" for the ultimate bar? **No.**
5. Does fog hide the exact landing from sub-agents as well as humans? **Yes** (same record for both).
6. Contest build: all classes unlocked, with the unlock order only for first-time players? **Yes.**
7. Poison weapon source waits until the ultimates are designed? **Yes.**
8. Are 4 stages enough, and is the order Pumpkin Patch, Crypt Court, Bone Marsh right? **Yes** (working names).

## 11. Summary (6 lines)

1. 16 additions ranked by wow per effort; top 6 are the turn cue/damage numbers/combo text, fog bank, kill-cam, rain-shifts-wind, statuses and combos, all buildable on the 1 v 1 engine now.
2. Only survival waves and the new-class passives need the 4 v 4 roster; `docs/roster_design.md` is not in this checkout, so I used the four existing classes.
3. Clean-screen rules cap weather at 1, roamer at 1, patches at 2, status icons at 2 per unit and text at 1; fairness rules make every new effect public state and hide the same data from humans and agents.
4. Build order: days 1 to 2 weather and feedback, days 3 to 5 statuses, combos and patches, days 6 to 7 storm, daily seed and practice; each step has automated tests plus a screenshot check, and every effect has an art-free fallback.
5. Five references compared (Worms, Scorched Earth, Pocket Tanks, GunBound, Slay the Spire); `docs/richness_asset_requests.md` lists 8 Colab images.
6. Nothing was run, played or heard; no file outside `docs/` was touched.

## 12. What I could not verify

- Nothing was played or run. Damage, durations, widths, flash limits, and the 7-day schedule are guesses; effort sizes are guesses.
- `docs/roster_design.md` does not exist, so per-class numbers for classes beyond the four are open.
- The sound files `chime_single`, `thunder`, `bell_round` and `rock_break` are named in `docs/sound_mapping.md` but that file says they were not in the checkout; `rain_bed` and the small status cues are new synthesized recipes I cannot hear.
- Whether the browser engine and the MCP engine can both host a status list without a large rewrite (they use different wind models today, per `wind_design.md` section 0).
- The Fandom Slay the Spire page returned HTTP 403, so "everyone shares one seed per day" is snippet only. The Worms series page was opened only in its first ~4 KB. I did not open the Hearthstone article again for this task; its three-beat summary is taken from `docs/airdrop_design.md`, where it was opened.
- The rule that status ticks stop at 1 HP is my own choice, not taken from a source.
- Whether the full-width fog and the lightning flash are comfortable to look at: needs a human eye and a safety review.
