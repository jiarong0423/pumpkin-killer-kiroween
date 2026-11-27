#!/usr/bin/env python3
"""Pumpkin Killer Streamable HTTP MCP server (G1: remote MCP entry at /mcp).

Loopback-only by default (127.0.0.1:8767); nginx proxies public /mcp and /mcp/health to it.
Implements MCP Streamable HTTP (2025-03-26 / 2025-06-18):
  - POST /mcp        JSON-RPC 2.0 request or batch; `initialize` creates a session and returns `Mcp-Session-Id`
  - DELETE /mcp      Closes the session (leaves any active relay room cleanly)
  - GET /mcp         405 Method Not Allowed (request-response POST transport; no server-initiated SSE)
  - OPTIONS /mcp     CORS preflight
  - GET /mcp/health  Loopback/public health readout (no secrets)

Security:
  - Browser Origin allowlist (`PK_ALLOWED_ORIGINS`, same env var as pk_relay.py); non-browser MCP clients without an Origin header are allowed.
  - SSRF protection: hosted HTTP MCP sessions always connect only to the configured local relay (`PK_MCP_RELAY_URL`, default `ws://127.0.0.1:8765/ws`).
  - Bounded request body (64 KiB), session cap (`PK_MCP_MAX_SESSIONS`, default 64), per-client cap (`PK_MCP_MAX_SESSIONS_PER_IP`, default 8, HTTP 429) and idle reaper (`PK_MCP_IDLE_SECONDS`, default 1800 s).
  - The relay counts hosted seats per remote client: `PK_RELAY_GATEWAY_TOKEN` (shared with the relay, random per start) goes out with `X-PK-Client-Addr`.
"""
import argparse
import http.server
import json
import os
import secrets
import signal
import socketserver
import sys
import threading
import time
from typing import Any, Dict, Optional, Set

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import mcp_stdio_server as mcp  # noqa: E402

MAX_BODY_BYTES = 64 * 1024
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8767
DEFAULT_RELAY_URL = "ws://127.0.0.1:8765/ws"
DEFAULT_MAX_SESSIONS = 64
DEFAULT_IDLE_SECONDS = 1800.0
DEFAULT_SEAT_IDLE_SECONDS = 180.0   # an agent seat that holds a page judge and has made no call for this long leaves its room, so the place is free again
DEFAULT_MAX_SESSIONS_PER_IP = 8


def parse_allowed_origins(raw: str) -> Set[str]:
    return {item.strip().rstrip("/") for item in (raw or "").split(",") if item.strip()}


class ClientLimit(Exception):
    """One client already holds the most sessions it may."""


class SessionEntry:
    def __init__(self, session_id: str, server: mcp.McpServer, client_ip: str = "") -> None:
        self.session_id = session_id
        self.server = server
        self.client_ip = client_ip
        self.lock = threading.Lock()
        self.last_used = time.monotonic()


class McpHttpServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 128

    def __init__(self, server_address, handler_cls, *,
                 relay_url: str = DEFAULT_RELAY_URL,
                 allowed_origins: Optional[Set[str]] = None,
                 max_sessions: int = DEFAULT_MAX_SESSIONS,
                 idle_seconds: float = DEFAULT_IDLE_SECONDS,
                 page_judge_mode: str = "off",
                 page_speed: float = 1.0,
                 max_sessions_per_ip: int = DEFAULT_MAX_SESSIONS_PER_IP,
                 trust_proxy: bool = False,
                 gateway_token: str = "") -> None:
        super().__init__(server_address, handler_cls)
        self.max_sessions_per_ip = max(1, int(max_sessions_per_ip))   # MCP-RISK-B: one client cannot fill the whole session table
        self.trust_proxy = bool(trust_proxy)                           # same meaning as PK_RELAY_TRUST_PROXY: take CF-Connecting-IP
        self.gateway_token = gateway_token or ""                       # MCP-RISK-A: lets the relay count seats per remote client
        self.relay_url = relay_url
        self.allowed_origins: Set[str] = set(allowed_origins or ())
        self.max_sessions = max(1, int(max_sessions))
        self.idle_seconds = max(5.0, float(idle_seconds))
        self.page_judge_mode = page_judge_mode
        self.page_speed = page_speed
        self._sessions_lock = threading.Lock()
        self._sessions: Dict[str, SessionEntry] = {}
        self._stop_reaper = threading.Event()
        self._reaper = threading.Thread(target=self._reap_loop, name="pk-mcp-reaper", daemon=True)
        self._reaper.start()

    def session_count(self) -> int:
        with self._sessions_lock:
            return len(self._sessions)

    def create_session(self, client_ip: str = "") -> Optional[SessionEntry]:
        """None = the table is full (503); raises ClientLimit when this client already holds its share (429)."""
        self._reap_expired()
        with self._sessions_lock:
            if len(self._sessions) >= self.max_sessions:
                return None
            if client_ip and sum(1 for e in self._sessions.values() if e.client_ip == client_ip) >= self.max_sessions_per_ip:
                raise ClientLimit(client_ip)
            sid = secrets.token_hex(16)
            game_session = mcp.Session(seed=1, seat="white", turn_seconds=0, human_turn_seconds=0)
            rpc_server = mcp.McpServer(
                game_session,
                enable_room_tools=True,
                default_relay_url=self.relay_url,
                allow_custom_relay=False,
                page_judge_mode=self.page_judge_mode,
                page_speed=self.page_speed,
                client_addr=client_ip or None,
                gateway_token=self.gateway_token or None,
            )
            entry = SessionEntry(sid, rpc_server, client_ip)
            self._sessions[sid] = entry
            return entry

    def get_session(self, session_id: str) -> Optional[SessionEntry]:
        with self._sessions_lock:
            entry = self._sessions.get(session_id)
            if entry is not None:
                entry.last_used = time.monotonic()
            return entry

    def delete_session(self, session_id: str) -> bool:
        with self._sessions_lock:
            entry = self._sessions.pop(session_id, None)
        if entry is None:
            return False
        try:
            entry.server.close()
        except Exception:
            pass
        return True

    def close_all_sessions(self) -> None:
        self._stop_reaper.set()
        with self._sessions_lock:
            entries = list(self._sessions.values())
            self._sessions.clear()
        for entry in entries:
            try:
                entry.server.close()
            except Exception:
                pass

    def _reap_expired(self) -> None:
        cutoff = time.monotonic() - self.idle_seconds
        expired = []
        with self._sessions_lock:
            for sid, entry in list(self._sessions.items()):
                if entry.last_used < cutoff:
                    expired.append(self._sessions.pop(sid))
        for entry in expired:
            try:
                entry.server.close()
            except Exception:
                pass
        self._release_idle_seats()

    def _release_idle_seats(self) -> None:
        """Take a silent agent out of its room (the MCP session stays; it may join again). A request in progress is never interrupted."""
        try:
            seat_idle = float(os.environ.get("PK_MCP_SEAT_IDLE_SECONDS", str(DEFAULT_SEAT_IDLE_SECONDS)))
        except ValueError:
            seat_idle = DEFAULT_SEAT_IDLE_SECONDS
        if seat_idle <= 0:
            return
        cutoff = time.monotonic() - seat_idle
        with self._sessions_lock:
            silent = [e for e in self._sessions.values() if e.last_used < cutoff and getattr(getattr(e.server, "relay", None), "_slot_held", False)]
        for entry in silent:
            if not entry.lock.acquire(blocking=False):
                continue
            try:
                if entry.last_used < cutoff:
                    entry.server._tool_leave_room({})
            except Exception as exc:
                sys.stderr.write("idle seat release failed: %r\n" % (exc,))
            finally:
                entry.lock.release()

    def _reap_loop(self) -> None:
        while not self._stop_reaper.wait(30.0):
            self._reap_expired()


class McpHttpHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server: McpHttpServer

    def log_message(self, fmt: str, *args: Any) -> None:
        pass

    def _path(self) -> str:
        return self.path.split("?", 1)[0]

    def _client_ip(self) -> str:
        """The remote client: CF-Connecting-IP only when the proxy is trusted (PK_RELAY_TRUST_PROXY=1), else the X-Real-IP nginx
        overwrites on every request, else the socket peer. The gateway listens on loopback only, so the peer is nginx itself."""
        if self.server.trust_proxy:
            value = (self.headers.get("CF-Connecting-IP") or "").strip()
            if value:
                return value[:64]
        value = (self.headers.get("X-Real-IP") or "").strip()
        if value:
            return value[:64]
        return str(self.client_address[0])[:64]

    def _check_origin(self) -> bool:
        origin = (self.headers.get("Origin") or "").strip().rstrip("/")
        if not origin:
            return True  # Non-browser MCP clients (Claude Code, Kiro, Cursor, curl) do not send Origin.
        if not self.server.allowed_origins:
            return True
        return origin in self.server.allowed_origins

    def _cors_headers(self) -> Dict[str, str]:
        origin = (self.headers.get("Origin") or "").strip().rstrip("/")
        hdrs: Dict[str, str] = {
            "Cache-Control": "no-store",
            "Vary": "Origin",
        }
        if origin and (not self.server.allowed_origins or origin in self.server.allowed_origins):
            hdrs["Access-Control-Allow-Origin"] = origin
            hdrs["Access-Control-Allow-Methods"] = "POST, DELETE, OPTIONS"
            hdrs["Access-Control-Allow-Headers"] = "Content-Type, Accept, Mcp-Session-Id, MCP-Protocol-Version"
            hdrs["Access-Control-Expose-Headers"] = "Mcp-Session-Id"
        return hdrs

    def _send_json(self, status: int, payload: Any, extra_headers: Optional[Dict[str, str]] = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for k, v in self._cors_headers().items():
            self.send_header(k, v)
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _send_empty(self, status: int, extra_headers: Optional[Dict[str, str]] = None) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        for k, v in self._cors_headers().items():
            self.send_header(k, v)
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()

    def do_OPTIONS(self) -> None:
        if self._path() != "/mcp":
            self._send_empty(404)
            return
        if not self._check_origin():
            self._send_json(403, {"error": "origin_not_allowed"})
            return
        self._send_empty(204)

    def do_GET(self) -> None:
        path = self._path()
        if path == "/mcp/health":
            self._send_json(200, {
                "status": "ok",
                "transport": "streamable-http",
                "server": mcp.SERVER_NAME,
                "version": mcp.SERVER_VERSION,
                "sessions": self.server.session_count(),
                "max_sessions": self.server.max_sessions,
            })
            return
        if path == "/mcp":
            self._send_json(405, {"error": "method_not_allowed", "detail": "Use POST /mcp for JSON-RPC requests"},
                            {"Allow": "POST, DELETE, OPTIONS"})
            return
        self._send_json(404, {"error": "not_found"})

    def do_DELETE(self) -> None:
        if self._path() != "/mcp":
            self._send_json(404, {"error": "not_found"})
            return
        if not self._check_origin():
            self._send_json(403, {"error": "origin_not_allowed"})
            return
        sid = (self.headers.get("Mcp-Session-Id") or "").strip()
        if not sid:
            self._send_json(400, {"error": "missing_session_id"})
            return
        if not self.server.delete_session(sid):
            self._send_json(404, {"error": "unknown_session"})
            return
        self._send_json(200, {"ok": True, "closed": True})

    def do_POST(self) -> None:
        if self._path() != "/mcp":
            self._send_json(404, {"error": "not_found"})
            return
        if not self._check_origin():
            self._send_json(403, {"error": "origin_not_allowed"})
            return
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            self._send_json(400, mcp._rpc_error(None, -32700, "Invalid Content-Length"))
            return
        if length <= 0 or length > MAX_BODY_BYTES:
            self._send_json(413 if length > MAX_BODY_BYTES else 400,
                            mcp._rpc_error(None, -32600, "Request body empty or too large"))
            return
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):   # RecursionError: arrays nested thousands deep inside the size limit
            self._send_json(400, mcp._rpc_error(None, -32700, "Parse error"))
            return

        is_batch = isinstance(payload, list)
        messages = payload if is_batch else [payload]
        if not messages:
            self._send_json(400, mcp._rpc_error(None, -32600, "Empty batch"))
            return

        sid = (self.headers.get("Mcp-Session-Id") or "").strip()
        is_init = (not is_batch) and isinstance(payload, dict) and payload.get("method") == "initialize"
        extra_headers: Dict[str, str] = {}

        if is_init and not sid:
            try:
                entry = self.server.create_session(self._client_ip())
            except ClientLimit:
                self._send_json(429, mcp._rpc_error(payload.get("id"), -32000, "Too many sessions from this client; close one (DELETE /mcp) or wait for idle expiry"),
                                {"Retry-After": "30"})
                return
            if entry is None:
                self._send_json(503, mcp._rpc_error(payload.get("id"), -32000, "Server session limit reached"))
                return
            extra_headers["Mcp-Session-Id"] = entry.session_id
        else:
            if not sid:
                self._send_json(400, mcp._rpc_error(
                    payload.get("id") if isinstance(payload, dict) else None,
                    -32600, "Missing Mcp-Session-Id header; call initialize first",
                ))
                return
            entry = self.server.get_session(sid)
            if entry is None:
                self._send_json(404, mcp._rpc_error(
                    payload.get("id") if isinstance(payload, dict) else None,
                    -32001, "Unknown or expired Mcp-Session-Id; re-initialize",
                ))
                return
            extra_headers["Mcp-Session-Id"] = entry.session_id

        responses = []
        with entry.lock:
            entry.last_used = time.monotonic()
            for msg in messages:
                resp = entry.server.handle_message(msg)
                if resp is not None:
                    responses.append(resp)
            entry.last_used = time.monotonic()

        if not responses:
            self._send_empty(202, extra_headers)
            return
        self._send_json(200, responses if is_batch else responses[0], extra_headers)


