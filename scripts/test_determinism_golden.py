#!/usr/bin/env python3
"""Verify portable deterministic match values against shared golden vectors."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import determinism_py as determinism  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

FUNCTIONS = {
    "wind": lambda value: determinism.wind(value["seed"], value["round"]),
    "startX": lambda value: determinism.start_x(value["seed"], value["side"], value["slot"]),
    "moveDie": lambda value: determinism.move_die(value["seed"], value["round"], value["side"]),
    "supplyDrop": lambda value: determinism.supply_drop(value["seed"], value["round"]),
    "bounceCount": lambda value: determinism.bounce_count(value["seed"], value["round"], value["throwId"]),
    "nunStunPick": lambda value: determinism.nun_stun_pick(value["seed"], value["round"], value["throwId"], value["n"]),
    "sideDraw": lambda value: determinism.side_draw(value["seed"]),
    "coinToss": lambda value: determinism.coin_toss(value["seed"]),
}


def main():
    golden = json.loads((ROOT / "shared" / "determinism_golden.json").read_text(encoding="utf-8"))
    assert golden["version"] == 1
    count = 0
    for name, function in FUNCTIONS.items():
        vectors = golden["vectors"][name]
        assert len(vectors) >= 40, "%s needs at least 40 vectors" % name
        for vector in vectors:
            assert function(vector["input"]) == vector["output"], (name, vector)
            count += 1

    for seed in range(10000):
        round_number = (seed % 99) + 1
        wind = determinism.wind(seed, round_number)
        assert -4 <= wind <= 4
        assert abs(wind * 10 - round(wind * 10)) < 1e-9

        slot = seed % 8
        left = determinism.start_x(seed, 0, slot)
        right = determinism.start_x(seed, 1, slot)
        assert 220 <= left <= 620 and left % 36 == 0
        assert 1280 <= right <= 1680 and right % 36 == 0
        assert left < right

        die = determinism.move_die(seed, round_number, seed & 1)
        assert 1 <= die <= 6
        drop = determinism.supply_drop(seed, round_number)
        assert drop["side"] in (0, 1) and drop["item"] in (0, 1)
        assert -120 <= drop["offset"] <= 120 and isinstance(drop["offset"], int)
        bounces = determinism.bounce_count(seed, round_number, seed)
        assert 1 <= bounces <= 6
        target_count = (seed % 17) + 1
        target = determinism.nun_stun_pick(seed, round_number, seed, target_count)
        assert 0 <= target < target_count
        assert determinism.side_draw(seed) in (0, 1)
        assert determinism.coin_toss(seed) in (0, 1)

    print("test_determinism_golden.py: %d golden vectors passed" % count)
    print("test_determinism_golden.py: 10000 seed property cases passed")


if __name__ == "__main__":
    main()
