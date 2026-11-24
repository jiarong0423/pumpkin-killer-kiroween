#!/usr/bin/env python3
"""Late join into a started room (redteam/ISSUE_LEDGER_slotfill_20261124.md, LATE-JOIN-1; Gemini T1 path 5).
Before the fix the relay created an extra red/white seat after the match had started: the seat never received `start`, the page
said nothing. Now a red/white `join` into a started room is answered with error `room_started` and no seat is added.
Spectators and `resume` of an existing seat are unchanged. Needs localhost sockets."""
import asyncio, json, os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import websockets
from pk_relay import RelayServer


async def recv_until(ws, wanted, timeout=3.0):
    async def loop():
        while True:
            message = json.loads(await ws.recv())
            if message.get("type") in wanted:
                return message
    return await asyncio.wait_for(loop(), timeout)


class LateJoinTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.relay = RelayServer("127.0.0.1", 0, max_rooms=4)
        await self.relay.start()
        self.url = "ws://127.0.0.1:%d/ws" % self.relay.bound_port
        self.sockets = []

    async def asyncTearDown(self):
        for ws in self.sockets:
            await ws.close()
        await self.relay.close()

    async def open(self):
        ws = await websockets.connect(self.url, max_size=64 * 1024)
        self.sockets.append(ws)
        return ws

    async def started_room(self):
        red = await self.open()
        await red.send(json.dumps({"type": "create_room", "seat": "red"}))
        boot = await recv_until(red, ("room_state",))
        white = await self.open()
        await white.send(json.dumps({"type": "join", "code": boot["code"], "seat": "white"}))
        await recv_until(white, ("room_state",))
        await red.send(json.dumps({"type": "ready"})); await white.send(json.dumps({"type": "ready"}))
        await recv_until(red, ("start",))
        return boot["code"], red, white, boot

    async def join_error(self, code, seat):
        late = await self.open()
        await late.send(json.dumps({"type": "join", "code": code, "seat": seat}))
        return await recv_until(late, ("error", "room_state"))

    async def test_a_player_seat_is_refused_after_the_start(self):
        code, red, white, _ = await self.started_room()
        seats_before = len(self.relay.rooms[code].sessions)
        for seat in ("white", "red"):
            reply = await self.join_error(code, seat)
            self.assertEqual((reply.get("type"), reply.get("code")), ("error", "room_started"), "seat=%s must be refused" % seat)
        self.assertEqual(len(self.relay.rooms[code].sessions), seats_before, "no extra seat may be created")

    async def test_a_spectator_may_still_watch_a_started_room(self):
        code, *_ = await self.started_room()
        reply = await self.join_error(code, "spectator")
        self.assertEqual(reply.get("type"), "room_state")

    async def test_resume_of_an_existing_seat_still_works_after_the_start(self):
        code, red, white, boot = await self.started_room()
        token = boot["seat_token"]
        await red.close()
        again = await self.open()
        await again.send(json.dumps({"type": "resume", "seat_token": token, "last_seq": 0}))
        reply = await recv_until(again, ("room_state", "error"))
        self.assertEqual(reply["type"], "room_state")

    async def test_joining_before_the_start_still_works(self):
        red = await self.open()
        await red.send(json.dumps({"type": "create_room", "seat": "red"}))
        boot = await recv_until(red, ("room_state",))
        reply = await self.join_error(boot["code"], "white")
        self.assertEqual(reply.get("type"), "room_state")


if __name__ == "__main__":
    unittest.main()
