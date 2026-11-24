#!/usr/bin/env python3
"""Verify the Python weather port against shared portable golden vectors."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from weather_py import for_round  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    data = json.loads((ROOT / "shared" / "weather_golden.json").read_text(encoding="utf-8"))
    cases = data["cases"]
    assert len(cases) >= 200
    assert {case["scene"] for case in cases} >= {"graveyard", "church", "school", "bell_tower"}
    assert {case["round"] for case in cases} >= set(range(1, 41))
    for case in cases:
        actual = for_round(case["seed"], case["round"], case["scene"])
        assert actual == case["weather"], case
    print("test_weather_golden.py: %d cases passed" % len(cases))


if __name__ == "__main__":
    main()
