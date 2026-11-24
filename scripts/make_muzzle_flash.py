#!/usr/bin/env python3
"""Draw the muzzle flash effect procedurally (no model, no faces).

Usage: make_muzzle_flash.py <out_png>

A star burst pointing right: dark outline, orange outer star, yellow middle,
white-hot core, plus a soft glow. Transparent background, 512x512.
"""
import math
import sys

from PIL import Image, ImageDraw, ImageFilter

SIZE = 512
CX, CY = 150, 256


def star(points, inner, outer_right, outer_side):
    pts = []
    for i in range(points * 2):
        a = math.pi * i / points
        if i % 2 == 0:
            side = abs(math.cos(a))
            r = outer_side + (outer_right - outer_side) * (side ** 3 if math.cos(a) > 0 else 0)
        else:
            r = inner
        pts.append((CX + r * math.cos(a), CY + r * math.sin(a)))
    return pts


def main(out):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(glow).polygon(star(10, 95, 330, 150), fill=(255, 150, 20, 150))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(22)))
    d = ImageDraw.Draw(img)
    d.polygon(star(10, 90, 345, 160), fill=(45, 18, 70, 255))
    d.polygon(star(10, 82, 320, 145), fill=(255, 110, 10, 255))
    d.polygon(star(10, 60, 250, 105), fill=(255, 205, 40, 255))
    d.polygon(star(10, 36, 150, 62), fill=(255, 250, 220, 255))
    img.save(out)
    print("OK wrote " + out)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: make_muzzle_flash.py <out_png>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
