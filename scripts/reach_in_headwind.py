#!/usr/bin/env python3
"""How far can each role shoot against the wind, and can it touch a target standing in the far corner? Red-team H1 R2-B1 / R3-A1: the numbers behind the owner question H15 (the rule 'every target must stay hittable' of 2026-11-16
against the retreat limits 110 / 1810 of 2026-11-17).
Reference flight (scripts/sim_team_headless.py flight, the Python twin of the page) with each role's REAL launch offsets from the engine, a shooter at x = 110 on the ground line, wind -3 / -4 / -5 (legal seeded wind is -4..+4, a storm adds 1.5 to its
magnitude), angle 20..50 step 0.5, power 90..115 step 0.5, the fence standing. Column 1: the farthest ground landing. Column 2: for each of the 8 target roles standing at the corner x (default 1810), does ANY of those shots touch the target by the
ENGINE's own hit rule (GameState.projectile_hits: half box + projectile radius + the binary mask; the bride's wave band), tested along the path every 3 px; printed as the number of target roles out of 8 that can be touched.
usage: python3 -B scripts/reach_in_headwind.py [--x 110] [--corner 1810]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mcp_stdio_server as srv, mcp_game_server as eng, sim_team_headless as S
A = sys.argv; X = float(A[A.index("--x") + 1]) if "--x" in A else 110.0; CORNER = float(A[A.index("--corner") + 1]) if "--corner" in A else 1810.0
HEROES = ["skeleton", "wizard", "bat", "knight", "reaper", "bride", "hunchback", "hag"]
print("shooter at x %.0f, corner target at x %.0f (distance %.0f); fence standing; engine hit rule" % (X, CORNER, CORNER - X))
for hero in HEROES:
    g = srv.TrackedGameState(mode="agent_vs_agent", seed=7, units=3, hero_red=[hero] * 3, hero_white=["skeleton", "wizard", "knight"])
    u = g.units["red_1"]; wave = u["weapon"] == "proj_soundwave"; targets = {}
    for t in HEROES:
        gt = srv.TrackedGameState(mode="agent_vs_agent", seed=7, units=3, hero_red=[hero] * 3, hero_white=[t] * 3)
        tu = gt.units["white_1"]; tu["x"] = CORNER; targets[t] = (gt, tu)
    row = []; hit_counts = []
    for w in (-3, -4, -5):
        best = 0.0; touched = set()
        for a2 in range(40, 101):
            for p2 in range(180, 231):
                pts, end = S.flight(X, float(u["y"]), 1, u["launch"], a2 / 2.0, p2 / 2.0, float(w), 100, sweep=True, wave=wave)
                if end != "ground": continue
                best = max(best, pts[-1][0])
                if pts[-1][0] < CORNER - 200: continue   # cannot touch a target 200 px or more beyond its landing (box 70 + radius <= 45 + wave band 105)
                for t, (gt, tu) in targets.items():
                    if t in touched: continue
                    if any(eng.GameState.projectile_hits(gt.units["red_1"], tu, x, y) for x, y in pts[-60:]): touched.add(t)
        row.append(best); hit_counts.append(len(touched))
    print("%-9s launch fwd %2d up %3d | farthest landing at wind -3 / -4 / -5: %4.0f / %4.0f / %4.0f | target roles touchable in the corner (of 8): %d / %d / %d" % (hero, u["launch"]["fwd"], u["launch"]["up"], *row, *hit_counts))
