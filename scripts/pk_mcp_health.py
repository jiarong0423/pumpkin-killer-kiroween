#!/usr/bin/env python3
"""Check that the configured Pumpkin Killer MCP server starts over stdio."""
import argparse
import datetime as _datetime
import json
import os
import queue
import shlex
import subprocess
import sys
import tempfile
import threading
from typing import Any, Dict, List, Optional


HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
DEFAULT_CONFIG = os.path.join(REPO_ROOT, ".kiro", "settings", "mcp.json")
LOG_DIR = os.path.join(REPO_ROOT, "docs", "kiro_evidence", "raw")
EXPECTED_TOOLS = {
    "get_public_state", "get_roster", "get_history", "submit_action",
    "end_turn", "set_notes", "get_notes",
}
FORBIDDEN_KEYS = {
    "seed", "rng", "dice", "pending_throw", "pending_action", "last_throw",
}
STEP_TIMEOUT = 10


class CheckFailure(Exception):
    """A health-check condition that failed without raising an exception."""


def walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


def short_reason(exc: BaseException) -> str:
    text = str(exc).replace("\n", " ").strip()
    if not text:
        return exc.__class__.__name__
    return text[:160]


def redact_home(text: str) -> str:
    home = os.path.expanduser("~")
    return text.replace(home, "<home>") if home else text


def config_command(config_path: str, units: int = 3) -> List[str]:
    try:
        with open(config_path, "r", encoding="utf-8") as handle:
            config = json.load(handle)
    except (OSError, ValueError) as exc:
        raise CheckFailure("could not read MCP config (%s)" % exc.__class__.__name__)
    try:
        entry = config["mcpServers"]["pumpkin-killer"]
        command = entry["command"]
        args = entry.get("args", [])
    except (KeyError, TypeError) as exc:
        raise CheckFailure("missing pumpkin-killer command (%s)" % exc.__class__.__name__)
    if not isinstance(command, str) or not command:
        raise CheckFailure("command must be a non-empty string")
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        raise CheckFailure("args must be a list of strings")
    return [command] + args + ["--seed", "7", "--units", str(units)]


class RpcClient:
    """Small JSON-RPC client with a bounded wait for every reply."""

    def __init__(self, command: List[str], cwd: str) -> None:
        self.proc = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self.lines: "queue.Queue[Optional[str]]" = queue.Queue()
        self.next_id = 1
        self.usable = True
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def _send(self, message: Dict[str, Any]) -> None:
        if not self.usable:
            raise CheckFailure("previous protocol step failed")
        if self.proc.stdin is None:
            raise CheckFailure("server stdin is unavailable")
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()

    def request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        message: Dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            message["params"] = params
        self._send(message)
        try:
            line = self.lines.get(timeout=STEP_TIMEOUT)
        except queue.Empty:
            self.usable = False
            raise CheckFailure("timed out after %ds" % STEP_TIMEOUT)
        if line is None:
            self.usable = False
            raise CheckFailure("server closed stdout")
        try:
            response = json.loads(line)
        except ValueError:
            self.usable = False
            raise CheckFailure("server wrote invalid JSON")
        if not isinstance(response, dict) or response.get("id") != request_id:
            self.usable = False
            raise CheckFailure("reply id does not match request")
        if "error" in response:
            self.usable = False
            raise CheckFailure("server returned an RPC error")
        return response

    def notify(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        message: Dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        self._send(message)

    def close(self) -> None:
        if self.proc.stdin is not None and not self.proc.stdin.closed:
            self.proc.stdin.close()
        try:
            self.proc.wait(timeout=STEP_TIMEOUT)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=STEP_TIMEOUT)
            raise CheckFailure("did not exit within %ds" % STEP_TIMEOUT)
        finally:
            if self.proc.stdout is not None:
                self.proc.stdout.close()
        if self.proc.returncode != 0:
            raise CheckFailure("server exited with status %d" % self.proc.returncode)


def append_log(command: List[str], cwd_label: str, lines: List[str]) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    date = _datetime.date.today().strftime("%Y%m%d")
    log_path = os.path.join(LOG_DIR, "mcp_health_%s.log" % date)
    safe_command = redact_home(shlex.join(command))
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write("command: %s\n" % safe_command)
        handle.write("working directory: %s\n" % cwd_label)
        for line in lines:
            handle.write(redact_home(line) + "\n")


