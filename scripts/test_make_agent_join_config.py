#!/usr/bin/env python3
"""scripts/make_agent_join_config.py prints a valid MCP entry for a host's own agent and refuses a bad room code or relay address (docs/HOST_AGENT_HOWTO.md)."""
import json
import os
import subprocess
import sys
import unittest

TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_agent_join_config.py")


def run(*args):
    return subprocess.run([sys.executable, "-B", TOOL, *args], capture_output=True, text=True)


class JoinConfigTests(unittest.TestCase):
    def test_entry_carries_relay_code_seat_and_auto_ready(self):
        out = run("--relay", "wss://x.example/ws", "--code", "abc234", "--seat", "red")
        self.assertEqual(out.returncode, 0)
        args = json.loads(out.stdout)["mcpServers"]["pumpkin-killer"]["args"]
        self.assertEqual(args[args.index("--code") + 1], "ABC234")
        self.assertEqual(args[args.index("--connect") + 1], "wss://x.example/ws")
        self.assertEqual(args[args.index("--seat") + 1], "red")
        self.assertIn("--auto-ready", args)
        self.assertTrue(os.path.isabs(args[1]) and args[1].endswith("mcp_stdio_server.py"))

    def test_bad_code_and_bad_relay_are_refused(self):
        self.assertEqual(run("--code", "bad").returncode, 2)
        self.assertEqual(run("--code", "ABC234", "--relay", "http://x").returncode, 2)

    def test_claude_command_form(self):
        out = run("--code", "ABC234", "--claude-command")
        self.assertEqual(out.returncode, 0)
        self.assertTrue(out.stdout.startswith("claude mcp add pumpkin-killer -- python3 -B "))

    def test_the_arguments_are_accepted_by_the_bridge_itself(self):
        # the bridge refuses --connect without --code or without a seat; the generated list must pass its own argument checks (--help exits before any connection)
        out = run("--code", "ABC234")
        args = json.loads(out.stdout)["mcpServers"]["pumpkin-killer"]["args"]
        bridge = subprocess.run([sys.executable, "-B", args[1], "--help"], capture_output=True, text=True)
        self.assertEqual(bridge.returncode, 0)
        for flag in ("--connect", "--code", "--auto-ready", "--seat"):
            self.assertIn(flag, bridge.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
