#!/usr/bin/env python3
"""Binary hit masks: 'a shot counts when its drawn disk touches a visible pixel of the figure inside the decided box' (owner 2026-11-17, replaces the empty corners of the 70 x 190 box).
make:  python3 -B scripts/hit_mask_py.py --make   writes shared/hit_masks.json (the data, run-length encoded) and js/hit_masks.js (the same data plus the same test, for the page).
       Each mask is the visible pixels (alpha > 40) of the figure drawn at the game's size: 220 px high, bottom at ground + 15, centred; window x -130..129, y -230..39 (feet line y = 0).
use:   from hit_mask_py import HitMasks; M = HitMasks(); M.touches('skeleton', dx, dy, r, face_right)   dx, dy = shot centre minus the unit's x, y; r = drawn shot radius.
rule:  a pixel (x, y) counts when (x + 0.5 - cx)^2 + (y + 0.5 - cy)^2 <= (r + 0.7072)^2 (0.7072 = a pixel's far corner), flipped sideways when the figure is mirrored. Pure integers + one sqrt:
       the JS and the Python test give the same answer (pinned by scripts/test_hit_masks.py).
check: python3 -B scripts/hit_mask_py.py --check   compares the rule with a brute-force disk test and prints the box-only false-hit share. Exit 1 on any disagreement."""
import argparse, json, math, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_JSON = os.path.join(ROOT, "shared", "hit_masks.json")
OUT_JS = os.path.join(ROOT, "js", "hit_masks.js")
HEROES = ('skeleton', 'wizard', 'bat', 'knight', 'bride', 'reaper', 'hag', 'hunchback')
X0, Y0, WD, HT = -130, -230, 260, 270
ALPHA_MIN = 40
CORNER = 0.7072

def rle(row):
    out, cur, n = [], row[0], 0
    for v in row:
        if v == cur: n += 1
        else: out.append(n); cur, n = v, 1
    out.append(n); return [row[0]] + out

def runs_of(enc):
    """[(start, end_inclusive)] of the 1-runs of one encoded row."""
    v, pos, out = enc[0], 0, []
    for n in enc[1:]:
        if v == 1: out.append((pos, pos + n - 1))
        pos += n; v ^= 1
    return out

def _page_tables():
    """The tables the page draws its figures with, read from index.html itself (one source): image paths, pose sets, unarmed art, x and foot corrections, which hero faces right."""
    import re
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    def obj(name):
        m = re.search(r"const %s = \{(.*?)\};" % name, src, re.S)
        if not m: raise SystemExit("ERROR: index.html no longer has const %s (hit_mask_py.py reads it)" % name)
        body = re.sub(r"//[^\n]*", "", m.group(1)); out = {}
        for k, v in re.findall(r"(\w+)\s*:\s*([^,}]+)", body):
            v = v.strip()
            out[k] = v.strip('"') if v.startswith('"') else (v == 'true' if v in ('true', 'false') else eval(v, {"__builtins__": {}}, {}))
        return out
    images = dict(re.findall(r'(\w+):\s*"(assets/[^"]+?\.png)"', src))
    sets = {}
    for hero_key, body in re.findall(r"(unit_\w+): \{ ((?:idle|windup|draw)[^}]*)\}", src[src.index("const POSE_SETS"):src.index("const UNARMED_ART")]):
        sets[hero_key] = dict(re.findall(r'(\w+): "(\w+)"', body))
    held = set(re.findall(r"(unit_\w+):\s*\{ img:", src[src.index("const HELD_WEAPON"):src.index("const HAND_RIG")]))
    layered = bool(re.search(r"const USE_LAYERED_HANDS = true;", src))
    return images, sets, obj("UNARMED_ART"), obj("ART_POSE_XFIX"), obj("ART_POSE_FOOT"), obj("ART_FOOT_FIX"), obj("ART_FACES_RIGHT"), (held if layered else set())

def frames_of(hero):
    """The pictures the page shows a hero in while it can be a TARGET, by the page's own draw rule (drawFullArtCharacter), in two states: ARMED (idle: the pose idle of the pose set if it has one, else the weapon-less art when the hero
    holds a layered weapon (skeleton and bat: their base art is never drawn), else the base art; plus the breathing second idle) and UNARMED (the weapon-less art, shown after the throw until the unit's next turn). The hit frame is not
    included: it is drawn only after a hit. Returns {"armed": [(path, x, foot, name)], "unarmed": [...]}; a hero without weapon-less art has the same list twice."""
    images, sets, unarmed, xfix, foot, footfix, _faces, held = _page_tables(); key = "unit_" + hero; ps = sets.get(key, {}); armed = []
    def mk(img_key, x=0.0, f=0.0): return (images[img_key], x, f, img_key) if img_key in images else None
    idle = ps.get("idle")
    if idle: armed.append(mk(idle, xfix.get(idle, 0.0), foot.get(idle, 0.0)))
    elif key in unarmed and key in held: armed.append(mk(unarmed[key]))
    else: armed.append(mk(key, 0.0, footfix.get(key, 0.0)))
    k2 = ps.get("idle2")
    if k2: armed.append(mk(k2, xfix.get(k2, 0.0), foot.get(k2, 0.0)))
    armed = [f for f in armed if f]
    un = [mk(unarmed[key])] if key in unarmed else list(armed)
    def uniq(lst):
        seen, out = set(), []
        for f in lst:
            if f and f[0] not in seen: seen.add(f[0]); out.append(f)
        return out
    return {"armed": uniq(armed), "unarmed": uniq(un)}

