#!/usr/bin/env python3
"""Key the Colab pictures of the ghost nun (hag_*) and install them on the 1024 canvas.

Clean magenta key: edge unmixing inside a thin band next to the background, only background connected to the picture border counts, the pink and blue-violet
glow the generator paints around the art is dropped (owner: no blue-violet), stray specks are removed, the picture edge is cleared.
Usage: python3 -B scripts/key_hag.py [--src-dir DIR] [--apply] [name ...]    (default: every hag_* / hand_* picture it knows)
Exit code 1 on any failure; one log line per picture. Dry run unless --apply.
"""
import argparse
import glob
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = {
    "hag_e_idle1_v1_p4.png": "assets/units/unit_hag_idle.png",   # empty-handed set (the silver cross is drawn by the page as its own layer)
    "hag_e_idle2_v1_p4.png": "assets/poses/hag_idle2.png",
    "hag_e_charge1_v1_p4.png": "assets/poses/hag_charge1.png",
    "hag_e_charge2_v1_p4.png": "assets/poses/hag_charge2.png",
    "hag_e_charge3_v1_p4.png": "assets/poses/hag_charge3.png",
    "hag_e_release_v1_p4.png": "assets/poses/hag_release.png",
    "hag_e_hit_v1_p4.png": "assets/poses/hag_hit.png",
    "hag_front_r2_v1_p4.png": "assets/portraits/hag_front.png",
}


def clean_key(path):
    """Magenta key with edge unmixing: observed = a*fg + (1-a)*magenta inside a thin band next to the background; the artwork itself stays opaque."""
    from scipy import ndimage
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    mag = (rgb[..., 0] + rgb[..., 2]) / 2.0 - rgb[..., 1]
    hard_bg = mag > 200.0
    labels, count = ndimage.label(hard_bg)
    if count:   # only background connected to the picture border counts (magenta inside the artwork stays)
        border = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))) - {0}
        hard_bg = np.isin(labels, list(border))
    hard_bg |= (rgb[..., 0] > 205) & (rgb[..., 2] > 205) & (rgb[..., 1] < 70)   # enclosed pure magenta (gaps inside the smoke) is background too: the nun has no magenta in her art
    dist = ndimage.distance_transform_edt(~hard_bg)
    band = (dist <= 4.0) & ~hard_bg
    alpha = np.ones(mag.shape, np.float32)
    alpha[hard_bg] = 0.0
    a_lin = np.clip(1.0 - mag / 247.0, 0.05, 1.0)
    alpha[band] = np.clip(a_lin[band] * 1.25, 0.0, 1.0)
    fg = rgb.copy()
    m = np.array([255.0, 0.0, 255.0], np.float32)
    for c in range(3):
        ch = fg[..., c]
        ch[band] = np.clip((rgb[..., c][band] - (1.0 - alpha[band]) * m[c]) / np.maximum(alpha[band], 0.05), 0, 255)
    # the generator paints a pink-orange glow around the art; where it is pink (blue well above green) it is magenta spill, not art: drop it
    near = (dist <= 10.0) & ~hard_bg
    pink = near & (rgb[..., 0] > 170) & (rgb[..., 2] > rgb[..., 1] + 25) & (rgb[..., 0] - rgb[..., 1] > 55)
    violet = (dist <= 16.0) & ~hard_bg & (rgb[..., 2] > rgb[..., 1] + 35) & (rgb[..., 2] >= rgb[..., 0] - 10) & (rgb[..., 1] > 25)   # blue-violet glow (owner: no blue-violet)
    alpha[pink | violet] = 0.0
    alpha[:6, :] = alpha[-6:, :] = 0.0
    alpha[:, :6] = alpha[:, -6:] = 0.0
    lab, n = ndimage.label(alpha > 0.1)
    if n > 1:
        sizes = ndimage.sum(alpha > 0.1, lab, range(1, n + 1))
        alpha[lab != int(np.argmax(sizes)) + 1] = 0.0
    # the generator sometimes adds green leaf-like wisps and pink specks to the smoke tail: the nun has neither (owner: no green on her), so wisps become dark smoke and specks go
    r_, g_, b_ = fg[..., 0], fg[..., 1], fg[..., 2]
    green = (g_ > r_ + 18) & (g_ > b_ + 8) & (alpha > 0)
    fg[green] = np.array([38.0, 38.0, 46.0])
    pinkspeck = (r_ > 190) & (b_ > 120) & (g_ < 135) & (r_ - g_ > 70) & (alpha > 0)
    alpha[pinkspeck] = 0.0
    return Image.fromarray(np.dstack([fg, alpha * 255.0]).astype(np.uint8), "RGBA")


def main():
    parser = argparse.ArgumentParser()
    hits = glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*/*/PumpkinKiller/out"))
    parser.add_argument("--src-dir", default=hits[0] if hits else None)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("names", nargs="*")
    args = parser.parse_args()
    failed = 0
    for name, dest in FRAMES.items():
        if args.names and name not in args.names:
            continue
        src = os.path.join(args.src_dir or "", name)
        if not os.path.exists(src):
            print("MISSING", name)
            continue
        try:
            img = clean_key(src)
            if img.getpixel((4, 4))[3] != 0:
                raise ValueError("background corner not transparent")
            box = img.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
            if args.apply:
                img.save(os.path.join(ROOT, dest), optimize=True)
            print("OK" if args.apply else "OK (dry)", name, "->", dest, "bbox", box)
        except Exception as exc:  # noqa: BLE001
            print("ERROR", name, repr(exc))
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
