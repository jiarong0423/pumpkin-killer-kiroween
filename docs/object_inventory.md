# Object detail inventory

Sources read: `(not published)` (1568 x 882 image, scaled x1.2245 to 1920 x 1080), `docs/game_mode.md`,
`docs/animation_plan.md`, `assets/units`, `assets/env`, `assets/fx`, `assets/sprites`, `(not published)`, the
manifest files, and the constants in `index.html` (canvas 1920 x 1080, GROUND_Y 860, fence at x 960, 130 x 250).
The same data is in `docs/object_inventory.json` (98 objects).

Sizes marked "about" come from measuring the mockup by eye, so they are +/- 15 percent. No projectile is visible
in the mockup, so projectile sizes are estimates.

Limits of this pass: I could not run scripts (shell was denied), so file dimensions are read from the viewer, not
measured, and I could not confirm the alpha channel of the env and fx PNGs (some show a pale halo on white).

## Legend

- **FL**: art faces LEFT, mirrored in code for the player team (players stand on the left and face right). The
  agent team uses the art unmirrored.
- **RR**: projectile art points RIGHT (direction of travel) and is rotated by code to follow the velocity. No
  team mirror.
- **NF**: no facing. Never mirrored (text and symmetric items).
- **Exists**: yes = usable file in repo; partial = a file exists but is baked, wrong or incomplete; no = not in repo.
- **Method**: IE = Colab image-edit from a reference; T2I = text-to-image; CODE = draw in code (UI/effects only);
  REUSE = use existing file or cut from existing art.

---

## 1. Characters (20)

Four classes x two teams = 8 units, the 4 body layers needed for a real arm swing, and 8 number/letter markers.
Player units stand left and are numbered 1-4 (bat, wizard, skeleton, knight); agent units stand right and are
lettered A-D (knight, skeleton, wizard, bat), as in the mockup. HP: bat 90, wizard 85, skeleton 100, knight 120.

States for every unit (from `animation_plan.md`, 12 fps, 88 frames): idle 12 loop, move_forward 12 loop,
move_back 12 loop, arm_charge 10, arm_throw 10, hit_react 10, defend 8, die 14.

| id | Looks | Size @1920 | States | Layers | Facing | Exists / path | Method |
|---|---|---|---|---|---|---|---|
| char_p1_bat | Small black bat-eared cat, big pointed ears with orange insides, grumpy eyes, black outfit with belt and short cloak, large bat wing behind, silver dagger low in the front hand, orange rim light | about 116 x 135 | 8 states above | body + arm + dagger | FL | partial: `assets/units/unit_bat.png`, `unit_bat_raw.png`, `unit_bat_unarmed.png`, `(not published)` | IE |
| char_p2_wizard | Pumpkin-headed gunner: glowing carved face, tall crooked purple hat with brass buckle, purple robe with gold trim, black boots, brass cannon with flared muzzle on the shoulder | about 171 x 165 | 8 states | body + cannon-with-arm | FL | partial: `assets/units/unit_wizard.png`, `unit_wizard_raw.png`, `(not published)` | IE |
| char_p3_skeleton | Cream skeleton, oversized round skull, cyan flame eyes, dark armour scraps on shoulder and forearm, hunched, long wooden spear with grey head on the shoulder | about 147 x 129 | 8 states | body + arm + spear | FL | partial: `assets/units/unit_skeleton.png`, `unit_skeleton_raw.png`, `unit_skeleton_unarmed.png`, `(not published)` | IE |
| char_p4_knight | Pumpkin head with curled green stem and glowing angry face, black plate armour, brown belt, dark trailing cloak, tall dark-wood shield with pale cross (coffin-shaped in mockup) | about 196 x 153 | 8 states | body + shield arm + throwing arm + pumpkin | FL | partial: `assets/units/unit_knight.png`, `unit_knight_raw.png`, `assets/sprites/unit_knight_*` | IE |
| char_aA_knight | Same design as char_p4_knight (agent A, 120/120) | about 196 x 153 | same | same | FL, unmirrored | partial, same files | REUSE |
| char_aB_skeleton | Same design as char_p3_skeleton (agent B, 100/100) | about 147 x 129 | same | same | FL, unmirrored | partial, same files | REUSE |
| char_aC_wizard | Same design as char_p2_wizard (agent C, 85/85) | about 171 x 165 | same | same | FL, unmirrored | partial, same files | REUSE |
| char_aD_bat | Same design as char_p1_bat (agent D, 90/90) | about 116 x 135 | same | same | FL, unmirrored | partial, same files | REUSE |
| layer_body_bat | Bat-cat without the dagger arm; clean shoulder socket | about 116 x 135, author at 1024 | 1 base image, rest by code | body | FL | partial: `assets/units/unit_bat_unarmed.png` | IE |
| layer_body_wizard | Pumpkin head, hat, robe, legs without cannon and raised arm | about 150 x 165 | 1 base | body | FL | no | IE |
| layer_body_skeleton | Skeleton without the spear arm | about 147 x 129 | 1 base | body | FL | partial: `assets/units/unit_skeleton_unarmed.png` | IE |
| layer_body_knight | Knight without both arms and shield | about 160 x 153 | 1 base | body | FL | no | IE |
| marker_p1 .. marker_p4 | Cyan glowing diamond with white digit 1, 2, 3, 4 | about 37 x 37 | normal, active (pulse 8 loop), dead (grey) | single | NF | no | CODE |
| marker_aA .. marker_aD | Purple glowing diamond with white letter A, B, C, D | about 37 x 37 | normal, active, dead | single | NF | no | CODE |

