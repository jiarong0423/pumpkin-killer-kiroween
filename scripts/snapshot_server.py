#!/usr/bin/env python3
"""Tiny local receiver so the page can save screenshots and audits as files (the browser tools cannot write files).

POST http://127.0.0.1:8081/save?name=<file name>   body = raw bytes, or a data: URL for a PNG. Writes into docs/audition/ only.
Binds 127.0.0.1 only, accepts only names matching [A-Za-z0-9_.-]+ ending in .png/.json, caps a body at 8 MB. Logs one line per save.
Run: python3 -B scripts/snapshot_server.py   (stop with Ctrl-C). Not for production: a development helper.
"""
import base64
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "audition")
NAME = re.compile(r"^[A-Za-z0-9_.-]+\.(png|json)$")
MAX = 8 * 1024 * 1024


class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_POST(self):
        u = urlparse(self.path)
        name = (parse_qs(u.query).get("name") or [""])[0]
        n = int(self.headers.get("Content-Length") or 0)
        if u.path != "/save" or not NAME.match(name) or n <= 0 or n > MAX:
            self.send_response(400); self._cors(); self.end_headers(); self.wfile.write(b"bad request"); print("ERROR rejected", self.path, n, flush=True); return
        body = self.rfile.read(n)
        if body.startswith(b"data:"):
            body = base64.b64decode(body.split(b",", 1)[1])
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, name), "wb") as f:
            f.write(body)
        self.send_response(200); self._cors(); self.end_headers(); self.wfile.write(b"ok")
        print("saved", name, len(body), flush=True)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("snapshot server on 127.0.0.1:8081 ->", OUT, flush=True)
    try:
        HTTPServer(("127.0.0.1", 8081), H).serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
