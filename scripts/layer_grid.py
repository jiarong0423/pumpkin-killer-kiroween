#!/usr/bin/env python3
"""Layer-by-layer scene composer with an OpenCV measuring grid (owner 2026-11-17: 'place objects layer by layer, use OpenCV for the grid, cut the phone proportion').

Layers (each written as its own PNG, phone view = world 1920x1080 plus PAD each side, aspect 932/430):
  1 map     the scene picture, drawn uniformly x1.25 into the 1920 core, mirrored sides (what the game does today)
  2 ground  + ground strip as drawn today (1920x260 at y = GROUND_Y-40) and, dashed, at its native 4:1 ratio; baseline 860 and feet 875
  3 units   + the six units at their start slots, with the REAL silhouette (OpenCV contour of the art alpha) next to the current hit box
  4 dock    + the dock bar picture at its design size (820x52 in a 390-high stage, scaled to world units)
It also prints and saves the measured numbers (silhouette box, body width holding 90 percent of the pixels) as JSON.
Read-only on the repository; outputs go to --out. Usage: python3 -B scripts/layer_grid.py --out DIR [--aspect 2.167]
Exit code 1 when a picture is missing."""
import argparse, json, os, sys
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, GROUND_Y, FEET = 1920, 1080, 860, 875
ART = {"skeleton": "assets/units/unit_skeleton.png", "wizard": "assets/units/unit_wizard.png", "bat": "assets/units/unit_bat.png", "knight": "assets/units/unit_knight.png",
       "bride": "assets/poses/bride_idle1.png", "reaper": "assets/poses/necro_idle.png", "hag": "assets/units/unit_hag_idle.png"}
HIT = {"reaper": (57, 165)}   # half width, height; everything else 70 x 190
LEFT = [("skeleton", 252), ("wizard", 432), ("bat", 612)]
RIGHT = [("bride", 1296), ("wizard", 1476), ("hag", 1656)]

def load(rel):
    p = os.path.join(ROOT, rel)
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if im is None:
        print("ERROR: missing picture " + rel, file=sys.stderr); sys.exit(1)
    if im.shape[2] == 3: im = cv2.cvtColor(im, cv2.COLOR_BGR2BGRA)
    return im

def paste(dst, src, x, y):
    h, w = src.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float64); d = dst[y0:y1, x0:x1].astype(np.float64)
    sa, da = s[:, :, 3:4] / 255.0, d[:, :, 3:4] / 255.0; oa = sa + da * (1 - sa)   # proper 'over' so a transparent working strip keeps its alpha
    oc = (s[:, :, :3] * sa + d[:, :, :3] * da * (1 - sa)) / np.maximum(oa, 1e-6)
    dst[y0:y1, x0:x1, :3] = oc.astype(np.uint8); dst[y0:y1, x0:x1, 3:4] = (oa * 255).astype(np.uint8)

def silhouette(im):
    a = im[:, :, 3]; mask = (a > 40).astype(np.uint8)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    big = max(cnts, key=cv2.contourArea); x, y, w, h = cv2.boundingRect(big)
    col = mask.sum(axis=0).astype(np.float64); c = np.cumsum(col); tot = c[-1]
    lo = int(np.searchsorted(c, tot * 0.05)); hi = int(np.searchsorted(c, tot * 0.95))
    return {"bbox": [x, y, w, h], "body90": [lo, hi], "hull_area": float(cv2.contourArea(cv2.convexHull(big))), "area": float(cv2.contourArea(big))}

