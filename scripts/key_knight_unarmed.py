#!/usr/bin/env python3
"""Key the flat magenta background out of the Colab picture of the shield-less knight and install it as assets/units/unit_knight_unarmed.png.

Source: <drive out>/unit_knight_unarmed_v1_p4.png (or --src). Same 1024 canvas as assets/units/unit_knight.png, so the feet line and the position match.
Background pixels are ~245 on the 'magenta-ness' scale (mean(R,B) - G), artwork is below ~120; alpha ramps between 145 and 215; spill is removed from soft edge pixels only.
Prints the bounding boxes of the original and the new art (the feet must sit within 6 px of each other). Exit code 1 on any failure.
Usage: python3 -B scripts/key_knight_unarmed.py [--src PATH] [--dry-run]
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SRC = os.path.join(ROOT, "docs", "audition", "p4_review", "unit_knight_unarmed_v1_p4.png")
ORIGINAL = os.path.join(ROOT, "assets", "units", "unit_knight.png")
DEST = os.path.join(ROOT, "assets", "units", "unit_knight_unarmed.png")


def key(path):
    img = Image.open(path).convert("RGB")
    a = np.asarray(img).astype(np.float32)
    mag = (a[..., 0] + a[..., 2]) / 2.0 - a[..., 1]
    alpha = np.clip((215.0 - mag) / (215.0 - 145.0), 0.0, 1.0)
    out = a.copy()
    soft = (alpha > 0.0) & (alpha < 1.0)
    # despill: pull red and blue down towards green on soft edge pixels
    spill = np.clip(mag[soft] / 245.0, 0.0, 1.0)
    out[..., 0][soft] = out[..., 0][soft] * (1.0 - 0.6 * spill) + out[..., 1][soft] * 0.6 * spill
    out[..., 2][soft] = out[..., 2][soft] * (1.0 - 0.6 * spill) + out[..., 1][soft] * 0.6 * spill
    alpha[:8, :] = 0.0   # the generator leaves a thin line on the picture edge
    alpha[-8:, :] = 0.0
    alpha[:, :8] = 0.0
    alpha[:, -8:] = 0.0
    from scipy import ndimage   # keep only the biggest piece (the knight); stray specks go
    labels, count = ndimage.label(alpha > 0.1)
    if count > 1:
        sizes = ndimage.sum(alpha > 0.1, labels, range(1, count + 1))
        alpha[labels != (int(np.argmax(sizes)) + 1)] = 0.0
    rgba = np.dstack([np.clip(out, 0, 255), alpha * 255.0]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def bbox(img):
    return img.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default=DEFAULT_SRC)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        new = key(args.src)
        old = Image.open(ORIGINAL).convert("RGBA")
        if new.size != old.size:
            print("ERROR size differs", new.size, old.size)
            return 1
        b_new, b_old = bbox(new), bbox(old)
        print("bbox original", b_old, "new", b_new)
        if abs(b_new[3] - b_old[3]) > 6:
            print("ERROR feet line differs by", abs(b_new[3] - b_old[3]), "px")
            return 1
        corner = new.getpixel((4, 4))
        if corner[3] != 0:
            print("ERROR background corner is not transparent", corner)
            return 1
        if args.dry_run:
            print("dry run: nothing written")
            return 0
        new.save(DEST, optimize=True)
        print("OK wrote", os.path.relpath(DEST, ROOT))
        return 0
    except Exception as exc:  # noqa: BLE001
        print("ERROR", repr(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
