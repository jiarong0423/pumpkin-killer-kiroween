#!/usr/bin/env python3
"""Pumpkin Killer: standard MCP server over stdio (newline-delimited JSON-RPC 2.0).

Stdlib only. Wraps the rules engine in `mcp_game_server.GameState` (physics untouched)
and exposes it through the standard MCP handshake and tools:

  get_public_state, get_history, submit_action, end_turn, set_notes, get_notes

Design notes
- The engine class is subclassed (`TrackedGameState`), not edited. The subclass records, for
  every throw, the round, the wind at throw time, and a sampled flight path (every 6th
  integration step) by re-integrating the throw with the engine's own formula and constants.
- Agents learn from `get_history`. No tool returns the RNG seed, pending (unsubmitted)
  actions, or the dice stream. Human throw angle/power are not published, only landings and paths.
- Phases per round: "human" (human-controlled units), then "agent" (subagent units, 12 s
  timeout), then the engine resolves the round. Units that did not act idle.
- The timeout is evaluated lazily at the next tool call (no threads, injectable clock).
- Optional staging on disk (`--memory-dir` or env PK_MEMORY_DIR), layout from
  docs/agent_memory_paths.md. Off by default because `data/` is not in .gitignore.
"""
import argparse
import asyncio
import subprocess
import hashlib
import json
import math
import os
import queue
import random
import re
import shutil
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import mcp_game_server as engine  # noqa: E402  (same directory)
import adaptive_level  # noqa: E402
import comeback_py  # noqa: E402
import determinism_py  # noqa: E402
from flight_py import simulate as simulate_flight  # noqa: E402
from round_hash_py import engine_unit_id, hash_state as round_hash, world_unit_id  # noqa: E402
from weather_py import apply_attack, apply_move, for_round  # noqa: E402

_REPO_ROOT = os.path.dirname(_HERE)
_CONSTANTS_PATH = os.path.join(_REPO_ROOT, "shared", "constants.json")
with open(_CONSTANTS_PATH, "r", encoding="utf-8") as _fh:
    SHARED: Dict[str, Any] = json.load(_fh)

SERVER_NAME = "pumpkin-killer"
SERVER_VERSION = "0.1.0"
SUPPORTED_PROTOCOLS = ["2025-06-18", "2025-03-26", "2024-11-05"]

GROUND_Y = SHARED["GROUND_Y"]
GRAVITY = SHARED["GRAVITY"]
V0_PER_POWER = SHARED["V0_PER_POWER"]
TURN_SECONDS = float(SHARED.get("TURN_SECONDS", 12))
# docs/game_mode.md (confirmed): 36 px per pip. The first task text said 16; change here only.
MOVE_PX_PER_PIP = int(SHARED.get("MOVE_PX_PER_PIP", 36))

# Same literals the engine uses inside resolve_round (see mcp_game_server.py).
STEP_DT = 1.0 / 60.0
MAX_STEPS = 300
WIND_PUSH_TAIL = 52.5   # about 0.9375 x the client's tailwind 56 (2026-11-16: tailwind and headwind differ)
WIND_PUSH_HEAD = 78.75     # about 0.9375 x the client's headwind 84
WIND_PUSH = WIND_PUSH_TAIL   # kept as a name for old readers
# (2026-11-17: no longer approximate: engine and sample_path use the same acceleration as the page.) Old note: the client uses acceleration (vx += wind*WIND_TAIL/WIND_HEAD*dt, 56/84), this server a constant drift; they agree at a flight time of about 1.9 s (typical flights are 1.1 to 1.8 s)
RELEASE_DX = 25
RELEASE_DY = 65
PATH_STEP = 6
RELAY_SEND_GAP_SECONDS = 0.11   # at most about 9 messages a second to the relay (pk_relay.MAX_MESSAGES_PER_SECOND is 10)
COARSE_PATH_POINTS = 5
COARSE_PATH_GRID = 10

ANGLE_MIN, ANGLE_MAX = 25.0, 80.0  # docs/game_mode.md
POWER_MIN, POWER_MAX = 0.0, 115.0
MAX_ULTIMATES_PER_MATCH = 2
REMEMBERED_PATHS = 4
MAX_NOTES_CHARS = 2000
HISTORY_MAX = 50
SEAT_IDS = ("referee", "red", "white", "spectator")

TEAM_X_LIMITS = engine.MOVE_X_LIMITS  # same allowed zones as the page's move code
SHIELD_AIRSPACE_X = {"red": (180.0, 850.0), "white": (1070.0, 1780.0)}  # mirrors engine.submit_defend
SHIELD_AIRSPACE_Y = (220.0, 680.0)

CLASS_BY_NAME = {key: key for key in engine.HERO_TEMPLATES}


class ToolError(Exception):
    """A tool call that must be reported with isError=true."""


# ------------------------------------------------------------------ flight path sampling
def sample_path(origin_x: float, origin_y: float, facing: int, angle: float, power: float,
                wind: float, landing_x: float, landing_y: float,
                launch: Dict[str, float]) -> List[List[float]]:
    """Re-integrate an engine throw using its hero-specific release point."""
    angle_rad = math.radians(angle)
    v0 = power * V0_PER_POWER
    vx = v0 * math.cos(angle_rad) * facing
    vy = -v0 * math.sin(angle_rad)
    cur_x = float(origin_x + launch["fwd"] * facing)
    cur_y = float(origin_y - launch["up"])
    points: List[List[float]] = [[round(cur_x, 1), round(cur_y, 1)]]
    for step in range(1, MAX_STEPS + 1):
        vx += wind * (engine._WIND_TAIL if wind * facing > 0 else engine._WIND_HEAD) * STEP_DT   # the page's step: wind is an acceleration (2026-11-17: the engine and this path used a constant drift before)
        vy += GRAVITY * STEP_DT
        prev_x, prev_y = cur_x, cur_y
        cur_x += vx * STEP_DT
        cur_y += vy * STEP_DT
        # the engine hit point can now lie BETWEEN two steps (swept contact every 3 px, 2026-11-18): stop at the step whose segment passes through the landing point
        seg_x, seg_y = cur_x - prev_x, cur_y - prev_y
        seg2 = seg_x * seg_x + seg_y * seg_y
        t_on = ((landing_x - prev_x) * seg_x + (landing_y - prev_y) * seg_y) / seg2 if seg2 > 0 else 0.0
        on_segment = 0.0 <= t_on <= 1.0 and math.hypot(prev_x + seg_x * t_on - landing_x, prev_y + seg_y * t_on - landing_y) <= 1.0
        on_ground = landing_y == GROUND_Y and cur_y >= GROUND_Y
        at_landing = round(cur_x, 1) == landing_x and (round(cur_y, 1) == landing_y or on_ground)
        if at_landing or on_segment or step == MAX_STEPS:
            break
        if step % PATH_STEP == 0:
            points.append([round(cur_x, 1), round(cur_y, 1)])
    points.append([landing_x, landing_y])
    return points


class TrackedGameState(engine.GameState):
    """Engine subclass: no built-in AI autofill, and a per-throw log with wind and path."""

    def __init__(self, mode: str = "human_vs_agent", seed: Optional[int] = None,
                 units: int = 3, hero_red: Any = None, hero_white: Any = None) -> None:
        super().__init__(mode=mode, seed=seed, units=units, hero_red=hero_red, hero_white=hero_white)
        self.throw_log: List[Dict[str, Any]] = []
        self.next_throw_id = 1

    def compute_subagent_throw(self, unit_id: str) -> Dict[str, Any]:
        # Agents act only through tools. An empty dict means "no throw": the unit idles.
        return {}

    def resolve_round(self) -> Dict[str, Any]:
        round_resolved = self.round_num
        wind_at_throw = self.wind
        eff_wind_at_throw = self.effective_wind()   # what the flight really used (storm bonus included), for the sampled path
        result = super().resolve_round()
        for rec in result["results"]:
            launch = rec.pop("_launch", None)
            if "landing_x" not in rec or not isinstance(launch, dict):
                continue
            self.throw_log.append({
                "throw_id": self.next_throw_id,
                "round": round_resolved,
                "team": rec["team"],
                "unit": rec["unit_id"],
                "controller": rec["controller"],
                "angle": rec["angle"],
                "power": rec["power"],
                "wind_at_throw": wind_at_throw,
                "landing_x": rec["landing_x"],
                "landing_y": rec["landing_y"],
                "hit_type": rec["hit_type"],
                "hit_target": rec["hit_target"],
                "damage_dealt": rec["damage_dealt"],
                "critical": rec.get("critical", False),
                "statuses": list(rec.get("statuses", [])),
                "knockback": rec.get("knockback", 0),
                "ultimate": bool(rec.get("ultimate", False)),
                **({"near_miss": rec["near_miss"]} if "near_miss" in rec else {}),
                "path": sample_path(launch["x"], launch["y"], launch["facing"], rec["angle"],
                                    rec["power"], eff_wind_at_throw, rec["landing_x"], rec["landing_y"],
                                    launch["launch"]),
            })
            self.next_throw_id += 1
        return result


def coarse_path(points: List[List[float]]) -> List[List[float]]:
    """Expose no more than five 10 px grid points from an opponent's flight."""
    if not points:
        return []
    count = min(COARSE_PATH_POINTS, len(points))
    indexes = [round(index * (len(points) - 1) / max(1, count - 1)) for index in range(count)]
    return [[float(round(points[index][0] / COARSE_PATH_GRID) * COARSE_PATH_GRID),
             float(round(points[index][1] / COARSE_PATH_GRID) * COARSE_PATH_GRID)]
            for index in indexes]


def public_throw(rec: Dict[str, Any], include_path: bool = True,
                 reveal_aim: Optional[bool] = None, coarse: bool = False) -> Dict[str, Any]:
    """Return a throw record without exposing an opponent's aim."""
    out = {k: rec[k] for k in ("throw_id", "round", "team", "unit", "controller", "wind_at_throw",
                               "landing_x", "landing_y", "hit_type", "hit_target", "damage_dealt",
                               "critical", "statuses", "knockback", "near_miss") if k in rec}
    show_aim = rec["controller"] != "human" if reveal_aim is None else reveal_aim
    if show_aim:
        out["angle"] = rec["angle"]
        out["power"] = rec["power"]
    if include_path:
        out["path"] = coarse_path(rec["path"]) if coarse else rec["path"]
    return out


# ------------------------------------------------------------------ argument validation
def _reject_unknown(args: Dict[str, Any], allowed: Tuple[str, ...], where: str) -> None:
    extra = sorted(set(args) - set(allowed))
    if extra:
        raise ToolError(f"unknown argument(s) in {where}: {', '.join(extra)}")


