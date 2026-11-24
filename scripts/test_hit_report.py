#!/usr/bin/env python3
"""Keep the Python engine's hit report identical to shared browser vectors."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mcp_game_server import hit_report  # noqa: E402

ROOT = os.path.dirname(HERE)
with open(os.path.join(ROOT, "shared", "hit_report_vectors.json"), encoding="utf-8") as handle:
    VECTORS = json.load(handle)

assert len(VECTORS) >= 30
assert {row["hero"] for row in VECTORS} == {"skeleton", "wizard", "bat", "knight", "reaper", "bride", "hunchback", "hag"}
for row in VECTORS:
    result = hit_report(row["landingX"], row["targetX"], row["hitType"], row["weapon"])
    actual = ("wave" + result["params"]["band"] if result["kind"] == "wave" else
              "hit" if result["kind"] == "hit" else
              "fence" if result["key"] == "hitReport.fence" else
              "shield" if result["key"] == "hitReport.shield" else
              "short" if result["key"] == "hitReport.short" else "long")
    assert actual == row["expected"], row["id"]
print("test_hit_report.py: %d shared vectors passed" % len(VECTORS))
