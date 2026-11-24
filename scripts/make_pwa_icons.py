#!/usr/bin/env python3
"""Create deterministic PWA icons from the game's existing skeleton unit art."""
import argparse
import hashlib
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "units" / "unit_skeleton.png"
ICONS = {
    "icons/icon-192.png": (192, False),
    "icons/icon-512.png": (512, False),
    "icons/icon-maskable-512.png": (512, True),
}
# Filled from the deterministic --apply output.  It detects accidental source
# changes and makes icon rebuilds auditable without adding a runtime dependency.
KNOWN_CHECKSUMS = {
    "assets/units/unit_skeleton.png": "56680273a3f09b70311b418d1427f25a05cf33c5e318e0aa5c7aab658879c627",
    "icons/icon-192.png": "bffd724bb5722245db199887061b88f141fab4181d5d5fc58cb9c558e94a21ed",
    "icons/icon-512.png": "97c72912675441d564f1ff93ef513b46f1ca6edc7a58f2c39db832a279853d5f",
    "icons/icon-maskable-512.png": "2d220566e1a325067b1618204de2d6079c22475cce96a2c3a956621616ec4269",
}
PROVENANCE = ROOT / "docs" / "ASSET_PROVENANCE.md"
PROVENANCE_ROW = "| `icons/` | Installable-web-app icons: 192 px, 512 px, and maskable 512 px PNGs | Deterministically cropped from `assets/units/unit_skeleton.png` by `scripts/make_pwa_icons.py` | Python Pillow | 2026-11-15 | Derived from the original skeleton unit art, so it follows that art's status (unknown - owner to confirm) |\n"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_icon(source, size, maskable):
    if maskable:
        canvas = Image.new("RGBA", (size, size), "#05020a")
        safe_size = size * 3 // 4
        art = ImageOps.fit(source, (safe_size, safe_size), method=Image.Resampling.LANCZOS, centering=(0.5, 0.38))
        offset = (size - safe_size) // 2
        canvas.alpha_composite(art, (offset, offset))
        return canvas
    return ImageOps.fit(source, (size, size), method=Image.Resampling.LANCZOS, centering=(0.5, 0.38))


def write_provenance():
    text = PROVENANCE.read_text(encoding="utf-8")
    if PROVENANCE_ROW in text:
        return
    anchor = "| `assets/units/unit_*.png`, `unit_*_raw.png` (bat, knight, skeleton, wizard) | Original 1024 px unit art, facing left | Made before the Kiro credits were approved (2026-11-04); `docs/ROLES.md` and `docs/game_mode.md` call this art placeholder AI-generated art | unknown - owner to confirm | unknown - owner to confirm | unknown - owner to confirm |\n"
    if anchor not in text:
        raise ValueError("asset provenance table anchor is missing")
    PROVENANCE.write_text(text.replace(anchor, anchor + PROVENANCE_ROW), encoding="utf-8")


def current_checksums():
    values = {"assets/units/unit_skeleton.png": sha256(SOURCE)}
    values.update({name: sha256(ROOT / name) for name in ICONS})
    return values


def verify_icons():
    for name, (size, _) in ICONS.items():
        path = ROOT / name
        if not path.is_file():
            raise ValueError("missing %s" % name)
        with Image.open(path) as image:
            if image.size != (size, size):
                raise ValueError("%s is %s, expected %dx%d" % (name, image.size, size, size))
    checksums = current_checksums()
    for name, expected in KNOWN_CHECKSUMS.items():
        if checksums.get(name) != expected:
            raise ValueError("checksum changed for %s" % name)
    return checksums


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write icons and their provenance row")
    args = parser.parse_args(argv)
    try:
        if not args.apply:
            checksums = verify_icons()
            print("OK PWA icons are current (%s)" % checksums["assets/units/unit_skeleton.png"][:12])
            return 0
        if not SOURCE.is_file():
            raise ValueError("missing source artwork %s" % SOURCE.relative_to(ROOT))
        with Image.open(SOURCE) as opened:
            source = opened.convert("RGBA")
        for name, (size, maskable) in ICONS.items():
            path = ROOT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            render_icon(source, size, maskable).save(path, "PNG", optimize=False, compress_level=9)
        write_provenance()
        checksums = verify_icons()
        print("OK wrote PWA icons")
        for name in sorted(checksums):
            print("%s %s" % (name, checksums[name]))
        return 0
    except (OSError, ValueError) as error:
        print("ERROR %s" % error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
