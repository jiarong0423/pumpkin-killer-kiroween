# Layout, art and hit-box methods: consolidated (2026-11-17)

Sources: three web research reports (about 60 distinct pages, each tagged read or secondhand in the reports kept in the session scratchpad) plus the repository measurements in `docs/LAYOUT_REBUILD_RECORD_20261117.md` and `scripts/layer_grid.py`. Honest gap: no published number exists for the share of screen height a bottom bar should take, no master-canvas width for ultrawide, and no developer source for Worms, Angry Birds or GunBound hit boxes. Those numbers below are our own design choices.

## 1. Layout (HUD and bottom dock)
| finding | source kind | what we do |
|---|---|---|
| Keep height, widen the stage, centre the fixed-design HUD block, fill extra width with scenery, no black bars; test 16:9, 19:9, 20:9, 4:3 | Android game docs (letterboxing, Defold form factors), Godot keep_height / expand | already our model (height fixed, width up to 2.6); add 4:3 and 21:9 to the measured set |
| Anchor interactive UI to the safe edge, read insets at runtime (`env(safe-area-inset-*)`, `visualViewport`, `dvh`) | MDN, Apple HIG, Unity | keep; the foldable path stays untouched |
| Touch floor 44 pt (Apple), 48 dp / 48 css px with 8 px spacing (Google, web.dev), 24 px WCAG minimum; keep the drawn control small but enlarge the invisible hit area | platform docs, WCAG | the skill button is 44 css px at scale 1 but 31 px at a 300 px stage: keep the drawing proportional and give the button a 44 px invisible hit area (CSS `::before` inset) instead of a bigger bar |
| Bottom bar share of height | NOT FOUND (Fortnite docs: no cap; only "key controls in the lower half", 5 to 6 controls) | our number: 52 + 6 of 430 = 13.5 percent; feet line at 81 percent, so 5 percent of calm space between feet and bar |
| One design block scaled as one picture | engine docs (CanvasScaler, Phaser FIT) | done: `css/dock_stage.css` (52 px design bar, scale = stage height / 430, width = 84 percent of the stage / scale) |

## 2. Art that must not deform
| finding | source kind | what we do |
|---|---|---|
| Slice corners are used once, never tiled; middle: `repeat` clips the last tile, `round` rescales one axis, `space` leaves gaps; size by width/height, not by Transform scale | MDN border-image-*, Unity and Pixi 9-slice, Godot NinePatchRect | done for the bar: 112 px caps, 104 px repeating middle (`repeat`) |
| Stretching one band to a wider screen is a non-uniform scale | Phaser/Godot docs | ground strip must be drawn 1:1 at 2808 x 260, not 1920 x 260 stretched; the old art (4:1 drawn 7.4:1) is 54 percent high |
| Hades: designed for 16:9 plus special edge art for 3440 x 1440 | developer reply (the only shipped example read) | map master 2808 x 1080 with the centre 1920 untouched; above 2.6 a declared cap |
| Mirrored edges: nothing authoritative; outpainting risks landmark drift and seams | vendor blog | replace the mirror by the new 444 px side art (Colab spec); keep the mirror only as a fallback |

## 3. Hit boxes
| finding | source kind | what we do |
|---|---|---|
| Inflate the SHOT or sweep it, do not inflate the target (sphere cast with a slightly larger radius) | Naughty Dog GDC 2024 notes | our shot radius (`projHitRadius`) is the right idea; the TARGET box is the part that is too wide |
| Circle or ellipse radius about 0.85 of the half width; target inside the art | KidsCanCode, DDNet (28 of 32), Celeste forgiveness 2 to 5 px | target = ellipse fitted to the measured body (half width 47 to 64, height 175 to 196), not a 140 x 190 rectangle |
| Inner two thirds = full hit, outer ring = graze at half damage (the only numeric crit-zone rule found) | Underrail devlog | optional: graze band instead of a hard edge; head zone stays the top quarter |
| Complaints: hits on empty air, visible misses that score, effects drawn late or off the spot | Overwatch forum, Kotaku, ShellShock Live thread, Riot hit-registration post | this is the owner's report ("did not hit but counted"); measured gap 16 to 23 px per side for five heroes |
| Players like their own box smaller and the enemy's slightly larger | critpoints, shmup design notes | our game is symmetric (both sides computer or player): keep symmetric |

## 4. Proposed order (layer by layer, the owner looks at each)
1. Hit judgment: measured ellipse per hero in ONE place (`shared/heroes.json`), frontend and the Python and JS twins read it; fix the reaper head line (165 vs 190) and the heavy-shot radius (frontend 25 px, backend 0). Needs the 10k verification run in the owner's terminal (resource gate first).
2. Bottom bar: the 44 px invisible hit area; add 4:3 and 21:9 to the measured set.
3. Ground strip 2808 x 260, then wide map 2808 x 1080 (Colab, after the owner's go on size and style).
4. Movement range behind the back unit (zone 240 today): a number from the owner.