UNSURE (characters):
- Which sprite team (red or white) is the player team, and should both teams keep natural colours as in the mockup
  with only marker and ring differing?
- The existing sheets bake a team-coloured ring under the feet (seen in `unit_knight_red_arm_throw.png`, white
  sheets not inspected). Remove it and draw the ring in code?
- The first frames of that sheet are clipped at the left of the 256 px cell (shield cut off).
- Defend for classes without a shield: what does it look like?
- Skeleton weapon: the mockup shows a short stick with a round white end, `game_mode.md` says a long spear.
- Does a tombstone remain after death? Hit numbers popping up?
- `unit_bat_unarmed.png` has a dagger fragment at the hand and `unit_skeleton_unarmed.png` a cut spear stump and a
  white patch under the chin, so neither is clean enough.
- Agent markers: diamond over the unit but hexagon pip in the top bar. Intended?

---

## 2. Held weapons and arms (9)

Arm poses are empty-hand layers with a shoulder pivot. The weapon is a separate layer, taken from the ORIGINAL
painted art (`assets/units/unit_*_raw.png`), not redrawn. Planned poses per arm: hold, charge (pulled back), release
(forward), follow-through. The weapon hides at release and fades back in after the 0.55 s resupply.

| id | Looks | Size @1920 | States / poses | Layers | Facing | Exists / path | Method |
|---|---|---|---|---|---|---|---|
| arm_bat | Black sleeve and clawed glove, round shoulder joint | about 60 x 50 | 4 poses | arm | FL | no | IE |
| arm_wizard | Purple sleeve, gold cuff, dark glove steadying the cannon | about 55 x 60 | 2 poses: carry, recoil-brace | arm | FL | no | IE |
| arm_skeleton | Bone arm with dark armour scrap on the forearm, open bony fingers | about 60 x 50 | 4 poses | arm | FL | no | IE |
| arm_knight | Black pauldron, armoured arm and gauntlet, hand open for a pumpkin | about 70 x 60 | 4 poses | arm | FL | no | IE |
| held_bat_dagger | Short straight silver blade, dark crossguard, round pommel; original painted dagger | about 60 x 25 | static, hidden from release to resupply | weapon | FL | partial: `assets/units/unit_bat_raw.png` | REUSE (cut out) |
| held_wizard_cannon | Heavy brass tube with ring bands, dark bore, flared muzzle; original painted cannon | about 95 x 40 | rotates 25..80 degrees, recoil 8 px over 6 frames | weapon (shoulder pivot, muzzle anchor) | FL | partial: `assets/units/unit_wizard_raw.png` | REUSE (cut out) |
| held_skeleton_spear | Long brown shaft, grey butt cap, big grey head with metal collars; original painted spear | about 190 x 45 | static, arcs over the shoulder at throw | weapon | FL | partial: `assets/units/unit_skeleton_raw.png` | REUSE (cut out) |
| held_knight_pumpkin | Small orange jack-o'-lantern with glowing face and short green stem in the gauntlet. Not in the unit art | about 40 x 38 | static, hidden after throw | weapon | FL | no (`assets/env/proj_pumpkin.png` can serve as reference) | IE |
| held_knight_shield | Tall pointed dark-wood shield, pale cream cross, wood grain | about 55 x 110 | down at side; raised in front (defend, 8 frames); dent flash on block | shield + shield arm | FL | partial: `assets/units/unit_knight_raw.png` | REUSE + IE (raised-arm pose) |

