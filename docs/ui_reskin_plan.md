# UI re-skin plan (Kiro task 32, design only)

Owner words (2026-11-09): "The bottom part and the whole UI must be redesigned." "Include the drops and the ghost." "Replace the objects, the fonts and the wind direction." "Replace ALL details." Earlier: compact half-transparent top HUD with short text, help only behind a small "?", black wrought-iron fence (tall, narrow, 3 states), real texture, clean screen, wizard-school Halloween magic. The big-head character at the lower left must be connected.

Nothing in `index.html`, `assets/`, `js/`, `scripts/` was changed. No image was made. No font was downloaded. Companion file: `docs/ui_asset_requests_2.md` (new Colab images).

## 0. What I read, what I could not read

Read in this checkout: `index.html` (HTML/CSS head, the draw code, `updatePhysics`, `updateDock`, airdrop code, `resetGame`), `css/dock.css`, `docs/dock_design.md`, `docs/dock_asset_requests.md`, `docs/wind_design.md`, `js/wind_fx.js`, `(not published)`, `docs/ROLES.md`, `shared/constants.json`, `(not published)`, and the wind lines of `scripts/mcp_game_server.py` and `scripts/mcp_stdio_server.py`.

Could not read or check:
- `docs/airdrop_design.md` does not exist in this checkout (file search found nothing). I read the drop code in `index.html` instead (`scheduleAirdrop`, `updateAirdrop`, `drawAirdrop`, `SUPPLY_ITEMS`).
- The Colab art on Drive (could not open): `ui_top_plate_left/right`, `ui_dock_frame`, `ui_plate_normal/active`, `ui_lock_plate`, `portrait_wizard`, `env_fence_intact`, the fx sprites, and the in-progress ghost carrier, crate, parachute and three portraits. Their pixel sizes and aspect ratios are unknown to me. Every "draw size" below is a target the main line should fit the art into, keeping aspect. If an aspect differs by more than 10 % from what I assume, tell me and I adjust.
- Nothing was rendered. All sizes are arithmetic from the code, not screenshots.
- Google Fonts pages (`fonts.google.com/...`) return no readable text to my tool (script-rendered). I read the license text from the `OFL.txt` files in the `google/fonts` GitHub repository instead.

### Findings in the current code that this plan fixes

1. **Canvas text is too small on screen.** The 1920x1080 canvas is shown in a container capped at 1400 px (`#game-container`, `max-width: 1400px`), so one canvas px is 0.729 CSS px. Canvas fonts of 11 to 13 px (landing tag 11, unit tag 13, HP number 12, shield text 12) are about 8 to 9.5 CSS px on a 1920 monitor. The dock already forbids anything under 12 CSS px.
2. **Debug text on every unit.** `drawFullArtCharacter` prints `我方 (1號位: x=560)` and `敵方 (2號位: x=…)` above each head. It breaks "screen must stay clean".
3. **Wind scale is stale.** `drawTopHUD` draws the wind bar as `wind / 5.0`, and `ambientSfx.setWind(Math.abs(wind) / 5)` uses 5, but the range is -4..+4 (`shared/constants.json`, and the draw `(Math.random() - 0.5) * 8.0`). The bar never fills and the wind sound never reaches full level.
4. **Shield counter does not match the rules.** The top plates print `🛡 charges/4`, but `resetGame` sets `shields.*.charges = 2` and the slab shows 2 blocks. Main line: confirm with the owner whether "4" means moves (`actions = 4`) or blocks. This plan shows 2 pips for blocks.
5. **Help text is stale.** `#instruction-pill` says the history path curves are kept on screen. The owner decided paths are hidden (`showPathLines = false`).
6. **The "?" overlaps the right team plate.** `#help-btn` sits at `top: 40px; right: 10px` (CSS px), 30x30. The right plate covers canvas x 1600..1900, y 12..68, which is CSS x about 1166..1385, y 9..50 in a 1400 container. Overlap is about 25x10 CSS px (my arithmetic, not measured).
7. **Top HUD colours disagree with the shield slabs.** HUD uses red (me) and teal (AI). The owner-approved slabs are blue (me) and purple (agents).
8. **The portrait is an emoji.** `updateDock` writes `DOCK_GLYPH[currentHero]` into `#dock-portrait-art`. `dock.css` already supports `--portrait-img` but nothing sets it. This is the "big head not connected" item. `portrait_wizard` exists; the other three are in progress.
9. **Wind model mismatch** (client acceleration 48 px/s² per unit, engine velocity offset 45 px/s per unit). See section c.

## 1. Scale rules used in this document

- Canvas objects are given in canvas px (1920x1080). On a 1920 monitor they show at 0.729x (1400 px container).
- DOM and CSS objects (dock, help) are given in CSS px at tier L from `docs/dock_design.md`. Multiply by 1.37 for canvas-equivalent.
- "Exists" means the Colab art is listed as existing in the task. "NEW" means a request in `docs/ui_asset_requests_2.md`.

## a. Replacement table

Order: top HUD, scene objects, drops, dock, overlays.

### a1. Top HUD (canvas, `drawTopHUD` and `drawRuleOverlay`)

