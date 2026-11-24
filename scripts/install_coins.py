#!/usr/bin/env python3
"""Install owner-approved pumpkin coin faces as 512px transparent UI assets.

The Colab files use #FF00FF backgrounds. This script removes that matte, crops
exactly to each opaque picture, and scales the result to a 512 x 512 RGBA PNG.
Run: python3 -B scripts/install_coins.py [--src DIR]
"""
import argparse
import glob
import os
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SIZE = 512
SOURCES = {
    "head": "coin_pumpkin_head_v1_p4.png",
    "tail": "coin_pumpkin_tail_v1_p4.png",
}


def key_magenta(image):
    """Remove the Colab magenta matte while retaining antialiased edges."""
    image = image.convert("RGBA")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, alpha = pixels[x, y]
            distance = ((red - 255) ** 2 + green ** 2 + (blue - 255) ** 2) ** 0.5
            if distance < 70:
                pixels[x, y] = (0, 0, 0, 0)
            elif distance < 150:
                opacity = int(255 * (distance - 70) / 80)
                spill = max(0, min(red, blue) - green)
                pixels[x, y] = (red - spill, green, blue - spill, opacity)
    return image


def source_dir(value):
    if value:
        return Path(value).expanduser()
    candidates = sorted(glob.glob(os.path.expanduser(
        "~/Library/CloudStorage/GoogleDrive-*/*/PumpkinKiller/out")))
    return Path(candidates[0]) if candidates else None


def install(name, source):
    keyed = key_magenta(Image.open(source))
    bounds = keyed.getbbox()
    if not bounds:
        raise RuntimeError("empty after magenta keying")
    cropped = keyed.crop(bounds)
    resized = cropped.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    output = ROOT / "assets" / "ui" / ("coin_pumpkin_%s.png" % name)
    output.parent.mkdir(parents=True, exist_ok=True)
    resized.save(output, optimize=True)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="owner's Colab output directory")
    args = parser.parse_args(argv)
    directory = source_dir(args.src)
    if not directory or not directory.is_dir():
        print("ERROR source folder not found; pass --src ~/Library/CloudStorage/GoogleDrive-*/<account>/PumpkinKiller/out", file=sys.stderr)
        return 1
    failed = False
    for name, filename in SOURCES.items():
        source = directory / filename
        if not source.is_file():
            print("ERROR missing %s" % source, file=sys.stderr)
            failed = True
            continue
        try:
            output = install(name, source)
            print("OK %s from %s" % (output.relative_to(ROOT), filename))
        except (OSError, RuntimeError) as error:
            print("ERROR %s: %s" % (filename, error), file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
