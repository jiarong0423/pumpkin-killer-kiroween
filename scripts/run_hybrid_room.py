#!/usr/bin/env python3
"""Hybrid room test (docs/SIX_SEAT_HYBRID_PLAN_20261117.md, option A): two seats per match, each seat plays a whole team of 3 units.

Seat kinds (any kind on either side):
  headless  the real index.html in the Node vm (scripts/hybrid_seat_headless.js), real WebSocket to the relay
  mcp       the Python MCP bridge scripts/mcp_stdio_server.py (--connect/--code), driven here through its public stdio tools only
  desktop   the real index.html in a headless desktop Chrome over CDP (scripts/hybrid_seat_chrome.mjs --kind desktop)
  phone     the real index.html in the phone's Chrome over CDP (scripts/hybrid_seat_chrome.mjs --kind phone; adb forward/reverse first)
  claude    an MCP bridge seat whose shot is decided by Claude through files (logs_local/hybrid_claude/turn.json -> action.json)

The runner starts the local relay in this process (every relay error is counted), opens a room as the spectator, starts the two seats, plays to
the end and writes one record per match in the matrix record format of docs/MATRIX_SPEC_20261117.md plus seat_left, seat_right, relay_errors and
hash_mismatches. A spectator page (scripts/hybrid_viewer.html, served on --viewer-port) shows the whole match live.

  python3 -B scripts/run_hybrid_room.py --kinds headless,mcp --matches 10                    every pair of kinds, 10 matches each
  python3 -B scripts/run_hybrid_room.py --kinds headless,mcp,desktop,phone --matches 10 --report docs/HYBRID_RUN_20261117.md
  python3 -B scripts/run_hybrid_room.py --pairs headless:mcp --matches 1 --speed 4          one match, 4 fake seconds per second: watch it
  python3 -B scripts/run_hybrid_room.py --report-only docs/HYBRID_RUN_20261117.md             rebuild the table from the result file

Sockets and Chrome cannot start in the Claude Bash sandbox: run it from the owner's terminal. Log: logs_local/hybrid_run.log.
Exit code 0 only when every match has no error, no relay error and no hash mismatch.
"""
import argparse
import asyncio
import datetime
import http.server
import itertools
import json
import os
import random
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import traceback
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import websockets  # noqa: E402

import agent_levels  # noqa: E402
import mcp_stdio_server as srv  # noqa: E402
from pk_relay import RelayServer  # noqa: E402
from round_hash_py import world_unit_id  # noqa: E402

HEROES = ["skeleton", "wizard", "bat", "knight", "bride", "hunchback", "reaper", "hag"]
TIERS = ["hard", "normal", "easy"]
KINDS = ["headless", "mcp", "desktop", "phone", "claude"]
LOG_PATH = os.path.join(ROOT, "logs_local", "hybrid_run.log")
CLAUDE_DIR = os.path.join(ROOT, "logs_local", "hybrid_claude")


def log(message: str) -> None:
    line = "%s %s" % (datetime.datetime.now().strftime("%H:%M:%S"), message)
    print(line, file=sys.stderr, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        pass


# ------------------------------------------------------------------ spec: heroes and hidden strength (docs/MATRIX_SPEC_20261117.md)
def mulberry(seed: int):
    state = [seed & 0xFFFFFFFF]

    def rnd() -> float:
        state[0] = (state[0] + 0x6D2B79F5) & 0xFFFFFFFF
        t = state[0]
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return rnd


def team_from(first: str, size: int) -> List[str]:
    start = HEROES.index(first)
    return [HEROES[(start + i) % len(HEROES)] for i in range(size)]


def match_plan(seed: int, size: int) -> Dict[str, Any]:
    hero = HEROES[seed % 8]
    hero_right = HEROES[(seed * 7 + 3) % 8]
    rnd = mulberry((seed ^ 0x5eed) & 0xFFFFFFFF)
    tier_left = TIERS[int(rnd() * 3)]
    tier_right = TIERS[int(rnd() * 3)]
    return {"hero": hero, "hero_right": hero_right, "heroes_left": team_from(hero, size) if size > 1 else [hero],
            "heroes_right": team_from(hero_right, size) if size > 1 else [hero_right],
            "tier_left": tier_left, "tier_right": tier_right}


# ------------------------------------------------------------------ the relay, in this process, with every error counted
class CountingRelay(RelayServer):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.error_log: List[Dict[str, Any]] = []

    async def _dispatch(self, websocket: Any, room: Any, entry: Any, message: Dict[str, Any], wrong_code_times: list) -> tuple:
        self._current = {"type": message.get("type"), "seat": entry["seat_id"] if entry else None, "round": message.get("round"), "phase": message.get("phase"),
                         "unit": message.get("unit"), "kind": message.get("kind"), "room_round": room.round if room else None, "room_phase": room.phase if room else None}
        return await super()._dispatch(websocket, room, entry, message, wrong_code_times)

    async def _error(self, websocket: Any, code: str, message: Optional[str] = None) -> None:
        self.error_log.append({"t": round(time.time(), 3), "code": code, "message": message, "while": dict(getattr(self, "_current", {}) or {})})
        await super()._error(websocket, code, message)


# ------------------------------------------------------------------ live state for the spectator page
class View:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.data: Dict[str, Any] = {"status": "idle", "finished": [], "match": None}

    def update(self, **fields: Any) -> None:
        with self.lock:
            self.data.update(fields)

    def mutate(self, fn: Any) -> None:
        with self.lock:
            fn(self.data)

    def snapshot(self) -> bytes:
        with self.lock:
            return json.dumps(self.data, ensure_ascii=False).encode("utf-8")


def start_viewer(view: View, port: int) -> Optional[http.server.ThreadingHTTPServer]:
    page = os.path.join(HERE, "hybrid_viewer.html")

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path.split("?")[0] == "/state.json":
                body, kind = view.snapshot(), "application/json"
            elif self.path.split("?")[0] in ("/", "/index.html", "/hybrid_viewer.html"):
                with open(page, "rb") as handle:
                    body, kind = handle.read(), "text/html; charset=utf-8"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args: Any) -> None:
            pass

    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as exc:
        log("viewer: cannot listen on %d (%s); the match still runs" % (port, exc))
        return None
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