UNSURE: one-handed or two-handed throw; single or two hands on the cannon; whether the cannon is carried on the
shoulder (unit art) or held forward at chest height (mockup); in the unit art the spear head points right while
the skull looks left, so the throw direction needs the head to lead; whether the skeleton arm detaches on hit/die;
whether the knight hand shield is the same object as the floating shield.

---

## 3. Projectiles (5)

| id | Looks | Size @1920 | States | Layers | Facing | Exists / path | Method |
|---|---|---|---|---|---|---|---|
| proj_bat_dagger | Silver blade, dark violet grip, cyan gem, purple flame along the blade | about 90 x 30 | 1 image, follows velocity | single | RR | yes: `assets/env/proj_dagger.png` | IE (match held plain dagger) |
| proj_wizard_cannonball | Round dark iron ball with orange rim and short smoke tail | about 40 x 40 | 1 image + code smoke | single | NF (round) | no | T2I |
| proj_skeleton_spear | Long brown shaft with wrapped grips, grey head with cyan glow | about 180 x 24 | 1 image, follows velocity | single | RR | yes: `assets/env/proj_spear.png` | REUSE |
| proj_knight_pumpkin | Orange jack-o'-lantern, glowing carved face, dark teal rim, flame trail | about 70 x 45 | 1 image, rotating | single | RR | yes: `assets/env/proj_pumpkin.png` | REUSE |
| proj_special_weapons | Not visible (special slot is an empty dashed square) | unknown | unknown | unknown | rotates by velocity | no | T2I later |

UNSURE: projectile sizes; thrown dagger differs from the held one (purple flame, cyan gems); cannonball (rules) or
pumpkin (mockup ammo icon) for the wizard; which special weapons exist and how many.

---

## 4. Floating shield (4)

| id | Looks | Size @1920 | States | Layers | Facing | Exists / path | Method |
|---|---|---|---|---|---|---|---|
| shield_bar | Thin glossy horizontal bar like a breakout paddle: rounded ends, light highlight along the top. Reference is a blue pill with white top gloss; restyle with faint cyan ghost glow | about 180 x 22 | place (fade in 8), idle shimmer (12 loop), block flash (6), break (8), expire (8) | single + code glow | NF | no (reference only: `(not published)`) | IE |
| shield_path_markers | Four faint dotted cyan arcs for the last 4 enemy paths | arcs across the field, 3 px line | shown while placing or moving, newest brightest | single | NF | no | CODE |
| shield_break_fx | Cyan-white spark ring on block, glass shards on the second block | about 120 x 120 | block 6, break 8 | single | NF | no | CODE |
| shield_status_pips | Pips for 2 blocks, 2 rounds, 4 uses (1 placement + 3 moves) | about 14 px each | full / used | single | NF | no | CODE |

Rules from `game_mode.md`: slides left-right only, height follows the remembered path at that x, remembers 4 paths
and snaps to them, blocks 2 projectiles, lasts 2 rounds, every placement or move costs the unit's turn.

UNSURE: bar width and thickness; the shield is not visible in the mockup; whether the remembered paths are shown;
where the counters sit in the target HUD.

---

## 5. Environment (14)

