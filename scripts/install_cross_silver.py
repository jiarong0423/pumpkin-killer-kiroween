#!/usr/bin/env python3
"""Install the Colab pictures of the silver-white metal cross: item_cross_silver_smoke_r3 (wreathed in black smoke) and item_cross_silver_plain_r3 (no smoke).

Magenta key (scripts/key_knight_unarmed.py), then a violet despill: dark pixels whose red and blue both sit well above green are magenta spill from the key colour
(owner: no blue-violet), so they are pulled to neutral grey. Tight crop with a 6 px margin. Dry run unless --apply. Exit code 1 on any failure.
Usage: python3 -B scripts/install_cross_silver.py [--src-dir DIR] [--apply]
"""
import argparse
import glob
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import key_knight_unarmed as K  # noqa: E402

FILES = {
    "item_cross_silver_smoke_r3_v1_p4.png": "assets/fx/sprites/item_cross_silver.png",
    "item_cross_silver_plain_r3_v1_p4.png": "assets/fx/sprites/item_cross_silver_plain.png",
}


def despill(img):
    a = np.array(img)
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    spill = (r > g + 22) & (b > g + 22) & (a[..., 3] > 0)
    grey = np.minimum(np.minimum(r, b), g + 18)
    for c in range(3):
        ch = a[..., c]
        ch[spill] = np.clip(grey[spill], 0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def main():
    parser = argparse.ArgumentParser()
    hits = glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*/*/PumpkinKiller/out"))
    parser.add_argument("--src-dir", default=hits[0] if hits else None)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    failed = 0
    for name, dest in FILES.items():
        src = os.path.join(args.src_dir or "", name)
        if not os.path.exists(src):
            print("MISSING", name)
            continue
        try:
            img = despill(K.key(src))
            box = K.bbox(img)
            m = 6
            img = img.crop((max(0, box[0] - m), max(0, box[1] - m), min(img.size[0], box[2] + m), min(img.size[1], box[3] + m)))
            if args.apply:
                img.save(os.path.join(K.ROOT, dest), optimize=True)
            print("OK" if args.apply else "OK (dry)", name, "->", dest, img.size)
        except Exception as exc:  # noqa: BLE001
            print("ERROR", name, repr(exc))
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
