#!/usr/bin/env python3
"""Install the generated avatar pictures (Colab outputs avatar_<hero>_v1_p4.png, magenta #FF00FF background) as assets/avatars/avatar_<hero>.png (256 x 256).
Steps per hero: key the magenta to transparent (distance below 70 = clear, 70 to 150 = soft edge with the magenta spill removed), crop to the opaque box,
pad to a square with a margin, scale into the rounded plate (dark fill, orange rim) used by every avatar. A picture whose opaque box touches the canvas edge on the
top or on a side by more than 40 percent of that side is reported as WARN (a bust may be cut by the bottom edge on purpose).
Usage: python3 -B scripts/install_avatars.py [--src DIR] [--heroes a,b] ; logs to docs/audition/install_avatars.log ; exit 1 on a missing source or a failed hero."""
import argparse, glob, os, sys, time
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "docs", "audition", "install_avatars.log")
HEROES = ["skeleton", "wizard", "bat", "knight", "reaper", "bride", "hunchback", "hag"]
SIZE = 256
BUST = {"bride": (0.16, 0.84, 0.60)}   # (x0, x1, height share) of the opaque box

def log(msg):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
    print(msg)

def key_magenta(im):
    im = im.convert("RGBA"); px = im.load(); w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            d = ((r - 255) ** 2 + g ** 2 + (b - 255) ** 2) ** 0.5
            if d < 70:
                px[x, y] = (0, 0, 0, 0)
            elif d < 150:
                t = (d - 70) / 80.0
                # remove the magenta spill from the soft edge: pull red and blue toward green
                m = min(r, b) - g
                if m > 0:
                    r = int(r - m * (1 - t)); b = int(b - m * (1 - t))
                px[x, y] = (max(0, r), g, max(0, b), int(255 * t))
    return im

def make(hero, src):
    im = key_magenta(Image.open(src))
    bb = im.getbbox()
    if not bb:
        raise RuntimeError("empty after keying")
    w, h = im.size
    if bb[1] <= 2 and (bb[2] - bb[0]) > 0.4 * w and False:
        log("WARN %s touches the top edge" % hero)
    keep = BUST.get(hero)   # owner 2026-11-16: a half-body (bust) avatar is enough; full-length figures are cut to the upper part
    if keep:
        w0, h0 = bb[2] - bb[0], bb[3] - bb[1]
        bb = (bb[0] + int(w0 * keep[0]), bb[1], bb[0] + int(w0 * keep[1]), bb[1] + int(h0 * keep[2]))
    crop = im.crop(bb)
    side = int(max(crop.size) * 1.10)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.alpha_composite(crop, ((side - crop.width) // 2, (side - crop.height) // 2))
    sq = sq.resize((int(SIZE * 0.88), int(SIZE * 0.88)), Image.LANCZOS)
    plate = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(plate)
    d.rounded_rectangle((2, 2, SIZE - 3, SIZE - 3), radius=36, fill=(22, 14, 34, 255), outline=(255, 160, 60, 255), width=5)
    plate.alpha_composite(sq, ((SIZE - sq.width) // 2, (SIZE - sq.height) // 2))
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((2, 2, SIZE - 3, SIZE - 3), radius=36, fill=255)
    a = plate.getchannel("A"); plate.putalpha(Image.composite(a, Image.new("L", (SIZE, SIZE), 0), mask))
    out = os.path.join(ROOT, "assets", "avatars", "avatar_%s.png" % hero)
    plate.save(out, optimize=True)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="")
    ap.add_argument("--heroes", default=",".join(HEROES))
    a = ap.parse_args()
    src = a.src or (sorted(glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*/*/PumpkinKiller/out"))) or [""])[0]
    if not src or not os.path.isdir(src):
        log("ERROR source folder not found"); return 1
    failed = 0
    for hero in a.heroes.split(","):
        p = os.path.join(src, "avatar_%s_v1_p4.png" % hero)
        if not os.path.isfile(p):
            log("ERROR missing %s" % p); failed += 1; continue
        try:
            log("OK %s from %s" % (make(hero, p), os.path.basename(p)))
        except Exception as e:
            log("ERROR %s: %s" % (hero, e)); failed += 1
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