| # | Object | Current look | New asset | Drawn in | Size @1920x1080 | State variants |
|---|---|---|---|---|---|---|
| 1 | Team plate, left (me) | `unitPanel(20, …)`: 300x56 rect at (20,12), fill 38 % dark, 2 px red edge `#ff6b6b`, "我方" 15 px bold sans, `🛡n/4` 13 px | `ui_top_plate_left` (exists). Blue trim to match the blue slab | canvas | 360x72 at (24,16). Draw at 85 % alpha so the scene shows through | normal; my turn (cyan rim breathes 2 s); hit (plate shakes 4 frames); KO (greyscale) |
| 2 | Team plate, right (agents) | Same code mirrored, teal `#2ee6d6`, label "AI" | `ui_top_plate_right` (exists). Purple trim | canvas | 360x72 at (1536,16) | same as row 1; "thinking" (violet ring spins while the agent decides) |
| 3 | HP bar | Flat rect 276x14, solid fill (red or teal), 12 px white number, AI bar fills from the right | NEW `ui_hp_bar` frame + fill. Fill colour by state (green > 60 %, amber 30..60 %, red < 30 %), not by team | canvas | 280x20 inside the plate. Number 20 px display, right-aligned inside the bar | full; mid; low (pulse 1 Hz); damage (a pale "ghost" segment drains over 0.6 s); heal (green sparkle); empty |
| 4 | Shield pips | Text `🛡 2/4`, 13 px cyan | NEW `ui_pip` on/off, tinted blue (me) or purple (agents) | canvas | 2 pips of 24x24 under the HP bar, 6 px gap (see finding 4) | on; off; just spent (pop and shatter 0.3 s) |
| 5 | Centre plate | 300x62 at (810,10), yellow edge, 38 % dark fill, holds round, distance and wind bar | NEW `ui_top_plate_center` | canvas | 480x92 at (720,10), three zones: A round and distance (x 720..846), B wind (846..1074), C timer (1074..1200) | normal; round change (number flips 0.25 s); game over (dim) |
| 6 | Round label and distance | `第 N 回合 · Dpx`, 14 px bold yellow | Same plate, display + body fonts | canvas | Line 1 `第 3 回合` 22 px body 700. Line 2 `距離 1100` 17 px body 400, dim | normal; new round (gold flash 0.4 s) |
| 7 | Wind readout | Bar from the centre, 240x24 track, `風 ▶ 2.4` 13 px, `wind/5` scale, one colour | Code-drawn flame-pip track using fx ghost-fire (exists). Spec in section c | canvas | Zone B, 228x60: word line y 38, track y 68, 10 sockets of 20 px at 22 px pitch | steps 0 to 5; direction left/right; gust (grows in 0.4 s); reduced motion (no sliding chevrons) |
| 8 | Turn timer | Text `⏱ N`, 26 px bold at (960,108), red at 3 s or less; only on my turn | NEW `ui_timer_frame` (ring); the arc is drawn by code | canvas | Zone C, ring 64x64 centred at (1137,56). Number 32 px display | my turn running; paused while charging; 3 s alarm (red, pulse 2 Hz); agent turn (violet spinner); over |
| 9 | Help button "?" | DOM `#help-btn` 30x30, dark circle, cyan edge, `?` 18 px sans | `ui_plate_normal/active` (exists) as background; `?` in display font | CSS | 44x44 hit area (36 px plate) at `right: 12px; top: 70px`, below the right plate (fixes finding 6) | normal; hover; pressed; open; focus ring (cyan 3 px) |
| 10 | Help pop-over | DOM `#instruction-pill`, 340 px wide, 94 % dark, cyan edge, 13 px bold, emoji lines | NEW `ui_help_scroll` (9-slice). Opens only on "?" or H, closes on Esc, outside click, or "?" again | CSS | 380x auto, right aligned under the button. Body 14 px regular 400, headings 16 px bold | closed; open (fade 150 ms); first-run (opens once at game start, closes at the first throw) |

### a2. Scene objects (canvas, `draw()`)

| # | Object | Current look | New asset | Drawn in | Size @1920x1080 | State variants |
|---|---|---|---|---|---|---|
| 11 | Unit tag (name + HP over the head) | Bar 110x9 at y-214, 13 px text including debug `x=…` (finding 2) | `ui_hp_bar` (small) + a round class badge cropped from the portrait. No coordinates | canvas | 170x44 plate, centred, bottom edge at `u.y - 206`. Name 17 px body 700. Bar 130x12 | normal; my unit (cyan rim); hit (flash 0.1 s); low HP (bar pulse); KO (fades) |
| 12 | Action menu above the head | Backing plate 76 tall, tail to the head, items 108x52 with emoji + 20 px bold label, border colour per action | NEW `ui_menu_chip` normal/hover. Backing plate drops; the chips carry their own frame | canvas | Chips 150x64, gap 12, centred at `u.y - 318` (`MOVE_ROW_DY` stays). Label 24 px display + small icon from `skill_icons` | normal; hover (lift 2 px, gold rim); pressed (sink 2 px); disabled (move used this turn, 50 % greyscale); keyboard focus |
| 13 | Move control (die, arrows, needle) | `drawDie` ivory die 56 px, two 104x48 arrow plates, 6 px needle, 16 to 26 px labels | Arrow plates reuse `ui_menu_chip`. Die and needle stay code-drawn. Rune circle fx (exists) under the die | canvas | Die 64, arrow chips 150x64 at dx ±110, needle 78 px | idle (die cycles); aiming (needle follows pointer, chip lights); rolling (wobble); result (`▶ 3` 34 px display) |
| 14 | Float texts | `bold 18px sans-serif`, shadow blur 8, rises 35 px/s, fades 0.65/s, emoji + long sentences | No image. New font, outline, number pop-ups. Section d for rules | canvas | Status 26 px body 700; damage 34 px display; max 3 on screen | damage; heal; block; fence; miss; pickup; warning (colours in section d) |
| 15 | Angle readout in the scene | `角度 54°` 18 px bold cyan at `(player.x, player.y-232)`; stepper plates are off (`SHOW_ANGLE_PLATES = false`) | Rune circle badge: fx rune circle (exists) behind the number | canvas | 88x88 badge near the throwing hand, number 28 px display. Shown only while aiming or charging | aiming; charging (badge glows orange); hidden in menu, move and defend modes. The dock shows the same value, that duplicate is intended (eyes stay on the unit) |
| 16 | Power charge arc | `drawPowerChargeArc`: 75 px radius arc, 14 px stroke, green to red gradient, `NN%` 22 px | fx rune circle (exists) as the dial, arc drawn in 20 steps of 5 (matches dock meter) | canvas | Radius 84, stroke 14, number 30 px display | idle (hidden); charging (arc fills, ping-pong 1.3 s as now); release (flash, arc collapses 0.15 s) |
| 17 | Fence, 3 states | `drawCentralWall`: 7 wooden pickets, two rails, posts, pumpkin lantern, label `中央圍籬 (85%)` 14 px. Hitbox 130x250 at x 895..1025 | `env_fence_intact` (exists) + NEW `env_fence_damaged`, `env_fence_broken` | canvas | Art box 130 wide x 250 tall to match the hitbox (see note below). Remove the percentage label | **intact** `wallHp` 100..70; **damaged** 55..10; **broken** 0 (no collision, rubble stays). Cross-fade 0.25 s on change. Hit: 4 px shake 0.2 s + spark |
| 18 | Floating shield slab | `drawAirborneShield`: slab art (exists in `assets/ui/shield_slab_*.png`), W+40 wide, 2 diamond blocks above, `剩 N 輪` and the drag hint at 12 px, vertical dashed guide | Keep slab art. Pips become `ui_pip`. Text uses the new fonts | canvas | Slab as now. Pips 24 px. Text 20 px body 700 with outline | preview (65 % alpha, dashed); placed; dragging (glow 26); hit (flash + crack for 0.3 s); last round (flicker); blue (me) / purple (agents) |
| 19 | Shield tether (guard only) | Dashed 3 px curve from the head to the slab | Ghost-fire line (fx ghost-fire, exists) | canvas | 3 px core, 10 px glow | active; hidden |
| 20 | Thrown-path trail | `drawThrownPaths`: additive dots every 3rd point (r 2.2 to 5.4) + faint 3 px line; ribbon behind the weapon; fades over `TRAIL_FADE_SEC = 1.8` | Stardust fx sprite (exists) for the dots; ribbon stays code-drawn | canvas | Dot sprite 18 px; ribbon 10..16 px | flying; fading (1.8 s); heavy (wider); per weapon colour as now. In wind, the fading tail drifts downwind up to 40 px (`wind_design.md`) |
| 21 | Remembered enemy path + landing tag | Dashed 3 or 6 px line, 6 px dot, tag `軌跡 [R3]` 11 px | Same line. Tag becomes a small plate | canvas | Tag 17 px body 700 on a 56x28 plate | shown only in defend mode, valid path glows cyan |
| 22 | Target ring | `ui_target_ring_sheet.png` exists (16 frames) but nothing draws it today (aim guide is off) | Same sheet | canvas | 120 px | **Landing mark**: at the impact point for 1.8 s with the trail. **Drop mark**: under a falling crate on the ground (row 24). No ring before the throw (no preview) |

