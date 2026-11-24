#!/usr/bin/env python3
"""Best dock size by binary masks (owner 2026-11-17: 'compute it yourself with the binary mask, I want the best display proportion within the range').
For each stage height h (css px) the scene is rasterised at 1 css px: figure silhouettes at the 3v3 slots (real art alpha, 220 px high, bottom at ground + 15), the turn ring and the two shadow ellipses
under each foot, and the dock bar (52 px high in its design space, 6 px above the stage bottom, plus a 5 px strip for the ammo count badges that stick out above it) scaled by s.
Largest s whose dock mask stays at least GAP css px away (vertically, in the same columns) from every non-dock pixel is the best s for that height. The reference R = h / s tells which single
constant makes s = h / R safe at EVERY height: use the largest R of the column (a smaller R would make the bar too big on a short stage). Read-only. Usage: python3 -B scripts/dock_fit_mask.py [--gap 4]"""
import argparse, os, sys
import cv2, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = {"skeleton": "assets/units/unit_skeleton.png", "wizard": "assets/units/unit_wizard.png", "bat": "assets/units/unit_bat.png", "bride": "assets/poses/bride_idle1.png", "hag": "assets/units/unit_hag_idle.png", "reaper": "assets/poses/necro_idle.png"}
SLOTS = [("skeleton", 252), ("wizard", 432), ("bat", 612), ("bride", 1296), ("wizard", 1476), ("hag", 1656)]
GROUND_Y, BORDER, BADGE = 860, 3, 5

def lowest_rows(h):
    """Per css column: the lowest non-dock pixel row (stage coordinates), -1 where nothing is drawn. World 1080 px high maps to h - 6 css px."""
    k = (h - 2 * BORDER) / 1080.0; width = int(round(h * 2.0)); low = np.full(width, -1.0)
    cx = lambda xw: int(round(xw * k)) + (width - int(round(1920 * k))) // 2      # the 1920 core centred in a 2.0 stage
    for hero, xw in SLOTS:
        im = cv2.imread(os.path.join(ROOT, ART[hero]), cv2.IMREAD_UNCHANGED); s = 220.0 / im.shape[0]
        sp = cv2.resize(im, (int(round(im.shape[1] * s * k)), max(1, int(round(220 * k)))), interpolation=cv2.INTER_AREA)
        ys, xs = np.nonzero(sp[:, :, 3] > 40); top = BORDER + (GROUND_Y + 15) * k - sp.shape[0]
        for x in np.unique(xs):
            col = cx(xw) - sp.shape[1] // 2 + x
            if 0 <= col < width: low[col] = max(low[col], top + ys[xs == x].max() + 1)
        for dy, rx, ry in ((-8, 54, 16), (12, 72.6, 14.3)):     # shadow ellipses (world px offsets from the foot line)
            yc = BORDER + (GROUND_Y + dy) * k
            for col in range(int(cx(xw) - rx * k), int(cx(xw) + rx * k) + 1):
                if 0 <= col < width:
                    t = (col - cx(xw)) / (rx * k); low[col] = max(low[col], yc + ry * k * np.sqrt(max(0.0, 1 - t * t)))
    return low, width

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--gap", type=float, default=4.0); a = ap.parse_args()
    print("stage h | best s | bar high | button | dock top | lowest figure/shadow pixel | R = h / s")
    Rs = []
    for h in (300, 330, 360, 390, 430, 480, 540, 800):
        low, width = lowest_rows(h); best = 0.0
        for s in np.arange(0.5, 3.0, 0.005):
            bottom = BORDER + (h - 2 * BORDER) - 6 * s; top = bottom - (52 + BADGE) * s
            x0, x1 = int(width * 0.06), int(width * 0.94)     # the dock spans 84 percent of the stage width
            if top - a.gap >= low[x0:x1].max(): best = s
        lw = low[int(width * 0.06):int(width * 0.94)].max(); bottom = BORDER + (h - 2 * BORDER) - 6 * best
        print("%7d | %6.3f | %8.1f | %6.1f | %8.1f | %26.1f | %9.1f" % (h, best, 52 * best, 44 * best, bottom - 52 * best, lw, h / best)); Rs.append(h / best)
    print("single reference that fits EVERY height: R = %.1f (s = h / R must not exceed the best s, so R is the largest of the column); rounded up to 390. The old 430 gave bars 9 percent smaller." % max(Rs))

if __name__ == "__main__":
    main()
