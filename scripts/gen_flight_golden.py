#!/usr/bin/env python3
"""Generate deterministic golden vectors from the Python shared-flight implementation."""
import json
import os

from flight_py import simulate

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OUTPUT = os.path.join(_ROOT, "shared", "flight_golden.json")


def compact(result):
    return {"landingX": result["landingX"], "landingY": result["landingY"], "hit": result["hit"]}


def build_cases():
    cases = []
    angles = [10, 20, 30, 40, 50, 60, 70, 80]
    powers = [20, 35, 50, 65, 80, 100]
    winds = [-5, -3, -1, 0, 1, 3, 5]
    starts = [(278, 750, 1), (510, 750, 1), (1412, 750, -1), (1655, 750, -1)]
    for index in range(64):
        start_x, start_y, direction = starts[index % len(starts)]
        data = {
            "startX": start_x,
            "startY": start_y,
            "dirX": direction,
            "angleDeg": angles[index % len(angles)],
            "power": powers[(index * 3) % len(powers)],
            "wind": winds[(index * 5) % len(winds)],
        }
        cases.append({"name": "grid-%02d" % index, "input": data, "result": compact(simulate(data))})
    fence = {"startX": 300, "startY": 750, "dirX": 1, "angleDeg": 35, "power": 70, "wind": 0}
    out = {"startX": 1660, "startY": 750, "dirX": 1, "angleDeg": 10, "power": 100, "wind": 0}
    wave_cases = []
    for index, (angle, power, wind, start_x, direction) in enumerate([(55, 85, 0, 300, 1), (50, 95, -3, 300, 1), (65, 80, 0, 300, 1), (58, 92, -2, 300, 1), (55, 85, 0, 1660, -1), (65, 80, 0, 1660, -1)]):   # every case lands on the ground beyond the fence
        data = {"startX": start_x, "startY": 750, "dirX": direction, "angleDeg": angle, "power": power, "wind": wind, "wave": True}
        wave_cases.append({"name": "wave-%02d" % index, "input": data, "result": compact(simulate(data))})
    cases.extend([
        {"name": "fence-hit", "input": fence, "result": compact(simulate(fence))},
        {"name": "right-out", "input": out, "result": compact(simulate(out))},
    ])
    cases.extend(wave_cases)   # the bride wave counts at the ground crossing point (2026-11-19, red-team H1 R1-A1); the 66 older cases are unchanged
    return cases


def main():
    payload = {"version": 1, "cases": build_cases()}
    with open(_OUTPUT, "w", encoding="utf-8") as output:
        json.dump(payload, output, indent=2, sort_keys=True)
        output.write("\n")
    print("wrote %d flight golden cases to %s" % (len(payload["cases"]), _OUTPUT))


if __name__ == "__main__":
    main()
