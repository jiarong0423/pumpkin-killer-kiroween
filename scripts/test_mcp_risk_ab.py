#!/usr/bin/env python3
"""Tests for MCP deploy risks A and B (redteam/ISSUE_LEDGER_slotfill_20261124.md, MCP-RISK-A / MCP-RISK-B).

A: hosted MCP seats must be counted per real remote client by the relay, not all as 127.0.0.1. The gateway sends
   X-PK-Client-Addr plus X-PK-Gateway-Token; the relay honours it only when the token matches its own.
B: /mcp must cap the sessions one client can hold (PK_MCP_MAX_SESSIONS_PER_IP).
"""
import asyncio
import json
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import websockets  # noqa: E402
from pk_relay import RelayServer  # noqa: E402

GW_CODE = "unit-test-gateway-value-0123456789abcdef"


class FakeRequest:
    def __init__(self, headers):
        self.headers = headers


class FakeSocket:
    def __init__(self, headers, peer="127.0.0.1"):
        self.request = FakeRequest(headers)
        self.remote_address = (peer, 5555)


class RelayAddrTests(unittest.TestCase):
    def addr(self, relay, headers):
        return relay._addr(FakeSocket(headers))

    def test_token_and_address_are_honoured_with_prefix(self):
        relay = RelayServer("127.0.0.1", 0, gateway_token=GW_CODE)
        got = self.addr(relay, {"X-PK-Gateway-Token": GW_CODE, "X-PK-Client-Addr": "203.0.113.5"})
        self.assertEqual(got, "mcp:203.0.113.5")

    def test_wrong_or_missing_token_is_ignored(self):
        relay = RelayServer("127.0.0.1", 0, gateway_token=GW_CODE)
        self.assertEqual(self.addr(relay, {"X-PK-Gateway-Token": "nope", "X-PK-Client-Addr": "203.0.113.5"}), "127.0.0.1")
        self.assertEqual(self.addr(relay, {"X-PK-Client-Addr": "203.0.113.5"}), "127.0.0.1")
        self.assertEqual(self.addr(relay, {"X-PK-Gateway-Token": GW_CODE}), "127.0.0.1")

    def test_relay_without_a_configured_token_ignores_the_header(self):
        relay = RelayServer("127.0.0.1", 0)
        self.assertEqual(self.addr(relay, {"X-PK-Gateway-Token": GW_CODE, "X-PK-Client-Addr": "203.0.113.5"}), "127.0.0.1")
        relay_empty = RelayServer("127.0.0.1", 0, gateway_token="")
        self.assertEqual(self.addr(relay_empty, {"X-PK-Gateway-Token": "", "X-PK-Client-Addr": "203.0.113.5"}), "127.0.0.1")

    def test_address_is_truncated(self):
        relay = RelayServer("127.0.0.1", 0, gateway_token=GW_CODE)
        got = self.addr(relay, {"X-PK-Gateway-Token": GW_CODE, "X-PK-Client-Addr": "9" * 500})
        self.assertLessEqual(len(got), 68)


class RelayCapEndToEnd(unittest.TestCase):
    """Real sockets: with a cap of 2 per address, three distinct hosted clients are all accepted, while three
    plain connections from the same peer are not."""

    async def _accepted(self, url, headers):
        sock = await websockets.connect(url, additional_headers=headers or None, max_size=64 * 1024)
        try:
            msg = await asyncio.wait_for(sock.recv(), 0.4)
            return not ("server_busy" in str(msg)), sock
        except asyncio.TimeoutError:
            return True, sock
        except websockets.ConnectionClosed:
            return False, sock

    async def _run(self):
        relay = RelayServer("127.0.0.1", 0, max_per_addr=2, gateway_token=GW_CODE)
        await relay.start()
        url = "ws://127.0.0.1:%d/ws" % relay.bound_port
        socks = []
        try:
            hosted = []
            for ip in ("198.51.100.1", "198.51.100.2", "198.51.100.3"):
                ok, sock = await self._accepted(url, {"X-PK-Gateway-Token": GW_CODE, "X-PK-Client-Addr": ip})
                socks.append(sock)
                hosted.append(ok)
            plain = []
            for _ in range(3):
                ok, sock = await self._accepted(url, None)
                socks.append(sock)
                plain.append(ok)
            return hosted, plain
        finally:
            for sock in socks:
                await sock.close()
            await relay.close()

    def test_hosted_clients_are_counted_apart(self):
        hosted, plain = asyncio.run(self._run())
        self.assertEqual(hosted, [True, True, True], "hosted clients with distinct addresses must all be accepted")
        self.assertEqual(plain, [True, True, False], "plain connections still share the peer address cap of 2")


