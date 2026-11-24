#!/usr/bin/env python3
"""Make assets/units/unit_bat_unarmed.png: bat art with the dagger blade removed (fist stays).

Blade = straight band from tip to guard; the fist is protected geometrically. Pixels the blade
covered that sit against the body are inpainted, the rest become transparent.
Exit code 0 on success, 1 on failure. Log: docs/make_unarmed_bat.log
"""
import sys, logging
from pathlib import Path
import numpy as np
import cv2

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/units/unit_bat.png"
DST = ROOT / "assets/units/unit_bat_unarmed.png"
LOG = ROOT / "docs/make_unarmed_bat.log"
TIP = np.array([185.0, 548.0])
GUARD = np.array([318.0, 678.0])
BLADE_R = 46.0
HAND = (352.0, 712.0, 52.0)   # x, y, radius of the gripping fist (kept)

def main():
    logging.basicConfig(filename=str(LOG), level=logging.INFO, format="%(asctime)s %(message)s")
    try:
        img = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
        if img is None or img.shape[2] != 4:
            raise RuntimeError(f"cannot read RGBA {SRC}")
        h, w = img.shape[:2]
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        ab = GUARD - TIP
        t = np.clip(((xs - TIP[0]) * ab[0] + (ys - TIP[1]) * ab[1]) / float(ab @ ab), 0, 1)
        d = np.hypot(xs - (TIP[0] + t * ab[0]), ys - (TIP[1] + t * ab[1]))
        a = img[..., 3]
        hand = np.hypot(xs - HAND[0], ys - HAND[1]) <= HAND[2]
        blade = (d <= BLADE_R) & (a > 10) & ~hand
        blade = cv2.dilate(blade.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
        blade &= ~hand
        keep = ((a > 10) & ~blade).astype(np.uint8)
        near_body = cv2.dilate(keep, np.ones((23, 23), np.uint8)) > 0
        hull = cv2.morphologyEx(keep * 255, cv2.MORPH_CLOSE, np.ones((45, 45), np.uint8)) > 0
        fill = blade & near_body & hull
        cut = blade & ~fill
        out = img.copy()
        rgb = cv2.inpaint(np.ascontiguousarray(img[..., :3]), fill.astype(np.uint8) * 255, 5, cv2.INPAINT_TELEA)
        out[..., :3] = rgb
        out[..., 3] = np.where(cut, 0, out[..., 3])
        n, lab, stats, _ = cv2.connectedComponentsWithStats((out[..., 3] > 10).astype(np.uint8), 8)
        big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        out[..., 3] = np.where(lab == big, out[..., 3], 0)
        cv2.imwrite(str(DST), out)
        logging.info("OK blade=%d fill=%d cut=%d", int(blade.sum()), int(fill.sum()), int(cut.sum()))
        print(f"OK {DST} blade={int(blade.sum())} fill={int(fill.sum())}")
        return 0
    except Exception as e:  # noqa
        logging.exception("ERROR %s", e)
        print(f"ERROR {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
