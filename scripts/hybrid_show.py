#!/usr/bin/env python3
"""Print the matches of a hybrid run result file in one line each (seed, winner, rounds, hash rounds, first hash difference, errors).

  python3 -B scripts/hybrid_show.py logs_local/hybrid_run_20261117.json
"""
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
for m in data["matches"]:
    print(m["seed"], m.get("seat_left"), "vs", m.get("seat_right"), m["winner"], m["rounds"], "relay", m.get("relay_errors"), "hash", m.get("hash_disagree_rounds"),
          "| diff:", (m.get("hash_diff") or [])[:2], "| errors:", [e[:160] for e in m["errors"]][:3])
    if m.get("relay_error_context"):
        print("   relay error while:", m["relay_error_context"][:2])