def _number(value: Any, name: str, lo: float, hi: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ToolError(f"{name} must be a number")
    number = float(value)
    if not math.isfinite(number):
        raise ToolError(f"{name} must be finite")
    if number < lo or number > hi:
        raise ToolError(f"{name} must be between {lo:g} and {hi:g}")
    return number


def _integer(value: Any, name: str, lo: int, hi: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ToolError(f"{name} must be an integer")
    if isinstance(value, float) and (not math.isfinite(value) or not value.is_integer()):
        raise ToolError(f"{name} must be an integer")
    number = int(value)
    if number < lo or number > hi:
        raise ToolError(f"{name} must be between {lo} and {hi}")
    return number


def _string(value: Any, name: str, max_len: int = 200) -> str:
    if not isinstance(value, str) or not value:
        raise ToolError(f"{name} must be a non-empty string")
    if len(value) > max_len:
        raise ToolError(f"{name} is longer than {max_len} characters")
    return value


def _enum(value: Any, name: str, options: Tuple[str, ...]) -> str:
    if value not in options:
        raise ToolError(f"{name} must be one of: {', '.join(options)}")
    return value


# ------------------------------------------------------------------ staging on disk
class MatchStore:
    """Writes the match folder described in docs/agent_memory_paths.md (public data only).

    Deviations: no seed in meta.json and the folder id uses the engine match_id, because an agent
    with file access could otherwise read the seed. Failures are logged, never raised.
    """

    def __init__(self, root: str, match_id: str, mode: str) -> None:
        now = datetime.now(timezone.utc)
        self.root = root
        self.rel = os.path.join("matches", now.strftime("%Y%m%d"),
                                "%s-%s" % (now.strftime("%Y%m%dT%H%M%SZ"), match_id))
        self.dir = os.path.join(root, self.rel)
        self.match_id = match_id
        self.date = now.strftime("%Y-%m-%d")
        try:
            os.makedirs(self.dir, exist_ok=True)
            version_file = os.path.join(root, "schema_version.json")
            if not os.path.exists(version_file):
                self._write(version_file, json.dumps({"version": 1}))
            with open(_CONSTANTS_PATH, "rb") as fh:
                digest = hashlib.sha256(fh.read()).hexdigest()[:16]
            self.write_json("meta.json", {"match_id": match_id, "started_at": now.isoformat(),
                                          "mode": mode, "constants_sha256": digest})
        except OSError as exc:
            self._log(exc)

    @staticmethod
    def _log(exc: Exception) -> None:
        sys.stderr.write("memory store error (ignored): %s\n" % exc)

    @staticmethod
    def _write(path: str, text: str) -> None:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)

    def write_json(self, name: str, obj: Any) -> None:
        try:
            self._write(os.path.join(self.dir, name), json.dumps(obj, ensure_ascii=False, indent=2))
        except OSError as exc:
            self._log(exc)

    def write_history(self, records: List[Dict[str, Any]]) -> None:
        text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
        try:
            self._write(os.path.join(self.dir, "history.jsonl"), text)
        except OSError as exc:
            self._log(exc)

    def finish(self, winner: Optional[str], rounds: int, hit_rate_by_round: Dict[str, float]) -> None:
        self.write_json("result.json", {"winner": winner, "rounds": rounds,
                                        "hit_rate_by_round": hit_rate_by_round, "ultimates_used": 0})
        try:
            line = json.dumps({"match_id": self.match_id, "date": self.date, "winner": winner,
                               "path": self.rel.replace(os.sep, "/")})
            with open(os.path.join(self.root, "index.jsonl"), "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            self._log(exc)


# ------------------------------------------------------------------ the match session
class Session:
    """One match: the engine plus phases, per-turn action bookkeeping, timer and notes."""

    def __init__(self, mode: str = "human_vs_agent", seed: Optional[int] = None,
                 clock: Callable[[], float] = time.monotonic, turn_seconds: float = TURN_SECONDS,
                 human_turn_seconds: float = TURN_SECONDS, memory_dir: Optional[str] = None,
                 engine_cls: Any = TrackedGameState, seat: str = "referee", units: int = 3,
                 hero_red: Any = None, hero_white: Any = None) -> None:
        self._engine_cls = engine_cls
        self._engine_options = {"mode": mode, "seed": seed, "units": units,
                                "hero_red": hero_red, "hero_white": hero_white}
        self.engine = engine_cls(**self._engine_options)
        self.clock = clock
        self.turn_seconds = float(turn_seconds)
        self.human_turn_seconds = float(human_turn_seconds)
        self.dice = random.Random(int(self.engine.seed) * 2654435761 + 97)  # never exposed
        self.acted: Dict[str, str] = {}
        self.moved: set = set()  # moving does not use the turn (game_mode.md): move once, then throw or defend
        self.submission_receipts: Dict[Tuple[str, int, str], Dict[str, Any]] = {}
        self.notes_by_seat: Dict[str, str] = {seat_id: "" for seat_id in SEAT_IDS}
        self.phase = "human"
        self.deadline: Optional[float] = None
        self.winner: Optional[str] = None
        self.winner_reason: Optional[str] = None   # None, or "round_cap" when a team match ended on the round limit
        self.last_timeout: Optional[Dict[str, Any]] = None
        self.shield_paths: Dict[str, List[int]] = {"red": [], "white": []}
        # Skills and ultimate energy are side resources, matching the page. They
        # live in Session so GameState's generic public view cannot disclose wall points.
        self.skills_remaining: Dict[str, Dict[str, int]] = {
            "red": {"heal": 1, "double": 1, "heavy": 1},
            "white": {"heal": 1, "double": 1, "heavy": 1},
        }
        self.energy: Dict[str, int] = {"red": 0, "white": 0}
        self.ultimates_used: Dict[str, int] = {"red": 0, "white": 0}
        self.skipped_units: set = set()
        self.active_unit_index: Dict[str, int] = {"red": 0, "white": 0}
        self.ai_level: Optional[str] = None
        self.ai_reason: Optional[str] = None
        # None preserves the offline public-state shape used by existing stdio clients.
        self.sync: Optional[Dict[str, Any]] = None
        # The browser's playable default scene is graveyard. Connected devices use
        # this shared public scene until room setup carries a selected scene.
        self.weather_enabled = False
        self.scene_id = "graveyard"
        self.relay_team = "red"
        self.seats = self._build_seats()
        if seat not in self.seats:
            raise ValueError("unknown seat: %s" % seat)
        self.seat = self.seats[seat]
        self.store = MatchStore(memory_dir, self.engine.match_id, mode) if memory_dir else None
        self.handlers = {
            "get_public_state": self._tool_get_public_state,
            "get_roster": self._tool_get_roster,
            "get_history": self._tool_get_history,
            "submit_action": self._tool_submit_action,
            "end_turn": self._tool_end_turn,
            "set_notes": self._tool_set_notes,
            "get_notes": self._tool_get_notes,
        }
        self._begin_round()

    def _build_seats(self) -> Dict[str, Dict[str, Any]]:
        """List owned units for 1v1 through 3v3 matches without policy rewrites."""
        all_units = sorted(self.engine.units)
        return {
            "referee": {"seat_id": "referee", "team": None, "units": all_units, "kind": "referee"},
            "red": {"seat_id": "red", "team": "red",
                    "units": [uid for uid in all_units if self.engine.units[uid]["team"] == "red"],
                    "kind": "player"},
            "white": {"seat_id": "white", "team": "white",
                      "units": [uid for uid in all_units if self.engine.units[uid]["team"] == "white"],
                      "kind": "player"},
            "spectator": {"seat_id": "spectator", "team": None, "units": [], "kind": "spectator"},
        }

    @staticmethod
    def _owns_unit(seat: Dict[str, Any], unit_id: str) -> bool:
        return seat["kind"] == "referee" or unit_id in seat["units"]

    def _seat_controls_phase(self, seat: Dict[str, Any]) -> bool:
        if seat["kind"] == "referee":
            return True
        if seat["kind"] == "spectator":
            return False
        wanted = "human" if self.phase == "human" else "subagent"
        if self.engine.units_per_side > 1:
            team = self._active_team()
            if team is None or seat.get("team") != team:
                return False
            active = self._active_unit(team)
            return bool(active and active in seat["units"] and self.engine.units[active]["controller"] == wanted)
        return any(self.engine.units[uid]["alive"] and self.engine.units[uid]["controller"] == wanted
                   for uid in seat["units"])

    @staticmethod
    def _require_writer(seat: Dict[str, Any]) -> None:
        if seat["kind"] == "spectator":
            raise ToolError("spectator seat is read-only")

    def _active_team(self) -> Optional[str]:
        """Return the team whose one active unit may act in this phase."""
        if self.engine.mode != "human_vs_agent":
            return None
        return "red" if self.phase == "human" else "white" if self.phase == "agent" else None

    def _team_unit_ids(self, team: str) -> List[str]:
        controller = "human" if team == "red" else "subagent"
        return [uid for uid in sorted(self.engine.units)
                if self.engine.units[uid]["team"] == team and self.engine.units[uid]["controller"] == controller]

    def _active_unit(self, team: str) -> Optional[str]:
        """The unit due to act: the index points into the FULL id order of the team (dead units keep their place), and a dead unit is skipped forward, so a death never changes the order of the others."""
        ids = self._team_unit_ids(team)
        if not ids:
            return None
        start = self.active_unit_index[team] % len(ids)
        for step in range(len(ids)):
            uid = ids[(start + step) % len(ids)]
            if self.engine.units[uid]["alive"]:
                return uid
        return None

    def _advance_active_unit(self, team: Optional[str]) -> None:
        if team is None:
            return
        uid = self._active_unit(team)
        ids = self._team_unit_ids(team)
        if uid is not None and ids:
            self.active_unit_index[team] = (ids.index(uid) + 1) % len(ids)
        else:
            self.active_unit_index[team] += 1

    # ---- phase machine
    def _alive_units(self, controller: str) -> List[str]:
        return [uid for uid, u in self.engine.units.items() if u["alive"] and u["controller"] == controller]

    def _phase_teams(self, controller: str) -> List[str]:
        return sorted({unit["team"] for unit in self.engine.units.values()
                       if unit["alive"] and unit["controller"] == controller})

    def _begin_phase_statuses(self, controller: str) -> bool:
        reports = [self.engine.begin_team_turn(team) for team in self._phase_teams(controller)]
        for report in reports:
            self.skipped_units.update(report.get("skipped", []))
        return any(report["stunned"] for report in reports)

    def _finish_phase_statuses(self, controller: str) -> None:
        for team in self._phase_teams(controller):
            self.engine.finish_team_turn(team)

    def _begin_round(self) -> None:
        self.acted.clear()
        self.moved.clear()
        self.skipped_units.clear()
        self.submission_receipts.clear()
        self.deadline = None
        if self.winner is not None:
            self.phase = "over"
        elif self._alive_units("human"):
            self.phase = "human"
            stunned = self._begin_phase_statuses("human")
            if self.human_turn_seconds > 0:
                self.deadline = self.clock() + (min(self.human_turn_seconds, 7.0) if stunned else self.human_turn_seconds)
        else:
            self._enter_agent_phase()

    def _enter_agent_phase(self) -> None:
        if self._alive_units("subagent"):
            self.phase = "agent"
            stunned = self._begin_phase_statuses("subagent")
            self.deadline = self.clock() + (min(self.turn_seconds, 7.0) if stunned else self.turn_seconds)
        else:
            self._resolve_round()

    def _resolve_round(self, seat: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        log_before = len(self.engine.throw_log)
        self.engine.weather = self.weather() if self.weather_enabled else None
        result = self.engine.resolve_round()
        # One direct damaging throw earns one pip. Follow-up ultimate contacts never
        # recharge the ultimate that created them.
        for rec in result["results"]:
            if rec.get("hit_type") == "hero" and rec.get("damage_dealt", 0) > 0 and not rec.get("ultimate"):
                self.energy[rec["team"]] = min(3, self.energy[rec["team"]] + 1)
        self.winner = result["winner"]
        self.winner_reason = result.get("winner_reason")
        seat = seat or self.seat
        throws = self.view_for(seat, records=self.engine.throw_log[log_before:])
        for team, shield in self.engine.shields.items():
            if not shield["active"]:
                self.shield_paths[team] = []
        summary = {"round_resolved": result["round_resolved"], "throws": throws,
                   "new_wind": result["new_wind"], "winner": self.winner}
        if self.winner_reason is not None:
            summary["winner_reason"] = self.winner_reason
        if self.engine.units_per_side > 1:
            summary.update(self.comeback_view())
        self._persist()
        self._begin_round()
        return summary

    def comeback_view(self) -> Dict[str, Any]:
        """Team matches only: the pity charge and the underdog bonus of each team, for a UI badge.
        pity = {team: {"misses": throws since the last direct hit, "bonus": extra damage fraction of the next hit}}; underdog_bonus = {team: extra damage fraction now};
        comeback_multiplier = {team: the real factor of its next direct hit after the cap: min(max_total_multiplier, underdog x (1 + pity))}."""
        return {"pity": {team: {"misses": self.engine.pity[team], "bonus": comeback_py.pity_bonus(self.engine.pity[team])}
                         for team in ("red", "white")},
                "underdog_bonus": {team: self.engine.underdog_bonus(team) for team in ("red", "white")},
                "comeback_multiplier": {team: self.engine.hit_multiplier(team) for team in ("red", "white")}}

    def tick(self) -> None:
        """Advance expired human or agent phases when a tool call observes the deadline."""
        if self.deadline is None or self.clock() < self.deadline:
            return
        if self.phase == "human":
            active_team = self._active_team()
            active = self._active_unit(active_team) if active_team is not None else None
            idle = ([active] if active is not None and active not in self.acted else
                    ([] if active is not None else sorted(uid for uid in self._alive_units("human") if uid not in self.acted)))
            self.last_timeout = {"round": self.engine.round_num, "idle_units": idle}
            self._advance_active_unit(active_team)
            self._finish_phase_statuses("human")
            self._enter_agent_phase()
        elif self.phase == "agent":
            active_team = self._active_team()
            active = self._active_unit(active_team) if active_team is not None else None
            idle = ([active] if active is not None and active not in self.acted else
                    ([] if active is not None else sorted(uid for uid in self._alive_units("subagent") if uid not in self.acted)))
            self.last_timeout = {"round": self.engine.round_num, "idle_units": idle}
            self._advance_active_unit(active_team)
            self._finish_phase_statuses("subagent")
            self._resolve_round()

    # ---- relay synchronization
    def reset_for_relay(self, seed: int, scene_id: str = "graveyard", units: Optional[int] = None,
                        heroes: Optional[Dict[str, Any]] = None) -> None:
        """Adopt the relay seed, selected scene and (when the room names one) team size before connected play begins.
        `heroes` is the start message's hero lists in world frame ({"left": [...], "right": [...]}); a team match takes them
        when both sides name every slot with a known hero, so every device builds the same two teams (hybrid rooms, 2026-11-17)."""
        if units in (1, 2, 3) and units != self._engine_options["units"]:
            # the room decides the team size (the relay omits it for one versus one): a 3-unit default must not meet a page at N = 1
            self._engine_options["units"] = units
            for key in ("hero_red", "hero_white"):
                hero = self._engine_options[key]
                if (isinstance(hero, list) and len(hero) != units) or (isinstance(hero, str) and units != 1):
                    self._engine_options[key] = None
        if (self._engine_options["units"] > 1 and isinstance(heroes, dict)
                and all(isinstance(heroes.get(side), list) and len(heroes[side]) == self._engine_options["units"]
                        and all(isinstance(hero, str) and hero in engine.HERO_TEMPLATES for hero in heroes[side])
                        for side in ("left", "right"))):
            self._engine_options["hero_red"] = list(heroes["left"])
            self._engine_options["hero_white"] = list(heroes["right"])
        options = dict(self._engine_options)
        options["seed"] = seed
        self.engine = self._engine_cls(**options)
        self.scene_id = scene_id
        self.dice = random.Random(int(self.engine.seed) * 2654435761 + 97)
        self.acted.clear()
        self.moved.clear()
        self.submission_receipts.clear()
        self.shield_paths = {"red": [], "white": []}
        self.skills_remaining = {team: {"heal": 1, "double": 1, "heavy": 1} for team in ("red", "white")}
        self.energy = {"red": 0, "white": 0}
        self.ultimates_used = {"red": 0, "white": 0}
        self.skipped_units = set()
        self.active_unit_index = {"red": 0, "white": 0}
        self.winner = None
        self.winner_reason = None
        self.last_timeout = None
        self.relay_team = "red"
        self.seats = self._build_seats()
        updated_seat = self.seats[self.seat["seat_id"]]
        self.seat.clear()
        self.seat.update(updated_seat)
        self.seats[self.seat["seat_id"]] = self.seat
        self._begin_round()

    def weather(self) -> Dict[str, Any]:
        """Return the shared seed-and-round weather for the selected page scene."""
        scene = "bell_tower" if self.scene_id == "belltower" else self.scene_id
        return for_round(self.engine.seed, self.engine.round_num, scene)

    def public_weather(self) -> Dict[str, Any]:
        if not self.weather_enabled:
            return {"id": "clear", "label": "Clear", "round": self.engine.round_num,
                    "active": False}
        weather = self.weather()
        return {"id": weather["id"], "label": weather["label"],
                "round": self.engine.round_num, "active": True}

    def set_relay_phase(self, team: str) -> None:
        """Align local controller phases with the relay's alternating team turn."""
        if team not in ("red", "white"):
            return
        self.relay_team = team
        self.phase = "human" if team == "red" else "agent"
        controller = "human" if self.phase == "human" else "subagent"
        seconds = self.human_turn_seconds if self.phase == "human" else self.turn_seconds
        stunned = self._begin_phase_statuses(controller)
        self.deadline = self.clock() + (min(seconds, 7.0) if stunned else seconds) if seconds > 0 else None

    # ---- persistence
    def _hit_rate_by_round(self) -> Dict[str, float]:
        totals: Dict[int, List[int]] = {}
        for rec in self.engine.throw_log:
            if rec["controller"] != "subagent":
                continue
            counts = totals.setdefault(rec["round"], [0, 0])
            counts[1] += 1
            counts[0] += 1 if rec["hit_type"] == "hero" else 0
        return {str(r): round(h / n, 3) for r, (h, n) in sorted(totals.items())}

    def _persist(self) -> None:
        if self.store is None:
            return
        self.store.write_history([public_throw(r) for r in self.engine.throw_log])
        if self.winner is not None:
            self.store.finish(self.winner, self.engine.round_num - 1, self._hit_rate_by_round())

    # ---- views
    def remembered_paths(self, team: str) -> List[int]:
        """Throw ids of the last 4 enemy throws that `team` remembers for its floating shield."""
        ids = [r["throw_id"] for r in self.engine.throw_log if r["team"] != team]
        return ids[-REMEMBERED_PATHS:]

    def public_state(self) -> Dict[str, Any]:
        """Return the legacy referee view without applying a seat filter."""
        base = self.engine.get_public_state()
        units = {}
        for uid, unit in base["units"].items():
            entry = dict(unit)
            entry["class"] = unit["hero"]
            entry["acted"] = uid in self.acted
            entry["moved"] = uid in self.moved
            units[uid] = entry
        shields = {}
        for team, shield in base["shields"].items():
            entry = dict(shield)
            entry["path_ids"] = list(self.shield_paths[team])
            shields[team] = entry
        seconds_left = None
        if self.phase == "agent" and self.deadline is not None:
            seconds_left = round(max(0.0, self.deadline - self.clock()), 1)
        state = {
            "match_id": base["match_id"],
            "mode": base["mode"],
            "round": base["round"],
            "phase": self.phase,
            "turn_seconds": self.turn_seconds,
            "turn_seconds_left": seconds_left,
            "wind": base["wind"],
            "weather": self.public_weather(),
            "winner": self.winner,
            "central_wall": base["central_wall"],
            "shields": shields,
            "units": units,
            "ultimates_remaining": {team: MAX_ULTIMATES_PER_MATCH - self.ultimates_used[team]
                                    for team in ("red", "white")},
            "ultimate_energy": dict(self.energy),
            "skills_remaining": {team: dict(counts) for team, counts in self.skills_remaining.items()},
            "knight_walls": {team: {"points_left": len(self.engine.knight_walls[team])}
                             for team in ("red", "white")},
            "remembered_enemy_paths": {t: self.remembered_paths(t) for t in ("red", "white")},
            "last_timeout": self.last_timeout,
        }
        if self.winner_reason is not None:
            state["winner_reason"] = self.winner_reason
        if self.engine.units_per_side > 1:
            state.update(self.comeback_view())
        if self.ai_level is not None:
            state.update({"engine": "py-practice", "ai_level": self.ai_level,
                          "ai_reason": self.ai_reason})
        if self.sync is not None:
            state["sync"] = dict(self.sync)
        state["round_hash"] = round_hash({"units": units, "wallHp": base["central_wall"]["hp"],
                                           "round": base["round"], "phase": self.phase, "seed": 0})
        return state

    def view_for(self, seat: Dict[str, Any], state: Optional[Dict[str, Any]] = None,
                 records: Optional[List[Dict[str, Any]]] = None,
                 include_path: bool = True) -> Any:
        """Apply the one per-seat disclosure policy to state or throw records."""
        if records is not None:
            if seat["kind"] == "referee":
                return [public_throw(record, include_path) for record in records]
            return [public_throw(record, include_path,
                                 reveal_aim=self._owns_unit(seat, record["unit"]),
                                 coarse=not self._owns_unit(seat, record["unit"]))
                    for record in records]
        state = self.public_state() if state is None else state
        if seat["kind"] == "referee":
            return state
        owned_units = set(seat["units"])
        units = {}
        for uid, unit in state["units"].items():
            entry = dict(unit)
            if uid not in owned_units:
                entry.pop("acted", None)
                entry.pop("moved", None)
            units[uid] = entry
        shields = {}
        for team, shield in state["shields"].items():
            shields[team] = dict(shield) if team == seat["team"] else {}
        remembered = ({seat["team"]: list(state["remembered_enemy_paths"][seat["team"]])}
                      if seat["team"] is not None else {})
        filtered = dict(state)
        filtered["units"] = units
        filtered["shields"] = shields
        filtered["remembered_enemy_paths"] = remembered
        walls = {team: dict(wall) for team, wall in state["knight_walls"].items()}
        if seat["team"] is not None:
            walls[seat["team"]]["points"] = [dict(point) for point in self.engine.knight_walls[seat["team"]]]
        filtered["knight_walls"] = walls
        filtered["recent_throws"] = self.view_for(seat, records=self.engine.throw_log[-8:])
        filtered["last_timeout"] = None
        return filtered

    # ---- tools
    def call(self, name: str, args: Dict[str, Any],
             seat: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        handler = self.handlers.get(name)
        if handler is None:
            raise ToolError("unknown tool: %s" % name)
        self.tick()
        return handler(args, seat or self.seat)

    def _tool_get_public_state(self, args: Dict[str, Any], seat: Dict[str, Any]) -> Dict[str, Any]:
        _reject_unknown(args, (), "get_public_state")
        return self.view_for(seat)

    def _tool_get_roster(self, args: Dict[str, Any], seat: Dict[str, Any]) -> Dict[str, Any]:
        """Expose unit count and ids without adding any write capability."""
        _reject_unknown(args, (), "get_roster")
        return {"units_per_side": self.engine.units_per_side,
                "teams": {team: [uid for uid in sorted(self.engine.units)
                                   if self.engine.units[uid]["team"] == team]
                          for team in ("red", "white")},
                "seat": {key: list(value) if key == "units" else value
                         for key, value in seat.items()}}

    def _tool_get_history(self, args: Dict[str, Any], seat: Dict[str, Any]) -> Dict[str, Any]:
        _reject_unknown(args, ("limit", "team", "unit", "include_path"), "get_history")
        limit = _integer(args.get("limit", 10), "limit", 1, HISTORY_MAX)
        team = _enum(args["team"], "team", ("red", "white")) if "team" in args else None
        unit = _string(args["unit"], "unit") if "unit" in args else None
        include_path = args.get("include_path", True)
        if not isinstance(include_path, bool):
            raise ToolError("include_path must be a boolean")
        rows = [r for r in self.engine.throw_log
                if (team is None or r["team"] == team) and (unit is None or r["unit"] == unit)]
        return {"round": self.engine.round_num,
                "throws": self.view_for(seat, records=rows[-limit:], include_path=include_path)}

    @staticmethod
    def _receipt_key(seat: Dict[str, Any], round_num: int, unit_id: str,
                     action: Dict[str, Any]) -> Tuple[str, int, str]:
        """Key a successful action receipt so an exact retry is side-effect free."""
        command = json.dumps({"unit": unit_id, "action": action}, ensure_ascii=False,
                             sort_keys=True, separators=(",", ":"))
        return seat["seat_id"], round_num, command

    def _tool_submit_action(self, args: Dict[str, Any], seat: Dict[str, Any]) -> Dict[str, Any]:
        self._require_writer(seat)
        _reject_unknown(args, ("unit", "action", "round"), "submit_action")
        unit_id = _string(args.get("unit"), "unit")
        action = args.get("action")
        if not isinstance(action, dict):
            raise ToolError("action must be an object with a type")
        if "round" in args:
            expected = _integer(args["round"], "round", 1, 10 ** 6)
            if expected != self.engine.round_num:
                raise ToolError("stale round: current round is %d" % self.engine.round_num)
        if self.phase == "over":
            raise ToolError("the match is over")
        unit = self.engine.units.get(unit_id)
        if unit is None:
            raise ToolError("unknown unit: %s" % unit_id)
        if not self._owns_unit(seat, unit_id):
            raise ToolError("seat %s does not control unit %s" % (seat["seat_id"], unit_id))
        receipt_key = self._receipt_key(seat, self.engine.round_num, unit_id, action)
        receipt = self.submission_receipts.get(receipt_key)
        if receipt is not None:
            return dict(receipt, duplicate=True)
        if not self._seat_controls_phase(seat):
            raise ToolError("seat %s does not control the %s phase" % (seat["seat_id"], self.phase))
        if not unit["alive"]:
            raise ToolError("unit %s is dead" % unit_id)
        if unit_id in self.skipped_units:
            raise ToolError("unit %s skips this turn" % unit_id)
        wanted = "human" if self.phase == "human" else "subagent"
        if unit["controller"] != wanted:
            raise ToolError("it is the %s phase; %s is controlled by %s"
                            % (self.phase, unit_id, unit["controller"]))
        active_team = self._active_team()
        active_unit = self._active_unit(active_team) if active_team is not None else None
        if active_unit is not None and unit_id != active_unit:
            raise ToolError("unit %s is frozen; active unit is %s" % (unit_id, active_unit))
        atype = _enum(action.get("type"), "action.type", ("throw", "move", "defend", "skill", "ultimate"))
        if atype == "move":
            if unit.get("statuses", {}).get("slow", 0):
                raise ToolError("unit %s is slowed and cannot move this turn" % unit_id)
            if unit_id in self.moved:
                raise ToolError("unit %s already moved this turn" % unit_id)
            if unit_id in self.acted:
                raise ToolError("unit %s already %s this turn; moving must come before the attack"
                                % (unit_id, self.acted[unit_id]))
            result = self._do_move(unit_id, unit, action)
            self.moved.add(unit_id)
        elif atype == "skill":
            result = self._do_skill(unit_id, unit, action)
            if action.get("skill") != "heal":
                self.acted[unit_id] = "skill"
        elif atype == "ultimate":
            result = self._do_ultimate(unit_id, unit, action)
            if unit["hero"] != "knight":
                self.acted[unit_id] = "ultimate"
        else:
            if unit_id in self.acted:
                previous = self.acted[unit_id]
                if previous == "defend" and atype == "throw":
                    raise ToolError("unit %s is defending this turn and cannot throw" % unit_id)
                raise ToolError("unit %s already submitted %s this turn" % (unit_id, previous))
            if atype == "throw":
                result = self._do_throw(unit_id, action)
            else:
                result = self._do_defend(unit_id, unit, action)
            self.acted[unit_id] = atype
        self.submission_receipts[receipt_key] = dict(result)
        return result

    def _do_throw(self, unit_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        _reject_unknown(action, ("type", "angle", "power"), "action")
        angle = _number(action.get("angle"), "angle", ANGLE_MIN, ANGLE_MAX)
        power = _number(action.get("power"), "power", POWER_MIN, POWER_MAX)
        res = self.engine.submit_throw(unit_id, angle, power)
        if not res.get("success"):
            raise ToolError(str(res.get("error", "throw rejected")))
        return {"ok": True, "unit": unit_id, "action": "throw", "angle": angle, "power": power}

    def _skill_throw(self, unit_id: str, unit: Dict[str, Any], action: Dict[str, Any], skill: str) -> Dict[str, Any]:
        if unit_id in self.acted:
            raise ToolError("unit %s already submitted %s this turn" % (unit_id, self.acted[unit_id]))
        angle = _number(action.get("angle"), "angle", ANGLE_MIN, ANGLE_MAX)
        power = _number(action.get("power"), "power", POWER_MIN, POWER_MAX)
        team = unit["team"]
        if self.skills_remaining[team][skill] <= 0:
            raise ToolError("team %s has already used its %s skill" % (team, skill))
        self.skills_remaining[team][skill] -= 1
        second = None
        scale = 1.0
        if skill == "double":
            second = {"angle": angle, "power": min(POWER_MAX, power * 1.04), "special": None,
                      "damage_scale": 1.0, "delay_seconds": 0.26}
        elif skill == "heavy":
            scale = 1.5
        res = self.engine.submit_throw(unit_id, angle, power, damage_scale=scale, second_throw=second)
        if not res.get("success"):
            raise ToolError(str(res.get("error", "skill throw rejected")))
        return {"ok": True, "unit": unit_id, "action": "skill", "skill": skill,
                "angle": angle, "power": power, "remaining": self.skills_remaining[team][skill]}

    def _do_skill(self, unit_id: str, unit: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
        skill = _enum(action.get("skill"), "skill", ("heal", "double", "heavy"))
        allowed = ("type", "skill") if skill == "heal" else ("type", "skill", "angle", "power")
        _reject_unknown(action, allowed, "action")
        team = unit["team"]
        if self.skills_remaining[team][skill] <= 0:
            raise ToolError("team %s has already used its %s skill" % (team, skill))
        if skill == "heal":
            self.skills_remaining[team][skill] -= 1
            before = unit["hp"]
            unit["hp"] = min(unit["max_hp"], unit["hp"] + 52.0)
            return {"ok": True, "unit": unit_id, "action": "skill", "skill": "heal",
                    "healed": round(unit["hp"] - before, 1), "hp": unit["hp"],
                    "remaining": 0}
        return self._skill_throw(unit_id, unit, action, skill)

    def _do_ultimate(self, unit_id: str, unit: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
        team = unit["team"]
        if self.energy[team] < 3:
            raise ToolError("ultimate_not_ready: %s needs three energy pips" % team)
        if self.ultimates_used[team] >= MAX_ULTIMATES_PER_MATCH:
            raise ToolError("no_ultimates_left: %s has used both ultimates" % team)
        if unit["hero"] == "knight":
            _reject_unknown(action, ("type", "points"), "action")
            raw_points = action.get("points")
            if not isinstance(raw_points, list) or len(raw_points) != 3:
                raise ToolError("knight ultimate requires exactly three stored points")
            points = []
            for point in raw_points:
                if not isinstance(point, dict):
                    raise ToolError("knight point must be an object with x and y")
                points.append({"x": _number(point.get("x"), "point.x", 0, 1920),
                               "y": _number(point.get("y"), "point.y", 0, GROUND_Y)})
            self.engine.set_knight_wall(team, points)
            self.energy[team] = 0
            self.ultimates_used[team] += 1
            return {"ok": True, "unit": unit_id, "action": "ultimate", "ultimate": "knight",
                    "points_stored": 3, "turn_cost": False}
        _reject_unknown(action, ("type", "angle", "power"), "action")
        if unit_id in self.acted:
            raise ToolError("unit %s already submitted %s this turn" % (unit_id, self.acted[unit_id]))
        angle = _number(action.get("angle"), "angle", ANGLE_MIN, ANGLE_MAX)
        power = _number(action.get("power"), "power", POWER_MIN, POWER_MAX)
        self.energy[team] = 0
        self.ultimates_used[team] += 1
        res = self.engine.submit_throw(unit_id, angle, power, special=unit["hero"])
        if not res.get("success"):
            raise ToolError(str(res.get("error", "ultimate rejected")))
        return {"ok": True, "unit": unit_id, "action": "ultimate", "ultimate": unit["hero"],
                "angle": angle, "power": power,
                "remaining": MAX_ULTIMATES_PER_MATCH - self.ultimates_used[team]}

    def _do_move(self, unit_id: str, unit: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
        _reject_unknown(action, ("type", "direction"), "action")
        direction = _enum(action.get("direction"), "direction", ("forward", "backward"))
        die = self.dice.randint(1, 6)  # engine-chosen, never the agent's choice
        sign = unit["facing"] if direction == "forward" else -unit["facing"]
        lo, hi = TEAM_X_LIMITS[unit["team"]]
        x_before = float(unit["x"])
        raw_pixels = die * MOVE_PX_PER_PIP
        pixels = apply_move(self.weather(), raw_pixels) if self.weather_enabled else raw_pixels
        target = x_before + sign * pixels
        edge_x = round(max(lo, min(hi, target)), 1)
        # Team matches: never stop within 120 px of a living teammate (the page's step-back rule); one unit per team has none.
        unit["x"] = self.engine.step_back_move(unit, x_before, edge_x)
        result = {"ok": True, "unit": unit_id, "action": "move", "direction": direction, "die": die,
                  "pixels": pixels, "x_before": x_before, "x_after": unit["x"],
                  "blocked_by_edge": edge_x != round(target, 1)}
        if unit["x"] != edge_x:
            result["blocked_by_teammate"] = True
        return result

    def _shield_anchor(self, team: str, throw_id: int) -> Tuple[float, float]:
        rec = next((r for r in self.engine.throw_log if r["throw_id"] == throw_id), None)
        if rec is None:
            raise ToolError("unknown path id: %d" % throw_id)
        x_lo, x_hi = SHIELD_AIRSPACE_X[team]
        y_lo, y_hi = SHIELD_AIRSPACE_Y
        inside = [p for p in rec["path"] if x_lo <= p[0] <= x_hi and y_lo <= p[1] <= y_hi]
        if not inside:
            raise ToolError("path %d never crosses the shield airspace of team %s" % (throw_id, team))
        mid = inside[len(inside) // 2]
        return float(mid[0]), float(mid[1])

    def _do_defend(self, unit_id: str, unit: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
        _reject_unknown(action, ("type", "path1", "path2"), "action")
        if unit["hero"] != "knight":
            raise ToolError("only the Pumpkin Guard (knight) can defend")
        path1 = _integer(action.get("path1"), "path1", 1, 10 ** 9)
        path2 = _integer(action.get("path2"), "path2", 1, 10 ** 9)
        if path1 == path2:
            raise ToolError("path1 and path2 must be different remembered paths")
        team = unit["team"]
        remembered = self.remembered_paths(team)
        for pid in (path1, path2):
            if pid not in remembered:
                raise ToolError("path %d is not one of the remembered enemy paths %s" % (pid, remembered))
        x1, y1 = self._shield_anchor(team, path1)
        self._shield_anchor(team, path2)  # validates that it also crosses the airspace
        res = self.engine.submit_defend(unit_id, x1, y1)
        if not res.get("success"):
            raise ToolError(str(res.get("error", "defend rejected")))
        self.shield_paths[team] = [path1, path2]
        return {"ok": True, "unit": unit_id, "action": "defend", "path1": path1, "path2": path2,
                "shield_x": res["shield_x"], "shield_y": res["shield_y"],
                "duration_rounds": res["duration_rounds"], "remaining_charges": res["remaining_charges"],
                "note": "the engine has one shield box; it is placed on path1, path2 is recorded"}

    def _tool_end_turn(self, args: Dict[str, Any], seat: Dict[str, Any]) -> Dict[str, Any]:
        self._require_writer(seat)
        _reject_unknown(args, ("phase", "round"), "end_turn")
        if seat["kind"] != "referee":
            missing = [name for name in ("round", "phase") if name not in args]
            if missing:
                raise ToolError("end_turn requires %s for seat %s" % (" and ".join(missing),
                                                                          seat["seat_id"]))
        if "round" in args:
            expected = _integer(args["round"], "round", 1, 10 ** 6)
            if expected != self.engine.round_num:
                raise ToolError("stale round: current round is %d" % self.engine.round_num)
        if self.phase == "over":
            raise ToolError("the match is over")
        if not self._seat_controls_phase(seat):
            raise ToolError("seat %s does not control the %s phase" % (seat["seat_id"], self.phase))
        if "phase" in args:
            _enum(args["phase"], "phase", ("human", "agent"))
            if args["phase"] != self.phase:
                raise ToolError("current phase is %s, not %s" % (self.phase, args["phase"]))
        ended = self.phase
        if self.weather_enabled:
            if seat["kind"] != "referee" and seat["team"] != self.relay_team:
                raise ToolError("seat %s does not control relay team %s" %
                                (seat["seat_id"], self.relay_team))
            self._advance_active_unit(self.relay_team)
            self._finish_phase_statuses("human" if ended == "human" else "subagent")
            first_team = engine.first_team_of_round(self.engine.round_num)
            if self.relay_team == first_team:
                self.set_relay_phase("white" if first_team == "red" else "red")
                return {"ended": ended, "phase": self.phase, "round": self.engine.round_num}
            summary = self._resolve_round(seat)
            summary.update({"ended": ended, "phase": self.phase, "round": self.engine.round_num})
            return summary
        if ended == "human":
            self._advance_active_unit(self._active_team())
            self._finish_phase_statuses("human")
            self._enter_agent_phase()
            return {"ended": "human", "phase": self.phase, "round": self.engine.round_num}
        self._advance_active_unit(self._active_team())
        self._finish_phase_statuses("subagent")
        summary = self._resolve_round(seat)
        summary.update({"ended": "agent", "phase": self.phase, "round": self.engine.round_num})
        return summary

    def _tool_set_notes(self, args: Dict[str, Any], seat: Dict[str, Any]) -> Dict[str, Any]:
        self._require_writer(seat)
        _reject_unknown(args, ("text", "mode"), "set_notes")
        text = args.get("text")
        if not isinstance(text, str):
            raise ToolError("text must be a string")
        mode = _enum(args.get("mode", "replace"), "mode", ("replace", "append"))
        current = self.notes_by_seat[seat["seat_id"]]
        new_notes = text if mode == "replace" else (current + "\n" + text if current else text)
        if len(new_notes) > MAX_NOTES_CHARS:
            raise ToolError("notes would exceed %d characters" % MAX_NOTES_CHARS)
        self.notes_by_seat[seat["seat_id"]] = new_notes
        if self.store is not None:
            self.store.write_json("notes.json", {"notes_by_seat": self.notes_by_seat})
        return {"ok": True, "chars": len(new_notes)}

    def _tool_get_notes(self, args: Dict[str, Any], seat: Dict[str, Any]) -> Dict[str, Any]:
        _reject_unknown(args, (), "get_notes")
        notes = self.notes_by_seat[seat["seat_id"]]
        return {"notes": notes, "chars": len(notes)}


# ------------------------------------------------------------------ tool schemas
_NO_ARGS = {"type": "object", "properties": {}, "additionalProperties": False}

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "get_public_state",
        "description": "Public match state: unit positions, hp, shield state, wind, round, phase "
                       "(human | agent | over), seconds left, remaining ultimates, remembered enemy "
                       "path ids. No hidden values.",
        "inputSchema": _NO_ARGS,
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "get_roster",
        "description": "Read the selected units per side, all unit ids, and this seat's owned unit ids. No hidden values.",
        "inputSchema": _NO_ARGS,
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "get_history",
        "description": "Last N throws (oldest first): round, team, unit, wind_at_throw, landing_x, "
                       "landing_y, hit_type, throw_id and the sampled flight path [[x, y], ...]. "
                       "Angle and power are shown only for agent throws. Learn from this.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": HISTORY_MAX, "default": 10},
                "team": {"type": "string", "enum": ["red", "white"]},
                "unit": {"type": "string", "description": "Only throws by this unit id, e.g. white_1"},
                "include_path": {"type": "boolean", "default": True},
            },
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "submit_action",
        "description": "Per unit per turn: one optional move, then one attack. Attack = throw {angle 25-80, power 0-115}, "
                       "ultimate {angle, power} when the side has three direct-hit pips (knight: {points:[three x/y points]}, no turn cost), "
                       "or defend {path1, path2} (knight only; two different throw_ids from "
                       "remembered_enemy_paths). Skill {skill: heal|double|heavy}: each side has one of each; heal restores "
                       "52 hp for free, double resolves a second 1.04x-power throw (capped at power 115) after 0.26 s, heavy deals 1.5x damage. "
                       "Move {direction forward|backward; the engine rolls a die 1-6, %d px per pip} does not use the turn "
                       "but only once and only before the attack. A second attack for the same unit is rejected; a "
                       "defending unit cannot throw." % MOVE_PX_PER_PIP,
        "inputSchema": {
            "type": "object",
            "properties": {
                "unit": {"type": "string", "description": "Unit id, e.g. white_1"},
                "action": {
                    "type": "object",
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["throw"]},
                                "angle": {"type": "number", "minimum": ANGLE_MIN, "maximum": ANGLE_MAX},
                                "power": {"type": "number", "minimum": POWER_MIN, "maximum": POWER_MAX},
                            },
                            "required": ["type", "angle", "power"],
                            "additionalProperties": False,
                        },
                        {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["move"]},
                                "direction": {"type": "string", "enum": ["forward", "backward"]},
                            },
                            "required": ["type", "direction"],
                            "additionalProperties": False,
                        },
                        {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["defend"]},
                                "path1": {"type": "integer", "minimum": 1},
                                "path2": {"type": "integer", "minimum": 1},
                            },
                            "required": ["type", "path1", "path2"],
                            "additionalProperties": False,
                        },
                        {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["skill"]},
                                "skill": {"type": "string", "enum": ["heal", "double", "heavy"]},
                                "angle": {"type": "number", "minimum": ANGLE_MIN, "maximum": ANGLE_MAX},
                                "power": {"type": "number", "minimum": POWER_MIN, "maximum": POWER_MAX},
                            },
                            "required": ["type", "skill"],
                            "additionalProperties": False,
                        },
                        {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["ultimate"]},
                                "angle": {"type": "number", "minimum": ANGLE_MIN, "maximum": ANGLE_MAX},
                                "power": {"type": "number", "minimum": POWER_MIN, "maximum": POWER_MAX},
                                "points": {"type": "array", "description": "Knight only: three private {x,y} Shield Wall points"},
                            },
                            "required": ["type"],
                            "additionalProperties": False,
                        },
                    ],
                },
                "round": {"type": "integer", "minimum": 1,
                          "description": "Optional guard: reject if the current round differs"},
            },
            "required": ["unit", "action"],
            "additionalProperties": False,
        },
    },
    {
        "name": "end_turn",
        "description": "End the current phase. Ending the human phase starts the agent phase "
                       "(separate human and agent timers); ending the agent phase resolves the round. "
                       "Non-referee seats must pass both the current round and phase so a retry "
                       "cannot end a later phase.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "phase": {"type": "string", "enum": ["human", "agent"]},
                "round": {"type": "integer", "minimum": 1},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "set_notes",
        "description": "Write the agent's per-match scratchpad (lessons in plain words, shown in the "
                       "UI). Max %d characters." % MAX_NOTES_CHARS,
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "maxLength": MAX_NOTES_CHARS},
                "mode": {"type": "string", "enum": ["replace", "append"], "default": "replace"},
            },
            "required": ["text"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_notes",
        "description": "Read the per-match scratchpad.",
        "inputSchema": _NO_ARGS,
        "annotations": {"readOnlyHint": True},
    },
]
TOOL_NAMES = [t["name"] for t in TOOLS]

