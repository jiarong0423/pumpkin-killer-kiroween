#!/usr/bin/env python3
"""Local-socket coverage for MCP relay connections."""
import asyncio
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
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.ready = threading.Event()
        self.relay = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        if not self.ready.wait(2):
            raise RuntimeError("relay did not start")

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.relay = RelayServer("127.0.0.1", 0)
        self.loop.run_until_complete(self.relay.start())
        self.ready.set()
        self.loop.run_forever()
        self.loop.run_until_complete(self.relay.close())
        self.loop.close()

    def close(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(2)


def wait_for(predicate, message):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError(message)


class McpConnectTest(unittest.TestCase):
    def setUp(self):
        self.host = RelayThread()
        self.code = "TEST42"
        self.host.relay.rooms[self.code] = Room(self.code, scene="church")
        self.url = "ws://127.0.0.1:%d/ws" % self.host.relay.bound_port
        self.bridges = []

    def tearDown(self):
        for bridge in self.bridges:
            bridge.close()
        self.host.close()

    def peer(self, seat, *, auto_ready=True):
        session = srv.Session(seed=1, clock=lambda: 0.0, turn_seconds=12,
                              human_turn_seconds=0, seat=seat)
        server = srv.McpServer(session)
        bridge = srv.ConnectedRelay(session, self.url, self.code, seat, auto_ready=auto_ready)
        server.relay = bridge
        bridge.start()
        self.bridges.append(bridge)
        return server, bridge

    def pair(self):
        red_server, red = self.peer("red")
        white_server, white = self.peer("white")
        wait_for(lambda: self.host.relay.rooms[self.code].started, "room did not start")
        wait_for(lambda: red.session.scene_id == "church" and white.session.scene_id == "church",
                 "peers did not receive the scene")
        wait_for(lambda: red.session.engine.seed == white.session.engine.seed,
                 "peers did not adopt the relay seed")
        self.assertGreaterEqual(red.session.engine.seed, 1)
        self.assertLessEqual(red.session.engine.seed, (1 << 31) - 1)
        self.assertEqual(red.session.scene_id, "church")
        self.assertEqual(white.session.scene_id, "church")
        return red_server, red, white_server, white

    def test_default_bridge_requires_an_explicit_ready_request(self):
        _, red = self.peer("red", auto_ready=False)
        _, white = self.peer("white", auto_ready=False)
        wait_for(lambda: len(self.host.relay.rooms[self.code].clients) == 2,
                 "both peers did not join")
        self.assertFalse(self.host.relay.rooms[self.code].started)
        self.assertFalse(red.ready_sent)
        self.assertFalse(white.ready_sent)
        red.request_ready()
        white.request_ready()
        wait_for(lambda: self.host.relay.rooms[self.code].started,
                 "explicitly ready peers did not start")

    def test_action_arrives_in_order_is_judged_and_uses_flight_py(self):
        red_server, red, _, white = self.pair()
        response = red_server._call_tool("submit_action", {"unit": "red_1", "round": 1,
                                                             "action": {"type": "throw", "angle": 54, "power": 55}})
        self.assertFalse(response["isError"])
        wait_for(lambda: bool(white.received_actions), "white did not receive the action")
        wait_for(lambda: not red.unacked and not red.outbound, "judge did not acknowledge the action")
        sent = red.last_sent_action
        self.assertIsNotNone(sent)
        flight = srv.simulate_flight({"startX": sent["start"]["x"], "startY": sent["start"]["y"],
                                      "dirX": sent["dirX"], "angleDeg": sent["angle"],
                                      "power": sent["power"], "wind": red.effective_wind()})
        self.assertEqual(sent["claimed_landing"], {"x": flight["landingX"], "y": flight["landingY"]})
        self.assertGreater(white.received_actions[0], 0)

    def test_changed_claimed_landing_marks_target_out_of_sync(self):
        _, red, _, white = self.pair()
        unit = red.session.engine.units["red_1"]
        red.outgoing.put({"type": "action", "round": 1, "phase": "red", "unit": "red_1", "kind": "throw",
                          "angle": 54, "power": 55, "dirX": unit["facing"],
                          "start": {"x": unit["x"] + srv.RELEASE_DX * unit["facing"], "y": unit["y"] - srv.RELEASE_DY},
                          "claimed_landing": {"x": 0, "y": 0}})
        wait_for(lambda: white.session.sync["status"] == "out_of_sync", "mismatch was not reported")
        self.assertEqual(white.session.sync["round"], 1)

    def test_round_hashes_agree_and_replayed_end_turn_is_dropped(self):
        red_server, red, white_server, white = self.pair()
        self.assertFalse(red_server._call_tool("submit_action", {"unit": "red_1", "round": 1,
                                                                     "action": {"type": "throw", "angle": 54, "power": 25}})["isError"])
        self.assertFalse(red_server._call_tool("end_turn", {"round": 1, "phase": "human"})["isError"])
        wait_for(lambda: white.session.phase == "agent", "white did not enter its phase")
        self.assertFalse(white_server._call_tool("submit_action", {"unit": "white_1", "round": 1,
                                                                       "action": {"type": "throw", "angle": 54, "power": 25}})["isError"])
        self.assertFalse(white_server._call_tool("end_turn", {"round": 1, "phase": "agent"})["isError"])
        wait_for(lambda: 1 in self.host.relay.rooms[self.code].round_hashes, "hashes were not sent")
        wait_for(lambda: len(self.host.relay.rooms[self.code].round_hashes[1]) == 2, "both hashes were not sent")
        self.assertEqual(len(set(self.host.relay.rooms[self.code].round_hashes[1].values())), 1)
        self.assertEqual(red.session.sync["status"], "ok")
        self.assertEqual(white.session.sync["status"], "ok")
        red.outgoing.put({"type": "end_turn", "round": 1, "phase": "red"})
        wait_for(lambda: red.failure == "stale_or_out_of_turn", "replayed end turn was not dropped")

    def test_wrong_code_is_rejected(self):
        session = srv.Session(seed=1, seat="red")
        bridge = srv.ConnectedRelay(session, self.url, "BAD999", "red")
        bridge.start()
        self.bridges.append(bridge)
        wait_for(lambda: bridge.failure == "unknown_code", "wrong code was not rejected")


if __name__ == "__main__":
    unittest.main(verbosity=2)
