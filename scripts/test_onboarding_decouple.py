#!/usr/bin/env python3
"""Unit tests for the three decoupled onboarding fixes (2026-11-28):
1. pk_mcp_http.py: reclaim oldest idle room-free session past reclaim age when one IP hits max_sessions_per_ip.
2. mcp_stdio_server.py: end_turn accepts 'red'/'white' aliases for 'human'/'agent' and wait_for_turn includes active_team.
3. index.html: relayJudgeDeparture pauses while document.hidden is true.
No sockets. usage: python3 -B scripts/test_onboarding_decouple.py
"""
import os
import subprocess
import threading
import time
import unittest
from pathlib import Path

import mcp_stdio_server as srv
import pk_mcp_http

REPO = Path(__file__).resolve().parent.parent


class EmptySessionReclaimTest(unittest.TestCase):
    def setUp(self):
        os.environ["PK_MCP_EMPTY_SESSION_RECLAIM_SECONDS"] = "60"

    def tearDown(self):
        os.environ.pop("PK_MCP_EMPTY_SESSION_RECLAIM_SECONDS", None)

    def _make_server(self, max_per_ip=2):
        server = object.__new__(pk_mcp_http.McpHttpServer)
        server._sessions_lock = threading.Lock()
        server._sessions = {}
        server.max_sessions = 10
        server.max_sessions_per_ip = max_per_ip
        server.idle_seconds = 1800.0
        server.relay_url = "ws://127.0.0.1:1/ws"
        server.page_judge_mode = "on"
        server.page_speed = 1.0
        server.gateway_token = ""
        server._reap_expired = lambda: None
        return server

    def _fake_entry(self, sid, ip, age, in_room=False):
        closed = []
        fake_srv = type("S", (), {
            "relay": object() if in_room else None,
            "close": lambda self: closed.append(sid),
        })()
        entry = pk_mcp_http.SessionEntry(sid, fake_srv, ip)
        entry.last_used = time.monotonic() - age
        return entry, closed

    def test_fresh_sessions_still_raise_client_limit(self):
        server = self._make_server(max_per_ip=2)
        e1, _ = self._fake_entry("s1", "1.2.3.4", age=5, in_room=False)
        e2, _ = self._fake_entry("s2", "1.2.3.4", age=10, in_room=False)
        server._sessions = {"s1": e1, "s2": e2}
        with self.assertRaises(pk_mcp_http.ClientLimit):
            server.create_session("1.2.3.4")

    def test_oldest_empty_stale_session_is_reclaimed_not_active_room(self):
        server = self._make_server(max_per_ip=2)
        in_room, closed_room = self._fake_entry("room1", "1.2.3.4", age=500, in_room=True)
        empty_old, closed_old = self._fake_entry("empty1", "1.2.3.4", age=120, in_room=False)
        server._sessions = {"room1": in_room, "empty1": empty_old}
        created = server.create_session("1.2.3.4")
        self.assertIsNotNone(created)
        self.assertIn("room1", server._sessions)
        self.assertNotIn("empty1", server._sessions)
        self.assertTrue(empty_old.closed)
        self.assertEqual(closed_old, ["empty1"])
        self.assertEqual(closed_room, [])

    def test_nan_and_zero_reclaim_env_are_safe(self):
        server = self._make_server(max_per_ip=1)
        empty_old, _ = self._fake_entry("empty1", "1.2.3.4", age=120, in_room=False)
        server._sessions = {"empty1": empty_old}
        os.environ["PK_MCP_EMPTY_SESSION_RECLAIM_SECONDS"] = "nan"
        created = server.create_session("1.2.3.4")
        self.assertIsNotNone(created)
        self.assertTrue(empty_old.closed)

        server2 = self._make_server(max_per_ip=1)
        empty2, _ = self._fake_entry("empty2", "1.2.3.4", age=120, in_room=False)
        server2._sessions = {"empty2": empty2}
        os.environ["PK_MCP_EMPTY_SESSION_RECLAIM_SECONDS"] = "0"
        with self.assertRaises(pk_mcp_http.ClientLimit):
            server2.create_session("1.2.3.4")


