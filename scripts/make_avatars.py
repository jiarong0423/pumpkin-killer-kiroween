#!/usr/bin/env python3
"""Make square head avatars (assets/avatars/avatar_<hero>.png, 256 x 256) from the existing front portraits and unit pictures.
Original art only: a crop of our own pictures, nothing generated. Usage: python3 -B scripts/make_avatars.py
Each hero has a crop box given as fractions of the picture's opaque bounding box (x0, y0, x1, y1); a round-edged dark plate with a thin rim is drawn behind.
Logs to docs/audition/make_avatars.log; exit 1 on any failure."""
import os, sys, time
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "avatars")
LOG = os.path.join(ROOT, "docs", "audition", "make_avatars.log")
SIZE = 256
# hero -> (source file, crop box as fractions of the opaque bounding box)
SRC = {
    "skeleton":  ("assets/portraits/skeleton_front.png", (0.05, 0.00, 0.95, 0.45)),
    "wizard":    ("assets/portraits/wizard_front.png",   (0.08, 0.00, 0.92, 0.55)),
    "bat":       ("assets/ui/portrait_bat.png",          (0.18, 0.00, 1.00, 0.46)),
    "knight":    ("assets/portraits/knight_front.png",   (0.12, 0.00, 0.88, 0.50)),
    "reaper":    ("assets/portraits/reaper_front.png",   (0.12, 0.00, 0.88, 0.52)),
    "bride":     ("assets/portraits/bride_front.png",    (0.22, 0.00, 0.78, 0.30)),
    "hunchback": ("assets/portraits/hunchback_front.png",(0.22, 0.00, 0.78, 0.36)),
    "hag":       ("assets/portraits/hag_front.png",      (0.00, 0.00, 0.62, 0.40)),
}

def log(msg):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
    print(msg)

def make(hero, rel, frac):
    im = Image.open(os.path.join(ROOT, rel)).convert("RGBA")
    bb = im.getbbox()
    if not bb:
        raise RuntimeError("empty picture " + rel)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    x0 = bb[0] + int(w * frac[0]); x1 = bb[0] + int(w * frac[2])
    y0 = bb[1] + int(h * frac[1]); y1 = bb[1] + int(h * frac[3])
    side = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) // 2, y0 + side // 2
    box = (cx - side // 2, cy - side // 2, cx + side // 2, cy + side // 2)
    crop = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    crop.alpha_composite(im.crop((max(box[0], 0), max(box[1], 0), min(box[2], im.width), min(box[3], im.height))),
                         (max(0, -box[0]), max(0, -box[1])))
    crop = crop.resize((int(SIZE * 0.92), int(SIZE * 0.92)), Image.LANCZOS)
    plate = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(plate)
    d.rounded_rectangle((2, 2, SIZE - 3, SIZE - 3), radius=36, fill=(22, 14, 34, 255), outline=(255, 160, 60, 255), width=5)
    plate.alpha_composite(crop, ((SIZE - crop.width) // 2, (SIZE - crop.height) // 2 + 4))
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((2, 2, SIZE - 3, SIZE - 3), radius=36, fill=255)
    plate.putalpha(Image.composite(plate.getchannel("A"), Image.new("L", (SIZE, SIZE), 0), mask))
    os.makedirs(OUT, exist_ok=True)
    plate.save(os.path.join(OUT, "avatar_%s.png" % hero), optimize=True)

def main():
    failed = 0
    for hero, (rel, frac) in SRC.items():
        try:
            make(hero, rel, frac)
            log("OK avatar_%s.png from %s" % (hero, rel))
        except Exception as e:
            failed += 1
            log("ERROR %s: %s" % (hero, e))
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