Fence note. The hitbox is shared with the engine (`FENCE_X`, `FENCE_W`, `FENCE_H` in `shared/constants.json`). The art must fill about 90 % or more of 130 px width, otherwise a throw "hits air". If the owner wants a narrower fence, that is a constants change in three places plus a re-run of the wind and reach checks, so it is a separate decision. Picket count is gone with the new art, so damage reads from the three states plus the shake, not from missing pickets.

### a3. Drops and the ghost (canvas, `drawAirdrop`)

| # | Object | Current look | New asset | Drawn in | Size | State variants |
|---|---|---|---|---|---|---|
| 23 | Ghost carrier | `drop_ghost` = `assets/env/ghost_lantern.png`, 120x180, alpha 0.9, flies left to right at 330 px/s, y 170 with a sine bob, crate 72x72 hangs below until released | Ghost carrier (Colab, in progress). Mist fx (exists) as a trail | canvas | 150x220 | enter (fades in at the edge); carrying; released (arms up, crate drops); leaving (fades out). A small ribbon cue `物資來了` shows once when it enters, with an arrow toward the drop side |
| 24 | Supply crate | `drop_crate` = `assets/env/crate_fire.png`, 96x96 | Supply crate (Colab, in progress) | canvas | 100x100 | falling (sways ±14 px); landed (bobs); pick-up (burst of stardust + rune circle fx, 0.4 s) |
| 25 | Parachute | `drop_parachute` file not made yet, nothing is drawn; 160x160 | Parachute (Colab, in progress) | canvas | 170x170, anchored 70 px above the crate | open; collapsing after landing (fades over 0.8 s) |
| 26 | Landed item icon | Emoji `🧪` or `💣`, 34 px, bobs 82 px above the crate | `skill_icons` heal potion and heavy bomb (NEW, reused) | canvas | 56x56 | bobbing; picked up (flies to the dock slot in 0.35 s) |
| 27 | Drop landing mark | none | Target ring sheet (exists) at the target x on the ground, 40 % alpha | canvas | 110 px | visible from the moment the ghost releases until landing |

### a4. Bottom dock (CSS, `css/dock.css`, already wired)

| # | Object | Current look | New asset | Drawn in | Size (CSS px, tier L) | State variants |
|---|---|---|---|---|---|---|
| 28 | Dock frame | CSS gradients: stone slab in a wood beam, rivets, 3 px ghost-fire line, two CSS candles | `ui_dock_frame` (exists), 9-slice via `border-image`; keep the ghost-fire line and candles in CSS | CSS | 1280x104, 12 px from the bottom | normal; my turn (frame rim glow); low HP (frame tint red 10 %) |
| 29 | Shot buttons (4) | `.skill-btn` stone tiles with emoji icons and 12 px labels, wax-seal count badge | `ui_plate_normal/active` (exists) as `background-image`; icons NEW `skill_icons` | CSS | 60x76 each, 6 gap, icon 28, label 12 | normal; hover; active; pressed; disabled; cooldown; ready pulse; focus (all in `dock.css`) |
| 30 | Hero chips (4) | `.hero-tab` 44x44 with emoji and 2-character name | `ui_plate_normal/active` with cyan tint | CSS | 44x44 | normal; hover; active (cyan); focus |
| 31 | Portrait ("big head") | 80x80 box, emoji glyph on a purple gradient, ring states `.is-charging`, `.is-shout`, `.is-hit` | `portrait_wizard` (exists), skeleton/bat/knight (in progress), expressions NEW `portrait_cutin_*` | CSS | 80x80 (cut-in at KO: 220x220, see row 40) | my turn (cyan ring); charging; shout; hit; KO (greyscale). **Wiring**: `updateDock` sets `--portrait-img` from `currentHero`; falls back to the emoji until the file loads |
| 32 | Dock name and HP | `.dock-name` 17 px serif, `.dock-hp` 12 px bar, number 14 px | `ui_hp_bar` (NEW) | CSS | 182x12 (bar), 182x20 (name row) | green, mid, low (pulse) |
| 33 | Angle plate and power meter | `.dock-plate` dark recess, 28 px gold angle, 20-segment CSS-masked meter | CSS stays (no image requested, meter is a flat mask). Fonts change | CSS | 88 wide; meter 22 high | idle; charging (orange glow); at 100 % (flash) |
| 34 | Ammo and supply slots | `.dock-slot-box` 60x60, emoji icon, dashed violet empty socket | NEW `slot_sockets`, `ammo_icons`; supply uses `skill_icons` | CSS | 60x60 each | ammo normal; supply empty (dashed); supply full (violet breathe); just filled (pop) |
| 35 | Lock button | `.dock-lock` orange CSS plate, 24 px 鎖定, hidden unless `defendMode` | `ui_lock_plate` (exists, pumpkin lid) | CSS | 120x68 | hidden; ready pulse; hover; pressed; disabled |
| 36 | Reset and sound buttons | `.skill-btn` 44x44 with 🔄 and 🔊 | `ui_plate_normal`; glyphs drawn with CSS shapes or the display font (no emoji) | CSS | 44x44 | normal; hover; sound muted (slash) |

### a5. Overlays (canvas)

