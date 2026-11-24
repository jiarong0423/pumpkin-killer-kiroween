#!/usr/bin/env python3
"""Make assets/units/unit_skeleton_unarmed.png: the skeleton art with the shoulder spear removed.

The spear is a straight shaft from tail to head. Pixels that are spear-coloured (wood,
orange sticker outline, steel, dark outline) and lie close to that line are erased; bone,
skull and cyan fire are protected. Holes the spear used to cover are filled by inpainting.
Usage: python3 scripts/make_unarmed_skeleton.py [--debug]
Exit code 0 on success, 1 on failure.
"""
import sys, logging
from pathlib import Path
import numpy as np
import cv2

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/units/unit_skeleton.png"
DST = ROOT / "assets/units/unit_skeleton_unarmed.png"
LOG = ROOT / "docs/make_unarmed_skeleton.log"

# Spear axis in 1024px art space (tail end -> head tip), measured from the 500px preview x2.048
TAIL = np.array([120.0, 640.0])
TIP = np.array([930.0, 300.0])
SHAFT_R = 30.0      # half width of band around shaft
HEAD_R = 120.0      # radius around the spearhead

def dist_to_segment(h, w, a, b):
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    ab = b - a
    t = ((xs - a[0]) * ab[0] + (ys - a[1]) * ab[1]) / float(ab @ ab)
    t = np.clip(t, 0, 1)
    px, py = a[0] + t * ab[0], a[1] + t * ab[1]
    return np.hypot(xs - px, ys - py)

def main():
    logging.basicConfig(filename=str(LOG), level=logging.INFO, format="%(asctime)s %(message)s")
    try:
        img = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
        if img is None or img.shape[2] != 4:
            raise RuntimeError(f"cannot read RGBA {SRC}")
        h, w = img.shape[:2]
        a = img[..., 3].astype(np.int32)
        ys, xs = np.mgrid[0:h, 0:w]
        near = dist_to_segment(h, w, TAIL, TIP) <= SHAFT_R
        near |= np.hypot(xs - 840.0, ys - 330.0) <= HEAD_R
        # Geometric protection instead of colour protection (steel highlights look like bone):
        skull = (((xs - 502.0) / 172.0) ** 2 + ((ys - 336.0) / 182.0) ** 2) <= 1.0           # skull stays whole
        hand = np.hypot(xs - 320.0, ys - 546.0) <= 46.0              # gripping hand stays
        protect = skull | hand
        spear = near & (a > 10) & ~protect
        spear = cv2.dilate(spear.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
        spear &= ~protect
        bone = np.zeros((h, w), bool)
        bgr = img[..., :3].astype(np.int32)
        mx, mn = bgr.max(2), bgr.min(2)
        bone = (mn > 150) & ((mx - mn) < 70) & ~spear
        out = img.copy()
        # inpaint only where the spear hid body pixels (inside the body silhouette hull), else cut away
        body_alpha = ((a > 10) & ~spear).astype(np.uint8) * 255
        k = np.ones((41, 41), np.uint8)
        body_hull = cv2.morphologyEx(body_alpha, cv2.MORPH_CLOSE, k) > 0
        # only fill spear pixels that are enclosed by body on the closed hull but not far from bone
        fill = spear & body_hull & (cv2.dilate(bone.astype(np.uint8), np.ones((25, 25), np.uint8)) > 0)
        cut = spear & ~fill
        rgb = np.ascontiguousarray(img[..., :3])
        rgb = cv2.inpaint(rgb, (fill.astype(np.uint8) * 255), 5, cv2.INPAINT_TELEA)
        out[..., :3] = rgb
        out[..., 3] = np.where(cut, 0, out[..., 3])
        # drop stray specks left floating by the cut
        n, lab, stats, _ = cv2.connectedComponentsWithStats((out[..., 3] > 10).astype(np.uint8), 8)
        big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        out[..., 3] = np.where(lab == big, out[..., 3], 0)
        if "--debug" in sys.argv:
            cv2.imwrite(str(ROOT / "docs/_unarmed_mask_debug.png"), (spear * 255).astype(np.uint8))
        cv2.imwrite(str(DST), out)
        logging.info("OK removed=%d filled=%d cut=%d", int(spear.sum()), int(fill.sum()), int(cut.sum()))
        print(f"OK {DST} removed={int(spear.sum())} filled={int(fill.sum())}")
        return 0
    except Exception as e:  # noqa
        logging.exception("ERROR %s", e)
        print(f"ERROR {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