def run(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DEFAULT_CONFIG,
                        help="MCP config containing mcpServers.pumpkin-killer")
    parser.add_argument("--units", type=int, choices=(1, 2, 3), default=3,
                        help="units per side for the health-check match")
    location = parser.add_mutually_exclusive_group()
    location.add_argument("--from-dir", help="Start the configured command from this folder")
    location.add_argument("--from-temp", action="store_true",
                          help="Start the configured command from an empty temporary folder")
    options = parser.parse_args(argv)

    log_lines: List[str] = []
    failed = False
    command: List[str] = []
    client: Optional[RpcClient] = None
    temp_dir: Optional[tempfile.TemporaryDirectory[str]] = None
    cwd = REPO_ROOT
    cwd_label = "<repo>"

    def report(step: str, check) -> None:
        nonlocal failed
        try:
            check()
        except CheckFailure as exc:
            failed = True
            line = redact_home("FAIL %s %s" % (step, short_reason(exc)))
            print(line)
            log_lines.append(line)
        except Exception as exc:  # Each check reports independently and continues.
            failed = True
            line = redact_home("ERROR %s %s" % (step, short_reason(exc)))
            print(line)
            log_lines.append(line)
        else:
            line = "ok %s" % step
            print(line)
            log_lines.append(line)

    try:
        if options.from_temp:
            temp_dir = tempfile.TemporaryDirectory(prefix="pk-mcp-health-")
            cwd = temp_dir.name
            cwd_label = "<temp>"
        elif options.from_dir:
            cwd = os.path.abspath(options.from_dir)
            cwd_label = "<repo>" if cwd == REPO_ROOT else "<from-dir>"

        def load_config() -> None:
            nonlocal command
            command = config_command(options.config, options.units)

        report("config", load_config)

        def start() -> None:
            nonlocal client
            if not command:
                raise CheckFailure("no command was loaded")
            client = RpcClient(command, cwd)

        report("start", start)

        def require_client() -> RpcClient:
            if client is None:
                raise CheckFailure("server was not started")
            return client

        report("initialize", lambda: require_client().request("initialize", {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "pk-mcp-health", "version": "1"},
        }))
        report("notifications/initialized", lambda: require_client().notify("notifications/initialized"))
        report("ping", lambda: require_client().request("ping"))

        def list_tools() -> None:
            response = require_client().request("tools/list")
            tools = response.get("result", {}).get("tools")
            if not isinstance(tools, list):
                raise CheckFailure("tools/list did not return a tool list")
            names = {tool.get("name") for tool in tools if isinstance(tool, dict)}
            if names != EXPECTED_TOOLS:
                raise CheckFailure("tool names do not match the expected six")

        report("tools/list", list_tools)

        def public_state() -> None:
            response = require_client().request("tools/call", {
                "name": "get_public_state", "arguments": {},
            })
            result = response.get("result")
            if not isinstance(result, dict) or result.get("isError") is not False:
                raise CheckFailure("get_public_state returned an error")
            content = result.get("content")
            if not isinstance(content, list) or not content or not isinstance(content[0], dict):
                raise CheckFailure("get_public_state returned no content")
            try:
                state = json.loads(content[0]["text"])
            except (KeyError, TypeError, ValueError):
                raise CheckFailure("get_public_state returned invalid JSON")
            forbidden = set(walk_keys(state)) & FORBIDDEN_KEYS
            if forbidden:
                raise CheckFailure("public state contains forbidden key %s" % sorted(forbidden)[0])

        report("get_public_state", public_state)
        report("stdin close", lambda: require_client().close())
    finally:
        if client is not None and client.proc.poll() is None:
            try:
                client.proc.kill()
                client.proc.wait(timeout=STEP_TIMEOUT)
            except OSError:
                pass
        if temp_dir is not None:
            temp_dir.cleanup()
        try:
            append_log(command, cwd_label, log_lines)
        except OSError as exc:
            failed = True
            print("ERROR log %s" % short_reason(exc))

    print("FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run())
