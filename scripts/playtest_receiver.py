#!/usr/bin/env python3
"""Temporary local receiver: lets the game page post playtest frames to docs/playtest/frames/.
Binds 127.0.0.1:8766 only, accepts POST /frame?name=<safe name> with a JPEG/PNG body (max 3 MB), CORS enabled. Stop with Ctrl-C.
Writes ONLY inside docs/playtest/frames/ and only names matching [a-z0-9_]{1,40}.(jpg|png).
"""
import http.server, re, sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

OUT = Path(__file__).resolve().parent.parent / "docs/playtest/frames"
NAME = re.compile(r"^[a-z0-9_]{1,40}\.(jpg|png)$")

class H(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()
    def do_POST(self):
        u = urlparse(self.path)
        name = (parse_qs(u.query).get("name") or [""])[0]
        n = int(self.headers.get("Content-Length") or 0)
        if u.path != "/frame" or not NAME.match(name) or n <= 0 or n > 3_000_000:
            self.send_response(400); self._cors(); self.end_headers(); return
        data = self.rfile.read(n)
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / name).write_bytes(data)
        self.send_response(200); self._cors(); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, fmt, *a):
        sys.stderr.write("frame " + (fmt % a) + "\n")

if __name__ == "__main__":
    print("receiving into", OUT, "on 127.0.0.1:8766")
    http.server.ThreadingHTTPServer(("127.0.0.1", 8766), H).serve_forever()