class PhaseAliasTest(unittest.TestCase):
    def test_end_turn_schema_enum_includes_red_and_white(self):
        tools = {t["name"]: t for t in srv.TOOLS}
        enum = tools["end_turn"]["inputSchema"]["properties"]["phase"]["enum"]
        self.assertEqual(enum, ["human", "agent", "red", "white"])

    def test_normalize_phase_accepts_red_white_aliases(self):
        self.assertEqual(srv._normalize_phase("human"), "human")
        self.assertEqual(srv._normalize_phase("agent"), "agent")
        self.assertEqual(srv._normalize_phase("red"), "human")
        self.assertEqual(srv._normalize_phase("white"), "agent")
        with self.assertRaises(srv.ToolError):
            srv._normalize_phase("blue")

    def test_session_end_turn_accepts_team_alias(self):
        sess = srv.Session(seed=1, seat="red", turn_seconds=0, human_turn_seconds=0)
        res = sess.call("end_turn", {"round": 1, "phase": "red"}, sess.seat)
        self.assertEqual(res["ended"], "human")
        self.assertEqual(res["phase"], "agent")

    def test_wait_for_turn_includes_active_team(self):
        sess = srv.Session(seed=1, seat="red", turn_seconds=0, human_turn_seconds=0)
        server = srv.McpServer(sess, enable_room_tools=True)
        turn = server._tool_wait_for_turn({"timeout_seconds": 0.2})
        self.assertEqual(turn["status"], "your_turn")
        self.assertEqual(turn["active_team"], "red")


class HiddenTabDepartureTest(unittest.TestCase):
    def test_relay_judge_departure_pauses_while_document_hidden(self):
        script = r"""
const { loadPage } = require('./scripts/page_harness');
const P = loadPage({ team: 1 });
let verdictCalled = 0;
let scheduled = [];
P.context.setTimeout = fn => { scheduled.push(fn); return scheduled.length; };
P.eval('relayPlaying = true; gameOver = null; relayClient = { state: () => ({ seat: "red", owners: {} }) }; projectiles = []; diceRoll = null; relayIncoming = 0; relayInbox = [];');
P.eval('relayDepartureVerdict = () => { globalThis.__verdictCalled = (globalThis.__verdictCalled || 0) + 1; };');
P.context.document.hidden = true;
P.eval('relayJudgeDeparture({ team: "red", seat_id: "red-2" }, relayClient, 0);');
for (let i = 0; i < 12; i++) { const fn = scheduled.shift(); if (fn) fn(); }
if (P.eval('globalThis.__verdictCalled || 0') !== 0) { console.error('FAIL: verdict fired while hidden'); process.exit(1); }
P.context.document.hidden = false;
for (let i = 0; i < 8; i++) { const fn = scheduled.shift(); if (fn) fn(); }
if (P.eval('globalThis.__verdictCalled || 0') !== 1) { console.error('FAIL: verdict did not fire once visible'); process.exit(1); }
console.log('hidden_tab_departure: OK');
"""
        proc = subprocess.run(["node", "-e", script], cwd=str(REPO), capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_relay_judge_departure_bails_out_after_match_gen_change(self):
        script = r"""
const { loadPage } = require('./scripts/page_harness');
const P = loadPage({ team: 1 });
let scheduled = [];
P.context.setTimeout = fn => { scheduled.push(fn); return scheduled.length; };
P.eval('relayPlaying = true; gameOver = null; relayClient = { state: () => ({ seat: "red", owners: {} }) }; projectiles = []; diceRoll = null; relayIncoming = 0; relayInbox = [];');
P.eval('relayDepartureVerdict = () => { globalThis.__verdictCalled = (globalThis.__verdictCalled || 0) + 1; };');
P.context.document.hidden = true;
P.eval('relayJudgeDeparture({ team: "red", seat_id: "red-2" }, relayClient, 0);');
for (let i = 0; i < 3; i++) { const fn = scheduled.shift(); if (fn) fn(); }
P.eval('matchGen++;');
P.context.document.hidden = false;
for (let i = 0; i < 10; i++) { const fn = scheduled.shift(); if (fn) fn(); }
if (P.eval('globalThis.__verdictCalled || 0') !== 0) { console.error('FAIL: stale departure fired in next match'); process.exit(1); }
console.log('match_gen_guard: OK');
"""
        proc = subprocess.run(["node", "-e", script], cwd=str(REPO), capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
