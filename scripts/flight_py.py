#!/usr/bin/env python3
"""Shared fixed-step flight model for golden-vector generation and tests."""
import json
import math
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(_ROOT, "shared", "constants.json"), encoding="utf-8") as _fh:
    CONSTANTS = json.load(_fh)

STEP = 1.0 / 60.0
WIND_TAIL = CONSTANTS["WIND_TAIL"]   # tailwind pushes harder than headwind slows (owner 2026-11-16); see js/flight.js
WIND_HEAD = CONSTANTS["WIND_HEAD"]
CANVAS_W = 1920.0
MAX_STEPS = 1200


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise TypeError("%s must be finite" % name)
    return float(value)


def simulate(data):
    """Return the page-equivalent flight, with wall, ground, and canvas-exit outcomes."""
    if not isinstance(data, dict):
        raise TypeError("input must be an object")
    start_x = _number(data.get("startX"), "startX")
    start_y = _number(data.get("startY"), "startY")
    direction = _number(data.get("dirX"), "dirX")
    angle = _number(data.get("angleDeg"), "angleDeg")
    power = _number(data.get("power"), "power")
    wind = _number(data.get("wind"), "wind")
    step = STEP if "step" not in data else _number(data["step"], "step")
    if "wave" in data and not isinstance(data["wave"], bool):
        raise TypeError("wave must be a boolean")
    wave = data.get("wave") is True   # the bride's wave counts where it REALLY lands (page tCross, engine twin): the step that crosses the ground is cut back to the crossing point
    if "wall" in data and not isinstance(data["wall"], bool):
        raise TypeError("wall must be a boolean")
    wall = data.get("wall") is not False   # owner 2026-11-19: broken central fence lets flat shots pass straight through
    if step <= 0:
        raise ValueError("step must be positive")

    radians = math.radians(angle)
    v0 = power * CONSTANTS["V0_PER_POWER"]
    vx = v0 * math.cos(radians) * direction
    vy = -v0 * math.sin(radians)
    x, y = start_x, start_y
    points = [{"x": x, "y": y}]
    for _ in range(MAX_STEPS):
        vx += wind * (WIND_TAIL if wind * direction > 0 else WIND_HEAD) * step
        vy += CONSTANTS["GRAVITY"] * step
        prev_x, prev_y = x, y
        x += vx * step
        y += vy * step
        if wave and prev_y < CONSTANTS["GROUND_Y"] < y:
            t_cross = (CONSTANTS["GROUND_Y"] - prev_y) / (y - prev_y)
            x = prev_x + (x - prev_x) * t_cross
            y = float(CONSTANTS["GROUND_Y"])
        points.append({"x": x, "y": y})
        if (wall and CONSTANTS["FENCE_X"] - CONSTANTS["FENCE_W"] / 2 <= x <= CONSTANTS["FENCE_X"] + CONSTANTS["FENCE_W"] / 2
                and y >= CONSTANTS["GROUND_Y"] - CONSTANTS["FENCE_H"]):
            return {"landingX": x, "landingY": y, "hit": "wall", "points": points}
        if y >= CONSTANTS["GROUND_Y"] and vy > 0:
            return {"landingX": x, "landingY": y, "hit": "ground", "points": points}
        if x < 0 or x > CANVAS_W:
            return {"landingX": x, "landingY": y, "hit": "out", "points": points}
    return {"landingX": x, "landingY": y, "hit": "out", "points": points}


def coarse_path(points):
    """Return at most five sampled points, snapped to the owner-approved 10 px grid."""
    if not points:
        return []
    count = min(5, len(points))
    result = []
    for index in range(count):
        point = points[round(index * (len(points) - 1) / max(1, count - 1))]
        result.append({"x": math.floor(point["x"] / 10.0 + 0.5) * 10, "y": math.floor(point["y"] / 10.0 + 0.5) * 10})
    return result


def _main():
    for line in sys.stdin:
        data = json.loads(line)
        result = simulate(data)
        sys.stdout.write(json.dumps({key: result[key] for key in ("landingX", "landingY", "hit")}, separators=(",", ":")) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    _main()
