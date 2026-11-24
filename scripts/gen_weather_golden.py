#!/usr/bin/env python3
"""Write portable weather vectors from the Python implementation."""
import json
from pathlib import Path

from weather_py import for_round

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "shared" / "weather_golden.json"
SCENES = ("graveyard", "church", "school", "bell_tower")


def generate():
    cases = []
    for seed in range(5):
        for round_number in range(1, 41):
            for scene in SCENES:
                cases.append({"seed": seed, "round": round_number, "scene": scene,
                              "weather": for_round(seed, round_number, scene)})
    OUTPUT.write_text(json.dumps({"version": 1, "cases": cases}, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print("wrote %d weather golden cases to %s" % (len(cases), OUTPUT))


if __name__ == "__main__":
    generate()
