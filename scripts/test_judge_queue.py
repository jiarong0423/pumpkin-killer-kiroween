#!/usr/bin/env python3
"""Agent seats: a short first-come queue when every page judge is in use, a clear refusal with a retry time, and silent seats released.
No sockets. usage: python3 -B scripts/test_judge_queue.py"""
import os
import threading
import time
import unittest

import mcp_stdio_server as srv
import pk_mcp_http


class Queue(unittest.TestCase):
    def setUp(self):
        os.environ.update({"PK_MCP_MAX_PAGE_JUDGES": "1", "PK_MCP_JUDGE_QUEUE": "2", "PK_MCP_JUDGE_WAIT": "2"})
        srv._PAGE_JUDGE_ACTIVE = 0
        del srv._PAGE_JUDGE_QUEUE[:]

    def tearDown(self):
        for name in ("PK_MCP_MAX_PAGE_JUDGES", "PK_MCP_JUDGE_QUEUE", "PK_MCP_JUDGE_WAIT"):
            os.environ.pop(name, None)
        srv._PAGE_JUDGE_ACTIVE = 0

    def release(self):
        holder = object.__new__(srv.PageJudgeRelay)
        holder._slot_held = True
        holder._release_slot()

    def test_waiters_are_served_in_order_and_the_queue_is_bounded(self):
        self.assertTrue(srv._take_judge_slot())
        served = []
        threads = []
        for name in ("first", "second"):
            threads.append(threading.Thread(target=lambda n=name: served.append((n, srv._take_judge_slot()))))
            threads[-1].start()
            time.sleep(0.1)
        started = time.monotonic()
        self.assertFalse(srv._take_judge_slot(), "a full queue refuses at once")
        self.assertLess(time.monotonic() - started, 0.5)
        self.release()
        time.sleep(0.2)
        self.release()
        for thread in threads:
            thread.join(5)
        self.assertEqual(served, [("first", True), ("second", True)])

    def test_a_wait_that_runs_out_is_refused_and_leaves_no_ticket(self):
        os.environ["PK_MCP_JUDGE_WAIT"] = "0.2"
        self.assertTrue(srv._take_judge_slot())
        self.assertFalse(srv._take_judge_slot())
        self.assertEqual(srv._PAGE_JUDGE_QUEUE, [])
        self.assertEqual(srv._PAGE_JUDGE_ACTIVE, 1)


class IdleSeats(unittest.TestCase):
    def test_only_a_silent_seat_that_holds_a_judge_is_released(self):
        server = object.__new__(pk_mcp_http.McpHttpServer)
        server._sessions_lock = threading.Lock()
        left = []

        def entry(name, age, holds):
            relay = type("R", (), {"_slot_held": holds})()
            fake = type("S", (), {"relay": relay, "_tool_leave_room": lambda self, a, n=name: left.append(n)})()
            made = pk_mcp_http.SessionEntry(name, fake)
            made.last_used = time.monotonic() - age
            return made
        server._sessions = {n: entry(n, a, h) for n, a, h in (("silent", 400, True), ("active", 5, True), ("watcher", 400, False))}
        busy = entry("busy", 400, True)
        busy.lock.acquire()
        server._sessions["busy"] = busy
        server._release_idle_seats()
        self.assertEqual(left, ["silent"])


if __name__ == "__main__":
    unittest.main()