| # | Object | Current look | New asset | Size | State variants |
|---|---|---|---|---|---|
| 37 | Game-over banner | Full-screen 72 % dark fill, `🎃 你贏了！` / `💀 子代理獲勝` 72 px bold, `點一下畫面重新開始` 26 px | NEW `ui_banner` win / lose | Banner 1100x330 centred at y 470; title 72 px display; sub 28 px body | win (gold, stardust); lose (violet, mist); restart accepts input after 1.0 s |
| 38 | Turn-start cue | None (only a sound) | NEW `ui_banner` ribbon | 520x108, y 300 | slides in 0.25 s, holds 0.6 s, out 0.25 s; text `你的回合` / `Your turn` |
| 39 | Low-HP vignette | None | Code only (radial gradient) | full screen, centre clear | off; on at HP 30 % or less (matches the existing heartbeat at 0.3) |
| 40 | KO cut-in | None | Portrait of the fallen unit, `ko` face (NEW `portrait_cutin_*_ko`) | 360x360 | slides in 0.2 s, holds 0.9 s, ghost wisps leave (existing `ko_wisps`), then the banner |

## b. Fonts

Goal: one display face for titles and numbers with a Halloween-magic feel, one highly readable body face, both usable for Traditional Chinese and Latin digits, free, SIL OFL, embedded in the page, no accounts, no payment.

### b1. Choice

| Role | Latin and digits | Traditional Chinese |
|---|---|---|
| **Display** (titles, numbers, banners, damage) | **Cinzel Decorative** Bold (inscription capitals, "old spellbook" feel) | Fallback: **Noto Serif TC** pinned at weight 900 and subset |
| **Body** (help, tooltips, status, small labels) | **Noto Sans TC** (its Latin and digits come with it) | **Noto Sans TC** |

Why: Cinzel Decorative is Latin only, so the Chinese in the display role must come from a fallback. A high-contrast Ming serif at heavy weight sits next to Roman capitals without a clash. Noto Sans TC is the plain, even-stroke choice for small text. Taste check: I have not seen these rendered. The pass condition in step 2 is a screenshot at 24 px that the owner approves. Alternates if the owner dislikes the look: Chiron Sung HK (OFL-1.1 per its GitHub page, `https://github.com/chiron-fonts/chiron-sung-hk-gf`, not evaluated by me) for the Chinese display fallback; plain Cinzel (same author, folder `ofl/cinzel`, which I did not open) if the swash capitals hurt readability.

### b2. Facts per font (all read from the sources in section b6)

| | Cinzel Decorative | Noto Serif TC | Noto Sans TC |
|---|---|---|---|
| License | SIL Open Font License 1.1 | SIL Open Font License 1.1 | SIL Open Font License 1.1 |
| Copyright line on its `OFL.txt` | "Copyright (c) 2012 Natanael Gama … with Reserved Font Name 'Cinzel'" | "Copyright 2012 Google Inc. All Rights Reserved." No reserved name | "Copyright 2014-2021 Adobe … with Reserved Font Name 'Source'" |
| Source file | `CinzelDecorative-Bold.ttf` | `NotoSerifTC[wght].ttf` (variable, wght 200 to 900 expected, axis range not read) | `NotoSansTC[wght].ttf` (variable, wght 100 to 900, from its `METADATA.pb`) |
| Size of the original | 62,300 bytes (Regular 60,408; Black 62,692) | 16,851,596 bytes (about 16.1 MiB) | 11,941,968 bytes (about 11.4 MiB) |
| Scripts | Latin | Traditional Chinese, Latin, Cyrillic, Greek, kana, Hangul | Traditional Chinese, Latin, Cyrillic, Vietnamese |
| Subset needed? | **No. Use the file unmodified.** 62 KB is small, and a subset would count as a Modified Version, which may not keep the reserved name "Cinzel" | Yes | Yes |

License consequences (my reading of the `OFL.txt` conditions, not legal advice):
- Free to embed and redistribute with the game. Each copy must ship the copyright notice and license text. Put each font's `OFL.txt` next to it in `assets/fonts/`.
- Do not sell a font file by itself.
- A subset or an instanced weight is a Modified Version. Rule 3 forbids using a Reserved Font Name for a modified file. Cinzel has one, so it stays unmodified. Noto Sans TC's reserved name is "Source", which is not in its family name, and Noto Serif TC has none. I did not find the OFL FAQ passage on subsetting; the FAQ page opened but the relevant section was not extracted.
- In CSS the family aliases are our own names (`"PK Display"`, `"PK Body"`), so no reserved name is used.

### b3. Official sources (the main line downloads, I did not)

| Font | Folder (license, metadata) | File to take |
|---|---|---|
| Cinzel Decorative | `https://github.com/google/fonts/tree/main/ofl/cinzeldecorative` | `https://raw.githubusercontent.com/google/fonts/main/ofl/cinzeldecorative/CinzelDecorative-Bold.ttf` and `…/OFL.txt` |
| Noto Serif TC | `https://github.com/google/fonts/tree/main/ofl/notoseriftc` | `https://raw.githubusercontent.com/google/fonts/main/ofl/notoseriftc/NotoSerifTC%5Bwght%5D.ttf` and `…/OFL.txt` |
| Noto Sans TC | `https://github.com/google/fonts/tree/main/ofl/notosanstc` | `https://raw.githubusercontent.com/google/fonts/main/ofl/notosanstc/NotoSansTC%5Bwght%5D.ttf` and `…/OFL.txt` |

Upstream projects: `https://github.com/NDISCOVER/Cinzel` (Cinzel) and `https://github.com/notofonts/noto-cjk` (Noto CJK).

### b4. Subsetting (so the page stays light)

Tool: fontTools (`fonttools subset`, `fonttools varLib.instancer`), free, Python. WOFF2 output needs the Python `brotli` package (I did not check it in this session). Options below are from the fontTools documentation pages listed in b6.

1. **Collect the characters the game uses.** Every non-ASCII character in `index.html`, `js/*.js` and the i18n string table (`docs/` or wherever Kiro task 08 lands), plus the strings in section d. Save to `(not published)`.
   ```
   cat index.html js/*.js css/*.css | python3 -c "import sys; t=sys.stdin.read(); print(''.join(sorted({c for c in t if ord(c)>=0x2E80})))" > build/fonts/cjk_chars.txt
   ```
   Add the i18n files to the `cat` list. Include the CJK punctuation block (U+3000 to U+303F) and fullwidth forms (U+FF00 to U+FFEF); the one-liner above already takes them.
