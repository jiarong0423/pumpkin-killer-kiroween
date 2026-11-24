#!/usr/bin/env python3
"""Key the magenta background out of the Colab-generated skeleton pose images and fit them to the base sprite.

Reads  <drive_out>/skeleton_javelin_windup_v1_r4.png, skeleton_pose_release_v1_r4.png, skeleton_pose_hit_v1_r4.png
Writes assets/poses/skel_windup.png, skel_release.png, skel_hit.png (1536x1024 RGBA: the base canvas plus 256 px padding on each side).

Fit: scale so the height of the biggest cyan eye flame matches the base sprite, then move so the feet (lowest opaque pixels) sit
on the base feet line and the feet centre lines up. Exit code 1 on any failure; a log line per image is printed.
Usage: python3 -B scripts/key_skeleton_poses.py [--drive-out DIR]
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.environ.get("PK_DRIVE_DIR", "<DRIVE_DIR>")
JOBS = {
    "skeleton_javelin_windup_v1_r4.png": "skel_windup.png",
    "skeleton_pose_release_v1_r4.png": "skel_release.png",
    "skeleton_pose_hit_v1_r4.png": "skel_hit.png",
}
PAD = 256
BASE = os.path.join(ROOT, "assets", "units", "unit_skeleton_unarmed.png")
OUT_DIR = os.path.join(ROOT, "assets", "poses")


def key_magenta(img):
    a = np.asarray(img.convert("RGB")).astype(float)
    mag = (a[..., 0] + a[..., 2]) / 2 - a[..., 1]           # background ~245, artwork < 120
    alpha = np.clip((200 - mag) / 80, 0, 1)
    spill = np.maximum(0, mag) * 0.9                          # remove magenta fringe on soft edges
    rgb = a.copy()
    rgb[..., 0] = np.clip(a[..., 0] - spill, 0, 255)
    rgb[..., 2] = np.clip(a[..., 2] - spill, 0, 255)
    out = np.dstack([rgb, alpha * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def clean_alpha(img):
    """Drop stray pixels: keep only rows/columns that hold a real amount of opaque pixels."""
    al = np.asarray(img.getchannel("A"))
    rows = np.where((al > 128).sum(axis=1) > 6)[0]
    cols = np.where((al > 128).sum(axis=0) > 3)[0]
    if len(rows) == 0 or len(cols) == 0:
        raise ValueError("empty image after keying")
    arr = np.asarray(img).copy()
    mask = np.zeros(al.shape, bool)
    mask[rows.min():rows.max() + 1, cols.min():cols.max() + 1] = True
    arr[..., 3] = np.where(mask, arr[..., 3], 0)
    return Image.fromarray(arr, "RGBA")


def eye_height(img):
    """Height in px of the biggest cyan eye flame. A turned head shows one big flame, so the height (not the width of
    both flames) is stable across poses."""
    from scipy import ndimage as ndi
    a = np.asarray(img).astype(int)
    m = (a[..., 3] > 200) & (a[..., 2] > 200) & (a[..., 1] > 170) & (a[..., 0] < 120)
    lab, n = ndi.label(m)
    best = None
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(xs) > 150 and (best is None or len(xs) > best[0]):
            best = (len(xs), ys.max() - ys.min() + 1)
    if best is None:
        raise ValueError("no eye flame found")
    return float(best[1])


def feet(img):
    al = np.asarray(img.getchannel("A"))
    ys, xs = np.where(al > 128)
    bottom = ys.max()
    band = xs[ys > bottom - 40]
    return int(bottom), float(band.mean())


def fit(pose, base):
    s = eye_height(base) / eye_height(pose)
    pose = pose.resize((round(pose.width * s), round(pose.height * s)), Image.LANCZOS)
    bb, bf = feet(base)
    pb, pf = feet(pose)
    # wider canvas (256 px padding each side) so a long spear is never cut off; the base sprite sits in the middle
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
        path = os.path.join(args.drive_out, src)
        try:
            pose = clean_alpha(key_magenta(Image.open(path)))
            out, s = fit(pose, base)
            out.save(os.path.join(OUT_DIR, dst))
            print("OK    %s -> %s (scale %.2f)" % (src, dst, s))
        except Exception as e:  # keep going, report at the end
            failed += 1
            print("ERROR %s: %r" % (src, e))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
