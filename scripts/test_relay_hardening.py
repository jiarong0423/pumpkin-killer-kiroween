#!/usr/bin/env python3
"""Red team 2026-11-26: frames the relay could never send on are refused, ids must match whole, and a client that does not read is cut off instead of stalling the others.
No sockets: runs in any sandbox. usage: python3 -B scripts/test_relay_hardening.py"""
import asyncio
import unittest

import pk_relay


class Parse(unittest.TestCase):
    def test_unsendable_frames_are_refused(self):
        bad = ['{"type":"action","angle":NaN}', '{"type":"action","angle":Infinity}', '{"type":"action","angle":1e999}', '{"type":"action","unit":"\\ud800"}',
               '{"type":"judge","ref":' + "9" * 5000 + '}', "[" * 100000, "not json"]
        for raw in bad:
            with self.assertRaises(ValueError, msg=raw[:60]):
                pk_relay.parse_message(raw)

    def test_ordinary_frames_pass(self):
        self.assertEqual(pk_relay.parse_message('{"type":"ping","name":"\\u5357\\u74dc \\ud83c\\udf83"}')["type"], "ping")

    def test_ids_match_whole(self):
        for pattern, good, bad in ((pk_relay.UNIT_ID, "wizard", "wizard\n"), (pk_relay.WORLD_UNIT, "left_1", "left_1\n"), (pk_relay.ROUND_HASH_FORMAT, "0123abcd", "0123abcd\n")):
            self.assertTrue(pattern.fullmatch(good))
            self.assertIsNone(pattern.fullmatch(bad))


class SlowReader(unittest.TestCase):
    def test_a_client_that_does_not_read_is_cut_off(self):
        class Transport:
            aborted = False

            def abort(self):
                self.aborted = True

        class Stuck:
            def __init__(self):
                self.transport = Transport()

            async def send(self, data):
                await asyncio.sleep(3600)

        async def run():
            old = pk_relay.SEND_TIMEOUT_SECONDS
            pk_relay.SEND_TIMEOUT_SECONDS = 0.1
            try:
                relay, stuck = pk_relay.RelayServer("127.0.0.1", 0), Stuck()
                started = asyncio.get_running_loop().time()
                await asyncio.gather(relay._send(stuck, {"type": "x"}), relay._send(stuck, {"type": "y"}))
                return asyncio.get_running_loop().time() - started, stuck.transport.aborted
            finally:
                pk_relay.SEND_TIMEOUT_SECONDS = old

        seconds, aborted = asyncio.run(run())
        self.assertTrue(aborted)
        self.assertLess(seconds, 1.0)


if __name__ == "__main__":
    unittest.main()
