#!/usr/bin/env python3
"""Smoke-check a deployed Pumpkin Killer page and same-origin room relay."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import socket
import ssl
import struct
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

TITLE_RE = re.compile(rb"<title[^>]*>\s*Pumpkin Killer\s*</title>", re.IGNORECASE)
IMAGE_PATH = "assets/avatars/avatar_skeleton.png"
MAX_FRAME_BYTES = 16 * 1024


class WebSocketError(RuntimeError):
    """The relay did not complete the small smoke-test exchange."""

# Cloudflare blocks the default Python-urllib agent and a missing one (403, error 1010).
USER_AGENT = "Mozilla/5.0 (compatible; PumpkinKillerSmoke/1.0)"


class WebSocketClient:
    """Minimal standard-library WebSocket client for the relay smoke exchange."""

    def __init__(self, url: str, timeout: float) -> None:
        parsed = urlsplit(url)
        if parsed.scheme not in {"ws", "wss"} or not parsed.hostname or parsed.username or parsed.password:
            raise WebSocketError("invalid relay URL")
        self.parsed = parsed
        self.timeout = timeout
        self.socket: socket.socket | ssl.SSLSocket | None = None

    def connect(self) -> None:
        port = self.parsed.port or (443 if self.parsed.scheme == "wss" else 80)
        raw_socket = socket.create_connection((self.parsed.hostname, port), self.timeout)
        raw_socket.settimeout(self.timeout)
        if self.parsed.scheme == "wss":
            context = ssl.create_default_context()
            self.socket = context.wrap_socket(raw_socket, server_hostname=self.parsed.hostname)
        else:
            self.socket = raw_socket
        path = self.parsed.path or "/"
        if self.parsed.query:
            path += "?" + self.parsed.query
        host = self.parsed.hostname
        if self.parsed.port and self.parsed.port not in {80, 443}:
            host += f":{self.parsed.port}"
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\n"
            "Connection: Upgrade\r\nSec-WebSocket-Version: 13\r\n"
            f"User-Agent: {USER_AGENT}\r\n"
            f"Sec-WebSocket-Key: {key}\r\n\r\n"
        ).encode("ascii")
        self._send_raw(request)
        status, headers = self._read_headers()
        if status != 101 or headers.get("upgrade", "").lower() != "websocket":
            raise WebSocketError("relay WebSocket handshake failed")

    def send_json(self, message: dict[str, object]) -> None:
        self._send_frame(0x1, json.dumps(message, separators=(",", ":")).encode("utf-8"))

    def receive_json(self) -> dict[str, object]:
        for _ in range(4):
            opcode, payload = self._receive_frame()
            if opcode == 0x1:
                try:
                    message = json.loads(payload.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as error:
                    raise WebSocketError("relay returned invalid JSON") from error
                if not isinstance(message, dict):
                    raise WebSocketError("relay returned a non-object message")
                return message
            if opcode == 0x9:
                self._send_frame(0xA, payload)
                continue
            if opcode == 0x8:
                raise WebSocketError("relay closed the smoke connection")
        raise WebSocketError("relay did not send a text message")

    def close(self) -> None:
        if self.socket is None:
            return
        try:
            self._send_frame(0x8, b"")
        except (OSError, WebSocketError):
            pass
        try:
            self.socket.close()
        finally:
            self.socket = None

    def _send_raw(self, data: bytes) -> None:
        if self.socket is None:
            raise WebSocketError("relay socket is unavailable")
        self.socket.sendall(data)

    def _read_exact(self, size: int) -> bytes:
        if self.socket is None:
            raise WebSocketError("relay socket is unavailable")
        chunks: list[bytes] = []
        remaining = size
        while remaining:
            chunk = self.socket.recv(remaining)
            if not chunk:
                raise WebSocketError("relay closed the connection")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def _read_headers(self) -> tuple[int, dict[str, str]]:
        data = bytearray()
        while not data.endswith(b"\r\n\r\n"):
            if len(data) >= 8192:
                raise WebSocketError("relay handshake headers are too large")
            data.extend(self._read_exact(1))
        lines = data.decode("iso-8859-1").split("\r\n")
        match = re.fullmatch(r"HTTP/1\.1\s+(\d{3}).*", lines[0])
        if not match:
            raise WebSocketError("relay returned an invalid HTTP status")
        headers: dict[str, str] = {}
        for line in lines[1:]:
            if not line:
                continue
            name, separator, value = line.partition(":")
            if not separator:
                raise WebSocketError("relay returned an invalid HTTP header")
            headers[name.lower()] = value.strip()
        return int(match.group(1)), headers

    def _send_frame(self, opcode: int, payload: bytes) -> None:
        if len(payload) > MAX_FRAME_BYTES:
            raise WebSocketError("smoke frame is too large")
        mask = os.urandom(4)
        size = len(payload)
        if size < 126:
            header = bytes((0x80 | opcode, 0x80 | size))
        else:
            header = bytes((0x80 | opcode, 0x80 | 126)) + struct.pack("!H", size)
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        self._send_raw(header + mask + masked)

    def _receive_frame(self) -> tuple[int, bytes]:
        first, second = self._read_exact(2)
        opcode = first & 0x0F
        masked = bool(second & 0x80)
        size = second & 0x7F
        if size == 126:
            size = struct.unpack("!H", self._read_exact(2))[0]
        elif size == 127:
            size = struct.unpack("!Q", self._read_exact(8))[0]
        if size > MAX_FRAME_BYTES:
            raise WebSocketError("relay frame is too large")
        mask = self._read_exact(4) if masked else b""
        payload = self._read_exact(size)
        if masked:
            payload = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        return opcode, payload


def fetch(url: str, timeout: float) -> tuple[str, bytes]:
    try:
        with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=timeout) as response:  # nosec B310: the owner supplies the target URL
            return str(response.status), response.read()
    except HTTPError as error:
        return str(error.code), error.read()
    except (URLError, OSError, ValueError):
        return "ERROR", b""


def relay_url(base_url: str, timeout: float = 10) -> str:
    """Read the hosted relay config rather than assuming a proxy path."""
    parsed = urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("base URL must be an http(s) origin")
    _, source = fetch(urljoin(base_url.rstrip("/") + "/", "relay-config.js"), timeout)
    text = source.decode("utf-8", "replace")
    if 'location.origin.replace(/^http/, "ws") + "/relay"' in text:
        scheme = "wss" if parsed.scheme == "https" else "ws"
        return urlunsplit((scheme, parsed.netloc, "/relay", "", ""))
    match = re.search(r'window\\.PK_RELAY\\s*=\\s*["\\\']([^"\\\']+)["\\\']', text)
    if not match:
        raise ValueError("relay-config.js has no supported PK_RELAY value")
    configured = match.group(1)
    value = urlsplit(configured)
    if value.scheme not in {"ws", "wss"} or not value.hostname:
        raise ValueError("relay-config.js has an invalid PK_RELAY value")
    return configured


def relay_room_check(base_url: str, timeout: float) -> tuple[bool, int]:
    """Create a room with one client and join it with another through /relay."""
    clients: list[WebSocketClient] = []
    try:
        first = WebSocketClient(relay_url(base_url), timeout)
        clients.append(first)
        first.connect()
        first.send_json({"type": "create_room", "seat": "red", "solo": False, "client_version": "smoke"})
        room = first.receive_json()
        code = room.get("code")
        if room.get("type") != "room_state" or not isinstance(code, str) or not code:
            raise WebSocketError("relay did not create a room")

        second = WebSocketClient(relay_url(base_url), timeout)
        clients.append(second)
        second.connect()
        second.send_json({"type": "join", "code": code, "seat": "white", "client_version": "smoke"})
        joined = second.receive_json()
        if joined.get("type") != "room_state" or joined.get("code") != code:
            raise WebSocketError("relay did not join the room")
        return True, 2
    except (OSError, ValueError, WebSocketError):
        return False, 0
    finally:
        for client in clients:
            client.close()


def config_is_valid(path: Path) -> bool:
    """Check the Nginx directives needed for the one-path relay proxy."""
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return False
    required = (
        "map $http_upgrade $pk_relay_path",
        "location = /relay",
        "proxy_pass http://127.0.0.1:8765$pk_relay_path;",
        "proxy_http_version 1.1;",
        "proxy_set_header Upgrade $http_upgrade;",
        'proxy_set_header Connection "upgrade";',
        "proxy_read_timeout 3600s;",
    )
    return all(value in source for value in required)


def check(base_url: str, timeout: float) -> int:
    """Print deployment check results and return zero only when all pass."""
    try:
        relay_address = relay_url(base_url)
    except ValueError:
        print("BASE_URL status=ERROR")
        print("OVERALL FAIL")
        return 1
    base = base_url.rstrip("/") + "/"
    index_status, index_body = fetch(base, timeout)
    sw_status, _ = fetch(urljoin(base, "sw.js"), timeout)
    manifest_status, _ = fetch(urljoin(base, "manifest.webmanifest"), timeout)
    image_status, _ = fetch(urljoin(base, IMAGE_PATH), timeout)
    health_status, health_body = fetch(urljoin(base, "relay"), timeout)
    room_ok, clients = relay_room_check(base, timeout)

    index_ok = index_status == "200" and bool(TITLE_RE.search(index_body))
    health_ok = health_status == "200" and health_body.strip() == b"ok"
    overall = all((index_ok, sw_status == "200", manifest_status == "200", image_status == "200", health_ok, room_ok))

    print(f"INDEX status={index_status} title={'yes' if index_ok else 'no'}")
    print(f"SERVICE_WORKER status={sw_status}")
    print(f"MANIFEST status={manifest_status}")
    print(f"IMAGE status={image_status}")
    print(f"RELAY_HEALTH status={health_status} body={'yes' if health_ok else 'no'}")
    print(f"RELAY_WS url={relay_address} room={'yes' if room_ok else 'no'} clients={clients}")
    print(f"OVERALL {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", nargs="?")
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--check-config", type=Path)
    args = parser.parse_args(argv)
    if args.check_config is not None:
        if args.base_url is not None:
            parser.error("base_url cannot be used with --check-config")
        print(f"NGINX_CONFIG {'PASS' if config_is_valid(args.check_config) else 'FAIL'}")
        return 0 if config_is_valid(args.check_config) else 1
    if args.base_url is None:
        parser.error("base_url is required unless --check-config is used")
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    return check(args.base_url, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
