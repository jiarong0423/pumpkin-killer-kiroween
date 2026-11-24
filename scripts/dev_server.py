#!/usr/bin/env python3
"""Run the local static server, optionally with the loopback room relay."""
import argparse
import http.server
import os
import signal
import socketserver
import subprocess
import sys
import threading
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_UPSTREAM = "http://127.0.0.1:8767"


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    request_queue_size = 512
    allow_reuse_address = True


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass

    def _proxy_mcp(self):
        length = int(self.headers.get("Content-Length") or "0")
        body = self.rfile.read(length) if length > 0 else None
        hdrs = {}
        for k in ("Content-Type", "Accept", "Mcp-Session-Id", "MCP-Protocol-Version", "Origin"):
            if k in self.headers:
                hdrs[k] = self.headers[k]
        req = urllib.request.Request(MCP_UPSTREAM + self.path, data=body, headers=hdrs, method=self.command)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in ("transfer-encoding", "connection", "content-length", "date", "server"):
                        self.send_header(k, v)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as err:
            data = err.read()
            self.send_response(err.code)
            for k, v in err.headers.items():
                if k.lower() not in ("transfer-encoding", "connection", "content-length", "date", "server"):
                    self.send_header(k, v)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as exc:
            msg = ('{"error":"mcp_upstream_unavailable","detail":"%s"}' % type(exc).__name__).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def do_GET(self):
        if self.path.split("?", 1)[0] in ("/mcp", "/mcp/health"):
            self._proxy_mcp()
            return
        super().do_GET()

    def do_POST(self):
        if self.path.split("?", 1)[0] == "/mcp":
            self._proxy_mcp()
            return
        self.send_error(405)

    def do_DELETE(self):
        if self.path.split("?", 1)[0] == "/mcp":
            self._proxy_mcp()
            return
        self.send_error(405)

    def do_OPTIONS(self):
        if self.path.split("?", 1)[0] == "/mcp":
            self._proxy_mcp()
            return
        self.send_error(405)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("port", nargs="?", type=int, default=8080)
    parser.add_argument("--with-relay", action="store_true", help="start scripts/pk_relay.py on loopback port 8765")
    parser.add_argument("--with-mcp", action="store_true", help="start scripts/pk_mcp_http.py on loopback port 8767 and proxy /mcp")
    args = parser.parse_args()
    os.chdir(ROOT)
    procs = []
    if args.with_relay:
        procs.append(subprocess.Popen([sys.executable, "-B", "scripts/pk_relay.py"], cwd=ROOT,
                                      env=dict(os.environ, HOST="127.0.0.1", PORT="8765")))
    if args.with_mcp:
        procs.append(subprocess.Popen([sys.executable, "-B", "scripts/pk_mcp_http.py"], cwd=ROOT,
                                      env=dict(os.environ, PK_MCP_HOST="127.0.0.1", PK_MCP_PORT="8767",
                                               PK_MCP_RELAY_URL="ws://127.0.0.1:8765/ws")))
    srv = Server(("127.0.0.1", args.port), Handler)

    def _handle_stop(_sig, _frame):
        threading.Thread(target=srv.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)
    try:
        modes = [m for m, on in (("relay", args.with_relay), ("mcp", args.with_mcp)) if on]
        print("serving on", args.port, ("with " + "+".join(modes)) if modes else "", flush=True)
        srv.serve_forever()
    finally:
        srv.server_close()
        for proc in procs:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


if __name__ == "__main__":
    main()
