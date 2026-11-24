#!/usr/bin/env python3
"""Judges a trace from scripts/trace_hit_paths.js with the INDEPENDENT hit rule (scripts/hit_mask_py.py: the decided box AND the binary figure mask, disk radius = the drawn shot).
Per physics step and per living enemy unit near the shot it compares what the page did (hp went down or not) with what the rule says:
  FALSE_HIT   hp went down, the rule says the shot did not touch that unit            (damage without contact: the owner's bug)
  MISSED_HIT  the rule says it touched a unit, nobody lost hp in that step             (contact without damage)
  WRONG_UNIT  a different unit than the nearest touched one lost hp
  EXTRA       more than one unit lost hp in one step of a plain (non-area) shot
  TUNNEL      the straight line between two steps passes through a unit (8 sub-points) while neither step touches and nobody was damaged in the shot
usage: python3 -B scripts/check_hit_trace.py logs_local/hit_trace/trace_pilot.jsonl [--examples 6]   exit 1 when any FALSE_HIT / WRONG_UNIT / EXTRA exists."""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hit_mask_py import HitMasks
M = HitMasks()
path = sys.argv[1]; EX = int(sys.argv[sys.argv.index("--examples") + 1]) if "--examples" in sys.argv else 6

def box(prof, dx, dy, r):
    hw, hh = (57, 165) if prof == "reaper" else (70, 190)
    return abs(dx) <= hw + r and -hh - r <= dy <= r

def touch(prof, dx, dy, r, side):
    return box(prof, dx, dy, r) and M.touches(prof, dx, dy, r, side == "left", True)

shots = collections.OrderedDict()
for line in open(path):
    o = json.loads(line); shots.setdefault((o["c"], o["dir"], o["hero"], o["ang"], o["pw"]), []).append(o)
cnt = collections.Counter(); ex = collections.defaultdict(list); by = collections.defaultdict(collections.Counter)
def note(kind, o, extra=""):
    cnt[kind] += 1; by[kind][(o["weapon"], o["dir"], o["prof"])] += 1
    if len(ex[kind]) < EX: ex[kind].append("%s %s ang %d pw %d step %d unit %d(%s) dx %.1f dy %.1f hitR %.1f %s" % (o["dir"], o["weapon"], o["ang"], o["pw"], o["step"], o["i"], o["prof"], o["px"] - o["ux"], o["py"] - o["uy"], o["hitR"], extra))
for key, recs in shots.items():
    bystep = collections.defaultdict(list)
    for o in recs: bystep[o["step"]].append(o)
    shot_damaged = any(o["hp1"] < o["hp0"] for o in recs)
    for step, rs in bystep.items():
        T = []; D = []
        for o in rs:
            cnt["records"] += 1
            dx, dy = o["px"] - o["ux"], o["py"] - o["uy"]
            t = touch(o["prof"], dx, dy, o["hitR"], o["side"]) and not o["cool"] and not o["pierced"]
            if t: T.append((abs(dx), o))
            if o["hp1"] < o["hp0"]:
                D.append(o)
                if not touch(o["prof"], dx, dy, o["hitR"], o["side"]): note("FALSE_HIT", o, "(rule: no contact; box %s)" % box(o["prof"], dx, dy, o["hitR"]))
        if len(D) > 1: note("EXTRA", D[0], "units damaged in one step: %d" % len(D))
        if T:
            want = min(T, key=lambda a: a[0])[1]
            if not D: note("MISSED_HIT", want)
            elif all(d["i"] != want["i"] for d in D) and not any(d is x[1] for d in D for x in T): note("WRONG_UNIT", D[0], "nearest touched was unit %d" % want["i"])
            elif len(D) == 1 and D[0]["i"] != want["i"]: note("WRONG_UNIT", D[0], "nearest touched was unit %d" % want["i"])
    if not shot_damaged:   # tunnelling: a straight line between two consecutive near steps
        steps = sorted(bystep)
        for a, b in zip(steps, steps[1:]):
            if b != a + 1: continue
            ra = {o["i"]: o for o in bystep[a]}
            for o2 in bystep[b]:
                o1 = ra.get(o2["i"])
                if not o1: continue
                if touch(o1["prof"], o1["px"] - o1["ux"], o1["py"] - o1["uy"], o1["hitR"], o1["side"]) or touch(o2["prof"], o2["px"] - o2["ux"], o2["py"] - o2["uy"], o2["hitR"], o2["side"]): continue
                for k in range(1, 8):
                    f = k / 8.0; qx = o1["px"] + (o2["px"] - o1["px"]) * f - o2["ux"]; qy = o1["py"] + (o2["py"] - o1["py"]) * f - o2["uy"]
                    if touch(o2["prof"], qx, qy, o2["hitR"], o2["side"]): note("TUNNEL", o2, "(passed through between steps %d and %d)" % (a, b)); break
print("records judged %d | shots %d" % (cnt["records"], len(shots)))
for kind in ("FALSE_HIT", "WRONG_UNIT", "EXTRA", "MISSED_HIT", "TUNNEL"):
    print("%-11s %d" % (kind, cnt[kind]))
    for e in ex[kind]: print("    " + e)
    if cnt[kind]: print("    by (weapon, dir, target class), top 6: " + "; ".join("%s/%s/%s %d" % (k[0], k[1], k[2], v) for k, v in by[kind].most_common(6)))
summary = {k: cnt[k] for k in ("records", "FALSE_HIT", "WRONG_UNIT", "EXTRA", "MISSED_HIT", "TUNNEL")}; summary["shots"] = len(shots)
json.dump(summary, open(path.replace(".jsonl", "_summary.json"), "w"))
sys.exit(1 if cnt["FALSE_HIT"] or cnt["WRONG_UNIT"] or cnt["EXTRA"] else 0)
