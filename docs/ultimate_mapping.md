# Ultimate mapping: the link-up table (Kiro task 39)

Status: **design only.** I changed no code, art or sound. I cannot play the game, see images or hear audio, so how any effect looks or sounds is **unverified**. Every damage number is my hand arithmetic from the owner's 1.5 x rule and the normal damage `N` in the table below. The rules for WHEN an ultimate may be used are in `docs/ultimate_rules.md`.

Row 7 update: owner 2026-11-15.

Owner words (2026-11-09): "Make a link-up (連連看, a matching table) of all the ultimates I just described." "Kiro, design it."

Sources, in priority order: `(not published)` (wins), `index.html` (built behaviour), `docs/ultimates_design.md` (my task 35, corrected here), `docs/converge_characters.md`, `docs/roster_design.md`, `docs/sound_mapping.md`, `docs/audio_event_map.json`, `js/particles.js`, `assets/`. **Not present:** `docs/review_reconcile.md`, `(not published)`.

## 0. Shared vocabulary and math (so each row stays short)

| Term | Meaning |
|---|---|
| `N` | The class's normal-attack damage, taken **after** the frost curse (x 0.7 while weakened). Working values: skeleton 24, wizard 28, cat-bat 20, knight 22 (`HERO_PROFILES` in `index.html`); flame necromancer (`reaper`) 23 comes from `docs/kiro_53_recommendations.md`; ghost bride 12 and hunchback 22 remain **INVENTED** in `docs/converge_characters.md`. |
| Trigger hit | The ultimate throw's first projectile damaging a unit. It is a **normal hit** (damage `N`, plus that class's normal effect). It is **not** part of the 1.5 x. No trigger hit (sky shield, fence, ground) means no follow-up. The flame necromancer's three-fire volley is an explicit exception: it has no trigger or follow-up phase. |
| Follow-up strikes | The strikes after the trigger. |
| Target set `T` | The units the follow-ups can reach; the class rule is in table 1b. `A` is the trigger unit. |
| 1.5 x rule | **Every unit in `T` takes 1.5 x `N` in total from the follow-ups**, split evenly over the strikes that land on it. Each strike is rounded to 0.1, as the built code does. |
| Trigger unit total | `N + 1.5 N = 2.5 N`. Every other unit in `T`: `1.5 N`. The cat-bat has no trigger hit, so its unit total is at most `1.5 N`. |
| 1 v 1 | `T` is only `A`. Extra follow-ups are lost, not redirected. |

Weakened example (skeleton, `N` = 24 x 0.7 = 16.8): trigger 16.8, each ghost javelin 25.2.

## 1. The link-up table (one row per class, split by columns so it stays readable)

### 1a. Name, owner's words, conflicts