# ------------------------------------------------------------------ spectator: creates the room, follows every ordered message
class Spectator:
    def __init__(self, relay_url: str, size: int, view: View, label: str, plan: Dict[str, Any]) -> None:
        self.relay_url = relay_url
        self.size = size
        self.view = view
        self.label = label
        self.plan = plan
        self.code = ""
        self.socket: Any = None
        self.task: Any = None
        self.messages: List[Dict[str, Any]] = []
        self.out_of_sync: List[int] = []
        self.hp: Dict[str, float] = {}
        self.maxhp: Dict[str, float] = {}
        self.units: Dict[str, Dict[str, Any]] = {}
        self.start: Optional[Dict[str, Any]] = None
        self.winner_seen: Optional[str] = None
        self.started = asyncio.Event()

    async def open(self) -> str:
        self.socket = await websockets.connect(self.relay_url + "/ws", max_size=16 * 1024)
        await self.socket.send(json.dumps({"type": "create_room", "seat": "spectator", "team_size": self.size, "scene": "graveyard"}))
        first = json.loads(await asyncio.wait_for(self.socket.recv(), 5))
        if first.get("type") != "room_state" or not first.get("code"):
            raise RuntimeError("room not created: %r" % (first,))
        self.code = first["code"]
        self.task = asyncio.ensure_future(self._follow())
        return self.code

    async def close(self) -> None:
        try:
            await self.socket.send(json.dumps({"type": "leave"}))
        except Exception:
            pass
        if self.task:
            self.task.cancel()
        try:
            await self.socket.close()
        except Exception:
            pass

    async def _follow(self) -> None:
        try:
            async for raw in self.socket:
                message = json.loads(raw)
                self.messages.append(message)
                self._handle(message)
        except (asyncio.CancelledError, websockets.ConnectionClosed):
            pass
        except Exception:
            log("spectator: %s" % traceback.format_exc().splitlines()[-1])

    def _set_match(self, **fields: Any) -> None:
        def apply(data: Dict[str, Any]) -> None:
            match = data.get("match") or {}
            match.update(fields)
            data["match"] = match
        self.view.mutate(apply)

    def _handle(self, m: Dict[str, Any]) -> None:
        kind = m.get("type")
        if kind == "room_state":
            self._set_match(seats=[{"seat_id": s["seat_id"], "team": s["team"], "ready": s["ready"], "units": s["units"]} for s in m.get("seats", [])], started=bool(m.get("started")))
        elif kind == "start":
            self.start = m
            asyncio.get_event_loop().call_later(0.6, self.started.set)   # a bridge needs a moment to adopt the room's seed and heroes before its bot acts
            heroes = m.get("heroes") or {}
            session = srv.Session(seed=m["seed"], units=self.size, hero_red=heroes.get("left"), hero_white=heroes.get("right"))
            session.reset_for_relay(m["seed"], m.get("scene", "graveyard"), self.size, heroes)
            rows = {}
            for uid, unit in session.engine.units.items():
                world = world_unit_id(uid)
                rows[world] = {"id": world, "team": unit["team"], "hero": unit["hero"], "x": unit["x"], "y": unit["y"], "hp": unit["hp"], "max_hp": unit["max_hp"], "alive": True}
                self.hp[world] = unit["hp"]
                self.maxhp[world] = unit["max_hp"]
            self.units = rows
            self._set_match(seed=m["seed"], units=list(rows.values()), round=1, phase=m.get("phase"), shots=[], log=[], winner=None)
        elif kind == "action":
            self._on_action(m)
        elif kind == "judge":
            self._on_judge(m)
        elif kind == "end_turn":
            self._set_match(round=m.get("next_round"), phase=m.get("next_phase"))
            self._log("end_turn %s -> round %s %s" % (m.get("phase"), m.get("next_round"), m.get("next_phase")))
        elif kind == "round_hash":
            self._log("hash round %s from %s" % (m.get("round"), m.get("seat_id")))
        elif kind == "out_of_sync":
            self.out_of_sync.append(m.get("round"))
            self._log("OUT OF SYNC round %s" % m.get("round"))

    def _log(self, text: str) -> None:
        def apply(data: Dict[str, Any]) -> None:
            match = data.get("match") or {}
            lines = match.get("log", [])
            lines.append(text)
            match["log"] = lines[-14:]
            data["match"] = match
        self.view.mutate(apply)

    def _on_action(self, m: Dict[str, Any]) -> None:
        unit = self.units.get(m.get("unit"))
        shot = {"unit": m.get("unit"), "kind": m.get("kind"), "angle": m.get("angle"), "power": m.get("power"), "start": m.get("start"),
                "landing": m.get("claimed_landing"), "dirX": m.get("dirX"), "seq": m.get("seq"), "hit": None}
        if unit is not None and m.get("start"):
            unit["x"] = round(m["start"]["x"] - 58 * (m.get("dirX") or 1))   # the shooter's real x, from where its shot leaves the hand (about 58 px in front of the body)

        def apply(data: Dict[str, Any]) -> None:
            match = data.get("match") or {}
            shots = match.get("shots", [])
            shots.append(shot)
            match["shots"] = shots[-6:]
            if unit is not None:
                match["units"] = list(self.units.values())
            data["match"] = match
        self.view.mutate(apply)
        self._log("%s throws angle %s power %s" % (m.get("unit"), m.get("angle"), m.get("power")))

    def _on_judge(self, m: Dict[str, Any]) -> None:
        unit_id = m.get("unit")
        if m.get("hit") is True and unit_id in self.units:
            self.hp[unit_id] = float(m.get("hp_after", self.hp[unit_id]))
            self.units[unit_id]["hp"] = self.hp[unit_id]
            self.units[unit_id]["alive"] = self.hp[unit_id] > 0

        def apply(data: Dict[str, Any]) -> None:
            match = data.get("match") or {}
            for shot in match.get("shots", []):
                if shot.get("seq") == m.get("ref") and m.get("hit") is True:
                    shot["hit"] = unit_id
                elif shot.get("seq") == m.get("ref") and shot.get("hit") is None:
                    shot["hit"] = False
            match["units"] = list(self.units.values())
            data["match"] = match
        self.view.mutate(apply)
        if m.get("hit") is True:
            self._log("judge: %s hit, hp %s (-%s)" % (unit_id, m.get("hp_after"), m.get("damage")))
        for team in ("left", "right"):
            ids = [uid for uid in self.units if uid.startswith(team)]
            if ids and all(self.units[uid]["hp"] <= 0 for uid in ids):
                self.winner_seen = "right" if team == "left" else "left"