_ROOM_CODE_RE = re.compile(r"^[A-Z0-9]{6}$")
WAIT_FOR_TURN_MAX_SECONDS = 25.0


def normalize_relay_url(raw: str) -> str:
    """Normalize a relay URL to ws(s)://... ending with /ws (or explicit path)."""
    text = str(raw or "").strip()
    if not text:
        raise ToolError("relay URL is empty")
    parsed = urlparse(text)
    if parsed.scheme not in ("ws", "wss") or not parsed.netloc:
        raise ToolError("relay URL must use ws:// or wss:// with a host")
    path = parsed.path or "/ws"
    if path == "/":
        path = "/ws"
    return "%s://%s%s" % (parsed.scheme, parsed.netloc, path)


_INVITE_RE = re.compile(r"^(red|white)\.[A-Za-z0-9_-]{4,64}$")


def parse_invite(raw: str) -> Dict[str, Any]:
    """Parse a 6-char room code or a full invite URL (?room=CODE&seat=...&team=...&relay=...)."""
    text = _string(raw, "room", max_len=1000).strip()
    if not text:
        raise ToolError("room code or invite URL is required")
    if _ROOM_CODE_RE.match(text.upper()):
        return {"code": text.upper(), "seat": None, "units": None, "relay": None, "invite": None}
    parsed = urlparse(text)
    if parsed.scheme not in ("http", "https", "ws", "wss") or not parsed.netloc:
        raise ToolError("room must be a 6-character code or an invite URL with ?room=CODE")
    qs = parse_qs(parsed.query)
    code_raw = (qs.get("room") or [""])[0].strip().upper()
    if not _ROOM_CODE_RE.match(code_raw):
        raise ToolError("invite URL is missing a valid 6-character ?room= code")
    seat_raw = (qs.get("seat") or [""])[0].strip().lower()
    seat = seat_raw if seat_raw in ("red", "white") else None
    units: Optional[int] = None
    team_raw = (qs.get("team") or [""])[0].strip()
    if team_raw.isdigit() and int(team_raw) in (1, 2, 3):
        units = int(team_raw)
    relay_raw = (qs.get("relay") or [""])[0].strip()
    relay_url: Optional[str] = None
    if relay_raw:
        relay_url = normalize_relay_url(relay_raw)
    invite = (qs.get("invite") or [""])[0].strip() or None
    return {"code": code_raw, "seat": seat, "units": units, "relay": relay_url, "invite": invite}


