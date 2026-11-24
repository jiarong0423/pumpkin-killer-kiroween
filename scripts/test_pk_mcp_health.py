#!/usr/bin/env python3
"""Tests for the stand-alone MCP stdio health check."""
import datetime as _datetime
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HEALTH = os.path.join(HERE, "pk_mcp_health.py")
LOG_DIR = os.path.join(ROOT, "docs", "kiro_evidence", "raw")


def run_health(*args, timeout=20):
    return subprocess.run(
        [sys.executable, "-B", HEALTH, *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def write_config(path, command, args):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"mcpServers": {"pumpkin-killer": {"command": command, "args": args}}}, handle)


class McpHealthCheckTest(unittest.TestCase):
    def test_real_server_passes_from_repository_root(self):
        result = run_health()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ok get_public_state", result.stdout)
        self.assertTrue(result.stdout.rstrip().endswith("PASS"), result.stdout)

    def test_missing_executable_fails_with_error_line(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = os.path.join(temporary, "missing.json")
            write_config(config, "definitely-not-a-pk-executable", [])
            result = run_health("--config", config)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ERROR start", result.stdout)
        self.assertTrue(result.stdout.rstrip().endswith("FAIL"), result.stdout)

    def test_garbage_server_fails_without_hanging(self):
        with tempfile.TemporaryDirectory() as temporary:
            script = os.path.join(temporary, "garbage_server.py")
            config = os.path.join(temporary, "garbage.json")
            with open(script, "w", encoding="utf-8") as handle:
                handle.write("import time\nprint('not json', flush=True)\ntime.sleep(60)\n")
            write_config(config, sys.executable, [script])
            started = time.monotonic()
            result = run_health("--config", config, timeout=20)
            elapsed = time.monotonic() - started
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL initialize server wrote invalid JSON", result.stdout)
        self.assertIn("FAIL stdin close did not exit within 10s", result.stdout)
        self.assertLess(elapsed, 15, "health check did not enforce its shutdown timeout")

    def test_log_does_not_contain_home_directory(self):
        result = run_health()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        date = _datetime.date.today().strftime("%Y%m%d")
        log_path = os.path.join(LOG_DIR, "mcp_health_%s.log" % date)
        with open(log_path, "r", encoding="utf-8") as handle:
            log_text = handle.read()
        self.assertFalse(os.path.expanduser("~") in log_text,
                         "home directory appeared in the health-check log")


if __name__ == "__main__":
    unittest.main(verbosity=2)