# ------------------------------------------------------------------ seat kinds
class SeatResult:
    def __init__(self, kind: str, team: str) -> None:
        self.kind = kind
        self.team = team
        self.data: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.exit_code: Optional[int] = None


async def stop_child(proc: Any) -> None:
    """SIGTERM first (the Chrome host takes its browser with it), SIGKILL after 4 s."""
    try:
        proc.terminate()
        await asyncio.wait_for(proc.wait(), 4)
    except (ProcessLookupError, asyncio.TimeoutError):
        try:
            proc.kill()
            await proc.wait()
        except ProcessLookupError:
            pass


async def run_process_seat(kind: str, team: str, command: List[str], timeout: float, log_path: str) -> SeatResult:
    """A node host (headless page or Chrome): it prints one HYBRID_SEAT_RESULT line when its match is over."""
    result = SeatResult(kind, team)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as err:
        env = dict(os.environ)
        report_dir = os.path.join(ROOT, "logs_local", "hybrid_reports")
        env["NODE_OPTIONS"] = (env.get("NODE_OPTIONS", "") + " --report-on-signal --report-signal=SIGUSR2 --report-directory=%s" % report_dir).strip()   # a stuck seat can be asked for its JavaScript stack before it is killed
        proc = await asyncio.create_subprocess_exec(*command, cwd=ROOT, stdout=asyncio.subprocess.PIPE, stderr=err, env=env)
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout)
        except asyncio.CancelledError:   # the other seat failed: do not leave this child (and its Chrome) running
            await stop_child(proc)
            raise
        except asyncio.TimeoutError:
            try:
                proc.send_signal(signal.SIGUSR2)   # a JavaScript stack report first
                await asyncio.sleep(3)
            except ProcessLookupError:
                pass
            await stop_child(proc)
            result.error = "seat process timed out after %ds" % timeout
            return result
    result.exit_code = proc.returncode
    for line in out.decode("utf-8", "replace").splitlines():
        if line.startswith("HYBRID_SEAT_RESULT "):
            try:
                result.data = json.loads(line[len("HYBRID_SEAT_RESULT "):])
            except ValueError:
                result.error = "unreadable result line"
    if result.data is None and result.error is None:
        result.error = "seat process ended without a result (exit %s), see %s" % (proc.returncode, os.path.relpath(log_path, ROOT))
    return result


