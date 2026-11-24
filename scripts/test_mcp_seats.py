#!/usr/bin/env python3
"""Seat isolation tests for the Pumpkin Killer stdio MCP server."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import mcp_stdio_server as srv  # noqa: E402

BASELINE = os.path.join(HERE, "mcp_referee_baseline_145.json")
THROW = {"type": "throw", "angle": 54, "power": 60}


def make_session(seat="referee"):
    return srv.Session(seed=145, clock=lambda: 0.0, turn_seconds=12, seat=seat)


def play_round(session):
    session.call("submit_action", {"unit": "red_1", "action": THROW})
    session.call("end_turn", {"phase": "human"})
    session.call("submit_action", {"unit": "white_1", "action": {"type": "throw", "angle": 62, "power": 70}})
    session.call("end_turn", {"phase": "agent"})


def normalized(view):
    clone = json.loads(json.dumps(view))
    clone["match_id"] = "<match_id>"
    return json.dumps(clone, ensure_ascii=False, sort_keys=True)


def add_red_path(session):
    throw_id = session.engine.next_throw_id
    session.engine.next_throw_id += 1
    session.engine.throw_log.append({
        "throw_id": throw_id, "round": 1, "team": "red", "unit": "red_1",
        "controller": "human", "angle": 54.0, "power": 60.0, "wind_at_throw": 0.0,
        "landing_x": 1450.0, "landing_y": 600.0, "hit_type": "ground",
        "hit_target": None, "damage_dealt": 0,
        "path": [[600.0, 500.0], [1200.0, 430.0], [1450.0, 600.0]],
    })
    return throw_id


class SeatViewTest(unittest.TestCase):
    def test_own_aim_is_visible_and_enemy_aim_is_hidden(self):
        session = make_session()
        play_round(session)
        red = session.call("get_history", {"limit": 10}, session.seats["red"])["throws"]
        white = session.call("get_history", {"limit": 10}, session.seats["white"])["throws"]
        red_white_throw = next(row for row in red if row["unit"] == "white_1")
        white_own_throw = next(row for row in white if row["unit"] == "white_1")
        self.assertNotIn("angle", red_white_throw)
        self.assertNotIn("power", red_white_throw)
        self.assertEqual(white_own_throw["angle"], 62.0)
        self.assertEqual(white_own_throw["power"], 70.0)

    def test_red_cannot_submit_for_white_and_state_is_unchanged(self):
        session = make_session(seat="red")
        server = srv.McpServer(session)
        before = normalized(session.call("get_public_state", {}))
        result = server._call_tool("submit_action", {"unit": "white_1", "action": THROW})
        self.assertTrue(result["isError"])
        self.assertIn("does not control unit", result["content"][0]["text"])
        self.assertEqual(normalized(session.call("get_public_state", {})), before)

    def test_enemy_defend_move_and_acted_flags_do_not_change_red_view(self):
        before, after = make_session(), make_session()
        first, second = add_red_path(after), add_red_path(after)
        add_red_path(before)
        add_red_path(before)
        before.call("end_turn", {"phase": "human"})
        after.call("end_turn", {"phase": "human"})
        after.active_unit_index["white"] = 1
        after.call("submit_action", {"unit": "white_2", "action": {"type": "defend", "path1": first, "path2": second}}, after.seats["white"])
        self.assertEqual(normalized(before.call("get_public_state", {}, before.seats["red"])),
                         normalized(after.call("get_public_state", {}, after.seats["red"])))

        before, after = make_session(), make_session()
        before.engine.units["white_1"]["x"] = after.engine.units["white_1"]["x"] = 1280.0   # the white zone edge: the forward limit is 1280 since 2026-11-18 (it was 1240): a forward move cannot change x there
        before.call("end_turn", {"phase": "human"})
        after.call("end_turn", {"phase": "human"})
        after.call("submit_action", {"unit": "white_1", "action": {"type": "move", "direction": "forward"}}, after.seats["white"])
        self.assertEqual(normalized(before.call("get_public_state", {}, before.seats["red"])),
                         normalized(after.call("get_public_state", {}, after.seats["red"])))

        before, after = make_session(), make_session()
        before.call("end_turn", {"phase": "human"})
        after.call("end_turn", {"phase": "human"})
        after.call("submit_action", {"unit": "white_1", "action": THROW}, after.seats["white"])
        self.assertEqual(normalized(before.call("get_public_state", {}, before.seats["red"])),
                         normalized(after.call("get_public_state", {}, after.seats["red"])))

    def test_notes_are_per_seat(self):
        session = make_session()
        session.call("set_notes", {"text": "red lesson"}, session.seats["red"])
        self.assertEqual(session.call("get_notes", {}, session.seats["red"])["notes"], "red lesson")
        self.assertEqual(session.call("get_notes", {}, session.seats["white"])["notes"], "")

    def test_spectator_cannot_write(self):
        server = srv.McpServer(make_session(seat="spectator"))
        for name, args in (
            ("submit_action", {"unit": "red_1", "action": THROW}),
            ("end_turn", {"phase": "human"}),
            ("set_notes", {"text": "nope"}),
        ):
            result = server._call_tool(name, args)
            self.assertTrue(result["isError"], name)
            self.assertIn("read-only", result["content"][0]["text"])

    def test_referee_matches_the_pre_seat_baseline(self):
        session = make_session()
        play_round(session)
        actual = {
            "state": session.call("get_public_state", {}),
            "history": session.call("get_history", {"limit": 10}),
            "notes": session.call("get_notes", {}),
        }
        actual["state"]["match_id"] = "<match_id>"
        # The saved K1 fixture predates public skill/energy and Shield Wall metadata.
        for field in ("ultimate_energy", "skills_remaining", "knight_walls"):
            actual["state"].pop(field, None)
        with open(BASELINE, "r", encoding="utf-8") as handle:
            expected = json.load(handle)
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
