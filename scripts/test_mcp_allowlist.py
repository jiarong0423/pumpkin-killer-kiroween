#!/usr/bin/env python3
"""Tests for the pinned Pumpkin Killer MCP tools and player-agent permissions."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import make_mcp_allowlist as allowlist  # noqa: E402


ALLOWLIST_PATH = os.path.join(ROOT, "docs", "mcp_tool_allowlist.json")
CONFIG_PATH = os.path.join(ROOT, ".kiro", "settings", "mcp.json")
PLAYER_PATH = os.path.join(ROOT, ".kiro", "agents", "pk-player.json")


class McpAllowlistTests(unittest.TestCase):
    def load_json(self, path):
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)

    def write_json(self, path, value):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(value, handle)

    def test_live_tools_match_the_pinned_allowlist(self):
        self.assertEqual([], allowlist.check(ALLOWLIST_PATH, CONFIG_PATH))
        document = self.load_json(ALLOWLIST_PATH)
        self.assertEqual(list(allowlist.EXPECTED_TOOL_NAMES),
                         [tool["name"] for tool in document["tools"]])
        self.assertEqual([True, True, True, False, False, False, True],
                         [tool["readOnly"] for tool in document["tools"]])

    def test_changed_description_pin_fails(self):
        document = self.load_json(ALLOWLIST_PATH)
        document["tools"][0]["descriptionSha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            altered = os.path.join(directory, "allowlist.json")
            self.write_json(altered, document)
            errors = allowlist.check(altered, CONFIG_PATH)
        self.assertTrue(any("allowlist tools" in error for error in errors), errors)

    def test_extra_auto_approved_tool_fails(self):
        config = self.load_json(CONFIG_PATH)
        config["mcpServers"]["pumpkin-killer"]["autoApprove"].append("submit_action")
        with tempfile.TemporaryDirectory() as directory:
            altered = os.path.join(directory, "mcp.json")
            self.write_json(altered, config)
            errors = allowlist.check(ALLOWLIST_PATH, altered)
        self.assertTrue(any("autoApprove" in error for error in errors), errors)

    def test_player_agent_has_only_pumpkin_killer_mcp_tools(self):
        player = self.load_json(PLAYER_PATH)
        self.assertEqual("pk-player", player.get("name"))
        self.assertFalse(player.get("includeMcpJson"))
        self.assertFalse(player.get("includePowers"))
        self.assertEqual(["@mcp"], player.get("tools"))
        self.assertEqual({"pumpkin-killer"}, set(player.get("mcpServers", {})))
        server = player["mcpServers"]["pumpkin-killer"]
        self.assertEqual("python3", server.get("command"))
        self.assertEqual(["-B", "scripts/mcp_stdio_server.py", "--seat", "white",
                          "--opponent", "builtin:normal", "--transcript",
                          "docs/kiro_evidence/raw/mcp_pk_player_match.jsonl"], server.get("args"))
        self.assertEqual(set(allowlist.PLAYER_TOOLS), set(server.get("autoApprove", [])))
        self.assertTrue(set(server["autoApprove"]).issubset(set(allowlist.EXPECTED_TOOL_NAMES)))
        forbidden_categories = {"read", "write", "shell", "web", "subagent", "@builtin", "*"}
        self.assertFalse(forbidden_categories & set(player["tools"]))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(McpAllowlistTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print("OK" if result.wasSuccessful() else "FAIL")
    raise SystemExit(0 if result.wasSuccessful() else 1)
