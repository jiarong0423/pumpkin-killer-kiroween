#!/bin/zsh
# 20,000-match random simulation on both ends (owner 2026-11-17: run the back end first, then the front end, likewise random simulation).
# One worker process per hero (8 heroes x 3 sizes x 834 plays = 20,016 matches per end), seeds from docs/MATRIX_SPEC_20261117.md (plays >= 10 have their own seed ranges).
# Usage: zsh scripts/run_matrix_20k.sh engine|page|merge     (engine: Python engine, page: the real index.html in the Node vm, merge: one file per end)
# Writes logs_local/m20k/<end>_<hero>.json and logs_local/m20k/<end>_<hero>.log; merge writes logs_local/matrix_engine_20k.json and logs_local/matrix_page_vm_20k.json. Exit code 1 if any worker fails.
ROOT="${0:A:h:h}"
cd "$ROOT" || exit 2
OUT=logs_local/m20k
HEROES=(skeleton wizard bat knight bride hunchback reaper hag)
PLAYS=${PLAYS:-834}   # plays per hero and size: 834 -> 20,016 matches per end, 417 -> 10,008
CHUNK=${CHUNK:-34}     # plays per page chunk: a chunk is CHUNK plays x 3 sizes = 3 x CHUNK matches in one fresh process (measured 1.9 MB per match + 130 MB base: 34 plays -> about 320 MB)
RICH=${RICH:-0}      # 1: full events (skills, ultimates, defend, crates; engine bot --rich, page --rich)
if [ "$RICH" = 1 ]; then OUT=logs_local/m_rich; RICHARG=--rich; SUFFIX=rich; else RICHARG=""; SUFFIX=20k; fi
mkdir -p "$OUT"
WORKERS=${WORKERS:-4}   # heroes run in waves of this many parallel workers (owner approved 4 on 2026-11-17: about 1.2 GB for the page run); resource-run-gate computes the safe number
started=0
throttle() { started=$(( started + 1 )); [ $(( started % WORKERS )) -eq 0 ] && wait; }
case "$1" in
  engine)
    for h in $HEROES; do
      /opt/anaconda3/bin/python3 -B scripts/engine_matrix.py --heroes $h --plays $PLAYS $RICHARG --quiet --out "$OUT/engine_$h.json" > "$OUT/engine_$h.log" 2>&1 &
      throttle
    done ;;
  page)
    # one worker per hero; each worker runs its plays in chunks of 100, one fresh node process per chunk (the page leaves about 1 MB per match in a process: 2,502 matches in one process need about 2.5 GB, eight workers swapped the 16 GB machine); a finished chunk file is kept and skipped on a rerun (resume)
    for h in $HEROES; do
      (
        from=0
        while [ $from -lt $PLAYS ]; do
          to=$(( from + CHUNK )); [ $to -gt $PLAYS ] && to=$PLAYS
          f="$OUT/page_${h}_$(printf %04d $from).json"
          if [ ! -f "$f" ]; then
            node scripts/run_page_matrix_vm.js --hero $h --per-cell $PLAYS --from $from --to $to $RICHARG --out "$f.tmp" >> "$OUT/page_$h.log" 2>&1 && mv "$f.tmp" "$f" || { echo "ERROR chunk $h $from failed" >> "$OUT/page_$h.log"; exit 1; }
          fi
          from=$to
        done
      ) &
      throttle
    done ;;
  merge)
    OUT_DIR="$OUT" SUFFIX="$SUFFIX" PLAYS="$PLAYS" CHUNK="$CHUNK" /opt/anaconda3/bin/python3 -B - <<'PY'
import json, os, sys
import math
out = os.environ.get("OUT_DIR", "logs_local/m20k"); suffix = os.environ.get("SUFFIX", "20k"); plays = int(os.environ.get("PLAYS", "834")); chunk = int(os.environ.get("CHUNK", "34")); bad = 0
for end, name in (("engine", "matrix_engine_%s.json" % suffix), ("page", "matrix_page_vm_%s.json" % suffix)):
    files = sorted(f for f in os.listdir(out) if f.startswith(end + "_") and f.endswith(".json"))
    matches = []
    for f in files:
        matches += json.load(open(os.path.join(out, f)))["matches"]
    seeds = {(m["hero"], m["size"], m["seed"]) for m in matches}
    print(end, len(files), "files,", len(matches), "matches,", len(seeds), "distinct (hero, size, seed)")
    expected_files = 8 if end == "engine" else 8 * math.ceil(plays / float(chunk))   # the page runs chunks of up to CHUNK plays per hero
    if len(files) != expected_files or len(matches) != 8 * 3 * plays or len(seeds) != len(matches):
        print("ERROR: " + end + " incomplete or duplicated"); bad = 1
    json.dump({"end": end, "matches": matches}, open("logs_local/" + name, "w"))
sys.exit(bad)
PY
    exit $? ;;
  *) echo "usage: zsh scripts/run_matrix_20k.sh engine|page|merge"; exit 2 ;;
esac
FAIL=0
for job in ${(k)jobstates}; do :; done
wait || FAIL=1
for f in $OUT/${1}_*.log; do grep -q "^ERROR\|Traceback" "$f" && { echo "ERROR in $f"; FAIL=1; }; done
exit $FAIL
