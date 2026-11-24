#!/usr/bin/env python3
"""Seat grace on the relay (red-team R6A-3; the MOBA / card-game rule: a disconnected seat is held for a while, then the player has left).
Needs localhost sockets (listed with the other socket tests in run_full_suite.sh). A short grace period is used so the test takes about a second.
Checks: (1) a seat that comes back inside the grace period resumes and nothing is announced; (2) a seat that stays away is removed and the remaining seat gets a
sequenced `seat_left`; (3) a room whose seats are all gone is deleted, so abandoned rooms cannot fill max_rooms; (4) a late resume is refused with resume_expired."""
import asyncio, json, os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import websockets
from pk_relay import RelayServer
from pk_relay_client import RelayClient

GRACE = 0.4


async def recv_type(client, wanted, timeout=3.0):
    async def loop():
        while True:
            message = await client.receive()
            if message.get("type") == wanted:
                return message
    return await asyncio.wait_for(loop(), timeout)


class SeatGraceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.relay = RelayServer("127.0.0.1", 0, seat_grace_seconds=GRACE, max_rooms=3)
        await self.relay.start()
        self.url = "ws://127.0.0.1:%d/ws" % self.relay.bound_port

    async def asyncTearDown(self):
        await self.relay.close()

    async def pair(self):
        red = RelayClient(self.url, None, "red"); boot = await red.connect()
        white = RelayClient(self.url, boot["code"], "white"); await white.connect()
        return red, white, boot

    async def test_back_inside_the_grace_period_resumes_and_nothing_is_announced(self):
        red, white, boot = await self.pair()
        token = boot["seat_token"]
        await red.close()
        await asyncio.sleep(GRACE / 3)
        ws = await websockets.connect(self.url, max_size=16 * 1024)
        await ws.send(json.dumps({"type": "resume", "seat_token": token, "last_seq": 0}))
        state = json.loads(await asyncio.wait_for(ws.recv(), 2))
        self.assertEqual(state["type"], "room_state")
        await asyncio.sleep(GRACE * 2)   # long after the original disconnect time: the resumed seat must not be swept
        self.assertEqual(len(self.relay.rooms), 1)
        for room in self.relay.rooms.values():
            self.assertTrue(any(e.get("connected") for e in room.sessions.values()))
            self.assertEqual([m for m in room.log if m.get("type") == "seat_left"], [])
        await ws.close(); await white.close()

    async def test_an_expired_unready_seat_lets_the_ready_seats_start(self):
        # red-team R1 B3 (unit slot fill): a placeholder seat that never readies holds the start back; if it dies (no `leave`) the grace expiry must release the start
        red = RelayClient(self.url, None, "red"); boot = await red.connect()
        holder = RelayClient(self.url, boot["code"], "white"); await holder.connect()
        white = RelayClient(self.url, boot["code"], "white"); await white.connect()
        await red.send({"type": "ready"}); await white.send({"type": "ready"})
        await asyncio.sleep(0.1)
        self.assertFalse(any(r.started for r in self.relay.rooms.values()), "the unready holder blocks the start")
        await holder.close()   # a connection that just disappears, no `leave`
        start = await recv_type(red, "start", timeout=GRACE * 6)
        self.assertEqual(start["type"], "start")
        self.assertTrue(all(r.started for r in self.relay.rooms.values()))
        await red.close(); await white.close()

    async def test_staying_away_removes_the_seat_and_tells_the_other_seat(self):
        red, white, boot = await self.pair()
        await red.close()
        message = await recv_type(white, "seat_left")
        self.assertEqual((message["team"], message["reason"]), ("red", "disconnect_timeout"))
        self.assertIsInstance(message["seq"], int)
        self.assertEqual(len(self.relay.rooms), 1, "the other seat is still there")
        await white.close()

    async def test_abandoned_rooms_are_deleted_and_do_not_fill_max_rooms(self):
        for _ in range(3):
            host = RelayClient(self.url, None, "red"); await host.connect(); await host.close()
        await asyncio.sleep(GRACE * 3)
        self.assertEqual(len(self.relay.rooms), 0)
        fresh = RelayClient(self.url, None, "red"); boot = await fresh.connect()   # max_rooms is 3: this would be server_busy if the three rooms had leaked
        self.assertEqual(boot["type"], "room_state")
        await fresh.close()

    async def test_a_late_resume_is_refused(self):
        red, white, boot = await self.pair()
        token = boot["seat_token"]
        await red.close()
        await recv_type(white, "seat_left")
        ws = await websockets.connect(self.url, max_size=16 * 1024)
        await ws.send(json.dumps({"type": "resume", "seat_token": token, "last_seq": 0}))
        reply = json.loads(await asyncio.wait_for(ws.recv(), 2))
        self.assertEqual(reply["type"], "error")
        self.assertIn(reply["code"], ("unknown_token", "resume_expired"))
        await ws.close(); await white.close()


class LazyExpiryTests(unittest.IsolatedAsyncioTestCase):
    """R7A-1: with the sweep stopped, only the lazy check inside `resume` can notice the expired seat. It must tell the other seat exactly like the sweep does."""
    async def test_late_resume_tells_the_other_seat(self):
        relay = RelayServer("127.0.0.1", 0, seat_grace_seconds=0.3, max_rooms=3)
        await relay.start()
        relay._reaper.cancel()
        url = "ws://127.0.0.1:%d/ws" % relay.bound_port
        try:
            red = RelayClient(url, None, "red"); boot = await red.connect()
            white = RelayClient(url, boot["code"], "white"); await white.connect()
            token = boot["seat_token"]
            await red.close()
            await asyncio.sleep(0.6)
            ws = await websockets.connect(url, max_size=16 * 1024)
            await ws.send(json.dumps({"type": "resume", "seat_token": token, "last_seq": 0}))
            reply = json.loads(await asyncio.wait_for(ws.recv(), 2))
            self.assertEqual((reply["type"], reply["code"]), ("error", "resume_expired"))
            message = await recv_type(white, "seat_left")
            self.assertEqual((message["team"], message["reason"]), ("red", "disconnect_timeout"))
            await ws.close(); await white.close()
        finally:
            await relay.close()


if __name__ == "__main__":
    unittest.main()
