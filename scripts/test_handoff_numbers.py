#!/usr/bin/env python3
"""Source pin (red-team H1 R3B P1-1): verify that numbers cited in HANDOFF.md and
docs/GAP_QUEUE_OPEN_20261119.md match the live evidence files on disk."""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def read_text(rel):
    with open(os.path.join(ROOT, rel), "r", encoding="utf-8") as f:
        return f.read()


def main():
    required = (
        "HANDOFF.md",
        "docs/GAP_QUEUE_OPEN_20261119.md",
        "redteam/evidence/full_suite_after_h1r2fix_20261119.txt",
    )
    if not all(os.path.exists(os.path.join(ROOT, rel)) for rel in required):
        print("SKIP test_handoff_numbers: internal working-repo files absent in clean release export")
        return 0
    counts = json.loads(read_text("redteam/evidence/hit_wall_down_judge_counts_20261119.json"))
    five_keys = ("full_natural", "full_down", "full_mid", "plain_down", "ult_down")
    five_steps = sum(counts[k]["steps"] for k in five_keys)
    break_steps = counts["ult_break"]["steps"]
    five_area = sum(counts[k]["area_or_return_steps"] for k in five_keys)
    five_blocked = sum(counts[k]["blocked_steps"] for k in five_keys)
    five_nearest = sum(counts[k]["nearest_touched_exempt"] for k in five_keys)
    six_blocked = sum(v["blocked_steps"] for v in counts.values())
    six_nearest = sum(v["nearest_touched_exempt"] for v in counts.values())
    area_pct = f"{five_area / five_steps * 100:.1f}%"

    suite_txt = read_text("redteam/evidence/full_suite_after_h1r2fix_20261119.txt")
    n_pass = len(re.findall(r"^PASS ", suite_txt, re.M))
    n_fail = len(re.findall(r"^FAIL ", suite_txt, re.M))
    n_skip = len(re.findall(r"^SKIP ", suite_txt, re.M))

    rear = json.loads(read_text("docs/rear_rear_weather_wind_20261119.json"))
    shots_per_dir = rear["meta"]["shots_per_direction"]

    handoff = read_text("HANDOFF.md")
    queue = read_text("docs/GAP_QUEUE_OPEN_20261119.md")

    checks = [
        ("five_steps", f"{five_steps:,}", (handoff, queue)),
        ("break_steps", f"{break_steps:,}", (handoff, queue)),
        ("five_area", f"{five_area:,}", (handoff, queue)),
        ("area_pct", area_pct.replace("%", ""), (handoff, queue)),
        ("five_blocked", str(five_blocked), (handoff,)),
        ("five_nearest", str(five_nearest), (handoff,)),
        ("six_blocked", str(six_blocked), (handoff,)),
        ("six_nearest", str(six_nearest), (handoff,)),
        ("shots_per_dir", f"{shots_per_dir:,}", (handoff,)),
        ("suite_pass", f"{n_pass} 過", (handoff,)),
        ("suite_fail", f"{n_fail} 失敗", (handoff,)),
        ("suite_skip", f"{n_skip} 跳過", (handoff,)),
        ("suite_ref", "full_suite_after_h1r2fix_20261119.txt", (handoff,)),
    ]
    for name, needle, texts in checks:
        for i, txt in enumerate(texts):
            assert needle in txt, f"{name}: expected {needle!r} in doc #{i}"

    print(
        f"test_handoff_numbers: OK (5-trace={five_steps:,}, break={break_steps:,}, "
        f"area={five_area:,} [{area_pct}], suite={n_pass}/{n_fail}/{n_skip}, "
        f"rear_rear={shots_per_dir:,})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
