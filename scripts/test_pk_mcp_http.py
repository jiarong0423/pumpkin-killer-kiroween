#!/usr/bin/env python3
"""End-to-end tests for the Streamable HTTP MCP server (scripts/pk_mcp_http.py) and its deployment wiring (G1)."""
import asyncio
import json
import subprocess
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from pk_relay import RelayServer, Room  # noqa: E402


class RelayThread:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.ready = threading.Event()
        self.relay = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        if not self.ready.wait(3):
            raise RuntimeError("relay did not start")

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.relay = RelayServer("127.0.0.1", 0)
        self.loop.run_until_complete(self.relay.start())
        self.ready.set()
        self.loop.run_forever()
        self.loop.run_until_complete(self.relay.close())
        self.loop.close()

    def close(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(2)


def http_req(url, method="GET", body=None, headers=None, timeout=10):
    hdrs = dict(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
        hdrs.setdefault("Accept", "application/json, text/event-stream")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, dict(resp.headers.items()), (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        try:
            parsed = json.loads(raw) if raw.strip() else None
        except ValueError:
            parsed = raw
        return err.code, dict(err.headers.items()), parsed


def header_ci(headers, name):
    low = name.lower()
    for k, v in headers.items():
        if k.lower() == low:
            return v
    return None


class StreamableHttpMcpTests(unittest.TestCase):
    def setUp(self):
        import pk_mcp_http as mcp_http
        self.mcp_http = mcp_http
        self.relay_host = RelayThread()
        self.relay_url = "ws://127.0.0.1:%d/ws" % self.relay_host.relay.bound_port
        self.server = mcp_http.create_server(
            host="127.0.0.1", port=0, relay_url=self.relay_url,
            allowed_origins={"https://pk.example.com"},
            page_judge_mode="off",
        )
        self.port = self.server.server_address[1]
        self.base = "http://127.0.0.1:%d" % self.port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.server.close_all_sessions()
        self.thread.join(timeout=3)
        self.relay_host.close()

    def _init_session(self):
        status, hdrs, body = http_req(
            self.base + "/mcp", method="POST",
            body={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                  "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}},
        )
        self.assertEqual(status, 200, body)
        sid = header_ci(hdrs, "Mcp-Session-Id")
        self.assertTrue(sid, "missing Mcp-Session-Id header")
        # Send notifications/initialized -> 202 Accepted
        st2, _, _ = http_req(
            self.base + "/mcp", method="POST",
            headers={"Mcp-Session-Id": sid},
            body={"jsonrpc": "2.0", "method": "notifications/initialized"},
        )
        self.assertEqual(st2, 202)
        return sid

    def _call(self, sid, req_id, name, arguments=None):
        status, _, body = http_req(
            self.base + "/mcp", method="POST",
            headers={"Mcp-Session-Id": sid},
            body={"jsonrpc": "2.0", "id": req_id, "method": "tools/call",
                  "params": {"name": name, "arguments": arguments or {}}},
        )
        self.assertEqual(status, 200, body)
        res = body["result"]
        return res["isError"], json.loads(res["content"][0]["text"])

    def test_health_method_guards_origin_and_session_lifecycle(self):
        # Health check
        st, _, data = http_req(self.base + "/mcp/health")
        self.assertEqual(st, 200)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["transport"], "streamable-http")

        # GET /mcp -> 405 Method Not Allowed
        st_get, hdrs_get, _ = http_req(self.base + "/mcp", method="GET")
        self.assertEqual(st_get, 405)
        self.assertIn("POST", header_ci(hdrs_get, "Allow") or "")

        # Disallowed browser Origin -> 403 Forbidden
        st_bad_origin, _, _ = http_req(
            self.base + "/mcp", method="POST",
            headers={"Origin": "https://evil.example"},
            body={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
        self.assertEqual(st_bad_origin, 403)

        # Allowed Origin passes
        st_ok_origin, hdrs_ok, _ = http_req(
            self.base + "/mcp", method="POST",
            headers={"Origin": "https://pk.example.com"},
            body={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
        self.assertEqual(st_ok_origin, 200)
        sid = header_ci(hdrs_ok, "Mcp-Session-Id")
        self.assertTrue(sid)

        # Missing session header on tools/list -> 400
        st_missing, _, _ = http_req(
            self.base + "/mcp", method="POST",
            body={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        )
        self.assertEqual(st_missing, 400)

        # Unknown session header -> 404
        st_unknown, _, _ = http_req(
            self.base + "/mcp", method="POST",
            headers={"Mcp-Session-Id": "deadbeef"},
            body={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        )
        self.assertEqual(st_unknown, 404)

        # DELETE /mcp closes session; subsequent call returns 404
        st_del, _, _ = http_req(self.base + "/mcp", method="DELETE", headers={"Mcp-Session-Id": sid})
        self.assertEqual(st_del, 200)
        st_after, _, _ = http_req(
            self.base + "/mcp", method="POST",
            headers={"Mcp-Session-Id": sid},
            body={"jsonrpc": "2.0", "id": 3, "method": "ping"},
        )
        self.assertEqual(st_after, 404)

    def test_two_http_mcp_sessions_play_a_full_round_via_invite_link(self):
        self.relay_host.relay.rooms["HTTP01"] = Room("HTTP01", scene="church", team_size=1)
        sid_r = self._init_session()
        sid_w = self._init_session()

        # Verify tools/list returns all 10 tools (7 core + 3 room tools)
        st, _, listing = http_req(
            self.base + "/mcp", method="POST",
            headers={"Mcp-Session-Id": sid_r},
            body={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        )
        self.assertEqual(st, 200)
        names = {t["name"] for t in listing["result"]["tools"]}
        self.assertEqual(len(names), 11)
        self.assertTrue({"join_room", "lock_hero", "leave_room", "wait_for_turn"}.issubset(names))

        # Join via bare code and via invite link (with bogus external relay -> SSRF pinned to local relay)
        err, r_join = self._call(sid_r, 3, "join_room", {"room": "HTTP01", "seat": "red", "units": 1})
        self.assertFalse(err, r_join)
        err, w_join = self._call(sid_w, 3, "join_room", {"room": "https://pk.example.com/index.html?room=HTTP01&seat=white&team=1&relay=ws://127.0.0.1:1"})
        self.assertFalse(err, w_join)

        # Wait for turn, play round 1
        err, r_turn = self._call(sid_r, 4, "wait_for_turn", {"timeout_seconds": 3.0})
        self.assertFalse(err, r_turn)
        self.assertEqual(r_turn["status"], "your_turn")
        err, _ = self._call(sid_r, 5, "submit_action", {"unit": "red_1", "round": 1, "action": {"type": "throw", "angle": 54, "power": 40}})
        self.assertFalse(err)
        err, _ = self._call(sid_r, 6, "end_turn", {"round": 1, "phase": "human"})
        self.assertFalse(err)

        err, w_turn = self._call(sid_w, 4, "wait_for_turn", {"timeout_seconds": 3.0})
        self.assertFalse(err, w_turn)
        self.assertEqual(w_turn["status"], "your_turn")
        err, _ = self._call(sid_w, 5, "submit_action", {"unit": "white_1", "round": 1, "action": {"type": "throw", "angle": 54, "power": 40}})
        self.assertFalse(err)
        err, _ = self._call(sid_w, 6, "end_turn", {"round": 1, "phase": "agent"})
        self.assertFalse(err)

        # Both sessions leave cleanly
        err, _ = self._call(sid_r, 7, "leave_room")
        self.assertFalse(err)
        err, _ = self._call(sid_w, 7, "leave_room")
        self.assertFalse(err)


class DeployMcpWiringTests(unittest.TestCase):
    def test_nginx_dockerfile_entrypoint_and_join_helper_wire_mcp(self):
        nginx = (ROOT / "deploy" / "nginx.conf").read_text(encoding="utf-8")
        self.assertIn("location = /mcp", nginx)
        self.assertIn("location = /mcp/health", nginx)
        self.assertIn("127.0.0.1:8767", nginx)

        dockerfile = (ROOT / "deploy" / "Dockerfile.coolify").read_text(encoding="utf-8")
        self.assertIn("pk_mcp_http.py", dockerfile)
        self.assertIn("mcp_stdio_server.py", dockerfile)
        self.assertIn("COPY shared/ /app/shared/", dockerfile)

        entrypoint = (ROOT / "deploy" / "entrypoint.sh").read_text(encoding="utf-8")
        self.assertIn("pk_mcp_http.py", entrypoint)
        sh_check = subprocess.run(["sh", "-n", str(ROOT / "deploy" / "entrypoint.sh")], capture_output=True, text=True)
        self.assertEqual(sh_check.returncode, 0, sh_check.stderr)

        # make_agent_join_config --http prints remote HTTP MCP config
        proc = subprocess.run(
            [sys.executable, "-B", str(HERE / "make_agent_join_config.py"), "--http", "https://pk.example.com/mcp", "--claude-command"],
            cwd=str(ROOT), capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--transport http", proc.stdout)
        self.assertIn("https://pk.example.com/mcp", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
