#!/usr/bin/env python3
"""Capacity guards of the relay (docs/THREAT_MODEL_20261117.md T1 and T3, owner 2026-11-17: 'if the traffic is too high the resources may not be enough').

Socket-free where possible (the same Peer / FakeSocket idea as scripts/test_pk_relay.py): the guards live in RelayServer._dispatch and _handle_socket.
Covers: a cap on rooms, a cap on spectators per room, the wrong-code limit per client ADDRESS (many connections do not bypass it), the address helper with and without the trusted proxy header,
and the idle-room reaper. Exit code 1 on any failure.
"""
import asyncio
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pk_relay import RelayServer  # noqa: E402


class FakeSocket:
    def __init__(self, address="203.0.113.7", headers=None):
        self.sent = []
        self.remote_address = (address, 5000)
        self.request_headers = headers or {}
        self.closed = None

    async def send(self, raw):
        import json
        self.sent.append(json.loads(raw))

    async def close(self, code=1000, reason=""):
        self.closed = (code, reason)


class Peer:
    def __init__(self, relay, address="203.0.113.7"):
        self.relay = relay
        self.socket = FakeSocket(address)
        self.room = None
        self.entry = None
        self.wrong_codes = []

    async def say(self, **message):
        self.room, self.entry = await self.relay._dispatch(self.socket, self.room, self.entry, message, self.wrong_codes)
        return self

    def error_codes(self):
        return [m["code"] for m in self.socket.sent if m.get("type") == "error"]


class LimitTests(unittest.IsolatedAsyncioTestCase):
    async def test_rooms_are_capped(self):
        relay = RelayServer("127.0.0.1", 0, max_rooms=2)
        a, b, c = Peer(relay), Peer(relay), Peer(relay)
        await a.say(type="create_room", seat="red", client_version="t")
        await b.say(type="create_room", seat="red", client_version="t")
        await c.say(type="create_room", seat="red", client_version="t")
        self.assertEqual(len(relay.rooms), 2)
        self.assertEqual(c.error_codes(), ["server_busy"])
        self.assertIsNone(c.room)

    async def test_spectators_are_capped_per_room(self):
        relay = RelayServer("127.0.0.1", 0, max_spectators=2)
        host = Peer(relay)
        await host.say(type="create_room", seat="red", client_version="t")
        code = [m for m in host.socket.sent if m.get("type") == "room_state"][-1]["code"]
        watchers = [Peer(relay) for _ in range(3)]
        for w in watchers:
            await w.say(type="join", code=code, seat="spectator")
        self.assertEqual([w.error_codes() for w in watchers], [[], [], ["room_full"]])

    async def test_wrong_codes_are_limited_per_address_not_only_per_connection(self):
        relay = RelayServer("127.0.0.1", 0, max_wrong_per_addr=6)
        codes = []
        for _ in range(4):                       # four connections from one address, each well under the per-connection limit of 5
            peer = Peer(relay)
            for _ in range(3):
                await peer.say(type="join", code="ZZZZZZ", seat="red")
            codes += peer.error_codes()
        self.assertIn("rate_limited", codes, "the address limit must stop the guesses: " + str(codes))
        other = Peer(relay, address="198.51.100.9")   # another address is not punished
        await other.say(type="join", code="ZZZZZZ", seat="red")
        self.assertEqual(other.error_codes(), ["unknown_code"])

    async def test_address_uses_the_proxy_header_only_when_trusted(self):
        socket = FakeSocket("10.0.0.1", {"CF-Connecting-IP": "198.51.100.77"})
        self.assertEqual(RelayServer("127.0.0.1", 0, trust_proxy=False)._addr(socket), "10.0.0.1")
        self.assertEqual(RelayServer("127.0.0.1", 0, trust_proxy=True)._addr(socket), "198.51.100.77")
        self.assertEqual(RelayServer("127.0.0.1", 0, trust_proxy=True)._addr(FakeSocket("10.0.0.1")), "10.0.0.1")

    async def test_idle_rooms_lose_their_sockets(self):
        relay = RelayServer("127.0.0.1", 0, room_idle_seconds=0.2)
        host = Peer(relay)
        await host.say(type="create_room", seat="red", client_version="t")
        relay.rooms[host.room.code].clients[host.socket] = {"seat_id": "x"}
        relay.last_seen[host.room.code] = time.monotonic() - 5
        task = asyncio.ensure_future(relay._reap_idle_rooms())
        await asyncio.sleep(0.4)
        task.cancel()
        self.assertEqual(host.socket.closed, (1001, "room idle"))


class SocketAdmissionTest(unittest.IsolatedAsyncioTestCase):
    """The connection caps live in _handle_socket: they need a real local socket (skipped where binding is refused, as in the Claude sandbox)."""

    async def test_third_connection_from_one_address_is_refused(self):
        import websockets
        relay = RelayServer("127.0.0.1", 0, max_per_addr=2)
        try:
            await relay.start()
        except OSError as error:
            self.skipTest("cannot bind a local socket here: %s" % error)
        url = "ws://127.0.0.1:%d/ws" % relay.bound_port
        sockets = []
        try:
            for _ in range(2):
                sockets.append(await websockets.connect(url))
            third = await websockets.connect(url)
            sockets.append(third)
            import json
            first = json.loads(await asyncio.wait_for(third.recv(), 3))
            self.assertEqual(first, {"type": "error", "code": "server_busy"})
            await asyncio.wait_for(third.wait_closed(), 3)
            self.assertEqual(relay.connections, 2)
        finally:
            for sock in sockets:
                await sock.close()
            await relay.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
