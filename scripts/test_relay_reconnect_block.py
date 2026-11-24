#!/usr/bin/env python3
"""Reconnect-storm and bad-resume block on the relay (FLOOD-1, 2026-11-25).
Needs localhost sockets (listed with the other socket tests in run_full_suite.sh).
Checks: (1) a client address that opens more connections than the window allows is blocked for the block time, and the block is answered at once with
`temporarily_blocked` and a close, before any room state exists; (2) the limit is per address, so a different address is not affected (the address is taken
from CF-Connecting-IP when the relay trusts the proxy); (3) a burst of bad `resume` tokens from one address blocks it the same way; (4) a block ends after its
time and a repeat offender is blocked for twice as long; (5) normal play inside the limits (a few reconnects) is never blocked; (6) the tracking tables stay
bounded when many different addresses connect."""
import asyncio, json, os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import websockets
from pk_relay import RelayServer


async def first_message(url, headers=None, timeout=2.0):
    """Open one socket, return (first parsed message or None, close code or None)."""
    kwargs = {"max_size": 16 * 1024}
    if headers:
        kwargs["additional_headers"] = headers
    ws = await websockets.connect(url, **kwargs)
    try:
        await ws.send(json.dumps({"type": "create_room", "solo": True}))
        raw = await asyncio.wait_for(ws.recv(), timeout)
        return json.loads(raw), None
    except websockets.ConnectionClosed as closed:
        return None, closed.code
    except asyncio.TimeoutError:
        return None, "timeout"
    finally:
        await ws.close()


async def blocked_probe(url, headers=None):
    """True when the relay answers a fresh connection with temporarily_blocked."""
    ws = await websockets.connect(url, max_size=16 * 1024, **({"additional_headers": headers} if headers else {}))
    try:
        raw = await asyncio.wait_for(ws.recv(), 2.0)
        return json.loads(raw).get("code") == "temporarily_blocked"
    except (websockets.ConnectionClosed, asyncio.TimeoutError):
        return False
    finally:
        await ws.close()


class ReconnectBlockTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.relay = RelayServer("127.0.0.1", 0, max_connects_per_min=6, max_bad_resumes_per_min=4,
                                 block_seconds=0.6, max_per_addr=50, trust_proxy=True, max_rooms=500, max_tracked_addrs=256)
        await self.relay.start()
        self.url = "ws://127.0.0.1:%d/ws" % self.relay.bound_port

    async def asyncTearDown(self):
        await self.relay.close()

    async def test_connection_churn_from_one_address_is_blocked_and_answered_at_once(self):
        headers = {"CF-Connecting-IP": "203.0.113.7"}
        for _ in range(6):
            await first_message(self.url, headers)          # inside the window: allowed
        for _ in range(3):
            await first_message(self.url, headers)
        self.assertTrue(await blocked_probe(self.url, headers), "the 10th connection in a minute must be answered with temporarily_blocked")
        self.assertEqual(len(self.relay.rooms) <= 9, True)

    async def test_the_limit_is_per_address(self):
        noisy = {"CF-Connecting-IP": "203.0.113.8"}
        calm = {"CF-Connecting-IP": "203.0.113.9"}
        for _ in range(12):
            await first_message(self.url, noisy)
        self.assertTrue(await blocked_probe(self.url, noisy))
        message, closed = await first_message(self.url, calm)
        self.assertIsNotNone(message, "another address must still be served (closed=%r)" % (closed,))

    async def test_bad_resume_tokens_in_a_loop_block_the_address(self):
        headers = {"CF-Connecting-IP": "203.0.113.10"}
        for _ in range(5):
            ws = await websockets.connect(self.url, max_size=16 * 1024, additional_headers=headers)
            await ws.send(json.dumps({"type": "resume", "seat_token": "no-such-token", "last_seq": 0}))
            try:
                await asyncio.wait_for(ws.recv(), 1.0)
            except (websockets.ConnectionClosed, asyncio.TimeoutError):
                pass
            await ws.close()
        self.assertTrue(await blocked_probe(self.url, headers), "5 bad resumes in a minute must block the address")

    async def test_a_block_ends_and_a_repeat_offender_waits_twice_as_long(self):
        headers = {"CF-Connecting-IP": "203.0.113.11"}
        for _ in range(8):
            await first_message(self.url, headers)
        self.assertTrue(await blocked_probe(self.url, headers))
        await asyncio.sleep(0.8)                             # first block was 0.6 s
        message, _ = await first_message(self.url, headers)
        self.assertIsNotNone(message, "the block must end after block_seconds")
        for _ in range(8):
            await first_message(self.url, headers)
        self.assertTrue(await blocked_probe(self.url, headers))
        await asyncio.sleep(0.8)                             # second block is 1.2 s, so still blocked here
        self.assertTrue(await blocked_probe(self.url, headers), "a repeat offender must wait longer than the first block")

    async def test_normal_reconnects_inside_the_limits_are_never_blocked(self):
        headers = {"CF-Connecting-IP": "203.0.113.12"}
        for _ in range(5):
            message, closed = await first_message(self.url, headers)
            self.assertIsNotNone(message, "a normal player must not be blocked (closed=%r)" % (closed,))

    async def test_tracking_tables_stay_bounded(self):
        for index in range(300):
            self.relay.note_connect_attempt("198.51.100.%d" % (index % 250) + "-%d" % index)
        self.assertLessEqual(len(self.relay.connect_times), 256)
        self.assertLessEqual(len(self.relay.blocked_until), 256)


class EnvFoolproofTests(unittest.TestCase):
    """A typo in a Coolify variable must not crash the relay at start-up (a crash loop takes the whole page down): bad or negative values fall back to the default."""
    def read(self, name, value):
        import subprocess
        env = dict(os.environ, **{name: value})
        out = subprocess.run([sys.executable, "-B", "-c", "import pk_relay as r; print(r.%s)" % self.attr[name]], cwd=os.path.dirname(os.path.abspath(__file__)),
                             env=env, capture_output=True, text=True)
        return out.returncode, out.stdout.strip(), out.stderr.strip()[-200:]

    attr = {"PK_RELAY_MAX_PER_ADDR": "MAX_CONNECTIONS_PER_ADDR", "PK_RELAY_MAX_CONNECTS_PER_MIN": "MAX_CONNECTS_PER_MIN",
            "PK_RELAY_BLOCK_SECONDS": "BLOCK_SECONDS", "PK_RELAY_MAX_ROOMS": "MAX_ROOMS"}

    def test_garbage_and_negative_values_fall_back_to_the_default(self):
        for name, default in (("PK_RELAY_MAX_PER_ADDR", "8"), ("PK_RELAY_MAX_CONNECTS_PER_MIN", "40"), ("PK_RELAY_BLOCK_SECONDS", "300.0"), ("PK_RELAY_MAX_ROOMS", "200")):
            for bad in ("sixteen", "", "-5", "nan"):
                code, out, err = self.read(name, bad)
                self.assertEqual((code, out), (0, default), "%s=%r gave code %s out %r %s" % (name, bad, code, out, err))

    def test_a_good_value_is_used(self):
        self.assertEqual(self.read("PK_RELAY_MAX_PER_ADDR", "16")[:2], (0, "16"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
