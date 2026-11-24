#!/usr/bin/env python3
"""Connected MCP peers share deterministic weather and report relay hash drift."""
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
    deadline = time.monotonic() + 10   # was 3 s: failed once in a full-suite run while the machine load average was above 20 (2026-11-19); passes alone 5 of 5 and in the next full run
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError(message)


class ConnectedWeatherTest(unittest.TestCase):
    def setUp(self):
        self.host = RelayThread()
        self.code = "WEATHR"
        self.host.relay.rooms[self.code] = Room(self.code, scene="belltower")
        self.url = "ws://127.0.0.1:%d/ws" % self.host.relay.bound_port
        self.bridges = []

    def tearDown(self):
        for bridge in self.bridges:
            bridge.close()
        self.host.close()

    def peer(self, seat):
        session = srv.Session(seed=1, clock=lambda: 0.0, turn_seconds=12,
                              human_turn_seconds=0, seat=seat)
        server = srv.McpServer(session)
        bridge = srv.ConnectedRelay(session, self.url, self.code, seat, auto_ready=True)
        server.relay = bridge
        bridge.start()
        self.bridges.append(bridge)
        return server, bridge

    def pair(self):
        red_server, red = self.peer("red")
        white_server, white = self.peer("white")
        wait_for(lambda: self.host.relay.rooms[self.code].started, "room did not start")
        wait_for(lambda: red.session.engine.seed == white.session.engine.seed,
                 "peers did not adopt the relay seed")
        self.assertEqual(red.session.scene_id, "belltower")
        self.assertEqual(white.session.scene_id, "belltower")
        return red_server, red, white_server, white

    @staticmethod
    def call(server, tool, arguments):
        result = server._call_tool(tool, arguments)
        assert not result["isError"], result

    def report_round(self, red_server, white_server, red, white, round_number):
        # A round report is emitted after local resolution. Advance both seeded
        # local replicas as the relay log would, without adding combat outcomes.
        for bridge in (red, white):
            bridge.session.engine.round_num = round_number
            bridge.session.set_relay_phase("red" if round_number % 2 else "white")
        red_state = red_server.session.public_state()
        white_state = white_server.session.public_state()
        self.assertEqual(red_state["weather"], white_state["weather"])
        self.assertEqual(red_state["weather"]["id"],
                         srv.for_round(red.session.engine.seed, round_number, "bell_tower")["id"])
        self.assertEqual(set(red_state["weather"]), {"id", "label", "round", "active"})
        self.assertTrue(red_state["weather"]["active"])
        self.assertEqual(red_state["weather"]["round"], round_number)
        red.send_round_hash(round_number)
        white.send_round_hash(round_number)
        wait_for(lambda: len(self.host.relay.rooms[self.code].round_hashes.get(round_number, {})) == 2,
                 "both hashes were not sent")
        self.assertEqual(red.local_hashes[round_number], white.local_hashes[round_number])
        self.assertEqual(set(self.host.relay.rooms[self.code].round_hashes[round_number].values()),
                         {red.local_hashes[round_number]})

    def test_weather_hashes_and_forced_mismatch(self):
        red_server, red, white_server, white = self.pair()
        for round_number in range(1, 4):
            self.report_round(red_server, white_server, red, white, round_number)
        red.outgoing.put({"type": "round_hash", "round": 3, "hash": "00000000"})
        wait_for(lambda: red.session.sync and red.session.sync["status"] == "out_of_sync",
                 "relay did not broadcast forced hash mismatch")
        state = red_server.session.public_state()
        self.assertEqual(state["sync"], {"status": "out_of_sync", "round": 3})


if __name__ == "__main__":
    unittest.main(verbosity=2)