2. **Pin the weights** (static instances are smaller than a variable font):
   ```
   fonttools varLib.instancer "NotoSansTC[wght].ttf" wght=400 -o build/fonts/NotoSansTC-400.ttf
   fonttools varLib.instancer "NotoSansTC[wght].ttf" wght=700 -o build/fonts/NotoSansTC-700.ttf
   fonttools varLib.instancer "NotoSerifTC[wght].ttf" wght=900 -o build/fonts/NotoSerifTC-900.ttf
   ```
3. **Subset** (default layout features do **not** include `tnum`, `pnum`, `lnum`, so add them):
   ```
   fonttools subset build/fonts/NotoSansTC-400.ttf --text-file=build/fonts/cjk_chars.txt --unicodes=U+0020-007E,U+00A0-00FF,U+2010-2027,U+2190-2193,U+25B6,U+25C0 --layout-features+=tnum,pnum,lnum --no-hinting --flavor=woff2 --output-file=assets/fonts/pk-body-400.woff2
   ```
   Repeat for `-700` (`pk-body-700.woff2`) and for the serif at 900 (`pk-display-cjk-900.woff2`).
4. **Copy** `CinzelDecorative-Bold.ttf` to `assets/fonts/` exactly as downloaded. Do not subset, instance or convert it: its license names a reserved font name, and the license defines a Modified Version as including a port to a new format or environment.
5. **Size budget:** all four files together at most 600 KB. I did not measure the result. My estimate is tens of KB to roughly 150 KB per CJK file for a few hundred characters, so the budget has room. If a build is above 600 KB, the character list has a bug (it probably swept in a large block).
6. **Coverage test (automatic):** open each subset with fontTools, read the `cmap`, and fail if any character from `cjk_chars.txt` that is also in the source font is missing. Run it as part of the font build step.

Files go in `assets/fonts/`:
```
assets/fonts/CinzelDecorative-Bold.ttf   + OFL-CinzelDecorative.txt
assets/fonts/pk-display-cjk-900.woff2    + OFL-NotoSerifTC.txt
assets/fonts/pk-body-400.woff2
assets/fonts/pk-body-700.woff2           + OFL-NotoSansTC.txt
```

### b5. CSS `@font-face` lines (put in a new `css/fonts.css`, linked before `dock.css`)

```css
@font-face {
  font-family: "PK Display";
  src: url("../assets/fonts/CinzelDecorative-Bold.ttf") format("truetype");
  font-weight: 700; font-style: normal; font-display: swap;
  unicode-range: U+0020-007E, U+00A0-00FF, U+2010-2027;
}
@font-face {
  font-family: "PK Display";
  src: url("../assets/fonts/pk-display-cjk-900.woff2") format("woff2");
  font-weight: 700; font-style: normal; font-display: swap;
  unicode-range: U+2E80-9FFF, U+F900-FAFF, U+3000-303F, U+FF00-FFEF;
}
@font-face {
  font-family: "PK Body";
  src: url("../assets/fonts/pk-body-400.woff2") format("woff2");
  font-weight: 400; font-style: normal; font-display: swap;
}
@font-face {
  font-family: "PK Body";
  src: url("../assets/fonts/pk-body-700.woff2") format("woff2");
  font-weight: 700; font-style: normal; font-display: swap;
}
:root {
  --font-display: "PK Display", "Noto Serif TC", "Songti TC", "PMingLiU", Georgia, serif;
  --font-body: "PK Body", "PingFang TC", "Microsoft JhengHei", "Noto Sans TC", sans-serif;
}
```
In `dock.css` replace `--serif` with `var(--font-display)` and `--sans` with `var(--font-body)`. In canvas code define once: `const FONT_DISPLAY = '"PK Display","Noto Serif TC","Songti TC",serif'` and `const FONT_BODY = '"PK Body","PingFang TC","Microsoft JhengHei",sans-serif'`.

Canvas does not load a web font by itself the first time a string uses it. Before the first frame: `await Promise.all([document.fonts.load('700 28px "PK Display"', '0123你的回合'), document.fonts.load('400 17px "PK Body"', '回合'), document.fonts.load('700 17px "PK Body"', '回合')])`. The text argument makes the browser fetch the CJK file. Test the game on `http://localhost` as well as how the owner opens it; I did not check whether `file://` blocks fonts.

### b6. Sources read for this section

- `https://api.github.com/repos/google/fonts/contents/ofl/notosanstc` (file list and sizes), `…/ofl/notoseriftc`, `…/ofl/cinzeldecorative`.
- `https://raw.githubusercontent.com/google/fonts/main/ofl/cinzeldecorative/OFL.txt`, `…/ofl/notosanstc/OFL.txt`, `…/ofl/notoseriftc/OFL.txt` (license text).
- `https://raw.githubusercontent.com/google/fonts/main/ofl/cinzeldecorative/METADATA.pb`, `…/FONTLOG.txt`, `…/ofl/notosanstc/METADATA.pb`, `…/ofl/notosanstc/upstream_info.md`.
- `https://fonttools.readthedocs.io/en/latest/subset/index.html` and `https://fonttools.readthedocs.io/en/latest/varLib/instancer.html` (option names).
- `https://github.com/chiron-fonts/chiron-sung-hk-gf` (seen only as a search result snippet for the alternate).
- Could not open: `https://fonts.google.com/specimen/Cinzel+Decorative/license` (no readable text). `https://fontsource.org/languages/chinese-traditional` (HTTP 500). The OFL FAQ at `https://openfontlicense.org/ofl-faq/` opened but the subsetting passage was not extracted.
- Not verified: whether Cinzel Decorative or the Noto subsets have working `tnum` figures. I found no page that says. Handled by the digit rule below.

### b7. Type rules

**Minimum sizes** (canvas px at 1920 wide, and what they are at the 1400 px container; helper below keeps CSS size from falling under 12 px):

| Role | Face | Canvas px | CSS px at 1400 |
|---|---|---|---|
| Smallest label (tags, pip captions) | Body 700 | 17 | 12.4 |
| HUD names, menu small text | Body 700 | 20 | 14.6 |
| Status pop-up | Body 700 | 26 | 19 |
| Damage and heal numbers | Display | 34 | 24.8 |
| Timer, round number, angle, power | Display | 28 to 34 | 20 to 25 |
| Banner title / subtitle | Display / Body 700 | 72 / 28 | 52 / 20 |
| DOM dock labels / values / help body | Body 700 / Display / Body 400 | n/a | 12 / 16 to 28 / 14 |