ROOM_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "join_room",
        "description": "Join a live Pumpkin Killer room by 6-character room code or invite URL "
                       "(e.g. https://<host>/index.html?room=ABC234&team=3). Automatically readies "
                       "your seat and waits briefly for room confirmation. Call leave_room before joining another room.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "room": {"type": "string", "description": "6-character room code (e.g. ABC234) or full invite URL"},
                "seat": {"type": "string", "enum": ["red", "white"],
                         "description": "Team side to join (defaults to invite URL ?seat= or 'white')"},
                "units": {"type": "integer", "minimum": 1, "maximum": 3,
                          "description": "Units per side (defaults to invite URL ?team= or 3)"},
                "claim": {"type": "integer", "minimum": 1, "maximum": 3,
                          "description": "How many units on your team this seat claims (1 to units; defaults to units = whole team)"},
                "heroes": {
                    "type": "array",
                    "items": {"type": "string", "enum": sorted(engine.HERO_TEMPLATES)},
                    "minItems": 1,
                    "maxItems": 3,
                    "description": "Optional hero ids for your team",
                },
                "relay": {"type": "string",
                          "description": "Optional ws:// or wss:// relay URL (stdio mode only; hosted HTTP MCP always uses its local relay)"},
                "invite": {"type": "string", "description": "Invitation from a player in the room (also read from the invite URL ?invite=). "
                                                            "It decides your team and gives you one unit; pass at most one hero."},
                "name": {"type": "string", "description": "Name shown above your characters (up to 10 half-width or 5 full-width characters)"},
            },
            "required": ["room"],
            "additionalProperties": False,
        },
    },
    {
        "name": "lock_hero",
        "description": "Choose the hero of your unit and lock it, before the match starts. Use it after joining with an invite and no hero.",
        "inputSchema": {
            "type": "object",
            "properties": {"hero": {"type": "string", "enum": sorted(engine.HERO_TEMPLATES)}},
            "required": ["hero"],
            "additionalProperties": False,
        },
    },
    {
        "name": "leave_room",
        "description": "Leave the current live room cleanly so this MCP session can join another room.",
        "inputSchema": _NO_ARGS,
    },
    {
        "name": "wait_for_turn",
        "description": "Wait (short long-poll, up to 25 s) until it is your seat's turn to act, the match ends, "
                       "or a relay error occurs. Returns immediately if already your turn; call again when status is 'waiting'.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "timeout_seconds": {"type": "number", "minimum": 0.1, "maximum": WAIT_FOR_TURN_MAX_SECONDS, "default": 15.0},
            },
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True},
    },
]
ROOM_TOOL_NAMES = [t["name"] for t in ROOM_TOOLS]


class TranscriptWriter:
    """Append public, redacted tool exchanges to an optional JSONL file."""

    _PRIVATE_KEYS = frozenset(("seed", "rng", "dice", "pending_throw", "pending_action",
                               "angle", "power", "token", "notes", "match_id"))

    def __init__(self, path: str) -> None:
        self._handle = open(path, "w", encoding="utf-8")

    @classmethod
    def _public(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: cls._public(item) for key, item in value.items()
                    if key not in cls._PRIVATE_KEYS}
        if isinstance(value, list):
            return [cls._public(item) for item in value]
        return value

    def record(self, tool: str, arguments: Dict[str, Any], result: Dict[str, Any]) -> None:
        text = result["content"][0]["text"]
        try:
            payload = json.loads(text)
        except (TypeError, ValueError):
            payload = {"error": "invalid tool response"}
        row = {"tool": tool, "arguments": self._public(arguments),
               "result": self._public(payload), "is_error": bool(result["isError"])}
        self._handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()


class InProcessToolClient:
    """A six-tool JSON-RPC client used by the practice seat and headless runner."""

    def __init__(self, server: Any) -> None:
        self.server = server
        self.next_id = 1
        self.calls: List[str] = []

    def call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name not in TOOL_NAMES:
            raise AssertionError("built-in practice seat attempted non-public tool: %s" % name)
        self.calls.append(name)
        response = self.server.handle_message({"jsonrpc": "2.0", "id": self.next_id,
                                               "method": "tools/call",
                                               "params": {"name": name, "arguments": arguments}})
        self.next_id += 1
        assert response is not None
        result = response["result"]
        payload = json.loads(result["content"][0]["text"])
        if result["isError"]:
            raise RuntimeError("%s failed: %s" % (name, payload))
        return payload


