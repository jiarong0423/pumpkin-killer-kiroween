#!/usr/bin/env python3
"""Needs a localhost socket. A request nested thousands of arrays deep gets a parse error instead of a dropped connection (2026-11-27 stress test).
usage: python3 -B scripts/test_mcp_http_deep.py"""
import threading
import unittest
import urllib.error
import urllib.request

import pk_mcp_http


class DeepBody(unittest.TestCase):
    def test_deeply_nested_body_is_answered(self):
        server = pk_mcp_http.create_server(host="127.0.0.1", port=0, relay_url="ws://127.0.0.1:1/ws")
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            request = urllib.request.Request("http://127.0.0.1:%d/mcp" % server.server_address[1], data=b"[" * 20000 + b"]" * 20000, headers={"Content-Type": "application/json"})
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request, timeout=10)
            self.assertEqual(caught.exception.code, 400)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
