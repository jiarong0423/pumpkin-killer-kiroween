#!/usr/bin/env python3
"""Prints a ready-to-paste MCP server entry that lets YOUR OWN agent join a Pumpkin Killer room (owner 2026-11-17: the room host brings their own sub-agent).

The agent runs on your machine with your own model account; the game server only relays small structured messages and never calls a model.

  python3 -B scripts/make_agent_join_config.py --relay wss://<relay host>/relay --code ABC234 [--seat white] [--name pumpkin-killer] [--claude-command]
Without --relay the local development relay ws://localhost:8765/ws is used. With --claude-command it prints the one-line `claude mcp add` command instead of JSON.
Exit code 0 on success, 2 on bad arguments (the code must be 6 letters or digits, the relay must start with ws:// or wss://).
"""
import argparse
import json
import os
import re
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = re.compile(r"^[A-Z0-9]{6}$")


def build(relay, code, seat, name):
    args = ["-B", os.path.join(HERE, "mcp_stdio_server.py"), "--seat", seat, "--connect", relay, "--code", code, "--auto-ready"]
    return {"mcpServers": {name: {"command": "python3", "args": args, "autoApprove": ["get_public_state", "get_history", "get_notes", "get_roster"]}}}, args


def build_http(http_url, name):
    return {"mcpServers": {name: {"type": "http", "url": http_url}}}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--relay", default="ws://localhost:8765/ws")
    parser.add_argument("--code", default="")
    parser.add_argument("--http", default="", help="remote Streamable HTTP MCP endpoint URL (e.g. https://<host>/mcp)")
    parser.add_argument("--seat", default="white", choices=["red", "white"])
    parser.add_argument("--name", default="pumpkin-killer")
    parser.add_argument("--claude-command", action="store_true")
    args = parser.parse_args()
    if args.http:
        http_url = args.http.strip()
        if not re.match(r"^https?://", http_url):
            print("ERROR: --http must start with http:// or https://")
            return 2
        if args.claude_command:
            print("claude mcp add --transport http %s %s" % (shlex.quote(args.name), shlex.quote(http_url)))
        else:
            print(json.dumps(build_http(http_url, args.name), indent=2))
        return 0
    code = args.code.strip().upper()
    if not CODE.match(code):
        print("ERROR: the room code is 6 letters or digits, got %r" % args.code)
        return 2
    if not re.match(r"^wss?://", args.relay):
        print("ERROR: --relay must start with ws:// or wss://")
        return 2
    config, argv = build(args.relay, code, args.seat, args.name)
    if args.claude_command:
        print("claude mcp add %s -- python3 %s" % (shlex.quote(args.name), " ".join(shlex.quote(a) for a in argv)))
    else:
        print(json.dumps(config, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