def _field(frames):
    import cv2, numpy as np
    field = np.zeros((HT, WD), np.uint8)
    for rel, xf, ft, name in frames:
        im = cv2.imread(os.path.join(ROOT, rel), cv2.IMREAD_UNCHANGED)
        if im is None: print("ERROR: missing " + rel, file=sys.stderr); sys.exit(1)
        k = 220.0 / im.shape[0]; sp = cv2.resize(im, (int(round(im.shape[1] * k)), 220), interpolation=cv2.INTER_AREA)
        mask = (sp[:, :, 3] > ALPHA_MIN).astype(np.uint8)
        ox = -(sp.shape[1] // 2) + int(round(xf * sp.shape[1])) - X0; oy = -205 + int(round(ft * 220)) - Y0   # the page: x = -dw/2 + xFix * dw, y = -h + 15 + foot * h
        x0, y0 = max(ox, 0), max(oy, 0); x1, y1 = min(ox + sp.shape[1], WD), min(oy + 220, HT)
        if x1 > x0 and y1 > y0: field[y0:y1, x0:x1] |= mask[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return field

def make():
    heroes = {}
    faces = _page_tables()[6]
    for hero in HEROES:
        fr = frames_of(hero); a = _field(fr["armed"]); u = _field(fr["unarmed"])
        entry = {"faces": "right" if faces.get("unit_" + hero) else "left", "frames": [f[3] for f in fr["armed"]], "unarmed_frames": [f[3] for f in fr["unarmed"]],
                 "pixels": int(a.sum()), "rows": [rle([int(v) for v in r]) for r in a]}
        if [f[0] for f in fr["armed"]] != [f[0] for f in fr["unarmed"]]: entry["rows_unarmed"] = [rle([int(v) for v in r]) for r in u]
        heroes[hero] = entry
    data = {"window": {"x0": X0, "y0": Y0, "w": WD, "h": HT}, "alpha_min": ALPHA_MIN, "heroes": heroes}
    json.dump(data, open(OUT_JSON, "w"), separators=(",", ":"))
    js = open(os.path.join(ROOT, "scripts", "hit_mask_template.js")).read().replace("/*DATA*/null", json.dumps(data, separators=(",", ":")))
    open(OUT_JS, "w").write(js)
    print("wrote shared/hit_masks.json (%d bytes) and js/hit_masks.js (%d bytes); two states for: %s" % (os.path.getsize(OUT_JSON), os.path.getsize(OUT_JS), [h for h, v in heroes.items() if "rows_unarmed" in v]))

class HitMasks:
    def __init__(self, path=OUT_JSON):
        d = json.load(open(path)); w = d["window"]; self.x0, self.y0, self.w, self.h = w["x0"], w["y0"], w["w"], w["h"]
        self.faces = {h: v["faces"] for h, v in d["heroes"].items()}
        self.runs = {h: [runs_of(r) for r in v["rows"]] for h, v in d["heroes"].items()}
        self.runs_unarmed = {h: [runs_of(r) for r in v["rows_unarmed"]] for h, v in d["heroes"].items() if "rows_unarmed" in v}
    def has(self, hero): return hero in self.runs
    def touches(self, hero, dx, dy, r, face_right, armed=True):
        if self.faces[hero] == "right": face_right = not face_right
        if face_right: dx = -dx                      # art drawn facing left; a figure facing right is the mirror image
        cx, cy = dx - self.x0, dy - self.y0; rr = (r + CORNER) ** 2
        y_lo, y_hi = max(0, int(math.floor(cy - r - 1))), min(self.h - 1, int(math.ceil(cy + r + 1)))
        rows = self.runs_unarmed[hero] if (not armed and hero in self.runs_unarmed) else self.runs[hero]
        for y in range(y_lo, y_hi + 1):
            ddy = (y + 0.5 - cy) ** 2
            if ddy > rr: continue
            s = math.sqrt(rr - ddy); xl = max(0, math.ceil(cx - s - 0.5)); xr = min(self.w - 1, math.floor(cx + s - 0.5))
            if xl > xr: continue
            for a, b in rows[y]:
                if a <= xr and b >= xl: return True
        return False

def check():
    import numpy as np
    M = HitMasks(); bad = shots = old_hit = old_false = 0
    for hero in M.runs:
        f = np.zeros((M.h, M.w), np.uint8)
        for y, rs in enumerate(M.runs[hero]):
            for a, b in rs: f[y, a:b + 1] = 1
        py, px = np.nonzero(f); hw, hh = (57, 165) if hero == "reaper" else (70, 190)
        for r in (0, 22, 25):
            for dx in range(-110, 111, 6):
                for dy in range(-215, 35, 6):
                    cx, cy = dx - M.x0, dy - M.y0
                    ref = bool((((px + 0.5 - cx) ** 2 + (py + 0.5 - cy) ** 2) <= (r + CORNER) ** 2).any())
                    got = M.touches(hero, dx, dy, r, False if M.faces[hero] == "left" else True)
                    shots += 1; bad += got != ref
                    if abs(dx) <= hw + r and -hh - r <= dy <= r: old_hit += 1; old_false += (not got)
    print("shots %d  disagreements with brute force %d  | box alone: %d hits, %.1f%% touch no visible pixel (box AND mask: 0 by construction)" % (shots, bad, old_hit, 100.0 * old_false / max(old_hit, 1)))
    return 1 if bad else 0

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--make", action="store_true"); ap.add_argument("--check", action="store_true"); a = ap.parse_args()
    if a.make: make()
    if a.check: sys.exit(check())
