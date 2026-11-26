#!/usr/bin/env python3
"""Tests for MCP room lifecycle tools (join_room, leave_room, wait_for_turn), invite URL parsing, and ConnectedRelay reconnect/resume (G1)."""
import asyncio
import json
import sys
import threading
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import mcp_stdio_server as srv  # noqa: E402
from pk_relay import RelayServer, Room  # noqa: E402


class RelayThread:
    def __init__(self, seat_grace_seconds: float = 10.0):
        self.loop = asyncio.new_event_loop()
        self.ready = threading.Event()
        self.relay = None
        self.seat_grace_seconds = seat_grace_seconds
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        if not self.ready.wait(3):
            raise RuntimeError("relay did not start")

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.relay = RelayServer("127.0.0.1", 0, seat_grace_seconds=self.seat_grace_seconds)
        self.loop.run_until_complete(self.relay.start())
        self.ready.set()
        self.loop.run_forever()
        self.loop.run_until_complete(self.relay.close())
        self.loop.close()

    def drop_seat_socket(self, code: str, seat_id: str) -> bool:
        fut = asyncio.run_coroutine_threadsafe(self._drop_async(code, seat_id), self.loop)
        return fut.result(timeout=3)

    async def _drop_async(self, code: str, seat_id: str) -> bool:
        room = self.relay.rooms.get(code)
        if not room:
            return False
        for ws, entry in list(room.clients.items()):
            if entry.get("seat_id") == seat_id:
                await ws.close(code=1011, reason="simulated drop")
                return True
        return False

    def close(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(2)


def wait_for(predicate, message, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError(message)


def tool_json(server, name, arguments=None):
    res = server._call_tool(name, arguments or {})
    return res["isError"], json.loads(res["content"][0]["text"])


class InviteParserTests(unittest.TestCase):
    def test_bare_code(self):
        parsed = srv.parse_invite("abc234")
        self.assertEqual(parsed["code"], "ABC234")
        self.assertIsNone(parsed["seat"])
        self.assertIsNone(parsed["units"])

    def test_full_invite_url_with_seat_and_team(self):
        parsed = srv.parse_invite("https://pk.example.com/index.html?room=ab12cd&seat=white&team=3")
        self.assertEqual(parsed["code"], "AB12CD")
        self.assertEqual(parsed["seat"], "white")
        self.assertEqual(parsed["units"], 3)

    def test_choose_side_invite_url(self):
        parsed = srv.parse_invite("https://pk.example.com/index.html?room=XY789Z&choose=1&team=2")
        self.assertEqual(parsed["code"], "XY789Z")
        self.assertIsNone(parsed["seat"])
        self.assertEqual(parsed["units"], 2)

    def test_local_url_with_relay_param(self):
        parsed = srv.parse_invite("http://localhost:8080/index.html?room=ABC234&relay=ws://localhost:8765&seat=red")
        self.assertEqual(parsed["code"], "ABC234")
        self.assertEqual(parsed["seat"], "red")
        self.assertEqual(parsed["relay"], "ws://localhost:8765/ws")

    def test_invalid_invite_rejected(self):
        with self.assertRaises(srv.ToolError):
            srv.parse_invite("not-a-code")
        with self.assertRaises(srv.ToolError):
            srv.parse_invite("https://pk.example.com/index.html?team=3")


class ReconnectAndRoomToolsTests(unittest.TestCase):
    def setUp(self):
        self.host = RelayThread(seat_grace_seconds=10.0)
        self.url = "ws://127.0.0.1:%d/ws" % self.host.relay.bound_port
        self.servers = []

    def tearDown(self):
        for s in self.servers:
            if s.relay is not None:
                s.relay.close()
        self.host.close()

    def make_room(self, code, scene="church", team_size=1):
        self.host.relay.rooms[code] = Room(code, scene=scene, team_size=team_size)

    def test_default_stdio_server_keeps_exact_seven_tools(self):
        sess = srv.Session(seed=1, seat="white")
        default_srv = srv.McpServer(sess)
        names = [t["name"] for t in default_srv.handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"]["tools"]]
        self.assertEqual(names, srv.TOOL_NAMES)
        self.assertEqual(len(names), 7)

    def test_connected_relay_reconnects_and_resumes_after_socket_drop(self):
        self.make_room("RECN01")
        red_sess = srv.Session(seed=1, clock=lambda: 0.0, turn_seconds=0, human_turn_seconds=0, seat="red")
        white_sess = srv.Session(seed=1, clock=lambda: 0.0, turn_seconds=0, human_turn_seconds=0, seat="white")
        red_srv = srv.McpServer(red_sess)
        white_srv = srv.McpServer(white_sess)
        red = srv.ConnectedRelay(red_sess, self.url, "RECN01", "red", auto_ready=True)
        white = srv.ConnectedRelay(white_sess, self.url, "RECN01", "white", auto_ready=True)
        red_srv.relay = red
        white_srv.relay = white
        self.servers.extend([red_srv, white_srv])
        red.start()
        white.start()

        wait_for(lambda: self.host.relay.rooms["RECN01"].started, "room did not start")
        wait_for(lambda: red.session.scene_id == "church" and white.session.scene_id == "church", "scene not received")
        self.assertTrue(white.seat_token, "white must capture seat_token from room_state")
        original_token = white.seat_token

        # Simulate network drop on white's WebSocket
        dropped = self.host.drop_seat_socket("RECN01", white.seat_id)
        self.assertTrue(dropped, "failed to drop white socket")
        wait_for(lambda: white.reconnect_count >= 1, "white did not reconnect after socket drop", timeout=5.0)
        wait_for(lambda: any(e.get("seat_token") == original_token and e.get("connected") for e in self.host.relay.rooms["RECN01"].sessions.values()),
                 "white did not resume connected state on relay", timeout=5.0)
        self.assertEqual(white.seat_token, original_token)
        self.assertIsNone(white.failure)

        # Match continues normally after reconnect
        err, _ = tool_json(red_srv, "submit_action", {"unit": "red_1", "round": 1, "action": {"type": "throw", "angle": 54, "power": 50}})
        self.assertFalse(err)
        wait_for(lambda: bool(white.received_actions), "resumed white did not receive red's action")
        err, _ = tool_json(red_srv, "end_turn", {"round": 1, "phase": "human"})
        self.assertFalse(err)
        wait_for(lambda: white.session.phase == "agent", "resumed white did not enter agent phase")

    def test_join_wait_play_leave_and_rejoin_second_room(self):
        self.make_room("ROOM01", scene="church", team_size=1)
        self.make_room("ROOM02", scene="school", team_size=1)

        red_srv = srv.McpServer(srv.Session(seed=1, seat="red"), enable_room_tools=True, default_relay_url=self.url, allow_custom_relay=False)
        white_srv = srv.McpServer(srv.Session(seed=1, seat="white"), enable_room_tools=True, default_relay_url=self.url, allow_custom_relay=False)
        self.servers.extend([red_srv, white_srv])

        # Room tools are listed when enabled
        names = [t["name"] for t in red_srv.handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"]["tools"]]
        for extra in ("join_room", "leave_room", "wait_for_turn"):
            self.assertIn(extra, names)

        # Join via bare code and via invite URL (external origin must be ignored when allow_custom_relay=False)
        err, r_join = tool_json(red_srv, "join_room", {"room": "ROOM01", "seat": "red", "units": 1})
        self.assertFalse(err, r_join)
        self.assertEqual(r_join["code"], "ROOM01")

        err, w_join = tool_json(white_srv, "join_room", {"room": "https://evil.invalid/index.html?room=ROOM01&seat=white&team=1&relay=ws://127.0.0.1:1"})
        self.assertFalse(err, w_join)
        self.assertEqual(w_join["code"], "ROOM01")
        self.assertEqual(w_join["seat"], "white")

        wait_for(lambda: self.host.relay.rooms["ROOM01"].started, "ROOM01 did not start")

        # wait_for_turn: red gets immediate your_turn, white gets short waiting
        err, w_wait = tool_json(white_srv, "wait_for_turn", {"timeout_seconds": 0.25})
        self.assertFalse(err, w_wait)
        self.assertEqual(w_wait["status"], "waiting")

        err, r_wait = tool_json(red_srv, "wait_for_turn", {"timeout_seconds": 2.0})
        self.assertFalse(err, r_wait)
        self.assertEqual(r_wait["status"], "your_turn")
        self.assertEqual(r_wait["round"], 1)

        # Start white waiting in a background thread while red throws & ends turn -> white wakes immediately
        white_result = {}
        def wait_white():
            white_result["out"] = tool_json(white_srv, "wait_for_turn", {"timeout_seconds": 4.0})
        t = threading.Thread(target=wait_white)
        t.start()
        time.sleep(0.08)

        err, sub = tool_json(red_srv, "submit_action", {"unit": "red_1", "round": 1, "action": {"type": "throw", "angle": 54, "power": 45}})
        self.assertFalse(err)
        # LIVE-3V3-1: in a room the attack does not end the turn; the result says which end_turn call finishes it (a live agent did not call it and its team stalled)
        self.assertEqual(sub.get("end_turn_args"), {"round": 1, "phase": "human"}, sub)
        self.assertIn("end_turn", sub.get("next", ""))
        err, _ = tool_json(red_srv, "end_turn", {"round": 1, "phase": "human"})
        self.assertFalse(err)
        t.join(timeout=4.0)
        self.assertFalse(t.is_alive(), "white wait_for_turn hung")
        err, w_turn = white_result["out"]
        self.assertFalse(err, w_turn)
        self.assertEqual(w_turn["status"], "your_turn")

        # Leave ROOM01 cleanly and join ROOM02 in the same MCP session (no server restart!)
        err, w_left = tool_json(white_srv, "leave_room")
        self.assertFalse(err, w_left)
        self.assertTrue(w_left["left"])
        err, r_left = tool_json(red_srv, "leave_room")
        self.assertFalse(err, r_left)
        self.assertTrue(r_left["left"])

        err, r2 = tool_json(red_srv, "join_room", {"room": "ROOM02", "seat": "red", "units": 1})
        self.assertFalse(err, r2)
        err, w2 = tool_json(white_srv, "join_room", {"room": "https://pk.example.com/?room=ROOM02&seat=white&team=1"})
        self.assertFalse(err, w2)
        wait_for(lambda: self.host.relay.rooms["ROOM02"].started, "ROOM02 did not start")


if __name__ == "__main__":
    unittest.main(verbosity=2)
