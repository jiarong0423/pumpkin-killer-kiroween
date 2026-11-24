#!/usr/bin/env python3
"""Key the magenta background out of the three new Colab necromancer frames and install them on the same 1024 canvas as the older necro frames.

necro_idle2 (second idle frame, breathing), necro_charge2 (second charge frame), necro_ult_point (finger-pointing ultimate pose).
Dry run unless --apply. Exit code 1 on any failure. Usage: python3 -B scripts/key_necro_poses.py [--src-dir DIR] [--apply]
"""
import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import key_knight_unarmed as K  # noqa: E402

FRAMES = {
    "necro_idle2_v1_p4.png": "assets/poses/necro_idle2.png",
    "necro_charge2_v1_p4.png": "assets/poses/necro_charge2.png",
    "necro_ult_point_v1_p4.png": "assets/poses/necro_ult_point.png",
}


def main():
    parser = argparse.ArgumentParser()
    hits = glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*/*/PumpkinKiller/out"))
    parser.add_argument("--src-dir", default=hits[0] if hits else None)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.src_dir or not os.path.isdir(args.src_dir):
        print("ERROR no source folder")
        return 1
    failed = 0
    for name, dest in FRAMES.items():
        try:
            img = K.key(os.path.join(args.src_dir, name))
            box = K.bbox(img)
            if img.size != (1024, 1024) or img.getpixel((4, 4))[3] != 0:
                raise ValueError("size %s or background not transparent" % (img.size,))
            if args.apply:
                img.save(os.path.join(K.ROOT, dest), optimize=True)
            print("OK" if args.apply else "OK (dry)", name, "->", dest, "bbox", box)
        except Exception as exc:  # noqa: BLE001
            print("ERROR", name, repr(exc))
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
