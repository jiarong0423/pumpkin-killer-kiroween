#!/usr/bin/env python3
"""Every role STANDS AT THE VERY BACK of its zone and shoots the unit standing at the VERY BACK of the other zone, all units on the ground line, with WIND and WEATHER in the physics
(owner 2026-11-18: "test every role standing at the rear hitting the rear, all on the bottom line, weather and wind included, see how big the deviation is"). Data only.
Left rear x = 110, right rear x = 1810 (range 1700 px), target formation spacing 130, the rear target is unit index 2. Grid: angle 5..85 step 5 x power 10..100 step 3; wind -5,-3,0,3,5 with clear and storm (storm adds 1.5 to the wind
magnitude); rain, snow, fog (no flight effect by their tables) at wind -5 and +5 as a check. The fence stands (100 hp).
Checks: (1) page versus Python engine (TrackedGameState, left shoots right): who was hit and where the shot ended, must agree; (2) the other direction on the page is the mirror (wind sign flipped); (3) the deviation: for every
(angle, power) that hits the rear target in calm air, how far does wind / storm move the landing point, and how many (angle, power) pairs hit the rear target per condition.
usage: python3 -B scripts/rear_rear_weather_wind.py [--out docs/rear_rear_weather_wind_20261119.json] [--coarse]   exit 1 on any page/engine or mirror mismatch."""
import json, os, subprocess, sys, collections, statistics
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mcp_stdio_server as srv
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
COARSE = "--coarse" in sys.argv   # a 1/10 grid for quick looks
HEROES = ["skeleton", "wizard", "bat", "knight", "reaper", "bride", "hunchback", "hag"]; PROF = ["skeleton", "wizard", "knight"]
WEATHER = {"clear": {"attackMult": 1, "moveMult": 1, "windBonus": 0}, "rain": {"attackMult": 0.9, "moveMult": 1, "windBonus": 0}, "snow": {"attackMult": 1, "moveMult": 0.5, "windBonus": 0},
           "storm": {"attackMult": 0.9, "moveMult": 1, "windBonus": 1.5}, "fog": {"attackMult": 1, "moveMult": 1, "windBonus": 0}}
COND = [("clear", w) for w in (-5, -3, 0, 3, 5)] + [("storm", w) for w in (-5, -3, 0, 3, 5)] + [(k, w) for k in ("rain", "snow", "fog") for w in (-5, 5)]
RIGHT_XS = [1810 - 260, 1810 - 130, 1810]; LEFT_XS = [110 + 260, 110 + 130, 110]
def shots_for(direction):
    out = []
    for hero in HEROES:
        for weather, wind in COND:
            for ang in range(5, 90, 20 if COARSE else 5):
                for pw in range(10, 101, 9 if COARSE else 3):
                    out.append({"dir": direction, "hero": hero, "angle": ang, "power": pw, "wind": wind if direction == "L2R" else -wind, "weather": weather,
                                "xs": RIGHT_XS if direction == "L2R" else LEFT_XS, "prof": PROF, "shooter_x": 110 if direction == "L2R" else 1810, "wall": True})
    return out
def page(shots):
    return json.loads(subprocess.run(["node", os.path.join(HERE, "rear_rear_weather_wind_page.js")], input=json.dumps(shots), capture_output=True, text=True, timeout=3000, check=True).stdout)
A = shots_for("L2R"); B = shots_for("R2L"); pa = page(A); pb = page(B)
bad = []; res = collections.defaultdict(dict); xdev = collections.defaultdict(list)   # (hero, weather, wind) -> {(ang,pw): (hit, x)}
for s, a, b in zip(A, pa, pb):
    g = srv.TrackedGameState(mode="agent_vs_agent", seed=7, units=3, hero_red=[s["hero"]] * 3, hero_white=PROF)
    g.wind = float(s["wind"]); g.weather = dict(WEATHER[s["weather"]]); g.central_wall_hp = 100
    for i in range(3): g.units["red_%d" % (i + 1)]["x"] = float(110 + 130 * i); g.units["white_%d" % (i + 1)]["x"] = float(s["xs"][i])
    for u in g.units.values(): u["hp"] = u["max_hp"] = 500.0
    assert g.submit_throw("red_1", s["angle"], s["power"])["success"]
    rec = g.resolve_round()["results"][0]
    eng = int(rec["hit_target"].split("_")[1]) - 1 if str(rec.get("hit_target", "")).startswith("white_") and rec["hit_type"] == "hero" else (-3 if rec["hit_type"] == "central_wall" else -1)
    bounce = s["hero"] in ("knight", "hunchback")
    dx = abs(rec["landing_x"] - a["x"]) if rec.get("landing_x") is not None else 999
    if dx < 999 and not bounce: xdev[s["hero"]].append(dx)
    same_id = eng == a["hit"] or (s["hero"] == "bride" and eng >= 0 and a["hit"] >= 0)   # the wave hurts several units: the page list gives the first damaged index, the engine the nearest touched one, so for the bride only landing x is compared when both hit somebody
    if not same_id or (dx > 1.0 and not bounce): bad.append(("PAGE/ENGINE-ID" if not same_id else "PAGE/ENGINE-X") + " %s %s wind %s ang %d pw %d: page hit %d x %.1f | engine hit %d x %s" % (s["hero"], s["weather"], s["wind"], s["angle"], s["power"], a["hit"], a["x"], eng, rec.get("landing_x")))
    mx = 1810 - 110 - b["x"] if False else None
    if a["hit"] != b["hit"] or abs((a["x"] - 110) - (1810 - b["x"])) > 1.0: bad.append("MIRROR %s %s wind %s ang %d pw %d: L2R hit %d x %.1f | R2L hit %d x %.1f" % (s["hero"], s["weather"], s["wind"], s["angle"], s["power"], a["hit"], a["x"], b["hit"], b["x"]))
    res[(s["hero"], s["weather"], s["wind"])][(s["angle"], s["power"])] = (a["hit"], a["x"], a["dmg"])
