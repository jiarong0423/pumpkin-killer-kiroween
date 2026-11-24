# Asset gap report

Compares `docs/object_inventory.md` (98 objects) with `assets/` (units, env, fx, sprites, colab_inputs, the two
`manifest.json` files) and `docs/`. `(not published)` does not exist yet (the Colab layered art has not landed).

Limits: I could not run scripts, so sizes and alpha were judged by looking at the images. Anything about alpha edges
needs a quick script check before the rework list is final.

Status counts: EXISTS_OK 7, EXISTS_NEEDS_REWORK 26, MISSING 65.

## Findings on the known problems

1. **Held weapons and hands.** The sprite sheets (`assets/sprites`, 64 sheets, 256 px cells, 12 fps) are the whole
   unit baked into one image, so the arm cannot swing on its own. The "unarmed" cutouts are worse than the
   originals: `unit_bat_unarmed.png` still has a dagger fragment at the hand, `unit_skeleton_unarmed.png` has a cut
   spear stump and a white patch under the chin, and there is no unarmed version of the wizard or knight. The
   painted weapons in `unit_*_raw.png` are the good ones. Plan: keep those painted weapons as their own layers (cut
   out, do not redraw), and generate only a clean body and empty-hand arm poses (hold, charge, release,
   follow-through) with a shoulder pivot.
2. **Floating shield.** Nothing exists. The only input is `ref_bar_from_video.png`, a small blurry blue pill with a
   white top highlight. One image-edit restyle gives the base bar; placing, blocking, breaking and path markers are
   drawn in code.
3. **Knight has no throwable.** `proj_pumpkin.png` exists as a flying projectile, but the knight art has no pumpkin
   in the hand, so the throw has nothing leaving the hand. Needs `held_knight_pumpkin` and an arm pose set that holds it.
4. Other problems found: a team ring is baked into the sheets, at least one sheet clips the first frames at the
   cell edge, the thrown dagger looks different from the held one, `bg_graveyard.png` has a different style from
   the mockup, and the ghost and crate files do not match the mockup (one rope and lantern; broken burning crate).

## Table

