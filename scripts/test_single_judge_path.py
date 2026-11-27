#!/usr/bin/env python3
"""Every product entry point judges a room with the real page only (2026-11-27). No sockets are opened: the refusal happens while the options are read.
usage: python3 -B scripts/test_single_judge_path.py"""
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV = {k: v for k, v in os.environ.items() if k not in ("PK_ALLOW_BRIDGE_FOR_TESTS", "PK_MCP_PAGE_JUDGE")}


def run(script, *args, **extra):
    return subprocess.run([sys.executable, "-B", str(HERE / script), *args], capture_output=True, text=True, timeout=30, env={**ENV, **extra}, stdin=subprocess.DEVNULL)


class OnePath(unittest.TestCase):
    def test_off_and_auto_are_refused(self):
        for script in ("mcp_stdio_server.py", "pk_mcp_http.py"):
            for mode in ("off", "auto"):
                result = run(script, "--page-judge", mode)
                self.assertEqual(result.returncode, 2, (script, mode, result.stderr[-300:]))
                self.assertIn("retired", result.stderr)

    def test_the_environment_cannot_switch_it_off(self):
        result = run("pk_mcp_http.py", PK_MCP_PAGE_JUDGE="off")
        self.assertEqual(result.returncode, 2, result.stderr[-300:])

    def test_a_missing_node_stops_room_play(self):
        result = run("mcp_stdio_server.py", "--room-tools", PATH="/nonexistent")
        self.assertEqual(result.returncode, 2, result.stderr[-300:])
        self.assertIn("Node 22", result.stderr)

    def test_the_container_forces_the_page_judge(self):
        script = (HERE.parent / "deploy" / "entrypoint.sh").read_text()
        self.assertIn("\nPK_MCP_PAGE_JUDGE=on", script)


if __name__ == "__main__":
    unittest.main()
