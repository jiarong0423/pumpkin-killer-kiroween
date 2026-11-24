#!/usr/bin/env python3
"""Key the flat magenta background out of Colab-generated item images and crop them tight.

Writes RGBA PNGs into assets/ui/ and assets/weapons/. Background pixels are ~245 on the "magenta-ness"
scale (mean(R,B) - G), artwork is below ~120; alpha ramps between 145 and 215; magenta spill is removed only from soft edge pixels.
Exit code 1 if any image fails; one log line per image.
Usage: python3 -B scripts/key_magenta_items.py [--drive-out DIR]
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.environ.get("PK_DRIVE_DIR", "<DRIVE_DIR>")
# source file on Drive -> destination inside the repo
JOBS = {
    "shield_bar_slab_blue_v2_r4.png": ("assets/ui/shield_slab_blue.png", "cyan_glow"),
    "shield_bar_slab_purple_v2_r4.png": "assets/ui/shield_slab_purple.png",
    "bat_dart_bag_v2_r4.png": "assets/weapons/dart_bag.png",   # owner picked v2 (final)
    "bat_shuriken_bag_v1_r4.png": "assets/weapons/shuriken_bag.png",
    "bat_dart_item_v1_r4.png": "assets/weapons/dart.png",
    "bat_shuriken_item_v1_r4.png": "assets/weapons/shuriken.png",   # the cat throws shuriken (owner 2026-11-09)
    "knight_small_shield_alone_v2_r4.png": "assets/weapons/small_shield.png",
    # Colab UI re-skin (U2, 2026-11-09) and effect sprites (FX1)
    "ui_top_plate_left_u2_v1_r4.png": ("assets/ui/top_plate_left.png", "tight"),
    "ui_top_plate_right_u2_v1_r4.png": ("assets/ui/top_plate_right.png", "tight"),
    "ui_dock_frame_u2_v1_r4.png": "assets/ui/dock_frame.png",
    "ui_plate_normal_u2_v1_r4.png": "assets/ui/plate_normal.png",
    "ui_plate_active_u2_v1_r4.png": ("assets/ui/plate_active.png", "tight"),
    "ui_lock_plate_u2_v1_r4.png": "assets/ui/lock_plate.png",
    "portrait_wizard_u2_v1_r4.png": "assets/ui/portrait_wizard.png",
    "ui_plate_hover_u2_v1_r4.png": ("assets/ui/plate_hover.png", "tight"),
    "ui_plate_disabled_u2_v1_r4.png": "assets/ui/plate_disabled.png",
    "ui_icon_normal_u2_v1_r4.png": "assets/ui/icon_normal.png",
    "ui_icon_double_u2_v1_r4.png": "assets/ui/icon_double.png",
    "ui_icon_heavy_u2_v1_r4.png": "assets/ui/icon_heavy.png",
    "ui_icon_heal_u2_v1_r4.png": "assets/ui/icon_heal.png",
    "ui_power_unlit_u2_v1_r4.png": "assets/ui/power_unlit.png",
    "ui_power_orange_u2_v1_r4.png": ("assets/ui/power_orange.png", "tight"),
    "ui_power_hot_u2_v1_r4.png": ("assets/ui/power_hot.png", "tight"),
    "ui_socket_ammo_u2_v1_r4.png": "assets/ui/socket_ammo.png",
    "ui_socket_special_u2_v1_r4.png": ("assets/ui/socket_special.png", "tight"),
    "ui_btn_sound_u2_v1_r4.png": "assets/ui/btn_sound.png",
    "ui_btn_reset_u2_v1_r4.png": "assets/ui/btn_reset.png",
    "ui_top_center_plate_u2_v1_r4.png": "assets/ui/top_center_plate.png",
    "ui_hp_frame_u2_v1_r4.png": "assets/ui/hp_frame.png",
    "ui_hp_fill_u2_v1_r4.png": "assets/ui/hp_fill.png",
    "ui_wind_frame_u2_v1_r4.png": "assets/ui/wind_frame.png",
    "ui_wind_arrow_u2_v1_r4.png": "assets/ui/wind_arrow.png",
    "ui_candle_u2_v1_r4.png": ("assets/ui/candle.png", "tight"),
    "ui_ghostfire_cyan_u2_v1_r4.png": ("assets/ui/ghostfire_cyan.png", "cyan_glow"),
    "ui_ghostfire_violet_u2_v1_r4.png": ("assets/ui/ghostfire_violet.png", "tight"),
    "env_fence_damaged_u2_v1_r4.png": "assets/env/fence_black_damaged.png",
    "env_fence_broken_u2_v1_r4.png": "assets/env/fence_black_broken.png",
    "drop_crate_v1_r4.png": "assets/env/drop_crate.png",
    "drop_parachute_v1_r4.png": "assets/env/drop_parachute.png",
    "portrait_skeleton_u2_v1_r4.png": "assets/ui/portrait_skeleton.png",
    "portrait_bat_u2_v1_r4.png": "assets/ui/portrait_bat.png",
    "portrait_knight_u2_v1_r4.png": "assets/ui/portrait_knight.png",
    "env_fence_intact_u2_v1_r4.png": "assets/env/fence_black_intact.png",
    "fx_ghostfire_v1_r4.png": ("assets/fx/sprites/fx_ghostfire.png", "cyan_glow"),
    "fx_rune_circle_v1_r4.png": ("assets/fx/sprites/fx_rune_circle.png", "tight"),
    "fx_stardust_v1_r4.png": ("assets/fx/sprites/fx_stardust.png", "tight"),
    "fx_spirit_mist_v1_r4.png": ("assets/fx/sprites/fx_spirit_mist.png", "cyan_glow"),
    "fx_impact_flash_v1_r4.png": "assets/fx/sprites/fx_impact_flash.png",
    "fx_poison_bubbles_v1_r4.png": ("assets/fx/sprites/fx_poison_bubbles.png", "tight"),
    "drop_ghost_v1_r4.png": "assets/env/drop_ghost.png",
    "drop_crate_v1_r4.png": "assets/env/drop_crate.png",
    "drop_parachute_v1_r4.png": "assets/env/drop_parachute.png",
    "bride_idle_v1_r4.png": "assets/units/unit_bride_idle.png",   # owner approved v1 (2026-11-09)
    "reaper_flame_idle2_v2_r13.png": "assets/units/unit_reaper_idle.png",   # necromancer: raised hand pinching the flame on the fingertip; the OWNER picked v2 (2026-11-09), over my v1
    "reaper_flame_idle_v1_r11.png": "assets/units/unit_reaper_idle_lowpalm.png",   # necromancer (internal id reaper): owner picked v1, purple flame above the open palm, no scythe
    "fx_ghostfire_purple_v1_r12.png": ("assets/fx/sprites/fx_ghostfire_purple.png", "tight"),   # single purple flame for the circling necromancer fires
    "hunchback_idle_v1_r8.png": "assets/units/unit_hunchback_idle.png",   # Qwen-Image-Edit-2511 r8: giant axe, ragged clothes
    "portrait_skeleton_v1_r4.png": "assets/ui/portrait_skeleton.png",
    "portrait_bat_v1_r4.png": "assets/ui/portrait_bat.png",
    "portrait_knight_v1_r4.png": "assets/ui/portrait_knight.png",
}


BG = np.array([251.0, 0.0, 247.0])      # the flat magenta background colour
CYAN = np.array([0.0, 220.0, 255.0])    # colour of a cyan glow before it was blended with the background


def unmix_cyan_glow(a, mag):
    """A cyan glow blended with magenta gives a violet fringe. Treat such pixels as glow = alpha * cyan + (1 - alpha) * magenta:
    solve alpha from the magenta-ness and recover the real glow colour. Pixels that are not on the magenta-cyan line
    (orange candle flames, wood, bone) are left alone."""
    mag_cyan = (CYAN[0] + CYAN[2]) / 2 - CYAN[1]
    bg_mag = (BG[0] + BG[2]) / 2 - BG[1]
    alpha = np.clip((bg_mag - mag) / (bg_mag - mag_cyan), 0, 1)
    cand = (mag > 25) & (mag < 240) & (a[..., 2] >= a[..., 0] * 0.9) & (a[..., 1] > 20)
    safe = np.maximum(alpha, 1e-3)[..., None]
    fg = np.clip((a - (1 - alpha)[..., None] * BG) / safe, 0, 255)
    return cand, alpha, fg


def key_and_crop(path, mode="plain"):
    a = np.asarray(Image.open(path).convert("RGB")).astype(float)
    mag = (a[..., 0] + a[..., 2]) / 2 - a[..., 1]
    alpha = np.clip((215 - mag) / 70, 0, 1)
    # spill removal only on soft edge pixels: opaque violet / purple art must keep its colour (it is close to magenta)
    spill = np.maximum(0, mag) * 0.9 * (1 - alpha)
    rgb = a.copy()
    rgb[..., 0] = np.clip(a[..., 0] - spill, 0, 255)
    rgb[..., 2] = np.clip(a[..., 2] - spill, 0, 255)
    if mode == "tight":
        # glowing art whose halo blended with magenta (pink fringe): cut the halo harder and pull the leftover pink toward the green channel
        alpha = np.clip((140 - mag) / 50, 0, 1)
        spill2 = np.maximum(0, mag) * 0.95 * (1 - alpha)
        rgb = a.copy()
        rgb[..., 0] = np.clip(a[..., 0] - spill2, 0, 255)
        rgb[..., 2] = np.clip(a[..., 2] - spill2, 0, 255)
    if mode == "cyan_glow":
        cand, ga, fg = unmix_cyan_glow(a, mag)
        rgb = np.where(cand[..., None], fg, rgb)
        alpha = np.where(cand, ga, alpha)
    out = Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA")
    al = np.asarray(out.getchannel("A"))
    rows = np.where((al > 40).sum(axis=1) > 6)[0]
    cols = np.where((al > 40).sum(axis=0) > 6)[0]
    if len(rows) == 0 or len(cols) == 0:
        raise ValueError("nothing left after keying")
    pad = 6
    box = (max(0, cols.min() - pad), max(0, rows.min() - pad),
           min(out.width, cols.max() + pad + 1), min(out.height, rows.max() + pad + 1))
    return out.crop(box)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drive-out", default=DEFAULT_OUT)
    args = ap.parse_args()
    failed = 0
    for src, spec in JOBS.items():
        dst, mode = spec if isinstance(spec, tuple) else (spec, "plain")
        try:
            img = key_and_crop(os.path.join(args.drive_out, src), mode)
            target = os.path.join(ROOT, dst)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            img.save(target)
            print("OK    %s -> %s %s" % (src, dst, img.size))
        except Exception as e:
            failed += 1
            print("ERROR %s: %r" % (src, e))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
