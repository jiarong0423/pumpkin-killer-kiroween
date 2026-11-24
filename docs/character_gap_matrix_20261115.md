# Character and image gap matrix, 2026-11-15 (Kiro task 137 and its addendum)
Facts come from `ls` of `assets/`, `colab/`, from `python3 -B scripts/release/check_asset_refs.py` (121 refs, 7 missing) and from the three job files. I did not judge picture quality. Pose files are in `assets/poses/` (stem only below). `(legacy)` = the file the pose checker accepts under an old name (`scripts/check_pose_set.py`). `job` = the job id and its file: `CH` = `colab/jobs_characters_20261115.json`, `HAG` = `colab/jobs_apple_hag_20261115.json`, `MISS` = `colab/jobs_missing_20261115.json`, `SC` = `colab/jobs_scenes_20261115.json`. `new` = job added by task 137. `code` = made by code, no picture needed.

## 1. Heroes (pose frames, portrait, projectile, ultimate effect, status icon)
| Hero | idle1 | idle2 | charge1 | charge2 | charge3 | release | empty | hit |
|---|---|---|---|---|---|---|---|---|
| skeleton | skeleton_idle1 | skeleton_idle2 | skeleton_charge1 | skel_windup (legacy) | skeleton_charge3 | skel_release (legacy) | skeleton_empty | skel_hit (legacy) |
| wizard | wizard_idle1 | wizard_idle2 | wizard_charge1 | wizard_charge2 | wizard_charge3 | **missing**, job `wizard_release` (CH, new) | wizard_empty | wizard_hit |
| bat | bat_idle1 | bat_idle2 | bat_draw (legacy) | bat_windup (legacy) | bat_charge3 | bat_release | bat_empty | bat_hit |
| knight | knight_idle1 | knight_idle2 | knight_charge1 | knight_charge2 | knight_charge3 | knight_release | knight_empty | knight_hit |
| necromancer (`reaper`) | reaper_idle1 | reaper_idle2 (job `necro_idle2` in CH also exists) | reaper_charge1 | necro_windup (legacy); job `necro_charge2` (CH) | reaper_charge3 | necro_release | necro_empty | necro_hit |
| ghost bride | bride_idle1 | bride_idle2 | bride_charge1 | bride_charge2 | bride_charge3 | bride_release | bride_empty | bride_hit |
| hunchback | hunchback_idle1 | hunchback_idle2 | hunchback_charge1 | hunchback_charge2 | hunchback_charge3 | hunchback_release | hunchback_empty | hunchback_hit |
| Apple Hag (`hag`) | job `hag_idle1` (HAG) | job `hag_idle2` | job `hag_charge1` | job `hag_charge2` | job `hag_charge3` | job `hag_release` | job `hag_empty` | job `hag_hit` |

| Hero | portrait | projectile | ultimate effect | status icon |
|---|---|---|---|---|
| skeleton | `assets/portraits/skeleton_front.png`; the page uses `assets/ui/portrait_skeleton.png` | `assets/weapons/proj_spear_colab.png` | code (ghost spears) | frost curse: **missing**, job `ui_frost_curse` (CH, new); bleed: **missing**, job `ui_bleed_drop` (CH, new) |
| wizard | `assets/portraits/wizard_front.png`; page: `assets/ui/portrait_wizard.png` | `assets/env/proj_pumpkin.png` (the page weapon id is `cannonball`; I did not check which picture it draws) | code (blast ring) | poison: effect `assets/fx/sprites/fx_poison_bubbles.png` present; icon **missing**, job `ui_poison_bubble` (CH, new) |
| bat | page: `assets/ui/portrait_bat.png`; `assets/portraits/bat_front.png` does not exist | `assets/weapons/shuriken.png` | `assets/weapons/shuriken.png` (reused) | slow chain: `assets/fx/sprites/fx_feet_chain.png` **missing**, job `fx_feet_chain` (MISS) |
| knight | `assets/portraits/knight_front.png`; page: `assets/ui/portrait_knight.png` | `assets/weapons/small_shield.png` | code (shield chain) | none (the knight inflicts no status) |
| necromancer | `assets/portraits/reaper_front.png` (page uses it); retake job `necro_front` (CH) | `assets/fx/sprites/fx_flame_comet.png`, `fx_flame_hand_purple.png` | `assets/fx/sprites/fx_ghostfire_purple.png`; pointing pose: job `necro_ult_point` (CH) | burn: **missing**, job `ui_burn_flame` (CH, new) |
| ghost bride | `assets/portraits/bride_front.png`; retake job `bride_front` (CH) | `assets/fx/sprites/fx_sonic_ring.png` | `assets/fx/sprites/fx_bat_swarm.png` | undecided (open owner question: does her ring poison?); `ui_poison_bubble` would serve |
| hunchback | `assets/portraits/hunchback_front.png`; retake job `hunchback_front` (CH) | `assets/fx/sprites/fx_axe_thrown.png` | `assets/fx/sprites/fx_axe_thrown.png` (reused for the boomerang) | bleed: job `ui_bleed_drop` (CH, new, shared with the skeleton) |
| Apple Hag | job `hag_front` (HAG) | job `proj_poison_apple` (HAG) | jobs `fx_apple_rain`, `fx_apple_rain_heal`, `fx_black_smoke` (HAG) | job `ui_bitten_apple` (HAG) |

Not gaps, by choice: optional ultimate pictures named in `docs/ultimate_mapping.md` (`ult_spectral_spear`, `ult_ricochet_shield`, `fx_shockwave_ring`, `ult_pip_socket`). The `ultimates-v2` spec builds those effects with code first. The page already draws status badges with emoji text, so the four icon jobs are optional polish, not blockers. All hero frames count as present by file name only.

## 2. Image gaps that are not heroes
| Gap | Evidence | Job |
|---|---|---|
| `assets/env/bg_belltower.png` | `check_asset_refs.py` MISSING (page `SCENES`) | `bg_belltower` (MISS) |
| `(not published)` | MISSING | `bg_pumpkin_field` (MISS) |
| `assets/fx/sprites/fx_feet_chain.png` | MISSING (page `imgList` `fx_chain`) | `fx_feet_chain` (MISS) |
| `assets/units/unit_knight_unarmed.png` | MISSING (`UNARMED_ART`) | `unit_knight_unarmed` (MISS) |
| scenes `ruined church`, `abandoned school` (two takes each) | not yet in the page | `bg_ruined_church`, `bg_ruined_church_b`, `bg_abandoned_school`, `bg_abandoned_school_b` (SC) |
| necromancer finger-point pose | no file | `necro_ult_point` (CH) |
| any other fx or ui picture the page names | none: all other literal refs in `index.html`, `js/` and `css/` exist | - |
`check_asset_refs.py` reads literal `(not published)` strings only. A path built in code from pieces is not covered. Not page gaps: `ghoststar_blow`, `ghoststar_blow_hard` (the page's `fx_ghost_blow.png` and `fx_ghost_blow_hard.png` exist now) and `coin_pumpkin_head`, `coin_pumpkin_tail` (no literal page reference). They stay in `MISS` as optional.

## 3. Audio refs the page needs (not Colab picture jobs)
| Path | Status |
|---|---|
| `(not published)` | MISSING; audio job `move_step` exists in `colab/audio_jobs.json` |
| `(not published)` | MISSING; audio job `item_pickup` exists in `colab/audio_jobs.json` |
| `(not published)` | MISSING; no audio job. The CC0 search is task 6 of `ultimates-v2`; the synthesized chime plays until then |
Run these two with `colab/audio_job.py`, a separate notebook cell. They are not in the picture run order.