class McpSeat:
    """The MCP bridge as a real stdio server; this class is the agent: it uses the public tools only (get_public_state, get_history, submit_action, end_turn)."""

    def __init__(self, team: str, relay_url: str, code: str, heroes: Dict[str, List[str]], level: str, rng_seed: int,
                 pace: float, log_path: str, claude: bool = False, page_judge: str = "on", page_speed: float = 8.0) -> None:
        self.page_judge = page_judge
        if page_judge != "on":
            os.environ["PK_ALLOW_BRIDGE_FOR_TESTS"] = "1"   # this research script compares the retired bridge with the page judge
        self.page_speed = page_speed
        self.rng_seed = rng_seed
        self.team = team
        self.relay_url = relay_url
        self.code = code
        self.heroes = heroes
        self.level = level
        self.pace = pace
        self.log_path = log_path
        self.claude = claude
        self.config = agent_levels.level_config(level)
        self.random = random.Random(rng_seed)
        self.proc: Any = None
        self.next_id = 0
        self.wanted = "human" if team == "red" else "agent"
        self.controller = "human" if team == "red" else "subagent"

    async def _rpc(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        self.next_id += 1
        request_id = self.next_id
        self.proc.stdin.write((json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}) + "\n").encode())
        await self.proc.stdin.drain()
        while True:
            line = await asyncio.wait_for(self.proc.stdout.readline(), 30)
            if not line:
                raise RuntimeError("mcp server closed its output")
            reply = json.loads(line)
            if reply.get("id") == request_id:
                return reply

    async def _tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        reply = await self._rpc("tools/call", {"name": name, "arguments": arguments})
        if "error" in reply:
            return {"error": reply["error"].get("message", "rpc error")}
        result = reply["result"]
        payload = json.loads(result["content"][0]["text"])
        if result.get("isError"):
            return {"error": payload.get("error", "tool error")}
        return payload

    async def _choose(self, state: Dict[str, Any], unit_id: str) -> Dict[str, Any]:
        unit = state["units"][unit_id]
        targets = [t for t in state["units"].values() if t["alive"] and t["team"] != unit["team"]]
        target = min(targets, key=lambda t: abs(t["x"] - unit["x"]))
        history = (await self._tool("get_history", {"limit": self.config["memory"], "unit": unit_id, "include_path": False})).get("throws", [])
        if self.claude:
            return await self._claude_decision(state, unit_id, unit, targets, history)
        target_x = float(target["x"]) + self.random.uniform(-self.config["perception_target_px"], self.config["perception_target_px"])
        if history:
            previous = history[-1]
            direction = 1.0 if target_x > float(unit["x"]) else -1.0
            power = float(previous["power"]) + direction * (target_x - float(previous["landing_x"])) / 20.0
        else:
            power = 70.0
        power += self.random.uniform(-self.config["aim_power_error"], self.config["aim_power_error"])
        return {"type": "throw", "angle": 62.0, "power": round(max(20.0, min(100.0, power)), 1)}

    async def _claude_decision(self, state: Dict[str, Any], unit_id: str, unit: Dict[str, Any], targets: List[Dict[str, Any]], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Claude plays: the turn is written to turn.json (public information only), the answer is read from action.json {"angle": 54, "power": 61}."""
        os.makedirs(CLAUDE_DIR, exist_ok=True)
        action_path, turn_path = os.path.join(CLAUDE_DIR, "action.json"), os.path.join(CLAUDE_DIR, "turn.json")
        if os.path.exists(action_path):
            os.remove(action_path)
        view = {"team": self.team, "round": state["round"], "unit": unit_id, "my_x": unit["x"], "wind": state.get("wind"), "weather": state.get("weather"),
                "enemies": [{"id": t["id"] if "id" in t else None, "x": t["x"], "hp": t["hp"], "hero": t.get("hero")} for t in targets],
                "my_hp": {uid: u["hp"] for uid, u in state["units"].items() if u["team"] == self.team},
                "my_recent_throws": [{"angle": h.get("angle"), "power": h.get("power"), "landing_x": h.get("landing_x"), "hit_type": h.get("hit_type")} for h in history[-6:]],
                "write_answer_to": os.path.relpath(action_path, ROOT)}
        with open(turn_path, "w", encoding="utf-8") as handle:
            json.dump(view, handle, indent=1)
        deadline = time.monotonic() + 900
        while time.monotonic() < deadline:
            if os.path.exists(action_path):
                await asyncio.sleep(0.2)
                with open(action_path, encoding="utf-8") as handle:
                    answer = json.load(handle)
                os.remove(action_path)
                return {"type": "throw", "angle": float(answer["angle"]), "power": float(answer["power"])}
            await asyncio.sleep(0.5)
        raise RuntimeError("claude gave no answer in 900 s")

    async def play(self, timeout: float, start_event: Optional[asyncio.Event] = None) -> SeatResult:
        result = SeatResult("claude" if self.claude else "mcp", self.team)
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        command = [sys.executable, "-B", os.path.join(HERE, "mcp_stdio_server.py"), "--connect", self.relay_url + "/ws", "--code", self.code,
                   "--seat", self.team, "--units", str(len(self.heroes["red"])), "--hero-red", *self.heroes["red"], "--hero-white", *self.heroes["white"],
                   "--auto-ready", "--turn-seconds", "3600", "--human-turn-seconds", "3600", "--page-judge", self.page_judge, "--page-speed", str(self.page_speed), "--seed", str(self.rng_seed)]
        started = time.monotonic()
        with open(self.log_path, "w", encoding="utf-8") as err:
            hash_path = self.log_path[:-4] + "_hash.jsonl"
            if os.path.exists(hash_path):
                os.remove(hash_path)
            env = dict(os.environ, PK_HASH_DUMP=hash_path)
            self.proc = await asyncio.create_subprocess_exec(*command, cwd=ROOT, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=err, limit=1 << 22, env=env)
            try:
                await self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "hybrid-runner", "version": "1"}})
                if start_event is not None:
                    await asyncio.wait_for(start_event.wait(), 60)   # the room must have started: an action before `start` is refused by the relay
                done_key = None
                final: Optional[Dict[str, Any]] = None
                state: Dict[str, Any] = {}
                while time.monotonic() - started < timeout:
                    state = await self._tool("get_public_state", {})
                    if "error" in state:
                        result.error = "get_public_state: %s" % state["error"]
                        break
                    if state.get("winner") or state.get("phase") == "over":
                        final = state
                        break
                    key = (state["round"], state["phase"])
                    if state["phase"] == self.wanted and key != done_key:
                        mine = [uid for uid in sorted(state["units"]) if state["units"][uid]["team"] == self.team and state["units"][uid]["alive"] and state["units"][uid]["controller"] == self.controller]
                        if mine:
                            unit_id = mine[0]
                            action = await self._choose(state, unit_id)
                            reply = await self._tool("submit_action", {"unit": unit_id, "round": state["round"], "action": action})
                            if "error" in reply:
                                hint = re.search(r"active unit is (\w+)", reply["error"])
                                if hint and hint.group(1) in mine:
                                    unit_id = hint.group(1)
                                    action = await self._choose(state, unit_id)
                                    reply = await self._tool("submit_action", {"unit": unit_id, "round": state["round"], "action": action})
                            if "error" in reply and "skips this turn" not in reply["error"]:
                                result.error = "submit_action %s: %s" % (unit_id, reply["error"])
                                break
                        ended = await self._tool("end_turn", {"round": state["round"], "phase": state["phase"]})
                        if "error" in ended:
                            result.error = "end_turn: %s" % ended["error"]
                            break
                        done_key = key
                        await asyncio.sleep(self.pace)
                    else:
                        await asyncio.sleep(0.05)
                if final is None and result.error is None:
                    result.error = "mcp seat timed out in round %s phase %s" % (state.get("round"), state.get("phase"))
                if final is not None:
                    await asyncio.sleep(1.0)   # the last judge or hash may still be on its way
                    final = await self._tool("get_public_state", {})
                    result.data = {"team": self.team, "reason": "game_over", "winner": final.get("winner"), "winner_reason": final.get("winner_reason"),
                                   "round": final["round"], "sync": final.get("sync"),
                                   "units": [{"id": world_unit_id(uid), "hero": u["hero"], "hp": u["hp"], "maxHp": u["max_hp"], "team": u["team"]} for uid, u in sorted(final["units"].items())],
                                   "realMs": int((time.monotonic() - started) * 1000)}
            except asyncio.CancelledError:
                result.error = "cancelled because the other seat failed"
            except Exception as exc:
                result.error = "mcp seat: %s: %s" % (type(exc).__name__, exc)
            finally:
                dumps: Dict[str, Any] = {}
                try:
                    with open(hash_path, encoding="utf-8") as handle:
                        for line in handle:
                            row = json.loads(line)
                            dumps[str(row["round"])] = {"hash": row["hash"], "units": [[u[0], round(u[1], 2), round(u[2], 2), round(u[3], 2), u[4]] for u in row["units"]], "wall": row["wall"]}
                except (OSError, ValueError):
                    pass
                if result.data is not None:
                    result.data["hashDumps"] = dumps
                try:
                    self.proc.stdin.close()
                    await asyncio.wait_for(self.proc.wait(), 3)
                except Exception:
                    self.proc.kill()
        return result


# ------------------------------------------------------------------ one match
class Context:
    def __init__(self, args: argparse.Namespace, relay: CountingRelay, view: View, relay_url: str, web_port: Optional[int]) -> None:
        self.args = args
        self.relay = relay
        self.view = view
        self.relay_url = relay_url
        self.web_port = web_port


def seat_command(kind: str, ctx: Context, code: str, team: str, heroes: List[str], level: str, rng: int, args: argparse.Namespace) -> List[str]:
    common = ["--code", code, "--team", team, "--heroes", ",".join(heroes), "--level", level, "--rng", str(rng), "--speed", str(args.speed), "--max-s", str(int(args.match_timeout)), "--gap-ms", str(args.gap_ms)]
    if kind == "headless":
        return ["node", os.path.join("scripts", "hybrid_seat_headless.js"), "--relay", ctx.relay_url] + common
    if kind in ("desktop", "phone"):
        page_host = "localhost" if kind == "phone" else "127.0.0.1"
        relay = "ws://%s:%d" % (page_host, ctx.relay.bound_port)
        page = "http://%s:%d/index.html" % (page_host, ctx.web_port)
        return ["node", os.path.join("scripts", "hybrid_seat_chrome.mjs"), "--kind", kind, "--page-url", page, "--relay", relay, "--cdp-port", str(args.phone_cdp_port)] + common
    raise ValueError(kind)


def hash_diff(seat_results: Dict[str, SeatResult], rounds: List[int]) -> List[str]:
    """For each round whose hashes differed: the first unit field that differs between the two page seats' own hash inputs (world frame)."""
    dumps = {team: (res.data or {}).get("hashDumps") for team, res in seat_results.items()}
    if not all(dumps.values()):
        return []
    names = ["id", "x", "y", "hp", "statuses"]
    out = []
    for r in rounds[:6]:
        a, b = dumps["red"].get(str(r)), dumps["white"].get(str(r))
        if not a or not b:
            continue
        rows_a = {row[0]: row for row in a["units"]}
        rows_b = {row[0]: row for row in b["units"]}
        found = None
        for uid in sorted(rows_a):
            for i in range(1, 5):
                if uid in rows_b and (abs(rows_a[uid][i] - rows_b[uid][i]) > 0.011 if i < 4 else sorted(rows_a[uid][i].split("|")) != sorted(rows_b[uid][i].split("|"))):
                    found = "round %d %s.%s red seat %s vs white seat %s" % (r, uid, names[i], rows_a[uid][i], rows_b[uid][i])
                    break
            if found:
                break
        if not found and a["wall"] != b["wall"]:
            found = "round %d wall %s vs %s" % (r, a["wall"], b["wall"])
        out.append(found or "round %d: same unit rows on both pages" % r)
    return out


def throw_diff(seat_results: Dict[str, SeatResult]) -> Optional[str]:
    """The first throw after which the two page seats disagree on a unit's hp or x (both lists are in world frame, one entry per landed throw, own/foe swapped between the seats)."""
    logs = {team: (res.data or {}).get("throwLog") for team, res in seat_results.items()}
    if not all(logs.values()):
        return None
    a, b = logs["red"], logs["white"]
    for index in range(min(len(a), len(b))):
        rows_a = {row[0]: row for row in a[index]["u"]}
        rows_b = {row[0]: row for row in b[index]["u"]}
        for uid in sorted(rows_a):
            if abs(rows_a[uid][2] - rows_b[uid][2]) > 0.05 or abs(rows_a[uid][1] - rows_b[uid][1]) > 1.0:
                return "throw %d (round %d, %s throw on the red page): %s hp %s vs %s, x %s vs %s (red page vs white page)" % (
                    index + 1, a[index]["r"], a[index]["t"], uid, rows_a[uid][2], rows_b[uid][2], rows_a[uid][1], rows_b[uid][1])
    if len(a) != len(b):
        return "the pages landed %d and %d throws" % (len(a), len(b))
    return None


def combine(plan: Dict[str, Any], size: int, seat_results: Dict[str, SeatResult], spectator: Spectator) -> Dict[str, Any]:
    """The match record in world frame (left = red seat), from the seats' own final states; the two seats and the spectator are cross-checked."""
    errors: List[str] = []
    worlds: Dict[str, Dict[str, Any]] = {}
    for team, res in seat_results.items():
        if res.error or not res.data:
            errors.append("%s seat (%s): %s" % (team, res.kind, res.error or "no result"))
            continue
        data = res.data
        if "units" not in data and ("own" not in data or "foe" not in data):
            errors.append("%s seat (%s) ended without a final state: %s" % (team, res.kind, "; ".join(data.get("errors", [])[:2]) or data.get("reason")))
            continue
        if data.get("errors"):
            errors.append("%s seat (%s) page errors: %s" % (team, res.kind, "; ".join(data["errors"][:3])))
        if data.get("reason") not in ("game_over", None):
            errors.append("%s seat (%s) ended with reason %s" % (team, res.kind, data.get("reason")))
        if "units" in data:   # mcp: world frame already
            units = {u["id"]: {"hp": u["hp"], "max": u["maxHp"], "hero": u["hero"]} for u in data["units"]}
            winner = data.get("winner")
            winner_side = {"red": "left", "white": "right"}.get(winner)
            capped = data.get("winner_reason") == "round_cap"
            rounds = data["round"]
            counters = None
        else:   # page: own = local left
            own_side, foe_side = ("left", "right") if team == "red" else ("right", "left")
            units = {}
            for index, u in enumerate(data["own"]):
                units["%s_%d" % (own_side, index)] = {"hp": u["hp"], "max": u["maxHp"], "hero": u["hero"]}
            for index, u in enumerate(data["foe"]):
                units["%s_%d" % (foe_side, index)] = {"hp": u["hp"], "max": u["maxHp"], "hero": u["hero"]}
            own_down = all(u["hp"] <= 0 for u in data["own"])
            foe_down = all(u["hp"] <= 0 for u in data["foe"])
            if data.get("gameOver") is None:
                winner_side, capped = None, False
            else:
                capped = not own_down and not foe_down
                winner_side = own_side if data["gameOver"] == "player" else foe_side
            rounds = min(data["roundNum"] - 1, data["cap"]) if capped else data["roundNum"]
            counters = data["counters"]
        worlds[team] = {"units": units, "winner": winner_side, "capped": capped, "rounds": rounds, "counters": counters, "res": data}
    record: Dict[str, Any] = {"winner": "none", "rounds": 0, "hp_share_left": None, "hp_share_right": None, "units_left_alive": None, "units_right_alive": None,
                              "throws": 0, "direct_hits": 0, "near_misses": None, "pity_triggers": None, "comeback_hits": None, "ultimates_left": 0, "ultimates_right": 0}
    if worlds:
        base = worlds.get("red") or next(iter(worlds.values()))
        # seats agree?
        for team, other in worlds.items():
            if other is base:
                continue
            if other["winner"] != base["winner"]:
                errors.append("seats disagree on the winner: %s vs %s" % (base["winner"], other["winner"]))
            for uid, row in base["units"].items():
                if uid in other["units"] and abs(row["hp"] - other["units"][uid]["hp"]) > 0.25:
                    errors.append("seats disagree on hp of %s: %s vs %s" % (uid, row["hp"], other["units"][uid]["hp"]))
                    break
        left = {uid: r for uid, r in base["units"].items() if uid.startswith("left")}
        right = {uid: r for uid, r in base["units"].items() if uid.startswith("right")}

        def share(units: Dict[str, Any]) -> float:
            maximum = sum(u["max"] for u in units.values())
            return round(sum(max(0, u["hp"]) for u in units.values()) / maximum, 4) if maximum else 0.0
        record["hp_share_left"], record["hp_share_right"] = share(left), share(right)
        record["units_left_alive"] = sum(1 for u in left.values() if u["hp"] > 0)
        record["units_right_alive"] = sum(1 for u in right.values() if u["hp"] > 0)
        if base["winner"]:
            record["winner"] = ("cap_" if base["capped"] else "") + base["winner"]
        record["rounds"] = base["rounds"]
        page = next((w for w in (worlds.get("red"), worlds.get("white")) if w and w["counters"]), None)
        if page:
            c = page["counters"]
            record["throws"] = c["throwsOwn"] + c["throwsFoe"]
            record["direct_hits"] = c["directOwn"] + c["directFoe"]
            record["near_misses"], record["pity_triggers"], record["comeback_hits"] = c["near"], c["pity"], c["comeback"]
    if record["winner"] == "none" and not errors:
        errors.append("no winner reported")
    record["errors"] = errors
    return record


async def play_match(ctx: Context, spec: Dict[str, Any]) -> Dict[str, Any]:
    args = ctx.args
    size = args.size
    plan = match_plan(spec["seed"], size)
    kinds = {"red": spec["left"], "white": spec["right"]}
    tiers = {"red": plan["tier_left"], "white": plan["tier_right"]}
    heroes = {"red": plan["heroes_left"], "white": plan["heroes_right"]}
    label = "%s (left) vs %s (right) seed %d" % (spec["left"], spec["right"], spec["seed"])
    log("MATCH %s: heroes %s | %s, strength %s | %s" % (label, ",".join(heroes["red"]), ",".join(heroes["white"]), tiers["red"], tiers["white"]))
    started = time.monotonic()
    error_mark = len(ctx.relay.error_log)
    spectator = Spectator("ws://127.0.0.1:%d" % ctx.relay.bound_port, size, ctx.view, label, plan)
    ctx.view.update(status="playing", match={"label": label, "seat_left": spec["left"], "seat_right": spec["right"], "heroes_left": heroes["red"], "heroes_right": heroes["white"],
                                             "tier_left": tiers["red"], "tier_right": tiers["white"], "units": [], "shots": [], "log": [], "round": 1, "phase": None, "winner": None})
    code = await spectator.open()
    ctx.view.mutate(lambda d: d["match"].update(code=code))
    tasks = {}
    logs = os.path.join(ROOT, "logs_local", "hybrid_seats")
    for team in ("red", "white"):
        kind = kinds[team]
        rng = (spec["seed"] * 31 + (1 if team == "red" else 2)) & 0xFFFFFFFF
        seat_log = os.path.join(logs, "%d_%s_%s.log" % (spec["seed"], team, kind))
        if kind in ("mcp", "claude"):
            seat = McpSeat(team, "ws://127.0.0.1:%d" % ctx.relay.bound_port, code, heroes, tiers[team], rng, args.mcp_pace, seat_log, claude=(kind == "claude"), page_judge=args.mcp_judge, page_speed=args.speed)
            tasks[team] = asyncio.ensure_future(seat.play(args.match_timeout, spectator.started))
        else:
            command = seat_command(kind, ctx, code, team, heroes[team], tiers[team], rng, args)
            tasks[team] = asyncio.ensure_future(run_process_seat(kind, team, command, args.match_timeout + 40, seat_log))
    seat_results: Dict[str, SeatResult] = {}
    for team, task in tasks.items():
        try:
            seat_results[team] = await task
        except asyncio.CancelledError:
            res = SeatResult(kinds[team], team)
            res.error = "cancelled because the other seat failed"
            seat_results[team] = res
        except Exception as exc:
            res = SeatResult(kinds[team], team)
            res.error = "%s: %s" % (type(exc).__name__, exc)
            seat_results[team] = res
        if seat_results[team].error:
            for other in tasks.values():   # one seat failed: do not wait the full time for the other
                if not other.done():
                    other.cancel()
    for team, task in tasks.items():
        if team not in seat_results:
            res = SeatResult(kinds[team], team)
            res.error = "cancelled"
            seat_results[team] = res
    await asyncio.sleep(1.0)   # last broadcasts to the spectator
    room = ctx.relay.rooms.get(code)
    hash_rounds = {}
    if room is not None:
        hash_rounds = {r: dict(h) for r, h in room.round_hashes.items()}
    hash_disagree = sorted(r for r, h in hash_rounds.items() if len(set(h.values())) > 1)
    hash_missing = sorted(r for r, h in hash_rounds.items() if len(h) < 2)
    relay_errors = [e["code"] for e in ctx.relay.error_log[error_mark:]]
    await spectator.close()
    record = combine(plan, size, seat_results, spectator)
    mismatches = len(set(hash_disagree) | set(spectator.out_of_sync))
    first_split = throw_diff(seat_results)
    if first_split and (record["errors"] or mismatches):
        record["errors"].append("first difference between the pages: " + first_split)
    record.update({
        "end": "hybrid", "pair": "%s:%s" % tuple(sorted([spec["left"], spec["right"]])), "seat_left": spec["left"], "seat_right": spec["right"],
        "hero": plan["hero"], "hero_right": plan["hero_right"], "heroes_left": heroes["red"], "heroes_right": heroes["white"], "size": size,
        "seed": spec["seed"], "relay_seed": spectator.start["seed"] if spectator.start else None, "tier_left": tiers["red"], "tier_right": tiers["white"],
        "relay_errors": relay_errors, "hash_mismatches": mismatches, "hash_rounds": len(hash_rounds), "hash_disagree_rounds": hash_disagree,
        "ms": int((time.monotonic() - started) * 1000), "code": code,
        "seats": {team: (res.data if res.data else {"error": res.error}) for team, res in seat_results.items()},
    })
    if record["errors"] or relay_errors or mismatches:   # the ordered action and judge messages of a failing match, to replay a throw offline
        keep = ("type", "seq", "round", "phase", "unit", "kind", "angle", "power", "start", "dirX", "claimed_landing", "ref", "hit", "damage", "hp_after", "statuses", "knockback", "seat_id")
        record["messages"] = [{k: m[k] for k in keep if k in m} for m in spectator.messages if m.get("type") in ("action", "judge", "end_turn")]
    if not record["errors"] and not relay_errors and not mismatches:
        for data in record["seats"].values():   # the per-round and per-throw dumps are for tracing a difference only
            for key in ("hashDumps", "throwLog"):
                data.pop(key, None)
    if relay_errors:
        record["errors"].append("relay errors: %s" % ",".join(relay_errors[:8]))
        record["relay_error_context"] = [e["while"] for e in ctx.relay.error_log[error_mark:]][:6]
    if mismatches:
        record["errors"].append("round hash mismatches in rounds %s" % sorted(set(hash_disagree) | set(spectator.out_of_sync)))
        record["hash_diff"] = hash_diff(seat_results, sorted(set(hash_disagree) | set(spectator.out_of_sync)))
    summary = {"label": label, "winner": record["winner"], "rounds": record["rounds"], "errors": len(record["errors"]), "relay_errors": len(relay_errors), "hash_mismatches": mismatches}
    ctx.view.mutate(lambda d: (d["finished"].append(summary), d.update(status="between")))
    log("  -> %s in %s rounds, %d s, relay errors %d, hash mismatches %d, errors %s" % (record["winner"], record["rounds"], record["ms"] // 1000, len(relay_errors), mismatches, record["errors"][:2]))
    return record


# ------------------------------------------------------------------ the run and the report
def pair_specs(kinds: List[str], pairs: Optional[str], matches: int, seed_base: int) -> List[Dict[str, Any]]:
    if pairs:
        chosen = [tuple(p.split(":")) for p in pairs.split(",")]
    else:
        chosen = list(itertools.combinations_with_replacement(kinds, 2))
    specs = []
    for index, (a, b) in enumerate(chosen):
        for k in range(matches):
            left, right = (a, b) if k % 2 == 0 else (b, a)   # both kinds play both sides
            specs.append({"pair": "%s:%s" % tuple(sorted([a, b])), "k": k, "left": left, "right": right, "seed": seed_base + 100 * index + k})
    return specs


def table(matches: List[Dict[str, Any]]) -> str:
    pairs: Dict[str, List[Dict[str, Any]]] = {}
    for m in matches:
        pairs.setdefault(m["pair"], []).append(m)
    lines = ["| seat pair | matches | win share of the first-named kind | left seat win share | rounds mean | relay errors | hash mismatches | other errors | seconds per match |",
             "|---|---|---|---|---|---|---|---|---|"]
    for pair, rows in sorted(pairs.items()):
        first = pair.split(":")[0]
        decided = [m for m in rows if m["winner"] != "none"]
        first_wins = sum(1 for m in decided if (m["winner"].endswith("left") and m["seat_left"] == first) or (m["winner"].endswith("right") and m["seat_right"] == first))
        left_wins = sum(1 for m in decided if m["winner"].endswith("left"))
        rounds = [m["rounds"] for m in rows if m["rounds"]]
        other = sum(1 for m in rows if [e for e in m["errors"] if not e.startswith("relay errors") and not e.startswith("round hash")])
        lines.append("| %s | %d | %s | %s | %s | %d | %d | %d | %s |" % (
            pair.replace(":", " vs "), len(rows), "%d%% (%d/%d)" % (round(100 * first_wins / len(decided)), first_wins, len(decided)) if decided else "-",
            "%d%%" % round(100 * left_wins / len(decided)) if decided else "-", "%.1f" % (sum(rounds) / len(rounds)) if rounds else "-",
            sum(len(m["relay_errors"]) for m in rows), sum(m["hash_mismatches"] for m in rows), other, "%.0f" % (sum(m["ms"] for m in rows) / len(rows) / 1000)))
    return "\n".join(lines)


def write_report(path: str, data: Dict[str, Any]) -> None:
    matches = data["matches"]
    bad = [m for m in matches if m["errors"] or m["relay_errors"] or m["hash_mismatches"]]
    out = ["# Hybrid room run (%s)" % datetime.date.today().isoformat(), "",
           "Generated by `scripts/run_hybrid_room.py` from `%s`. Option A of `docs/SIX_SEAT_HYBRID_PLAN_20261117.md`: two seats per match, each seat plays a whole team of %s units, mixed teams, red opens every round, strength hidden and random per AI seat." % (data.get("source", "logs_local/hybrid_run.json"), data.get("size", 3)),
           "", "Target: zero relay errors and zero round-hash mismatches. Result: **%d matches, %d with an error, %d relay errors, %d hash mismatches**." % (
               len(matches), len(bad), sum(len(m["relay_errors"]) for m in matches), sum(m["hash_mismatches"] for m in matches)), "",
           table(matches), ""]
    if data.get("skipped"):
        out += ["## Not run", ""] + ["- %s: %s" % (k, v) for k, v in data["skipped"].items()] + [""]
    if bad:
        out += ["## Matches with an error", ""]
        for m in bad[:40]:
            out.append("- seed %d, %s (left) vs %s (right): %s" % (m["seed"], m["seat_left"], m["seat_right"], "; ".join(m["errors"][:3])[:300]))
        out.append("")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(out) + "\n")


def chrome_available() -> Optional[str]:
    candidates = [os.environ.get("CHROME_PATH", ""), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Chromium.app/Contents/MacOS/Chromium", "/usr/bin/google-chrome", "/usr/bin/chromium"]
    return next((c for c in candidates if c and os.path.exists(c)), None)


def port_open(port: int) -> bool:
    with socket.socket() as probe:
        probe.settimeout(0.5)
        return probe.connect_ex(("127.0.0.1", port)) == 0


async def main_async(args: argparse.Namespace) -> int:
    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    kinds = [k for k in args.kinds.split(",") if k]
    skipped: Dict[str, str] = {}
    for kind in list(kinds):
        reason = None
        if kind not in KINDS:
            reason = "unknown seat kind"
        elif kind == "desktop" and not chrome_available():
            reason = "Chrome not found (set CHROME_PATH)"
        elif kind == "phone" and not port_open(args.phone_cdp_port):
            reason = "no phone Chrome DevTools on 127.0.0.1:%d (adb forward tcp:%d localabstract:chrome_devtools_remote)" % (args.phone_cdp_port, args.phone_cdp_port)
        elif kind == "headless" and shutil.which("node") is None:
            reason = "node not found"
        if reason:
            skipped[kind] = reason
            kinds.remove(kind)
            log("seat kind %s not run: %s" % (kind, reason))
    if args.pairs:
        wanted = {k for p in args.pairs.split(",") for k in p.split(":")}
        kinds = sorted(wanted - set(skipped), key=KINDS.index)
    specs = [s for s in pair_specs(kinds, args.pairs, args.matches, args.seed_base) if s["left"] in kinds and s["right"] in kinds]
    done: List[Dict[str, Any]] = []
    if args.resume and os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as handle:
            done = [m for m in json.load(handle).get("matches", []) if not m["errors"] and not m["relay_errors"] and not m["hash_mismatches"]]
    finished = {m["seed"] for m in done}
    todo = [s for s in specs if s["seed"] not in finished]
    view = View()
    viewer = start_viewer(view, args.viewer_port)
    if viewer:
        log("spectator page: http://127.0.0.1:%d/" % args.viewer_port)
    relay = CountingRelay("127.0.0.1", args.relay_port)
    await relay.start()
    relay_url = "ws://127.0.0.1:%d" % relay.bound_port
    log("relay on %s; %d matches to play (%d kept from the result file); kinds %s" % (relay_url, len(todo), len(done), kinds))
    web: Optional[subprocess.Popen] = None
    web_port = args.web_port
    if any(k in ("desktop", "phone") for k in kinds):
        web = subprocess.Popen([sys.executable, "-B", os.path.join("scripts", "dev_server.py"), str(web_port)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            if port_open(web_port):
                break
            await asyncio.sleep(0.1)
    ctx = Context(args, relay, view, relay_url, web_port)
    matches = list(done)
    started = datetime.datetime.now().isoformat(timespec="seconds")

    def save(finished_at: Optional[str]) -> None:
        payload = {"end": "hybrid", "source": os.path.relpath(out_path, ROOT), "size": args.size, "started": started, "finished": finished_at, "kinds": kinds, "skipped": skipped, "matches": matches}
        with open(out_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1)
            handle.write("\n")
    try:
        for spec in todo:
            try:
                record = await play_match(ctx, spec)
            except Exception as exc:
                log("match crashed: %s" % traceback.format_exc().splitlines()[-1])
                plan = match_plan(spec["seed"], args.size)
                record = {"end": "hybrid", "pair": spec["pair"], "seat_left": spec["left"], "seat_right": spec["right"], "size": args.size, "seed": spec["seed"], "winner": "none", "rounds": 0,
                          "errors": ["runner crash: %s: %s" % (type(exc).__name__, exc)], "relay_errors": [], "hash_mismatches": 0, "ms": 0, "tier_left": plan["tier_left"], "tier_right": plan["tier_right"]}
            matches.append(record)
            save(None)
        save(datetime.datetime.now().isoformat(timespec="seconds"))
    finally:
        await relay.close()
        if web:
            web.terminate()
        if viewer:
            viewer.shutdown()
    if args.report:
        write_report(os.path.abspath(args.report), {"matches": matches, "skipped": skipped, "size": args.size, "source": os.path.relpath(out_path, ROOT)})
        log("report -> %s" % args.report)
    print(table(matches))
    bad = [m for m in matches if m["errors"] or m["relay_errors"] or m["hash_mismatches"]]
    log("run_hybrid_room: %d matches, %d with errors, %d relay errors, %d hash mismatches -> %s" % (
        len(matches), len(bad), sum(len(m["relay_errors"]) for m in matches), sum(m["hash_mismatches"] for m in matches), os.path.relpath(out_path, ROOT)))
    for m in bad[:10]:
        print("ERROR seed %s (%s left vs %s right): %s" % (m["seed"], m["seat_left"], m["seat_right"], "; ".join(m["errors"][:2])[:240]))
    return 1 if bad else 0


def main() -> int:
    today = datetime.date.today().strftime("%Y%m%d")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--kinds", default="headless,mcp,desktop,phone", help="seat kinds to pair up (every unordered pair, same kind included)")
    parser.add_argument("--pairs", default=None, help="explicit pairs such as headless:mcp,mcp:mcp (overrides --kinds pairing)")
    parser.add_argument("--matches", type=int, default=10, help="matches per pair; both kinds play both sides")
    parser.add_argument("--size", type=int, default=3, choices=[2, 3], help="units per team (1 is the plain duel, not a team room)")
    parser.add_argument("--seed-base", type=int, default=9000)
    parser.add_argument("--speed", type=float, default=8, help="page seats: fake seconds per real second. Both pages must run at the same rate (an unlimited seat races ahead and the pages part, see docs/HYBRID_RUN); 1 is real time, 4 is good to watch")
    parser.add_argument("--gap-ms", type=int, default=130, help="page seats: minimum gap between two relay messages of one socket (the relay refuses more than 10 a second)")
    parser.add_argument("--mcp-pace", type=float, default=0.4, help="MCP seat: seconds between two of its turns (same reason)")
    parser.add_argument("--mcp-judge", default="on", choices=["on", "off"], help="MCP seat: judge with the real page (on) or the engine's own approximation (off, the old bridge)")
    parser.add_argument("--match-timeout", type=float, default=300)
    parser.add_argument("--relay-port", type=int, default=0, help="0 = any free port; the phone needs a fixed one (adb reverse)")
    parser.add_argument("--web-port", type=int, default=8080, help="static server for the Chrome seats")
    parser.add_argument("--viewer-port", type=int, default=8099)
    parser.add_argument("--phone-cdp-port", type=int, default=9333)
    parser.add_argument("--out", default=os.path.join(ROOT, "logs_local", "hybrid_run_%s.json" % today))
    parser.add_argument("--report", default=None, help="write the markdown table here at the end")
    parser.add_argument("--report-only", default=None, metavar="MD", help="rebuild the table from --out and exit")
    parser.add_argument("--resume", action="store_true", help="keep the clean matches already in --out")
    args = parser.parse_args()
    if args.report_only:
        with open(args.out, encoding="utf-8") as handle:
            data = json.load(handle)
        write_report(os.path.abspath(args.report_only), data)
        print("report -> %s" % args.report_only)
        return 0
    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        log("stopped")
        return 130


if __name__ == "__main__":
    sys.exit(main())
