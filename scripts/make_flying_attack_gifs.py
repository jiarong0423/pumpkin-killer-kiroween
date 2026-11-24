#!/usr/bin/env python3
"""Generate true attack animations with flying projectiles and muzzle flash for all 4 heroes.

Key Improvements (Kiroween v2.0):
1. FIXED Launch Point: Shifted launch anchors forward from back/chest (X:145) to true front muzzle/hand (X:200~215).
2. TRUE Weapon Detachment: When projectile enters flight (frames 8-18), the hand weapon is removed/masked from character layer.
3. Realistic Biomechanical Timing: Anticipation -> explosive forward swing -> front release peak -> empty-hand recovery.
4. Tangent Tracking for spears and spinning physics for mortars/bombs.
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SPRITES_DIR = os.environ.get("PK_SPRITES_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "sprites"))
ENV_DIR = os.environ.get("PK_ENV_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "env"))
FX_DIR = os.environ.get("PK_FX_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fx"))
OUT_DIR = os.environ.get("PK_GIF_OUTPUT_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "gifs"))

CELL = 256
OUT_W = 512
OUT_H = 256
FPS = 12
FRAME_MS = int(1000 / FPS)  # ~83ms
BG_COLOR = (18, 10, 32)  # Dark Halloween midnight

os.makedirs(OUT_DIR, exist_ok=True)


def slice_sheet(path, cell=CELL):
    if not os.path.exists(path):
        return []
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    n = w // cell
    return [im.crop((i * cell, 0, (i + 1) * cell, h)) for i in range(n)]


def get_cropped(path, max_w, max_h):
    if not os.path.exists(path):
        return None
    im = Image.open(path).convert("RGBA")
    bbox = im.getbbox()
    if not bbox:
        return None
    c = im.crop(bbox)
    c.thumbnail((max_w, max_h), Image.LANCZOS)
    return c


# Preload FX sheets
FLASH_FRAMES = slice_sheet(os.path.join(FX_DIR, "fx_muzzle_flash_sheet.png"), cell=CELL)
BURST_FRAMES = slice_sheet(os.path.join(FX_DIR, "fx_impact_burst_sheet.png"), cell=CELL)
CHARGE_FRAMES = slice_sheet(os.path.join(FX_DIR, "fx_charge_glow_sheet.png"), cell=CELL)

# Preload Projectiles
PROJ_DAGGER = get_cropped(os.path.join(ENV_DIR, "proj_dagger.png"), 75, 30)
PROJ_PUMPKIN = get_cropped(os.path.join(ENV_DIR, "proj_pumpkin.png"), 60, 60)
PROJ_SPEAR = get_cropped(os.path.join(ENV_DIR, "proj_spear.png"), 110, 25)

# Unit configurations with CORRECTED front release points
CONFIGS = {
    "unit_bat": {
        "name": "蝙蝠貓刺客",
        "weapon_name": "銀色短匕首",
        "dmg": "直擊 14 傷害",
        "launch_pt": (205, 135),  # Front paw throwing release point
        "target_pt": (465, 175),
        "traj_type": "flat",      # Fast low dart trajectory
        "proj_img": PROJ_DAGGER,
        "color": (162, 155, 254),
        "weapon_bbox_in_cell": (145, 110, 215, 175) # hand weapon zone to mask on detachment
    },
    "unit_wizard": {
        "name": "南瓜巫師炮手",
        "weapon_name": "南瓜重型迫擊砲",
        "dmg": "直擊 26 + 範圍 10 傷害",
        "launch_pt": (215, 105),  # Front cannon barrel muzzle
        "target_pt": (465, 215),
        "traj_type": "high_arc",  # High mortar arc
        "proj_img": PROJ_PUMPKIN,
        "color": (255, 159, 67),
        "weapon_bbox_in_cell": (160, 75, 230, 140)
    },
    "unit_skeleton": {
        "name": "骷髏長矛兵",
        "weapon_name": "零重力符文骨矛",
        "dmg": "直擊 18 傷害 (可反彈)",
        "launch_pt": (220, 115),  # Extended spear tip at throw release
        "target_pt": (470, 132),
        "traj_type": "laser",     # Zero gravity linear throw
        "proj_img": PROJ_SPEAR,
        "color": (0, 210, 211),
        "weapon_bbox_in_cell": (145, 70, 235, 150)
    },
    "unit_knight": {
        "name": "南瓜重裝盾衛",
        "weapon_name": "硬殼巨石重彈",
        "dmg": "直擊 18 傷害",
        "launch_pt": (210, 135),  # Pushing palm release
        "target_pt": (465, 215),
        "traj_type": "medium_arc",# Heavy parabolic arc
        "proj_img": PROJ_PUMPKIN,
        "color": (77, 238, 234),
        "weapon_bbox_in_cell": (150, 100, 220, 175)
    }
}


def mask_hand_weapon(char_img, weapon_box):
    """Cleanly mask the hand weapon area when the projectile is airborne."""
    if not weapon_box:
        return char_img
    img = char_img.copy()
    w_min_x, w_min_y, w_max_x, w_max_y = weapon_box
    
    # Soft circular gradient mask to simulate empty hands without sharp rectangular holes
    mask = Image.new("L", (CELL, CELL), 255)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([w_min_x, w_min_y, w_max_x, w_max_y], fill=30)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=8))
    
    r, g, b, a = img.split()
    a_arr = np.array(a, dtype=np.float32)
    m_arr = np.array(mask, dtype=np.float32) / 255.0
    new_a = np.clip(a_arr * m_arr, 0, 255).astype(np.uint8)
    img.putalpha(Image.fromarray(new_a))
    return img


def calc_trajectory(cfg, t):
    """Calculate projectile position (x, y) and rotation angle for t in [0, 1]."""
    x0, y0 = cfg["launch_pt"]
    x1, y1 = cfg["target_pt"]
    dx = x1 - x0

    x = x0 + dx * t
    traj = cfg["traj_type"]

    if traj == "flat":
        # Swift flat trajectory with tangent rotation
        y = y0 + (y1 - y0) * t - 30 * math.sin(math.pi * t)
        # derivative for tangent
        dy_dt = (y1 - y0) - 30 * math.pi * math.cos(math.pi * t)
        angle = math.degrees(math.atan2(dy_dt, dx))
    elif traj == "high_arc":
        # High soaring mortar arc with continuous tumbling spin
        apex_h = 110
        y = (1 - t) * y0 + t * y1 - apex_h * math.sin(math.pi * t)
        angle = -45 + 540 * t  # 1.5 full tumbling spins
    elif traj == "laser":
        # Flat spear thrust, tip always strictly pointing forward
        y = y0 + (y1 - y0) * t
        dy_dt = (y1 - y0)
        angle = math.degrees(math.atan2(dy_dt, dx))
    elif traj == "medium_arc":
        # Medium heavy throw with solid tumbling spin
        apex_h = 65
        y = (1 - t) * y0 + t * y1 - apex_h * math.sin(math.pi * t)
        angle = -30 + 360 * t
    else:
        y = y0 + (y1 - y0) * t
        angle = 0

    return x, y, angle


def render_attack_frames(unit_id, team="red"):
    cfg = CONFIGS[unit_id]
    charge_f = slice_sheet(os.path.join(SPRITES_DIR, f"{unit_id}_{team}_arm_charge.png"))
    throw_f = slice_sheet(os.path.join(SPRITES_DIR, f"{unit_id}_{team}_arm_throw.png"))
    idle_f = slice_sheet(os.path.join(SPRITES_DIR, f"{unit_id}_{team}_idle.png"))

    TOTAL_FRAMES = 24
    frames = []

    # Timeline layout:
    # 0 ~ 5: Anticipation & Power Charge (leaning back)
    # 6: Forward Acceleration Swing
    # 7: PEAK RELEASE POINT (Flash + Projectile Detaches at front muzzle/hand)
    # 8 ~ 17: Airborne Flight (Character hand is EMPTY, projectile travels)
    # 18 ~ 21: Impact burst at target
    # 22 ~ 23: Settle / recovery back to idle

    for i in range(TOTAL_FRAMES):
        canvas = Image.new("RGBA", (OUT_W, OUT_H), BG_COLOR + (255,))
        d = ImageDraw.Draw(canvas)

        # Ground line and spooky graveyard base
        d.line([(0, 236), (OUT_W, 236)], fill=(70, 45, 95), width=3)
        d.rectangle([(0, 237), (OUT_W, OUT_H)], fill=(25, 14, 40))

        # Target tombstone on the right
        tx, ty = cfg["target_pt"][0] + 15, 236
        d.line([(tx, ty - 45), (tx, ty)], fill=(60, 40, 80), width=6)
        d.text((tx, ty - 60), "敵方目標", fill=(120, 100, 150), anchor="mm")

        # 1. Determine Character Animation Pose
        if i < 6:
            # Charging (hold weapon back)
            c_idx = min(i, len(charge_f) - 1)
            char_img = charge_f[c_idx]
        elif i == 6:
            # Forward swing acceleration
            t_idx = min(2, len(throw_f) - 1)
            char_img = throw_f[t_idx]
        elif i == 7:
            # RELEASE FRAME: Maximum forward thrust peak
            t_idx = min(3, len(throw_f) - 1)
            char_img = throw_f[t_idx]
        elif i < 18:
            # Follow-through RECOVERY: Weapon has DETACHED! Hand is empty!
            t_idx = min(4 + (i - 8) // 2, len(throw_f) - 1)
            raw_char = throw_f[t_idx]
            # MASK weapon from hand so weapon is NOT duplicated on body
            char_img = mask_hand_weapon(raw_char, cfg["weapon_bbox_in_cell"])
        else:
            # Idle recovery
            id_idx = (i - 18) % len(idle_f)
            char_img = idle_f[id_idx]

        # Paste character on left (x=10, y=0)
        canvas.paste(char_img, (10, 0), char_img)

        # 2. Charge Aura FX during charging (frames 2~5)
        if 2 <= i <= 5 and CHARGE_FRAMES:
            glow = CHARGE_FRAMES[(i - 2) * 2 % len(CHARGE_FRAMES)]
            g_scaled = glow.resize((100, 100), Image.LANCZOS)
            canvas.paste(g_scaled, (cfg["launch_pt"][0] - 65, cfg["launch_pt"][1] - 45), g_scaled)

        # 3. Muzzle Flash strictly on FRONT launch point (frames 7~9)
        if 7 <= i <= 9 and FLASH_FRAMES:
            f_idx = i - 7
            if f_idx < len(FLASH_FRAMES):
                flash = FLASH_FRAMES[f_idx]
                f_scaled = flash.resize((100, 100), Image.LANCZOS)
                canvas.paste(f_scaled, (cfg["launch_pt"][0] - 40, cfg["launch_pt"][1] - 50), f_scaled)

        # 4. Flying Projectile during flight (frames 8~17)
        if 8 <= i <= 17:
            t = (i - 8) / 9.0  # normalized time [0.0, 1.0]
            x, y, angle = calc_trajectory(cfg, t)

            proj = cfg["proj_img"]
            if proj:
                # Rotate projectile dynamically (tangent or spin)
                rotated = proj.rotate(-angle, expand=True, resample=Image.BICUBIC)
                w, h = rotated.size
                canvas.paste(rotated, (int(x - w / 2), int(y - h / 2)), rotated)

            # Trajectory motion trail sparks
            trail_color = cfg["color"]
            for trail_k in range(1, 4):
                tt = max(0.0, t - trail_k * 0.08)
                tx, ty, _ = calc_trajectory(cfg, tt)
                radius = max(1, 4 - trail_k)
                alpha_spark = int(220 / (trail_k + 0.5))
                spark_c = (trail_color[0], trail_color[1], trail_color[2], alpha_spark)
                sp_img = Image.new("RGBA", (radius * 2, radius * 2), spark_c)
                canvas.paste(sp_img, (int(tx - radius), int(ty - radius)), sp_img)

        # 5. Impact Burst FX at target (frames 17~21)
        if 17 <= i <= 21 and BURST_FRAMES:
            b_idx = i - 17
            if b_idx < len(BURST_FRAMES):
                burst = BURST_FRAMES[b_idx]
                b_scaled = burst.resize((140, 140), Image.LANCZOS)
                canvas.paste(b_scaled, (cfg["target_pt"][0] - 70, cfg["target_pt"][1] - 70), b_scaled)

        # 6. Hero HUD Banner
        d.rectangle([(0, 0), (OUT_W, 28)], fill=(10, 5, 20, 230))
        d.text((12, 6), f"【{cfg['name']}】破空投擲", fill=(255, 255, 255))
        d.text((170, 6), f"武器: {cfg['weapon_name']}", fill=cfg["color"])
        d.text((360, 6), cfg["dmg"], fill=(255, 215, 0))

        frames.append(canvas.convert("RGB"))

    return frames


def build_quad_gif(all_frames):
    """Combine 4 heroes into a 2x2 arena attack GIF."""
    quad_w = OUT_W * 2
    quad_h = OUT_H * 2
    n_frames = len(all_frames["unit_bat"])
    quad_frames = []

    order = ["unit_bat", "unit_wizard", "unit_skeleton", "unit_knight"]

    for i in range(n_frames):
        canvas = Image.new("RGB", (quad_w, quad_h))
        # Top-left: Bat
        canvas.paste(all_frames[order[0]][i], (0, 0))
        # Top-right: Wizard
        canvas.paste(all_frames[order[1]][i], (OUT_W, 0))
        # Bottom-left: Skeleton
        canvas.paste(all_frames[order[2]][i], (0, OUT_H))
        # Bottom-right: Knight
        canvas.paste(all_frames[order[3]][i], (OUT_W, OUT_H))

        draw = ImageDraw.Draw(canvas)
        draw.line([(OUT_W, 0), (OUT_W, quad_h)], fill=(255, 68, 68), width=3)
        draw.line([(0, OUT_H), (quad_w, OUT_H)], fill=(255, 68, 68), width=3)

        quad_frames.append(canvas)

    quad_path = os.path.join(OUT_DIR, "all_heroes_attack_quad.gif")
    quad_frames[0].save(
        quad_path,
        save_all=True,
        append_images=quad_frames[1:],
        duration=FRAME_MS,
        loop=0,
        optimize=True,
    )
    print(f"Bake Quad Attack Arena GIF -> {quad_path}")


def main():
    print("=== Generating True Attack Animations with Detached Weapons ===")
    all_frames = {}

    for unit_id in ["unit_bat", "unit_wizard", "unit_skeleton", "unit_knight"]:
        print(f"Rendering attack GIF for {CONFIGS[unit_id]['name']}...")
        frames = render_attack_frames(unit_id)
        all_frames[unit_id] = frames

        out_gif = os.path.join(OUT_DIR, f"{unit_id}_attack.gif")
        frames[0].save(
            out_gif,
            save_all=True,
            append_images=frames[1:],
            duration=FRAME_MS,
            loop=0,
            optimize=True,
        )
        print(f" -> {out_gif}")

    build_quad_gif(all_frames)
    print("=== All 4 Heroes Flying Attack Animations Successfully Updated ===")


if __name__ == "__main__":
    main()
