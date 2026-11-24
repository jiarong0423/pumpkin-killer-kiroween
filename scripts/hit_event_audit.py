#!/usr/bin/env python3
"""Hit-event audit on real engine matches (owner 2026-11-17: 'the trajectory did not touch but the opponent still lost hp; run many simulations with the mask range, binary only, no rendering').
Plays engine matches (scripts/engine_matrix.py, both sides computer) and wraps GameState.projectile_hits: every time the game COUNTS a normal shot as a hit, the shot's drawn disk is tested against the
binary mask of the target figure (shared/hit_masks.json). A counted hit whose disk touches no visible pixel is a FALSE HIT; its distance to the nearest visible pixel (px) is recorded.
Nothing in the game is changed. Usage: python3 -B scripts/hit_event_audit.py [--plays 30] [--out FILE.json]. Exit 1 when a match raised an error."""
import argparse, json, math, os, runpy, sys
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mcp_game_server as srv
from hit_mask_py import HitMasks

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--plays", type=int, default=30); ap.add_argument("--out"); a = ap.parse_args()
    M = HitMasks(); dist = {}
    for hero, rows in M.runs.items():
        f = np.zeros((M.h, M.w), np.uint8)
        for y, rs in enumerate(rows):
            for p, q in rs: f[y, p:q + 1] = 1
        dist[hero] = cv2.distanceTransform((1 - f).astype(np.uint8), cv2.DIST_L2, 5)
    events = []; real = srv.GameState.projectile_hits
    def spy(attacker, target, x, y):
        ok = real(attacker, target, x, y)
        if ok and attacker["weapon"] != "proj_soundwave" and target.get("hero") in dist:
            r = srv.GameState.projectile_radius(attacker["weapon"]); face_right = target["facing"] > 0
            if M.faces[target["hero"]] == "right": face_right = not face_right
            dx = x - target["x"]; dy = y - target["y"]
            if face_right: dx = -dx
            cx, cy = int(math.floor(dx - M.x0)), int(math.floor(dy - M.y0))
            d = float(dist[target["hero"]][cy, cx]) if 0 <= cx < M.w and 0 <= cy < M.h else 999.0
            events.append((target["hero"], r, d, M.touches(target["hero"], x - target["x"], y - target["y"], r, target["facing"] > 0)))
        return ok
    srv.GameState.projectile_hits = staticmethod(spy)
    out = os.path.join(os.environ.get("TMPDIR", "/tmp"), "hit_event_audit_matrix.json")
    sys.argv = ["engine_matrix.py", "--out", out, "--plays", str(a.plays), "--quiet"]
    try: runpy.run_path(os.path.join(HERE, "engine_matrix.py"), run_name="__main__")
    except SystemExit as e:
        if e.code not in (0, None): print("ERROR engine_matrix exit %s" % e.code, file=sys.stderr); sys.exit(1)
    n = len(events); fh = [e for e in events if not e[3]]
    ds = sorted(e[2] - e[1] for e in fh)   # how far the shot's EDGE was from the figure
    res = {"counted_hits": n, "false_hits": len(fh), "false_hit_pct": round(100.0 * len(fh) / max(n, 1), 1),
           "edge_gap_px": {"median": round(ds[len(ds) // 2], 1) if ds else 0, "p90": round(ds[int(len(ds) * 0.9)], 1) if ds else 0, "max": round(ds[-1], 1) if ds else 0},
           "by_hero": {h: {"hits": sum(1 for e in events if e[0] == h), "false": sum(1 for e in fh if e[0] == h)} for h in M.runs}}
    print(json.dumps(res, indent=1))
    if a.out: json.dump(res, open(a.out, "w"), indent=1)

if __name__ == "__main__":
    main()
