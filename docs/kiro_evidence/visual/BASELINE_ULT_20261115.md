# Visual baseline of the CURRENT ultimate (before ultimates-v2 is wired), 2026-11-15

Made by the main line in the right-hand browser (viewport 1280 x 720, page `http://localhost:8080/index.html`, hero skeleton, start screen then "開始戰鬥"). Pictures are working evidence for Kiro and the main line to compare against after the new effects are wired; a picture cannot show sound or smoothness.

How it was triggered (script, no full match): `energy.player = 3; ultArmed.player = true; executeThrow("player", 78)`.

Facts read from the page right after the throw (code, not eyes):
- hero `skeleton`; `ULT_BUILT` = bat, skeleton, wizard; `ultUsed` = player 1, ai 0; `ultArmed.player` = false; `projectiles.length` = 3 (the one javelin plus two extra, as in the built code); the turn passes to the opponent ("對手回合").

What the two frames show (main line's reading, `ult_baseline_skeleton_frame1_20261115.jpg`, `..._frame2_...jpg`):
- Frame 1: gold floating text above the skeleton "大招：三連標槍"; a blue glow orb at the spear tip; top bar, timer, wind readout, health bars and the bottom dock are all visible and not covered by effects; the wind gauge text sits in the top bar.
- Frame 2: the three javelin paths arc to the right; impact sparks and an orange burst near the wizard on the right; nothing from the effect layer overlaps the dock or the top bar.
- Not judged: speed of the animation, sound, how it looks on other viewport sizes.

## After wiring `js/ultimate_fx.js` into the page (main line, 2026-11-15 ~17:30)
Picture: `ult_after_wiring_skeleton_20261115.jpg` (same trigger, same viewport class). Facts read by script from the particle system after the throw:
- Launch: the system received `weapon_charge_aura`, `face_glow_skeleton`, `weapon_trail_spear` x3 from the module, then the page's own trail, `weapon_rune_halo`, `muzzle_flash`.
- Impact: `sprite_ghostfire` x3 (one per javelin), `impact_burst`, `hit_sparks` and the page's own burst; the opponent's turn followed normally; `ultUsed` player = 1.
- Combat numbers: unchanged (the helper never reads or writes damage; hp moved as before). HUD, top bar and dock are not covered (picture).
- Console: only the known 404 for missing assets listed by `check_asset_refs.py`; no script error.
- Not checked: wizard and bat ultimates visually (code path is the same helper; tests pass), smoothness, sound.