| id | Looks | Size @1920 | States | Layers | Facing | Exists / path | Method |
|---|---|---|---|---|---|---|---|
| env_sky_moon | Deep indigo-purple painterly sky and clouds, very large pale-yellow moon with halo | 1920 x about 700; moon about 400 across | static, optional cloud drift | far background | NF | partial: `assets/env/bg_graveyard.png` (bright flat-vector blue, different style) | IE |
| env_castle | Gothic castle with many spires and orange lit windows on a hill, in front of the moon, right of centre | about 610 x 400 | static, window flicker in code | background | NF | partial: `bg_graveyard.png` | IE (same plate as sky) |
| env_mid_graveyard | Hills of tombstones, crosses, crooked iron fences, bare trees, mist, purple-blue haze | 1920 x about 330 | static | background mid | NF | partial: `bg_graveyard.png` | IE |
| env_tree_frame | Dark twisted bare trees with hanging branches in the top corners | about 450 x 500 each | static | frame layer | drawn left, mirrored right | partial: baked into `bg_graveyard.png` | IE |
| env_bats_flying | Small black bat silhouettes, wings spread, 3-4 | 50 x 30 to 80 x 40 | flap 6 loop | single | drawn left, mirrored by direction | partial: baked into `bg_graveyard.png` | REUSE (cut out) |
| env_ground_band | Wide dark cracked-earth strip where units stand, rock cliff face below with roots, orange candle light | 1920 x about 180 | static | ground | NF | partial: `assets/env/ground_strip.png` (floating island, 1536 x 384, props baked at both ends) | IE |
| env_foreground_props | Dark tombstones, crosses, small jack-o'-lanterns, clusters of lit candles; large candle bottom-left, jack-o'-lantern bottom-right | strip 1920 x about 120 | static, flame 4-frame flicker | foreground | NF | no | T2I |
| platform_corner_blue | Top-left tilted dark-wood slab, iron corners, glowing blue spiral eye rune, blue ghost flames on corners, icicle drips | about 214 x 147 | bob 2 px; flame 8 loop | single + code flames | drawn left, not mirrored | partial: `assets/env/platform_coffin_blue.png` (edge-on coffin, no rune eye) | IE (from the purple one) |
| platform_corner_purple | Top-right twin of the blue slab with purple rune and purple wisps | about 214 x 147 | bob 2 px; flame 8 loop | single + code flames | drawn right, not mirrored | yes: `assets/env/platform_coffin_purple.png` | REUSE |
| platform_plank | Long flat weathered plank, purple edge trim, iron brackets, small skull on the front, lit candles at one end, pale blue wisps below | about 343 x 86 (+ wisps, 150 total) | bob 2 px; flame 4; wisps 8 loop | plank + code | candles on LEFT, mirrored for the right plank | partial: `assets/env/platform_skull_plank.png` (3/4-view block, skull at a corner) | IE |
| env_wisps_under_plank | Pale blue-white translucent ghost flame tongues | about 120 x 70 each | sway 8 loop | single, additive | NF | no | CODE |
| env_ghost_carrier | Cute white-blue ghost, big smile, pink cheeks, both arms up gripping ropes, round tail | about 160 x 122 (left), 125 x 95 (right) | idle bob 12 loop; drop 10; fly off 10 | ghost, separate from crate and ropes | symmetric | partial: `assets/env/ghost_lantern.png` (one rope, lantern) | IE |
| env_crate_hanging | Dark wooden crate, iron corner plates, glowing orange jack-o'-lantern flame emblem, two ropes in a V | about 92 x 98 + 60 rope | sway 12 loop; fall 6; open 10; empty 1 | crate + ropes | symmetric | partial: `assets/env/crate_fire.png` (broken and burning) | IE |
| env_fence_center | Not clearly visible in the mockup. Prototype fence in the middle of the field. Graveyard style: weathered dark pickets or iron rail | 130 x 250 (from `index.html`) | intact, cracked, heavily broken, destroyed (debris) | single per state | symmetric | no | T2I |

UNSURE: replace or keep `bg_graveyard.png` as a placeholder (the mockup is darker and painted); a full-width flat
ground band or the island shape; terrain damage or craters; whether the platforms are solid terrain, cover or
decoration; whether runes or a spiral eye marks the slabs; ghost holds two ropes to a crate (mockup) but the file
has one rope to a lantern; airdrop rules (what it gives, when it falls, how it is collected); whether a centre
fence exists in the target mode (the mockup shows only background iron fences).