| # | Class | Ultimate (繁中 / English) | Owner's own words that define it | Conflicts with owner rules? |
|---|---|---|---|---|
| 1 | 骷髏長矛兵 Skeleton | 三魂落矛 / Triple Soul Javelins | Owner has not specified; Kiro proposal. (Normal attack words, log section 1: "Throws a javelin ... idle = spear resting on the shoulder in the real hand"; section 6: "the unit hit attacks weaker for 2 throws" = frost curse.) | No. The frost curse stays on the trigger hit only. |
| 2 | 南瓜巫師 Wizard | 南瓜連環爆 / Pumpkin Chain Blast | Owner has not specified; Kiro proposal. (Owner: "Wizard: cannon.") | No. The poison shell of task 35 is dropped (poison is not an owner rule). |
| 3 | 蝙蝠貓刺客 Cat-bat | 手裡劍雨 / Shuriken Rain (the built text is "✨ 大招：手裡劍雨") | Log section 6: "Shuriken become a scatter of 5 over a small area." Log section 6: "the big ultimate deals 1.5 x the class's normal attack." Task: "each shuriken 1.5 x normal / 5." | **Partly.** (a) Built version fires by itself when the third pip lights, which breaks "cannot be used at any time"; arming is added in `ultimate_rules.md`. (b) It has no trigger hit, unlike the generic structure; the owner's cat row does not ask for one, so I keep it. (c) 1.5 x is a ceiling reached only when all 5 land on one unit; owner to confirm (question 3). |
| 4 | 南瓜重裝盾衛 Knight | 連環盾舞 / Shield Chain | Owner has not specified; Kiro proposal. (Normal attack words, log section 6: "A die decides the number of collisions (a bouncing shield); damage is split evenly over them.") | No. The normal attack already bounces, so the ultimate may not be "the bouncing shield" again (task 35 did that). It becomes a bounce that travels to other units. |
| 5 | 鬼娃新娘 Ghost bride | 穿魂哀歌 / Soul-Piercing Dirge | Owner has not specified; Kiro proposal. (Log section 6: "The ghost bride's attack is a SOUND-WAVE attack ... a wave is naturally an area effect.") | **Yes, at the normal-attack level.** Owner: a normal attack hits ONE unit; the wave is area by nature. Change: her normal wave damages only the first unit it touches (rings are visual); the all-units pierce is the ultimate. The start-screen blurb ("everything on the flight path is hurt") must change. |
| 6 | 鐘樓怪人 Hunchback | 鐘樓喪鐘 / Tower Toll | Owner has not specified; Kiro proposal. (Log section 6: "a bell-tower hunchback (鐘樓怪人)"; the bronze-bell weapon and 100 px knockback are from `converge_characters.md`, not the owner.) | No, but the weapon is not owner-confirmed. |
| 7 | 死靈法師 Necromancer (internal id `reaper`) | 三魂火葬 / Three-Soul Pyre | Owner: the black-robed reaper is the flame-magic necromancer. Normal attack: a purple flame held in the palm and pushed forward. Ultimate: the hand is empty with a finger pointing forward while three ghost fires behind the caster change colour and fly out. No scythe, knife, or skull. | No. It is a three-flame volley from one aim; each flame is a normal projectile, not a seeking attack. |
| 8 | Ghost Nun (internal id `hag`, display name PROVISIONAL) | 旋十字 / Spinning Cross | Owner: chest-level push-throw a small wooden cross. Ultimate: the cross flies like a spinning dart. Skill: electric shock stun. | No. These latest owner rules replace the earlier apple-lob design. |

### 1b. Trigger, follow-ups, targets, damage math, worked example

