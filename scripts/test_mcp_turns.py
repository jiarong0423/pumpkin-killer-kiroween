#!/usr/bin/env python3
"""Turn safety, resolution order, path disclosure, and human timer tests."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import mcp_game_server as engine  # noqa: E402
import mcp_stdio_server as srv  # noqa: E402

THROW = {"type": "throw", "angle": 54, "power": 60}


class FakeClock:
    def __init__(self):
        self.value = 100.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


def normalized(value):
    return json.dumps(value, sort_keys=True)


def lethal_duel(game):
    game.wind = 0.0   # fixed: the duel is about turn order, not the wind (wind x1.5 on 2026-11-15 changed the seed-73 landing)
    for unit in game.units.values():
        unit["alive"] = False
        unit["hp"] = 0
    red = game.units["red_3"]
    white = game.units["white_1"]
    red.update({"alive": True, "hp": 20, "x": 1200.0,
                "pending_throw": {"angle": 25.0, "power": 30.0}})
    white.update({"alive": True, "hp": 20, "x": 1400.0,
                  "pending_throw": {"angle": 25.0, "power": 30.0}})


def fitted_gravity_from_public_points(points):
    """Fit y = a*t² + b*t + c using the public point order as fixed sample intervals."""
    times = [index * srv.PATH_STEP * srv.STEP_DT for index in range(len(points))]
    rows = [[sum(t ** (row + column) for t in times) for column in range(3)]
            + [sum(point[1] * t ** row for point, t in zip(points, times))]
            for row in range(3)]
    for column in range(3):
        pivot = max(range(column, 3), key=lambda row: abs(rows[row][column]))
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        for index in range(column, 4):
            rows[column][index] /= divisor
        for row in range(3):
            if row == column:
                continue
            factor = rows[row][column]
            for index in range(column, 4):
                rows[row][index] -= factor * rows[column][index]
    return 2.0 * rows[2][3]


class TurnSafetyTest(unittest.TestCase):
    def test_non_referee_end_turn_needs_round_and_phase_without_state_change(self):
        session = srv.Session(seed=10, clock=lambda: 0.0, seat="red")
        before = normalized(session.call("get_public_state", {}))
        with self.assertRaisesRegex(srv.ToolError, "requires round"):
            session.call("end_turn", {"phase": "human"})
        self.assertEqual(normalized(session.call("get_public_state", {})), before)
        with self.assertRaisesRegex(srv.ToolError, "requires phase"):
            session.call("end_turn", {"round": 1})
        self.assertEqual(normalized(session.call("get_public_state", {})), before)
        session.call("end_turn", {"round": 1, "phase": "human"})
        after = normalized(session.call("get_public_state", {}))
        with self.assertRaisesRegex(srv.ToolError, "does not control the agent phase"):
            session.call("end_turn", {"round": 1, "phase": "human"})
        self.assertEqual(normalized(session.call("get_public_state", {})), after)

    def test_exact_submit_retry_returns_receipt_without_changing_state(self):
        session = srv.Session(seed=11, clock=lambda: 0.0, seat="red")
        args = {"unit": "red_1", "action": THROW, "round": 1}
        first = session.call("submit_action", args)
        before_retry = normalized(session.call("get_public_state", {}))
        retry = session.call("submit_action", args)
        self.assertEqual(retry, dict(first, duplicate=True))
        self.assertEqual(normalized(session.call("get_public_state", {})), before_retry)
        with self.assertRaisesRegex(srv.ToolError, "already submitted"):
            session.call("submit_action", {"unit": "red_1", "round": 1,
                                              "action": {"type": "throw", "angle": 55, "power": 60}})

    def test_first_team_is_fixed_and_round_two_resolves_red_first_again(self):   # owner 2026-11-17: no alternation, nobody attacks twice in a row
        round_one = engine.GameState(seed=73, units=3)
        lethal_duel(round_one)
        result_one = round_one.resolve_round()
        self.assertEqual([result["unit_id"] for result in result_one["results"]], ["red_3"])
        self.assertFalse(round_one.units["white_1"]["alive"])

        round_two = engine.GameState(seed=73, units=3)
        lethal_duel(round_two)
        round_two.round_num = 2
        result_two = round_two.resolve_round()
        self.assertEqual([result["unit_id"] for result in result_two["results"]], ["red_3"])
        self.assertFalse(round_two.units["white_1"]["alive"])
        self.assertEqual([engine.first_team_of_round(r) for r in range(1, 7)], ["red"] * 6)

    def test_enemy_paths_are_coarse_in_history_and_public_state(self):
        session = srv.Session(seed=456, clock=lambda: 0.0)
        session.call("submit_action", {"unit": "red_1", "action": THROW})
        session.call("end_turn", {"phase": "human"})
        session.call("submit_action", {"unit": "white_1",
                                        "action": {"type": "throw", "angle": 62, "power": 70}})
        session.call("end_turn", {"phase": "agent"})
        history = session.call("get_history", {"limit": 10}, session.seats["red"])["throws"]
        enemy = next(row for row in history if row["unit"] == "white_1")
        own = next(row for row in history if row["unit"] == "red_1")
        self.assertLessEqual(len(enemy["path"]), srv.COARSE_PATH_POINTS)
        self.assertTrue(all(x % srv.COARSE_PATH_GRID == 0 and y % srv.COARSE_PATH_GRID == 0
                            for x, y in enemy["path"]))
        self.assertGreater(len(own["path"]), len(enemy["path"]))
        public_enemy = next(row for row in session.call("get_public_state", {}, session.seats["red"])["recent_throws"]
                            if row["unit"] == "white_1")
        self.assertEqual(public_enemy["path"], enemy["path"])
        estimated = fitted_gravity_from_public_points(enemy["path"])
        self.assertGreater(abs(estimated - srv.GRAVITY) / srv.GRAVITY, 0.05)

    def test_human_timer_expires_and_zero_disables_it(self):
        clock = FakeClock()
        session = srv.Session(seed=12, clock=clock, human_turn_seconds=12)
        clock.advance(12)
        state = session.call("get_public_state", {})
        self.assertEqual(state["phase"], "agent")
        self.assertEqual(state["last_timeout"]["idle_units"], ["red_1"])

        off_clock = FakeClock()
        disabled = srv.Session(seed=12, clock=off_clock, human_turn_seconds=0)
        off_clock.advance(999)
        self.assertEqual(disabled.call("get_public_state", {})["phase"], "human")


if __name__ == "__main__":
    unittest.main(verbosity=2)