---

## 6. Effects (16)

| id | Looks | Size @1920 | States | Layers | Facing | Exists / path | Method |
|---|---|---|---|---|---|---|---|
| fx_muzzle_flash | White-yellow-orange starburst with long streak, dark purple outline | about 120 x 120 | 8 frames one shot | single, additive | streak points right, rotated to barrel | yes: `assets/env/fx_muzzle_flash.png`, `(not published)` | REUSE |
| fx_impact_burst | Cartoon mushroom cloud, orange and purple, cyan edge, debris | about 200 x 200 | 14 frames | single | NF | yes: `assets/env/fx_impact_burst.png`, `(not published)` | REUSE |
| fx_hit_spark | Yellow-orange star burst, black outline, white centre | about 100 x 100 | 8 frames | single | NF | yes: `assets/env/fx_hit_spark.png`, `(not published)` | REUSE |
| fx_charge_glow | Swirling orange-yellow vortex, purple body, cyan lightning edge | about 90 x 90 | 16 frames loop, scales with power | single, additive | NF | yes: `assets/env/fx_charge_glow.png`, `(not published)` | REUSE |
| fx_landing_ring | Thin flat gold ellipse on the ground with sparks and a glowing vertical line or arrow | about 110 x 17; beam about 130 high | pulse 16 loop; spawn 6 | single | NF | partial: `assets/env/ui_target_ring.png`, `(not published)` (thick perspective disc) | CODE |
| fx_aim_arc | Yellow dashed parabola with an arrowhead | up to about 700 x 250 | dash flow | single | follows shot | no | CODE |
| fx_cannon_smoke | Grey-purple soft smoke puffs from the muzzle | about 100 x 100 | 10 frames | single | drifts from barrel | no | CODE |
| fx_dust_puff | Small grey-brown dust puffs at the feet | about 40 x 30 | 6 frames | single | NF | no | CODE |
| fx_projectile_trail | Fading ribbon behind the weapon; orange pumpkin, purple dagger, grey ball, cyan spear | about 120 long | continuous | single | follows velocity | no | CODE |
| fx_damage_number | Bold white-yellow number with dark outline, rises and fades | about 40 px tall | 0.8 s | single | NF | no | CODE |
| fx_selection_ring | Glowing cyan ellipse under the active unit | about 170 x 30 | pulse 12 loop | single | NF | no | CODE |
| fx_candle_flame | Small orange-yellow flame | about 10 x 18 | 4 loop | single, additive | NF | no | CODE |
| fx_spirit_flame | Blue (left) and purple (right) flames on corner slabs | about 40 x 60 | 8 loop | single, additive | NF | no | CODE |
| fx_fence_debris | Splinters of dark wood and rail pieces, dust | 10 to 40 px | 1.0 s burst | particles | away from impact | no | CODE |
| fx_death_wisps | Unit turns translucent and breaks into rising cyan ghost flames | about 100 x 140 | 14 frames | single | NF | no | CODE |
| fx_crate_open | Orange sparks and cyan wisps at airdrop collection | about 140 x 140 | 10 frames | single | NF | no | CODE |

Camera shake exists in the prototype and is not an art object. UNSURE: what the two rings in the mockup mean (a
dashed arc and a prediction would conflict with the no-preview rule in `product.md`); whether the charge-glow
image has a solid dark disc that would cover the hand; hit numbers wanted; ring colour for agents.

---

## 7. UI (21)

