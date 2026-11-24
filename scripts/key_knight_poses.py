#!/usr/bin/env python3
"""Key the magenta background out of the three Colab pictures of the shield-less knight (wind-up with the small buckler, release with an empty hand, hit)
and install them as assets/poses/knight_unarmed_{windup,release,hit}.png on the same 1024 canvas as assets/units/unit_knight_unarmed.png.

The feet line of each frame must sit within 12 px of the idle art (bottom of the bounding box); otherwise it is reported and NOT installed.
Usage: python3 -B scripts/key_knight_poses.py [--src-dir DIR] [--dry-run]    (default src dir: the Drive 'out' folder found under ~/Library/CloudStorage)
Exit code 1 if any frame is missing or fails a check; one log line per frame.
"""
import argparse
import glob
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import key_knight_unarmed as K  # noqa: E402

ROOT = K.ROOT
FRAMES = {
    "pose_knight_unarmed_windup_v1_p4.png": "assets/poses/knight_unarmed_windup.png",
    "pose_knight_unarmed_release_v1_p4.png": "assets/poses/knight_unarmed_release.png",
    "pose_knight_unarmed_hit_v1_p4.png": "assets/poses/knight_unarmed_hit.png",
}


def find_drive_out():
    hits = glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*/*/PumpkinKiller/out"))
    return hits[0] if hits else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src-dir", default=find_drive_out())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.src_dir or not os.path.isdir(args.src_dir):
        print("ERROR no source folder")
        return 1
    idle = Image.open(K.DEST).convert("RGBA")
    idle_bottom = K.bbox(idle)[3]
    failed = 0
    for name, dest in FRAMES.items():
        src = os.path.join(args.src_dir, name)
        try:
            if not os.path.exists(src):
                print("MISSING", name)
                failed += 1
                continue
            img = K.key(src)
            box = K.bbox(img)
            if img.size != idle.size or abs(box[3] - idle_bottom) > 12:
                print("ERROR", name, "size", img.size, "bbox", box, "idle bottom", idle_bottom)
                failed += 1
                continue
            if img.getpixel((4, 4))[3] != 0:
                print("ERROR", name, "background corner not transparent")
                failed += 1
                continue
            if args.dry_run:
                print("OK (dry)", name, "bbox", box)
            else:
                img.save(os.path.join(ROOT, dest), optimize=True)
                print("OK", name, "->", dest, "bbox", box)
        except Exception as exc:  # noqa: BLE001
            print("ERROR", name, repr(exc))
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
