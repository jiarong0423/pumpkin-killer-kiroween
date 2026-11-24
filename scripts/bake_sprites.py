#!/usr/bin/env python3
"""Bake animation sprite sheets from one idle image per unit.

Usage: bake_sprites.py <units_dir> <params.json> <out_dir> [teams]

Every unit PNG (RGBA, transparent background, facing right) is normalised to
one height, recoloured per team, pivoted at its feet, and transformed per
frame (scale, rotate, offset, fade, white flash). A glowing team ring is drawn
under the feet. Loop states sample t in [0, 1) so the first frame equals the
frame that would follow the last one; one-shot states sample t in [0, 1] so
they start at idle and end on their final pose.

teams is a comma separated list, default "red,white".
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CELL = 256
BASE_H = 200
FEET_Y = 236
RING_RGB = {"red": (255, 64, 64), "white": (245, 245, 255)}


def ease(t):
    return t * t * (3 - 2 * t)


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def pose(state, t):
    p = {"sx": 1.0, "sy": 1.0, "rot": 0.0, "dx": 0.0, "dy": 0.0, "alpha": 1.0, "flash": 0.0}
    s = math.sin(2 * math.pi * t)
    if state == "idle":
        p["sy"] = 1 + 0.02 * s
        p["sx"] = 1 - 0.01 * s
    elif state == "move_forward":
        p["rot"] = -5 + 1.5 * s
        p["dx"] = 2 * s
        p["dy"] = -5 * abs(math.sin(4 * math.pi * t))
    elif state == "move_back":
        p["rot"] = 5 + 1.5 * s
        p["dx"] = -2 * s
        p["dy"] = -5 * abs(math.sin(4 * math.pi * t))
    elif state == "arm_charge":
        e = ease(t)
        p["rot"] = 20 * e
        p["dx"] = -25 * e
        p["dy"] = 8 * e
        p["sy"] = 1 - 0.12 * e
        p["sx"] = 1 + 0.08 * e
    elif state == "arm_throw":
        if t < 0.30:
            u = ease(t / 0.30)
            p["rot"] = 20 - 42 * u
            p["dx"] = -25 + 65 * u
            p["dy"] = 8 - 14 * u
            p["sy"] = 0.88 + 0.22 * u
            p["sx"] = 1.08 - 0.14 * u
        elif t < 0.45:
            w = (t - 0.30) / 0.15
            shake = math.sin(w * math.pi * 3) * (1 - w) * 5
            p["rot"] = -22 + shake
            p["dx"] = 40 - shake * 0.5
            p["dy"] = -6
            p["sy"] = 1.05
            p["sx"] = 0.96
        else:
            v = ease((t - 0.45) / 0.55)
            p["rot"] = -22 * (1 - v)
            p["dx"] = 40 * (1 - v)
            p["dy"] = -6 * (1 - v)
            p["sy"] = 1.05 - 0.05 * v
            p["sx"] = 0.96 + 0.04 * v
    elif state == "hit_react":
        k = math.sin(math.pi * t)
        p["dx"] = -12 * k
        p["rot"] = 10 * k
        p["flash"] = max(0.0, 1 - t * 3.5)
    elif state == "defend":
        e = ease(min(t * 2, 1.0))
        p["sy"] = 1 - 0.12 * e
        p["sx"] = 1 + 0.05 * e
    elif state == "die":
        e = ease(t)
        p["rot"] = 80 * e
        p["dx"] = 58 * e
        p["dy"] = -50 * e
        p["sx"] = 1 - 0.3 * e
        p["sy"] = 1 - 0.3 * e
        p["alpha"] = 1 - clamp((t - 0.3) / 0.7) ** 1.5
    else:
        raise ValueError("unknown state: " + state)
    return p


def recolor(sprite, team):
    """Shift the purple/blue parts, the cyan flames and the dark armour to the team palette."""
    alpha = sprite.split()[3]
    hsv = np.array(sprite.convert("RGB").convert("HSV")).astype(np.float32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    purple = (h >= 165) & (h <= 225) & (s >= 60)
    cyan = (h >= 110) & (h <= 150) & (s >= 80)
    dark = (v < 100) & ~purple
    if team == "red":
        h[purple] = 0
        h[cyan] = 8
        h[dark] = 0
        s[dark] = np.maximum(s[dark], 130)
        v[dark] = np.minimum(255, v[dark] * 1.1)
    elif team == "white":
        s[purple] = s[purple] * 0.1
        v[purple] = np.minimum(255, v[purple] * 1.5 + 35)
        s[dark] = s[dark] * 0.1
        v[dark] = np.minimum(255, v[dark] * 1.8 + 30)
    else:
        raise ValueError("unknown team: " + team)
    out = Image.fromarray(np.stack([h, s, v], axis=-1).astype(np.uint8), "HSV").convert("RGB").convert("RGBA")
    out.putalpha(alpha)
    return out


def make_ring(team):
    rgb = RING_RGB[team]
    layer = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    box = (CELL // 2 - 58, FEET_Y - 9, CELL // 2 + 58, FEET_Y + 8)
    d.ellipse(box, fill=rgb + (70,), outline=rgb + (230,), width=4)
    glow = layer.filter(ImageFilter.GaussianBlur(3))
    return Image.alpha_composite(glow, layer)


def render(sprite, p, ring):
    w, h = sprite.size
    k = BASE_H / h
    sw = max(1, int(w * k * p["sx"]))
    sh = max(1, int(h * k * p["sy"]))
    img = sprite.resize((sw, sh), Image.LANCZOS)
    big = Image.new("RGBA", (CELL * 2, CELL * 2), (0, 0, 0, 0))
    big.paste(img, (CELL - sw // 2, CELL - sh), img)
    big = big.rotate(p["rot"], resample=Image.BICUBIC, center=(CELL, CELL))
    left = CELL - (CELL // 2 + int(round(p["dx"])))
    top = CELL - (FEET_Y + int(round(p["dy"])))
    frame = big.crop((left, top, left + CELL, top + CELL))
    alpha = frame.split()[3]
    if p["flash"] > 0:
        white = Image.new("RGBA", frame.size, (255, 255, 255, 255))
        frame = Image.blend(frame, white, p["flash"])
    if p["alpha"] < 1:
        alpha = alpha.point(lambda v: int(v * p["alpha"]))
    frame.putalpha(alpha)
    base = ring.copy()
    if p["alpha"] < 1:
        base.putalpha(base.split()[3].point(lambda v: int(v * p["alpha"])))
    return Image.alpha_composite(base, frame)


def bake(units_dir, params_path, out_dir, teams):
    with open(params_path, encoding="utf-8") as fh:
        params = json.load(fh)
    os.makedirs(out_dir, exist_ok=True)
    manifest = {"cell": CELL, "fps": params["fps"], "feet": [CELL // 2, FEET_Y], "teams": teams, "units": {}}
    names = sorted(f for f in os.listdir(units_dir) if f.startswith("unit_") and f.endswith(".png") and "_raw" not in f)
    if not names:
        print("ERROR no unit PNG found in " + units_dir, file=sys.stderr)
        return 2
    rings = {t: make_ring(t) for t in teams}
    for name in names:
        unit = name[:-4]
        base = Image.open(os.path.join(units_dir, name)).convert("RGBA")
        box = base.getbbox()
        if box is None:
            print("ERROR empty image " + name, file=sys.stderr)
            return 2
        base = base.crop(box)
        manifest["units"][unit] = {}
        for team in teams:
            sprite = recolor(base, team)
            manifest["units"][unit][team] = {}
            for state, spec in params["states"].items():
                n = spec["frames"]
                loop = spec["loop"]
                sheet = Image.new("RGBA", (CELL * n, CELL), (0, 0, 0, 0))
                for i in range(n):
                    t = i / n if loop else i / (n - 1)
                    sheet.paste(render(sprite, pose(state, t), rings[team]), (i * CELL, 0))
                fname = "%s_%s_%s.png" % (unit, team, state)
                sheet.save(os.path.join(out_dir, fname))
                manifest["units"][unit][team][state] = {"file": fname, "frames": n, "loop": loop}
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    total = sum(len(s) for v in manifest["units"].values() for s in v.values())
    print("OK baked %d sheets for %d units x %d teams" % (total, len(names), len(teams)))
    return 0


if __name__ == "__main__":
    if len(sys.argv) not in (4, 5):
        print("usage: bake_sprites.py <units_dir> <params.json> <out_dir> [teams]", file=sys.stderr)
        sys.exit(2)
    team_list = (sys.argv[4] if len(sys.argv) == 5 else "red,white").split(",")
    for tm in team_list:
        if tm not in RING_RGB:
            print("ERROR unknown team " + tm, file=sys.stderr)
            sys.exit(2)
    sys.exit(bake(sys.argv[1], sys.argv[2], sys.argv[3], team_list))
