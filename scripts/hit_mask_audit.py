#!/usr/bin/env python3
"""Hit-box audit against the real art (owner 2026-11-17: 'how do you prove the hit box is wrong?').
Ground truth: a shot of radius r that touches at least one visible (alpha > 40) pixel of the figure SHOULD count; one that touches none should NOT.
For each hero the figure is drawn at the game's size (220 px high, bottom at ground + 15, centred). A shot centre is tried at every 1 px inside a generous window; the rule under test says 'hit' or 'miss'.
  false hit  = rule says hit, the shot touches no visible pixel     (the owner's complaint: 'I did not hit but it counted')
  false miss = rule says miss, the shot touches a visible pixel     (an attack that overlaps the body but does nothing: the 2026-11-16 bug)
Rules: current = rectangle (half width, height) widened by r;  ellipse = ellipse fitted to the body (90 percent of the pixels) widened by r.
Read-only. Usage: python3 -B scripts/hit_mask_audit.py [--json OUT]. Exit 1 when a picture is missing."""
import argparse, json, os, sys
import cv2, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = {"skeleton": "assets/units/unit_skeleton.png", "wizard": "assets/units/unit_wizard.png", "bat": "assets/units/unit_bat.png", "knight": "assets/units/unit_knight.png",
       "bride": "assets/poses/bride_idle1.png", "reaper": "assets/poses/necro_idle.png", "hag": "assets/units/unit_hag_idle.png"}
HIT = {"reaper": (57, 165)}
RADII = {"cannonball r=0": 0, "spear r=22": 22, "heavy pumpkin r=25": 25}

def run():
    out = {}
    for hero, rel in ART.items():
        im = cv2.imread(os.path.join(ROOT, rel), cv2.IMREAD_UNCHANGED)
        if im is None: print("ERROR: missing " + rel, file=sys.stderr); sys.exit(1)
        k = 220.0 / im.shape[0]; sp = cv2.resize(im, (int(round(im.shape[1] * k)), 220), interpolation=cv2.INTER_AREA)
        mask = (sp[:, :, 3] > 40).astype(np.uint8)
        col = mask.sum(axis=0).astype(float); c = np.cumsum(col); lo, hi = int(np.searchsorted(c, c[-1] * .05)), int(np.searchsorted(c, c[-1] * .95))
        vis_top = int(np.argmax(mask.any(axis=1)))      # first visible row
        # world window relative to the unit: x -160..160, y -260..+40 (y up is negative); art row 0 is at y = -205, centre column at x = 0
        X0, Y0, Wd, Ht = -160, -260, 320, 300
        field = np.zeros((Ht, Wd), np.uint8)
        ox, oy = -(sp.shape[1] // 2) - X0, -205 - Y0
        field[oy:oy + 220, ox:ox + sp.shape[1]] = mask
        dist = cv2.distanceTransform((1 - field).astype(np.uint8), cv2.DIST_L2, 5)   # distance to the nearest visible pixel
        ys, xs = np.mgrid[0:Ht, 0:Wd]; wx, wy = xs + X0, ys + Y0
        hw, hh = HIT.get(hero, (70, 190))
        bcx = (lo + hi) / 2.0 - sp.shape[1] / 2.0; a = (hi - lo) / 2.0; top = -205 + vis_top; b = (0 - top) / 2.0; cy = top + b
        res = {}
        for name, r in RADII.items():
            touch = dist <= r
            rect = (np.abs(wx) <= hw + r) & (wy >= -hh - r) & (wy <= r)
            ell = (((wx - bcx) / (a + r)) ** 2 + ((wy - cy) / (b + r)) ** 2) <= 1.0
            for rn, rule in (("current rect", rect), ("body ellipse", ell)):
                fh = int((rule & ~touch).sum()); fm = int((~rule & touch).sum()); hit = int(rule.sum())
                res[name + " | " + rn] = {"false_hit_pct_of_hits": round(100.0 * fh / max(hit, 1), 1), "false_miss_pct_of_touches": round(100.0 * fm / max(int(touch.sum()), 1), 1)}
        out[hero] = {"half_w_now": hw, "height_now": hh, "body_half_w": round(a, 1), "visible_h": round(-top, 1), "results": res}
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--json"); a = ap.parse_args(); r = run()
    if a.json: json.dump(r, open(a.json, "w"), indent=1)
    for hero, d in r.items():
        print("%-9s now %dx%d  body half-w %.0f  visible h %.0f" % (hero, d["half_w_now"], d["height_now"], d["body_half_w"], d["visible_h"]))
        for k, v in d["results"].items():
            print("   %-34s false hit %5.1f%%   false miss %5.1f%%" % (k, v["false_hit_pct_of_hits"], v["false_miss_pct_of_touches"]))
