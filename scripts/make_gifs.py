#!/usr/bin/env python3
"""Generate animated GIFs for each character in Pumpkin Killer.

Extracts animation frames from assets/sprites/*.png and creates:
1. Individual Action GIFs (idle, attack, defend, hit, die, move)
2. Character Full Showcase GIFs (idle -> move -> charge -> throw -> hit -> defend)
3. 4-Hero Quad Arena GIF (2x2 animated grid of all four classes together)
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

SPRITES_DIR = os.environ.get("PK_SPRITES_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "sprites"))
OUT_DIR = os.environ.get("PK_GIF_OUTPUT_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "gifs"))
CELL = 256
FPS = 12
FRAME_MS = int(1000 / FPS)  # ~83ms

UNITS = {
    "unit_bat": {
        "name": "蝙蝠貓刺客 (Bat Scout)",
        "role": "高機動繞後 / 搶箱伏擊",
        "hp": 90,
        "color": (162, 155, 254)
    },
    "unit_wizard": {
        "name": "南瓜巫師炮手 (Witch Gunner)",
        "role": "大仰角高拋 / 破掩體壓制",
        "hp": 85,
        "color": (255, 159, 67)
    },
    "unit_skeleton": {
        "name": "骷髏長矛兵 (Skeleton Ricochet)",
        "role": "符文板反射 / 穿襠直線狙擊",
        "hp": 100,
        "color": (0, 210, 211)
    },
    "unit_knight": {
        "name": "南瓜重裝盾衛 (Pumpkin Guard)",
        "role": "三檔浮空阻擋 / 正面肉盾",
        "hp": 120,
        "color": (77, 238, 234)
    }
}

os.makedirs(OUT_DIR, exist_ok=True)


def slice_sheet(path, cell=CELL):
    if not os.path.exists(path):
        return []
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    n = w // cell
    return [im.crop((i * cell, 0, (i + 1) * cell, h)) for i in range(n)]


def save_gif(frames, out_path, duration=FRAME_MS, bg_color=(20, 11, 36)):
    """Save frames as animated GIF composited against dark theme background."""
    if not frames:
        return
    bg_frames = []
    for f in frames:
        bg = Image.new("RGB", f.size, bg_color)
        bg.paste(f, (0, 0), f)
        bg_frames.append(bg)

    bg_frames[0].save(
        out_path,
        save_all=True,
        append_images=bg_frames[1:],
        duration=duration,
        loop=0
    )


def save_transparent_gif(frames, out_path, duration=FRAME_MS):
    """Save frames as transparent GIF."""
    if not frames:
        return
    p_frames = []
    for f in frames:
        alpha = f.split()[-1]
        p = f.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=254)
        mask = Image.eval(alpha, lambda a: 255 if a < 128 else 0)
        p.paste(255, mask)
        p.info["transparency"] = 255
        p_frames.append(p)

    p_frames[0].save(
        out_path,
        save_all=True,
        append_images=p_frames[1:],
        duration=duration,
        loop=0,
        transparency=255,
        disposal=2
    )


def build_single_unit_gifs(unit_id, team="red"):
    meta = UNITS[unit_id]
    print(f"--> Building GIFs for {meta['name']} (team: {team})...")

    # 1. Idle Loop
    idle_sheet = os.path.join(SPRITES_DIR, f"{unit_id}_{team}_idle.png")
    idle_frames = slice_sheet(idle_sheet)
    if idle_frames:
        save_gif(idle_frames, os.path.join(OUT_DIR, f"{unit_id}_idle.gif"))
        save_transparent_gif(idle_frames, os.path.join(OUT_DIR, f"{unit_id}_idle_trans.gif"))

    # 2. Raw Attack Combo (charge + throw without external projectiles)
    charge_frames = slice_sheet(os.path.join(SPRITES_DIR, f"{unit_id}_{team}_arm_charge.png"))
    throw_frames = slice_sheet(os.path.join(SPRITES_DIR, f"{unit_id}_{team}_arm_throw.png"))
    attack_frames = charge_frames + throw_frames
    if attack_frames:
        save_gif(attack_frames, os.path.join(OUT_DIR, f"{unit_id}_attack_raw.gif"))

    # 3. Defend Loop
    defend_frames = slice_sheet(os.path.join(SPRITES_DIR, f"{unit_id}_{team}_defend.png"))
    if defend_frames:
        save_gif(defend_frames, os.path.join(OUT_DIR, f"{unit_id}_defend.gif"))

    # 4. Move Forward Loop
    move_frames = slice_sheet(os.path.join(SPRITES_DIR, f"{unit_id}_{team}_move_forward.png"))
    if move_frames:
        save_gif(move_frames, os.path.join(OUT_DIR, f"{unit_id}_move.gif"))

    # 5. Full Moveset Showcase (Idle -> Move -> Charge -> Throw -> Hit -> Defend)
    hit_frames = slice_sheet(os.path.join(SPRITES_DIR, f"{unit_id}_{team}_hit_react.png"))
    full_showcase = idle_frames + move_frames + charge_frames + throw_frames + hit_frames + defend_frames
    if full_showcase:
        save_gif(full_showcase, os.path.join(OUT_DIR, f"{unit_id}_showcase.gif"))
        print(f"    Saved {unit_id}_showcase.gif ({len(full_showcase)} frames)")


def build_quad_arena_gif(team="red"):
    print("--> Generating 4-Hero Quad Arena GIF (2x2 animated arena)...")
    
    # Load idle loops for all 4
    bat_f = slice_sheet(os.path.join(SPRITES_DIR, f"unit_bat_{team}_idle.png"))
    wiz_f = slice_sheet(os.path.join(SPRITES_DIR, f"unit_wizard_{team}_idle.png"))
    skel_f = slice_sheet(os.path.join(SPRITES_DIR, f"unit_skeleton_{team}_idle.png"))
    kni_f = slice_sheet(os.path.join(SPRITES_DIR, f"unit_knight_{team}_idle.png"))

    num_frames = min(len(bat_f), len(wiz_f), len(skel_f), len(kni_f))
    if num_frames == 0:
        return

    canvas_w = CELL * 2 + 60
    canvas_h = CELL * 2 + 100
    bg_color = (16, 10, 28)

    quad_frames = []
    for i in range(num_frames):
        img = Image.new("RGB", (canvas_w, canvas_h), bg_color)
        draw = ImageDraw.Draw(img)

        # Header Title
        draw.text((canvas_w // 2, 20), "🎃 PUMPKIN KILLER — FOUR HEROES 🎃", fill=(255, 177, 66), anchor="mm")

        # Top-Left: Bat Scout
        b_x, b_y = 20, 45
        draw.rectangle([b_x, b_y, b_x + CELL, b_y + CELL], outline=(50, 30, 80), width=2)
        img.paste(bat_f[i], (b_x, b_y), bat_f[i])
        draw.text((b_x + CELL // 2, b_y + CELL - 15), "🦇 蝙蝠貓刺客 (HP 90)", fill=(162, 155, 254), anchor="mm")

        # Top-Right: Witch Gunner
        w_x, w_y = CELL + 40, 45
        draw.rectangle([w_x, w_y, w_x + CELL, w_y + CELL], outline=(50, 30, 80), width=2)
        img.paste(wiz_f[i], (w_x, w_y), wiz_f[i])
        draw.text((w_x + CELL // 2, w_y + CELL - 15), "🧙 南瓜巫師炮手 (HP 85)", fill=(255, 159, 67), anchor="mm")

        # Bottom-Left: Skeleton Ricochet
        s_x, s_y = 20, CELL + 65
        draw.rectangle([s_x, s_y, s_x + CELL, s_y + CELL], outline=(50, 30, 80), width=2)
        img.paste(skel_f[i], (s_x, s_y), skel_f[i])
        draw.text((s_x + CELL // 2, s_y + CELL - 15), "💀 骷髏長矛兵 (HP 100)", fill=(0, 210, 211), anchor="mm")

        # Bottom-Right: Pumpkin Guard
        k_x, k_y = CELL + 40, CELL + 65
        draw.rectangle([k_x, k_y, k_x + CELL, k_y + CELL], outline=(50, 30, 80), width=2)
        img.paste(kni_f[i], (k_x, k_y), kni_f[i])
        draw.text((k_x + CELL // 2, k_y + CELL - 15), "🛡️ 南瓜重裝盾衛 (HP 120)", fill=(77, 238, 234), anchor="mm")

        quad_frames.append(img)

    quad_out = os.path.join(OUT_DIR, "all_heroes_idle_quad.gif")
    quad_frames[0].save(
        quad_out,
        save_all=True,
        append_images=quad_frames[1:],
        duration=FRAME_MS,
        loop=0
    )
    print(f"    Saved {quad_out} ({len(quad_frames)} frames)")


def main():
    print("=== Starting Pumpkin Killer GIF Generation ===")
    for unit_id in UNITS:
        build_single_unit_gifs(unit_id, team="red")
    build_quad_arena_gif(team="red")
    print("=== All GIFs generated successfully in docs/gifs/! ===")


if __name__ == "__main__":
    main()