class SeenAddrRelay(RelayServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen = []

    def _addr(self, websocket):
        value = super()._addr(websocket)
        self.seen.append(value)
        return value


class BridgeSendsHeaders(unittest.TestCase):
    def test_connected_relay_identifies_the_client(self):
        import mcp_stdio_server as srv
        loop = asyncio.new_event_loop()
        ready = threading.Event()
        box = {}

        def run():
            asyncio.set_event_loop(loop)
            box["relay"] = SeenAddrRelay("127.0.0.1", 0, gateway_token=GW_CODE)
            loop.run_until_complete(box["relay"].start())
            ready.set()
            loop.run_forever()
            loop.run_until_complete(box["relay"].close())
            loop.close()

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        self.assertTrue(ready.wait(3))
        url = "ws://127.0.0.1:%d/ws" % box["relay"].bound_port
        try:
            session = srv.Session(seed=1, seat="red", turn_seconds=0, human_turn_seconds=0)
            bridge = srv.ConnectedRelay(session, url, "NOPE22", "red", client_addr="203.0.113.77", gateway_token=GW_CODE)
            bridge.start()
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline and not box["relay"].seen:
                time.sleep(0.02)
            bridge.closed.set()
            self.assertIn("mcp:203.0.113.77", box["relay"].seen)
        finally:
            loop.call_soon_threadsafe(loop.stop)
            thread.join(3)


def http_post(base, body, headers=None):
    hdrs = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    hdrs.update(headers or {})
    req = urllib.request.Request(base + "/mcp", data=json.dumps(body).encode(), headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            resp.read()
            return resp.status
    except urllib.error.HTTPError as err:
        err.read()
        return err.code


INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}}


class PerClientSessionCap(unittest.TestCase):
    def serve(self, **kwargs):
        import pk_mcp_http as mcp_http
        server = mcp_http.create_server(host="127.0.0.1", port=0, max_sessions=64, max_sessions_per_ip=2, **kwargs)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close(), server.close_all_sessions(), thread.join(3)))
        return "http://127.0.0.1:%d" % server.server_address[1]

    def test_cap_applies_per_client_and_x_real_ip_is_used(self):
        base = self.serve()
        real = {"X-Real-IP": "203.0.113.1"}
        self.assertEqual([http_post(base, INIT, real) for _ in range(2)], [200, 200])
        self.assertEqual(http_post(base, INIT, real), 429, "third session of the same client must be refused")
        self.assertEqual(http_post(base, INIT, {"X-Real-IP": "203.0.113.2"}), 200, "another client is unaffected")

    def test_spoofed_cf_header_is_ignored_unless_proxy_trusted(self):
        base = self.serve(trust_proxy=False)
        self.assertEqual([http_post(base, INIT, {"X-Real-IP": "203.0.113.9", "CF-Connecting-IP": "198.51.100.%d" % i}) for i in range(2)], [200, 200])
        self.assertEqual(http_post(base, INIT, {"X-Real-IP": "203.0.113.9", "CF-Connecting-IP": "198.51.100.99"}), 429)

    def test_trusted_proxy_uses_cf_connecting_ip(self):
        base = self.serve(trust_proxy=True)
        cf = {"X-Real-IP": "10.0.0.1", "CF-Connecting-IP": "198.51.100.7"}
        self.assertEqual([http_post(base, INIT, cf) for _ in range(2)], [200, 200])
        self.assertEqual(http_post(base, INIT, cf), 429)
        self.assertEqual(http_post(base, INIT, {"X-Real-IP": "10.0.0.1", "CF-Connecting-IP": "198.51.100.8"}), 200)

    def test_no_proxy_headers_falls_back_to_the_peer_address(self):
        base = self.serve()
        self.assertEqual([http_post(base, INIT) for _ in range(2)], [200, 200])
        self.assertEqual(http_post(base, INIT), 429)


if __name__ == "__main__":
    unittest.main()
