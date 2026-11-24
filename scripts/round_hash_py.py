#!/usr/bin/env python3
"""Canonical public-round serialization and eight-character SHA-256 sync hash."""
import hashlib
import json
import math
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_GOLDEN = os.path.join(_ROOT, "shared", "round_hash_golden.json")


def _finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise TypeError("%s must be finite" % name)
    return float(value)


def _round_half_up(value, decimals):
    return math.floor(_finite(value, "number") * (10 ** decimals) + 0.5) / (10 ** decimals)


def _fixed(value, decimals):
    return ("%%.%df" % decimals) % _round_half_up(value, decimals)


def _units(state):
    units = state.get("units")
    if isinstance(units, list):
        return list(units)
    if isinstance(units, dict):
        return [dict(unit, id=unit.get("id", unit_id)) for unit_id, unit in units.items()]
    raise TypeError("state.units must be an array or object")


_STATUS_WORD = re.compile(r"^(?:(?:bleed|poison|burn|weak|slow):[1-9][0-9]*|stun)$")


def _statuses(statuses):
    if statuses is None:
        return ""
    if (not isinstance(statuses, list) or
            any(not isinstance(status, str) or not _STATUS_WORD.fullmatch(status) for status in statuses)):
        raise TypeError("statuses must be canonical status words")
    return "|".join(sorted(statuses))


MAX_TEAM_SIZE = 3
_UNIT_ID = re.compile(r"^[A-Za-z0-9_.:-]+$")   # ASCII only and nothing below ',': sorting by id equals sorting by row text in every runtime
_WORLD_ID = re.compile(r"^(?:(left|right)(?:_([0-2]))?|(red|white)_([1-3]))$")


def world_unit_id(unit_id):
    """Team-battle ids on the wire and in the hash are left_0..left_2 and right_0..right_2.
    The MCP engine names the same units red_1..red_3 and white_1..white_3 (one-based)."""
    match = _WORLD_ID.match(unit_id) if isinstance(unit_id, str) else None
    if not match:
        raise TypeError("unit id has no world form: %r" % (unit_id,))
    if match.group(1):
        return match.group(1) if match.group(2) is None else "%s_%s" % (match.group(1), match.group(2))
    return "%s_%d" % ("left" if match.group(3) == "red" else "right", int(match.group(4)) - 1)


_ENGINE_FROM_WORLD = re.compile(r"^(left|right)_([0-2])$")


def engine_unit_id(unit_id):
    """The inverse of world_unit_id for team matches: left_0..left_2 and right_0..right_2 name the MCP engine's red_1..red_3 and white_1..white_3.
    An id that is already an engine id comes back unchanged; anything else raises TypeError."""
    match = _ENGINE_FROM_WORLD.match(unit_id) if isinstance(unit_id, str) else None
    if match:
        return "%s_%d" % ("red" if match.group(1) == "left" else "white", int(match.group(2)) + 1)
    if isinstance(unit_id, str) and re.match(r"^(red|white)_[1-3]$", unit_id):
        return unit_id
    raise TypeError("unit id has no engine form: %r" % (unit_id,))


def unit_ids(team_size):
    if isinstance(team_size, bool) or not isinstance(team_size, int) or not 1 <= team_size <= MAX_TEAM_SIZE:
        raise ValueError("teamSize must be 1..%d" % MAX_TEAM_SIZE)
    return ["left_%d" % i for i in range(team_size)] + ["right_%d" % i for i in range(team_size)]


def _check_team_size(state, ids):
    size = state.get("teamSize", state.get("team_size"))
    if size is None:
        return
    expected = unit_ids(size)
    if len(ids) != len(expected):
        raise TypeError("state must list every unit of both teams: expected %d, got %d" % (len(expected), len(ids)))
    if size > 1 and ids != expected:
        raise TypeError("team units must be " + ",".join(expected))


