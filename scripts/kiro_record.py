#!/usr/bin/env python3
"""Record the main line's own check of a Kiro task in docs/kiro_verified.json and regenerate docs/KIRO_LEDGER.md.
Usage: python3 -B scripts/kiro_record.py TASK STATUS "what you re-ran and what came out" [--date YYYY-MM-DD]
STATUS is one of: verified | partly | read_only | not_checked | failed. The text must name a command or a file (the main line never copies a Kiro report as evidence).
Writes a backup of the json to docs/audition/ first; log docs/audition/kiro_record.log; exit 0 ok, 2 bad arguments, 1 failure."""
import json
import os
import shutil
import subprocess
import sys
import time
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON = os.path.join(ROOT, "docs", "kiro_verified.json")
LOG = os.path.join(ROOT, "docs", "audition", "kiro_record.log")
STATUSES = ("verified", "partly", "read_only", "not_checked", "failed")


def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def record(task, status, what, date=None, path=JSON):
    if not str(task).isdigit():
        raise ValueError("task must be a number")
    if status not in STATUSES:
        raise ValueError("status must be one of %s" % (STATUSES,))
    if len(what.strip()) < 12 or not any(k in what for k in ("python", "node", ".md", ".py", ".js", "docs/", "scripts/", "git ", "ls ", "grep", "wc ")):
        raise ValueError("the text must name the command or the file you checked")
    data = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        shutil.copy2(path, os.path.join(os.path.dirname(LOG), "backup_kiro_verified_%s.json" % time.strftime("%Y%m%d_%H%M%S")))
    data[str(int(task))] = {"status": status, "what": what.strip(), "date": date or time.strftime("%Y-%m-%d")}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return data[str(int(task))]


def main(argv):
    args = [a for a in argv if not a.startswith("--date")]
    date = None
    for i, a in enumerate(argv):
        if a == "--date" and i + 1 < len(argv):
            date = argv[i + 1]
            args = [x for x in args if x != date]
    if len(args) != 3:
        print(__doc__)
        return 2
    try:
        entry = record(args[0], args[1], args[2], date)
        log("OK task %s -> %s (%s)" % (args[0], entry["status"], entry["date"]))
        r = subprocess.run([sys.executable, "-B", os.path.join(ROOT, "scripts", "make_kiro_ledger.py"), "--apply"], capture_output=True, text=True)
        if r.returncode != 0:
            log("ERROR ledger regeneration failed: %s" % r.stdout[-300:])
            return 1
        log("OK ledger regenerated")
        return 0
    except ValueError as e:
        log("ERROR bad input: %s" % e)
        return 2
    except Exception as e:
        log("ERROR %r\n%s" % (e, traceback.format_exc()))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
