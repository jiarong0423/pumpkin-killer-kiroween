#!/usr/bin/env python3 -B
"""Does the drawn art line up with the judged hit box? Numbers, not screenshots.

Draw rule (index.html drawFullArtCharacter, read): the picture is drawn dw = 220 * aspect wide and 220 high, centred on the unit's x, its bottom edge 15 px below the feet line
(+ ART_FOOT_FIX * 220 for the reaper): left = -dw/2, top = -220 + 15 + foot_fix, relative to (unit.x, feet y).
Hit box (shared/heroes.json, index.html): |dx| <= 70 (reaper 57), from 190 (reaper 165) above the feet down to the feet.
For every hero idle picture this measures where the opaque pixels (alpha > 40) fall relative to the box: share of pixels inside the box, extent beyond the box on each side.
Weapons held in the picture stick out of the box by design (the projectile radius widens the real reach), so the share inside is a measure, not a pass/fail except for the head and torso rows.
Writes docs/ART_VS_HITBOX_20261117.md and logs_local/probe_art_vs_hitbox.log. Exit 1 if a picture is missing.
"""
import os, re, sys, logging
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(ROOT, "logs_local"), exist_ok=True)
logging.basicConfig(filename=os.path.join(ROOT, "logs_local", "probe_art_vs_hitbox.log"), level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
UNIT = 220
FOOT_FIX = {"unit_reaper": 66 / 1024}
BOX = {"reaper": (57, 165)}
HEROES = ["skeleton", "wizard", "bat", "knight", "reaper", "bride", "hunchback", "hag"]

def main():
    page = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    rows, bad = [], 0
    for h in HEROES:
        key = "unit_" + h
        m = re.search(r"\b" + key + r': "(assets/[^"]+\.png)"', page)
        if not m:
            logging.error("ERROR no picture path for %s", key); bad += 1; continue
        path = os.path.join(ROOT, m.group(1))
        if not os.path.exists(path):
            logging.error("ERROR missing %s", path); bad += 1; continue
        im = Image.open(path).convert("RGBA")
        w, hgt = im.size
        aspect = w / hgt
        dw = UNIT * aspect
        foot = FOOT_FIX.get(key, 0) * UNIT
        half, height = BOX.get(h, (70, 190))
        a = im.split()[3].point(lambda v: 255 if v > 40 else 0)
        px = a.load()
        total = inside = 0
        minx, maxx, miny, maxy = 1e9, -1e9, 1e9, -1e9
        left_out = right_out = top_out = 0.0
        for yy in range(0, hgt, 2):
            wy = -UNIT + 15 + foot + (yy + 0.5) / hgt * UNIT   # world y relative to the feet line (negative = above)
            for xx in range(0, w, 2):
                if px[xx, yy] == 0:
                    continue
                wx = -dw / 2 + (xx + 0.5) / w * dw
                total += 1
                minx, maxx, miny, maxy = min(minx, wx), max(maxx, wx), min(miny, wy), max(maxy, wy)
                if abs(wx) <= half and -height <= wy <= 0:
                    inside += 1
        share = 100.0 * inside / max(1, total)
        rows.append("| %s | %dx%d | %.0f | %.0f to %.0f | %.0f to %.0f | %d x %d | %.1f%% |" % (h, w, hgt, dw, minx, maxx, -maxy, -miny, half * 2, height, share))
        logging.info("%s share inside %.1f%% x %.0f..%.0f y %.0f..%.0f", h, share, minx, maxx, miny, maxy)
    if bad:
        print("ERROR missing pictures:", bad); return 1
    md = ["# Drawn art versus the hit box (2026-11-17)", "", "Method and draw rule: header of `scripts/probe_art_vs_hitbox.py` (numbers from the page's own draw code, the 1024 px pictures and the box in `shared/heroes.json`). Unit 220, feet line y = 0, centre x = 0, box 140 x 190 (reaper 114 x 165).", "",
          "| Hero | Picture | Drawn width | Art x range (opaque pixels) | Art height above the feet (low to high) | Box (width x height) | Share of the art inside the box |", "|---|---|---|---|---|---|---|"] + rows + ["", "The share is below 100 percent because the held weapon, cape and hood stick out sideways and the picture is drawn 15 px below the feet line; the hit reach adds the projectile radius on top of the box (see `docs/HIT_RANGE_MEASURED_20261117.md`)."]
    open(os.path.join(ROOT, "docs", "ART_VS_HITBOX_20261117.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("OK wrote docs/ART_VS_HITBOX_20261117.md")
    return 0

if __name__ == "__main__":
    sys.exit(main())
