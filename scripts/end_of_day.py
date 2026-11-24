#!/usr/bin/env python3
"""End-of-day routine (owner 2026-11-10: before stopping each day, merge, inventory and generate the progress table).
Default is a plan only (prints the steps, runs nothing). With --apply it runs, in order:
  1. scripts/make_asset_inventory.py            (docs/asset_inventory.json)
  2. scripts/make_kiro_ledger.py --apply        (docs/KIRO_LEDGER.md)
  3. scripts/daily_log.py --apply --date D      (docs/daily/<D>.md and docs/PROGRESS_TABLE.md)
  4. the test scripts (node scripts/test_*.js, python3 -B scripts/test_*.py, one at a time) and writes the result table to docs/kiro_evidence/<D>_tests.md
Then it prints the manual checklist (merge verified Kiro results, record each check with scripts/kiro_record.py, refresh HANDOFF.md, commit only this day's files, never push).
It never merges, commits, pushes or touches the cloud. Exit 0 all steps ok; 1 a step failed (the table still lists it); 2 bad arguments. Log: docs/audition/end_of_day.log."""
import glob
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "docs", "audition", "end_of_day.log")
KNOWN_FAIL = {"test_i18n.js": "missing assets/i18n/zh-TW.json (known)"}


def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(cmd, timeout=300):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    tail = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
    return r.returncode, tail[0][:140]


def main(argv):
    apply = "--apply" in argv
    date = time.strftime("%Y-%m-%d")
    for i, a in enumerate(argv):
        if a == "--date" and i + 1 < len(argv):
            date = argv[i + 1]
    py = sys.executable
    steps = [("asset inventory", [py, "-B", "scripts/make_asset_inventory.py"]),
             ("Kiro ledger", [py, "-B", "scripts/make_kiro_ledger.py", "--apply"]),
             ("daily log and progress table", [py, "-B", "scripts/daily_log.py", "--apply", "--date", date])]
    if not apply:
        log("PLAN only (use --apply to run) for date %s" % date)
        for n, c in steps:
            log("  would run: %s  (%s)" % (" ".join(c[1:]), n))
        log("  would run every scripts/test_*.js and scripts/test_*.py and write docs/kiro_evidence/%s_tests.md" % date)
        return 0
    bad = 0
    for n, c in steps:
        try:
            code, tail = run(c)
        except Exception as e:
            code, tail = 1, repr(e)
        log("%s %s: %s" % ("OK" if code == 0 else "ERROR", n, tail))
        bad += code != 0
    rows = []
    tests = sorted(glob.glob(os.path.join(ROOT, "scripts", "test_*.js"))) + sorted(glob.glob(os.path.join(ROOT, "scripts", "test_*.py")))
    for t in tests:
        name = os.path.basename(t)
        cmd = ["node", t] if t.endswith(".js") else [py, "-B", t]
        try:
            code, tail = run(cmd)
        except Exception as e:
            code, tail = 1, repr(e)
        known = name in KNOWN_FAIL and code != 0
        rows.append("| %s | %s | %s |" % (name, "OK" if code == 0 else ("known failure" if known else "FAIL"), (KNOWN_FAIL[name] if known else tail).replace("|", "/")))
        bad += (code != 0 and not known)
    out = os.path.join(ROOT, "docs", "kiro_evidence", "%s_tests.md" % date)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("# Test run %s (by scripts/end_of_day.py, one test at a time)\n\n| test | result | last line |\n|---|---|---|\n%s\n" % (date, "\n".join(rows)))
    log("%s wrote %s (%d tests, %d problems in total)" % ("OK" if not bad else "ERROR", out, len(rows), bad))
    log("MANUAL: 1) merge the Kiro results you verified today (worktree diff, tests, then merge); 2) python3 -B scripts/kiro_record.py TASK STATUS \"command and result\" for each check; "
        "3) add today's evidence file docs/kiro_evidence/%s.md; 4) refresh HANDOFF.md; 5) commit only today's files (no broad stage, no co-author trailer, no push)." % date)
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:
        log("ERROR %r" % (e,))
        sys.exit(1)
