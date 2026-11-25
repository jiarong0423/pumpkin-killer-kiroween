"""Red-team A harness: in-process RelayServer on a free port plus small socket helpers."""
import os
import asyncio
import json
import sys
import time

import websockets

REPO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
import pk_relay  # noqa: E402
from pk_relay import RelayServer  # noqa: E402

RESULTS = []


def verdict(name, broken, observed, expected):
    RESULTS.append((name, broken))
    print("[%s] %s\n    observed: %s\n    expected: %s" % ("BREAK" if broken else "HELD", name, observed, expected))


class C:
    """One client socket that keeps every message it receives."""
    def __init__(self, ws):
        self.ws = ws
        self.inbox = []
        self.task = asyncio.ensure_future(self._pump())

    async def _pump(self):
        try:
            async for raw in self.ws:
                self.inbox.append(json.loads(raw))
        except Exception:
            pass

    async def send(self, **msg):
        await self.ws.send(json.dumps(msg))
        await asyncio.sleep(0.12)   # stay under 10 msg/s and let the relay answer

    def last(self, typ, pred=lambda m: True):
        for m in reversed(self.inbox):
            if m.get("type") == typ and pred(m):
                return m
        return None

    def errors(self):
        return [m.get("code") for m in self.inbox if m.get("type") == "error"]

    def state(self):
        return self.last("room_state")

    async def close(self):
        await self.ws.close()
        await asyncio.sleep(0.1)


class H:
    def __init__(self, **limits):
        base = dict(max_per_addr=1000, max_connects_per_min=100000, max_connections=5000)
        base.update(limits)
        self.relay = RelayServer("127.0.0.1", 0, **base)
        self.socks = []

    async def __aenter__(self):
        await self.relay.start()
        self.url = "ws://127.0.0.1:%d/ws" % self.relay.bound_port
        return self

    async def __aexit__(self, *a):
        for c in self.socks:
            try:
                await c.ws.close()
            except Exception:
                pass
        await self.relay.close()

    async def open(self, headers=None):
        ws = await websockets.connect(self.url, max_size=2 ** 24, additional_headers=headers)
        c = C(ws)
        self.socks.append(c)
        return c

    async def create(self, **kw):
        c = await self.open()
        msg = {"type": "create_room", "seat": "red", "client_version": "rt"}
        msg.update(kw)
        await c.send(**msg)
        st = c.state()
        return c, st["code"], st

    async def join(self, code, **kw):
        c = await self.open()
        msg = {"type": "join", "code": code, "client_version": "rt"}
        msg.update(kw)
        await c.send(**msg)
        return c

    def room(self, code):
        return self.relay.rooms.get(code)


def run(coro):
    asyncio.run(coro)
    broken = [n for n, b in RESULTS if b]
    print("SUMMARY: %d probes, %d broke: %s" % (len(RESULTS), len(broken), broken))
