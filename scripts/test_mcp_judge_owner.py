#!/usr/bin/env python3
"""LIVE-3V3-2 (2026-11-26, local copy of the live 3v3 run): an MCP agent that holds one unit of a mixed team (a browser player and a computer seat hold
the others) judged an enemy throw that landed on a TEAMMATE's unit and named that unit in its judge. The relay refused it (unit_not_yours), the
bridge took the refusal as a lasting failure and the agent was out of the match from round 1.

Rule (relay `_judge`, page `relayOwnsUnit`): every unit owner judges its own unit only. A throw that lands on a teammate's unit is judged by that
teammate; the agent still applies the hit to its own copy of the match (the teammate's judge then confirms it). Socket-free.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import mcp_stdio_server as srv  # noqa: E402


def drained(q):
    out = []
    while not q.empty():
        out.append(q.get_nowait())
    return out


class JudgeOwnUnitOnly(unittest.TestCase):
    def setUp(self):
        self.sess = srv.Session(seed=1, seat="white")
        self.bridge = srv.ConnectedRelay(self.sess, "ws://127.0.0.1:1/ws", "ABCDEF", "white", claim_heroes=["knight"])
        self.bridge.seat_id = "white-2"
        owners = {"left_0": "red-1", "left_1": "red-2", "left_2": "red-3", "right_0": "white-1", "right_1": "white-2", "right_2": "white-3"}
        self.bridge._receive_locked({"type": "start", "seed": 77, "scene": "graveyard", "team_size": 3, "round": 1, "phase": "red", "seq": 1,
                                     "heroes": {"left": ["skeleton", "wizard", "hag"], "right": ["skeleton", "knight", "reaper"]}, "owners": owners})
        self.assertTrue(self.bridge.started)
        drained(self.bridge.outgoing)
        self._real = srv.simulate_flight

    def tearDown(self):
        srv.simulate_flight = self._real

    def throw_landing_on(self, engine_unit):
        target = self.sess.engine.units[engine_unit]
        x, y = float(target["x"]), float(target["y"]) - 60
        srv.simulate_flight = lambda spec: {"points": [{"x": 700.0, "y": 600.0}, {"x": x, "y": y}], "landingX": x, "landingY": y}
        self.bridge._receive_locked({"type": "action", "round": 1, "phase": "red", "unit": "left_0", "kind": "throw", "angle": 50, "power": 70,
                                     "start": {"x": 310, "y": 750}, "claimed_landing": {"x": x, "y": y}, "dirX": 1, "seat_id": "red-1", "seq": 2})
        return [m for m in drained(self.bridge.outgoing) if m.get("type") == "judge"]

    def test_a_hit_on_a_teammates_unit_is_not_judged_here(self):
        judges = self.throw_landing_on("white_1")   # right_0, held by the browser player white-1
        self.assertFalse(any(j.get("unit") == "right_0" for j in judges), judges)
        self.assertFalse(any(j.get("hit") for j in judges), judges)
        self.assertIsNone(self.bridge.failure)

    def test_a_hit_on_its_own_unit_is_judged_with_that_unit(self):
        judges = self.throw_landing_on("white_2")   # right_1, held by this agent
        self.assertEqual([(j.get("hit"), j.get("unit")) for j in judges], [(True, "right_1")], judges)


if __name__ == "__main__":
    unittest.main()
