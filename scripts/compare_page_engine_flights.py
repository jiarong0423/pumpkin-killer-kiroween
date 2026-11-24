#!/usr/bin/env python3
"""Front end / back end matching, data only: the SAME shots (hero, angle, power, formation) are flown through the real page physics (scripts/page_flight_outcomes.js, vm) and through the Python engine
(mcp_game_server.TrackedGameState); the outcomes are compared: which unit was hit (or none), and where the shot ended (hit point or landing) within 1 px.
usage: python3 -B scripts/compare_page_engine_flights.py [--examples 8]   exit 1 on any mismatch. No wind, no fence, no ultimate, plain weapon, near-miss compensation irrelevant (hit identity only)."""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mcp_game_server as engine
import mcp_stdio_server as srv
EX = int(sys.argv[sys.argv.index("--examples") + 1]) if "--examples" in sys.argv else 8
HEROES = ["skeleton", "bat", "knight", "hag", "hunchback", "reaper", "wizard"]
SETS = [["skeleton", "wizard", "knight"], ["bat", "hag", "reaper"]]
FORM = [(1240, 125), (1240, 200), (1450, 125), (1450, 200)]
DEAD = "--dead-front" in sys.argv   # the first enemy unit is dead
WALL = "--wall" in sys.argv   # the central fence on (wall hp 100): the outcome "fence" is compared too
shots = []
for hero in HEROES:
    for x0, sp in FORM:
        for si, prof in enumerate(SETS):
            for ang in range(5, 90, 10):
                for pw in list(range(10, 101, 10)) + [105, 110, 115]:   # 105..115: MAX_POWER is 115 since 2026-11-19
                    xs = [x0, x0 + sp, x0 + 2 * sp]; over = xs[2] - 1810
                    if over > 0: xs = [x - over for x in xs]
                    shots.append({"hero": hero, "angle": ang, "power": pw, "shooter_x": 300, "xs": xs, "prof": prof, "wall": WALL, "dead_front": DEAD})
page = json.loads(subprocess.run(["node", os.path.join(HERE, "page_flight_outcomes.js")], input=json.dumps(shots), capture_output=True, text=True, timeout=600, check=True).stdout)
bad = []; n_hit = 0
for s, pg in zip(shots, page):
    g = srv.TrackedGameState(mode="agent_vs_agent", seed=7, units=3, hero_red=[s["hero"]] * 3, hero_white=s["prof"])
    g.wind = 0; g.central_wall_hp = 100 if WALL else 0
    for i in range(3):
        g.units["red_%d" % (i + 1)]["x"] = float(s["shooter_x"] + 150 * i); g.units["white_%d" % (i + 1)]["x"] = float(s["xs"][i])
    for u in g.units.values(): u["hp"] = u["max_hp"] = 500.0
    if DEAD: g.units["white_1"].update({"alive": False, "hp": 0.0})
    assert g.submit_throw("red_1", s["angle"], s["power"])["success"]
    rec = g.resolve_round()["results"][0]
    eng_hit = int(rec["hit_target"].split("_")[1]) - 1 if str(rec.get("hit_target", "")).startswith("white_") and rec["hit_type"] == "hero" else (-3 if rec["hit_type"] == "central_wall" else -1)
    n_hit += pg["hit"] >= 0
    dx = abs(rec["landing_x"] - pg["x"]) if rec.get("landing_x") is not None else 999
    bounce = s["hero"] in ("knight", "hunchback")   # the thrown shield bounces and the boomerang axe comes back on the page: its final resting point is not the hit point, so only WHO was hit is compared for them
    if eng_hit != pg["hit"] or (dx > 1.0 and not bounce):
        bad.append("%s ang %d pw %d xs %s %s: page hit %d end %.1f | engine hit %d end %.1f (%s)" % (s["hero"], s["angle"], s["power"], s["xs"], s["prof"], pg["hit"], pg["x"], eng_hit, rec.get("landing_x", -1), rec["hit_type"]))
print("shots %d | page hits %d | mismatches %d" % (len(shots), n_hit, len(bad)))
for b in bad[:EX]: print("  " + b)
sys.exit(1 if bad else 0)