- The display face is used for Chinese only at 22 canvas px or more. Below that its thin serifs break up; use Body 700.
- Display face for English: at most three words, capitals. Sentences in English go in the body face.
- Helper: `const S = canvas.clientWidth / 1920; const fs = base => Math.max(base, Math.ceil(12 / S));` Use `fs()` for every `ctx.font`. Below a 1000 px container the HUD text may outgrow its plate; 1000 px is the smallest supported canvas HUD. The dock has its own tiers down to 720.

**Text over the scene** (no plate behind it):
- Canvas: draw `strokeText` first with `lineJoin = "round"`, `miterLimit = 2`, `strokeStyle = "rgba(8,4,16,0.92)"`, `lineWidth = Math.max(3, size * 0.16)`, then `fillText`. Add `shadowBlur = 6`, `shadowColor = "rgba(0,0,0,0.8)"` only for the stroke pass.
- CSS: `text-shadow: 0 1px 0 #000, 1px 0 0 #000, -1px 0 0 #000, 0 -1px 0 #000, 0 0 8px rgba(0,0,0,.7)`. `paint-order: stroke fill` with `-webkit-text-stroke` would be cleaner but I did not verify browser support.
- On a plate: no stroke, one 1 px dark offset shadow.

**Numbers in tabular style:** live numbers (HP, timer, angle, power, wind, damage) use `font-variant-numeric: tabular-nums` in CSS. In canvas I found no setting for numeric variants (canvas has `fontKerning` and `fontVariantCaps`, not numeric), so draw digit by digit in fixed cells: cell width = widest of `0..9` from `measureText`, each digit centred in its cell. This works whether or not the font has `tnum`, so the numbers never jitter. Pass check: draw `1111` and `8888`; the two rectangles have equal width.

## c. Wind indicator

Inputs: `docs/wind_design.md` (task 25) and `js/wind_fx.js` (not wired). This section changes the HUD part and the asset bindings, and sets the constant. The scene numbers (counts, speeds, lean angles, clean-screen budget of 64 default and 96 maximum) stay as in `wind_design.md` section 2.

### c1. Strength steps 0 to 5

`step = Math.min(5, Math.round(Math.abs(wind) / 0.8))`. Wind is `uniform(-4, 4)` rounded to one decimal, so each of the six steps is hit about 10 %, 20 %, 20 %, 20 %, 20 %, 10 % of rounds (my arithmetic: step 0 covers |w| < 0.4, step 5 covers |w| of 3.6 or more).

| Step | |w| range | zh-TW word | English word | Colour of word, number and lit sockets |
|---|---|---|---|---|
| 0 | 0 to 0.39 | 無風 | Calm | `#cfd8ff` pale blue-white |
| 1 | 0.4 to 1.19 | 微風 | Breeze | `#cfd8ff` |
| 2 | 1.2 to 1.99 | 和風 | Gentle | `#ffd27a` warm gold |
| 3 | 2.0 to 2.79 | 強風 | Strong | `#ffd27a` |
| 4 | 2.8 to 3.59 | 烈風 | Gale | `#ff8a4d` ember orange |
| 5 | 3.6 to 4.0 | 狂風 | Storm | `#ff8a4d` |

The colour bands (steps 0 to 1, 2 to 3, 4 to 5) replace the 1.5 and 3 thresholds in `wind_design.md` section 3, so colour and step always agree. The zh-TW words are my proposal for a Taiwan reader; the owner should read them.

### c2. Top plate, zone B (228x60 at x 846, y 10)

- **Line 1 (y 38):** the word in the display face 24 px (Noto Serif TC at this size is allowed), then the signed number with one decimal and a real minus sign, `+3.2` or `−1.0` or `0.0`, 22 px display, tabular cells. Both in the step colour. Centred on x 960.
- **Line 2 (y 68): the track.** 10 round sockets, 20 px, 22 px pitch, five each side of a centre diamond. Sockets light outward from the centre on the side the wind blows toward. Step n lights n sockets, drawn with the ghost-fire sprite (exists), unlit ones are dark carved holes. An arrowhead chevron sits on the last lit socket. At step 0 only the centre diamond glows and no arrow is shown.
- **Motion:** three small chevrons slide along the lit sockets at `60 + 120 × |n|` px/s (n = wind / 4), in the wind direction. They stop at step 0 and when `prefers-reduced-motion` is on. When a new wind arrives the lit length grows (or shrinks) from the old step to the new one in 0.4 s, in step with the gust in `wind_fx.js`.
- **Meaning without colour:** the word, the number, the socket count and the arrow direction each carry the information, so colour is a fourth redundant cue.
- **Direction wording:** positive wind blows to the right, which helps a left-side player and hurts a right-side one. The arrow points on screen; the tooltip (hover 500 ms) adds `順風 (對你有利)` / `逆風` or `Tailwind` / `Headwind` for the human side. No extra widget on the plate.
- **Scale fix:** the old `wind / 5` becomes `step / 5` for the track and `|wind| / WIND_MAX` for sound. `WIND_MAX` is 4.

### c3. In the scene

Binding of `wind_fx.js` items to art (the scene numbers are in `wind_design.md`):

| Element | Art | Notes |
|---|---|---|
| Fog banks (6, cap 8) | fx mist sprite (exists) instead of radial gradients | keep alpha 0.05 calm and 0.09 strong |
| Ghost-dust (32) | fx stardust sprite (exists) | stretch along the wind at strong |
| Dry leaves (26) | NEW `fx_leaves` strip (4 shapes) | replace the brown ellipses |
| Flames lean | fx ghost-fire and the fence-side lantern flame | `flameLean(w)`, 34° at the maximum |
| Banners and hanging lanterns | NEW `env_wind_props` | `swayAngle(w, t)`; cloth drawn in 8 horizontal strips with a phase offset per strip so it ripples |
| Flight ribbon tail and damage numbers | code | tail drifts up to 40 px, numbers lean 25 px (as designed) |

Placement: behind the units, in front of the background, inside the band 740 to 1180 canvas x (around the fence, where nobody stands for long), and never inside a keep-out rectangle.

Keep-out rectangles for `windFx.setAvoid` in canvas px: left plate `[24,16,384,88]`, right plate `[1536,16,1896,88]`, centre plate `[720,10,1200,102]`, dock zone `[0,915,1920,1080]` (dock top about y 921 in canvas px at tier L, from the clearance table in `dock_design.md`), and one rectangle per unit tag `[u.x-90, u.y-268, u.x+90, u.y-206]`. Call `setAvoid` after any unit move.

Code notes for the main line:
- `wind_fx.js` documents that `draw()` uses no transforms. Sprite leaves need `translate` and `rotate`. Use `save`/`restore` per item and keep each item's `ext` at the half-diagonal of the sprite so the keep-out test stays exact. Update `scripts/test_wind_fx.js` where it checks the allowed canvas calls.
- Keep the gradient drawing as the fallback when a sprite has not loaded.
- `ambientSfx.setWind(Math.abs(wind) / 5)` becomes `/ WIND_MAX`.