def create_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                  relay_url: str = DEFAULT_RELAY_URL,
                  allowed_origins: Optional[Set[str]] = None,
                  max_sessions: int = DEFAULT_MAX_SESSIONS,
                  idle_seconds: float = DEFAULT_IDLE_SECONDS,
                  page_judge_mode: str = "off",
                  page_speed: float = 1.0,
                  max_sessions_per_ip: int = DEFAULT_MAX_SESSIONS_PER_IP,
                  trust_proxy: bool = False,
                  gateway_token: str = "") -> McpHttpServer:
    return McpHttpServer(
        (host, port),
        McpHttpHandler,
        relay_url=relay_url,
        allowed_origins=allowed_origins,
        max_sessions=max_sessions,
        idle_seconds=idle_seconds,
        page_judge_mode=page_judge_mode,
        page_speed=page_speed,
        max_sessions_per_ip=max_sessions_per_ip,
        trust_proxy=trust_proxy,
        gateway_token=gateway_token,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("PK_MCP_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PK_MCP_PORT", str(DEFAULT_PORT))))
    parser.add_argument("--relay", default=os.environ.get("PK_MCP_RELAY_URL", DEFAULT_RELAY_URL))
    parser.add_argument("--allowed-origins", default=os.environ.get("PK_ALLOWED_ORIGINS", ""))
    parser.add_argument("--max-sessions", type=int, default=int(os.environ.get("PK_MCP_MAX_SESSIONS", str(DEFAULT_MAX_SESSIONS))))
    parser.add_argument("--idle-seconds", type=float, default=float(os.environ.get("PK_MCP_IDLE_SECONDS", str(DEFAULT_IDLE_SECONDS))))
    parser.add_argument("--page-judge", default=os.environ.get("PK_MCP_PAGE_JUDGE", "on"), choices=["off", "auto", "on"])
    parser.add_argument("--max-sessions-per-ip", type=int, default=int(os.environ.get("PK_MCP_MAX_SESSIONS_PER_IP", str(DEFAULT_MAX_SESSIONS_PER_IP))))
    args = parser.parse_args()
    retired = mcp.retired_judge_path(args.page_judge, True)
    if retired:
        parser.error(retired)

    srv = create_server(
        host=args.host,
        port=args.port,
        relay_url=args.relay,
        allowed_origins=parse_allowed_origins(args.allowed_origins),
        max_sessions=args.max_sessions,
        idle_seconds=args.idle_seconds,
        page_judge_mode=args.page_judge,
        max_sessions_per_ip=args.max_sessions_per_ip,
        trust_proxy=os.environ.get("PK_RELAY_TRUST_PROXY", "") == "1",
        gateway_token=os.environ.get("PK_RELAY_GATEWAY_TOKEN", ""),
    )

    def _handle_signal(_sig, _frame):
        threading.Thread(target=srv.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)
    print("pk_mcp_http listening on http://%s:%d/mcp (relay=%s)" % (args.host, srv.server_address[1], args.relay), flush=True)
    try:
        srv.serve_forever()
    finally:
        srv.server_close()
        srv.close_all_sessions()
    return 0


if __name__ == "__main__":
    sys.exit(main())