| Object | Status | Why | Fill with |
|---|---|---|---|
| char_p1_bat | EXISTS_NEEDS_REWORK | Baked sheets, no separate arm, ring baked in | Colab image-edit (layers) |
| char_p2_wizard | EXISTS_NEEDS_REWORK | Same | Colab image-edit (layers) |
| char_p3_skeleton | EXISTS_NEEDS_REWORK | Same | Colab image-edit (layers) |
| char_p4_knight | EXISTS_NEEDS_REWORK | Same; first frames clipped in one sheet | Colab image-edit (layers) |
| char_aA_knight | EXISTS_NEEDS_REWORK | Shares player art | Re-use player layers |
| char_aB_skeleton | EXISTS_NEEDS_REWORK | Shares player art | Re-use player layers |
| char_aC_wizard | EXISTS_NEEDS_REWORK | Shares player art | Re-use player layers |
| char_aD_bat | EXISTS_NEEDS_REWORK | Shares player art | Re-use player layers |
| layer_body_bat | EXISTS_NEEDS_REWORK | `unit_bat_unarmed.png` has dagger remnant at the hand | Colab image-edit from `unit_bat_raw.png` |
| layer_body_wizard | MISSING | No unarmed version | Colab image-edit from `unit_wizard_raw.png` |
| layer_body_skeleton | EXISTS_NEEDS_REWORK | `unit_skeleton_unarmed.png` has spear stump and white patch | Colab image-edit from `unit_skeleton_raw.png` |
| layer_body_knight | MISSING | No unarmed version | Colab image-edit from `unit_knight_raw.png` |
| marker_p1, marker_p2, marker_p3, marker_p4 (4 objects) | MISSING | Not in repo | Code-drawn |
| marker_aA, marker_aB, marker_aC, marker_aD (4 objects) | MISSING | Not in repo | Code-drawn |
| arm_bat | MISSING | No separate arm art | Colab image-edit |
| arm_wizard | MISSING | Same | Colab image-edit |
| arm_skeleton | MISSING | Same | Colab image-edit |
| arm_knight | MISSING | Same | Colab image-edit |
| held_bat_dagger | EXISTS_NEEDS_REWORK | Good painted dagger, but baked into the raw body | Re-use: cut out of `unit_bat_raw.png` |
| held_wizard_cannon | EXISTS_NEEDS_REWORK | Good painted cannon, baked in; hidden hat parts behind it | Re-use: cut out of `unit_wizard_raw.png` |
| held_skeleton_spear | EXISTS_NEEDS_REWORK | Good painted spear, baked in | Re-use: cut out of `unit_skeleton_raw.png` |
| held_knight_pumpkin | MISSING | Knight has no throwable in hand | Colab image-edit (reference `proj_pumpkin.png`) |
| held_knight_shield | EXISTS_NEEDS_REWORK | Painted shield baked in; no raised-arm pose | Re-use cutout + one Colab image-edit for the raised pose |
| proj_bat_dagger | EXISTS_NEEDS_REWORK | `assets/env/proj_dagger.png` exists but looks unlike the held dagger | Colab image-edit (match held dagger) |
| proj_wizard_cannonball | MISSING | No cannonball | Text-to-image |
| proj_skeleton_spear | EXISTS_OK | `assets/env/proj_spear.png`, close to the held spear | Re-use |
| proj_knight_pumpkin | EXISTS_OK | `assets/env/proj_pumpkin.png` | Re-use |
| proj_special_weapons | MISSING | Weapons undefined | Decide list first; then text-to-image |
| shield_bar | MISSING | Only the small reference exists | Colab image-edit from `ref_bar_from_video.png` |
| shield_path_markers | MISSING | None | Code-drawn |
| shield_break_fx | MISSING | None | Code-drawn |
| shield_status_pips | MISSING | None | Code-drawn |
| env_sky_moon | EXISTS_NEEDS_REWORK | `bg_graveyard.png` is bright flat-vector blue, one flattened plate | Colab image-edit (mockup as reference); placeholder until then |
| env_castle | EXISTS_NEEDS_REWORK | Baked in the same plate | Same image as sky and moon |
| env_mid_graveyard | EXISTS_NEEDS_REWORK | Baked in; has its own cracked floor that clashes with the ground | Colab image-edit |
| env_tree_frame | EXISTS_NEEDS_REWORK | Baked in | Colab image-edit |
| env_bats_flying | EXISTS_NEEDS_REWORK | Bats are baked into the plate | Re-use: cut out of `bg_graveyard.png` |
| env_ground_band | EXISTS_NEEDS_REWORK | `ground_strip.png` is a floating island with props at both ends | Colab image-edit |
| env_foreground_props | MISSING | Only baked bits in the bg | Text-to-image |
| platform_corner_blue | EXISTS_NEEDS_REWORK | `platform_coffin_blue.png` is edge-on, no rune eye, pale mist | Colab image-edit from the purple one |
| platform_corner_purple | EXISTS_OK | `platform_coffin_purple.png` is close to the mockup | Re-use |
| platform_plank | EXISTS_NEEDS_REWORK | `platform_skull_plank.png` is a 3/4 block, mockup is a flat plank | Colab image-edit |
| env_wisps_under_plank | MISSING | None | Code-drawn particles |
| env_ghost_carrier | EXISTS_NEEDS_REWORK | `ghost_lantern.png` is the right character but has one rope and a lantern | Colab image-edit (arms up, no lantern) |
| env_crate_hanging | EXISTS_NEEDS_REWORK | `crate_fire.png` is broken and burning | Colab image-edit |
| env_fence_center | MISSING | Prototype draws it in code only | Text-to-image (4 states) |
| fx_muzzle_flash | EXISTS_OK | `fx_muzzle_flash_sheet.png`, 8 frames | Re-use |
| fx_impact_burst | EXISTS_OK | `fx_impact_burst_sheet.png`, 14 frames | Re-use |
| fx_hit_spark | EXISTS_OK | `fx_hit_spark_sheet.png`, 8 frames | Re-use |
| fx_charge_glow | EXISTS_OK | `fx_charge_glow_sheet.png`, 16 frames; check alpha | Re-use |
| fx_landing_ring | EXISTS_NEEDS_REWORK | `ui_target_ring_sheet.png` is a thick perspective disc, mockup is a thin flat ring with a beam | Code-drawn |
| fx_aim_arc | MISSING | None | Code-drawn |
| fx_cannon_smoke | MISSING | None | Code-drawn |
| fx_dust_puff | MISSING | None | Code-drawn |
| fx_projectile_trail | MISSING | None | Code-drawn |
| fx_damage_number | MISSING | None | Code-drawn |
| fx_selection_ring | MISSING | Only a baked ring in sheets | Code-drawn |
| fx_candle_flame | MISSING | None | Code-drawn |
| fx_spirit_flame | MISSING | None | Code-drawn |
| fx_fence_debris | MISSING | None | Code-drawn |
| fx_death_wisps | MISSING | None | Code-drawn |
| fx_crate_open | MISSING | None | Code-drawn |
| ui_title_logo | MISSING | None | Colab image-edit from a mockup crop; fallback code text |
| ui_topbar_frame | MISSING | `docs/gameplay_mockup.svg` and `layout_plan.svg` are older layouts | Code-drawn |
| ui_top_players_panel | MISSING | None | Code-drawn |
| ui_top_round_timer | MISSING | None | Code-drawn |
| ui_top_wind | MISSING | None | Code-drawn |
| ui_top_agents_panel | MISSING | None | Code-drawn |
| ui_unit_hp_bar | MISSING | None | Code-drawn |
| ui_bottom_bar_frame | MISSING | Prototype has an HTML dock with 4 skills, not the target layout | Code-drawn |
| ui_portrait_frame | MISSING | None | Code-drawn |
| ui_unit_name_hp | MISSING | None | Code-drawn |
| ui_btn_throw | MISSING | None | Code-drawn |
| ui_btn_move | MISSING | None | Code-drawn |
| ui_btn_defend | MISSING | None | Code-drawn |
| ui_action_icons | MISSING | None | Text-to-image (one sheet) or code |
| ui_angle_selector | MISSING | None | Code-drawn |
| ui_power_bar | MISSING | None | Code-drawn |
| ui_ammo_slot | MISSING | None | Code-drawn |
| ui_special_slot | MISSING | None | Code-drawn |
| ui_lock_button | MISSING | None | Code-drawn |
| ui_phase_banner | MISSING | Not in mockup | Code-drawn (if wanted) |
| ui_game_over | MISSING | Not in mockup | Code-drawn (if wanted) |
| cutin_portrait_bat | MISSING | No portraits at all | Colab image-edit, 4 states |
| cutin_portrait_wizard | MISSING | Same; mockup shows the target look | Colab image-edit, 4 states |
| cutin_portrait_skeleton | MISSING | Same | Colab image-edit, 4 states |
| cutin_portrait_knight | MISSING | Same | Colab image-edit, 4 states |
| cutin_frame | MISSING | None | Code-drawn |
| cutin_speedlines | MISSING | None | Code-drawn |
| cutin_release_flash | MISSING | None | Code-drawn |
| cutin_name_banner | MISSING | None | Code-drawn |
| cutin_hit_overlay | MISSING | None | Code-drawn |

