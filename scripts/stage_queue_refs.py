#!/usr/bin/env python3
"""Copy a Colab job queue and every reference picture it names into the Drive inputs folder as NEW files (never overwrites).
Run it in your own terminal (the sandbox cannot write to Google Drive).
Usage: python3 -B scripts/stage_queue_refs.py --queue colab/jobs_queue_round3_20261115.json --name jobs_queue_round3.json [--dest DIR]
The default destination is the first Drive folder  */PumpkinKiller/inputs  under ~/Library/CloudStorage.
"""
import argparse, glob, hashlib, json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--dest", default="")
    a = ap.parse_args()
    dest = a.dest or (sorted(glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*/*/PumpkinKiller/inputs")) ) or [""])[0]
    if not dest or not os.path.isdir(dest):
        print("ERROR Drive inputs folder not found", file=sys.stderr); return 1
    q = os.path.join(ROOT, a.queue) if not os.path.isabs(a.queue) else a.queue
    spec = json.load(open(q, encoding="utf-8"))
    rc = 0
    for name, rel in sorted(spec["refs"].items()):
        if rel.startswith("out:"):
            continue
        src = os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            print("ERROR missing", rel, file=sys.stderr); rc = 1; continue
        dst = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            print("SKIP exists", rel)
        else:
            shutil.copyfile(src, dst); print("OK", rel)
    dq = os.path.join(dest, a.name)
    shutil.copyfile(q, dq)
    print("OK queue", a.name, "checksum matches" if sha(q) == sha(dq) else "CHECKSUM DIFFERS")
    return rc if sha(q) == sha(dq) else 1


if __name__ == "__main__":
    sys.exit(main())