| id | Looks | Size @1920 | States | Layers | Facing | Exists | Method |
|---|---|---|---|---|---|---|---|
| ui_title_logo | 南瓜殺手 in large cream-orange carved letters with dark outline, small jack-o'-lantern and bat at the right | about 370 x 90, top-left | static | single | NF | no | IE (mockup crop), fallback CODE text + ornament |
| ui_topbar_frame | Dark navy bar with thin gothic metal edges and thorn corners; four sections | 1920 x about 60 | static | 9-slice | NF | no | CODE |
| ui_top_players_panel | Blue plate, "4 PLAYERS", four cyan diamond pips | about 330 x 50 | pip lit / lost | plate + text + pips | NF | no | CODE |
| ui_top_round_timer | Centre plate "第 3 回合" and large orange "08" | about 270 x 60 | normal; last 3 s red pulse | plate + text | NF | no | CODE |
| ui_top_wind | Dark plate with white arrow, 風 and value (0 in mockup) | about 190 x 45 | arrow flips with sign; range about -4..+4 | plate + arrow + text | arrow follows wind | no | CODE |
| ui_top_agents_panel | Purple plate, "4 AGENTS", four lavender hexagon pips | about 330 x 50 | pip lit / lost | plate + text + pips | NF | no | CODE |
| ui_unit_hp_bar | Small dark rounded bar, bright green fill, white "90/90" above, diamond marker at upper left | bar about 81 x 10 | full; damage trail; low; dead hidden | bar + text + marker | NF | no | CODE |
| ui_bottom_bar_frame | Wide dark plate, silver-grey metal edge, corner clasps, dividers | 1920 x about 160 | static; dim when locked | 9-slice | NF | no | CODE |
| ui_portrait_frame | Dark rectangle with ornate silver-grey border and unit-colour inner glow | about 178 x 135 | normal; selected; hit flash | frame | NF | no | CODE |
| ui_unit_name_hp | Class name (巫師炮手) in cream, "85 / 85", wide green HP bar | about 200 x 100 | HP fill | text + bar | NF | no | CODE |
| ui_btn_throw | Dark rounded square, orange border and glow when selected, jack-o'-lantern icon above 投射 | about 122 x 116 | normal, hover, selected, pressed, disabled | button + icon | NF | no | CODE |
| ui_btn_move | Dark rounded square, grey border, boot icon above 移動 | about 122 x 116 | same 5 | button + icon | NF | no | CODE |
| ui_btn_defend | Dark rounded square, grey border, shield icon above 防禦 | about 122 x 116 | same 5 | button + icon | NF | no | CODE |
| ui_action_icons | Jack-o'-lantern, boot, shield, special placeholder | about 50 x 50 | static | single each | NF | no | T2I (one sheet) or CODE |
| ui_angle_selector | Label 角度, dark pill with orange left/right arrows and value "55°" | about 150 x 40 | normal; pressed; range 25..80 | pill + text | NF | no | CODE |
| ui_power_bar | Long dark pill with orange segments from the left | about 215 x 36 | fill 0..100, ping-pong | pill + segments | fills left to right | no | CODE |
| ui_ammo_slot | Small dark square frame with a jack-o'-lantern, label 彈藥 | about 60 x 70 | loaded; empty (0.55 s resupply) | frame + icon | NF | no | CODE |
| ui_special_slot | Dashed empty square, label 特殊武器 | about 65 x 65 | empty; filled; used | frame + icon | NF | no | CODE |
| ui_lock_button | Large orange gradient rounded button, dark bold 鎖定 | about 226 x 92 | normal, hover, pressed, disabled, locked | button + text | NF | no | CODE |
| ui_phase_banner | Not in mockup; shows human phase / agent phase | about 500 x 70 | slide in and out 1 s | single | NF | no | CODE |
| ui_game_over | Not in mockup; victory / defeat when HP reaches 0 | about 800 x 300 | victory, defeat | single | NF | no | CODE |

UNSURE: timer length (8 s mockup, 12 s prototype); wind arrow shows direction only or strength too; HP colour
thresholds; segment count of the power bar (about 12); whether the ammo icon follows the class weapon; whether
phase and game-over screens are wanted and what ends the game (one unit at HP 0 or a whole team); whether the
Chinese glyphs in the logo survive image-edit.

---

## 8. Throw cut-in (9)

When a unit throws, a large portrait of the attacker ("big head") pops up from the mockup's bottom-left portrait
panel and reacts. Portrait art needed per class: neutral, charging, throwing, hit (16 images).

Proposed timeline (design proposal, not in the mockup):

