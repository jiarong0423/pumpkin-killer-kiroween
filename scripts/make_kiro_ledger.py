#!/usr/bin/env python3
"""Write docs/KIRO_LEDGER.md: ONE table of every Kiro task so assignments and results are recorded in one place.
Sources (read only): docs/kiro_task_NN.md (the brief and its first heading), result/output files docs/kiro_NN_* in this folder (MERGED into main)
and in ../pumpkin-killer_kiroNN*/docs (only in a worktree, NOT merged), kiro_route_*.log lines (model, status), docs/kiro_verified.json (the main line's own re-checks).
Default is --check (prints the table, exit 0, writes nothing); --apply writes docs/KIRO_LEDGER.md (previous copy backed up to docs/audition/). Log: docs/audition/kiro_ledger.log. Exit 1 on any failure."""
import glob
import json
import os
import re
import shutil
import sys
import time
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "docs", "KIRO_LEDGER.md")
LOG = os.path.join(ROOT, "docs", "audition", "kiro_ledger.log")


def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def title_of(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                return re.sub(r"^#+\s*(Kiro task \d+\s*[—:-]\s*)?", "", line.strip())[:90]
    return ""


def route_status(n):
    """Last status found in any kiro_route log of task n: (model, status)."""
    best = ("", "no log")
    pats = [os.path.join(ROOT, "kiro_route_kiro_task_%s.log" % n), os.path.join(PARENT, "pumpkin-killer_kiro%s*" % n, "kiro_route_kiro_task_%s.log" % n)]
    for pat in pats:
        for p in glob.glob(pat):
            model, status = "", "no result line"
            with open(p, encoding="utf-8") as f:
                for line in f:
                    m = re.search(r"model (\S+) attempt", line)
                    if m:
                        model = m.group(1)
                    if "DONE with" in line:
                        status = "ok"
                    elif "every model" in line:
                        status = "failed"
                    elif "throttled" in line and status != "ok":
                        status = "throttled"
            best = (model, status)
    return best


def main(argv):
    apply = "--apply" in argv
    try:
        verified = {}
        vp = os.path.join(ROOT, "docs", "kiro_verified.json")
        if os.path.exists(vp):
            with open(vp, encoding="utf-8") as f:
                verified = json.load(f)
        ids = {}
        for p in glob.glob(os.path.join(ROOT, "docs", "kiro_task_*.md")):
            m = re.search(r"kiro_task_(\d+)\.md$", p)
            if m:
                ids[int(m.group(1))] = p
        rows = []
        for n in sorted(ids):
            brief = ids[n]
            merged = sorted(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "docs", "kiro_%d_*" % n)))
            wt = sorted(set(os.path.basename(p) for p in glob.glob(os.path.join(PARENT, "pumpkin-killer_kiro%d*" % n, "docs", "kiro_%d_*" % n))) - set(merged))
            model, status = route_status(n)
            v = verified.get(str(n), {})
            rows.append("| %d | %s | %s | %s | %s | %s | %s |" % (
                n, title_of(brief).replace("|", "/"), model or "-", status,
                ("main: " + ", ".join(merged)) if merged else "-",
                ("worktree only: " + ", ".join(wt)) if wt else "-",
                ("%s: %s" % (v["status"], v["what"])) if v else "not checked by the main line"))
        head = ["# Kiro ledger (generated %s by scripts/make_kiro_ledger.py)" % time.strftime("%Y-%m-%d %H:%M"), "",
                "One row per task brief in docs/. 'main' = the result file is inside this project; 'worktree only' = it exists only in a ../pumpkin-killer_kiroNN folder and is NOT merged.",
                "The last column comes from docs/kiro_verified.json, which only the main line edits after re-running a check itself. Route status comes from the kiro_route logs (they may be missing for old tasks).", "",
                "| id | task | model | route status | results | unmerged | main-line verification |", "|---|---|---|---|---|---|---|"]
        text = "\n".join(head + rows) + "\n"
        print(text)
        if not apply:
            log("CHECK only: %d tasks, nothing written (use --apply)" % len(rows))
            return 0
        if os.path.exists(OUT):
            shutil.copy2(OUT, os.path.join(ROOT, "docs", "audition", "backup_KIRO_LEDGER_%s.md" % time.strftime("%Y%m%d_%H%M%S")))
        with open(OUT, "w", encoding="utf-8") as f:
            f.write(text)
        log("OK wrote %s (%d tasks)" % (OUT, len(rows)))
        return 0
    except Exception as e:
        log("ERROR %r\n%s" % (e, traceback.format_exc()))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
