#!/usr/bin/env python3
"""Decoupled similarity of every generated pose frame against its class idle picture (docs/pose_spec.md).

Each factor is measured on its own, so a failure can be traced to one cause (owner 2026-11-10: 'do image similarity decoupled'):
  palette_sim  colour-histogram overlap (Lab, opaque pixels only): did the colours drift?              1.0 = same palette
  face_sim     structural similarity (SSIM on Canny edges) of the HEAD region (top 30 percent of the figure) after the head
               is cut out, centred and resized: is it the same face / head?                           1.0 = identical
  face_orb     ORB feature matches that agree between the two heads (robust to small shifts)           count
  scale        figure height / idle figure height: did the size change?                                 1.0 = same
  head_scale   head width / idle head width                                                             1.0 = same
  pose_diff    1 - IoU of the two silhouettes (feet aligned, centred): how much did the pose change?   higher = more change
  lean         which side the figure's mass leans to (-1 left, +1 right): a sign flip against the idle means another direction
Flags: FACE (face_sim or face_orb too low), PALETTE, SCALE, DIRECTION, COPY (pose_diff too small for a pose that must change).
The thresholds were calibrated on known good and bad pairs (see CAL below); they are guides, not a judge: the final call stays with the owner.
Usage: python3 -B scripts/pose_similarity.py [--tag q1] [--drive-out DIR] [--json out.json]   Exit 0 always (it reports; it does not gate).
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF = os.environ.get("PK_DRIVE_DIR", "<DRIVE_DIR>")
CLASSES = ["skeleton", "wizard", "bat", "knight", "bride", "hunchback", "reaper"]
FRAMES = ["idle2", "charge1", "charge2", "charge3", "release", "empty", "hit"]
# thresholds (calibrated against what the owner flagged: wizard idle2 / bride = same face 0.7 to 0.9; knight, bat, skeleton = changed face 0.24 to 0.45)
TH = {"face_sim": 0.50, "face_orb": 10, "palette_sim": 0.55, "scale_lo": 0.8, "scale_hi": 1.25, "copy_diff": 0.06}   # face 0.5: the owner saw the knight (0.36 to 0.45) and the bat (0.24) change faces; the unchanged ones score 0.7 and up


def load_keyed(path, size=None):
    """RGBA from a magenta-keyed Colab picture or an RGBA file; returns (rgb float array, mask bool)."""
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise ValueError("unreadable " + path)
    if im.ndim == 3 and im.shape[2] == 4:
        rgb = im[..., :3][..., ::-1].astype(np.float32)
        mask = im[..., 3] > 128
    else:
        rgb = im[..., ::-1].astype(np.float32)
        mag = (rgb[..., 0] + rgb[..., 2]) / 2 - rgb[..., 1]
        mask = mag < 145
    return rgb, mask


def bbox(mask):
    rows = np.where(mask.sum(axis=1) > 4)[0]
    cols = np.where(mask.sum(axis=0) > 4)[0]
    if len(rows) == 0:
        return None
    return int(cols.min()), int(rows.min()), int(cols.max()) + 1, int(rows.max()) + 1


def head_crop(rgb, mask, out=160):
    b = bbox(mask)
    if not b:
        return None, None
    x0, y0, x1, y1 = b
    h = y1 - y0
    top = mask[y0:y0 + int(h * 0.30)]
    cols = np.where(top.sum(axis=0) > 2)[0]
    if len(cols) == 0:
        return None, None
    cx = int(np.average(cols, weights=top.sum(axis=0)[cols]))
    half = int(max(40, (cols.max() - cols.min()) / 2 * 1.05))
    xa, xb = max(0, cx - half), min(rgb.shape[1], cx + half)
    ya, yb = y0, min(rgb.shape[0], y0 + int(h * 0.30))
    crop = rgb[ya:yb, xa:xb]
    m = mask[ya:yb, xa:xb]
    if crop.size == 0:
        return None, None
    crop = cv2.resize(crop, (out, out), interpolation=cv2.INTER_AREA)
    m = cv2.resize(m.astype(np.uint8), (out, out), interpolation=cv2.INTER_NEAREST).astype(bool)
    return crop, (xb - xa)


def edges(img):
    g = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    return cv2.GaussianBlur(cv2.Canny(g, 60, 150), (3, 3), 0)


def palette_sim(a, ma, b, mb):
    def hist(rgb, m):
        lab = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2LAB)
        h = cv2.calcHist([lab], [0, 1, 2], m.astype(np.uint8) * 255, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        return cv2.normalize(h, h, 1, 0, cv2.NORM_L1).flatten()
    return float(np.sum(np.sqrt(hist(a, ma) * hist(b, mb))))


def orb_matches(ha, hb):
    orb = cv2.ORB_create(nfeatures=300)
    ga = cv2.cvtColor(ha.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    gb = cv2.cvtColor(hb.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    ka, da = orb.detectAndCompute(ga, None)
    kb, db = orb.detectAndCompute(gb, None)
    if da is None or db is None or len(ka) < 3 or len(kb) < 3:
        return 0
    m = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db)
    return int(sum(1 for x in m if x.distance < 40))


def align_mask(mask, b, size=512):
    """Silhouette on a fixed canvas: feet on the bottom line, centred on the bbox centre (no rescale: the size is part of the question)."""
    x0, y0, x1, y1 = b
    canvas = np.zeros((size, size), bool)
    h, w = y1 - y0, x1 - x0
    s = size / 1024.0
    crop = cv2.resize(mask[y0:y1, x0:x1].astype(np.uint8), (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_NEAREST).astype(bool)
    ch, cw = crop.shape
    ys = size - 10 - ch
    xs = (size - cw) // 2
    if ys < 0 or xs < 0:
        return canvas
    canvas[ys:ys + ch, xs:xs + cw] = crop
    return canvas


def lean(mask, b):
    x0, y0, x1, y1 = b
    xs = np.where(mask[y0:y1])[1]
    return float(np.sign(np.mean(xs) - (x0 + x1) / 2)) if len(xs) else 0.0


def compare(idle_path, frame_path, frame=''):
    ra, ma = load_keyed(idle_path)
    rb, mb = load_keyed(frame_path)
    ba, bb = bbox(ma), bbox(mb)
    if not ba or not bb:
        return {"error": "empty silhouette"}
    ha, wa = head_crop(ra, ma)
    hb, wb = head_crop(rb, mb)
    r = {}
    r["palette_sim"] = round(palette_sim(ra, ma, rb, mb), 3)
    if ha is not None and hb is not None:
        r["face_sim"] = round(float(ssim(edges(ha), edges(hb), data_range=255)), 3)
        r["face_orb"] = orb_matches(ha, hb)
        r["head_scale"] = round(wb / wa, 3)
    else:
        r["face_sim"], r["face_orb"], r["head_scale"] = 0.0, 0, 0.0
    r["scale"] = round((bb[3] - bb[1]) / (ba[3] - ba[1]), 3)
    ia, ib = align_mask(ma, ba), align_mask(mb, bb)
    union = np.logical_or(ia, ib).sum()
    r["pose_diff"] = round(1 - float(np.logical_and(ia, ib).sum()) / union, 3) if union else 0.0
    r["lean"] = lean(mb, bb)
    r["lean_idle"] = lean(ma, ba)
    flags = []
    if r["face_sim"] < TH["face_sim"] and r["face_orb"] < TH["face_orb"]:
        flags.append("FACE")
    if r["palette_sim"] < TH["palette_sim"]:
        flags.append("PALETTE")
    if not (TH["scale_lo"] <= r["scale"] <= TH["scale_hi"]):
        flags.append("SCALE")
    if r["lean"] != 0 and r["lean_idle"] != 0 and r["lean"] != r["lean_idle"]:
        flags.append("DIRECTION?")
    if frame in ("charge1", "charge2", "charge3", "release", "hit") and r["pose_diff"] < TH["copy_diff"]:
        flags.append("COPY")   # the pose did not change: the picture is the idle again
    r["flags"] = flags
    return r


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="q1")
    ap.add_argument("--drive-out", default=DEF)
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    res = {}
    for cls in CLASSES:
        idle = os.path.join(ROOT, "assets", "poses", "%s_idle1.png" % cls)
        if not os.path.exists(idle):
            print("ERROR no idle1 for", cls, file=sys.stderr)
            continue
        for fr in FRAMES:
            p = os.path.join(a.drive_out, "pose_%s_%s_v1_%s.png" % (cls, fr, a.tag))
            if not os.path.exists(p):
                continue
            try:
                r = compare(idle, p, fr)
            except Exception as e:  # noqa: BLE001 - report and continue
                r = {"error": repr(e)}
            res["pose_%s_%s" % (cls, fr)] = r
            print("%-26s %s" % ("%s_%s" % (cls, fr), ("face %.2f orb %2d pal %.2f scale %.2f head %.2f diff %.2f %s" % (r["face_sim"], r["face_orb"], r["palette_sim"], r["scale"], r["head_scale"], r["pose_diff"], " ".join(r["flags"])) if "error" not in r else r["error"])))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
