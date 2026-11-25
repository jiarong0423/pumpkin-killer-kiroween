#!/usr/bin/env python3
"""ROOM-FLOW R9, MCP side: a lost AI seat is not a forfeit for an agent either. No sockets."""
import threading
import types
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mcp_stdio_server as mcp_srv  # noqa: E402


def bridge(seat="white", claim=("wizard",)):
    b = mcp_srv.ConnectedRelay.__new__(mcp_srv.ConnectedRelay)
    b.cond = threading.Condition(threading.RLock())
    b.last_seq, b.seat, b.seat_id, b.claim_heroes = 0, seat, seat + "-1", list(claim) if claim else None
    b.relay_owners = {}
    b.started = True
    b.session = types.SimpleNamespace(phase="playing", winner=None, winner_reason=None, seat={"units": [mcp_srv.engine_unit_id("right_0")]})
    return b


def left(seat_id, team, **extra):
    return dict({"type": "seat_left", "seq": 5, "seat_id": seat_id, "team": team, "reason": "disconnect_timeout"}, **extra)


class McpAiSeatTests(unittest.TestCase):
    def test_a_lost_ai_teammate_hands_its_units_to_the_agent(self):
        b = bridge()
        b._receive(left("white-2", "white", ai=True, team_empty=False, owners={"right_0": "white-1", "right_1": "white-1", "left_0": "red-1"}))
        self.assertEqual((b.session.phase, b.session.winner), ("playing", None))
        self.assertEqual(b.session.seat["units"], sorted(mcp_srv.engine_unit_id(u) for u in ("right_0", "right_1")))

    def test_a_lost_ai_opponent_with_a_teammate_left_changes_nothing(self):
        b = bridge()
        before = list(b.session.seat["units"])
        b._receive(left("red-2", "red", ai=True, team_empty=False, owners={"right_0": "white-1", "left_0": "red-1", "left_1": "red-1"}))
        self.assertEqual((b.session.phase, b.session.winner, b.session.seat["units"]), ("playing", None, before))

    def test_a_whole_ai_team_lost_ends_with_no_result(self):
        b = bridge()
        b._receive(left("red-1", "red", ai=True, team_empty=True, owners={}))
        self.assertEqual((b.session.phase, b.session.winner, b.session.winner_reason), ("over", "none", "ai_seat_lost"))

    def test_a_person_whose_units_are_all_down_leaves_without_deciding_the_match(self):
        b = bridge()
        b.relay_owners = {"left_0": "red-1", "left_1": "red-2"}
        b.session.engine = types.SimpleNamespace(units={mcp_srv.engine_unit_id("left_0"): {"alive": False}, mcp_srv.engine_unit_id("left_1"): {"alive": True}})
        b._receive(left("red-1", "red"))
        self.assertEqual((b.session.phase, b.session.winner), ("playing", None))
        b._receive(dict(left("red-2", "red"), seq=6))
        self.assertEqual((b.session.phase, b.session.winner), ("over", "white"))

    def test_a_seat_that_leaves_before_the_start_decides_nothing(self):   # red team A12
        b = bridge()
        b.started = False
        b._receive(left("red-1", "red"))
        self.assertEqual((b.session.phase, b.session.winner), ("playing", None))

    def test_a_lost_person_still_forfeits(self):
        b = bridge()
        b._receive(left("red-1", "red"))
        self.assertEqual((b.session.phase, b.session.winner), ("over", "white"))


if __name__ == "__main__":
    unittest.main()