1. Unit selected: the portrait panel shows the neutral bust at 178 x 135 with the name and HP beside it.
2. Press to charge: frame pops from 1.0 to about 2.3 scale in 0.12 s (about 420 x 320), swaps to the charging
   portrait, speed lines loop, charge glow on the hand, frame glow brightens with the power meter.
3. Release: 2-frame white flash, throwing portrait with a shout, frame shake for 0.25 s together with the arm
   swing, muzzle flash and camera shake. The cannon adds smoke and recoil.
4. After about 0.6 s the frame shrinks back (0.2 s) to the neutral portrait. If the same unit is hit while
   shown, swap to the hit portrait with the red-white flash and cracks.

| id | Looks | Size @1920 | States / frames | Layers | Facing | Exists | Method |
|---|---|---|---|---|---|---|---|
| cutin_portrait_bat | Bust of the bat-cat: black face, orange-lined ears, collar, wing tip, dark backdrop. Neutral smug half-lidded; charging eyes narrow and ears back; throwing mouth open shouting, leaning forward; hit eyes shut, one ear flat | thumbnail about 178 x 135; cut-in about 420 x 320; author 1024 x 1024 | 4 images | bust on transparent background | FL (3/4 view) | no (source `assets/units/unit_bat_raw.png`) | IE |
| cutin_portrait_wizard | Mockup bust: glowing jack-o'-lantern with wide toothy grin and bright orange-yellow eyes, purple hat brim above, brass cannon barrel at lower right. Neutral that grin; charging brighter eyes, gritted grin; throwing mouth wide with flame light, hat blown back; hit squashed face, eyes shut, cracked rim | same | 4 images | same | FL | no (source `unit_wizard_raw.png`; target look is the mockup portrait) | IE |
| cutin_portrait_skeleton | Cream skull with cyan flame eyes, jaw and neck bones, armour scrap on the shoulder. Neutral grin; charging flames flare, brow down; throwing jaw dropped, flames streak back; hit skull tilted, eyes dim, crack | same | 4 images | same | FL | no (source `unit_skeleton_raw.png`) | IE |
| cutin_portrait_knight | Big pumpkin head with curled green stem, angry glowing face, black pauldron and shield edge. Neutral stern glare; charging stem trembles, eyes brighter, teeth bared; throwing roaring mouth with flame glow; hit wincing, face dim, dented plate | same | 4 images | same | FL | no (source `unit_knight_raw.png`) | IE |
| cutin_frame | Portrait border enlarged: dark metal, silver edge, corner studs, glow in the attacker's colour | 178 x 135 in bar; about 420 x 320 popped | idle; pop 0.12 s; hold; shake 0.25 s; return 0.2 s | frame + backdrop | NF | no | CODE |
| cutin_speedlines | Radial white and orange lines behind the portrait | about 500 x 400 | loop while charging; burst 6 frames | behind portrait | radial | no | CODE |
| cutin_release_flash | 2-frame white flash and short shout burst | covers the cut-in | 4 frames | overlay | radial | no | CODE |
| cutin_name_banner | Dark strip with class name and marker under the portrait | about 260 x 36 | slides in with portrait | strip + text | NF | no | CODE |
| cutin_hit_overlay | Red-white flash and crack lines over the portrait | covers the portrait | 6 frames | overlay | NF | no | CODE |

UNSURE: portrait orientation (the mockup bust looks front or slightly right); a fifth smirk state for a successful
hit (the brief says smirk/hit but lists four states); whether the cut-in rises above the bar or stays inside; whether
it also plays for agent throws; shout text per class.

---

## Totals

| Group | Objects | Exists (yes) | Partial | No |
|---|---|---|---|---|
| Characters | 20 | 0 | 10 | 10 |
| Held weapons and arms | 9 | 0 | 4 | 5 |
| Projectiles | 5 | 3 | 0 | 2 |
| Floating shield | 4 | 0 | 0 | 4 |
| Environment | 14 | 1 | 10 | 3 |
| Effects | 16 | 4 | 1 | 11 |
| UI | 21 | 0 | 0 | 21 |
| Throw cut-in | 9 | 0 | 0 | 9 |
| **Total** | **98** | **8** | **25** | **65** |
