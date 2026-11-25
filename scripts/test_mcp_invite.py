#!/usr/bin/env python3
"""ROOM-FLOW R11, MCP side: join_room with an invite takes the inviter's team and one place, returns the briefing; lock_hero picks. Needs sockets."""
import asyncio
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mcp_stdio_server as mcp_srv  # noqa: E402
import test_mcp_claim  # noqa: E402  (module import: importing its TestCase would run it again here)
import websockets  # noqa: E402

_call_tool = test_mcp_claim._call_tool


class McpInviteTests(unittest.TestCase):
    setUp = test_mcp_claim.McpClaimTests.setUp
    tearDown = test_mcp_claim.McpClaimTests.tearDown

    def run_host(self, coroutine):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coroutine(loop))
        finally:
            loop.close()

    def test_invite_url_is_parsed(self):
        info = mcp_srv.parse_invite("https://x.example/?room=ABC234&team=2&invite=white.AbCdEfGh12")
        self.assertEqual((info["code"], info["units"], info["invite"]), ("ABC234", 2, "white.AbCdEfGh12"))
        self.assertIsNone(mcp_srv.parse_invite("ABC234")["invite"])

    def test_join_with_an_invite_then_lock_a_hero_and_play_that_unit(self):
        async def flow(loop):
            async with websockets.connect(self.url) as host:
                async def until(wanted):
                    while True:
                        m = json.loads(await asyncio.wait_for(host.recv(), 5))
                        if wanted(m):
                            return m
                await host.send(json.dumps({"type": "create_room", "seat": "red", "team_size": 2, "claim": 2, "name": "房主"}))
                code = (await until(lambda m: m.get("type") == "room_state"))["code"]
                async with websockets.connect(self.url) as white:
                    await white.send(json.dumps({"type": "join", "code": code, "seat": "white", "claim": 1}))
                    await white.recv()
                    await white.send(json.dumps({"type": "invite"}))
                    while True:
                        made = json.loads(await asyncio.wait_for(white.recv(), 5))
                        if made.get("type") == "invite_created":
                            break
                    server = mcp_srv.McpServer(mcp_srv.Session(seed=1), enable_room_tools=True, default_relay_url=self.url, page_judge_mode="off")
                    try:
                        err, joined = await loop.run_in_executor(None, _call_tool, server, "join_room", {"room": code, "units": 2, "invite": made["invite"], "name": "小幫手"})
                        self.assertFalse(err, joined)
                        self.assertEqual((joined["seat"], joined["claim"], joined["briefing"]["team"]), ("white", 1, "white"), joined)
                        self.assertIn("lock_hero", joined["next"])
                        seats = (await until(lambda m: m.get("type") == "room_state" and len(m["seats"]) == 3))["seats"]
                        agent = next(x for x in seats if x["agent"])
                        self.assertEqual((agent["name"], agent["ready"], agent["invited_by"]), ("小幫手", False, "white-1"), agent)
                        err, locked = await loop.run_in_executor(None, _call_tool, server, "lock_hero", {"hero": "hag"})
                        self.assertFalse(err, locked)
                        await until(lambda m: m.get("type") == "room_state" and any(x["agent"] and x["ready"] and x["units"] == ["hag"] for x in m["seats"]))
                        await white.send(json.dumps({"type": "ready", "units": ["knight"]}))
                        await host.send(json.dumps({"type": "ready", "units": ["skeleton", "bat"]}))
                        start = await until(lambda m: m.get("type") == "start")
                        self.assertEqual(start["owners"]["right_1"], agent["seat_id"], start)
                        for _ in range(60):
                            if server.relay.started:
                                break
                            await asyncio.sleep(0.05)
                        self.assertIsNone(server.relay.failure)
                        self.assertEqual(server.session.seat["units"], [mcp_srv.engine_unit_id("right_1")])
                        err, late = await loop.run_in_executor(None, _call_tool, server, "lock_hero", {"hero": "bat"})
                        self.assertTrue(err, late)
                    finally:
                        await loop.run_in_executor(None, server.close)
        self.run_host(flow)

    def test_an_agent_whose_inviter_leaves_is_told(self):
        async def flow(loop):
            async with websockets.connect(self.url) as host:
                await host.send(json.dumps({"type": "create_room", "seat": "red", "team_size": 2, "claim": 1}))
                code = json.loads(await host.recv())["code"]
                await host.send(json.dumps({"type": "invite"}))
                while True:
                    made = json.loads(await asyncio.wait_for(host.recv(), 5))
                    if made.get("type") == "invite_created":
                        break
                server = mcp_srv.McpServer(mcp_srv.Session(seed=1), enable_room_tools=True, default_relay_url=self.url, page_judge_mode="off")
                try:
                    err, joined = await loop.run_in_executor(None, _call_tool, server, "join_room", {"room": code, "units": 2, "invite": made["invite"], "heroes": ["bat"]})
                    self.assertFalse(err, joined)
                    self.assertNotIn("lock_hero", joined["next"])
                    await host.send(json.dumps({"type": "leave"}))
                    for _ in range(60):
                        if server.relay.failure:
                            break
                        await asyncio.sleep(0.05)
                    self.assertEqual(server.relay.failure, "kicked:inviter_left")
                finally:
                    await loop.run_in_executor(None, server.close)
        self.run_host(flow)

    def test_a_used_or_wrong_invite_is_an_error(self):
        server = mcp_srv.McpServer(mcp_srv.Session(seed=1), enable_room_tools=True, default_relay_url=self.url, page_judge_mode="off")
        try:
            err, answer = _call_tool(server, "join_room", {"room": "ABC234", "invite": "white.nope"})
            self.assertTrue(err, answer)
            err, answer = _call_tool(server, "join_room", {"room": "ABC234", "invite": "nonsense"})
            self.assertTrue(err, answer)
        finally:
            server.close()


if __name__ == "__main__":
    unittest.main()