## Prioritised recommendations

### Generate first (biggest visual gain)

1. **Layered unit art, 20 images.** 4 clean body layers, 14 empty-hand arm poses (bat 4, wizard 2, skeleton 4,
   knight 4), 1 raised-shield pose, 1 held pumpkin for the knight. Characters are what the player watches every
   turn, and this removes the stiff baked-sheet look and the weapon problem. Cut the three painted weapons and the
   shield out of the raw art by hand (0 images).
2. **Throw cut-in portraits, 16 images.** 4 classes x (neutral, charging, throwing, hit). The mockup bottom-left
   panel and the owner's "dramatic throw" request both depend on them, and the cut-in is cheap in code once the art exists.
3. **Floating shield bar, 1 image**, plus 1 restyled thrown dagger and 1 cannonball (text-to-image). Without the bar
   the knight class cannot be played as designed.

### Second wave (scene quality)

4. Background plates (4 image-edits): sky + moon + castle, mid graveyard, corner trees, ground band. Foreground
   props (1 text-to-image). Until then keep `bg_graveyard.png` and `ground_strip.png` as placeholders.
5. Platforms and airdrops (4 image-edits): blue corner slab, skull plank, ghost, hanging crate.
6. Fence, 4 states (4 text-to-image). The prototype already draws a code fence, so this is polish.

### Third wave

7. Logo (1 image-edit, code fallback) and the action icon sheet (1 text-to-image).

### Can stay as is

`proj_spear`, `proj_pumpkin`, `platform_coffin_purple`, and the four effect sheets (`fx_muzzle_flash`,
`fx_impact_burst`, `fx_hit_spark`, `fx_charge_glow`). Enemy-team art is the same set as the player team, so there is
no second generation pass for agents.

### Cut or retire

- The 64 baked unit sheets in `assets/sprites` once the layered art lands (keep until then), and the red/white
  duplicate set: one art set, mirrored and tinted or ringed in code.
- `unit_bat_unarmed.png` and `unit_skeleton_unarmed.png` after the clean body layers replace them.
- `ghost_lantern.png` as a whole (keep only the ghost cut-out) and `crate_fire.png` in its current broken form.
- `ui_target_ring` sheet as the landing ring (keep only as an impact flourish if wanted).
- Special weapons (`proj_special_weapons`), phase banner and game-over art until the owner confirms the rules.
- Gameplay mockup extras that are not in the rules: death tombstone and hit numbers, until confirmed.

## Colab image estimate

| Wave | Image-edit | Text-to-image | Total |
|---|---|---|---|
| 1. Units 20, portraits 16, shield bar 1, dagger restyle 1, cannonball 1 | 38 | 1 | 39 |
| 2. Background 4 + foreground 1, platforms and airdrop 4, fence 4 | 8 | 5 | 13 |
| 3. Logo 1, icon sheet 1 | 1 | 1 | 2 |
| **Total deliverables** | **47** | **7** | **54** |

At roughly two tries per accepted image that is about 100 to 130 Colab runs. Wave 1 alone is 39 deliverables (about
80 runs). Special weapons would add roughly 4 to 6 images once defined.
