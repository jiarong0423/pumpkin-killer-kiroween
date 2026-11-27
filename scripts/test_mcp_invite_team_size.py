#!/usr/bin/env python3
"""An agent that only follows the in-game invite text (room code + invite, no units, no link) sits down in a room of any size.

2026-11-28, live site: join_room assumed 3 units per side, so in a 2v2 room the agent's page switched the team size, left the room it had just joined and the
agent got `join_required` with its one-use ticket spent. The ticket now says the team size. Needs Node 22+ and local sockets."""
import asyncio
import shutil
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mcp_stdio_server as mcp_srv  # noqa: E402
import test_mcp_claim  # noqa: E402
import test_mcp_invite_page  # noqa: E402
import websockets  # noqa: E402

NODE = shutil.which("node")
_call_tool = test_mcp_claim._call_tool
Raw = test_mcp_invite_page.Raw


class TicketSizeTests(unittest.TestCase):
    def test_the_size_is_read_from_the_ticket_and_old_tickets_still_parse(self):
        for size in (1, 2, 3):
            ticket = "white.n%d-AbC_def-123456" % size
            self.assertTrue(mcp_srv._INVITE_RE.match(ticket), ticket)
            self.assertEqual(mcp_srv.invite_team_size(ticket), size, ticket)
        for ticket in ("white.AbCdef123456", "red.n4-AbCdef123456", "red.n2AbCdef123456"):
            self.assertTrue(mcp_srv._INVITE_RE.match(ticket), ticket)
            self.assertIsNone(mcp_srv.invite_team_size(ticket), ticket)


@unittest.skipIf(NODE is None, "Node is not installed")
class McpInviteTeamSizeTests(unittest.TestCase):
    setUp = test_mcp_claim.McpClaimTests.setUp
    tearDown = test_mcp_claim.McpClaimTests.tearDown

    def _join(self, size, extra):
        """Host a lobby room of `size` per side, invite, and join with room + invite plus `extra` arguments."""
        self.relay.agent_pick_seconds = 600
        loop = asyncio.new_event_loop()
        server = mcp_srv.McpServer(mcp_srv.Session(seed=1), enable_room_tools=True, default_relay_url=self.url, page_judge_mode="on", page_speed=6.0)

        async def tool(name, args=None):
            return await loop.run_in_executor(None, _call_tool, server, name, args or {})

        async def flow():
            async with websockets.connect(self.url) as host_socket:
                host = Raw(host_socket)
                await host.send(type="create_room", seat="red", team_size=size, claim=1, lobby=True, name="Host")
                code = (await host.until(lambda m: m.get("type") == "room_state", what="the room"))["code"]
                await host.send(type="room_options", allow_mcp=True)
                await host.send(type="ready", units=["skeleton"])
                await host.send(type="invite")
                invite = (await host.until(lambda m: m.get("type") == "invite_created", what="the invite"))["invite"]
                try:
                    err, joined = await tool("join_room", dict({"room": code, "invite": invite, "name": "PageBot"}, **extra))
                    self.assertFalse(err, joined)
                    self.assertEqual((joined["seat"], joined["claim"], joined["units"]), ("red", 1, size), joined)
                    err, locked = await tool("lock_hero", {"hero": "hag"})
                    self.assertFalse(err, locked)
                    await host.until(lambda m: m.get("type") == "room_state" and any(x.get("agent") and x["ready"] and x["units"] == ["hag"] for x in m["seats"]), what="the agent locked")
                    err, waiting = await tool("wait_for_turn", {"timeout_seconds": 1.5})
                    self.assertFalse(err, waiting)
                    self.assertIsNone(server.relay.failure)
                finally:
                    await loop.run_in_executor(None, server.close)

        try:
            loop.run_until_complete(asyncio.wait_for(flow(), 90))
        finally:
            loop.close()

    def test_two_a_side_with_code_and_invite_only(self):
        self._join(2, {})

    def test_three_a_side_with_code_and_invite_only(self):
        self._join(3, {})

    def test_a_wrong_units_argument_does_not_override_the_ticket(self):
        self._join(2, {"units": 3})


if __name__ == "__main__":
    unittest.main()
