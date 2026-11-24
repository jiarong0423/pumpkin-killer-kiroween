# Colab spec: wide map and ground strip (draft, nothing generated yet)

Owner rule: before any external generation, a screenshot of the current state + size + style are written down. The current state is in `scripts/layer_grid.py` (OpenCV layers, phone view 2340x1080 = world 1920 + 210 each side). Run it to regenerate the four layer pictures: `python3 -B scripts/layer_grid.py --out <dir>`.

## Why these two pictures
| picture | today | problem | evidence |
|---|---|---|---|
| ground strip | `assets/env/ground_strip.png` 1536x384 (4:1), drawn 1920x260 | height squashed to 54 percent: pumpkins, candles and stones are flat | `layer_report.json` `ground_strip.vertical_squash` 0.542 |
| map | `bg_*.png` 1536x864 (16:9) in the 1920 core, mirrored at the sides on wide phones | at 2.17 the mirrored sides are 18 percent of the width, at 2.6 buildings repeat | inventory_map report |

## Spec 1: ground strip
- Size: **2808 x 260** (10.8:1), drawn 1:1 with no scaling, so it also covers the wide-phone sides (research C: stretching a 1920 band to 2808 would be a 1.46x non-uniform scale; the current 1920 band leaves the 210 px sides without a floor in the layer pictures). The walkable slab sits in the TOP 260 px, nothing important below. The old 4:1 art drawn at 7.4:1 is what squashes the props (height 54 percent).
- Content: cracked stone slab edge seen from the front, a few pumpkins, candles and stones at the two far ends (x < 330 and x > 1590 of 1920), the middle 1260 px calm so shots and the dock read clearly. The slab top edge should sit at y = 40 inside the strip (world y 860) so the units' feet line (world 875) is ON the slab, not above it.
- Style: same as the current scene art (deep blue-violet, restrained orange, cyan ghost fire), outlined cartoon, no new characters.
- Reference: the current `ground_strip.png` for palette and props; `(not published)` for the layout sketches.

## Spec 2: wide map
- Size: **2808 x 1080** (aspect 2.6, the JS maximum), centre 1920 px keeps today's composition (same horizon, same landmarks), the outer 444 px each side is NEW scenery (not a mirror).
- Calm zones: top band (y < 14 percent) for the HUD, bottom band (y > 81 percent) for the dock, the outer 8 percent of the 1920 core.
- Horizon: graveyard 0.78, church 0.81, school 0.76 of the height (belltower tilts 0.76 to 0.60: ask for a level horizon at 0.78).
- Four scenes: graveyard, belltower, church, school. Prompts of the last three: `colab/jobs_scenes_20261115.json`; the graveyard prompt was not found, its finished picture is `(not published)`.
- Draw code change after the art exists: `drawImage(bg, 0, 0, W, H)` becomes a centre-crop of the wide picture and the mirror block is removed.

## Order (layer by layer, the owner looks at each)
1. Map layer (Spec 2), one scene first (graveyard). 2. Ground strip (Spec 1). 3. Stand and hit layer from the new ground line. 4. Bottom bar (done as a candidate). 5. Top HUD.

## Not started
No Colab job has been opened or queued. Opening one needs the owner's Colab session and a go for the size and style above.
