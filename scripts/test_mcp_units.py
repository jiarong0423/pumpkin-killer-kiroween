#!/usr/bin/env python3
"""Seeded 1v1 through 3v3 invariants for the MCP engine and seat views."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import mcp_game_server as engine  # noqa: E402
import mcp_stdio_server as server  # noqa: E402

THROW = {"type": "throw", "angle": 54, "power": 60}


def public_unit(unit):
    """Fields both seats are entitled to observe for every unit."""
    return {key: unit[key] for key in (
        "team", "name", "controller", "x", "y", "hp", "max_hp", "alive",
        "weapon", "hero", "statuses", "class",
    )}


def public_view(view):
    return {
        "round": view["round"],
        "phase": view["phase"],
        "wind": view["wind"],
        "winner": view["winner"],
        "central_wall": view["central_wall"],
        "round_hash": view["round_hash"],
        "units": {uid: public_unit(unit) for uid, unit in view["units"].items()},
    }


class McpUnitsPropertyTest(unittest.TestCase):
    def assert_seeded_match(self, units, seed):
        try:
            session = server.Session(seed=seed, units=units, clock=lambda: 0.0,
                                     human_turn_seconds=0, turn_seconds=100)
            red_view = session.call("get_public_state", {}, session.seats["red"])
            white_view = session.call("get_public_state", {}, session.seats["white"])
            self.assertEqual(public_view(red_view), public_view(white_view))
            self.assertEqual(red_view["round_hash"], white_view["round_hash"])

            roster = session.call("get_roster", {}, session.seats["red"])
            self.assertEqual(units, roster["units_per_side"])
            self.assertEqual(["red_%d" % index for index in range(1, units + 1)], roster["teams"]["red"])
            self.assertEqual(["white_%d" % index for index in range(1, units + 1)], roster["teams"]["white"])
            self.assertEqual(roster["teams"]["red"], roster["seat"]["units"])

            for team in ("red", "white"):
                positions = sorted(unit["x"] for unit in session.engine.units.values()
                                   if unit["team"] == team)
                self.assertTrue(all(right - left >= 120 for left, right in zip(positions, positions[1:])),
                                "%s positions are closer than 120 px: %r" % (team, positions))

            # One active unit per side may queue an action. Other units remain frozen.
            red_active = session._active_unit("red")
            self.assertEqual("red_1", red_active)
            if units > 1:
                with self.assertRaisesRegex(server.ToolError, "frozen"):
                    session.call("submit_action", {"unit": "red_2", "action": THROW}, session.seats["red"])
            session.call("submit_action", {"unit": red_active, "action": THROW}, session.seats["red"])
            session.call("end_turn", {"phase": "human"}, session.seats["referee"])
            white_active = session._active_unit("white")
            self.assertEqual("white_1", white_active)
            session.call("submit_action", {"unit": white_active, "action": THROW}, session.seats["white"])
            session.call("end_turn", {"phase": "agent"}, session.seats["referee"])
            self.assertEqual("red_%d" % (2 if units > 1 else 1), session._active_unit("red"))

            # Finish a valid terminal state and ensure dead units never resolve an action.
            dead_units = [uid for uid, unit in session.engine.units.items() if unit["team"] == "white"]
            log_before_terminal = len(session.engine.throw_log)
            for uid in dead_units:
                session.engine.units[uid].update({"alive": False, "hp": 0.0, "pending_throw": None})
            session.call("end_turn", {"phase": "human"}, session.seats["referee"])
            self.assertEqual("red", session.winner)
            self.assertEqual("over", session.phase)
            self.assertTrue(all(record["damage_dealt"] >= 0 for record in session.engine.throw_log))
            self.assertFalse(any(record["unit"] in dead_units
                                 for record in session.engine.throw_log[log_before_terminal:]))

            red_final = session.call("get_public_state", {}, session.seats["red"])
            white_final = session.call("get_public_state", {}, session.seats["white"])
            self.assertEqual(public_view(red_final), public_view(white_final))
            self.assertEqual(red_final["round_hash"], white_final["round_hash"])
        except AssertionError as error:
            self.fail("units=%d seed=%d: %s" % (units, seed, error))

    def test_seeded_match_matrix(self):
        for units in range(1, 4):
            for seed in range(1, 51):
                with self.subTest(units=units, seed=seed):
                    self.assert_seeded_match(units, seed)

    def test_roster_arguments_require_exact_unit_counts(self):
        for units in range(1, 4):
            red = ["skeleton"] * units
            white = ["wizard"] * units
            game = engine.GameState(seed=88, units=units, hero_red=red, hero_white=white)
            self.assertEqual(red, [game.units["red_%d" % index]["hero"] for index in range(1, units + 1)])
            self.assertEqual(white, [game.units["white_%d" % index]["hero"] for index in range(1, units + 1)])
        with self.assertRaisesRegex(ValueError, "units must be 1, 2 or 3"):
            engine.GameState(seed=1, units=4)
        with self.assertRaisesRegex(ValueError, "units must be 1, 2 or 3"):
            server.Session(seed=1, units=4)
        with self.assertRaises(ValueError):
            engine.GameState(seed=1, units=2, hero_red="skeleton")
        with self.assertRaises(ValueError):
            engine.GameState(seed=1, units=3, hero_white=["wizard", "bat"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
