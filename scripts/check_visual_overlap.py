#!/usr/bin/env python3
"""What the player SEES against what the page judged (owner 2026-11-18: "the final attack landing point vs the coordinate landing point", "do the hit judgement", "the bottom cannot be hit").
For every recorded step of a spear / flame shot: rasterise the weapon picture the way the page DRAWS it (rotated along the flight, scaled to wLen x wThick and by the 1.35 weapon draw scale, the flame mirrored)
and test it against the target figure's visible pixels (binary mask, the figure placed with the same flip as the hit rule). Then, per shot:
  SEEN_NOT_HIT   the drawn weapon overlapped a visible pixel of the figure at some step but the unit never lost hp
  HIT_NOT_SEEN   the unit lost hp but the drawn weapon never overlapped it
usage: python3 -B scripts/check_visual_overlap.py logs_local/hit_trace/visual.jsonl [--scale 1.35] [--flame-head-shift 0.353]"""
import json, math, os, sys, collections
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from hit_mask_py import HitMasks
ROOT = os.path.dirname(HERE); M = HitMasks()
SCALE = float(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 1.35
HEAD = float(sys.argv[sys.argv.index("--flame-head-shift") + 1]) if "--flame-head-shift" in sys.argv else 0.0   # fraction of wLen the flame picture is moved backwards so its head sits on the shot centre (the page uses 0.353)
SPR = {"proj_spear": "assets/weapons/proj_spear_colab.png", "proj_flame": "assets/fx/sprites/fx_flame_comet.png"}
alpha = {k: np.asarray(Image.open(os.path.join(ROOT, v)).convert("RGBA").getchannel("A")) > 40 for k, v in SPR.items()}
def unit_mask(hero, face_right):
    # the figure as the hit rule sees it: window x0..x0+w, y0..y0+h relative to the feet, mirrored like HitMasks.touches
    rows = M.runs[hero]; a = np.zeros((M.h, M.w), bool)
    for y, rs in enumerate(rows):
        for s, e in rs: a[y, s:e + 1] = True
    fr = face_right
    if M.faces[hero] == "right": fr = not fr
    if fr: a = a[:, ::-1]                        # dx = -dx when the figure is mirrored
    return a
MASKS = {}
def weapon_pixels(weapon, wl, wt, rot):
    a = alpha[weapon]; img = Image.fromarray((a * 255).astype(np.uint8))
    if weapon == "proj_flame": img = img.transpose(Image.FLIP_LEFT_RIGHT)       # the page mirrors it so the head leads
    w = max(2, int(wl * SCALE)); h = max(2, int(wt * SCALE)); img = img.resize((w, h), Image.BILINEAR)
    return np.asarray(img.rotate(-math.degrees(rot), expand=True, resample=Image.BILINEAR)) > 127
def overlap(wp, dx, dy, um):
    # wp: boolean sprite centred at (dx, dy) relative to the unit feet; um: unit mask placed with x0, y0
    hh, ww = wp.shape; ox = int(round(dx - ww / 2.0)) - M.x0; oy = int(round(dy - hh / 2.0)) - M.y0     # top-left of the sprite in the mask grid
    x0, y0 = max(0, ox), max(0, oy); x1, y1 = min(M.w, ox + ww), min(M.h, oy + hh)
    if x0 >= x1 or y0 >= y1: return False
    return bool((wp[y0 - oy:y1 - oy, x0 - ox:x1 - ox] & um[y0:y1, x0:x1]).any())
shots = collections.OrderedDict()
for line in open(sys.argv[1]):
    o = json.loads(line); shots.setdefault((o["hero"], o["tp"], o["ang"], o["pw"], o["x0"]), []).append(o)
cnt = collections.Counter(); by = collections.defaultdict(collections.Counter); ex = collections.defaultdict(list); cache = {}
for key, recs in shots.items():
    hit = any(r["damaged"] for r in recs); seen = False; seen_step = None
    tp = key[1]; um = MASKS.setdefault(tp, unit_mask(tp, False))       # the right-hand team faces left: face_right False
    for r in recs:
        if abs(r["px"] - r["ux"]) > 260 or r["py"] - r["uy"] < -330 or r["py"] - r["uy"] > 70: continue
        rot = math.atan2(r["vy"], r["vx"]); ck = (r["weapon"], round(rot, 2)); wp = cache.get(ck)
        if wp is None: wp = cache[ck] = weapon_pixels(r["weapon"], r["wl"], r["wt"], rot)
        sh = HEAD * r["wl"] * SCALE if r["weapon"] == "proj_flame" else 0.0   # the picture centre trails the shot centre along the flight
        if overlap(wp, r["px"] - r["ux"] - math.cos(rot) * sh, r["py"] - r["uy"] - math.sin(rot) * sh, um): seen = True; seen_step = r["step"]; break
    k = "hit" if hit else "nohit"; cnt[(key[0], k, "seen" if seen else "unseen")] += 1
    if seen and not hit and len(ex["SEEN_NOT_HIT"]) < 6: ex["SEEN_NOT_HIT"].append("%s -> %s ang %d pw %d x0 %d (overlap at step %s)" % (key[0], tp, key[2], key[3], key[4], seen_step))
    if hit and not seen and len(ex["HIT_NOT_SEEN"]) < 6: ex["HIT_NOT_SEEN"].append("%s -> %s ang %d pw %d x0 %d" % (key[0], tp, key[2], key[3], key[4]))
print("draw scale %.2f; shots %d" % (SCALE, len(shots)))
for hero in ("skeleton", "reaper"):
    h = cnt[(hero, "hit", "seen")]; hu = cnt[(hero, "hit", "unseen")]; ns = cnt[(hero, "nohit", "seen")]; nu = cnt[(hero, "nohit", "unseen")]
    print("%-9s judged hit: %d (seen %d, NOT seen %d) | judged miss: %d (seen %d = SEEN_NOT_HIT, unseen %d) -> looks like a hit but no damage: %.0f%% of the shots that visually touched" % (hero, h + hu, h, hu, ns + nu, ns, nu, 100.0 * ns / max(1, h + ns)))
for kind in ("SEEN_NOT_HIT", "HIT_NOT_SEEN"):
    print(kind); [print("   " + e) for e in ex[kind]]