### c4. The constant (the owner said wind feels too weak)

- Today: the client adds `wind * 48 * dt` to `vx` each step (`updatePhysics`, `simulateLandingX`, and the disabled `drawAimGuide`). The engine adds a constant velocity offset of `wind * 45` px/s (`scripts/mcp_game_server.py`, `WIND_PUSH = 45.0` in `scripts/mcp_stdio_server.py`). Different models, so MCP paths in `get_history` disagree with what the player sees.
- **Recommendation: `WIND_ACCEL = 96` px/s² per wind unit, acceleration model everywhere, range stays -4..+4** (`wind_design.md` section 1: shift at wind ±4 goes from about ±190 px to about ±381 px, 20 % to 40 % of the field). Its open question 1 is still waiting for an owner "yes".
- One source: add `WIND_ACCEL` to `shared/constants.json`. `index.html` has no loader for that file; it hard-codes constants and `scripts/test_constants_sync.py` compares them. So: `const WIND_ACCEL = 96;` in `index.html` (replace the three literal `48`s), `WIND_ACCEL = _SHARED["WIND_ACCEL"]` in both Python servers, and add the key to the sync test.
- Engine change: replace `cur_x += (vx + wind * 45.0) * dt` by `vx += wind * WIND_ACCEL * dt; cur_x += vx * dt` in the same order as the client (wind, gravity, then positions). Same in `sample_path` in the stdio server.

### c5. AI wind compensation stays in sync

- Browser AI (`triggerAITurn` → `estimatePowerForTarget` → `simulateLandingX`): reads `WIND_ACCEL`, so it follows the constant automatically as long as the literal `48` is gone. But this is the simulator `product.md` forbids and owner question 5 (log section 4) is still open. If the owner answers "no simulator", this code and the `-3.2` below are removed and the AI learns from `get_history` only.
- Built-in Python AI (`wind_comp = self.wind * unit["facing"] * -3.2`): tuned for the old model. For 96 the matching figure is about 3.8 (`wind_design.md` section 5). A fixed number is a hidden simulator, so treat it as temporary.
- Sub-agents over MCP get only the public `wind` and `get_history`. They must not get the constant.
- **Sync test (automatic):** for a grid of wind (-4, -2, 0, 2, 4), power (40, 65, 90) and angle (40, 54, 70), the client step function and the engine function give the same landing x within 3 px. `scripts/eval_agent_learning.py` must still show the learning curve improve after the change.

## d. Detail pass checklist

Each line has a way to check it.

| # | Item | Spec | Check |
|---|---|---|---|
| 1 | Cursor | Field: `crosshair` (as now). Over menu chips, dock, help: `pointer`. While dragging the shield: `grabbing`. Not my turn: `not-allowed` over the field. No custom cursor image | DOM: computed `cursor` on canvas for each state in a script |
| 2 | Hover | Chips and dock buttons: lift 2 px, gold rim, 120 to 150 ms. Hover wrapped in `@media (hover: hover)` | CSS test: rule exists; screenshot of one hovered chip |
| 3 | Pressed | Sink 2 px, inner shadow, 120 ms | screenshot, `:active` forced |
| 4 | Focus ring | 3 px cyan outline, 3 px offset on all DOM buttons (already in `dock.css`). Canvas chips get the same ring when a keyboard shortcut selects them | Tab through the DOM; every button shows an outline |
| 5 | Tooltips | DOM `title` stays (zh/en). Canvas objects (plates, wind, timer): custom tooltip after 500 ms hover, 16 px body, on the help scroll 9-slice. Never above the dock, never in the clean zone | screenshot with the pointer parked on the wind readout |
| 6 | Turn-start cue | Ribbon `你的回合` slides in 0.25 s, holds 0.6 s, out 0.25 s. Portrait ring starts breathing. The existing `round_start` sound plays | force `turn="player"`, screenshot at 0.5 s |
| 7 | Low-HP vignette | At HP 30 % or less: dark red edge vignette, alpha 0.25, pulses 0.2 to 0.35 at 1 Hz in time with the existing heartbeat. Centre 60 % stays clear. No pulse under reduced motion | force `player.hp = 25`, pixel at (20,540) is redder than at (960,540) |
| 8 | KO cut-in | Fallen unit's `ko` portrait slides in 0.2 s, holds 0.9 s, ghost wisps (existing `ko_wisps`), then banner | force `gameOver`, screenshot at 0.6 s |
| 9 | Win / lose banner | `ui_banner` win (gold) or lose (violet). Title 72 px display. Subtitle `點一下畫面重新開始` / `Click to play again`. Input accepted after 1.0 s so a late click does not restart at once | wait 0.5 s: click ignored; 1.2 s: restarts |
| 10 | Number pop-ups | Display font 34 px, pop scale 1.4 to 1.0 in 0.12 s, rise 35 px/s, fade over 1.1 s, 3 on screen at most, others queue. Text such as `-24`, `+30`. Long sentences go away from the canvas (help scroll instead) | count of live pop-ups in the test never above 3 |
| 11 | Damage colours | Hit on a unit `#ff5d6c`. Heavy hit `#ffcf5a` with a starburst. Heal `#62e88a`. Shield block `#5df2ee`. Fence hit `#ffb347`. Ground miss `#b9aecb`. Pickup `#a98bff`. Sign always shown, so colour is never alone | unit test: colour table covers every `floatTexts.push` type |
| 12 | Max text per pop-up | At most 8 Chinese characters or 14 Latin characters. Today's `🛡️ 凌空預判攔截！(0 傷害！防禦餘 N 輪)` becomes `攔截！` / `Blocked!`, the rest is the pip count | script scans strings for length |
| 13 | Emoji | No emoji in canvas text or DOM labels. Icons come from `skill_icons` and plates (emoji look different per system) | grep of source finds none in UI strings |
| 14 | Debug text | Remove `(1號位: x=…)` | grep for `號位` returns nothing |
| 15 | Reduced motion | Under `prefers-reduced-motion: reduce`: no sliding chevrons, no vignette pulse, no ring breathing, banner appears without slide | emulate media in test, nothing animates |
| 16 | Contrast | Plate text `#f6ecd8` on dark. Wind colours on dark plate. Check with a tool, not by eye. Dock numbers in `dock_design.md` are estimates too | contrast script over the palette, 4.5:1 for text under 24 px, 3:1 above |
| 17 | Clean screen | At most 2 pulsing things at once. Plates are 85 % alpha. Wind particles stay out of the keep-out rectangles | wind field `getState()` shows 0 items inside keep-outs; count of pulsing elements in a script |
| 18 | Locale | Every new string has `zh-TW` and `en`. The text for both is kept per the owner log and Kiro task 08. This checkout still hard-codes zh-TW, so the keys below are the contract for task 08 | test: each key present in both tables, none empty |

