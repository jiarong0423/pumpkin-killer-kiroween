#!/usr/bin/env python3
"""Build or verify the pinned local Pumpkin Killer MCP tool allowlist."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Sequence


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, ".kiro", "settings", "mcp.json")
ALLOWLIST_PATH = os.path.join(ROOT, "docs", "mcp_tool_allowlist.json")
SERVER_NAME = "pumpkin-killer"
EXPECTED_TOOL_NAMES = (
    "get_public_state",
    "get_roster",
    "get_history",
    "submit_action",
    "end_turn",
    "set_notes",
    "get_notes",
)
READ_ONLY_TOOLS = ("get_public_state", "get_roster", "get_history", "get_notes")
PLAYER_TOOLS = (
    "get_public_state", "get_history", "submit_action", "end_turn", "set_notes", "get_notes",
)
ALLOWED_SEATS = ("red", "white", "spectator", "referee")
ALLOWED_OPPONENTS = ("builtin:easy", "builtin:normal", "builtin:hard", "builtin:adaptive")


class AllowlistError(Exception):
    """A local allowlist or configured MCP server failed a safety check."""


def load_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, ValueError) as exc:
        raise AllowlistError("could not read %s: %s" % (os.path.basename(path), exc.__class__.__name__))
    if not isinstance(value, dict):
        raise AllowlistError("%s must contain a JSON object" % os.path.basename(path))
    return value


def configured_server(config_path: str = CONFIG_PATH) -> Dict[str, Any]:
    config = load_json(config_path)
    try:
        server = config["mcpServers"][SERVER_NAME]
    except (KeyError, TypeError):
        raise AllowlistError("MCP configuration has no pumpkin-killer server")
    if not isinstance(server, dict):
        raise AllowlistError("pumpkin-killer server configuration must be an object")
    command = server.get("command")
    args = server.get("args")
    if not isinstance(command, str) or not command:
        raise AllowlistError("MCP command must be a non-empty string")
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        raise AllowlistError("MCP args must be a list of strings")
    return server


def validate_launch(command: Any, args: Any) -> None:
    if command != "python3":
        raise AllowlistError("MCP command must be python3")
    if not isinstance(args, list) or len(args) not in (2, 4):
        raise AllowlistError("MCP args must contain the stdio server and optional --seat")
    if args[:2] != ["-B", "scripts/mcp_stdio_server.py"]:
        raise AllowlistError("MCP args must start with -B scripts/mcp_stdio_server.py")
    if len(args) == 4 and (args[2] != "--seat" or args[3] not in ALLOWED_SEATS):
        raise AllowlistError("MCP --seat flag is invalid")


def live_tools(config_path: str = CONFIG_PATH) -> List[Dict[str, Any]]:
    server = configured_server(config_path)
    command = server["command"]
    args = server["args"]
    validate_launch(command, args)
    process = subprocess.Popen(
        [command] + args,
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    try:
        assert process.stdin is not None
        assert process.stdout is not None
        process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}) + "\n")
        process.stdin.flush()
        line = process.stdout.readline()
        if not line:
            raise AllowlistError("MCP server returned no tools/list response")
        try:
            response = json.loads(line)
            tools = response["result"]["tools"]
        except (KeyError, TypeError, ValueError):
            raise AllowlistError("MCP server returned an invalid tools/list response")
        if not isinstance(tools, list) or not all(isinstance(tool, dict) for tool in tools):
            raise AllowlistError("MCP tools/list response must contain tool objects")
        return tools
    finally:
        if process.stdin is not None and not process.stdin.closed:
            process.stdin.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def tool_record(tool: Dict[str, Any]) -> Dict[str, Any]:
    name = tool.get("name")
    description = tool.get("description")
    annotations = tool.get("annotations", {})
    if not isinstance(name, str) or not isinstance(description, str):
        raise AllowlistError("every MCP tool needs a string name and description")
    if not isinstance(annotations, dict):
        raise AllowlistError("tool annotations must be an object")
    return {
        "name": name,
        "readOnly": annotations.get("readOnlyHint") is True,
        "descriptionSha256": hashlib.sha256(description.encode("utf-8")).hexdigest(),
    }


def build_document(config_path: str = CONFIG_PATH) -> Dict[str, Any]:
    server = configured_server(config_path)
    validate_launch(server["command"], server["args"])
    records = [tool_record(tool) for tool in live_tools(config_path)]
    names = tuple(record["name"] for record in records)
    if names != EXPECTED_TOOL_NAMES:
        raise AllowlistError("live tools/list names do not match the six pinned tool names")
    return {
        "server": SERVER_NAME,
        "transport": "stdio",
        "command": "python3",
        "args": ["-B", "scripts/mcp_stdio_server.py"],
        "allowedFlags": {
            "--seat": list(ALLOWED_SEATS),
            "--opponent": list(ALLOWED_OPPONENTS),
            "--transcript": "docs/kiro_evidence/raw/<recorded-match>.jsonl",
        },
        "tools": records,
        "autoApprove": {
            "readOnly": list(READ_ONLY_TOOLS),
            "pk-player": list(PLAYER_TOOLS),
            "rule": "Nothing else may be auto-approved.",
        },
    }


def compare_allowlist(expected: Dict[str, Any], actual: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for key in ("server", "transport", "command", "args", "allowedFlags", "autoApprove", "tools"):
        if actual.get(key) != expected.get(key):
            errors.append("allowlist %s does not match the pinned live configuration" % key)
    return errors


def validate_config(document: Dict[str, Any], config_path: str = CONFIG_PATH) -> List[str]:
    errors: List[str] = []
    try:
        server = configured_server(config_path)
        validate_launch(server["command"], server["args"])
    except AllowlistError as exc:
        return [str(exc)]
    if document.get("command") != server["command"]:
        errors.append("allowlist command does not match MCP configuration")
    if document.get("args") != server["args"][:2]:
        errors.append("allowlist stdio args do not match MCP configuration")
    configured_auto = server.get("autoApprove")
    read_only = document.get("autoApprove", {}).get("readOnly")
    if not isinstance(configured_auto, list) or not isinstance(read_only, list) or not set(configured_auto).issubset(set(read_only)):
        errors.append("MCP configuration autoApprove is outside the read-only allowlist")
    if server.get("disabled") is not False:
        errors.append("MCP configuration must explicitly enable pumpkin-killer")
    return errors


def check(allowlist_path: str = ALLOWLIST_PATH, config_path: str = CONFIG_PATH) -> List[str]:
    try:
        actual = load_json(allowlist_path)
        expected = build_document(config_path)
    except AllowlistError as exc:
        return [str(exc)]
    return compare_allowlist(expected, actual) + validate_config(actual, config_path)


def main(argv: Sequence[str] = ()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="write hashes from live tools/list")
    group.add_argument("--check", action="store_true", help="verify pinned hashes and MCP configuration")
    options = parser.parse_args(argv)
    if options.write:
        try:
            document = build_document()
            with open(ALLOWLIST_PATH, "w", encoding="utf-8") as handle:
                json.dump(document, handle, indent=2)
                handle.write("\n")
        except (AllowlistError, OSError) as exc:
            print("FAIL: %s" % exc, file=sys.stderr)
            return 1
        print("WROTE docs/mcp_tool_allowlist.json from live tools/list")
        return 0
    errors = check()
    if errors:
        for error in errors:
            print("FAIL: %s" % error, file=sys.stderr)
        return 1
    print("OK: MCP allowlist matches live tools/list and configuration")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