def canonical_text(state):
    if not isinstance(state, dict):
        raise TypeError("state must be an object")
    rows = []
    for unit in _units(state):
        unit_id = unit.get("id")
        if not isinstance(unit_id, str) or not _UNIT_ID.match(unit_id):
            raise TypeError("unit id is invalid")
        if not isinstance(unit.get("alive"), bool):
            raise TypeError("unit.alive must be boolean")
        rows.append((unit_id, "%s,%s,%s,%s,%s,%s" % (
            unit_id, _fixed(unit.get("x"), 0), _fixed(unit.get("y"), 0), _fixed(unit.get("hp"), 1),
            "true" if unit["alive"] else "false", _statuses(unit.get("statuses")))))
    rows.sort(key=lambda row: row[0])
    ids = [row[0] for row in rows]
    for index in range(1, len(ids)):
        if ids[index] == ids[index - 1]:
            raise TypeError("duplicate unit id: " + ids[index])
    _check_team_size(state, ids)
    wall_hp = state.get("wallHp", state.get("wall_hp"))
    lines = [row[1] for row in rows]
    lines.extend(("wall_hp," + _fixed(wall_hp, 1), "round," + _fixed(state.get("round"), 0),
                  "phase," + str(state.get("phase")), "seed," + str(state.get("seed"))))
    return "\n".join(lines)


def hash_state(state):
    return hashlib.sha256(canonical_text(state).encode("utf-8")).hexdigest()[:8]


def _golden_states():
    states = []
    status_sets = ([], ["burn:3"], ["weak:2", "bleed:2"], ["stun"], ["poison:2", "slow:1"])
    for index in range(20):
        states.append({
            "units": [
                {"id": "white_2", "x": 1499.51 - index * 3.25, "y": 860.49, "hp": 120 - index * 1.1,
                 "alive": index != 7, "statuses": status_sets[index % len(status_sets)]},
                {"id": "red_1", "x": 220.49 + index * 2.75, "y": 859.51, "hp": 90 - index * 0.6,
                 "alive": True, "statuses": list(reversed(status_sets[(index + 2) % len(status_sets)]))},
            ],
            "wallHp": max(0, 100 - index * 8), "round": index + 1,
            "phase": ("red", "white")[index % 2], "seed": 90125 + index,
        })
    return states


def _team_golden_states():
    """Team-battle vectors (2026-11-17): units of BOTH teams, listed in a deliberately shuffled order,
    dead units kept in the list, phase "round_end" for team rooms."""
    status_sets = ([], ["burn:3"], ["weak:2", "bleed:2"], ["stun"], ["poison:2", "slow:1"])
    states = []
    for size in (1, 2, 3):
        for variant in range(4):
            units = []
            for side, base_x, step in (("left", 252.4, 120.0), ("right", 1656.5, -120.0)):
                for index in range(size):
                    serial = variant * 7 + index * 2 + (0 if side == "left" else 1)
                    units.append({
                        "id": "%s_%d" % (side, index),
                        "x": base_x + step * index - variant * 3.3 + (0.49 if index % 2 else 0.0),
                        "y": 860.0 + index * 14.0 - (0.5 if variant == 2 else 0.0),
                        "hp": round(120.0 - serial * 4.7, 1) if not (variant == 3 and index == size - 1) else 0.0,
                        "alive": not (variant == 3 and index == size - 1),
                        "statuses": list(reversed(status_sets[serial % len(status_sets)])),
                    })
            units.reverse() if variant % 2 else units.insert(0, units.pop())
            states.append({"teamSize": size, "units": units, "wallHp": 100 - variant * 17.5,
                           "round": 3 + variant, "phase": "round_end", "seed": 1234567 + size * 11 + variant})
    states.append({"teamSize": 1, "units": [
        {"id": "right", "x": 1500.4, "y": 860, "hp": 77.7, "alive": True, "statuses": ["bleed:2"]},
        {"id": "left", "x": 220.6, "y": 860, "hp": 66.0, "alive": True, "statuses": []}],
        "wallHp": 100, "round": 2, "phase": "throws:left:54:50|right:60:48", "seed": 90125})
    return states


def generate_golden():
    all_states = [("state-%02d" % index, state) for index, state in enumerate(_golden_states())]
    all_states += [("team-%d-%d" % (state["teamSize"], index), state)
                   for index, state in enumerate(_team_golden_states())]
    cases = [{"name": name, "state": state, "canonical": canonical_text(state), "hash": hash_state(state)}
             for name, state in all_states]
    with open(_GOLDEN, "w", encoding="utf-8") as output:
        json.dump({"version": 1, "cases": cases}, output, indent=2, sort_keys=True)
        output.write("\n")
    print("wrote %d round-hash golden cases to %s" % (len(cases), _GOLDEN))


def _main():
    if len(sys.argv) == 2 and sys.argv[1] == "--generate":
        generate_golden()
        return
    for line in sys.stdin:
        state = json.loads(line)
        sys.stdout.write(json.dumps({"canonical": canonical_text(state), "hash": hash_state(state)}, separators=(",", ":")) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    _main()
