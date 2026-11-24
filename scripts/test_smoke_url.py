#!/usr/bin/env python3
"""Tests for the release URL smoke checker."""

from __future__ import annotations

import functools
import http.server
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SMOKE_SCRIPT = ROOT / "scripts" / "release" / "smoke_url.py"


class QuietStaticServer(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


class SmokeUrlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "assets").mkdir()
        (self.root / "index.html").write_text(
            '<!doctype html><title>Pumpkin Killer</title><img src="assets/pumpkin.png">',
            encoding="utf-8",
        )
        (self.root / "assets" / "pumpkin.png").write_bytes(b"image")
        handler = functools.partial(QuietStaticServer, directory=str(self.root))
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address[:2]
        self.url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp_dir.cleanup()

    def run_smoke(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(SMOKE_SCRIPT), self.url],
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_good_tree_passes(self) -> None:
        result = self.run_smoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            [
                "INDEX status=200 title=yes",
                "PATHS checked=1",
                "NON_200 count=0 first_five=-",
                "OVERALL PASS",
            ],
        )

    def test_missing_referenced_file_fails(self) -> None:
        (self.root / "assets" / "pumpkin.png").unlink()
        result = self.run_smoke()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("NON_200 count=1 first_five=assets/pumpkin.png", result.stdout)
        self.assertTrue(result.stdout.endswith("OVERALL FAIL\n"))


if __name__ == "__main__":
    unittest.main()