### d1. String keys (new or changed), zh-TW and English

| Key | zh-TW | English |
|---|---|---|
| `team.me` | 我方 | You |
| `team.agent` | 子代理 | Agents |
| `hud.round` | 第 {n} 回合 | Round {n} |
| `hud.gap` | 距離 {n} | Gap {n} |
| `hud.thinking` | 對手思考中 | Thinking |
| `wind.0` … `wind.5` | 無風 微風 和風 強風 烈風 狂風 | Calm Breeze Gentle Strong Gale Storm |
| `wind.tail` / `wind.head` | 順風 / 逆風 | Tailwind / Headwind |
| `turn.yours` | 你的回合 | Your turn |
| `end.win` | 你贏了！ | You win! |
| `end.lose` | 子代理獲勝 | Agents win |
| `end.restart` | 點一下畫面重新開始 | Click to play again |
| `menu.move` / `menu.attack` / `menu.defend` | 移動 / 攻擊 / 防禦 | Move / Attack / Defend |
| `fx.hit` / `fx.block` / `fx.fence` / `fx.miss` | 命中 / 攔截！ / 圍籬！ / 偏了 | Hit / Blocked! / Fence! / Miss |
| `fx.fence_down` | 圍籬倒了 | Fence down |
| `drop.coming` | 物資來了 | Supply drop |
| `drop.got` | 拿到物資 | Got supply |
| `help.title` | 玩法 | How to play |

## e. Order of work

Eight small steps. The main line does one, tests it, then the next. Steps 4 to 7 can show the old drawing wherever a NEW image has not arrived yet; the code falls back to the current look when an image is missing.

| Step | Work | Pass condition (automatic or screenshot) |
|---|---|---|
| 1 | **Wind constant and scale fixes, no art.** `WIND_ACCEL = 96` in `shared/constants.json`, `index.html` (3 places), both servers (acceleration model), sync test. Replace `wind / 5` and `/ 5` scales. Fix the `-5 to +5` comments | `scripts/test_constants_sync.py` passes with the new key; client-vs-engine landing grid within 3 px; `scripts/test_wind_fx.js` passes; `scripts/eval_agent_learning.py` still improves |
| 2 | **Fonts.** Download the three font files from the URLs in b3, build subsets, add `assets/fonts/`, `css/fonts.css`, the OFL files, the loader promise | Four font files plus three OFL files present; total at most 600 KB; coverage test passes; `document.fonts.check('700 28px "PK Display"', '你的回合')` is true; screenshot of `第 3 回合` and `Round 3` at 28 px approved by the owner |
| 3 | **Text helper and clean-up.** `fs()`, outlined `drawText`, digit-cell numbers. Remove debug coordinates, emoji in canvas text, long pop-ups. No new art | grep: no `ctx.font` below 17 px, no `號位`; `1111` and `8888` draw at equal width; screenshot before and after |
| 4 | **Top HUD.** Team plates, `ui_hp_bar`, pips, centre plate (round, distance, timer ring), move the "?" below the right plate | Screenshot of the top strip at 1400 and 1000 px; `#help-btn` rectangle and right plate rectangle do not intersect (script on `getBoundingClientRect`); the HP bar width equals `hp / maxHp` in a forced-HP test |
| 5 | **Wind indicator and scene wind.** Zone B track and word, `wind_fx.js` wired in `draw()` with keep-outs, sprites for fog and dust (leaves and props when they arrive), flame lean, sound scale | For wind -4, 0, +4: lit sockets 5 / 0 / 5 on the correct side, word and colour match the table; `getState()` shows at most 96 items and none inside a keep-out; draw time added by wind effects stays under 2 ms per frame on average over 300 frames (measured with `performance.now()`) |
| 6 | **Fence, shield slab pips, float texts, trail and rings.** Three fence states switched by `wallHp`, `ui_pip` on the slab, pop-up queue and colours, stardust trail, landing ring | Screenshots with `wallHp` 100, 40, 0: the fence region differs between all three (pixel difference above a threshold); collision test with `wallHp` 0 passes through; at most 3 pop-ups alive; landing ring appears at the impact x |
| 7 | **Dock skin and portrait wiring.** `ui_dock_frame` 9-slice, plates, lock plate, icons, slots; `updateDock` sets `--portrait-img` from `currentHero` | For each of the four heroes `getComputedStyle(.dock-portrait).backgroundImage` is not `none` once the file exists; dock screenshot at 1400, 1000 and 800 px; no overlap between dock and unit tags; Tab order reaches every button |
| 8 | **Drops, overlays, locale.** Ghost carrier, crate, parachute, drop mark, item icons; turn cue, low-HP vignette, KO cut-in, win/lose banner; string table in zh-TW and en | Forced-state screenshots: carrier mid-flight, crate landed, `hp = 25`, `gameOver = "player"` and `"ai"`; banner ignores a click at 0.5 s and accepts one at 1.2 s; every key in section d1 exists in both languages |

Dependencies on Colab art: step 4 needs `ui_top_plate_left/right` (exists) and `ui_hp_bar`, `ui_top_plate_center`, `ui_timer_frame` (NEW). Step 6 needs `env_fence_damaged/broken` (NEW). Step 7 needs the dock art (exists) and `skill_icons`. Step 8 needs the in-progress drop art and `ui_banner`. Order of Colab jobs is in `docs/ui_asset_requests_2.md`.

## Not verified

- No page was rendered; no sizes were measured. The 0.729 scale, text sizes in CSS px, the "?" overlap and the dock top at y 921 are arithmetic from CSS and canvas values.
- The Colab art on Drive was not opened (sizes, aspect, trim colours unknown).
- Whether Cinzel Decorative, Noto Serif TC or Noto Sans TC have working tabular figures. The digit-cell rule avoids the question.
- Subset file sizes are an estimate. `brotli` availability and `file://` font loading were not checked.
- Whether the OFL allows a subset of Noto Sans TC without renaming: I read the license conditions, not the FAQ passage.
- The zh-TW wind words and the English words need an owner read.
- `docs/airdrop_design.md` and `(not published)` were not present, so nothing from them is used.
