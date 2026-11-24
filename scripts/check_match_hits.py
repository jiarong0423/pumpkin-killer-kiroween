#!/usr/bin/env python3
"""Judge the in-match records of scripts/trace_match_hits.js with the INDEPENDENT hit rule (box AND binary mask, scripts/hit_mask_py.py), split by the state of the central fence:
  wall_up      the fence stood before and after the step
  wall_break   the step in which the fence went from > 0 to 0 hp
  wall_down    the fence was already destroyed
Per record: FALSE_HIT (damage although the rule says no contact; area effects, flagged by the tracer, are left out) and MISSED_HIT (the rule says contact, nobody was damaged, and nothing blocked the shot in that step:
fence / floating shield / knight wall). usage: python3 -B scripts/check_match_hits.py logs_local/hit_trace/matches.jsonl [--examples 5]   exit 1 on any FALSE_HIT or MISSED_HIT in any state."""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hit_mask_py import HitMasks
M = HitMasks(); EX = int(sys.argv[sys.argv.index("--examples") + 1]) if "--examples" in sys.argv else 5
def box(prof, dx, dy, r):
    hw, hh = (57, 165) if prof == "reaper" else (70, 190); return abs(dx) <= hw + r and -hh - r <= dy <= r
def touch(prof, dx, dy, r, side): return box(prof, dx, dy, r) and M.touches(prof, dx, dy, r, side == "left", True)
cnt = collections.Counter(); ex = collections.defaultdict(list); sizes = collections.Counter()
bystep = collections.defaultdict(list)
for line in open(sys.argv[1]):
    o = json.loads(line); bystep[(o["size"], o["c"], o["step_group"] if "step_group" in o else None, o["ang"], o["pw"], o["w0"], o["w1"])].append(o)
# group the records of one projectile step: the tracer wrote them in order; the projectile (ang = throw id, pw = list index) and the wall state identify the step, the unit index tells the units apart
rows = [json.loads(line) for line in open(sys.argv[1])]
# one physics step = (size, match, tick); a unit that lost hp in that step must be touched by SOME plain projectile of the same step (several shots fly at once: a double shot, a volley, both teams)
ticks = collections.OrderedDict()
for o in rows: ticks.setdefault((o["size"], o["c"], o["tick"]), []).append(o)
for key, rs in ticks.items():
    state = "wall_down" if rs[0]["w0"] <= 0 else ("wall_break" if rs[0]["w1"] <= 0 else "wall_up")
    area_in_step = any(o["area"] or o.get("ret") for o in rs)   # the boomerang axe's return hit is a deliberate bonus on the first victim, not a contact: left out like area effects
    blocked = any(o["blocked"] for o in rs)
    per_unit = collections.defaultdict(list)
    for o in rs: per_unit[(o["side"], o["i"])].append(o)
    cnt[(state, "steps")] += 1
    if area_in_step: cnt[(state, "area_steps")] += 1   # red-team H1 R1-A5: steps whose FALSE_HIT check is skipped (area effect or the boomerang return hit)
    if blocked: cnt[(state, "blocked_steps")] += 1   # steps whose MISSED_HIT check is skipped (fence, floating shield or knight wall changed in the step)
    for (side, i), us in per_unit.items():
        dmg = us[0]["hp1"] < us[0]["hp0"]; touchers = []
        for o in us:
            if o["area"] or o.get("ret"): continue
            dx, dy = o["px"] - o["ux"], o["py"] - o["uy"]
            if touch(o["prof"], dx, dy, o["hitR"], o["side"]) and not o["cool"] and not o["pierced"]: touchers.append(o)
        if dmg and not touchers and not area_in_step:
            o = us[0]; cnt[(state, "FALSE_HIT")] += 1
            if len(ex["FALSE_HIT " + state]) < EX: ex["FALSE_HIT " + state].append("size %d match %d tick %d unit %d (%s) hp %.1f->%.1f; shots in the step: %s" % (o["size"], o["c"], o["tick"], i, o["prof"], o["hp0"], o["hp1"], "; ".join("%s dx %.0f dy %.0f r %.0f%s" % (x["weapon"], x["px"] - x["ux"], x["py"] - x["uy"], x["hitR"], " ult" if x["ult"] else "") for x in us[:3])))
        if touchers and not dmg and not blocked:
            # nearest-touched rule: another touched unit of the same side may have taken it; only count when no unit of that side was damaged by that projectile step
            siblings = [x for (sd, k), vs in per_unit.items() if sd == side and k != i for x in vs if x["hp1"] < x["hp0"]]
            if siblings: cnt[(state, "sibling_exempt")] += 1   # the nearest-touched rule: a nearer unit of the same side took the shot
            if not siblings:
                o = touchers[0]; cnt[(state, "MISSED_HIT")] += 1
                if len(ex["MISSED_HIT " + state]) < EX: ex["MISSED_HIT " + state].append("size %d match %d tick %d %s dir %s unit %d (%s) dx %.1f dy %.1f hitR %.1f ult %d" % (o["size"], o["c"], o["tick"], o["weapon"], o["dir"], i, o["prof"], o["px"] - o["ux"], o["py"] - o["uy"], o["hitR"], o["ult"]))
groups = ticks
print("records %d, physics steps judged %d" % (len(rows), len(groups)))
bad = 0
for st in ("wall_up", "wall_break", "wall_down"):
    print("%-10s steps %-7d FALSE_HIT %-4d MISSED_HIT %-4d   (exempt from FALSE_HIT: %d area/return steps; from MISSED_HIT: %d blocked steps, %d nearest-touched units)" % (st, cnt[(st, "steps")], cnt[(st, "FALSE_HIT")], cnt[(st, "MISSED_HIT")], cnt[(st, "area_steps")], cnt[(st, "blocked_steps")], cnt[(st, "sibling_exempt")])); bad += cnt[(st, "FALSE_HIT")] + cnt[(st, "MISSED_HIT")]
for k, v in ex.items():
    print(k); [print("    " + e) for e in v]
sys.exit(1 if bad else 0)
