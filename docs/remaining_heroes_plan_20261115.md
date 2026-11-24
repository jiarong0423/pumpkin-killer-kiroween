# Remaining heroes plan (work block B21), written 2026-11-15 by Kiro task 116
Docs only. Nothing was run and no picture was opened (file names only). Marks: [file:line] = read there; [guess] = my reading. Sizes: S = one small run, M = one run with a new test, L = several runs.
**The brief's "rows 5 to 7" are out of date.** Later owner decisions replace them, so I use the decided numbers (steering rule 5). INVENTED = no owner number.
- Row 5 bride (12 damage, 1.5x ring) is replaced by: wave hits only the aimed unit [owner_feedback_log.md "Kiro 76 questions answered", Q6], ultimate = precise hit, then a bat swarm of 25 x 1.3 = 32.5 on every enemy [kiro_74_flow_plan_claude-sonnet-5.5.md:82].
- Row 6 hunchback (bell, 22, 100 px knockback) is replaced by: giant axe, HP 110, damage 21, knockback 50 px [class_stats_v2.md section 1]; ultimate = boomerang axe, return hit 31.5 [kiro_74_flow_plan_claude-sonnet-5.5.md:83].
- Row 7 reaper (skull, 3 scythe slashes) is replaced by: necromancer, flame, burn 2 x 3, ultimate = 3 flames of 11.5 [owner_feedback_log.md:146; kiro_53_recommendations.md section 5].
- The necromancer IS the reaper: renamed, id stays `reaper` [owner_feedback_log.md:136]. `COMING_HEROES` still lists it as a third card [index.html:361-365].
- Stale code: `js/class_stats.js` has bride 75/27, hunchback 130/20/bell, reaper 110/22 [js/class_stats.js:113-123; scripts/test_class_stats.js:48]. `js/ultimate_fx.js` has bride 12, hunchback 22, reaper 18, a scythe helper and NO timeline for the three [js/ultimate_fx.js:22-26,57].
- The page has one launch speed for every class [index.html:995,1263]; `class_stats_v2.md` wants 0.9 (bride) and 0.85 (hunchback). See question 4.