def grid(img, pad, step=120):
    for gx in range(-pad // step * step, W + pad + 1, step):
        X = gx + pad
        if 0 <= X < img.shape[1]: cv2.line(img, (X, 0), (X, H), (255, 255, 255), 1); cv2.putText(img, str(gx), (X + 3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    for gy in range(0, H + 1, step):
        cv2.line(img, (0, gy), (img.shape[1], gy), (255, 255, 255), 1); cv2.putText(img, str(gy), (3, gy - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--aspect", type=float, default=932 / 430); ap.add_argument("--scene", default="graveyard")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    view = int(round(H * a.aspect / 2) * 2); pad = (view - W) // 2
    bg = cv2.resize(load("assets/env/bg_%s.png" % {"church": "ruined_church", "school": "abandoned_school"}.get(a.scene, a.scene))[:, :, :3], (W, H), interpolation=cv2.INTER_LANCZOS4)
    canvas = np.zeros((H, view, 4), np.uint8); canvas[:, :, 3] = 255; canvas[:, pad:pad + W, :3] = bg
    canvas[:, :pad, :3] = bg[:, :pad][:, ::-1]; canvas[:, pad + W:, :3] = bg[:, W - pad:][:, ::-1]
    L1 = canvas.copy(); g1 = L1[:, :, :3].copy(); grid(g1, pad); cv2.imwrite(os.path.join(a.out, "layer1_map.png"), g1)
    gs = load("assets/env/ground_strip.png"); now = cv2.resize(gs, (W, 260), interpolation=cv2.INTER_AREA)
    L2 = canvas.copy(); paste(L2, now, pad, GROUND_Y - 40); g2 = L2[:, :, :3].copy()
    native_h = int(round(W * gs.shape[0] / gs.shape[1])); cv2.rectangle(g2, (pad, GROUND_Y - 40), (pad + W, GROUND_Y - 40 + native_h), (0, 255, 255), 2)
    cv2.line(g2, (0, GROUND_Y), (view, GROUND_Y), (255, 255, 255), 2); cv2.line(g2, (0, FEET), (view, FEET), (203, 155, 255), 2); grid(g2, pad)
    cv2.imwrite(os.path.join(a.out, "layer2_ground.png"), g2)
    L3 = L2.copy(); report = {"view_w": view, "pad": pad, "ground_strip": {"native": list(gs.shape[1::-1]), "drawn": [W, 260], "native_aspect": round(gs.shape[1] / gs.shape[0], 3), "drawn_aspect": round(W / 260, 3), "vertical_squash": round(260 / native_h, 3)}, "units": {}}
    sil = {}
    for side, units in (("left", LEFT), ("right", RIGHT)):
        for hero, x in units:
            im = load(ART[hero]); s = silhouette(im); k = 220.0 / im.shape[0]
            sil[hero] = s; face_right = side == "left"
            sp = cv2.resize(im, (int(im.shape[1] * k), 220), interpolation=cv2.INTER_AREA)
            if face_right: sp = sp[:, ::-1].copy()   # the art faces left; the left team faces right
            paste(L3, sp, pad + x - sp.shape[1] // 2, FEET - 220)
    g3 = L3[:, :, :3].copy()
    for side, units in (("left", LEFT), ("right", RIGHT)):
        for hero, x in units:
            s = sil[hero]; k = 220.0 / load(ART[hero]).shape[0]; hw, hh = HIT.get(hero, (70, 190)); X = pad + x
            bx, by, bw, bh = s["bbox"]; lo, hi = s["body90"]
            cv2.rectangle(g3, (X - hw, GROUND_Y - hh), (X + hw, GROUND_Y), (42, 42, 255), 2)                      # current hit box (red)
            cv2.rectangle(g3, (X - int((hi - lo) * k / 2), GROUND_Y - int((FEET - 220 + 220 - by * k - (FEET - 220)) * 0) - int(220 - 15 - by * k)), (X + int((hi - lo) * k / 2), GROUND_Y), (153, 255, 51), 2)   # body box from the silhouette (green)
            cv2.rectangle(g3, (X - hw - 30, GROUND_Y - hh - 30), (X + hw + 30, GROUND_Y + 30), (42, 211, 255), 1)  # + projectile radius 30 (yellow)
            report["units"][side + ":" + hero] = {"x": x, "body90_width": round((hi - lo) * k), "silhouette_height": round(bh * k), "visible_top_above_feet": round(220 - 15 - by * k), "hit_half_width_now": hw, "hit_height_now": hh, "gap_per_side": round(hw - (hi - lo) * k / 2), "convexity": round(s["area"] / s["hull_area"], 3)}
    grid(g3, pad); cv2.imwrite(os.path.join(a.out, "layer3_units.png"), g3)
    bar = load("assets/ui/dock_bar.png"); s = H / 390.0; dw, dh = int(view * 0.84), 52   # design stage height 390 (css/dock_stage.css); width = 84 percent of the view
    ends = bar[:, :112]; mid = bar[:, 112:216]; right = bar[:, 216:]; strip = np.zeros((104, int(dw / s * 2), 4), np.uint8); mw = strip.shape[1] - 224
    for i in range(0, mw, 104): paste(strip, mid[:, :min(104, mw - i)], 112 + i, 0)
    paste(strip, ends, 0, 0); paste(strip, right, strip.shape[1] - 112, 0)
    strip = cv2.resize(strip, (int(strip.shape[1] / 2 * s), int(104 / 2 * s)), interpolation=cv2.INTER_AREA)
    L4 = L3.copy(); paste(L4, strip, (view - strip.shape[1]) // 2, H - int(6 * s) - strip.shape[0]); g4 = L4[:, :, :3].copy()
    cv2.line(g4, (0, FEET), (view, FEET), (203, 155, 255), 2); grid(g4, pad); cv2.imwrite(os.path.join(a.out, "layer4_dock.png"), g4)
    top = H - int(6 * s) - strip.shape[0]; report["dock"] = {"top_world_y": top, "feet_y": FEET, "clear_world_px": top - FEET, "shadow_bottom_y": FEET + 18}
    json.dump(report, open(os.path.join(a.out, "layer_report.json"), "w"), indent=1)
    print(json.dumps(report, indent=1))

if __name__ == "__main__":
    main()
