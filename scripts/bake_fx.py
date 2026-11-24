#!/usr/bin/env python3
"""Bake effect sprite sheets from single effect images.

Usage: bake_fx.py <env_dir> <out_dir>

Reads fx_*.png and ui_target_ring.png (RGBA, transparent background) from
env_dir and writes one horizontal sheet per effect plus manifest.json.
Loop effects sample t in [0, 1) so the last frame leads back into the first.
"""
import json
import math
import os
import sys

from PIL import Image

CELL = 256

# name -> (frames, loop, motion)
EFFECTS = {
    "fx_charge_glow": (16, True, "spin_pulse"),
    "fx_muzzle_flash": (8, False, "pop_fade"),
    "fx_hit_spark": (8, False, "pop_fade"),
    "fx_impact_burst": (14, False, "grow_fade"),
    "ui_target_ring": (16, True, "pulse"),
}


def ease(t):
    return t * t * (3 - 2 * t)


def transform(t, motion):
    """Return scale, rotation in degrees and opacity for t."""
    if motion == "spin_pulse":
        return 0.82 + 0.1 * math.sin(2 * math.pi * t), 360 * t, 0.85 + 0.15 * math.sin(2 * math.pi * t)
    if motion == "pop_fade":
        return 0.4 + 0.5 * ease(min(t * 2, 1.0)), 0.0, 1.0 - max(0.0, (t - 0.4) / 0.6) ** 1.5
    if motion == "grow_fade":
        return 0.3 + 0.65 * ease(t), 0.0, 1.0 - max(0.0, (t - 0.5) / 0.5) ** 1.5
    if motion == "pulse":
        return 0.9 + 0.1 * math.sin(2 * math.pi * t), 0.0, 0.75 + 0.25 * math.sin(2 * math.pi * t)
    raise ValueError("unknown motion: " + motion)


def frame_for(img, t, motion):
    scale, rot, opacity = transform(t, motion)
    w, h = img.size
    k = CELL * 0.9 / max(w, h) * scale
    sized = img.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS)
    layer = Image.new("RGBA", (CELL * 2, CELL * 2), (0, 0, 0, 0))
    layer.paste(sized, (CELL - sized.width // 2, CELL - sized.height // 2), sized)
    layer = layer.rotate(rot, resample=Image.BICUBIC, center=(CELL, CELL))
    out = layer.crop((CELL // 2, CELL // 2, CELL // 2 + CELL, CELL // 2 + CELL))
    alpha = out.split()[3].point(lambda v: int(v * max(0.0, min(1.0, opacity))))
    out.putalpha(alpha)
    return out


def bake(env_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    manifest = {"cell": CELL, "effects": {}}
    for name, (frames, loop, motion) in EFFECTS.items():
        path = os.path.join(env_dir, name + ".png")
        if not os.path.isfile(path):
            print("ERROR missing " + path, file=sys.stderr)
            return 2
        img = Image.open(path).convert("RGBA")
        box = img.getbbox()
        if box is None:
            print("ERROR empty image " + path, file=sys.stderr)
            return 2
        img = img.crop(box)
        sheet = Image.new("RGBA", (CELL * frames, CELL), (0, 0, 0, 0))
        for i in range(frames):
            t = i / frames if loop else i / (frames - 1)
            sheet.paste(frame_for(img, t, motion), (i * CELL, 0))
        fname = name + "_sheet.png"
        sheet.save(os.path.join(out_dir, fname))
        manifest["effects"][name] = {"file": fname, "frames": frames, "loop": loop}
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print("OK baked %d effect sheets" % len(manifest["effects"]))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: bake_fx.py <env_dir> <out_dir>", file=sys.stderr)
        sys.exit(2)
    sys.exit(bake(sys.argv[1], sys.argv[2]))
