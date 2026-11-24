#!/usr/bin/env python3
"""Tests for the Coolify deployment smoke checker and proxy files."""

from __future__ import annotations

import base64
import http.server
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

from smoke_deployed import check, config_is_valid

ROOT = Path(__file__).resolve().parent.parent


class FakeDeployment(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:
        pass

    def do_GET(self) -> None:
        if self.path == "/relay" and self.headers.get("Upgrade", "").lower() == "websocket":
            self._websocket()
            return
        files = {
            "/": (b"<!doctype html><title>Pumpkin Killer</title>", "text/html"),
            "/relay-config.js": (b'window.PK_RELAY = location.origin.replace(/^http/, "ws") + "/relay";\n', "application/javascript"),
            "/sw.js": (b"self.addEventListener('install', () => {});", "application/javascript"),
            "/manifest.webmanifest": (b'{"name":"Pumpkin Killer"}', "application/manifest+json"),
            "/assets/avatars/avatar_skeleton.png": (b"png", "image/png"),
            "/relay": (b"ok\n", "text/plain"),
        }
        payload = files.get(self.path)
        if payload is None:
            self.send_error(404)
            return
        body, content_type = payload
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _websocket(self) -> None:
        key = self.headers.get("Sec-WebSocket-Key")
        if not key:
            self.send_error(400)
            return
        import hashlib

        accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()).decode("ascii")
        self.send_response_only(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()
        message = self._receive_message()
        if message.get("type") == "create_room":
            response = {"type": "room_state", "code": "ABC123"}
        elif message.get("type") == "join" and message.get("code") == "ABC123":
            response = {"type": "room_state", "code": "ABC123"}
        else:
            response = {"type": "error"}
        self._send_message(response)

    def _receive_message(self) -> dict[str, object]:
        first, second = self.rfile.read(2)
        size = second & 0x7F
        if size == 126:
            size = int.from_bytes(self.rfile.read(2), "big")
        mask = self.rfile.read(4)
        payload = self.rfile.read(size)
        decoded = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        if first & 0x0F != 0x1:
            raise ValueError("expected a text frame")
        return json.loads(decoded.decode("utf-8"))

    def _send_message(self, message: dict[str, object]) -> None:
        payload = json.dumps(message, separators=(",", ":")).encode("utf-8")
        self.wfile.write(bytes((0x81, len(payload))) + payload)
        self.wfile.flush()


class SmokeDeployedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeDeployment)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address[:2]
        self.url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_fake_deployment_passes_every_http_and_websocket_check(self) -> None:
        self.assertEqual(check(self.url, 2), 0)

    def test_rejects_a_proxy_config_without_upgrade_headers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "nginx.conf"
            path.write_text("location = /relay { proxy_pass http://127.0.0.1:8765; }", encoding="utf-8")
            self.assertFalse(config_is_valid(path))

    def test_repository_proxy_config_and_entrypoint_syntax(self) -> None:
        self.assertTrue(config_is_valid(ROOT / "deploy" / "nginx.conf"))
        result = subprocess.run(
            ["sh", "-n", str(ROOT / "deploy" / "entrypoint.sh")],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        dockerfile = (ROOT / "deploy" / "Dockerfile.coolify").read_text(encoding="utf-8")
        self.assertIn("COPY deploy/relay-config.js /usr/share/nginx/html/relay-config.js", dockerfile)
        self.assertIn("COPY scripts/pk_relay.py /app/pk_relay.py", dockerfile)
        self.assertIn("EXPOSE 80", dockerfile)


if __name__ == "__main__":
    unittest.main()
