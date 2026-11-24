#!/usr/bin/env python3
"""Constants sync test (stdlib only).

Parses the authoritative constants out of ``index.html`` (the playable browser
game) and asserts they equal ``shared/constants.json``. Fails if either side
drifts.

Run with: ``python3 -B scripts/test_constants_sync.py``
"""
import ast
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML = os.path.join(ROOT, "index.html")
CONSTANTS_JSON = os.path.join(ROOT, "shared", "constants.json")
ADAPTIVE_PYTHON = os.path.join(ROOT, "scripts", "adaptive_level.py")
ADAPTIVE_JAVASCRIPT = os.path.join(ROOT, "js", "adaptive_level.js")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _find(pattern: str, text: str, label: str) -> str:
    """Return the first capture group for ``pattern`` or fail loudly."""
    m = re.search(pattern, text)
    if not m:
        raise AssertionError(f"Could not parse {label} from index.html")
    return m.group(1)


def parse_index_html(text: str) -> dict:
    """Extract the shared constants from index.html source forms."""
    num = r"(-?\d+(?:\.\d+)?)"
    values = {
        # Plain `const NAME = value;` declarations near the top of the script.
        "GROUND_Y": float(_find(r"const\s+GROUND_Y\s*=\s*" + num, text, "GROUND_Y")),
        "FENCE_X": float(_find(r"const\s+FENCE_X\s*=\s*" + num, text, "FENCE_X")),
        "FENCE_W": float(_find(r"const\s+FENCE_W\s*=\s*" + num, text, "FENCE_W")),
        "FENCE_H": float(_find(r"const\s+FENCE_H\s*=\s*" + num, text, "FENCE_H")),
        "GRAVITY": float(_find(r"const\s+GRAVITY\s*=\s*" + num, text, "GRAVITY")),
        "TURN_SECONDS": float(_find(r"const\s+TURN_SECONDS\s*=\s*" + num, text, "TURN_SECONDS")),
        "WALL_HIT_DMG": float(_find(r"const\s+WALL_HIT_DMG\s*=\s*" + num, text, "WALL_HIT_DMG")),
        "KNIGHT_ZONE": float(_find(r"const\s+KNIGHT_ZONE\s*=\s*" + num, text, "KNIGHT_ZONE")),
        "SHIELD_WALL_COFFIN_HEIGHT": float(_find(r"SHIELD_WALL_COFFIN_HEIGHT\s*=\s*" + num, text, "SHIELD_WALL_COFFIN_HEIGHT")),
        "SHIELD_WALL_EXPIRES_AFTER_ATTACKS": float(_find(r"SHIELD_WALL_EXPIRES_AFTER_ATTACKS\s*=\s*" + num, text, "SHIELD_WALL_EXPIRES_AFTER_ATTACKS")),
        # Wind strengths: `const WIND_TAIL = 140, WIND_HEAD = 80;`
        "WIND_TAIL": float(_find(r"const\s+WIND_TAIL\s*=\s*" + num, text, "WIND_TAIL")),
        "WIND_HEAD": float(_find(r"WIND_HEAD\s*=\s*" + num, text, "WIND_HEAD")),
        # Inline launch-speed factor: `const v0 = power * 13.8;`
        "V0_PER_POWER": float(_find(r"const\s+v0\s*=\s*power\s*\*\s*" + num, text, "V0_PER_POWER")),
        # Default aim angle: `let playerAngle = 54;`
        "THROW_ANGLE_DEFAULT": float(_find(r"let\s+playerAngle\s*=\s*" + num, text, "THROW_ANGLE_DEFAULT")),
    }
    # Wind: `(Math.random() - 0.5) * 8.0` => symmetric range of +/- (span / 2).
    # Anchor on the `wind = parseFloat(` assignment: another `(Math.random() - 0.5) * 6.5`
    # (AI aim noise) appears earlier in the file and must not be mistaken for the wind range.
    span = float(_find(r"wind\s*=\s*parseFloat\(\(\(Math\.random\(\)\s*-\s*0\.5\)\s*\*\s*" + num, text, "wind span"))
    values["WIND_MIN"] = -(span / 2.0)
    values["WIND_MAX"] = span / 2.0
    return values


def parse_python_adaptive(text: str) -> dict:
    """Read the literal adaptive table without importing its controller."""
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "ADAPTIVE_LEVEL"
                for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("Could not parse ADAPTIVE_LEVEL from adaptive_level.py")


def parse_javascript_adaptive(text: str) -> dict:
    """Read the JavaScript adaptive table's simple literal values."""
    keys = ("INITIAL_LEVEL", "WINDOW_THROWS", "HIGH_RATE", "LOW_RATE", "MAX_CHANGES",
            "COOLDOWN_THROWS", "UP_REASON", "DOWN_REASON")
    values = {}
    for key in keys:
        pattern = r"\b" + key + r"\s*:\s*(?:\"([^\"]*)\"|(-?\d+(?:\.\d+)?))"
        match = re.search(pattern, text)
        if not match:
            raise AssertionError("Could not parse %s from adaptive_level.js" % key)
        values[key] = match.group(1) if match.group(1) is not None else float(match.group(2))
    return values


def main() -> int:
    parsed = parse_index_html(_read(INDEX_HTML))

    with open(CONSTANTS_JSON, "r", encoding="utf-8") as f:
        shared = json.load(f)

    expected_keys = {
        "GROUND_Y", "GRAVITY", "V0_PER_POWER", "FENCE_X", "FENCE_W",
        "FENCE_H", "WIND_MIN", "WIND_MAX", "THROW_ANGLE_DEFAULT", "TURN_SECONDS",
        "WALL_HIT_DMG", "KNIGHT_ZONE", "SHIELD_WALL_COFFIN_HEIGHT", "SHIELD_WALL_EXPIRES_AFTER_ATTACKS", "WIND_TAIL", "WIND_HEAD",
    }

    required_keys = expected_keys | {"ADAPTIVE_LEVEL"}
    missing = required_keys - set(shared)
    assert not missing, f"shared/constants.json is missing keys: {sorted(missing)}"
    extra = set(shared) - required_keys
    assert not extra, f"shared/constants.json has unexpected keys: {sorted(extra)}"

    mismatches = []
    for key in sorted(expected_keys):
        want = parsed[key]
        got = float(shared[key])
        if abs(want - got) > 1e-9:
            mismatches.append(f"  {key}: index.html={want} != constants.json={got}")

    if mismatches:
        print("CONSTANTS DRIFT DETECTED:")
        print("\n".join(mismatches))
        return 1

    shared_adaptive = shared["ADAPTIVE_LEVEL"]
    python_adaptive = parse_python_adaptive(_read(ADAPTIVE_PYTHON))
    javascript_adaptive = parse_javascript_adaptive(_read(ADAPTIVE_JAVASCRIPT))
    assert python_adaptive == shared_adaptive, "adaptive Python constants drift from constants.json"
    assert javascript_adaptive == shared_adaptive, "adaptive JavaScript constants drift from constants.json"

    print("OK: shared/constants.json matches index.html for all",
          len(expected_keys), "constants and adaptive-level tables.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
