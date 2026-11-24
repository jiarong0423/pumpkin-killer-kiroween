#!/usr/bin/env python3 -B
"""Coverage table: how far each hit box and area effect reaches, in world px and on a phone, and which teammates it covers at the team start slots.

All numbers come from index.html and shared/*.json (read, not guessed): hit box half-width 70 (reaper 57) and height 190; projectile radius sqrt(len*thick)/2 - 20;
wave: 105 px either side of the landing point, 40 px above the ground, damage 100 percent to 35 px, 75 percent to 70 px, 50 percent to 105 px (cells of 35 px since 2026-11-18, js/sound_wave.js);
wizard blast: 234 px; bat swarm: every living enemy unit; start slots (js/team_battle.js): left 252..612, right 1296..1656, N = 2 -> 360 px apart, N = 3 -> 180 px apart.
Screen mapping: screen_x = stage_x + (world_x + PAD) * k, k = canvas_css_width / VIEW_W = s (stage height / 1080); on a phone only s matters for sizes.
Writes docs/COVERAGE_TABLE_20261117.md and logs_local/coverage_table.log; exit 1 on a failed self-check.
"""
import os, sys, math, logging
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "COVERAGE_TABLE_20261117.md")
os.makedirs(os.path.join(ROOT, "logs_local"), exist_ok=True)
logging.basicConfig(filename=os.path.join(ROOT, "logs_local", "coverage_table.log"), level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
HALF, HEIGHT, REAPER_HALF, REAPER_H = 70, 190, 57, 165
PROJ = {"spear": (210, 33), "cannonball": (40, 40), "shuriken": (58, 58), "flame": (150, 55), "cross": (118, 82), "axe": (130, 130), "shield": (62, 92)}
WAVE_HALF, WAVE_H, BLAST = 105, 40, 234
S_PHONES = {"owner phone fullscreen (800x360)": 308 / 1080, "owner phone with address bar (760x266)": 214 / 1080, "iPhone 17 Pro Max fullscreen": 388 / 1080}
SLOTS = {2: [252, 612], 3: [252, 432, 612]}

def wave_pct(dx):
    return 100 if dx <= 35 else 75 if dx <= 70 else 50 if dx <= 105 else 0   # cells of 35 px (owner 2026-11-18); twin of js/sound_wave.js

def radius(w):
    l, t = PROJ[w]
    return max(0.0, math.sqrt(l * t) / 2 - 20)

def main():
    md = ["# Coverage table (2026-11-17)", "", "Formulas and sources: header of `scripts/coverage_table.py`. World px; phone px = world px x s.", ""]
    s_main = S_PHONES["owner phone fullscreen (800x360)"]
    md += ["## 1. Single-target reach (a shot at one unit)", "", "| Weapon | Projectile | Radius added | Reach left/right of the unit centre | Reach above the feet | Phone px (s=%.3f) |" % s_main, "|---|---|---|---|---|---|"]
    for w, (l, t) in PROJ.items():
        r = radius(w)
        md.append("| %s | %dx%d | %.1f | %.1f | %.1f | %.1f wide, %.1f high |" % (w, l, t, r, HALF + r, HEIGHT + r, 2 * (HALF + r) * s_main, (HEIGHT + r) * s_main))
    md += ["| reaper as target | - | - | %d | %d | %.1f wide, %.1f high |" % (REAPER_HALF, REAPER_H, 2 * REAPER_HALF * s_main, REAPER_H * s_main), ""]
    md += ["## 2. Area effects", "", "| Effect | Reach | World px | Phone px (s=%.3f) |" % s_main, "|---|---|---|---|",
           "| Bride wave | left/right of the landing point, 40 px above the ground | %d, steps 35/70/105 = 100/75/50 percent | %.1f (%.1f / %.1f / %.1f) |" % (WAVE_HALF, WAVE_HALF * s_main, 40 * s_main, 75 * s_main, 105 * s_main),
           "| Wizard blast | radius around the landing point | %d | %.1f |" % (BLAST, BLAST * s_main),
           "| Bat swarm | every living enemy unit after ANY hit of the armed ultimate wave (since 2026-11-18; it was a precise hit inside 55 px) | whole team | - |", ""]
    md += ["## 3. What an area effect covers at the team start slots", "", "Centre on each unit in turn (a shot that lands exactly on it); 'covered' = the other units of the same team inside the reach.", "", "| Team size | Slots | Spacing | Wave: neighbours covered (damage percent) | Blast: neighbours covered |", "|---|---|---|---|---|"]
    for n, xs in SLOTS.items():
        sp = xs[1] - xs[0]
        wave_rows, blast_rows = [], []
        for i, cx in enumerate(xs):
            cw = ["unit%d %d%%" % (j, wave_pct(abs(cx - x))) for j, x in enumerate(xs) if j != i and abs(cx - x) <= WAVE_HALF]
            cb = ["unit%d" % j for j, x in enumerate(xs) if j != i and abs(cx - x) <= BLAST]
            wave_rows.append("centre unit%d: %s" % (i, ", ".join(cw) or "none"))
            blast_rows.append("centre unit%d: %s" % (i, ", ".join(cb) or "none"))
        md.append("| %d | %s | %d | %s | %s |" % (n, "/".join(map(str, xs)), sp, "; ".join(wave_rows), "; ".join(blast_rows)))
    md += ["", "## 4. Spacing needed", "", "- The wave covers a neighbour when spacing <= 105 px; 100 percent at <= 35, 75 at <= 70. The minimum unit spacing is 90 px, so the wave can reach a neighbour only at the tightest spacing (and then at 50 percent).", "- The blast (234 px) covers a neighbour at any spacing <= 234 px: at 3 v 3 (180 px) it covers the adjacent unit, and the far one only when centred on the middle unit (180 px each side); at 2 v 2 (360 px) it never covers the teammate.", "- The designer's proposal (spacing 130 px for 3 v 3, 160 px for 2 v 2) would put neighbours inside the blast and outside the wave.", ""]
    md += ["## 5. Phone size of the same reaches", "", "| Phone case | s | Wave half-width | Blast radius | Hit box (140 x 190) |", "|---|---|---|---|---|"]
    for name, s in S_PHONES.items():
        md.append("| %s | %.3f | %.1f | %.1f | %.1f x %.1f |" % (name, s, WAVE_HALF * s, BLAST * s, 2 * HALF * s, HEIGHT * s))
    # self checks against known values
    assert wave_pct(30) == 100 and wave_pct(50) == 75 and wave_pct(100) == 50 and wave_pct(106) == 0
    assert abs(radius("spear") - 21.6) < 0.2 and radius("cannonball") == 0
    open(OUT, "w", encoding="utf-8").write("\n".join(md) + "\n")
    logging.info("wrote %s", OUT)
    print("OK wrote", OUT)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        logging.error("ERROR self-check failed: %s", e); print("ERROR self-check failed", e); sys.exit(1)
