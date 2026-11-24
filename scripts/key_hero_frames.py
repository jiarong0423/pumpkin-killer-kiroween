#!/usr/bin/env python3
"""Key the magenta background out of the Colab action frames of the bride, the hunchback and the wizard and install them on the 1024 canvas.

Each frame must keep the feet line of its hero (bottom of the opaque box within 14 px of the hero's reference frame), else it is reported and NOT installed.
Dry run unless --apply. Exit code 1 when a frame fails a check (a missing picture is only reported). Usage: python3 -B scripts/key_hero_frames.py [--src-dir DIR] [--apply]
"""
import argparse
import glob
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import key_knight_unarmed as K  # noqa: E402

ROOT = K.ROOT
# source on Drive -> (destination, reference picture whose feet line it must keep)
FRAMES = {
    "bride_wail_windup_v1_p4.png": ("assets/poses/bride_windup.png", "assets/poses/bride_idle1.png"),
    "bride_wail_release_v1_p4.png": ("assets/poses/bride_release_new.png", "assets/poses/bride_idle1.png"),
    "bride_wail_hit_v1_p4.png": ("assets/poses/bride_hit_new.png", "assets/poses/bride_idle1.png"),
    "hunchback_axe_gone_v1_p4.png": ("assets/poses/hunchback_unarmed.png", "assets/poses/hunchback_idle1.png"),
    "hunchback_axe_windup_v1_p4.png": ("assets/poses/hunchback_windup.png", "assets/poses/hunchback_idle1.png"),
    "hunchback_axe_release_v1_p4.png": ("assets/poses/hunchback_release_new.png", "assets/poses/hunchback_idle1.png"),
    "hunchback_axe_hit_r2b_v1_p4.png": ("assets/poses/hunchback_hit_new.png", "assets/poses/hunchback_idle1.png"),   # r2b: both hands drawn (the first hit frame lost a hand)
    "wizard_fl_windup_v1_p4.png": ("assets/poses/wizard_windup.png", "assets/units/unit_wizard.png"),
    "wizard_fl_charge_v1_p4.png": ("assets/poses/wizard_charge_hot.png", "assets/units/unit_wizard.png"),
    "wizard_fl_release_v1_p4.png": ("assets/poses/wizard_release_new.png", "assets/units/unit_wizard.png"),
    "wizard_fl_hit_v1_p4.png": ("assets/poses/wizard_hit_new.png", "assets/units/unit_wizard.png"),
}


def main():
    parser = argparse.ArgumentParser()
    hits = glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*/*/PumpkinKiller/out"))
    parser.add_argument("--src-dir", default=hits[0] if hits else None)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    failed = 0
    for name, (dest, ref) in FRAMES.items():
        src = os.path.join(args.src_dir or "", name)
        if not os.path.exists(src):
            print("MISSING", name)
            continue
        try:
            img = K.key(src)
            box = K.bbox(img)
            ref_box = K.bbox(Image.open(os.path.join(ROOT, ref)).convert("RGBA"))
            if img.size != (1024, 1024) or img.getpixel((4, 4))[3] != 0:
                raise ValueError("size %s or background not transparent" % (img.size,))
            if abs(box[3] - ref_box[3]) > 14:
                print("ERROR", name, "feet line", box[3], "vs reference", ref_box[3], "- not installed")
                failed += 1
                continue
            if args.apply:
                img.save(os.path.join(ROOT, dest), optimize=True)
            print("OK" if args.apply else "OK (dry)", name, "->", dest, "bbox", box, "ref", ref_box)
        except Exception as exc:  # noqa: BLE001
            print("ERROR", name, repr(exc))
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
