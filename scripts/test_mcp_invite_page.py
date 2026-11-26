#!/usr/bin/env python3
"""LIVE-3V3-4: an INVITED MCP agent is judged by the real page (PageJudgeRelay, one unit), not by the bridge's own engine.

A lobby room of two against two on a local relay. Red: the host (a raw socket, one place) and the agent it invited (the bridge, page judge on, one place);
white: one raw socket with both places. Checked: join_room with an invite gives a PageJudgeRelay seat with the briefing; a hero a teammate holds comes back
as pick_again and lock_hero may try again; after the start the seat owns exactly the unit the relay gave it; the agent is told `your_turn` only for that unit
(never in a teammate's turn of its own team); its throw goes out under its own seat and unit and the turn ends; after the host's reset_lobby the agent is
asked to lock again and the second match starts on the same seat. Needs Node 22+ and local sockets."""
import asyncio
import json
import shutil
import sys
import threading
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mcp_stdio_server as mcp_srv  # noqa: E402
import test_mcp_claim  # noqa: E402
import websockets  # noqa: E402

NODE = shutil.which("node")
_call_tool = test_mcp_claim._call_tool


class Raw:
    """A raw relay seat: every message it received is kept; `until` waits for one that fits (also among those already received)."""

    def __init__(self, socket):
        self.socket = socket
        self.seen = []
        self.pos = 0

    async def send(self, **message):
        await self.socket.send(json.dumps(message))

    async def until(self, wanted, seconds=10.0, what="a message"):
        deadline = time.monotonic() + seconds
        while True:
            while self.pos < len(self.seen):
                message = self.seen[self.pos]
                self.pos += 1
                if wanted(message):
                    return message
            left = deadline - time.monotonic()
            if left <= 0:
                raise AssertionError("timed out waiting for %s; last messages: %s" % (what, [m.get("type") for m in self.seen[-12:]]))
            try:
                self.seen.append(json.loads(await asyncio.wait_for(self.socket.recv(), left)))
            except asyncio.TimeoutError:
                pass


