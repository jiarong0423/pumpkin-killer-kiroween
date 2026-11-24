#!/usr/bin/env python3
"""Front end / back end, data only, the unit standing at the VERY BACK of the zone (x = 1810, the rear of the formation). Owner 2026-11-18: "closest to the very back, count how many shots can hit it, same back end and front end simulation".
The same shots (7 roles x angle 5..85 step 5 x power 10..100 step 2 x 2 spacings x 2 target sets) are flown through the real page physics (scripts/page_flight_outcomes.js) and the Python engine (TrackedGameState); the rear unit is the
third one (x 1810). Prints, per role: shots, hits on the rear unit in the page and in the engine, and the number of outcome mismatches. usage: python3 -B scripts/rear_position_hit_count.py [--wall] [--out file.json]   exit 1 on any mismatch.
Left team shoots right team (the other direction is the mirror and is covered by scripts/trace_hit_paths.js, both directions)."""
import json, os, subprocess, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mcp_stdio_server as srv
WALL = "--wall" in sys.argv; OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
HEROES = ["skeleton", "wizard", "bat", "knight", "reaper", "hunchback", "hag"]; SETS = [["skeleton", "wizard", "knight"], ["bat", "hag", "reaper"]]; SP = [125, 200]
shots = []
for hero in HEROES:
    for sp in SP:
        for prof in SETS:
            for ang in range(5, 90, 5):
                for pw in range(10, 101, 2):
                    shots.append({"hero": hero, "angle": ang, "power": pw, "shooter_x": 300, "xs": [1810 - 2 * sp, 1810 - sp, 1810], "prof": prof, "wall": WALL, "dead_front": False})
page = json.loads(subprocess.run(["node", os.path.join(HERE, "page_flight_outcomes.js")], input=json.dumps(shots), capture_output=True, text=True, timeout=1500, check=True).stdout)
per = collections.defaultdict(lambda: [0, 0, 0, 0, 0]); bad = []   # shots, page rear hits, engine rear hits, any-unit hits (page), mismatches
for s, pg in zip(shots, page):
    g = srv.TrackedGameState(mode="agent_vs_agent", seed=7, units=3, hero_red=[s["hero"]] * 3, hero_white=s["prof"]); g.wind = 0; g.central_wall_hp = 100 if WALL else 0
    for i in range(3): g.units["red_%d" % (i + 1)]["x"] = float(300 + 150 * i); g.units["white_%d" % (i + 1)]["x"] = float(s["xs"][i])
    for u in g.units.values(): u["hp"] = u["max_hp"] = 500.0
    assert g.submit_throw("red_1", s["angle"], s["power"])["success"]
    rec = g.resolve_round()["results"][0]
    eng = int(rec["hit_target"].split("_")[1]) - 1 if str(rec.get("hit_target", "")).startswith("white_") and rec["hit_type"] == "hero" else (-3 if rec["hit_type"] == "central_wall" else -1)
    r = per[s["hero"]]; r[0] += 1; r[1] += pg["hit"] == 2; r[2] += eng == 2; r[3] += pg["hit"] >= 0
    if eng != pg["hit"]: r[4] += 1; bad.append("%s ang %d pw %d xs %s: page %d engine %d" % (s["hero"], s["angle"], s["power"], s["xs"], pg["hit"], eng))
print("fence %s | rear unit at x 1810" % ("up" if WALL else "down"))
tot = [0] * 5
for h in HEROES:
    r = per[h]; tot = [a + b for a, b in zip(tot, r)]; print("  %-10s shots %5d  rear hits page %4d engine %4d  (any unit, page %4d)  mismatches %d" % (h, *r))
print("  TOTAL      shots %5d  rear hits page %4d engine %4d  (any unit, page %4d)  mismatches %d" % tuple(tot))
for b in bad[:8]: print("   " + b)
if OUT: json.dump({"fence_up": WALL, "per_role": per, "total": tot}, open(OUT, "w"), indent=1)
sys.exit(1 if bad else 0)
