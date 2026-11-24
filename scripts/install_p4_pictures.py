#!/usr/bin/env python3
"""Install the accepted round-7 (tag p4) Colab pictures into assets/: four scenes and the feet chain.

Scenes: Colab writes 1024x576; the page's scene art is 1536x864, so each is scaled up with LANCZOS and written as PNG (a sharper retake can replace them later).
Feet chain: magenta key + tight crop with a 6 px margin (same key as the knight: scripts/key_knight_unarmed.py).
Dry run unless --apply. Every overwrite first copies the old file to docs/audition/backup_p4_<time>/. Exit code 1 on any failure.
Usage: python3 -B scripts/install_p4_pictures.py [--src-dir DIR] [--apply]
"""
import argparse
import datetime as dt
import glob
import os
import shutil
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import key_knight_unarmed as K  # noqa: E402

ROOT = K.ROOT
SCENES = {
    "bg_belltower_v3_v1_p4.png": "assets/env/bg_belltower.png",
    "bg_pumpkin_field_v3_v1_p4.png": "assets/env/bg_pumpkin_field.png",
    "bg_ruined_church_v3_v1_p4.png": "assets/env/bg_ruined_church.png",
    "bg_abandoned_school_v3_v1_p4.png": "assets/env/bg_abandoned_school.png",
}
SCENE_SIZE = (1536, 864)
CHAIN = ("fx_feet_chain_v1_p4.png", "assets/fx/sprites/fx_feet_chain.png")


def drive_out():
    hits = glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*/*/PumpkinKiller/out"))
    return hits[0] if hits else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src-dir", default=drive_out())
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.src_dir or not os.path.isdir(args.src_dir):
        print("ERROR no source folder")
        return 1
    backup = os.path.join(ROOT, "docs", "audition", "backup_p4_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
    failed = 0

    def put(img, dest, fmt_kwargs):
        full = os.path.join(ROOT, dest)
        if args.apply:
            if os.path.exists(full):
                os.makedirs(backup, exist_ok=True)
                shutil.copy2(full, os.path.join(backup, os.path.basename(full)))
            img.save(full, **fmt_kwargs)

    for name, dest in SCENES.items():
        try:
            im = Image.open(os.path.join(args.src_dir, name)).convert("RGB")
            if im.size[0] * 9 != im.size[1] * 16:
                raise ValueError("not 16:9: %s" % (im.size,))
            put(im.resize(SCENE_SIZE, Image.LANCZOS), dest, {"optimize": True})
            print("OK" if args.apply else "OK (dry)", name, "->", dest)
        except Exception as exc:  # noqa: BLE001
            print("ERROR", name, repr(exc))
            failed += 1
    try:
        img = K.key(os.path.join(args.src_dir, CHAIN[0]))
        box = K.bbox(img)
        m = 6
        img = img.crop((max(0, box[0] - m), max(0, box[1] - m), min(img.size[0], box[2] + m), min(img.size[1], box[3] + m)))
        put(img, CHAIN[1], {"optimize": True})
        print("OK" if args.apply else "OK (dry)", CHAIN[0], "->", CHAIN[1], img.size)
    except Exception as exc:  # noqa: BLE001
        print("ERROR", CHAIN[0], repr(exc))
        failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
