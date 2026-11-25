"""F10: the MCP bridge treats a pre-start seat_left (a lobby player whose grace ran out) as the end of a match and names a winner.
Run: python3 -B scripts/redteam_probes/probe_mcp.py"""
import os
import asyncio
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h import H, run, verdict  # noqa: E402
import mcp_stdio_server as mcp  # noqa: E402  (scripts/ is on sys.path via h)


async def main():
    async with H(seat_grace_seconds=0.6) as h:
        host, code, _ = await h.create(team_size=2, claim=1, units=["wizard"])
        await host.send(type="invite", note="play")
        ticket = host.last("invite_created")["invite"]
        human = await h.join(code, seat="white", claim=1, units=["bat"])
        sess = mcp.Session(seed=1, turn_seconds=0, human_turn_seconds=0, seat="red", units=2)
        bridge = mcp.ConnectedRelay(sess, h.url, code, "red", auto_ready=False, explicit_units=False,
                                    claim_heroes=["knight"], invite=ticket, name="bot")
        bridge.start()
        for _ in range(40):
            await asyncio.sleep(0.05)
            if bridge.seat_token:
                break
        before = (sess.phase, sess.winner)
        await human.close()                 # the white player closes the tab in the lobby; grace 0.6 s
        await asyncio.sleep(2.0)
        room = h.room(code)
        left = host.last("seat_left")
        verdict("F10 MCP agent marks the match over before it started", (not room.started) and sess.phase == "over",
                "relay started=%s, seat_left sent pre-start=%s; agent session before=%s after=(phase=%s, winner=%s)" % (
                    room.started, left is not None, before, sess.phase, sess.winner),
                "a seat_left before `start` changes nothing in the agent's match state")
        bridge.close()


run(main())
