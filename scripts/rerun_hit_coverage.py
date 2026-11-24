#!/usr/bin/env python3
"""Re-run the whole hit-coverage evidence chain in one go, one process at a time (owner 2026-11-18/19: data only, then compress to a snapshot chart and delete the dry-run files):
  1. real matches, 40 per team size, three fence modes (natural, held down, forced down mid-match)   scripts/trace_match_hits.js
  2. every angle x power, both directions, fence destroyed: plain throws and ultimates             scripts/trace_ult_down.js
  3. every ultimate with the fence one hit from breaking                                           scripts/trace_ult_down.js --wall-one-hit
  Each trace is judged by scripts/check_match_hits.py (box AND binary mask); the counts, INCLUDING the exempted steps (red-team H1 R1-A5), go to redteam/evidence/hit_wall_down_judge_counts_<date>.json; the chart
  docs/hit_coverage_<date>.svg/.json is rebuilt by scripts/make_hit_coverage_snapshot.py; the big jsonl files are then deleted. Exit 1 when any FALSE_HIT or MISSED_HIT exists.
usage: python3 -B scripts/rerun_hit_coverage.py --date 20261119 [--log logs_local/rerun_hit_coverage.log]"""
import json, os, re, shutil, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); os.chdir(ROOT)
A = sys.argv; DATE = A[A.index("--date") + 1] if "--date" in A else time.strftime("%Y%m%d")
D = "logs_local/hit_trace"; os.makedirs(D, exist_ok=True)
STEPS = [("full_natural", ["node", "scripts/trace_match_hits.js", "--wall", "natural", "--matches", "40"]), ("full_down", ["node", "scripts/trace_match_hits.js", "--wall", "down", "--matches", "40"]),
         ("full_mid", ["node", "scripts/trace_match_hits.js", "--wall", "mid", "--matches", "40"]), ("plain_down", ["node", "scripts/trace_ult_down.js", "--plain"]),
         ("ult_down", ["node", "scripts/trace_ult_down.js"]), ("ult_break", ["node", "scripts/trace_ult_down.js", "--wall-one-hit"])]
counts = {}; bad = 0
for name, cmd in STEPS:
    out = "%s/%s.jsonl" % (D, name); t0 = time.time()
    r = subprocess.run(cmd + ["--out", out], capture_output=True, text=True)
    if r.returncode: print("ERROR trace %s failed: %s" % (name, r.stderr[-300:])); sys.exit(2)
    if not os.path.exists(out) or os.path.getsize(out) == 0: print("ERROR trace %s wrote no records" % name); sys.exit(2)   # red-team H1 R2-A2: never go green on an empty trace
    j = subprocess.run([sys.executable, "-B", "scripts/check_match_hits.py", out], capture_output=True, text=True).stdout
    c = {"steps": 0, "FALSE_HIT": 0, "MISSED_HIT": 0, "area_or_return_steps": 0, "blocked_steps": 0, "nearest_touched_exempt": 0}
    for m in re.finditer(r"(wall_\w+)\s+steps (\d+)\s+FALSE_HIT (\d+)\s+MISSED_HIT (\d+)\s+\(exempt from FALSE_HIT: (\d+) area/return steps; from MISSED_HIT: (\d+) blocked steps, (\d+) nearest-touched units\)", j):
        for k, v in zip(("steps", "FALSE_HIT", "MISSED_HIT", "area_or_return_steps", "blocked_steps", "nearest_touched_exempt"), m.groups()[1:]): c[k] += int(v)
    strict = len(re.findall(r"^wall_\w+\s+steps \d+\s+FALSE_HIT \d+\s+MISSED_HIT \d+\s+\(exempt from FALSE_HIT: \d+ area/return steps; from MISSED_HIT: \d+ blocked steps, \d+ nearest-touched units\)", j, re.M))
    total = re.search(r"physics steps judged (\d+)", j)   # red-team H1 R3-A2: all three state lines must parse strictly and add up to the judge's own total
    states = len(re.findall(r"^wall_\w+\s+steps", j, re.M))
    if states != 3 or strict != 3 or not total or int(total.group(1)) != c["steps"] or c["steps"] <= 0: print("ERROR judge output of %s not understood (%d state lines, %d steps)" % (name, states, c["steps"])); sys.exit(2)   # the files stay for inspection
    counts[name] = c; bad += c["FALSE_HIT"] + c["MISSED_HIT"]; print("%-12s %s (%.0f s)" % (name, json.dumps(c), time.time() - t0), flush=True)
five_steps = sum(counts[k]["steps"] for k in ("full_natural", "full_down", "full_mid", "plain_down", "ult_down"))
if five_steps < 200000:
    print("ERROR five-trace total steps %d looks truncated (< 200000); keeping traces" % five_steps); sys.exit(2)
bak_dir = "redteam/backups/bak_hit_coverage_%s" % DATE
os.makedirs(bak_dir, exist_ok=True)
counts_out = "redteam/evidence/hit_wall_down_judge_counts_%s.json" % DATE
chart_prefix = "docs/hit_coverage_%s" % DATE
for p in (counts_out, chart_prefix + ".svg", chart_prefix + ".json"):
    if os.path.exists(p): shutil.copy2(p, os.path.join(bak_dir, os.path.basename(p)))
json.dump(counts, open("%s/judge_counts.json" % D, "w")); json.dump(counts, open(counts_out, "w"), indent=1)
s = subprocess.run([sys.executable, "-B", "scripts/make_hit_coverage_snapshot.py", "--dir", D, "--out", chart_prefix], capture_output=True, text=True)
if s.returncode: print("ERROR snapshot failed: " + s.stderr[-300:]); sys.exit(2)
if not bad:
    for name, _ in STEPS: os.remove("%s/%s.jsonl" % (D, name))   # kept for inspection when anything was flagged
print("snapshot docs/hit_coverage_%s.svg written, dry-run files %s, FALSE_HIT+MISSED_HIT = %d" % (DATE, "kept" if bad else "deleted", bad)); sys.exit(1 if bad else 0)
