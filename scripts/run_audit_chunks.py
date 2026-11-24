#!/usr/bin/env python3
"""Run the page-match event audit (scripts/audit_page_events.js) for N matches in small chunks, each chunk in a FRESH node process (resident memory grows about 3.5 MB per match inside one process: 20,000 matches in one process would need ~70 GB),
a few chunks at a time, resumable (a finished chunk file is skipped, a chunk is written under a temporary name and renamed when done), refusing to start a chunk when free memory is below the floor, then merged into logs_local/audit/merged.json.
usage: python3 -B scripts/run_audit_chunks.py --total 20000 --chunk 80 --workers 3 [--min-free-pct 20] [--keep-chunks]
Exit codes: 0 done and merged, 1 a chunk failed, 2 stopped for low memory (rerun to resume). Log: logs_local/audit/run.log (failures start with ERROR)."""
import json, os, re, subprocess, sys, time, concurrent.futures
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); os.chdir(ROOT)
A = sys.argv; arg = lambda k, d: A[A.index("--" + k) + 1] if "--" + k in A else d
TOTAL, CHUNK, WORKERS, FLOOR = int(arg("total", 20000)), int(arg("chunk", 80)), int(arg("workers", 3)), int(arg("min-free-pct", 20))
D = "logs_local/audit"; os.makedirs(D, exist_ok=True); LOG = open(D + "/run.log", "a")
def log(m): LOG.write(time.strftime("%H:%M:%S ") + m + "\n"); LOG.flush(); print(m, flush=True)
def free_pct():
    out = subprocess.run(["memory_pressure"], capture_output=True, text=True).stdout
    m = re.search(r"free percentage: (\d+)%", out); return int(m.group(1)) if m else 100
def run(start):
    f = "%s/chunk_%06d.json" % (D, start)
    if os.path.exists(f): return ("skip", start)
    if free_pct() < FLOOR: return ("lowmem", start)
    n = min(CHUNK, TOTAL - start)
    r = subprocess.run(["node", "scripts/audit_page_events.js", "--from", str(start), "--matches", str(n), "--out", f], capture_output=True, text=True)
    if r.returncode or not os.path.exists(f): log("ERROR chunk %d failed: %s" % (start, r.stderr[-200:])); return ("fail", start)
    return ("ok", start)
starts = list(range(0, TOTAL, CHUNK)); t0 = time.time(); done = 0; low = False; fail = False
log("start total %d chunk %d workers %d floor %d%% (%d chunks)" % (TOTAL, CHUNK, WORKERS, FLOOR, len(starts)))
with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
    for status, start in ex.map(run, starts):
        if status == "ok": done += 1
        if status == "lowmem": low = True
        if status == "fail": fail = True
        if status == "ok" and done % 10 == 0: log("progress %d chunks done in %.0f s, free memory %d%%" % (done, time.time() - t0, free_pct()))
if fail: log("ERROR at least one chunk failed"); sys.exit(1)
if low: log("ERROR stopped: free memory under %d%%; rerun to resume" % FLOOR); sys.exit(2)
files = sorted(f for f in os.listdir(D) if f.startswith("chunk_") and f.endswith(".json"))
r = subprocess.run(["node", "scripts/audit_page_events.js", "--report"] + [D + "/" + f for f in files] + ["--write", D + "/merged.json"], capture_output=True, text=True)
open(D + "/report.txt", "w").write(r.stdout); log("merged %d chunks; report in %s/report.txt" % (len(files), D)); print(r.stdout[-2500:])
if "--keep-chunks" not in A:
    for f in files: os.remove(D + "/" + f)
log("done in %.0f s" % (time.time() - t0))
