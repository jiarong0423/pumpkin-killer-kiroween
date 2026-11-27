#!/usr/bin/env python3
"""The MCP bridge (ConnectedRelay) numbers the throws of a room match like the page does: every throw and ultimate of every seat, never a move, from 1 again in a new match.
No sockets. usage: python3 -B scripts/test_bridge_throw_numbers.py"""
import unittest

import mcp_stdio_server as srv


class ThrowNumbers(unittest.TestCase):
    def test_every_throw_counts_and_the_judged_one_gets_the_page_number(self):
        bridge = object.__new__(srv.ConnectedRelay)
        bridge.room_throws, bridge.seat_id, bridge.seat, bridge.claim_heroes = 0, "white-1", "white", None
        bridge.received_actions, judged = [], []
        bridge.engine_unit = lambda unit: "red_1"
        bridge._judge_action = lambda message, unit_id=None: judged.append(bridge.room_throws)

        class Units(dict):
            def __missing__(self, key):
                return {}

        class Session:
            seats = {"red": {}, "referee": {}}
            engine = type("E", (), {"units": Units()})()

            def call(self, *args):
                return {}
        bridge.session = Session()
        log = [("red-1", "throw"), ("white-1", "throw"), ("red-1", "move"), ("red-1", "ultimate"), ("white-1", "throw"), ("red-1", "throw")]
        for seq, (seat, kind) in enumerate(log, 1):
            if kind == "move":
                continue_after = bridge.room_throws
                try:
                    bridge._apply_action({"seat_id": seat, "kind": kind, "seq": seq, "round": 1, "unit": "left_0"})
                except KeyError:
                    pass
                self.assertEqual(bridge.room_throws, continue_after)
                continue
            bridge._apply_action({"seat_id": seat, "kind": kind, "seq": seq, "round": 1, "unit": "left_0", "angle": 45, "power": 60})
        self.assertEqual(bridge.room_throws, 5)
        self.assertEqual(judged[0], 1)
        self.assertEqual(judged[-1], 5)


if __name__ == "__main__":
    unittest.main()