summary = {}; lines = []
for hero in HEROES:
    calm = res[(hero, "clear", 0)]; calm_rear = {k for k, v in calm.items() if v[0] == 2}
    row = {}
    for weather, wind in COND:
        r = res[(hero, weather, wind)]; rear = {k for k, v in r.items() if v[0] == 2}
        shift = [abs(r[k][1] - calm[k][1]) for k in calm_rear if r[k][0] != -3 and calm[k][0] != -3]
        row["%s%+d" % (weather, wind)] = {"rear_hits": len(rear), "still_hit_of_calm": len(rear & calm_rear), "calm_pairs": len(calm_rear), "mean_shift_px": round(statistics.mean(shift), 1) if shift else None, "max_shift_px": round(max(shift), 1) if shift else None}
    summary[hero] = row
    lines.append("%-9s calm rear-hit pairs %3d | wind +5: %3d hit (kept %3d, mean shift %s px) | wind -5: %3d hit (kept %3d, mean shift %s px) | storm +5: %3d | storm -5: %3d" % (hero, len(calm_rear), row["clear+5"]["rear_hits"], row["clear+5"]["still_hit_of_calm"], row["clear+5"]["mean_shift_px"], row["clear-5"]["rear_hits"], row["clear-5"]["still_hit_of_calm"], row["clear-5"]["mean_shift_px"], row["storm+5"]["rear_hits"], row["storm-5"]["rear_hits"]))
print("shots per direction %d | page/engine + mirror mismatches %d" % (len(A), len(bad)))
neq = collections.Counter((h, k) for h in HEROES for k in ("rain", "snow", "fog") for w in (-5, 5) for p in res[(h, "clear", w)] if (res[(h, k, w)][p][:1] != res[(h, "clear", w)][p][:1]) or (h not in ("knight", "hunchback") and res[(h, k, w)][p][1] != res[(h, "clear", w)][p][1]))
print("rain/snow/fog flight differs from clear at the same wind (pairs): %s" % (dict(neq) or "none"))
ex = [(h, k, w, p, res[(h, k, w)][p][:2], res[(h, "clear", w)][p][:2]) for h in HEROES for k in ("rain", "snow", "fog") for w in (-5, 5) for p in res[(h, "clear", w)] if res[(h, k, w)][p][:1] != res[(h, "clear", w)][p][:1]][:3]
for e in ex: print("   ", e)
for h in HEROES: print("  landing-x difference page vs engine, %-9s %s" % (h, ("max %.1f px  mean %.2f px  (%d shots)" % (max(xdev[h]), statistics.mean(xdev[h]), len(xdev[h]))) if xdev[h] else "n/a (bouncing weapon: only who was hit is compared)"))
for l in lines: print(l)
cat = collections.Counter((b.split()[0], b.split()[1], b.split()[2], b.split()[3]) for b in bad)   # (kind, hero, weather, "wind")
by = collections.Counter()
for b in bad: t = b.split(); by[(t[0], t[1], t[3] + " " + t[4])] += 1
for k, v in sorted(by.items()): print("  mismatch", k, v)
for b in bad[:6]: print("  " + b)
if OUT: json.dump({"meta": {"command": "python3 -B scripts/rear_rear_weather_wind.py --out " + OUT, "git_head_when_run": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=os.path.dirname(HERE)).stdout.strip(), "shots_per_direction": len(A)}, "range_px": 1700, "summary": summary, "mismatches": len(bad)}, open(OUT, "w"), indent=1)
sys.exit(1 if bad else 0)