| # | Trigger hit | Follow-up strikes | Targets (`T`) | Damage math | Worked example (from the class's normal damage) |
|---|---|---|---|---|---|
| 1 | The real javelin hits `A`: `N` = 24 and the normal frost curse (-30 % for `A`'s next 2 throws) | 3 ghost javelins fall from above 0.4 s after the trigger, 0.12 s apart, one per unit in `T`, nearest other unit first, then `A` | `A` plus the 2 nearest other living enemies (by public x distance to `A`, no range limit); one ghost javelin per unit | Ghost javelin = 1.5 x 24 = 36 on each unit in `T`. Ghost javelins do not carry the curse | 4 v 4: `A` 24 + 36 = **60**, B 36, C 36, total **132**. 1 v 1: 60 |
| 2 | The cannonball hits `A`: `N` = 28 | One blast at `A`'s x: a ring grows to 240 px in 0.35 s, one strike per unit | Every living enemy whose centre is within 240 px (x distance) of `A`, at most 3 units including `A` (nearest first) | 1.5 x 28 = 42 on each unit in range, `A` included | `A` 28 + 42 = **70**; a neighbour 200 px away 42; total **112**. 1 v 1: 70 |
| 3 | **None.** The scatter replaces the throw | The 5 shuriken, fan -8, -4, 0, +4, +8 degrees, each hits like a normal shot | Whoever a shuriken touches (70 px hit test as normal); no limit on units | Each shuriken = 1.5 x 20 / 5 = **6**; max 30 on one unit (= 1.5 N) | 3 shuriken on B and 2 on C: B 18, C 12, total 30. All 5 on one unit: 30. One shuriken: 6 |
| 4 | The shield's **first collision with a unit**, `A`: `N` = 22 as one plain hit (no die in the trigger) | The die (1 to 6, rolled by the engine like the normal throw) = number of follow-up collisions, low 0.3 s hops, dealt round-robin over `T`. The sky shield only stops the first flight, not the hops | `T` = the 2 nearest other living enemies, then `A`, in that order | A unit that gets at least one collision takes 1.5 x 22 = 33 in total, split evenly over its collisions | Die 4: collisions B, C, A, B. B 2 x 16.5 = 33, C 33, `A` 22 + 33 = 55, total **121**. Die 1: only B 33, `A` 22. Die 2: B, C 33 each, `A` 22. 1 v 1: all collisions on `A`, `A` 22 + 33 = 55 |
| 5 | The wave touches its first unit `A`: `N` = 12 (**INVENTED**) | The wave keeps travelling away from the bride and passes each unit in `T` in order, 0.1 s apart, one strike each | `A` and every living enemy farther from the bride than `A`, at most 4 units in all | 1.5 x 12 = 18 on each unit in `T` | `A` 12 + 18 = **30**, B 18, C 18, D 18, total **84**. 1 v 1: 30 |
| 6 | The bell hits `A`: `N` = 22 (**INVENTED**) and the normal knockback of 100 px (**INVENTED**) on `A` only | One toll: a ground ring runs left and right from the impact x, one strike per unit. Neighbours are fixed at impact, before the knockback | `A` and the units next to it in line order (1 or 2 of them), at most 3 units | 1.5 x 22 = 33 on each unit in `T`, no knockback on the follow-up | `A` 22 + 33 = **55**, two neighbours 33 each, total **121**. 1 v 1: 55 |
| 7 | **No trigger hit.** The normal shot is a purple palm flame: `N` = 23 and it refreshes burn for 2 damage at each of 3 round starts, non-lethal (task 53). | Three ghost fires launch 0.15 s apart from a pointing front hand. Each is an ordinary projectile; the first enemy hit gains one non-stacking hallucination that skips its next turn. The three caster fires vanish at 0.35 s and return one per earned pip. | Each flame uses the normal single-target hit box; this design has no multi-target guarantee. | Flames deal `1.1 N`, `1.3 N`, then `1.5 N` times a provisional volley scale 0.5 (owner 2026-11-15: lower the total now, tune later), rounded to 0.1. Burn applies once to the whole volley. | `N` = 23: **12.7**, **15.0**, **17.3**, total **45.0** direct damage (before the scale: 25.3, 29.9, 34.5), plus one burn and hallucination on the first enemy hit. |
| 8 | **No separate trigger.** Normal attack: one chest-level wooden-cross dart, `N` still unchosen. Ultimate: one spinning cross follows its contact path. Skill: electric shock sets the same shortened-next-turn stun. | The spinning cross touches the first 3 distinct enemies in its path, at most twice per enemy. After its final touch, one touched enemy is randomly selected for electric stun using injected seeded randomness. | The first 3 distinct enemies in contact order; each may receive 1 or 2 touches, never more. | **PROVISIONAL:** every touch = `0.5 N`, rounded to 0.1; 6 hits maximum = `3 N` total. `N` and the 0.5 multiplier need owner balance tuning. | With **PROVISIONAL** `N` = 20 and contacts A, A, B, B, C, C: six hits x 10 = **60** total; A, B, or C receives the electric stun. |

Rule for a trigger kill: if the trigger hit kills `A`, follow-ups still resolve on the other units that were chosen at impact. This does not apply to the flame necromancer's no-trigger three-fire volley.

Balance note (hand arithmetic, not tested): in 1 v 1 the three hits that light the pips leave the target `100 - 3N` HP (skeleton 28, wizard 16, cat 40, knight 34, flame necromancer 31, bride 64, hunchback 34). The necromancer's no-trigger volley totals 45.0 direct damage when all three fires hit (after the provisional volley scale 0.5; 89.7 before it), plus one burn status for up to 6 non-lethal damage. Its old 45-damage skull-and-scythe finisher is **OBSOLETE**. Other class totals remain 60, 70, 30, 55, 30, and 55 in table order.

### 1c. Controls, effects, sounds, art, engine status

Effects use preset names found in `js/particles.js` (my search output was cut, so the existing list may be longer). Sound events are in `docs/audio_event_map.json` unless marked "via sound_mapping.md". New items need free CC0 audio or Colab art; none is made here.

| # | Controls | Effects: existing / new | Sounds: existing / new | Art needed (Colab names) | Engine status |
|---|---|---|---|---|---|
| 1 | Menu `✨ 大招`, hold, release. Nothing else | Existing: `weapon_charge_aura`, `weapon_trail_spear`, `face_glow_skeleton`, `weapon_rune_halo`, `sprite_ghostfire`, `sprite_impact_flash`, `impact_burst`, `hit_sparks`, `damage_number`. New: `ghost_spear_fall` (3 translucent spears falling onto each unit) | Existing: `charge`, `throw_spear`, `impact_unit_heavy`, `impact_unit` (via sound_mapping.md), file `bones_rattle.ogg` under each ghost landing. New: none | `ult_spectral_spear` (task 35 request 5, still valid), `ult_pip_socket` | Design only |
| 2 | Same | Existing: `weapon_charge_aura`, `muzzle_flash`, `smoke_puff`, `weapon_trail_cannon`, `impact_burst`, `landing_ring_dust`, `hit_sparks`, `sprite_impact_flash`, `damage_number`. New: `shock_ring` (thin ground ellipse, 0.35 s). The built wizard shake (0.18 s) stays | Existing: `charge`, `throw_cannon`, `impact_unit_heavy`, `impact_ground_heavy`, file `rock_break.ogg` as the planned heavy-ground layer. New: none | `fx_shockwave_ring` (task 35 request 11, optional texture), `ult_pip_socket` | Design only |
| 3 | Same. Angle from the pointer as always | Existing and in the built code: the 5 flying shuriken, `weapon_trail_dart`, float text. Existing but unused here: `dart_rain` (not needed: the 5 shuriken are the effect). New: none | Existing: `throw_shuriken`; hits use `impact_unit`; optional file `metal_bing.ogg` on each landing, pitch inside +/-6 %. New: none | None new (`assets/weapons/shuriken.png`), `ult_pip_socket` | **Built** in `executeThrow` as an automatic branch, cat-bat only, per side, no arming, gives 1 pip after landing. Needs the arming from `ultimate_rules.md` |
| 4 | Same. The die is rolled by the engine and shown above the unit like the normal throw | Existing: `weapon_trail_shield`, `shield_materialize_ripple`, `weapon_rune_halo`, `shield_ricochet_sparks`, `impact_burst`, `hit_sparks`, `sprite_stardust`, `damage_number`. New: `chain_hop_trail` (a short gold ribbon per hop) | Existing: `dice_rattle`, `dice_result`, `throw_shield`, `impact_unit`, file `metal_bing.ogg` per collision with pitch stepping 0.98, 1.00, 1.02, 1.04. New: none | `ult_ricochet_shield` (task 35 request 6, still valid), `ult_pip_socket` | Design only. The normal bouncing shield is built (1 to 6 collisions, even split) |
| 5 | Same | Existing: `weapon_rune_halo`, `sprite_mist`, `impact_burst`, `hit_sparks`, `damage_number`. New: `soundwave_rings` (translucent rings that widen, drawn from the normal-attack ring sprite) | Existing stand-ins: `spell_magic.ogg` and `ghost_real.ogg` (both exist). New events: `throw_soundwave`, `impact_soundwave` (CC0 sources needed) | The class set from `converge_characters.md` section 3c (`bride_idle`, `bride_windup`, `bride_release`, `bride_hit`, `bride_portrait_*`) and the normal-attack ring sprite named in her Colab prompt (**I could not find it in `colab/jobs.json`**). No new ultimate art | Design only; class not built (start-screen card "製作中") |
| 6 | Same | Existing: `weapon_charge_aura`, `smoke_puff`, `impact_burst`, `landing_ring_dust`, `hit_sparks`, `damage_number`. New: `bell_toll_rings` (three bronze ground rings, uses `shock_ring`) | Existing: `impact_unit_heavy`, file `bell_round.ogg` on the toll (the file exists in `assets/audio/sfx/`). New event: `throw_bell` (from `converge_characters.md`) | `proj_bell` and the `hunch_*` set (`converge_characters.md` 3c), `fx_shockwave_ring` | Design only; class not built |
| 7 | Same. A normal shot is a purple flame held above the open palm, then pushed forward. The ultimate uses the empty, pointing hand. | Existing: `sprite_ghostfire`, `hit_sparks`, `impact_burst`, `ko_wisps`, `damage_number`. New presentation: a purple palm-flame charge and a burn-body flame overlay. No skull, scythe, knife, or slash effects. | New events from task 53: `flame_throw`, `flame_hit`, `burn_tick`, `soulfire_volley`; all require a CC0 source before shipping. | `proj_flame`, `fx_flame_impact`, `fx_burn_body`, the flame-hand `reaper_*` poses and pointing `reaper_ult`; no skull, scythe, or slash art. | Design only; `timeline("reaper_flame_trio", input)` aliases the three ghost-fire timeline. |
| 8 | Chest-level cross push-throw; ultimate cross spins like a dart; skill applies the electric shortened-turn status. | Code-made: `cross_spin_trail` (orange cross and black smoke), `spark_electric` (yellow-white stun arcs), `ult_pip_socket`. No blue-violet aura. | No new sound event is required for the quiet landing. | `proj_cross` and the ghost-nun pose set remain art work; the ultimate effects themselves are code-made. | `NunUlt.resolve()` and `ElectricStun` are pure modules; `timeline("nun_cross_dart", input)` is ready for page wiring. |

Existing sound notes: `ultimate_ready` points at `(not published)`, which is **not** in the folder, so the synthesized arpeggio plays. `assets/audio/CREDITS.md` has no credit line for `bell_round`, `bones_rattle`, `metal_bing`, `rock_break`, `chime_single`, `spell_magic` or `ghost_real` (I searched for those names), so I could **not verify** they are CC0. The main line must confirm before shipping (owner rule: free CC0 sound only).

## 2. Second table: each owner statement linked to the rows that implement it

| Owner statement (source) | Rows | Where it is implemented | State |
|---|---|---|---|
| "An ultimate cannot be used at any time (不能隨時放大招)." (task) | 1 to 7 | `ultimate_rules.md` section 2a gate, 2b input, 3 alternatives | Designed; the built cat branch breaks it until arming exists |
| "Make a link-up of all the ultimates I just described." / "Kiro, design it." (task) | 1 to 7 | This file, tables 1a to 1c | Done |
| Normal attack: ONE shot at ONE unit (log, "Single vs multi target") | 1 to 7 (normal side) | Table 0 `N`; row 5 conflict fixed (wave single-target) | Row 5 needs owner confirmation |
| Ultimate hits MULTIPLE units (same log row) | 1, 2, 3, 4, 5, 6 | Table 1b "Targets" | Designed. Row 7 is the owner's own exception |
| Three successful hits light three pips above the head; only then can the ultimate be triggered (log, "Ultimate trigger") | 1 to 7 | `ultimate_rules.md` 2a (gate), 2i (pips); counter built in `index.html` | Counting built per side; per unit and the display need work |
| Each player counts their own hits (log) | 1 to 7 | `ultimate_rules.md` 2a, 2g (`ult_pips` per unit) | Designed; depends on log question 3 |
| At most 2 ultimates per match (log) | 1 to 7 | `ultimate_rules.md` 2a, 2d, 2g (`ULT_MAX_PER_MATCH`) | Built per side (`ultUsed < 2`) |
| Each unit hit by an ultimate takes 1.5 x the class's normal attack; confirmed "好" (log, "Ultimate damage per unit") | 1, 2, 4, 5, 6, 7 (per unit); 3 (per shuriken) | Table 0 (1.5 x rule), table 1b "Damage math" | Designed. Row 3 is a ceiling (conflict noted in 1a) |
| Structure: a TRIGGER hit first, then follow-up strikes; the trigger hit is a normal hit and not part of 1.5 x (task, log) | 1, 2, 4, 5, 6 | Table 0 (trigger hit), table 1b "Trigger hit" | Designed. Rows 3 and 7 are no-trigger volleys (noted). |
| Flame necromancer: purple palm flame; ultimate = empty pointing hand and three colour-changing ghost fires from behind the caster | 7 | Row 7, all three tables | Design and timeline updated; browser wiring and art remain unverified. Superseded 2026-11-15, owner: skull-and-scythe combo. |
| Cat-bat: normal = one shuriken; the 5-shuriken scatter is the ultimate, each shuriken 1.5 x normal / 5 (log, task) | 3 | Row 3 | **Built** (arming missing) |
| Ghost bride: attack = SOUND WAVES, an area effect (log) | 5 | Row 5 (normal wave single-target, ultimate pierces all) | Designed; conflict with "normal = one unit" flagged |
| Hunchback: bell-tower character (log) | 6 | Row 6 | Designed; weapon not owner-confirmed |
| Knight: bouncing shield, die 1 to 6 collisions, damage split evenly (log) | 4 | Row 4 (the same die and even split carry into the ultimate) | Normal attack built; ultimate designed |
| Skeleton: javelin with frost curse, the unit hit attacks 30 % weaker for its next 2 throws (log) | 1 | Row 1 (curse stays on the trigger hit); `ultimate_rules.md` 2f (weakened units may use it) | Normal attack built; ultimate designed |
| Wizard: cannon (task) | 2 | Row 2 | Normal attack built; ultimate designed |
| At least 6 classes, at most 4 v 4 on the field (log) | 1 to 7 | Seven rows; "Targets" never exceeds 4 enemy units (row 5 maximum) | Designed |
| One character chosen at the start (log) | 1 to 7 | `ultimate_rules.md` 2c (arming belongs to one unit and one turn) | No extra work |
| Screen stays clean (task) | 1 to 7 | `ultimate_rules.md` 2i (no cut-in, no dimming); table 1c effects use existing presets first | Designed |
| Free CC0 sound only (task) | 1 to 7 | Table 1c "Sounds" and the CC0 note under it | Existing files unverified; new events need CC0 sources |
| Art made on Colab (task) | 1, 2, 4, 5, 6, 7 | Table 1c "Art needed" and section 4 | Nothing generated here |

## 3. Third table: conflicts between `docs/ultimates_design.md` (task 35) and the owner rules

| # | What `ultimates_design.md` says | Owner rule | Corrected value |
|---|---|---|---|
| 1 | Energy bar needs **4** hits; 4 pips; `ult_pips` 0 to 4; four rune sockets 4 x 22 px; "4 hits for every class"; fill estimates 4 / p throws (section 1a, 1b, 1e, 1g question 4, engine step 1) | THREE successful hits light three pips (log, "latest, overrides the earlier 4 hits") | **3** pips; `ult_pips` 0 to 3; three sockets; fill needs 3 / p throws (9 at p = 0.33, 6 at 0.5, 4.3 at 0.7) |
| 2 | Skeleton "Triple Spectral Javelin": 3 javelins x 13, max 39, spread by power offsets | Each unit hit takes 1.5 x `N`; trigger hit first | Row 1: trigger 24 + ghost javelin 36 per unit |
| 3 | Wizard "Plague Pumpkin Shell": 24 direct + poison 9 over 3 turns, burst radius 120, poison status and green tint | Same; poison is not an owner rule | Row 2: trigger 28 + blast 42 per unit within 240 px; no poison |
| 4 | Bat "Shadow-Stitch Shuriken Rain": a marker, then **10** shuriken x 4 in a 300 px zone, pinned status, `fx_pin_rune` | Scatter of **5** shuriken over a small area; each 1.5 x normal / 5 | Row 3: 5 shuriken x 6, fan -8..+8 degrees, no pin, no marker |
| 5 | Knight "Ricochet Aegis": d6 gives 1 to 3 extra bounces, 12 per collision, max 4 collisions; it duplicates the normal bounce | The normal attack IS the bouncing shield (1 to 6 collisions, even split); ultimate per unit 1.5 x | Row 4: trigger 22 + die 1 to 6 follow-up collisions, 33 per unit, split evenly |
| 6 | Per-target cap of **40 HP**, team cap 25 %, "no ultimate kills from full HP", single-target E ratio 1.5 to 2.1 (shared rules, 1e) | 1.5 x `N` per unit hit, no cap given | Cap removed. The wizard's 1.5 x 28 = 42 already exceeds 40. Keep the caps only as optional test flags |
| 7 | Ultimates for 4 classes only; no reaper, bride or hunchback (it said `roster_design.md` was missing) | Roster of 7 with the reaper's combo settled | Rows 5, 6, 7 added; the fit-check at the end of section 1b is replaced by the 1.5 x rule |
| 8 | Statuses `poison`, `pinned`, and public field `ground_effects` (`poison_cloud`) | Only the frost curse is an owner status | Public `statuses` lists only `frost_curse`; `ground_effects` dropped |
| 9 | Menu entry hidden for a knight with an active sky shield ("empty hand") | Not an owner rule; no code shows an empty hand | Removed. Only a defend turn blocks it (`ultimate_rules.md` 2c) |
| 10 | Cut-in band 0.45 s with edge dimming, kill-cam, lightning accents, moon boost and 14 showpieces (1d) | "Screen stays clean" | Version 1 uses pips, ready ring, name text only. The showpieces stay optional behind a calm flag, not built |
| 11 | Area shots for normal play from airdrop crates (`area_charge`, `poison_jar`): bomb, bone wave, cone, shockwave, cloud | A normal attack hits ONE unit | Set aside until the owner approves; they would break the owner's single-target normal attack |
| 12 | Ultimate throw "gives 0 pips" | Owner log question 2 (assumed reset) | Kept. The built cat code gives 1 pip after the scatter lands and is to be changed |
| 13 | "Ultimate replaces the unit's one throw", pips public, per-unit bar with a cap of 2 per side, hit definition (one pip per throw, blocks and misses do not count), no confirm step, knight die rolled by the engine | Compatible with the owner's rules | **Kept** |
| 14 | Public field `ult_kind` examples such as `triple_javelin`; asset requests `ult_poison_shell`, `ult_shuriken_shadow`, `fx_pin_rune`, `fx_poison_puddle`, `fx_ground_crack`, `fx_bone_wave`, `proj_poison_jar`, `icon_area_charge` | Follows from rows 2 to 5, 11 | New ids in `ultimate_rules.md` 2g. Drop those eight Colab requests; keep `ult_pip_socket`, `ult_spectral_spear`, `ult_ricochet_shield`, `fx_shockwave_ring` |

## 4. Other documents that disagree with the owner rules (found while reading, not edited)

| Document | Disagreement | Owner rule that wins |
|---|---|---|
| `docs/roster_design.md` | Adds a Plague Doctor and a Lantern Warden as the new classes; the bat throws a volley of three, the skeleton pierces, the wizard bursts, the doctor poisons: several normal attacks hit more than one unit | Owner roster is ghost bride, hunchback, grim reaper; a normal attack is one shot at one unit; the bat's normal attack is one shuriken |
| `docs/converge_characters.md` | Cat-bat "8 per shuriken, 40 in total"; the built code gives 6 each, 30 in total (20 x 1.5 / 5). Its bride row still says bouquet area damage (its own correction block voids that) | 1.5 x rule; sound-wave attack |
| `(not published)` section 1 | "Energy bar needs FOUR successful hits ... ultimates NOT designed ... do not build any ultimate effect or sound" | The later section 6 rows say THREE hits and ask for the designs |
| `docs/game_mode.md` ultimate section | Four hits; per-class triggers; bouncing as an ultimate | Three hits; bouncing is the knight's normal attack |
| `index.html` start-screen blurb for the bride | "Everything along the flight path is hurt" | Normal attack hits one unit |
| `docs/sound_mapping.md` | Says the five new SFX and the ambient folder are missing | They are present in `assets/audio/sfx/` and `assets/audio/ambient/` now |

## 5. New Colab art and new sound events this design asks for

| Kind | Name | Used by |
|---|---|---|
| Art (new) | `proj_cross` and the ghost-nun pose set | row 8; the cross trail and electric arcs are code-made |
| Art (reuse from task 35) | `ult_spectral_spear`, `ult_ricochet_shield` | 1, 4; optional weapon texture only |
| Sound events (new) | `throw_skull`, `scythe_slash`, `throw_soundwave`, `impact_soundwave`, `throw_bell` | rows 7, 5, 6 |
| Effect presets (code-made) | `ult_pip_socket`, `ghost_spear_fall`, `shock_ring`, `chain_hop_trail`, `soundwave_rings`, `bell_toll_rings`, `spark_electric`, `cross_spin_trail` | shared pips; rows 1, 2, 4, 5, 6, 8 |

## 6. Questions for the owner (one word each, my recommendation first)

1. Does the trigger unit also take the follow-up (so `2.5 N` on it, like the reaper)? **Yes.**
2. Is the bride's normal wave single-target (first unit it touches), with the pierce kept for the ultimate? **Yes.**
3. Cat-bat: damage per shuriken that lands (as built), or a flat 1.5 x for every unit touched? **Per shuriken.**
4. Are the working numbers for reaper 18, bride 12 and hunchback 22, and the bell weapon, acceptable for now? **Yes, until a balance run.** I suggest raising the bride once her wave is single-target.
5. Keep the die in the knight's follow-up (reach by luck)? **Yes.**

## 7. What I could not verify

- Nothing was run. No game, no test, no tool call against the engine. All damage figures are arithmetic from `N` and 1.5 x.
- How any effect looks or any sound plays; whether `ultimate_ready` has its file (it does not) or the existing sound files are CC0 (no credit line found).
- Whether the three pips are drawn in `index.html` (no code found) and what the menu looks like with a fourth entry.
- `colab/jobs.json` has no reaper, bride or hunchback entries, so I cannot confirm the owner-log statement that their art is queued.
- My preset search output was cut, so the list of existing presets may be incomplete.
- `docs/review_reconcile.md` and `(not published)` are not in the repo.
- The follow-up timings (0.4 s, 0.12 s, 0.25 s, 0.1 s), 240 px radius and the target-selection rules are guesses for a playtest.