## 1. What exists, per hero
### 1a. Necromancer (id `reaper`)
| Item | In code | In assets/ | Drive list only | Missing |
|---|---|---|---|---|
| Profile, blurb, glyph | none; card text only [index.html:361-365]; no `HERO_PROFILES.reaper` [index.html:525] | `assets/units/unit_reaper_idle.png` (+ `_lowpalm`) | `reaper_flame_idle*_r11/r13` | profile, blurb, glyph, tab, `aiClass` list [index.html:246-249,371,403] |
| Portrait | `DOCK_PORTRAIT` has 4 heroes [index.html:1569] | `assets/portraits/reaper_front.png` (made before the redesign [guess]) | none | `necro_front.png` [kiro_73_art_pack_gpt-5.6-terra.md:4]; emoji fallback exists [index.html:379] |
| Poses: idle, charge, release, hit, empty | none | `necro_idle`, `necro_windup`, `necro_release`, `necro_hit`, `necro_empty`; `reaper_idle1/2`, `reaper_charge1/3` | `necro2_*_r15`, `necro3_*_r16`, `necro4_release_r17`, `necro_*_r14`, `reaper_pose_*_r12` (which version is installed is unknown [guess]) | `charge2`, a pointing-hand ultimate pose (only `reaper_pose_ult_v1_r12` on Drive); fingertip anchors file `(not published)` [owner_feedback_log.md "Flame as its own layer"] |
| Weapon / effects | circling fires, one per pip, `ORBIT_FIRE_CLASSES=["reaper"]` [index.html:694,2494]; `fx_ghostfire_purple` loaded [index.html:495]; `proj_axe` already bleeds [index.html:1759] | `fx/sprites/fx_flame_comet`, `fx_flame_hand_purple`, `fx_ghostfire_purple` | `fx_flame_comet_*_r17` (v1 to v3) | burn status (`applyBurn`/`tickBurn` do not exist; only poison and bleed [index.html:1553-1563]); flame projectile; volley |
| Sounds | `THROW_SOUND` has no flame [index.html:345] | `bones_rattle.ogg`, `spell_magic.ogg` | none | `throw_flame`, `burn_tick` events [kiro_53_recommendations.md section 9] |
| Ultimate | no timeline [js/ultimate_fx.js]; not in `ULT_BUILT` [index.html:576] | n/a | n/a | everything; design = decided volley (numbers above) |
### 1b. Ghost bride (id `bride`)
| Item | In code | In assets/ | Drive list only | Missing |
|---|---|---|---|---|
| Profile, blurb | card text says every unit on the path is hurt [index.html:362], which contradicts Q6 | `assets/units/unit_bride_idle.png` | `bride_idle_v1/v2_r4` | profile, new blurb, glyph, tab |
| Portrait | none | `assets/portraits/bride_front.png` (the 2026-11-10 log calls the bride/hunchback portraits full-body [owner_feedback_log.md "Overnight art result"]; unchecked) | `portrait_front_bride_v1_q1` | possible retake |
| Poses | none | full set of 8: `bride_idle1/2`, `charge1/2/3`, `release`, `empty`, `hit` | `pose_bride_*_v1_q1` (same names, already installed) | quality unchecked |
| Effects | poison status exists, wizard-only [index.html:1553,1762] | `fx_sonic_ring`, `fx_bat_swarm`, `fx_poison_bubbles` (only `fx_poison_bubbles` is loaded [index.html:500]; the other two are not in `imgList` yet [guess]) | none | wave rule, swarm |
| Sounds | none | `spell_magic.ogg`, `ghost_real.ogg` as stand-ins [ultimate_mapping.md section 1c row 5] | none | `throw_soundwave`, `impact_soundwave` (CC0 source needed) |
| Ultimate | no timeline; `BRIDE_NORMAL_DAMAGE` 12 is wrong [js/ultimate_fx.js:22] | n/a | n/a | everything |
### 1c. Bell-tower hunchback (id `hunchback`)
| Item | In code | In assets/ | Drive list only | Missing |
|---|---|---|---|---|
| Profile, blurb | card text, "one big hit" [index.html:363] | `assets/units/unit_hunchback_idle.png` | `hunchback_idle_v1_r4/5/6/8`, `v2_r4` | profile, glyph, tab |
| Portrait | none | `assets/portraits/hunchback_front.png` (same full-body doubt as the bride) | `hunchback_portrait_v1_r10` | possible retake |
| Poses | none | full set of 8 `hunchback_*`; the log says the first set were copies of the idle [owner_feedback_log.md "Overnight art result"] | `hunchback_pose_windup/release/hit_v1_r10/r12` (redo candidates) | quality unchecked |
| Weapon / effects | `proj_axe` already bleeds [index.html:1759-1760]; no knockback code anywhere in the page [grep, no match] | `fx/sprites/fx_axe_thrown` (I take it as the flying axe [guess]); no axe in `assets/weapons/` | none | knockback, spin, boomerang |
| Sounds | none | `thwack_wood.ogg`, `bell_round.ogg` | none | `throw_axe` event (not required) |
| Ultimate | no timeline; `HUNCHBACK_NORMAL_DAMAGE` 22 is wrong [js/ultimate_fx.js:24] | n/a | n/a | everything |
Drive-only pictures are ingested by `scripts/ingest_queue.py` (tag `q1` only: `pose_*`, `portrait_front_*`, `fx_*` [scripts/ingest_queue.py:1-14]) or, for the `r`-series names, a new entry in the `JOBS` table of `scripts/key_magenta_items.py` [scripts/key_magenta_items.py, "source file on Drive -> destination" comment]. Check with `python3 -B scripts/check_pose_set.py` and `scripts/pose_similarity.py` [guess: it compares poses].
## 2. Task lists (one task = one change; "idx" = touches `index.html`, one at a time)
| ID | Size | Change | Check |
|---|---|---|---|
| S1 | S | Refresh `js/class_stats.js` and `scripts/test_class_stats.js` to the decided numbers; reaper gets burn instead of execute. No idx. | `node scripts/test_class_stats.js`, `node scripts/test_sim_balance.js` |
| S2 | S | ONLY if question 4 says yes: per-class `speedMul` in `executeThrow` and `simulateLandingX` (the AI must use the same integrator [tech.md]). idx | `node scripts/test_sim_balance.js` compares constants with the page [scripts/sim_balance.js header]; speedMul 1 must give the old landing x |
| N1 | S | idx: `HERO_PROFILES.reaper` (hp 105, dmg 23, `proj_flame`), `imgList` entries for `unit_reaper` and `proj_flame` (= `fx_flame_comet`), `HERO_BLURB`, `DOCK_GLYPH`, tab, `ART_FACES_RIGHT`, `aiClass` lists; delete the card from `COMING_HEROES`. | match starts as reaper; 5 start cards fit at 1078 and 634 px; `python3 -B scripts/release/check_asset_refs.py` missing count not higher |
| N2 | S | idx: `POSE_SETS.unit_reaper` (idle/windup/release/hit from `necro_*`), `UNARMED_ART` to `necro_empty`; refresh preload links. | `python3 -B scripts/check_pose_set.py` (reports 5 of 8, honestly), `python3 -B scripts/test_preload_links.py`, recorded run |
| N3 | M | No idx: script `(not published)` [new, guess] finds the fingertip per pose, writes `(not published)` and an overlay image. | every anchor lies inside the opaque box; owner or main line looks at the overlay |
| N4 | M | No idx: `(not published)` [new, guess] plus `(not published)`: burn 2 per round start, 3 turns, refresh not stack, never kills [kiro_53 section 4]. | `node (not published)` (300 seeded cases) |
| N5 | M | idx: flame projectile drawn as a horizontal comet, burn applied beside `applyPoison` [index.html:1762], `tickBurn` at round start [index.html:1372], reset [index.html:1410]; no ground fire. | N4 test; recorded run shows 3 ticks and no kill |
| N6 | S | idx: hide the three pip dots for reaper (fires are the pips, decided); `THROW_SOUND.proj_flame` to an existing event such as `throw_shuriken` [guess]. | recorded run |
| N7 | M | No idx: timeline `reaper_soulfire_volley` in `js/ultimate_fx.js` (3 flames, power offsets -1.2/0/+1.2, 0.15 s apart, 11.5 each, no crit, burn once); delete the scythe helper. | `node scripts/test_ultimate_fx.js` incl. 1.5x cap and preset names found in `js/particles.js` |
| N8 | M | idx: volley branch like the wizard's [index.html:1056-1061], `ULT_FX_ID.reaper` [index.html:704], pointing pose from `necro_release`/`necro_empty`, `"reaper"` added to `ULT_BUILT` last [index.html:576]. | recorded run of the whole flow; `node scripts/test_ultimate.js` |
| N9 | S | Balance: `node scripts/sim_balance.js --matches 200 --seed 7` with reaper. The sim has no burn ticks, so it checks direct damage only [kiro_53 section 6]. | every pair 40 to 60 percent [scripts/sim_balance.js header] |
| B1 | S | idx: `HERO_PROFILES.bride` (hp 75, dmg 25, `proj_soundwave` [INVENTED id]), `unit_bride` and `fx_sonic_ring` in `imgList`, new blurb, glyph, tab; remove card. | as N1 |
| B2 | S | idx: `POSE_SETS.unit_bride` (idle1, charge3 as windup, release, hit). | `check_pose_set.py` shows bride 8 of 8; recorded run |
| B3 | M | No idx: `js/sound_wave.js` [new, guess]: damage by distance from the wave centre, aimed unit only. Falloff: owner said 3 stepped bands 100/75/50 percent; v2 says linear 100 to 45 percent over 105 px. Use the owner's bands, band widths INVENTED. | `node scripts/test_sound_wave.js` (300 seeded cases) |
| B4 | M | idx: wave drawn as growing rings, hit test half-width 105 [class_stats_v2.md section 1], poison on hit beside line 1762. | B3 test; recorded run |
| B5 | S | idx: sounds from stand-ins (`spell_magic`), no new file. | recorded run |
| B6 | M | No idx: timeline `bride_bat_swarm` (sprite `fx_bat_swarm`; 32.5 per enemy; trigger = hit inside the 40 px centre, INVENTED [kiro_74 provisional]); fix the 12 constant. | `node scripts/test_ultimate_fx.js` |
| B7 | M | idx: swarm wiring, enemies only, not blockable, `"bride"` into `ULT_BUILT`. 1 v 1 total 57.5. | recorded run |
| B8 | S | Balance sim as N9. | as N9 |
| H1 | S | idx: `HERO_PROFILES.hunchback` (hp 110, dmg 21, `proj_axe`), `unit_hunchback`, `proj_axe` = `fx_axe_thrown`, glyph, tab; remove card. | as N1 |
| H2 | S | Check poses first with `check_pose_set.py` and `pose_similarity.py`; if they are copies of the idle, add the r10/r12 Drive files to the key script. Then idx: `POSE_SETS.unit_hunchback`. | scripts exit 0; recorded run |
| H3 | M | No idx: `js/knockback.js` [new, guess]: 50 px on a direct, non-fatal hit; clamp to zones 160-760 / 1160-1760; none on fence, ground or shield [class_stats_v2.md section 3]. | `node scripts/test_knockback.js` |
| H4 | M | idx: axe spins 2 turns a second, knockback applied after hit-stop; bleed already works. | H3 test; recorded run |
| H5 | S | idx: sounds from `throw_spear` / `impact_unit_heavy` [guess]. | recorded run |
| H6 | L | No idx: `js/boomerang.js` [new, guess]: pierce, return to the first unit only if the last was hit, 31.5, return speed 1400 px/s INVENTED, not blockable; property tests; timeline `hunchback_boomerang`. | `node scripts/test_boomerang.js`, `node scripts/test_ultimate_fx.js` |
| H7 | L | idx: boomerang in the projectile loop, `"hunchback"` into `ULT_BUILT`; 1 v 1 hits the only enemy twice (21 + 31.5). | recorded run |
| H8 | S | Balance sim as N9. | as N9 |
Statuses, `ULT_BUILT` and all numbers are the decided ones above; the sky shield, wind and fence code stay as they are.
## 3. Order, honest estimate, new pictures
1. S1, N3, N4 in parallel (no idx). 2. N1, N2, N5, N6: first playable extra hero. Why first: five poses, idle, flame sprites, purple fire and the circling-fire code exist [index.html:694,2494], speed stays 1.0, and no new hit rule is needed.
3. N7, N8 (necromancer ultimate). 4. B1 to B5 (bride; no new art required [guess]), then B6, B7. 5. H1 to H5, then H6, H7 (largest code, cut first).
Estimate [guess]: necromancer 9 tasks (5 idx), bride 8 (4 idx), hunchback 8 (4 idx), shared 1 or 2. That is 13 idx tasks in one lane that B04, B06 and B09 also use [WORK_QUEUE_20261115.md B04, B06, B09]. At about one idx task a day, two heroes finish before the freeze (12-02 06:00), the third only in normal-attack form.
New pictures from the owner (Colab/Qwen; code must not draw art [team_plan.md section 4]): `necro_front` (stopgap: emoji, already the fallback), a pointing-hand ultimate pose (replace with `necro_release`), `charge2` and `idle2` for the necromancer (not needed: the page uses one windup frame [index.html:2151-2154]), possible portrait retakes for bride and hunchback, hunchback poses only if H2 finds copies. Nothing else.
## 4. Questions for the owner (recommendation first)
1. Necromancer is the reaper, one class, no separate reaper? Yes (already logged [owner_feedback_log.md:136]); confirm so the docs stop listing both.
2. Order necromancer, bride, hunchback? Yes.
3. Which of the three are firm before the 12-02 freeze? Necromancer and bride firm; hunchback normal attack best effort, boomerang cut first.
4. Per-class launch speed 0.9 and 0.85? No, keep 1.0: v2 says flight time stays equal and the hit-rate gain is 11 to 18 percent, and it saves S2 and an AI change. Yes means S2 is added.
5. Bride falloff: the owner's three stepped bands (100/75/50) or v2's linear 105 px? Stepped bands.
6. Do rows 5 to 7 of `docs/ultimate_mapping.md` get a "superseded" note? Yes (the file is the owner's rule source only on instruction [structure.md]).
7. New sounds (`throw_flame`, `throw_axe`, `throw_soundwave`) or stand-ins? Stand-ins until B08 picks a source.
8. Retake bride and hunchback portraits on Colab? Only if the start-screen cards look wrong after B1 and H1.