@unittest.skipIf(NODE is None, "Node is not installed")
class McpInvitePageJudgeTests(unittest.TestCase):
    setUp = test_mcp_claim.McpClaimTests.setUp
    tearDown = test_mcp_claim.McpClaimTests.tearDown

    def test_an_invited_agent_plays_one_unit_on_the_real_page_for_two_matches(self):
        self.relay.countdown_seconds = 0.2
        self.relay.agent_pick_seconds = 600   # the test locks by itself; the relay's own pick must not hide a missing lock
        loop = asyncio.new_event_loop()
        server = mcp_srv.McpServer(mcp_srv.Session(seed=1), enable_room_tools=True, default_relay_url=self.url, page_judge_mode="on", page_speed=6.0)

        async def tool(name, args=None):
            return await loop.run_in_executor(None, _call_tool, server, name, args or {})

        async def raw_turn(seat, other, team, unit, rnd):
            """A raw seat throws short (nobody is hit), the other team's raw seat says miss, the turn ends."""
            left = team == "red"
            await seat.send(type="action", round=rnd, phase=team, unit=unit, kind="throw", angle=70, power=12.0,
                            start={"x": 300.0 if left else 1620.0, "y": 760.0}, dirX=1 if left else -1, claimed_landing={"x": 340.0 if left else 1580.0, "y": 870.0})
            ack = await seat.until(lambda m: m.get("type") == "action_ack", what="action_ack of %s" % unit)
            await other.send(type="judge", ref=ack["seq"], hit=False)
            await asyncio.sleep(0.4)
            await seat.send(type="end_turn", round=rnd, phase=team)
            await seat.until(lambda m: m.get("type") == "end_turn" and m.get("round") == rnd and m.get("phase") == team, what="end_turn of %s" % unit)

        async def one_match(host, white, agent_seat_id, number):
            start = await host.until(lambda m: m.get("type") == "start", what="start of match %d" % number)
            await white.until(lambda m: m.get("type") == "start")
            mine = [unit for unit, owner in start["owners"].items() if owner == agent_seat_id]
            self.assertEqual(mine, ["left_1"], start["owners"])
            for _ in range(200):
                if server.relay.started:
                    break
                await asyncio.sleep(0.05)
            self.assertTrue(server.relay.started, "the bridge's page did not see match %d start (failure %r)" % (number, server.relay.failure))
            self.assertEqual(server.session.seat["units"], [mcp_srv.engine_unit_id("left_1")])
            # round 1, red: the host's unit is due. The agent's own team is on, but it is not the agent's turn.
            err, waiting = await tool("wait_for_turn", {"timeout_seconds": 1.5})
            self.assertFalse(err, waiting)
            self.assertEqual(waiting["status"], "waiting", waiting)
            await raw_turn(host, white, "red", "left_0", 1)
            await raw_turn(white, host, "white", "right_0", 1)
            # round 2, red: the agent's unit is due
            err, turn = await tool("wait_for_turn", {"timeout_seconds": 20})
            self.assertFalse(err, turn)
            self.assertEqual((turn["status"], turn.get("active_unit"), turn.get("round")), ("your_turn", mcp_srv.engine_unit_id("left_1"), 2), turn)
            err, sent = await tool("submit_action", {"unit": turn["active_unit"], "round": 2, "action": {"type": "throw", "angle": 70, "power": 12.0}})
            self.assertFalse(err, sent)
            self.assertEqual(sent.get("end_turn_args"), {"round": 2, "phase": turn["phase"]}, sent)
            action = await white.until(lambda m: m.get("type") == "action" and m.get("round") == 2, what="the agent's action on the wire")
            self.assertEqual((action["seat_id"], action["unit"], action["phase"]), (agent_seat_id, "left_1", "red"), action)
            await white.send(type="judge", ref=action["seq"], hit=False)
            err, ended = await tool("end_turn", sent["end_turn_args"])
            self.assertFalse(err, ended)
            done = await white.until(lambda m: m.get("type") == "end_turn" and m.get("round") == 2 and m.get("phase") == "red", what="the agent's end_turn on the wire")
            self.assertEqual(done["seat_id"], agent_seat_id, done)
            # a second end_turn for the turn that is already over is not an error for the agent (the page ended it after the landing)
            err, again = await tool("end_turn", sent["end_turn_args"])
            self.assertFalse(err, again)
            self.assertIsNone(server.relay.failure)

        async def flow():
            async with websockets.connect(self.url) as host_socket, websockets.connect(self.url) as white_socket:
                host, white = Raw(host_socket), Raw(white_socket)
                await host.send(type="create_room", seat="red", team_size=2, claim=1, lobby=True, name="Host")
                code = (await host.until(lambda m: m.get("type") == "room_state", what="the room"))["code"]
                await host.send(type="room_options", allow_mcp=True)
                await white.send(type="join", code=code, seat="white", claim=2, name="White")
                await white.until(lambda m: m.get("type") == "room_state" and m.get("seat_token"), what="white seated")
                await host.send(type="ready", units=["skeleton"])
                await host.send(type="invite")
                invite = (await host.until(lambda m: m.get("type") == "invite_created", what="the invite"))["invite"]
                try:
                    err, joined = await tool("join_room", {"room": code, "units": 2, "invite": invite, "name": "PageBot"})
                    self.assertFalse(err, joined)
                    self.assertIsInstance(server.relay, mcp_srv.PageJudgeRelay, "an invited agent must be judged by the real page (LIVE-3V3-4)")
                    self.assertEqual((joined["seat"], joined["claim"], joined["briefing"]["team"]), ("red", 1, "red"), joined)
                    self.assertIn("lock_hero", joined["next"])
                    seats = (await host.until(lambda m: m.get("type") == "room_state" and any(x.get("agent") for x in m["seats"]), what="the agent seat"))["seats"]
                    agent = next(x for x in seats if x.get("agent"))
                    self.assertEqual((agent["name"], agent["ready"], agent["invited_by"], agent["team"]), ("PageBot", False, "red-1", "red"), agent)
                    self.assertEqual(joined["seat_id"], agent["seat_id"], joined)
                    # the host holds the skeleton: the relay refuses it, the agent is told to pick again and may
                    err, locked = await tool("lock_hero", {"hero": "skeleton"})
                    self.assertFalse(err, locked)
                    err, again = await tool("wait_for_turn", {"timeout_seconds": 5})
                    self.assertEqual(again.get("status"), "pick_again", again)
                    err, locked = await tool("lock_hero", {"hero": "hag"})
                    self.assertFalse(err, locked)
                    await host.until(lambda m: m.get("type") == "room_state" and any(x.get("agent") and x["ready"] and x["units"] == ["hag"] for x in m["seats"]), what="the agent locked with the hag")
                    await white.send(type="ready", units=["knight", "bat"])
                    await host.send(type="begin")
                    await one_match(host, white, agent["seat_id"], 1)
                    # back to the lobby of the same room: the agent is asked to lock again, then the second match runs on the same seat
                    await host.send(type="reset_lobby")
                    await host.until(lambda m: m.get("type") == "lobby_reset", what="lobby_reset")
                    err, lobby = await tool("wait_for_turn", {"timeout_seconds": 10})
                    self.assertFalse(err, lobby)
                    self.assertEqual(lobby.get("status"), "pick_again", lobby)
                    err, late = await tool("submit_action", {"unit": mcp_srv.engine_unit_id("left_1"), "action": {"type": "throw", "angle": 50, "power": 50.0}})
                    self.assertTrue(err, late)
                    err, locked = await tool("lock_hero", {"hero": "wizard"})
                    self.assertFalse(err, locked)
                    await host.until(lambda m: m.get("type") == "room_state" and not m.get("started") and any(x.get("agent") and x["ready"] and x["units"] == ["wizard"] for x in m["seats"]), what="the agent locked again")
                    await host.send(type="ready", units=["skeleton"])
                    await white.send(type="ready", units=["knight", "bat"])
                    await host.send(type="begin")
                    await one_match(host, white, agent["seat_id"], 2)
                    err, left = await tool("leave_room")
                    self.assertFalse(err, left)
                    gone = await host.until(lambda m: m.get("type") == "seat_left" and m.get("seat_id") == agent["seat_id"], seconds=5, what="the agent's seat released at once by leave_room")
                    self.assertEqual(gone["team"], "red", gone)
                finally:
                    await loop.run_in_executor(None, server.close)

        try:
            loop.run_until_complete(asyncio.wait_for(flow(), 150))
        finally:
            loop.close()

    def test_a_wrong_invite_is_an_error_with_the_page_judge_too(self):
        server = mcp_srv.McpServer(mcp_srv.Session(seed=1), enable_room_tools=True, default_relay_url=self.url, page_judge_mode="on")
        try:
            err, answer = _call_tool(server, "join_room", {"room": "ABC234", "invite": "white.nope"})
            self.assertTrue(err, answer)
            self.assertIsNone(server.relay)
        finally:
            server.close()


if __name__ == "__main__":
    unittest.main()
