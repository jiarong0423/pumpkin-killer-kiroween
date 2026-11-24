#!/usr/bin/env python3
"""Key the magenta background out of the Colab-generated cat (bat-cat assassin) pose images and fit them to the base sprite.

Writes assets/poses/bat_draw.png, bat_windup.png, bat_release.png, bat_hit.png on a 1536x1024 RGBA canvas (the base canvas plus 256 px padding each side).
Fit: scale so the height of the biggest orange inner-ear blob matches the base sprite (assets/units/unit_bat_unarmed.png), then put the feet on the base feet line.
Exit code 1 on any failure; one log line per image.
Usage: python3 -B scripts/key_bat_poses.py [--drive-out DIR]
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from key_skeleton_poses import DEFAULT_OUT, PAD, clean_alpha, feet, key_magenta  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "assets", "units", "unit_bat_unarmed.png")
OUT_DIR = os.path.join(ROOT, "assets", "poses")
JOBS = {
    "bat_shuriken_draw_v2_r4.png": "bat_draw.png",
    "bat_shuriken_windup_v1_r4.png": "bat_windup.png",
    "bat_pose_release_v1_r4.png": "bat_release.png",
    "bat_pose_hit_v1_r4.png": "bat_hit.png",
}


def ear_height(img):
    """Height of the biggest bright-orange blob (the inner ear). The thin orange outline is too small to count."""
    a = np.asarray(img).astype(int)
    m = (a[..., 3] > 200) & (a[..., 0] > 220) & (a[..., 1] > 110) & (a[..., 1] < 190) & (a[..., 2] < 90)
    m = ndi.binary_opening(m, iterations=2)
    lab, n = ndi.label(m)
    best = None
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(xs) > 300 and (best is None or len(xs) > best[0]):
            best = (len(xs), ys.max() - ys.min() + 1)
    if best is None:
        raise ValueError("no orange ear found")
    return float(best[1])


def fit(pose, base):
    s = ear_height(base) / ear_height(pose)
    pose = pose.resize((round(pose.width * s), round(pose.height * s)), Image.LANCZOS)
    bb, bf = feet(base)
    pb, pf = feet(pose)
    canvas = Image.new("RGBA", (base.width + 2 * PAD, base.height), (0, 0, 0, 0))
    canvas.alpha_composite(pose, (round(bf - pf) + PAD, round(bb - pb)))
    return canvas, s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drive-out", default=DEFAULT_OUT)
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    base = Image.open(BASE).convert("RGBA")
    failed = 0
    for src, dst in JOBS.items():
        try:
            pose = clean_alpha(key_magenta(Image.open(os.path.join(args.drive_out, src))))
            out, s = fit(pose, base)
            out.save(os.path.join(OUT_DIR, dst))
            print("OK    %s -> %s (scale %.2f)" % (src, dst, s))
        except Exception as e:
            failed += 1
            print("ERROR %s: %r" % (src, e))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