class BuiltinPracticeSeat:
    """A deterministic history learner that can act only through its seat's six tools."""

    LEVELS = ("easy", "normal", "hard", "adaptive")
    _LEVEL_BY_NUMBER = {1: "easy", 2: "normal", 3: "hard"}

    def __init__(self, session: Session, seat: Dict[str, Any], level: str,
                 transcript: Optional[TranscriptWriter] = None) -> None:
        if level not in self.LEVELS:
            raise ValueError("unknown built-in level: %s" % level)
        self.seat = seat
        self.level = level
        # agent_levels imports this server, so load it only after module initialization.
        import agent_levels as levels
        self._level_config = levels.level_config
        self.random = random.Random(0)
        self.client = InProcessToolClient(McpServer(session, seat=seat, transcript=transcript))
        self.adaptive = adaptive_level.AdaptiveLevel() if level == "adaptive" else None
        self.seen_enemy_throws: set = set()
        self.last_view: Optional[Dict[str, Any]] = None
        self._publish_status(session)

    def _active_level(self) -> str:
        if self.adaptive is None:
            return self.level
        return self._LEVEL_BY_NUMBER[self.adaptive.public_state()["level"]]

    def _publish_status(self, session: Session) -> None:
        active = self._active_level()
        if self.adaptive is None:
            session.ai_level = active
            session.ai_reason = "built-in practice level: %s" % active
        else:
            change = self.adaptive.public_state()["last_change"]
            session.ai_level = active
            session.ai_reason = change or "adaptive level starts at normal"

    def _observe_adaptive(self, session: Session) -> None:
        if self.adaptive is None:
            return
        history = self.client.call("get_history", {"limit": HISTORY_MAX, "include_path": False})
        for record in history["throws"]:
            throw_id = record["throw_id"]
            if record["unit"] in self.seat["units"] or throw_id in self.seen_enemy_throws:
                continue
            self.seen_enemy_throws.add(throw_id)
            self.adaptive.record_hit(record["hit_type"] == "hero")
        self._publish_status(session)

    def _action(self, state: Dict[str, Any], unit_id: str) -> Dict[str, Any]:
        config = self._level_config(self._active_level())
        unit = state["units"][unit_id]
        targets = [(target_id, target) for target_id, target in state["units"].items()
                   if target["alive"] and target["team"] != unit["team"]]
        target_id, target = min(targets, key=lambda pair: abs(pair[1]["x"] - unit["x"]))
        del target_id
        target_x = float(target["x"]) + self.random.uniform(-config["perception_target_px"],
                                                               config["perception_target_px"])
        history = self.client.call("get_history", {"limit": config["memory"], "unit": unit_id,
                                                    "include_path": False})["throws"]
        if history:
            previous = history[-1]
            direction = 1.0 if target_x > float(unit["x"]) else -1.0
            power = float(previous["power"]) + direction * (target_x - float(previous["landing_x"])) / 20.0
        else:
            power = 70.0
        power += self.random.uniform(-config["aim_power_error"], config["aim_power_error"])
        return {"type": "throw", "angle": 62.0, "power": round(max(20.0, min(POWER_MAX, power)), 1)}

    def drive(self, session: Session) -> None:
        """Take one available phase, polling only the built-in seat's public view."""
        self._observe_adaptive(session)
        state = self.client.call("get_public_state", {})
        self.last_view = state
        if state["phase"] not in ("human", "agent"):
            return
        wanted = "human" if state["phase"] == "human" else "subagent"
        units = [uid for uid in self.seat["units"]
                 if state["units"][uid]["alive"] and state["units"][uid]["controller"] == wanted]
        if not units:
            return
        unit_id = units[0]
        self.client.call("submit_action", {"unit": unit_id, "round": state["round"],
                                            "action": self._action(state, unit_id)})
        self.client.call("end_turn", {"round": state["round"], "phase": state["phase"]})
        self._observe_adaptive(session)
        self.last_view = self.client.call("get_public_state", {})


