#!/usr/bin/env python3
"""Full-coverage audit of the hit rule: physics x binary masks, no rendering (owner 2026-11-17: 'print the false-zone and offset coverage so we know how to solve it').
Grid: every shooter hero (its weapon radius and launch point) x angle 20..80 step 5 x power 30..100 step 5 x wind -5..5 step 1 = 17,160 shots from x = 300, flown with the PAGE's flight step
(semi-implicit Euler at 1/60 s, wind = acceleration 56 tail / 84 head, gravity 980, fence and shields ignored) against every target hero standing at x = 1240..1810 (step 114).
For each shot and target: A = first step the DECIDED BOX counts a hit (the game's rule today), B = first step the box AND the binary mask count (the shot's drawn disk touches a visible pixel).
Reported: how often A fires while the disk does not touch (false hit), how far the disk is from the figure then (gap), where the hit fires (entry offset from the figure's centre), how many box hits the
mask rule would turn into pass-through or later hits, per target hero, per shot radius, per wind direction and per distance. Writes docs/HIT_COVERAGE_20261117.md. Read-only on the game. Exit 1 on a missing file."""
import json, math, os, sys
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import mcp_game_server as eng
from hit_mask_py import HitMasks

def main():
    M = HitMasks(); heroes = json.load(open(os.path.join(ROOT, "shared", "heroes.json")))
    dist = {}
    for hero, rows in M.runs.items():
        f = np.zeros((M.h, M.w), np.uint8)
        for y, rs in enumerate(rows):
            for p, q in rs: f[y, p:q + 1] = 1
        dist[hero] = cv2.distanceTransform((1 - f).astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32)
    angles = np.arange(20, 81, 5); powers = np.arange(30, 101, 5); winds = np.arange(-5, 6)
    targets_x = np.arange(1240, 1811, 114)
    # trajectories (semi-implicit Euler, the page's order), all shooters
    shots = []   # (hero, radius, X[steps], Y[steps], wind, angle, power)
    T = 300; dt = 1 / 60.0
    for hero, h in heroes.items():
        r = eng.GameState.projectile_radius(h["weapon"]); fwd, up = h["launch"]["fwd"], h["launch"]["up"]
        A, P, W = np.meshgrid(angles, powers, winds, indexing="ij"); A, P, W = A.ravel(), P.ravel(), W.ravel().astype(np.float64)
        rad = np.radians(A); v0 = P * eng.V0_PER_POWER; vx = v0 * np.cos(rad); vy = -v0 * np.sin(rad)
        x = np.full(A.shape, 300.0 + fwd); y = np.full(A.shape, 860.0 - up)
        accel = W * np.where(W > 0, eng._WIND_TAIL, eng._WIND_HEAD)      # facing right: positive wind is a tailwind
        X = np.empty((A.size, T), np.float32); Y = np.empty((A.size, T), np.float32)
        for t in range(T):
            vx = vx + accel * dt; vy = vy + eng.GRAVITY * dt; x = x + vx * dt; y = y + vy * dt
            X[:, t] = x; Y[:, t] = y
        # stop at the ground: after the first step with y >= 860 and falling, push the rest far away
        grounded = (Y >= 860.0); first_ground = np.where(grounded.any(axis=1), grounded.argmax(axis=1), T)
        idx = np.arange(T)[None, :] >= first_ground[:, None]; X[idx] = -9999.0; Y[idx] = -9999.0
        shots.append((hero, r, X, Y, W))
    agg = {}
    def add(key, **kw):
        d = agg.setdefault(key, {"shots": 0, "box_hit": 0, "false_hit": 0, "mask_hit": 0, "lost": 0, "later": 0, "gaps": [], "entry": []})
        for k, v in kw.items():
            if isinstance(v, list): d[k].extend(v)
            else: d[k] += v
    for shooter, r, X, Y, W in shots:
        for target, dm in dist.items():
            hw, hh = (57, 165) if target == "reaper" else (70, 190)
            for tx in targets_x:
                dx = X - tx; dy = Y - 860.0
                box = (np.abs(dx) <= hw + r) & (dy >= -hh - r) & (dy <= r)
                anyb = box.any(axis=1); a = box.argmax(axis=1)
                ix = np.clip((dx - M.x0).astype(np.int32), 0, M.w - 1); iy = np.clip((dy - M.y0).astype(np.int32), 0, M.h - 1)
                inwin = (dx >= M.x0) & (dx < M.x0 + M.w) & (dy >= M.y0) & (dy < M.y0 + M.h)
                d = np.where(inwin, dm[iy, ix], 999.0)
                touch = d <= (r + 0.5)
                both = box & touch; anym = both.any(axis=1); b = both.argmax(axis=1)
                rows = np.nonzero(anyb)[0]
                false = rows[~touch[rows, a[rows]]]
                gap = (d[false, a[false]] - r).tolist()
                entry = np.abs(dx[rows, a[rows]]).tolist()
                lost = int((anyb & ~anym).sum()); later = int((anyb & anym & (b > a)).sum())
                wk = "head" if False else None
                for key in (("target", target), ("radius", round(r)), ("tx", int(tx)), ("shooter", shooter)):
                    add(key, shots=int(X.shape[0]), box_hit=int(anyb.sum()), false_hit=int(len(false)), mask_hit=int(anym.sum()), lost=lost, later=later, gaps=gap, entry=entry)
                # wind split: shooter faces right, positive wind = tailwind
                tail = W > 0
                for name, sel in (("tailwind", tail), ("headwind", W < 0), ("no wind", W == 0)):
                    s = sel & anyb; f2 = sel & anyb & ~touch[np.arange(X.shape[0]), a]
                    add(("wind", name), shots=int(sel.sum()), box_hit=int(s.sum()), false_hit=int(f2.sum()), mask_hit=int((sel & anym).sum()), lost=int((sel & anyb & ~anym).sum()), later=int((sel & anyb & anym & (b > a)).sum()))
    def line(label, d):
        g = np.array(d["gaps"]) if d["gaps"] else np.array([0.0]); e = np.array(d["entry"]) if d["entry"] else np.array([0.0])
        return "| %s | %d | %d | %.1f%% | %.1f | %.1f | %.0f | %.1f%% | %.1f%% |" % (label, d["shots"], d["box_hit"], 100.0 * d["false_hit"] / max(d["box_hit"], 1), float(np.median(g)), float(np.percentile(g, 90)), float(np.mean(e)),
                                                                                  100.0 * d["lost"] / max(d["box_hit"], 1), 100.0 * d["later"] / max(d["box_hit"], 1))
    head = ["| group | shots x targets | box hits | false hit share | gap median (px) | gap p90 (px) | mean entry |dx| | box hits lost under the mask | box hits later under the mask |", "|---|---|---|---|---|---|---|---|---|"]
    out = ["# Hit coverage, physics x binary masks (2026-11-17)", "", "Generated by `scripts/hit_coverage.py` (17,160 shots per target position, 6 target positions, 8 target heroes, page flight step, no rendering).",
           "False hit = the game's box rule fires while the shot's drawn disk touches no visible pixel. Gap = distance from the disk edge to the figure at that moment. Entry |dx| = distance of the shot centre from the figure centre when the hit fires (the box edge is 70 + radius). Lost = box hits that never touch a visible pixel on the whole flight (the mask rule would let them pass). Later = box hits the mask rule would register later in the flight.", ""]
    for title, kind, keys in (("By target hero", "target", sorted(dist)), ("By shot radius (weapon size)", "radius", sorted({k[1] for k in agg if k[0] == "radius"})),
                              ("By target distance (x)", "tx", [int(v) for v in targets_x]), ("By shooter hero", "shooter", sorted(heroes))):
        out += ["## " + title, ""] + head + [line(str(k), agg[(kind, k)]) for k in keys] + [""]
    out += ["## By wind (shooter faces right)", ""] + head + [line(n, agg[("wind", n)]) for n in ("tailwind", "headwind", "no wind")] + [""]
    tot = {"shots": 0, "box_hit": 0, "false_hit": 0, "mask_hit": 0, "lost": 0, "later": 0, "gaps": [], "entry": []}
    for k in sorted(dist):
        for f in tot:
            v = agg[("target", k)][f]; tot[f] = tot[f] + v if not isinstance(v, list) else tot[f] + v
    out += ["## All", ""] + head + [line("all targets", tot)] + [""]
    open(os.path.join(ROOT, "docs", "HIT_COVERAGE_20261117.md"), "w").write("\n".join(out) + "\n"); print("\n".join(out))

if __name__ == "__main__":
    main()
