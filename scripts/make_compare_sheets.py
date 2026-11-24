#!/usr/bin/env python3
"""One comparison sheet per class for the art review: the class idle picture (the reference) on the left, every generated frame next to it.
Writes docs/audition/compare/<class>.png. Uses the raw Colab outputs (tag q1) so rejected pictures are shown too, keyed over a dark backdrop.
Usage: python3 -B scripts/make_compare_sheets.py [--tag q1] [--drive-out DIR]"""
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF = os.environ.get("PK_DRIVE_DIR", "<DRIVE_DIR>")
BG = (36, 32, 66)
CLASSES = ["skeleton", "wizard", "bat", "knight", "bride", "hunchback", "reaper"]
FRAMES = ["idle2", "charge1", "charge2", "charge3", "release", "empty", "hit"]


def keyed(path, size):
    a = np.asarray(Image.open(path).convert("RGB")).astype(float)
    mag = (a[..., 0] + a[..., 2]) / 2 - a[..., 1]
    al = np.clip((160 - mag) / 50, 0, 1)[..., None]
    out = Image.fromarray((a * al + (np.zeros_like(a) + np.array(BG, float)) * (1 - al)).astype(np.uint8))
    out.thumbnail((size, size))
    return out


def main(argv):
    ap = argparse.ArgumentParser(); ap.add_argument("--tag", default="q1"); ap.add_argument("--drive-out", default=DEF)
    a = ap.parse_args(argv)
    os.makedirs(os.path.join(ROOT, "docs", "audition", "compare"), exist_ok=True)
    cell = 300
    for cls in CLASSES:
        idle = os.path.join(ROOT, "assets", "poses", "%s_idle1.png" % cls)
        if not os.path.exists(idle):
            print("ERROR missing idle1 for", cls, file=sys.stderr); continue
        ref = Image.open(idle).convert("RGBA"); bg = Image.new("RGBA", ref.size, BG + (255,)); bg.alpha_composite(ref); ref = bg.convert("RGB"); ref.thumbnail((cell * 2, cell * 2))
        items = []
        for fr in FRAMES:
            p = os.path.join(a.drive_out, "pose_%s_%s_v1_%s.png" % (cls, fr, a.tag))
            if os.path.exists(p):
                items.append((fr, keyed(p, cell)))
        cols = 4
        rows = (len(items) + cols - 1) // cols
        W = Image.new("RGB", (cell * 2 + cols * cell, max(cell * 2, rows * (cell + 20))), BG)
        W.paste(ref, (0, 20))
        d = ImageDraw.Draw(W)
        d.text((8, 4), "REFERENCE idle1 (%s)" % cls, fill=(255, 255, 255))
        for i, (fr, im) in enumerate(items):
            x = cell * 2 + (i % cols) * cell; y = (i // cols) * (cell + 20)
            d.text((x + 6, y + 4), fr, fill=(255, 211, 42))
            W.paste(im, (x, y + 20))
        W.save(os.path.join(ROOT, "docs", "audition", "compare", cls + ".png"))
        print("OK", cls, len(items), "frames")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