class PageJudgeRelay:
    """A room seat whose judge is the REAL page.

    The bridge's own engine approximates the page (flight integrator, wave area, per-unit judge, pity counters, statuses), so a room that mixes an agent with a page
    drifted apart (docs/HYBRID_RUN_20261117.md). This class replaces that approximation: it runs scripts/page_judge_seat.js, the real index.html in a Node vm joined to the room
    like any page seat. The page simulates every throw, judges its own units, hashes the round and ends turns by its own rules; the Session below is only the agent's PUBLIC VIEW,
    overwritten from the page's state after every change (positions, hp, statuses, fence, round, phase, landed throws). The agent still decides the shots only and sees the public
    tools only: no flight formula, no calibration constant and no judge reaches it. Plain throws only (the relay carries nothing else yet)."""

    def __init__(self, session: Session, url: str, code: str, seat: str, *, speed: float = 1.0, rng: int = 1,
                 auto_ready: bool = True, node: str = "node") -> None:
        self.session = session
        self.url = url
        self.code = code
        self.seat = seat
        self.speed = speed
        self.rng = rng
        self.node = node
        self.auto_ready = auto_ready
        self.ready_sent = True
        self.lock = threading.RLock()
        self.cond = threading.Condition(self.lock)
        self.closed = threading.Event()
        self.ready = threading.Event()
        self.proc: Any = None
        self.thread: Optional[threading.Thread] = None
        self.failure: Optional[str] = None
        self.state: Optional[Dict[str, Any]] = None
        self.started = False
        self.unacked: List[Dict[str, Any]] = []       # kept for the interface of ConnectedRelay
        self.outbound: Dict[int, Dict[str, Any]] = {}
        self.received_actions: List[int] = []

    # ---- process
    def start(self) -> None:
        session = self.session
        session.weather_enabled = True
        session.sync = {"status": "pending", "round": session.engine.round_num}
        own = session.engine.hero_red if self.seat == "red" else session.engine.hero_white
        heroes = list(own) if isinstance(own, (list, tuple)) else [own]
        command = [self.node, os.path.join(_HERE, "page_judge_seat.js"), "--relay", self.url.rsplit("/ws", 1)[0], "--code", self.code, "--team", self.seat,
                   "--heroes", ",".join(heroes), "--rng", str(self.rng), "--speed", str(self.speed)]
        self.proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1, cwd=_REPO_ROOT)
        self.thread = threading.Thread(target=self._read, name="pk-page-judge", daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.closed.set()
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.stdin.write(json.dumps({"cmd": "quit"}) + "\n")
                self.proc.stdin.flush()
                self.proc.wait(timeout=2)
        except Exception:
            pass
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.kill()
            if self.proc:
                for pipe in (self.proc.stdin, self.proc.stdout):
                    if pipe:
                        pipe.close()
        except Exception:
            pass
        with self.cond:
            self.cond.notify_all()

    def request_ready(self) -> None:
        """The page seat sends its own `ready` as soon as the room code is known."""

    def _send(self, message: Dict[str, Any]) -> None:
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()

    def _read(self) -> None:
        try:
            for line in self.proc.stdout:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get("event") == "state":
                    with self.cond:
                        self._apply(event["state"], event.get("records", []))
                        self.cond.notify_all()
                elif event.get("event") == "error":
                    self.failure = str(event.get("message", "page error"))[:200]
        except Exception as exc:
            self.failure = type(exc).__name__
        finally:
            self.ready.clear()
            with self.cond:
                self.cond.notify_all()

    # ---- the page's state becomes the agent's public view
    def _engine_id(self, world_id: str) -> str:
        if self.session.engine.units_per_side == 1 or world_id in ("left", "right"):
            return "red_1" if world_id.startswith("left") else "white_1"
        return engine_unit_id(world_id)

    def _apply(self, st: Dict[str, Any], records: List[Dict[str, Any]]) -> None:
        sess = self.session
        self.state = st
        if not self.started:
            if not (st.get("started") and st.get("seed")):
                return
            heroes = {"left": [u["hero"] for u in st["units"] if u["id"].startswith("left")],
                      "right": [u["hero"] for u in st["units"] if u["id"].startswith("right")]}
            sess.reset_for_relay(st["seed"], st.get("scene") or "graveyard", len(heroes["left"]), heroes)
            sess.weather_enabled = True
            self.started = True
            self.ready.set()
        eng = sess.engine
        mine, foe = (self.seat, "white" if self.seat == "red" else "red")
        for row in st["units"]:
            unit = eng.units.get(self._engine_id(row["id"]))
            if unit is None:
                continue
            unit["x"], unit["y"], unit["hp"], unit["max_hp"] = row["x"], row["y"], row["hp"], row["maxHp"]
            unit["alive"] = row["hp"] > 0
            unit["pending_throw"] = None
            engine.set_status_words(unit, row["statuses"])
        eng.central_wall_hp = st["wallHp"]
        eng.wind = st["wind"]
        eng.pity[mine], eng.pity[foe] = st["pity"]["own"], st["pity"]["foe"]
        if "energy" in st:
            sess.energy[mine], sess.energy[foe] = st["energy"]["own"], st["energy"]["foe"]
        if "ultUsed" in st:
            sess.ultimates_used[mine], sess.ultimates_used[foe] = st["ultUsed"]["own"], st["ultUsed"]["foe"]
        relay_state = st.get("relay") or {}
        round_number = relay_state.get("round") if isinstance(relay_state.get("round"), int) else st["round"]
        phase_team = relay_state.get("phase")
        new_phase = "human" if phase_team == "red" else "agent" if phase_team == "white" else sess.phase
        if round_number != eng.round_num or new_phase != sess.phase:
            sess.acted.clear()
            sess.moved.clear()
            sess.submission_receipts.clear()
            sess.skipped_units.clear()
        eng.round_num = round_number
        sess.phase = new_phase
        if phase_team in ("red", "white"):
            sess.relay_team = phase_team
        sess.deadline = None
        for team, key in ((mine, "activeOwn"), (foe, "activeFoe")):
            ids = sess._team_unit_ids(team)
            wanted = self._engine_id(st[key])
            if wanted in ids:
                sess.active_unit_index[team] = ids.index(wanted)
        for rec in records:
            team = mine if rec["team"] == "own" else foe
            unit_id = self._engine_id(rec["unit"])
            target = self._engine_id(rec["hit_target"]) if rec.get("hit_target") else None
            eng.throw_log.append({
                "throw_id": eng.next_throw_id, "round": rec["round"], "team": team, "unit": unit_id,
                "controller": "human" if team == "red" else "subagent", "angle": rec["angle"], "power": rec["power"],
                "wind_at_throw": rec["wind"], "landing_x": rec["landing_x"], "landing_y": rec["landing_y"], "hit_type": rec["hit_type"],
                "hit_target": target, "damage_dealt": rec["damage"], "critical": False,
                "statuses": engine._status_words(eng.units[target]) if target in eng.units else [], "knockback": 0, "ultimate": bool(rec.get("ultimate", False)),
                "path": rec.get("path", [])})
            eng.next_throw_id += 1
            if len(eng.throw_log) > 400:
                del eng.throw_log[:100]
        if st.get("gameOver") in ("player", "ai"):
            sess.winner = mine if st["gameOver"] == "player" else foe
            alive = {t: any(u["alive"] for u in eng.units.values() if u["team"] == t) for t in ("red", "white")}
            sess.winner_reason = "round_cap" if alive["red"] and alive["white"] else None
            sess.phase = "over"
        sess.sync = {"status": "out_of_sync" if st.get("outOfSync") else "ok", "round": round_number}

    # ---- what the McpServer asks of a relay
    def send_action(self, arguments: Dict[str, Any]) -> None:
        action = arguments["action"]
        cmd = "ultimate" if action.get("type") == "ultimate" else "throw"
        self._send({"cmd": cmd, "angle": action["angle"], "power": action["power"]})

    def send_end_turn(self, arguments: Dict[str, Any], before_round: int) -> None:
        """The page ends its own turns after the landing; nothing to send."""

    def wait_for_judges(self, seconds: float = 10.0) -> bool:
        return True

    def pass_turn(self) -> None:
        self._send({"cmd": "pass"})

    def wait_turn_over(self, phase: str, round_number: int, seconds: float = 60.0) -> bool:
        """Block until the page has passed the turn on (the relay phase or round moved on, or the match is over)."""
        deadline = time.monotonic() + seconds
        with self.cond:
            while time.monotonic() < deadline and not self.closed.is_set():
                sess = self.session
                if sess.phase != phase or sess.engine.round_num != round_number or sess.winner is not None:
                    return True
                self.cond.wait(0.2)
        return False


class ConnectedRelay:
    """Forward MCP actions to a room relay while keeping all flight maths local.

    Connected mode uses ``flight_py.simulate`` rather than the practice engine's
    WIND_PUSH approximation.  Offline mode never creates this bridge and retains
    its historical engine behaviour.
    """

    _FATAL_ERRORS = frozenset(("unknown_code", "room_full", "unknown_token", "resume_expired",
                               "invalid_seat", "invalid_resume", "room_closed", "invalid_invite", "mcp_disabled", "team_full", "invalid_name"))
    _RECONNECT_DELAYS = (0.2, 0.5, 1.0, 2.0, 4.0, 8.0)
    _RECONNECT_LIMIT_SECONDS = 60.0

    def __init__(self, session: Session, url: str, code: str, seat: str,
                 *, auto_ready: bool = False, client_addr: Optional[str] = None,
                 gateway_token: Optional[str] = None, explicit_units: bool = True,
                 claim_heroes: Optional[List[str]] = None, invite: Optional[str] = None, name: Optional[str] = None) -> None:
        self.invite = invite                    # ROOM-FLOW R11: the ticket a player gave this agent
        self.name = name
        self.briefing: Optional[Dict[str, Any]] = None
        self.pick_again: Optional[str] = None   # the relay refused this seat's heroes before the start (a teammate holds one)
        self.session = session
        self.url = url
        self.code = code
        self.seat = seat
        self.auto_ready = auto_ready
        self.client_addr = client_addr          # MCP-RISK-A: the remote client this hosted seat serves (None = a local bridge)
        self.gateway_token = gateway_token      # proves to the relay that the address above comes from the hosted gateway
        self.explicit_units = explicit_units
        self.claim_heroes = list(claim_heroes) if claim_heroes is not None else None
        self.outgoing: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self.ready = threading.Event()
        self.closed = threading.Event()
        self.lock = threading.RLock()
        self.cond = threading.Condition(self.lock)
        self.thread = threading.Thread(target=self._run, name="pk-relay", daemon=True)
        self.last_seq = 0
        self.ready_sent = False
        self.failure: Optional[str] = None
        self.relay_owners: Dict[str, str] = {}   # world unit id -> seat id, from `start` and an AI hand-over
        self.seat_token: Optional[str] = None
        self.seat_id: str = ""
        self.started: bool = False
        self.reconnect_count: int = 0
        self.deliberate_leave: bool = False
        self.local_hashes: Dict[int, str] = {}
        self.outbound: Dict[int, Dict[str, Any]] = {}
        self.unacked: List[Dict[str, Any]] = []
        self.judged_refs: set = set()
        self.received_actions: List[int] = []
        self.last_sent_action: Optional[Dict[str, Any]] = None
        self.last_sent_engine_unit: Optional[str] = None

    def start(self) -> None:
        self.session.weather_enabled = True
        self.session.sync = {"status": "pending", "round": self.session.engine.round_num}
        self.thread.start()

    def leave(self, timeout: float = 1.5) -> None:
        """Send an explicit leave to the relay (releasing the seat immediately) and stop the background loop."""
        self.deliberate_leave = True
        self.outgoing.put({"type": "leave"})
        if self.thread.is_alive():
            self.thread.join(timeout=timeout)
        self.close()

    def close(self) -> None:
        self.deliberate_leave = True
        self.closed.set()
        with self.cond:
            self.cond.notify_all()
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def request_ready(self) -> None:
        """Mark this connected seat ready after its caller has chosen to start."""
        if not self.ready_sent:
            ready: Dict[str, Any] = {"type": "ready"}
            units = self.own_heroes()
            if units:
                ready["units"] = units   # team rooms: the other devices learn this seat's heroes from here
            self.outgoing.put(ready)
            self.ready_sent = True

    def own_heroes(self) -> List[str]:
        """This seat's hero list in unit order when the session plays a team match (empty for one versus one: that wire is unchanged)."""
        if self.claim_heroes is not None:
            return list(self.claim_heroes)
        eng = self.session.engine
        if eng.units_per_side <= 1:
            return []
        return [unit["hero"] for uid, unit in sorted(eng.units.items()) if unit["team"] == self.seat]

    def wire_unit(self, unit_id: str) -> str:
        """The unit id as it goes on the wire: engine ids at N = 1 (as before), world ids left_i / right_i in team matches."""
        return world_unit_id(unit_id) if self.session.engine.units_per_side > 1 else unit_id

    def engine_unit(self, unit_id: Any) -> Any:
        """The inverse of wire_unit for an incoming message; an unknown shape is returned as it is so the caller's own checks refuse it."""
        if self.session.engine.units_per_side > 1:
            try:
                return engine_unit_id(unit_id)
            except TypeError:
                return unit_id
        return unit_id

    def effective_wind(self) -> float:
        """Mirror index.html effWind: a storm increases magnitude, never flips sign."""
        wind = float(self.session.engine.wind)
        bonus = float(self.session.weather()["windBonus"])
        return wind + (math.copysign(bonus, wind) if wind else 0.0)

    def send_action(self, arguments: Dict[str, Any]) -> None:
        unit_id = arguments["unit"]
        action = arguments["action"]
        if action.get("type") != "throw":
            return
        unit = self.session.engine.units[unit_id]
        start = {"x": float(unit["x"] + unit["launch"]["fwd"] * unit["facing"]),
                 "y": float(unit["y"] - unit["launch"]["up"])}
        flight = simulate_flight({"startX": start["x"], "startY": start["y"],
                                  "dirX": unit["facing"], "angleDeg": action["angle"],
                                  "power": action["power"], "wind": self.effective_wind(),
                                  "wave": unit.get("weapon") == "proj_soundwave",
                                  "wall": self.session.engine.central_wall_hp > 0})
        if self.session.engine.central_wall_hp > 0 and self.wall_contact_index(flight["points"]) is not None:
            self.hit_wall()   # both 1v1 and team rooms: the fence is part of the round hash, and only the devices' own simulations see it
        outbound = {"type": "action", "round": self.session.engine.round_num,
                    "phase": self.seat, "unit": self.wire_unit(unit_id), "kind": "throw",
                    "angle": action["angle"], "power": action["power"], "start": start,
                    "dirX": unit["facing"],
                    "claimed_landing": {"x": flight["landingX"], "y": flight["landingY"]}}
        self.unacked.append({"unit": unit_id})
        self.last_sent_action = dict(outbound)
        self.last_sent_engine_unit = unit_id
        self.outgoing.put(outbound)

    def sync_wind(self) -> None:
        """Connected play: the round wind is the room's seeded one (determinism_py.wind, the page's Determinism.wind), not the practice engine's own random draw;
        without this every flight here differs from the page's (found by the hybrid room run: round 1 of one seed was 2.0 on the page and -3.0 in the engine)."""
        eng = self.session.engine
        eng.wind = determinism_py.wind(eng.seed, eng.round_num)

    @staticmethod
    def wall_contact_index(points: List[Dict[str, Any]]) -> Optional[int]:
        """Index of the first flight point inside the central wall (engine rule: x range of the fence and below its top), or None."""
        for index, point in enumerate(points):
            if engine.WALL_X_MIN <= point["x"] <= engine.WALL_X_MAX and point["y"] >= engine.WALL_TOP_Y:
                return index
        return None

    def hit_wall(self) -> None:
        """A throw that reaches the fence damages it by WALL_HIT_DMG while it stands (the page does it in its own simulation; no judge message carries it)."""
        eng = self.session.engine
        if eng.central_wall_hp > 0:
            eng.central_wall_hp = max(0, eng.central_wall_hp - engine.WALL_HIT_DMG)

    def wait_for_judges(self, seconds: float = 10.0) -> bool:
        """Block (the relay runs on its own thread) until every action this bridge sent has its judge, at most `seconds`.
        Returns False on a timeout: the turn then ends on what is known, and the round hash will say if that was wrong."""
        deadline = time.monotonic() + seconds
        while (self.unacked or self.outbound) and not self.closed.is_set() and time.monotonic() < deadline:
            time.sleep(0.02)
        return not (self.unacked or self.outbound)

    def send_end_turn(self, arguments: Dict[str, Any], before_round: int) -> None:
        self.outgoing.put({"type": "end_turn", "round": before_round, "phase": self.seat})
        if self.session.engine.round_num > before_round:
            self.sync_wind()
            self.session.set_relay_phase(engine.first_team_of_round(self.session.engine.round_num))
            self.send_round_hash(before_round)

    def send_round_hash(self, round_number: int) -> None:
        state = self._hash_state(round_number)
        digest = round_hash(state)
        dump_path = os.environ.get("PK_HASH_DUMP")
        if dump_path:   # diagnostics for the hybrid room test: what this bridge hashed (scripts/run_hybrid_room.py compares it with the page's own inputs)
            try:
                with open(dump_path, "a", encoding="utf-8") as handle:
                    handle.write(json.dumps({"round": round_number, "hash": digest, "units": [[row["id"], row["x"], row["y"], row["hp"], "|".join(row["statuses"])] for row in state["units"]], "wall": state["wallHp"]}) + "\n")
            except OSError:
                pass
        self.local_hashes[round_number] = digest
        self.session.sync = {"status": "pending", "round": round_number}
        self.outgoing.put({"type": "round_hash", "round": round_number, "hash": digest})

    def _hash_state(self, round_number: int) -> Dict[str, Any]:
        """The state the PAGE hashes (`currentRoundHash` in index.html, read-only), so a page seat and this bridge agree.

        One unit per team (the frozen page recipe): ids `left` / `right` (page: `localPerspective.worldUnitId("left")`
        in world frame; the bridge's red_1 / white_1 are world left / right), world x, y, hp, alive, public status
        words, wall hp, the round that just ended, phase string `"throws:" + throws`, and the match seed. In a room the
        page calls it from `resolveRound` after it has emptied `roundThrowNumbers`, so its phase is the bare "throws:".
        Two or three units per team (docs/relay_team_page_hooks.md item 4): every unit of both teams, dead ones kept,
        ids left_i / right_i via `world_unit_id`, `teamSize`, phase "round_end".
        The wind is not part of the canonical text (round_hash_py), so it is not passed."""
        eng = self.session.engine
        count = eng.units_per_side
        bare = {"red_1": "left", "white_1": "right"}
        rows = [{"id": bare[uid] if count == 1 else world_unit_id(uid), "x": unit["x"], "y": unit["y"], "hp": unit["hp"],
                 "alive": bool(unit["alive"]), "statuses": engine._status_words(unit)}
                for uid, unit in eng.units.items()]
        state = {"units": rows, "wallHp": eng.central_wall_hp, "round": round_number,
                 "phase": "throws:" if count == 1 else "round_end", "seed": eng.seed}
        if count > 1:
            state["teamSize"] = count
        return state

    def _run(self) -> None:
        try:
            asyncio.run(self._run_async())
        except Exception as exc:
            self.failure = self.failure or type(exc).__name__
        finally:
            self.ready.clear()
            with self.cond:
                self.cond.notify_all()

    async def _run_async(self) -> None:
        import websockets  # Connected mode alone requires the relay dependency.
        attempt = 0
        reconnect_started_at: Optional[float] = None
        while not self.closed.is_set():
            if self.failure in self._FATAL_ERRORS:
                break
            was_seated = self.seat_token is not None
            try:
                extra = ({"X-PK-Gateway-Token": self.gateway_token, "X-PK-Client-Addr": self.client_addr}
                         if self.client_addr and self.gateway_token else None)
                async with websockets.connect(self.url, max_size=64 * 1024, ping_interval=20, ping_timeout=20,
                                              additional_headers=extra) as socket:
                    if self.seat_token:
                        await socket.send(json.dumps({
                            "type": "resume", "seat_token": self.seat_token, "last_seq": self.last_seq,
                        }, separators=(",", ":")))
                        self.reconnect_count += 1
                    else:
                        join_msg: Dict[str, Any] = {
                            "type": "join", "code": self.code, "seat": self.seat, "client_version": "mcp-stdio", "client_kind": "mcp",
                        }
                        units = self.own_heroes() if self.explicit_units else []
                        if units:
                            join_msg["units"] = units
                        if self.invite:
                            join_msg["invite"] = self.invite
                        if self.name:
                            join_msg["name"] = self.name
                        await socket.send(json.dumps(join_msg, separators=(",", ":")))
                    attempt = 0
                    reconnect_started_at = None
                    last_send = time.monotonic()
                    self.ready.set()
                    with self.cond:
                        self.cond.notify_all()
                    while not self.closed.is_set():
                        if self.failure in self._FATAL_ERRORS:
                            break
                        try:
                            raw = await asyncio.wait_for(socket.recv(), 0.05)
                        except asyncio.TimeoutError:
                            raw = None
                        if raw is not None:
                            self._receive(json.loads(raw))
                            if self.failure in self._FATAL_ERRORS:
                                break
                        leave_sent = False
                        while True:
                            try:
                                message = self.outgoing.get_nowait()
                            except queue.Empty:
                                break
                            wait = RELAY_SEND_GAP_SECONDS - (time.monotonic() - last_send)
                            if wait > 0:
                                await asyncio.sleep(wait)   # the relay refuses a socket above 10 messages a second; a quick agent must stay under it
                            last_send = time.monotonic()
                            await socket.send(json.dumps(message, separators=(",", ":")))
                            if message.get("type") == "leave":
                                leave_sent = True
                                break
                        if leave_sent:
                            self.closed.set()
                            break
            except Exception as exc:
                self.ready.clear()
                closed_with = getattr(exc, "rcvd", None)
                if closed_with is not None and getattr(closed_with, "code", None) == 1000 and getattr(closed_with, "reason", "") in ("inviter_left", "host_left", "removed_by_host", "ai_off", "agents_off"):
                    self.failure = "kicked:%s" % closed_with.reason   # the relay removed this seat; a send can fail before the `kicked` message is read
                    break
                if self.closed.is_set() or self.deliberate_leave or self.failure in self._FATAL_ERRORS:
                    break
                now = time.monotonic()
                if reconnect_started_at is None:
                    reconnect_started_at = now
                if now - reconnect_started_at >= self._RECONNECT_LIMIT_SECONDS:
                    self.failure = self.failure or type(exc).__name__
                    break
                # Only retry indefinitely within the grace window if we had a seat token or initial transport error.
                if not was_seated and self.failure is not None:
                    break
                delay = self._RECONNECT_DELAYS[min(attempt, len(self._RECONNECT_DELAYS) - 1)]
                attempt += 1
                end_sleep = time.monotonic() + delay
                while time.monotonic() < end_sleep and not self.closed.is_set():
                    await asyncio.sleep(min(0.05, end_sleep - time.monotonic()))
        self.ready.clear()

    def _receive(self, message: Dict[str, Any]) -> None:
        with self.cond:
            self._receive_locked(message)
            self.cond.notify_all()

    def _receive_locked(self, message: Dict[str, Any]) -> None:
        message_type = message.get("type")
        if message_type == "error":
            err_code = str(message.get("code", "relay_error"))
            if err_code == "invalid_units" and not self.started:
                self.pick_again = str(message.get("message") or err_code)   # red team (polish) P2: a refused pick before the start is not the end; lock_hero may try again
                return
            if err_code != "duplicate_judge" and not str(self.failure or "").startswith("kicked:"):
                self.failure = err_code
            return
        if message_type == "kicked":
            self.failure = "kicked:%s" % message.get("reason", "removed")   # the host removed this seat, or its inviter left
            self.deliberate_leave = True   # red team A1/A12: the seat is gone; no reconnect (its resume would only overwrite why)
            return
        if message_type == "room_state":
            if isinstance(message.get("briefing"), dict):
                self.briefing = message["briefing"]
            token = message.get("seat_token")
            if isinstance(token, str) and token:
                self.seat_token = token
            sid = message.get("seat_id")
            if isinstance(sid, str) and sid:
                self.seat_id = sid
            if message.get("started"):
                self.started = True
            if self.auto_ready and not self.ready_sent:
                # Connected seats wait for an explicit request unless the CLI opted in.
                self.request_ready()
            return
        if message_type == "start":
            seed = message.get("seed")
            scene = message.get("scene")
            if isinstance(seed, int) and isinstance(scene, str):
                team_size = message.get("team_size", 1)
                parsed_ts = team_size if isinstance(team_size, int) and not isinstance(team_size, bool) else None
                self.session.reset_for_relay(seed, scene, parsed_ts, message.get("heroes"))
                self.relay_owners = dict(message["owners"]) if isinstance(message.get("owners"), dict) else {}
                if self.claim_heroes is not None:
                    owners = message.get("owners")
                    if not isinstance(owners, dict) or not self.seat_id:
                        self.failure = "owners_missing_seat"
                        return
                    owned = sorted(
                        engine_unit_id(wuid)
                        for wuid, owner_sid in owners.items()
                        if owner_sid == self.seat_id and isinstance(wuid, str)
                    )
                    if not owned:
                        self.failure = "owners_missing_seat"
                        return
                    self.session.seat["units"] = owned
                self.sync_wind()
                self.started = True
                self.session.sync = {"status": "pending", "round": self.session.engine.round_num}
            return
        if message_type == "action_ack":
            # The action broadcast has the same sequence number and reaches the
            # sender first. A receipt is not a replay and must still clear it.
            details = self.unacked.pop(0) if self.unacked else {}
            details.update({"round": message.get("round"), "phase": message.get("phase")})
            if message["seq"] not in self.judged_refs:
                self.outbound[message["seq"]] = details
            return
        seq = message.get("seq")
        if isinstance(seq, int):
            if seq <= self.last_seq:
                return
            self.last_seq = seq
        if message_type == "seat_left":
            left_team = message.get("team")
            left_seat = message.get("seat_id")
            if not self.started:
                return   # red team A12: before the start a seat that leaves decides nothing (the relay only reports it)
            if message.get("ai"):
                # ROOM-FLOW R9: a lost AI filler is nobody's forfeit. A teammate takes its units; with no seat left on its team the match has no result.
                owners = message.get("owners")
                if isinstance(owners, dict):
                    self.relay_owners = dict(owners)
                if message.get("team_empty") and self.session.phase != "over":
                    self.session.winner, self.session.winner_reason, self.session.phase = "none", "ai_seat_lost", "over"
                elif self.claim_heroes is not None and isinstance(owners, dict) and left_team == self.seat:
                    self.session.seat["units"] = sorted(engine_unit_id(unit) for unit, owner in owners.items() if owner == self.seat_id and isinstance(unit, str))
                return
            gone = [engine_unit_id(unit) for unit, owner in self.relay_owners.items() if owner == left_seat and isinstance(unit, str)]
            if gone and not any(self.session.engine.units.get(unit, {}).get("alive", True) for unit in gone):
                return   # the same rule as the page (red-team R2A-F1): a seat whose units are all down cannot stall play, so leaving decides nothing
            if left_team in ("red", "white") and left_seat != self.seat_id and self.session.phase != "over":
                self.session.winner = ("white" if self.seat == "red" else "red") if left_team == self.seat else self.seat
                self.session.phase = "over"
            return
        if message_type == "action":
            self._apply_action(message)
        elif message_type == "judge":
            self._apply_judge(message)
        elif message_type == "end_turn":
            self._apply_end_turn(message)
        elif message_type == "round_hash":
            round_number = message.get("round")
            if isinstance(round_number, int) and round_number in self.local_hashes:
                self.session.sync = {"status": "ok", "round": round_number}
        elif message_type == "out_of_sync" and isinstance(message.get("round"), int):
            self.session.sync = {"status": "out_of_sync", "round": message["round"]}

    def _apply_action(self, message: Dict[str, Any]) -> None:
        seat_id = message.get("seat_id", "")
        team = seat_id.split("-", 1)[0]
        if team not in ("red", "white"):
            return
        if seat_id == self.seat_id or (team == self.seat and self.claim_heroes is None):
            return
        action = {"type": "throw", "angle": message.get("angle"), "power": message.get("power")}
        unit_id = self.engine_unit(message.get("unit"))
        is_teammate = (team == self.seat)
        actor_seat = self.session.seats["referee"] if is_teammate else self.session.seats[team]
        try:
            self.session.call("submit_action", {"unit": unit_id, "action": action,
                                                "round": message["round"]}, actor_seat)
        except (KeyError, ToolError):
            return
        if is_teammate:
            seq = message.get("seq")
            if isinstance(seq, int) and seq not in self.judged_refs:
                self.outbound[seq] = {"unit": unit_id, "round": message.get("round"), "phase": message.get("phase")}
            start = message.get("start") or {}
            try:
                attacker = self.session.engine.units[unit_id]
                flight = simulate_flight({"startX": start["x"], "startY": start["y"],
                                          "dirX": message.get("dirX"), "angleDeg": message["angle"],
                                          "power": message["power"], "wind": self.effective_wind(),
                                          "wave": attacker.get("weapon") == "proj_soundwave",
                                          "wall": self.session.engine.central_wall_hp > 0})
                if self.session.engine.central_wall_hp > 0 and self.wall_contact_index(flight["points"]) is not None:
                    self.hit_wall()
            except (KeyError, TypeError, ValueError):
                pass
            return
        self.received_actions.append(message["seq"])
        self._judge_action(message, unit_id)
        self.session.engine.units[unit_id]["pending_throw"] = None

    def _judge_action(self, message: Dict[str, Any], unit_id: Optional[str] = None) -> None:
        unit_id = unit_id if unit_id is not None else message.get("unit")
        start = message.get("start") or {}
        try:
            attacker = self.session.engine.units[unit_id]
            flight = simulate_flight({"startX": start["x"], "startY": start["y"],
                                      "dirX": message.get("dirX"), "angleDeg": message["angle"],
                                      "power": message["power"], "wind": self.effective_wind(),
                                      "wave": attacker.get("weapon") == "proj_soundwave",
                                      "wall": self.session.engine.central_wall_hp > 0})
        except (KeyError, TypeError, ValueError):
            return
        claimed = message.get("claimed_landing") or {}
        if (abs(float(claimed.get("x", flight["landingX"])) - flight["landingX"]) > 4 or
                abs(float(claimed.get("y", flight["landingY"])) - flight["landingY"]) > 4):
            self.session.sync = {"status": "out_of_sync", "round": message["round"]}
        own = [unit for unit in self.session.engine.units.values() if unit["team"] == self.seat and unit["alive"]]
        hit_pair = None
        wall_at = self.wall_contact_index(flight["points"]) if self.session.engine.central_wall_hp > 0 else None
        for index, point in enumerate(flight["points"]):
            if wall_at is not None and index >= wall_at:
                break   # the fence stops the throw before it reaches anyone behind it
            # the first living own unit the path touches (TEAM_RULES item 4); on a tie the unit nearest to the projectile
            touched = [unit for unit in own if engine.GameState.projectile_hits(attacker, unit, point["x"], point["y"])]
            if touched:
                hit_pair = (min(touched, key=lambda unit: abs(float(unit["x"]) - float(point["x"]))), point)
                break
        target = hit_pair[0] if hit_pair else None
        if target is None and wall_at is not None:
            self.hit_wall()   # the throw ended on the fence
        outcome = {"damage": 0, "statuses": [], "knockback": 0}
        if target is not None:
            impact = hit_pair[1]
            self.session.engine.weather = self.session.weather()
            outcome = self.session.engine._apply_hit(attacker, target, impact["x"], impact["y"])
        if self.session.engine.units_per_side > 1 and target is None:
            # team rooms: a miss names no unit (the relay refuses a unit that is not one of the sender's own, and `unit: null` is not a unit id)
            self.outgoing.put({"type": "judge", "ref": message["seq"], "hit": False})
            return
        self.outgoing.put({"type": "judge", "ref": message["seq"], "hit": target is not None,
                           "unit": self.wire_unit(target["id"]) if target else None, "damage": outcome["damage"],
                           "hp_after": target["hp"] if target else None,
                           "statuses": outcome["statuses"], "knockback": outcome["knockback"]})

    def _apply_judge(self, message: Dict[str, Any]) -> None:
        ref = message.get("ref")
        details = self.outbound.get(ref)
        if details is None and ref == self.last_seq and self.last_sent_action is not None:
            # The target may judge before the relay's acknowledgement reaches us.
            # Recover the source from the single outstanding local action instead
            # of letting message timing leave its pending throw in the hash.
            details = {"unit": self.last_sent_engine_unit}
        if details is None:
            return
        source_id = details.get("unit")
        source = self.session.engine.units.get(source_id) if isinstance(source_id, str) else None
        if source is not None:
            source["pending_throw"] = None
            if source.get("statuses", {}).get("weak", 0):
                source["statuses"]["weak"] -= 1
                if not source["statuses"]["weak"]:
                    source["statuses"].pop("weak")
        unit_id = self.engine_unit(message.get("unit"))
        if isinstance(unit_id, str) and unit_id in self.session.engine.units:
            unit = self.session.engine.units[unit_id]
            hp_after = message.get("hp_after")
            if isinstance(hp_after, (int, float)):
                unit["hp"] = max(0, float(hp_after))
                unit["alive"] = unit["hp"] > 0
            # Relay messages are authoritative snapshots. Never merge stale status effects.
            engine.set_status_words(unit, message.get("statuses", []))
            knockback = message.get("knockback", 0)
            if source is not None and isinstance(knockback, (int, float)) and knockback > 0 and unit["alive"]:
                direction = 1 if unit["x"] > source["x"] else -1
                lo, hi = engine.MOVE_X_LIMITS[unit["team"]]
                unit["x"] = round(max(lo, min(hi, unit["x"] + direction * float(knockback))), 1)
        if isinstance(ref, int):
            self.judged_refs.add(ref)
            self.outbound.pop(ref, None)

    def _apply_end_turn(self, message: Dict[str, Any]) -> None:
        seat_id = message.get("seat_id", "")
        team = seat_id.split("-", 1)[0]
        if team not in ("red", "white"):
            return
        if seat_id == self.seat_id or (team == self.seat and self.claim_heroes is None):
            return
        before = self.session.engine.round_num
        actor_seat = self.session.seats["referee"] if team == self.seat else self.session.seats[team]
        try:
            self.session.call("end_turn", {"round": before, "phase": self.session.phase}, actor_seat)
        except ToolError:
            return
        if self.session.engine.round_num > before:
            self.sync_wind()
            self.session.set_relay_phase(message.get("next_phase", ""))
            self.send_round_hash(before)


# ------------------------------------------------------------------ JSON-RPC / MCP layer
def _rpc_error(req_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


class McpServer:
    def __init__(self, session: Session, seat: Optional[Dict[str, Any]] = None,
                 transcript: Optional[Any] = None, *,
                 enable_room_tools: bool = False,
                 default_relay_url: Optional[str] = None,
                 allow_custom_relay: bool = True,
                 page_judge_mode: str = "off",
                 page_speed: float = 1.0,
                 client_addr: Optional[str] = None,
                 gateway_token: Optional[str] = None) -> None:
        self.session = session
        self.client_addr = client_addr
        self.gateway_token = gateway_token
        self.seat = seat or session.seat
        self.transcript = transcript
        self.opponent: Optional[Any] = None
        self.relay: Optional[Any] = None
        self.enable_room_tools = enable_room_tools
        self.default_relay_url = default_relay_url
        self.allow_custom_relay = allow_custom_relay
        self.page_judge_mode = page_judge_mode
        self.page_speed = page_speed

    def _tools(self) -> List[Dict[str, Any]]:
        return (TOOLS + ROOM_TOOLS) if self.enable_room_tools else TOOLS

    def _tool_names(self) -> List[str]:
        return (TOOL_NAMES + ROOM_TOOL_NAMES) if self.enable_room_tools else TOOL_NAMES

    def close(self) -> None:
        if self.relay is not None:
            if hasattr(self.relay, "leave"):
                self.relay.leave()
            else:
                self.relay.close()
            self.relay = None

    def handle_message(self, msg: Any) -> Optional[Dict[str, Any]]:
        """Return the response for a request, or None for notifications and client responses."""
        if not isinstance(msg, dict):
            return _rpc_error(None, -32600, "Invalid Request")
        if "method" not in msg and ("result" in msg or "error" in msg):
            return None  # a response to a request we never send
        method = msg.get("method")
        if msg.get("jsonrpc") != "2.0" or not isinstance(method, str):
            return _rpc_error(msg.get("id"), -32600, "Invalid Request")
        is_notification = "id" not in msg
        req_id = msg.get("id")
        if not is_notification and (isinstance(req_id, bool) or not isinstance(req_id, (int, str))):
            return _rpc_error(None, -32600, "Invalid Request: id must be a string or integer")
        params = msg.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return None if is_notification else _rpc_error(req_id, -32602, "params must be an object")
        if is_notification:
            return None  # notifications/initialized, notifications/cancelled, ...: nothing to do
        try:
            return self._dispatch(req_id, method, params)
        except Exception as exc:  # never crash the loop
            sys.stderr.write("internal error: %r\n" % (exc,))
            return _rpc_error(req_id, -32603, "Internal error")

    def _dispatch(self, req_id: Any, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if method == "initialize":
            requested = params.get("protocolVersion")
            version = requested if requested in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[0]
            instructions = (
                "Pumpkin Killer. Call join_room with a 6-character code or invite URL, then loop: "
                "wait_for_turn -> get_history -> submit_action per unit -> end_turn. "
                "Call leave_room before joining another room."
                if self.enable_room_tools else
                "Pumpkin Killer. Poll get_public_state until phase is 'agent', "
                "learn from get_history, submit_action per unit, then end_turn "
                "with phase 'agent'. Never act in the human phase."
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": version,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": instructions,
            }}
        if method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": self._tools()}}
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            if arguments is None:
                arguments = {}
            if not isinstance(name, str) or name not in self._tool_names():
                return _rpc_error(req_id, -32602, "Unknown tool: %s" % (name,))
            if not isinstance(arguments, dict):
                return _rpc_error(req_id, -32602, "arguments must be an object")
            return {"jsonrpc": "2.0", "id": req_id, "result": self._call_tool(name, arguments)}
        return _rpc_error(req_id, -32601, "Method not found: %s" % method)

    def _page_submit(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """submit_action in a room judged by the page: the same checks as Session._tool_submit_action for a plain throw, then the shot goes to the page."""
        sess, seat = self.session, self.seat
        _reject_unknown(arguments, ("unit", "action", "round"), "submit_action")
        unit_id = _string(arguments.get("unit"), "unit")
        action = arguments.get("action")
        if not isinstance(action, dict):
            raise ToolError("action must be an object with a type")
        if "round" in arguments and _integer(arguments["round"], "round", 1, 10 ** 6) != sess.engine.round_num:
            raise ToolError("stale round: current round is %d" % sess.engine.round_num)
        if sess.phase == "over":
            raise ToolError("the match is over")
        unit = sess.engine.units.get(unit_id)
        if unit is None:
            raise ToolError("unknown unit: %s" % unit_id)
        if not sess._owns_unit(seat, unit_id):
            raise ToolError("seat %s does not control unit %s" % (seat["seat_id"], unit_id))
        if not sess._seat_controls_phase(seat):
            raise ToolError("seat %s does not control the %s phase" % (seat["seat_id"], sess.phase))
        if not unit["alive"]:
            raise ToolError("unit %s is dead" % unit_id)
        active_team = sess._active_team()
        active_unit = sess._active_unit(active_team) if active_team is not None else None
        if active_unit is not None and unit_id != active_unit:
            raise ToolError("unit %s is frozen; active unit is %s" % (unit_id, active_unit))
        atype = _enum(action.get("type"), "action.type", ("throw", "move", "defend", "skill", "ultimate"))
        if atype not in ("throw", "ultimate") or (atype == "ultimate" and unit["hero"] in ("knight", "reaper")):
            # the page refuses these two ultimates in a room as well (index.html toggleUltimate): the knight places hidden points, the reaper's flames start on an orbit read from the clock,
            # so two pages simulate different volleys (gap N10, redteam/evidence/n10_diagnosis_20261123.md)
            raise ToolError("a room judged by the page carries plain throws and thrown ultimates only for now (the knight's and the necromancer's ultimates are not in rooms yet)")
        _reject_unknown(action, ("type", "angle", "power"), "action")
        angle = _number(action.get("angle"), "angle", ANGLE_MIN, ANGLE_MAX)
        power = _number(action.get("power"), "power", POWER_MIN, POWER_MAX)
        if unit_id in sess.acted:
            raise ToolError("unit %s already submitted %s this turn" % (unit_id, sess.acted[unit_id]))
        if atype == "ultimate":
            team = unit["team"]
            if sess.energy[team] < 3:
                raise ToolError("ultimate_not_ready: %s needs three energy pips" % team)
            if sess.ultimates_used[team] >= MAX_ULTIMATES_PER_MATCH:
                raise ToolError("no_ultimates_left: %s has used both ultimates" % team)
        sess.acted[unit_id] = atype
        self.relay.send_action({"unit": unit_id, "action": {"type": atype, "angle": angle, "power": power}})
        return {"ok": True, "unit": unit_id, "action": atype, "angle": angle, "power": power}

    def _page_end_turn(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        sess, relay = self.session, self.relay
        _reject_unknown(arguments, ("phase", "round"), "end_turn")
        with relay.lock:
            for name in ("round", "phase"):
                if name not in arguments:
                    raise ToolError("end_turn requires round and phase for seat %s" % self.seat["seat_id"])
            if _integer(arguments["round"], "round", 1, 10 ** 6) != sess.engine.round_num:
                raise ToolError("stale round: current round is %d" % sess.engine.round_num)
            if sess.phase == "over":
                raise ToolError("the match is over")
            if not sess._seat_controls_phase(self.seat):
                raise ToolError("seat %s does not control the %s phase" % (self.seat["seat_id"], sess.phase))
            if _enum(arguments["phase"], "phase", ("human", "agent")) != sess.phase:
                raise ToolError("current phase is %s, not %s" % (sess.phase, arguments["phase"]))
            ended, round_number, acted = sess.phase, sess.engine.round_num, bool(sess.acted)
        if not acted:
            relay.pass_turn()
        if not relay.wait_turn_over(ended, round_number):
            raise ToolError("the page did not finish the turn in time")
        with relay.lock:
            return {"ended": ended, "phase": sess.phase, "round": sess.engine.round_num}

    def _call_tool_page(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if name == "submit_action":
                with self.relay.lock:
                    payload = self._page_submit(arguments)
            elif name == "end_turn":
                payload = self._page_end_turn(arguments)
            else:
                with self.relay.lock:
                    payload = self.session.call(name, arguments, self.seat)
            result = {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}], "isError": False}
        except ToolError as exc:
            result = {"content": [{"type": "text", "text": json.dumps({"error": str(exc)}, ensure_ascii=False)}], "isError": True}
        except Exception as exc:
            sys.stderr.write("tool failure in %s: %r\n" % (name, exc))
            result = {"content": [{"type": "text", "text": json.dumps({"error": "internal error"})}], "isError": True}
        if self.transcript is not None:
            self.transcript.record(name, arguments, result)
        return result

    def _tool_join_room(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        _reject_unknown(arguments, ("room", "seat", "units", "claim", "heroes", "relay", "invite", "name"), "join_room")
        if self.relay is not None:
            if self.session.phase == "over" or getattr(self.relay, "failure", None) is not None:
                self.close()
            else:
                raise ToolError("already in room %s; call leave_room first" % self.relay.code)
        info = parse_invite(arguments.get("room"))
        if "seat" in arguments and arguments["seat"] is not None:
            seat = _enum(arguments["seat"], "seat", ("red", "white"))
        else:
            seat = info["seat"] or "white"
        if "units" in arguments and arguments["units"] is not None:
            units = _integer(arguments["units"], "units", 1, 3)
        else:
            units = info["units"] or 3
        if "claim" in arguments and arguments["claim"] is not None:
            claim = _integer(arguments["claim"], "claim", 1, units)
        else:
            claim = units
        invite = arguments.get("invite") or info.get("invite")
        if invite is not None:
            # ROOM-FLOW R11: the ticket starts with its team; it gives exactly one unit.
            match = _INVITE_RE.match(_string(invite, "invite", max_len=100))
            if not match:
                raise ToolError("invite is not an invitation from a room (expected red.… or white.…)")
            seat, claim = match.group(1), 1
        name = arguments.get("name")
        if name is not None:
            name = _string(name, "name", max_len=64)
        heroes_arg = arguments.get("heroes")
        hero_list: Optional[List[str]] = None
        claim_heroes: Optional[List[str]] = None
        valid = sorted(engine.HERO_TEMPLATES)
        if heroes_arg is not None:
            max_h = claim if claim < units else units
            if not isinstance(heroes_arg, list) or not (1 <= len(heroes_arg) <= max_h):
                raise ToolError("heroes must be a list of 1 to %d hero ids" % max_h)
            picked = [_enum(h, "heroes", tuple(valid)) for h in heroes_arg]
            if len(picked) < max_h:
                extras = [h for h in valid if h not in picked]
                picked = (picked + extras)[:max_h]
            if claim < units:
                claim_heroes = list(picked)
            else:
                hero_list = list(picked)
        elif claim < units:
            claim_heroes = valid[:claim]
        if invite is not None and claim_heroes is None:
            claim_heroes, hero_list = (hero_list or valid)[:1], None
        if self.allow_custom_relay:
            raw_relay = arguments.get("relay") or info["relay"] or self.default_relay_url
        else:
            raw_relay = self.default_relay_url
        if not raw_relay:
            raise ToolError("no relay URL configured (pass relay or configure default_relay_url)")
        relay_url = normalize_relay_url(raw_relay)
        sess = Session(
            seed=1, turn_seconds=0, human_turn_seconds=0, seat=seat, units=units,
            hero_red=hero_list if seat == "red" else None,
            hero_white=hero_list if seat == "white" else None,
        )
        node_path = shutil.which("node")
        use_page = self.page_judge_mode == "on" or (
            self.page_judge_mode == "auto" and node_path is not None and os.path.exists(os.path.join(_REPO_ROOT, "index.html"))
        )
        if invite is not None:
            use_page = False   # the page judge plays a whole side; an invited agent owns one unit
        if use_page:
            relay: Any = PageJudgeRelay(sess, relay_url, info["code"], seat, speed=self.page_speed, rng=1, node=node_path or "node")
        else:
            explicit_units = bool(arguments.get("units") is not None or info["units"] is not None or hero_list is not None or claim_heroes is not None)
            relay = ConnectedRelay(sess, relay_url, info["code"], seat, auto_ready=invite is None or heroes_arg is not None,
                                   client_addr=self.client_addr, gateway_token=self.gateway_token,
                                   explicit_units=explicit_units and (invite is None or heroes_arg is not None), claim_heroes=claim_heroes,
                                   invite=invite, name=name)
        relay.start()
        deadline = time.monotonic() + 5.0
        with relay.cond:
            while time.monotonic() < deadline:
                if relay.failure is not None:
                    break
                if getattr(relay, "seat_token", None) or getattr(relay, "started", False) or getattr(relay, "state", None) is not None:
                    break
                relay.cond.wait(0.1)
        if relay.failure is not None:
            err_code = relay.failure
            relay.close()
            raise ToolError("failed to join room %s: %s" % (info["code"], err_code))
        if not (getattr(relay, "seat_token", None) or getattr(relay, "started", False) or getattr(relay, "state", None) is not None):
            relay.close()
            raise ToolError("timed out joining room %s on %s" % (info["code"], relay_url))
        self.session = sess
        self.seat = sess.seat
        self.relay = relay
        result = {
            "ok": True,
            "code": info["code"],
            "seat": seat,
            "seat_id": getattr(relay, "seat_id", ""),
            "units": units,
            "claim": claim,
            "started": bool(getattr(relay, "started", False)),
            "phase": sess.phase,
            "round": sess.engine.round_num,
            "next": "Call wait_for_turn until status is 'your_turn'.",
        }
        if invite is not None:
            briefing = getattr(relay, "briefing", None)
            if briefing is not None:
                result["briefing"] = briefing
            flow = "Then loop: wait_for_turn, get_public_state, submit_action, end_turn."
            result["next"] = ("Your hero is locked. " + flow) if heroes_arg is not None else (
                "Call lock_hero with one of briefing.heroes now (within %s seconds, or one is picked for you). " % (briefing or {}).get("pick_within_seconds", 30) + flow)
        return result

    def _tool_lock_hero(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        _reject_unknown(arguments, ("hero",), "lock_hero")
        relay = self.relay
        if relay is None or not isinstance(relay, ConnectedRelay):
            raise ToolError("not in a room; call join_room first")
        if relay.failure is not None:
            raise ToolError("the room connection failed: %s" % relay.failure)
        if relay.started:
            raise ToolError("the match has already started")
        if relay.claim_heroes is None or len(relay.claim_heroes) != 1:
            raise ToolError("lock_hero is for a seat that owns one unit")
        hero = _enum(arguments.get("hero"), "hero", tuple(sorted(engine.HERO_TEMPLATES)))
        relay.claim_heroes = [hero]
        relay.pick_again = None
        relay.ready_sent = False
        relay.request_ready()
        return {"ok": True, "hero": hero, "next": "Call wait_for_turn until status is 'your_turn'."}

    def _tool_leave_room(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        _reject_unknown(arguments, (), "leave_room")
        if self.relay is None:
            return {"ok": True, "left": False, "message": "not in a room"}
        prev_code = self.relay.code
        self.close()
        seat_id = self.seat["seat_id"] if isinstance(self.seat, dict) and self.seat.get("seat_id") in SEAT_IDS else "white"
        self.session = Session(seed=1, seat=seat_id, turn_seconds=0, human_turn_seconds=0)
        self.seat = self.session.seat
        return {"ok": True, "left": True, "code": prev_code}

    def _tool_wait_for_turn(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        _reject_unknown(arguments, ("timeout_seconds",), "wait_for_turn")
        timeout = _number(arguments.get("timeout_seconds", 15.0), "timeout_seconds", 0.1, WAIT_FOR_TURN_MAX_SECONDS)

        def check_now() -> Optional[Dict[str, Any]]:
            relay = self.relay
            if relay is not None and relay.failure is not None:
                return {"status": "error", "error": relay.failure, "state": self.session.call("get_public_state", {}, self.seat)}
            if relay is not None and getattr(relay, "pick_again", None) and not getattr(relay, "started", False):
                return {"status": "pick_again", "error": relay.pick_again, "next": "Call lock_hero with another hero: a teammate already holds that one."}
            if self.session.phase == "over":
                return {"status": "game_over", "winner": self.session.winner, "state": self.session.call("get_public_state", {}, self.seat)}
            started = True if relay is None else bool(getattr(relay, "started", False))
            if started and self.session._seat_controls_phase(self.seat):
                pub = self.session.call("get_public_state", {}, self.seat)
                active_team = self.session._active_team()
                active_unit = self.session._active_unit(active_team) if active_team else pub.get("active_unit")
                return {
                    "status": "your_turn",
                    "round": pub["round"],
                    "phase": pub["phase"],
                    "active_unit": active_unit,
                    "state": pub,
                }
            return None

        relay = self.relay
        if relay is None:
            ready = check_now()
            if ready is not None:
                return ready
            pub = self.session.call("get_public_state", {}, self.seat)
            return {"status": "waiting", "started": True, "round": pub["round"], "phase": pub["phase"], "state": pub}

        deadline = time.monotonic() + timeout
        with relay.cond:
            while True:
                ready = check_now()
                if ready is not None:
                    return ready
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    pub = self.session.call("get_public_state", {}, self.seat)
                    return {
                        "status": "waiting",
                        "started": bool(getattr(relay, "started", False)),
                        "round": pub["round"],
                        "phase": pub["phase"],
                        "state": pub,
                    }
                relay.cond.wait(min(0.25, remaining))

    def _call_room_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if name == "join_room":
                payload = self._tool_join_room(arguments)
            elif name == "lock_hero":
                payload = self._tool_lock_hero(arguments)
            elif name == "leave_room":
                payload = self._tool_leave_room(arguments)
            else:
                payload = self._tool_wait_for_turn(arguments)
            result = {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}], "isError": False}
        except ToolError as exc:
            result = {"content": [{"type": "text", "text": json.dumps({"error": str(exc)}, ensure_ascii=False)}], "isError": True}
        except Exception as exc:
            sys.stderr.write("tool failure in %s: %r\n" % (name, exc))
            result = {"content": [{"type": "text", "text": json.dumps({"error": "internal error"})}], "isError": True}
        if self.transcript is not None:
            self.transcript.record(name, arguments, result)
        return result

    def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name in ROOM_TOOL_NAMES:
            return self._call_room_tool(name, arguments)
        if isinstance(self.relay, PageJudgeRelay):
            return self._call_tool_page(name, arguments)
        try:
            if self.opponent is not None:
                self.opponent.drive(self.session)
            if name == "end_turn" and self.relay is not None:
                self.relay.wait_for_judges()   # connected play: the other device's judge decides what the own throw did, and it arrives after the landing there; ending the turn first would resolve the round on the engine's own simulation
            round_before = self.session.engine.round_num
            payload = self.session.call(name, arguments, self.seat)
            if self.relay is not None and not payload.get("duplicate"):
                if name == "submit_action":
                    self.relay.send_action(arguments)
                elif name == "end_turn":
                    self.relay.send_end_turn(arguments, round_before)
            result = {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                      "isError": False}
        except ToolError as exc:
            result = {"content": [{"type": "text", "text": json.dumps({"error": str(exc)}, ensure_ascii=False)}],
                      "isError": True}
        except Exception as exc:
            sys.stderr.write("tool failure in %s: %r\n" % (name, exc))
            result = {"content": [{"type": "text", "text": json.dumps({"error": "internal error"})}],
                      "isError": True}
        if self.transcript is not None:
            self.transcript.record(name, arguments, result)
        return result


def serve(server: McpServer, stdin: Any = None, stdout: Any = None) -> None:
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout

    def send(obj: Dict[str, Any]) -> None:
        stdout.write(json.dumps(obj) + "\n")  # ensure_ascii: one line, no raw newlines
        stdout.flush()

    while True:
        line = stdin.readline()
        if line == "":
            break
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except (ValueError, RecursionError):
            send(_rpc_error(None, -32700, "Parse error"))
            continue
        response = server.handle_message(msg)
        if response is not None:
            send(response)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Pumpkin Killer MCP server (stdio)")
    parser.add_argument("--mode", default="human_vs_agent",
                        choices=["human_vs_agent", "agent_vs_agent", "random_assignment"])
    parser.add_argument("--seed", type=int, default=None, help="for tests; default is random")
    parser.add_argument("--units", type=int, default=3,
                        help="units per side")
    parser.add_argument("--hero-red", nargs="+", choices=sorted(engine.HERO_TEMPLATES), default=None,
                        help="one hero for --units 1, otherwise exactly one hero per red unit")
    parser.add_argument("--hero-white", nargs="+", choices=sorted(engine.HERO_TEMPLATES), default=None,
                        help="one hero for --units 1, otherwise exactly one hero per white unit")
    parser.add_argument("--turn-seconds", type=float, default=TURN_SECONDS,
                        help="agent-phase timer in seconds; 0 disables it")
    parser.add_argument("--human-turn-seconds", type=float, default=TURN_SECONDS,
                        help="human-phase timer in seconds; 0 disables it")
    parser.add_argument("--memory-dir", default=os.environ.get("PK_MEMORY_DIR") or None)
    parser.add_argument("--seat", default="referee", choices=SEAT_IDS,
                        help="view and write permissions for this stdio client")
    parser.add_argument("--opponent", default=None,
                        choices=["builtin:%s" % level for level in BuiltinPracticeSeat.LEVELS],
                        help="optional in-process built-in practice opponent for the other seat")
    parser.add_argument("--transcript", default=None,
                        help="optional public-only JSONL transcript path")
    parser.add_argument("--connect", default=None,
                        help="relay WebSocket URL; disabled unless paired with --code")
    parser.add_argument("--code", default=None,
                        help="invitation code used only to join --connect")
    parser.add_argument("--auto-ready", action="store_true",
                        help="send ready after joining a relay room")
    parser.add_argument("--page-judge", default="auto", choices=["auto", "on", "off"],
                        help="room play: judge with the real page (scripts/page_judge_seat.js, needs Node 22+) instead of the engine's approximation; auto = on when Node is found")
    parser.add_argument("--page-speed", type=float, default=1.0,
                        help="page judge: fake seconds per real second; 1 is real time (use the same rate as the opposing page)")
    parser.add_argument("--room-tools", action="store_true",
                        help="expose join_room, leave_room, and wait_for_turn tools for dynamic room play")
    parser.add_argument("--relay", default=None,
                        help="default relay WebSocket URL for join_room (implies --room-tools)")
    args = parser.parse_args(argv)
    if bool(args.connect) != bool(args.code):
        parser.error("--connect and --code must be provided together")
    if args.connect and args.seat not in ("red", "white"):
        parser.error("--connect requires --seat red or --seat white")
    if args.auto_ready and not args.connect:
        parser.error("--auto-ready requires --connect")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    session = Session(mode=args.mode, seed=args.seed, turn_seconds=args.turn_seconds,
                      human_turn_seconds=args.human_turn_seconds, memory_dir=args.memory_dir,
                      seat=args.seat, units=args.units, hero_red=args.hero_red,
                      hero_white=args.hero_white)
    transcript = TranscriptWriter(args.transcript) if args.transcript else None
    enable_room_tools = bool(args.room_tools or args.relay)
    server = McpServer(
        session, transcript=transcript,
        enable_room_tools=enable_room_tools,
        default_relay_url=args.relay or args.connect,
        allow_custom_relay=True,
        page_judge_mode=args.page_judge,
        page_speed=args.page_speed,
    )
    relay = None
    if args.connect:
        node_path = shutil.which("node")
        use_page = args.page_judge == "on" or (args.page_judge == "auto" and node_path is not None and os.path.exists(os.path.join(_REPO_ROOT, "index.html")))
        if use_page:
            relay = PageJudgeRelay(session, args.connect, args.code, args.seat, speed=args.page_speed, rng=(args.seed or 1), node=node_path or "node")
        else:
            relay = ConnectedRelay(session, args.connect, args.code, args.seat,
                                   auto_ready=args.auto_ready)
        server.relay = relay
        relay.start()
    if args.opponent:
        if args.seat not in ("red", "white"):
            parser.error("--opponent requires --seat red or --seat white")
        other_seat = "white" if args.seat == "red" else "red"
        server.opponent = BuiltinPracticeSeat(session, session.seats[other_seat],
                                              args.opponent.split(":", 1)[1], transcript)
    try:
        serve(server)
    finally:
        server.close()
        if transcript is not None:
            transcript.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
