#!/usr/bin/env python3
"""Reference pictures for the owner's Gemini jobs (2026-11-18): contact sheets of the EXISTING art (style, maps, portraits, poses, effects) so the generator can match the look.
Writes docs/gemini_refs_20261118/*.png and README.md. Data only: reads assets/, writes only that folder. usage: python3 -B scripts/make_gemini_refs.py"""
import os, glob
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "gemini_refs_20261118"); os.makedirs(OUT, exist_ok=True)
BG = (18, 10, 34)
def load(p):
    return Image.open(os.path.join(ROOT, p)).convert("RGBA")
def sheet(items, cols, cell, name, label=True, pad=10):
    rows = (len(items) + cols - 1) // cols; lab = 18 if label else 0
    W = cols * (cell + pad) + pad; H = rows * (cell + lab + pad) + pad
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    for i, (path, title) in enumerate(items):
        x = pad + (i % cols) * (cell + pad); y = pad + (i // cols) * (cell + lab + pad)
        a = load(path); a.thumbnail((cell, cell), Image.LANCZOS)
        ox = x + (cell - a.width) // 2; oy = y + (cell - a.height) // 2
        im.paste(a, (ox, oy), a)
        if label: d.text((x, y + cell + 2), title[:44], fill=(210, 200, 240))
    im.save(os.path.join(OUT, name)); return name, im.size
made = []
fx = [("assets/fx/sprites/fx_cross_silver.png", "fx_cross_silver (new)"), ("assets/fx/sprites/fx_sonic_ring.png", "fx_sonic_ring"), ("assets/fx/sprites/fx_rune_circle.png", "fx_rune_circle"),
      ("assets/fx/sprites/fx_ghost_puff.png", "fx_ghost_puff"), ("assets/fx/sprites/fx_spirit_mist.png", "fx_spirit_mist"), ("assets/fx/sprites/fx_stardust.png", "fx_stardust"),
      ("assets/fx/sprites/fx_flame_comet.png", "fx_flame_comet"), ("assets/fx/sprites/fx_impact_flash.png", "fx_impact_flash"), ("assets/fx/sprites/fx_heal_rain_drop.png", "fx_heal_rain_drop")]
made.append(sheet([i for i in fx if os.path.exists(os.path.join(ROOT, i[0]))], 3, 360, "ref_style_effects.png"))
maps = [("assets/env/bg_graveyard.png", "bg_graveyard"), ("assets/env/bg_belltower.png", "bg_belltower"), ("assets/env/bg_ruined_church.png", "bg_ruined_church"), ("assets/env/bg_abandoned_school.png", "bg_abandoned_school")]
made.append(sheet(maps, 2, 700, "ref_maps_current.png"))
bg = load("assets/env/bg_graveyard.png"); w, h = bg.size; strip = bg.crop((0, int(h * 0.76), w, h)).convert("RGB"); strip.thumbnail((1800, 400)); strip.save(os.path.join(OUT, "ref_ground_strip_crop.png")); made.append(("ref_ground_strip_crop.png (the bottom 24 percent of bg_graveyard %dx%d)" % (w, h), strip.size))
ports = [("assets/portraits/%s_front.png" % r, r) for r in ("skeleton", "wizard", "knight", "reaper", "bride", "hunchback", "hag")] + [("assets/units/unit_bat.png", "bat unit (no portrait yet)"), ("assets/avatars/avatar_bat.png", "bat avatar")]
made.append(sheet(ports, 5, 330, "ref_portraits_and_bat.png"))
for role in ("skeleton", "reaper", "hag", "knight", "bat"):
    files = sorted(glob.glob(os.path.join(ROOT, "assets", "poses", role + "_*.png")))
    items = [(os.path.relpath(f, ROOT), os.path.basename(f).replace(".png", "")) for f in files if not f.endswith("_raw.png")]
    if items: made.append(sheet(items, 5, 230, "ref_poses_%s.png" % role))
readme = """# Reference pictures for Gemini (2026-11-18)

These sheets are made from the art that already exists (script `scripts/make_gemini_refs.py`), so a generated picture can copy the look. Upload the sheet(s) listed for an item together with its prompt.
Common style: flat dark-fantasy 2D cartoon, thick clean near-black contour, thin warm or cool outer glow, flat three-tone shading, soft highlights, chibi faces, isolated sprite on a solid magenta (#FF00FF) or transparent background, 8 to 10 percent margin. No photo look, no 3D or plastic shine, no text.

| item | size | upload these references | prompt |
|---|---|---|---|
| ground strip | 2808 x 260 | ref_ground_strip_crop.png, ref_maps_current.png | "A seamless horizontal ground strip for a night graveyard artillery game: cracked grey stone path with a little grass, moss, small candles and bones at the edges, flat dark-fantasy cartoon, same palette as the reference, the top edge irregular and clean, the strip tiles left to right without a visible seam, no characters, no text." |
| wide map | 2808 x 1080 | ref_maps_current.png | "A wide 21:9-style night backdrop for the same game: a haunted graveyard with a moonlit gothic castle on the right, twisted trees, gravestones, green and blue ghost fire, low mist, the lower 24 percent calm and flat so a ground strip can sit on it, same painterly cartoon style as the references, no characters, no text." |
| bat portrait | same as the other portraits (705 x 978) | ref_portraits_and_bat.png | "Front portrait of the cat-bat assassin (black cat with bat wings, cyan and orange accents, as in the bat unit picture), same pose framing, outline and glow as the seven portraits in the sheet, transparent or magenta background." |
| missing poses | 1024 x 1024 each | ref_poses_<role>.png of that role | "The same character, same size and framing as the other poses in the sheet, in the pose <name> (windup / charge2 / release / hit / empty / idle1), same outline and colours, magenta background." Poses wanted: skeleton windup, charge2, release, hit; reaper windup, charge2, release, hit, empty; hag idle1, windup, empty; knight windup; bat charge1, charge2. |
| axe slash arc | 512 x 512 | ref_style_effects.png | "A single white crescent slash arc, thick at the middle and tapering to points, soft glow, white on transparent so it can be tinted, centred." |
| heal pulse ring | 512 x 512 | ref_style_effects.png | "A soft white ring with small plus-shaped sparkles around it, glowing, white on transparent so it can be tinted green, centred." |
| ultimate aura disk | 512 x 512 | ref_style_effects.png | "A soft white radial aura disk with faint rotating light rays and a bright core, white on transparent so it can be tinted per role colour, centred." |

Delivery: PNG with transparency (or magenta background: the main line keys it out), file names as in `docs/GEMINI_GENERATION_LIST_20261118.md`, put them anywhere under Downloads and tell the main line the folder.
"""
open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write(readme)
for n, sz in made: print(n, sz)
