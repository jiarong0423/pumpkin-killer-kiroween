#!/usr/bin/env python3
"""Data only (no rendering): how much of each thrown weapon's picture box is visible, against the disk the hit rule uses.
The page counts a shot when a disk of radius hitR = max(0, sqrt(wLen * wThick) / 2 - 20) around the shot centre touches a visible pixel of the figure inside the decided box (index.html projHitRadius).
This prints, per weapon, the picture's visible (alpha > 40) bounding box and radius, and how far the disk reaches beyond the visible weapon (phantom reach). Writes logs_local/hit_trace/weapon_extent.json."""
import json, os, re, sys, math
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
paths = {k: re.search(r'\b%s: "(assets/[^"]+)"' % k, src).group(1) for k in ["proj_spear", "proj_shuriken", "proj_flame", "proj_cross", "proj_axe", "proj_shield"]}
sizes = {}
for m in re.finditer(r"weapon: \"(\w+)\",.*?wLen: (\d+), wThick: (\d+)", src, re.S):
    sizes.setdefault(m.group(1), (int(m.group(2)), int(m.group(3))))
out = {}
for w, rel in paths.items():
    im = Image.open(os.path.join(ROOT, rel)).convert("RGBA"); W, H = im.size; a = im.getchannel("A").point(lambda v: 255 if v > 40 else 0)
    bb = a.getbbox() or (0, 0, 0, 0); wl, wt = sizes.get(w, (W, H))
    sx, sy = wl / W, wt / H                                  # picture pixels to game pixels
    vis_w, vis_h = (bb[2] - bb[0]) * sx, (bb[3] - bb[1]) * sy
    cx, cy = (bb[0] + bb[2]) / 2 * sx - wl / 2, (bb[1] + bb[3]) / 2 * sy - wt / 2
    hitR = max(0.0, math.sqrt(wl * wt) / 2 - 20)
    # the farthest visible pixel from the picture centre, in game pixels (the weapon spins, so this is the true drawn radius)
    px = a.load(); far = 0.0
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            if px[x, y]:
                d = math.hypot((x - W / 2) * sx, (y - H / 2) * sy); far = max(far, d)
    cover = sum(1 for y in range(H) for x in range(W) if px[x, y]) / float(W * H)
    out[w] = {"picture_px": [W, H], "game_box": [wl, wt], "visible_box_game_px": [round(vis_w, 1), round(vis_h, 1)], "visible_centre_offset": [round(cx, 1), round(cy, 1)], "visible_fill_of_box": round(cover, 3), "farthest_visible_pixel_game_px": round(far, 1), "hitR_used": round(hitR, 1), "disk_beyond_visible_px": round(hitR - far, 1)}
os.makedirs(os.path.join(ROOT, "logs_local", "hit_trace"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "logs_local", "hit_trace", "weapon_extent.json"), "w"), indent=1)
print("%-14s %-13s %-14s %-9s %-9s %-8s %s" % ("weapon", "game box", "visible box", "fill", "farthest", "hitR", "disk beyond visible (px)"))
for w, d in out.items():
    print("%-14s %-13s %-14s %-9s %-9s %-8s %+.1f" % (w, "x".join(map(str, d["game_box"])), "x".join(map(str, d["visible_box_game_px"])), d["visible_fill_of_box"], d["farthest_visible_pixel_game_px"], d["hitR_used"], d["disk_beyond_visible_px"]))
