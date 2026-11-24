#!/usr/bin/env python3
"""T4 tests: partial-unit MCP claim (1..units), teammate action sync, and round_hash parity."""
import asyncio
import json
import os
import sys
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import mcp_stdio_server as mcp_srv
from pk_relay import RelayServer
import websockets


def _call_tool(server: mcp_srv.McpServer, name: str, args: dict):
    res = server._call_tool(name, args)
    payload = json.loads(res["content"][0]["text"])
    return res["isError"], payload


class McpClaimTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.new_event_loop()
        self.relay = RelayServer(host="127.0.0.1", port=0)
        ready = threading.Event()
        self.port = 0

        def run_relay():
            asyncio.set_event_loop(self.loop)
            async def start():
                await self.relay.start()
                self.port = self.relay._server.sockets[0].getsockname()[1]
                ready.set()
                await asyncio.Future()
            try:
                self.loop.run_until_complete(start())
            except asyncio.CancelledError:
                pass

        self.thread = threading.Thread(target=run_relay, daemon=True)
        self.thread.start()
        assert ready.wait(5.0), "relay did not start"
        self.url = f"ws://127.0.0.1:{self.port}/ws"

    def tearDown(self) -> None:
        async def stop():
            await self.relay.stop()
            for task in asyncio.all_tasks(self.loop):
                if task is not asyncio.current_task():
                    task.cancel()
        try:
            fut = asyncio.run_coroutine_threadsafe(stop(), self.loop)
            fut.result(timeout=3.0)
        except Exception:
            pass
        self.thread.join(timeout=2.0)

    def test_t4_claim_validation_and_3v3_partial_ownership_and_parity(self) -> None:
        # 1. Create a 3v3 room on the relay (host spectator or red1 MCP):
        #    - Red seat 1 (MCP):   claims 2 units ["skeleton", "wizard"] via claim=2
        #    - Red seat 2 (MCP):   claims 1 unit  ["bat"] via claim=1
        #    - White seat 1 (MCP): claims 3 units ["knight", "reaper", "hag"] (whole team default)
        code_box = {}

        async def create_room_only():
            ws = await websockets.connect(self.url)
            await ws.send(json.dumps({
                "type": "create_room", "seat": "spectator", "scene": "graveyard",
                "team_size": 3, "client_version": "test-host",
            }))
            while True:
                msg = json.loads(await asyncio.wait_for(ws.recv(), 5))
                if msg.get("type") == "room_state" and msg.get("code"):
                    code_box["code"] = msg["code"]
                    code_box["host_ws"] = ws
                    break

        asyncio.run_coroutine_threadsafe(create_room_only(), self.loop).result(timeout=5.0)
        code = code_box["code"]

        # 2. Invalid claim (> units) rejected cleanly
        bad_srv = mcp_srv.McpServer(mcp_srv.Session(seed=1, seat="red"), enable_room_tools=True, default_relay_url=self.url)
        is_err, payload = _call_tool(bad_srv, "join_room", {"room": code, "seat": "red", "units": 3, "claim": 4})
        self.assertTrue(is_err)
        self.assertIn("claim", payload["error"])

        # 3. MCP Red-1 joins with claim=2, MCP Red-2 joins with claim=1, MCP White joins whole team (default claim=3)
        mcp_red1 = mcp_srv.McpServer(mcp_srv.Session(seed=1, seat="red"), enable_room_tools=True, default_relay_url=self.url)
        is_err, j_red1 = _call_tool(mcp_red1, "join_room", {
            "room": code, "seat": "red", "units": 3, "claim": 2, "heroes": ["skeleton", "wizard"],
        })
        self.assertFalse(is_err, j_red1)
        self.assertEqual(j_red1["claim"], 2)

        mcp_red2 = mcp_srv.McpServer(mcp_srv.Session(seed=1, seat="red"), enable_room_tools=True, default_relay_url=self.url)
        is_err, j_red2 = _call_tool(mcp_red2, "join_room", {
            "room": code, "seat": "red", "units": 3, "claim": 1, "heroes": ["bat"],
        })
        self.assertFalse(is_err, j_red2)
        self.assertEqual(j_red2["claim"], 1)

        mcp_white = mcp_srv.McpServer(mcp_srv.Session(seed=1, seat="white"), enable_room_tools=True, default_relay_url=self.url)
        is_err, j_white = _call_tool(mcp_white, "join_room", {
            "room": code, "seat": "white", "units": 3, "heroes": ["knight", "reaper", "hag"],
        })
        self.assertFalse(is_err, j_white)
        self.assertEqual(j_white["claim"], 3)

        # Wait for start on all three MCP servers
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and not (mcp_red1.relay.started and mcp_red2.relay.started and mcp_white.relay.started):
            time.sleep(0.05)
        self.assertTrue(mcp_red1.relay.started, f"red1 failure={mcp_red1.relay.failure}")
        self.assertTrue(mcp_red2.relay.started, f"red2 failure={mcp_red2.relay.failure}")
        self.assertTrue(mcp_white.relay.started, f"white failure={mcp_white.relay.failure}")

        # 5. Verify exact ownership split: red1=['red_1','red_2'], red2=['red_3'], white=['white_1','white_2','white_3']
        self.assertEqual(mcp_red1.seat["units"], ["red_1", "red_2"])
        self.assertEqual(mcp_red2.seat["units"], ["red_3"])
        self.assertEqual(mcp_white.seat["units"], ["white_1", "white_2", "white_3"])

        # 6. Round 1: red_1 belongs to mcp_red1; mcp_red2 must wait & be rejected if it submits for red_1
        is_err, w_r2 = _call_tool(mcp_red2, "wait_for_turn", {"timeout_seconds": 0.2})
        self.assertFalse(is_err)
        self.assertEqual(w_r2["status"], "waiting")
        is_err, bad_act = _call_tool(mcp_red2, "submit_action", {
            "unit": "red_1", "action": {"type": "throw", "angle": 45, "power": 65},
        })
        self.assertTrue(is_err)
        self.assertIn("does not control", bad_act["error"])

        # Play 3 full rounds across all 3 seats:
        # R1: red_1 (mcp_red1) -> white_1 (mcp_white)
        # R2: white_2 (mcp_white) or red_2 (mcp_red1) depending on alternating opener!
        # Let's drive each round cleanly by checking who has status == 'your_turn'!
        seats_list = [("red1", mcp_red1), ("red2", mcp_red2), ("white", mcp_white)]
        acted_by = []
        for _step in range(6):  # 3 rounds * 2 phases = 6 turns
            found = False
            for label, srv in seats_list:
                is_err, w = _call_tool(srv, "wait_for_turn", {"timeout_seconds": 0.4})
                self.assertFalse(is_err, w)
                if w.get("status") == "your_turn":
                    uid = w["active_unit"]
                    is_err, s = _call_tool(srv, "submit_action", {"unit": uid, "action": {"type": "throw", "angle": 45.0, "power": 58.0}})
                    self.assertFalse(is_err, f"{label} {uid} submit failed: {s}")
                    is_err, e = _call_tool(srv, "end_turn", {"round": w["round"], "phase": w["phase"]})
                    self.assertFalse(is_err, f"{label} {uid} end_turn failed: {e}")
                    acted_by.append((label, uid))
                    found = True
                    break
            self.assertTrue(found, f"no seat became active after {acted_by}")

        # Verify all 3 seats actually acted, including mcp_red2 on red_3!
        self.assertIn(("red1", "red_1"), acted_by)
        self.assertIn(("red1", "red_2"), acted_by)
        self.assertIn(("red2", "red_3"), acted_by)
        self.assertIn(("white", "white_1"), acted_by)
        self.assertIn(("white", "white_2"), acted_by)
        self.assertIn(("white", "white_3"), acted_by)

        # Verify 3-way round_hash parity across mcp_red1, mcp_red2, and mcp_white for every completed round!
        time.sleep(0.25)
        h_r1 = dict(mcp_red1.relay.local_hashes)
        h_r2 = dict(mcp_red2.relay.local_hashes)
        h_w = dict(mcp_white.relay.local_hashes)
        self.assertTrue(len(h_w) >= 3, f"expected >=3 round hashes, got {h_w}")
        self.assertEqual(h_r1, h_w, f"red1 vs white hashes mismatch: {h_r1} != {h_w}")
        self.assertEqual(h_r2, h_w, f"red2 vs white hashes mismatch: {h_r2} != {h_w}")
        self.assertNotEqual(mcp_red1.session.sync.get("status"), "out_of_sync")
        self.assertNotEqual(mcp_red2.session.sync.get("status"), "out_of_sync")
        self.assertNotEqual(mcp_white.session.sync.get("status"), "out_of_sync")

        mcp_red1.close()
        mcp_red2.close()
        mcp_white.close()
        bad_srv.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
