#!/usr/bin/env python3
"""Small in-memory room relay for Pumpkin Killer's trust-based matches.

The relay orders and forwards protocol messages. It never simulates a match or
interprets aim values, power, or projectile paths as game rules.
"""
import hmac
import asyncio
import json
import logging
import os
import re
import secrets
import signal
import string
import time
from http import HTTPStatus
from typing import Any, Dict, Optional

from websockets.exceptions import ConnectionClosed
from websockets.legacy.server import serve as websocket_serve

MAX_MESSAGE_BYTES = 16 * 1024
MAX_MESSAGES_PER_SECOND = 10
MAX_WRONG_CODES_PER_MINUTE = 5
MAX_TEAM_SEATS = 4
MAX_UNITS_PER_TEAM = 3
MAX_TEAM_SIZE = 3
# Capacity guards for a public URL (owner 2026-11-17: 'if the traffic is too high the resources may not be enough'). Every number is overridable by an environment variable or a RelayServer argument;
# the defaults are conservative for a small server and are replaced by numbers measured with scripts/relay_load_probe.py. docs/THREAT_MODEL_20261117.md rows T1 and T3.
# Measured 2026-11-17 (scripts/relay_load_probe.py, 100 rooms): 0.03 MB per idle room, 165 microseconds of CPU per message. The server (Contabo Tokyo: 4 cores, 7.9 GB, 5.2 GB available, load 2.6 to 3.1 because it hosts many apps)
# is not limited by the relay's memory or CPU but by open files (Linux default 1024 per process, two sockets per room): raise the two limits together, 800 connections stay under it; raise `ulimit -n` to 4096 in the service before raising them.
MAX_ROOMS = int(os.getenv("PK_RELAY_MAX_ROOMS", "200"))   # the free open test: 200 rooms (owner 2026-11-17); the relay itself would carry far more, raise it after watching the real load
MAX_CONNECTIONS = int(os.getenv("PK_RELAY_MAX_CONNECTIONS", "520"))   # two seats per room plus a few spectators, under the default open-file limit of 1024
MAX_CONNECTIONS_PER_ADDR = int(os.getenv("PK_RELAY_MAX_PER_ADDR", "8"))
MAX_SPECTATORS_PER_ROOM = int(os.getenv("PK_RELAY_MAX_SPECTATORS", "12"))
MAX_WRONG_CODES_PER_MINUTE_PER_ADDR = int(os.getenv("PK_RELAY_MAX_WRONG_PER_ADDR", "20"))
ROOM_IDLE_SECONDS = float(os.getenv("PK_RELAY_ROOM_IDLE_SECONDS", "1800"))
SEAT_GRACE_SECONDS = float(os.getenv("PK_RELAY_SEAT_GRACE_SECONDS", "60"))   # a disconnected seat is kept this long for its resume; after it the seat is removed, an empty room is deleted and the remaining seats are told (red-team R6A-3; the lazy check in resume used a hard-coded 60)
GATEWAY_TOKEN = os.getenv("PK_RELAY_GATEWAY_TOKEN", "")   # MCP-RISK-A: the hosted MCP gateway proves itself with this one-time random token and then names the real client address; empty = feature off
TRUST_PROXY = os.getenv("PK_RELAY_TRUST_PROXY", "") == "1"   # behind the Cloudflare tunnel the peer address is the tunnel: take CF-Connecting-IP instead
SIDE_OF_TEAM = {"red": "left", "white": "right"}
WORLD_UNIT = re.compile(r"^(left|right)_([0-2])$")
ROUND_HASH_FORMAT = re.compile(r"^[0-9a-f]{8}$")
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
RULES_VERSION = "relay-v0"
LOG = logging.getLogger("pk_relay")


def make_code() -> str:
    """Return a short invitation code without visually ambiguous characters."""
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(6))


def json_bytes(message: Dict[str, Any]) -> str:
    return json.dumps(message, separators=(",", ":"), ensure_ascii=False)


VALID_SCENES = ("graveyard", "church", "school", "belltower")


class Room:
    def __init__(self, code: str, *, solo: bool = False, scene: str = "graveyard",
                 host_side_choice: Optional[str] = None, team_size: int = 1) -> None:
        self.code = code
        self.solo = solo
        self.scene = scene
        # Units per side, 1 to 3. One means the one-versus-one wire, unchanged since relay-v0.
        self.team_size = team_size
        self.owners: Dict[str, str] = {}
        self.host_side_choice = host_side_choice
        self.host_seat_id: Optional[str] = None
        self.host_side_coin: Optional[int] = None
        self.resolved_host_side: Optional[str] = None
        # Sessions survive a transient socket loss for the 60 s reconnect window.
        self.clients: Dict[Any, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.log: list = []
        self.next_seq = 1
        self.started = False
        self.seed: Optional[int] = None
        self.first_team: Optional[str] = None
        self.round = 1
        self.phase: Optional[str] = None
        self.actions: Dict[int, Dict[str, Any]] = {}
        self.action_by_turn: set = set()
        self.turn_unit: Dict[tuple, str] = {}
        self.judged: set = set()
        self.round_hashes: Dict[int, Dict[str, str]] = {}
        self.reported_mismatches: set = set()

    def stamp(self, message: Dict[str, Any], *, keep: bool = True) -> Dict[str, Any]:
        message = dict(message)
        message["seq"] = self.next_seq
        self.next_seq += 1
        if keep:
            self.log.append(dict(message))
        return message

    def seats(self) -> list:
        return [
            {"seat_id": entry["seat_id"], "team": entry["team"], "ready": entry["ready"],
             "units": entry["units"]}
            for entry in sorted(self.sessions.values(), key=lambda item: item["seat_id"])
        ]

    def state(self, include_code: bool = False) -> Dict[str, Any]:
        message: Dict[str, Any] = {
            "type": "room_state",
            "seats": self.seats(),
            "rules_version": RULES_VERSION,
            "started": self.started,
        }
        if include_code:
            message["code"] = self.code
        if self.team_size > 1:
            message["team_size"] = self.team_size
        if self.started:
            message.update({"seed": self.seed, "round": self.round,
                            "phase": self.phase, "first_team": self.first_team})
        return message

    def team_count(self, team: str) -> int:
        return sum(1 for entry in self.sessions.values() if entry["team"] == team)

    @property
    def team_match(self) -> bool:
        return self.team_size > 1

    def team_seats(self, team: str) -> list:
        """Player seats of one team in join order (red-1, red-2, ...)."""
        seats = [entry for entry in self.sessions.values() if entry["team"] == team]
        return sorted(seats, key=lambda entry: int(entry["seat_id"].rsplit("-", 1)[1]))

    def assign_units(self) -> Dict[str, Any]:
        """Hero list per side and unit owners, computed once when the match starts (team matches only).

        One player seat on a team controls every unit of it. Several seats split the unit ids in seat
        order by the length of their own unit lists, but only when every seat sent a list and the lengths
        add up to the team size; otherwise the owners of that team stay unknown and any of its seats may
        act for any of its units (trust-based, like the rest of the relay)."""
        heroes: Dict[str, list] = {}
        owners: Dict[str, str] = {}
        for team, side in SIDE_OF_TEAM.items():
            seats = self.team_seats(team)
            listed = [hero for seat in seats for hero in seat["units"]][:self.team_size]
            heroes[side] = listed + [None] * (self.team_size - len(listed))
            if len(seats) == 1:
                owners.update({"%s_%d" % (side, index): seats[0]["seat_id"] for index in range(self.team_size)})
            elif seats and all(seat["units"] for seat in seats) and sum(len(seat["units"]) for seat in seats) == self.team_size:
                index = 0
                for seat in seats:
                    for _ in seat["units"]:
                        owners["%s_%d" % (side, index)] = seat["seat_id"]
                        index += 1
        self.owners = owners
        return {"heroes": heroes, "owners": owners}

    def all_players_ready(self) -> bool:
        players = [entry for entry in self.sessions.values() if entry["team"] in ("red", "white")]
        if not players or not all(entry["ready"] for entry in players):
            return False
        return self.solo or {entry["team"] for entry in players} == {"red", "white"}


class RelayServer:
    """A single-process room relay that retains state only while clients connect."""
    def __init__(self, host: str = "127.0.0.1", port: int = 8765,
                 origin_allowlist: Optional[str] = None, **limits: Any) -> None:
        self.host = host
        self.port = int(port)
        self.max_rooms = int(limits.get("max_rooms", MAX_ROOMS))
        self.max_connections = int(limits.get("max_connections", MAX_CONNECTIONS))
        self.max_per_addr = int(limits.get("max_per_addr", MAX_CONNECTIONS_PER_ADDR))
        self.max_spectators = int(limits.get("max_spectators", MAX_SPECTATORS_PER_ROOM))
        self.max_wrong_per_addr = int(limits.get("max_wrong_per_addr", MAX_WRONG_CODES_PER_MINUTE_PER_ADDR))
        self.room_idle_seconds = float(limits.get("room_idle_seconds", ROOM_IDLE_SECONDS))
        self.seat_grace_seconds = float(limits.get("seat_grace_seconds", SEAT_GRACE_SECONDS))
        self.trust_proxy = bool(limits.get("trust_proxy", TRUST_PROXY))
        self.gateway_token = str(limits.get("gateway_token", GATEWAY_TOKEN) or "")
        self.connections = 0
        self.connections_by_addr: Dict[str, int] = {}
        self.wrong_by_addr: Dict[str, list] = {}
        self.last_seen: Dict[str, float] = {}   # room code -> last message time (monotonic)
        self._reaper: Any = None
        configured = origin_allowlist if origin_allowlist is not None else os.getenv("PK_RELAY_ORIGINS", "")
        self.origins = {value.strip().rstrip("/") for value in configured.split(",") if value.strip()}
        self.rooms: Dict[str, Room] = {}
        self._server: Any = None

    @property
    def bound_port(self) -> int:
        if self._server is None:
            return self.port
        return int(self._server.sockets[0].getsockname()[1])

    async def start(self) -> None:
        self._server = await websocket_serve(
            self._handle_socket, self.host, self.port, max_size=MAX_MESSAGE_BYTES,
            process_request=self._process_request,
        )
        if self.room_idle_seconds > 0 or self.seat_grace_seconds > 0:
            self._reaper = asyncio.ensure_future(self._reap_idle_rooms())

    async def _reap_idle_rooms(self) -> None:
        """Close the sockets of rooms that have been silent for room_idle_seconds, so an idle room cannot hold memory for ever."""
        periods = [value for value in (self.room_idle_seconds, self.seat_grace_seconds) if value > 0]
        interval = max(0.05, min(60.0, min(periods) / 4.0))
        while True:
            await asyncio.sleep(interval)
            now = time.monotonic()
            await self._sweep_disconnected_seats(now)
            for code, room in list(self.rooms.items()):
                if self.room_idle_seconds > 0 and now - self.last_seen.get(code, now) >= self.room_idle_seconds:
                    for websocket in list(room.clients):
                        try:
                            await websocket.close(code=1001, reason="room idle")
                        except Exception:  # noqa: BLE001 - a socket that is already gone is fine
                            pass

    async def _expire_seat(self, room: Room, token: str) -> None:
        """One way to end a seat that stayed away past the grace period, shared by the sweep and the lazy check in `resume` (red-team R7A-1): the seat is removed, an empty
        room is deleted, the seats still in the room get a sequenced `seat_left` and the new room state."""
        entry = room.sessions.pop(token, None)
        if entry is None:
            return
        if not room.sessions:
            self.rooms.pop(room.code, None)
            self.last_seen.pop(room.code, None)
            return
        await self._broadcast(room, {"type": "seat_left", "seat_id": entry["seat_id"], "team": entry["team"], "reason": "disconnect_timeout"})
        await self._broadcast_state(room)
        await self._start_if_ready(room)   # red-team R1 B3: a seat that held the start back (a killed placeholder) may have been the only one not ready

    async def _sweep_disconnected_seats(self, now: float) -> None:
        """Expire seats that stayed disconnected longer than the grace period (the MOBA / card-game rule: the seat is held for a while, then the player has left)."""
        if self.seat_grace_seconds <= 0:
            return
        for room in list(self.rooms.values()):
            for token, entry in list(room.sessions.items()):
                if not entry.get("connected") and now - entry.get("disconnected_at", now) >= self.seat_grace_seconds:
                    await self._expire_seat(room, token)

    def _addr(self, websocket: Any) -> str:
        """The client address used for the per-address limits: CF-Connecting-IP when the relay sits behind the trusted tunnel, else the peer address."""
        if self.gateway_token:
            try:   # MCP-RISK-A: a seat opened by the hosted MCP gateway is counted under the remote client it serves, not under 127.0.0.1
                gw_headers = getattr(getattr(websocket, "request", None), "headers", None) or getattr(websocket, "request_headers", None)
                token = gw_headers.get("X-PK-Gateway-Token") if gw_headers is not None else None
                client = gw_headers.get("X-PK-Client-Addr") if gw_headers is not None else None
                if token and client and hmac.compare_digest(str(token).encode("utf-8"), self.gateway_token.encode("utf-8")):
                    return "mcp:" + str(client).strip()[:64]
            except Exception:  # noqa: BLE001
                pass
        if self.trust_proxy:
            try:
                headers = getattr(getattr(websocket, "request", None), "headers", None) or getattr(websocket, "request_headers", None)
                value = headers.get("CF-Connecting-IP") if headers is not None else None
                if value:
                    return str(value).strip()[:64]
            except Exception:  # noqa: BLE001
                pass
        peer = getattr(websocket, "remote_address", None)
        return str(peer[0]) if peer else "unknown"

    async def close(self) -> None:
        if self._reaper is not None:
            self._reaper.cancel()
            self._reaper = None
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        self.rooms.clear()

    async def _process_request(self, path: str, headers: Any) -> Optional[tuple]:
        upgrade = headers.get("Upgrade", "").lower()
        if upgrade != "websocket":
            if path == "/health":
                return (HTTPStatus.OK, [("Content-Type", "text/plain; charset=utf-8")], b"ok\n")
            return (HTTPStatus.NOT_FOUND, [("Content-Type", "text/plain; charset=utf-8")], b"not found\n")
        if path != "/ws":
            return (HTTPStatus.NOT_FOUND, [("Content-Type", "text/plain; charset=utf-8")], b"not found\n")
        origin = headers.get("Origin")
        if not self._origin_allowed(origin):
            return (HTTPStatus.FORBIDDEN, [("Content-Type", "text/plain; charset=utf-8")], b"origin denied\n")
        return None

    def _origin_allowed(self, origin: Optional[str]) -> bool:
        # Non-browser local clients omit Origin. Browsers must be loopback by default.
        if origin is None:
            return True
        normalized = origin.rstrip("/")
        if self.origins:
            return normalized in self.origins
        return normalized.startswith("http://localhost") or normalized.startswith("http://127.0.0.1")

    async def _send(self, websocket: Any, message: Dict[str, Any]) -> None:
        try:
            await websocket.send(json_bytes(message))
        except ConnectionClosed:
            pass

    async def _error(self, websocket: Any, code: str, message: Optional[str] = None) -> None:
        LOG.warning("relay error code=%s", code)
        payload = {"type": "error", "code": code}
        if message is not None:
            payload["message"] = message
        await self._send(websocket, payload)

    async def _broadcast(self, room: Room, message: Dict[str, Any], *, exclude: Any = None,
                         include: Any = None) -> None:
        stamped = room.stamp(message)
        targets = room.clients.keys() if include is None else include
        await asyncio.gather(*[
            self._send(client, stamped) for client in list(targets)
            if client is not exclude
        ], return_exceptions=True)

    async def _send_state(self, room: Room, websocket: Any, entry: Dict[str, Any],
                          include_code: bool = False) -> None:
        # Bootstrap is private and deliberately unsequenced: a global sequence may
        # only be used for messages every connected seat receives.
        message = room.state(include_code=include_code)
        message.update({"seat": entry["team"], "seat_id": entry["seat_id"],
                        "seat_token": entry["seat_token"], "last_seq": room.next_seq - 1})
        await self._send(websocket, message)

    async def _replay(self, room: Room, websocket: Any, last_seq: int) -> None:
        for message in room.log:
            if message["seq"] > last_seq:
                await self._send(websocket, message)

    async def _broadcast_state(self, room: Room) -> None:
        await self._broadcast(room, room.state())

    def _allocate_seat(self, room: Room, team: str) -> str:
        prefix = "spectator" if team == "spectator" else team
        used = {entry["seat_id"] for entry in room.sessions.values()}
        index = 1
        while f"{prefix}-{index}" in used:
            index += 1
        return f"{prefix}-{index}"

    @staticmethod
    def _parse_solo(value: Any) -> bool:
        if not isinstance(value, bool):
            raise ValueError("invalid_solo")
        return value

    @staticmethod
    def _parse_scene(value: Any) -> str:
        if value not in VALID_SCENES:
            raise ValueError("invalid_scene")
        return value

    @staticmethod
    def _parse_host_side_choice(value: Any) -> Optional[str]:
        """Accept only the three host options; invalid optional values are ignored."""
        return value if value in ("left", "right", "computer") else None

    @staticmethod
    def _parse_team_size(value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_TEAM_SIZE:
            raise ValueError("invalid_team_size")
        return value

    @staticmethod
    def _resolve_host_side(room: Room) -> Optional[str]:
        if room.host_side_choice in ("left", "right"):
            room.resolved_host_side = room.host_side_choice
            return room.resolved_host_side
        if room.host_side_choice == "computer":
            room.host_side_coin = secrets.randbits(31)
            room.resolved_host_side = "right" if room.host_side_coin & 1 else "left"
            return room.resolved_host_side
        return None

    def _parse_units(self, value: Any) -> list:
        if value is None:
            return []
        if not isinstance(value, list) or len(value) > MAX_UNITS_PER_TEAM or any(not isinstance(unit, str) or not unit for unit in value):
            raise ValueError
        return list(value)

    @staticmethod
    def _check_team_units(room: Room, entry: Dict[str, Any], units: list) -> None:
        """Team matches only: a seat may not list more units than the team has room for."""
        if not room.team_match:
            return
        others = sum(len(seat["units"]) for seat in room.team_seats(entry["team"]) if seat is not entry)
        if len(units) + others > room.team_size:
            raise ValueError("too_many_units")

    async def _handle_socket(self, websocket: Any, path: Optional[str] = None) -> None:
        room: Optional[Room] = None
        entry: Optional[Dict[str, Any]] = None
        timestamps: list = []
        wrong_code_times: list = []
        addr = self._addr(websocket)
        if self.connections >= self.max_connections or self.connections_by_addr.get(addr, 0) >= self.max_per_addr:
            await self._error(websocket, "server_busy")
            await websocket.close(code=1013, reason="server busy")
            return
        self.connections += 1
        self.connections_by_addr[addr] = self.connections_by_addr.get(addr, 0) + 1
        try:
            async for raw in websocket:
                if not isinstance(raw, str):
                    await self._error(websocket, "text_frame_required")
                    continue
                if len(raw.encode("utf-8")) > MAX_MESSAGE_BYTES:
                    await self._error(websocket, "message_too_large")
                    continue
                now = time.monotonic()
                timestamps[:] = [value for value in timestamps if now - value < 1.0]
                if len(timestamps) >= MAX_MESSAGES_PER_SECOND:
                    await self._error(websocket, "rate_limited")
                    continue
                timestamps.append(now)
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    await self._error(websocket, "invalid_json")
                    continue
                if not isinstance(message, dict) or not isinstance(message.get("type"), str):
                    await self._error(websocket, "invalid_message")
                    continue
                room, entry = await self._dispatch(websocket, room, entry, message, wrong_code_times)
                if room is not None:
                    self.last_seen[room.code] = now
        except ConnectionClosed:
            pass
        finally:
            self.connections -= 1
            left = self.connections_by_addr.get(addr, 1) - 1
            if left > 0:
                self.connections_by_addr[addr] = left
            else:
                self.connections_by_addr.pop(addr, None)
            if room is not None and websocket in room.clients:
                await self._remove_client(room, websocket)

    async def _dispatch(self, websocket: Any, room: Optional[Room], entry: Optional[Dict[str, Any]],
                        message: Dict[str, Any], wrong_code_times: list) -> tuple:
        message_type = message["type"]
        if message_type == "resume":
            if room is not None:
                await self._error(websocket, "already_joined")
                return room, entry
            token = message.get("seat_token")
            last_seq = message.get("last_seq")
            if not isinstance(token, str) or not isinstance(last_seq, int) or isinstance(last_seq, bool) or last_seq < 0:
                await self._error(websocket, "invalid_resume")
                return None, None
            for candidate in self.rooms.values():
                restored = candidate.sessions.get(token)
                if restored is None:
                    continue
                if restored.get("connected"):
                    await self._error(websocket, "seat_in_use")
                    return None, None
                if time.monotonic() - restored.get("disconnected_at", time.monotonic()) > (self.seat_grace_seconds if self.seat_grace_seconds > 0 else SEAT_GRACE_SECONDS):
                    await self._expire_seat(candidate, token)
                    await self._error(websocket, "resume_expired")
                    return None, None
                if last_seq > candidate.next_seq - 1:
                    await self._error(websocket, "invalid_resume")
                    return None, None
                room, entry = candidate, restored
                entry["connected"] = True
                entry.pop("disconnected_at", None)
                room.clients[websocket] = entry
                await self._send_state(room, websocket, entry, include_code=True)
                await self._replay(room, websocket, last_seq)
                await self._broadcast_state(room)
                return room, entry
            await self._error(websocket, "unknown_token")
            return None, None
        if message_type == "create_room":
            if room is not None:
                await self._error(websocket, "already_joined")
                return room, entry
            if len(self.rooms) >= self.max_rooms:
                await self._error(websocket, "server_busy")
                return room, entry
            try:
                solo = self._parse_solo(message.get("solo", False))
                scene = self._parse_scene(message.get("scene", "graveyard"))
                team_size = self._parse_team_size(message.get("team_size", 1))
            except ValueError as exc:
                await self._error(websocket, str(exc))
                return room, entry
            room = Room(self._new_code(), solo=solo, scene=scene, team_size=team_size,
                        host_side_choice=self._parse_host_side_choice(message.get("host_side_choice")))
            self.rooms[room.code] = room
            entry = await self._join(room, websocket, message)
            if entry is None:
                self.rooms.pop(room.code, None)
                return None, None
            room.host_seat_id = entry["seat_id"]
            await self._send_state(room, websocket, entry, include_code=True)
            return room, entry
        if message_type == "join":
            if room is not None:
                await self._error(websocket, "already_joined")
                return room, entry
            code = message.get("code")
            if isinstance(code, str):
                code = code.strip().upper()
            now = time.monotonic()
            wrong_code_times[:] = [value for value in wrong_code_times if now - value < 60]
            addr_times = self.wrong_by_addr.setdefault(self._addr(websocket), [])   # the same limit per client address, so opening many connections does not bypass it
            addr_times[:] = [value for value in addr_times if now - value < 60]
            if len(addr_times) > self.max_wrong_per_addr:
                await self._error(websocket, "rate_limited")
                return room, entry
            if not isinstance(code, str) or code not in self.rooms:
                wrong_code_times.append(now)
                addr_times.append(now)
                if len(wrong_code_times) > MAX_WRONG_CODES_PER_MINUTE:
                    await self._error(websocket, "rate_limited")
                else:
                    await self._error(websocket, "unknown_code")
                return room, entry
            room = self.rooms[code]
            entry = await self._join(room, websocket, message)
            if entry is not None:
                await self._send_state(room, websocket, entry, include_code=True)
                await self._replay(room, websocket, 0)
                await self._broadcast_state(room)
                return room, entry
            return None, None
        if room is None or entry is None:
            await self._error(websocket, "join_required")
            return room, entry
        if message_type == "ready":
            if not room.started:
                # Optional team-battle fields, honoured only before the match starts. The host may set the
                # team size; a seat may replace its unit list. A bad value is an explicit error and the
                # seat does not become ready, so a mistake can never start a different match.
                if entry["seat_id"] == room.host_seat_id and "team_size" in message:
                    try:
                        room.team_size = self._parse_team_size(message["team_size"])
                    except ValueError as exc:
                        await self._error(websocket, str(exc), "team_size must be an integer from 1 to 3")
                        return room, entry
                if "units" in message and entry["team"] != "spectator":
                    try:
                        units = self._parse_units(message["units"])
                        self._check_team_units(room, entry, units)
                    except ValueError:
                        await self._error(websocket, "invalid_units")
                        return room, entry
                    entry["units"] = units
            if entry["seat_id"] == room.host_seat_id and "host_side_choice" in message:
                choice = self._parse_host_side_choice(message["host_side_choice"])
                if choice is not None:
                    room.host_side_choice = choice
            entry["ready"] = True
            await self._broadcast_state(room)
            await self._start_if_ready(room)
            return room, entry
        if message_type == "action":
            await self._action(room, websocket, entry, message)
            return room, entry
        if message_type == "judge":
            await self._judge(room, websocket, entry, message)
            return room, entry
        if message_type == "end_turn":
            await self._end_turn(room, websocket, entry, message)
            return room, entry
        if message_type == "round_hash":
            await self._round_hash(room, websocket, entry, message)
            return room, entry
        if message_type in ("leave", "timeout"):
            await self._remove_client(room, websocket, release=True)
            return None, None
        await self._error(websocket, "unknown_type")
        return room, entry

    def _new_code(self) -> str:
        code = make_code()
        while code in self.rooms:
            code = make_code()
        return code

    async def _join(self, room: Room, websocket: Any, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        team = message.get("seat")
        if team not in ("red", "white", "spectator"):
            await self._error(websocket, "invalid_seat")
            return None
        if team != "spectator" and room.started:
            # LATE-JOIN-1: a player seat created after the start never receives `start` and cannot take part. Refuse it with a clear code;
            # `resume` of an existing seat and spectators are unchanged.
            await self._error(websocket, "room_started", "the match has already started; ask the host for a new room")
            return None
        if team != "spectator" and room.team_count(team) >= MAX_TEAM_SEATS:
            await self._error(websocket, "team_full")
            return None
        if team == "spectator" and sum(1 for seat in room.sessions.values() if seat.get("team") == "spectator") >= self.max_spectators:
            await self._error(websocket, "room_full")
            return None
        try:
            units = self._parse_units(message.get("units"))
            if team != "spectator" and room.team_match and len(units) > room.team_size:
                raise ValueError
        except ValueError:
            await self._error(websocket, "invalid_units")
            return None
        entry = {"seat_id": self._allocate_seat(room, team), "team": team, "units": units,
                 "ready": False, "client_version": message.get("client_version", ""),
                 "seat_token": secrets.token_urlsafe(24), "connected": True}
        room.sessions[entry["seat_token"]] = entry
        room.clients[websocket] = entry
        return entry

    def _valid_turn(self, room: Room, entry: Dict[str, Any], message: Dict[str, Any]) -> bool:
        return (room.started and entry["team"] in ("red", "white") and
                message.get("round") == room.round and message.get("phase") == room.phase and
                entry["team"] == room.phase)

    @staticmethod
    def _valid_action_integer(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 6

    @staticmethod
    def _team_unit_error(room: Room, entry: Dict[str, Any], unit: Any, team: str) -> Optional[str]:
        """Team matches only. A unit id is a world id, left_0..left_2 or right_0..right_2, below the team size,
        on the side of the team that owns it (red is left, white is right), and, when the start message named
        the owners, owned by that seat. The relay cannot cheaply know whose turn it is or who is alive (the
        rotation rule is the devices' business and a fallen unit is the judge's report), so it checks no more."""
        match = WORLD_UNIT.match(unit) if isinstance(unit, str) else None
        if match is None or int(match.group(2)) >= room.team_size:
            return "invalid_unit"
        if match.group(1) != SIDE_OF_TEAM.get(team):
            return "unit_not_yours"
        owner = room.owners.get(unit)
        if owner is not None and owner != entry["seat_id"]:
            return "unit_not_yours"
        return None

    async def _action(self, room: Room, websocket: Any, entry: Dict[str, Any], message: Dict[str, Any]) -> None:
        if not self._valid_turn(room, entry, message):
            await self._error(websocket, "stale_or_out_of_turn")
            return
        if not isinstance(message.get("unit"), str) or message.get("kind") not in ("throw", "move", "defend", "ultimate"):
            await self._error(websocket, "invalid_action")
            return
        if room.team_match:
            unit_error = self._team_unit_error(room, entry, message["unit"], entry["team"])
            if unit_error is not None:
                await self._error(websocket, unit_error, "unit must be %s_0 to %s_%d for this seat" % (
                    SIDE_OF_TEAM[entry["team"]], SIDE_OF_TEAM[entry["team"]], room.team_size - 1))
                return
        for field in ("die", "bounce"):
            if field in message and not self._valid_action_integer(message[field]):
                await self._error(websocket, "invalid_%s" % field,
                                  "%s must be an integer from 1 to 6" % field)
                return
        category = "move" if message["kind"] == "move" else "attack"
        turn_key = (entry["seat_id"], room.round, room.phase, category)
        if turn_key in room.action_by_turn:
            await self._error(websocket, "action_already_submitted")
            return
        if room.team_match:
            # One active unit per team: its move and its attack in one turn come from the same unit.
            unit_key = (entry["seat_id"], room.round, room.phase)
            if room.turn_unit.setdefault(unit_key, message["unit"]) != message["unit"]:
                await self._error(websocket, "unit_changed_in_turn")
                return
        room.action_by_turn.add(turn_key)
        # The relay forwards a small allowlist only. Receivers recompute flight paths.
        outbound = {key: message[key] for key in ("type", "round", "phase", "unit", "kind", "angle", "power", "start", "claimed_landing", "dirX", "target", "die", "bounce") if key in message}
        outbound["seat_id"] = entry["seat_id"]
        stamped = room.stamp(outbound)
        room.actions[stamped["seq"]] = {"sender": websocket, "team": entry["team"]}
        await asyncio.gather(*[
            self._send(client, stamped) for client in list(room.clients)
        ], return_exceptions=True)
        await self._send(websocket, {"type": "action_ack", "seq": stamped["seq"], "round": stamped.get("round"), "phase": stamped.get("phase")})   # the sender learns the stamp, so it can match the judge reply

    async def _judge(self, room: Room, websocket: Any, entry: Dict[str, Any], message: Dict[str, Any]) -> None:
        ref = message.get("ref")
        action = room.actions.get(ref) if isinstance(ref, int) else None
        if not room.started or entry["team"] not in ("red", "white") or action is None or action["team"] == entry["team"]:
            await self._error(websocket, "invalid_judge")
            return
        if room.team_match:
            # Every unit owner judges its own unit; an attack may hit several units, one judge each, never twice.
            if message.get("hit") is True and "unit" not in message:
                await self._error(websocket, "invalid_unit", "a hit names the unit that was hit")
                return
            if "unit" in message:
                unit_error = self._team_unit_error(room, entry, message["unit"], entry["team"])
                if unit_error is not None:
                    await self._error(websocket, unit_error, "the judge names one of its own units")
                    return
            judged_key = (ref, message.get("unit"))
            if judged_key in room.judged:
                await self._error(websocket, "duplicate_judge")
                return
            room.judged.add(judged_key)
        outbound = {key: message[key] for key in ("type", "ref", "hit", "unit", "damage", "hp_after", "statuses", "knockback") if key in message}
        outbound["seat_id"] = entry["seat_id"]
        await self._broadcast(room, outbound)

    async def _end_turn(self, room: Room, websocket: Any, entry: Dict[str, Any], message: Dict[str, Any]) -> None:
        if not self._valid_turn(room, entry, message):
            await self._error(websocket, "stale_or_out_of_turn")
            return
        ended_phase = room.phase

        def first_of(round_number: int) -> str:
            """The team that acts first in a round: the room's first team in every round (owner 2026-11-17: no alternation, so no team attacks twice in a row)."""
            return room.first_team or "red"

        if ended_phase == first_of(room.round):
            room.phase = "white" if ended_phase == "red" else "red"   # the second team of the SAME round
        else:
            room.round += 1                                           # the second team ended: the next round starts with its first team
            room.phase = first_of(room.round)
        await self._broadcast(room, {"type": "end_turn", "round": message["round"], "phase": ended_phase,
                                     "next_round": room.round, "next_phase": room.phase,
                                     "seat_id": entry["seat_id"]})

    async def _round_hash(self, room: Room, websocket: Any, entry: Dict[str, Any], message: Dict[str, Any]) -> None:
        round_number = message.get("round")
        digest = message.get("hash")
        if not room.started or not isinstance(round_number, int) or not isinstance(digest, str) or not digest:
            await self._error(websocket, "invalid_round_hash")
            return
        if room.team_match and not ROUND_HASH_FORMAT.match(digest):
            await self._error(websocket, "invalid_round_hash", "hash must be 8 lowercase hex characters")
            return
        hashes = room.round_hashes.setdefault(round_number, {})
        hashes[entry["seat_id"]] = digest
        await self._broadcast(room, {"type": "round_hash", "round": round_number,
                                     "seat_id": entry["seat_id"]})
        distinct = set(hashes.values())
        mismatch_key = (round_number, tuple(sorted(hashes)))
        if len(distinct) > 1 and mismatch_key not in room.reported_mismatches:
            room.reported_mismatches.add(mismatch_key)
            await self._broadcast(room, {"type": "out_of_sync", "round": round_number})

    async def _start_if_ready(self, room: Room) -> None:
        """Start the match when every player seat is ready and both teams are present. Called after a `ready` and after a seat leaves before the start (a seat that held the start back may be the last one not ready)."""
        if not room.started and room.all_players_ready():
            room.started = True
            # JSON peers include the browser, whose exact integer range ends at 2**53 - 1.
            # Match seeds also reserve zero as "unset" in the rules engine.
            room.seed = secrets.randbits(31) or 1
            room.first_team = "red"
            room.round = 1
            room.phase = room.first_team
            resolved_host_side = self._resolve_host_side(room)
            start = {"type": "start", "seed": room.seed, "scene": room.scene,
                     "first_team": room.first_team, "round": room.round, "phase": room.phase}
            if room.team_match:
                # Absent keys mean one unit per side (relay-v0). Heroes are listed per world side:
                # red is left, white is right; null marks a slot nobody named.
                assigned = room.assign_units()
                start.update({"team_size": room.team_size, "heroes": assigned["heroes"],
                              "owners": assigned["owners"]})
            if resolved_host_side is not None:
                start["host_side_choice"] = resolved_host_side
            await self._broadcast(room, start)

    async def _remove_client(self, room: Room, websocket: Any, *, release: bool = False) -> None:
        entry = room.clients.pop(websocket, None)
        if entry is None:
            return
        entry["connected"] = False
        entry["disconnected_at"] = time.monotonic()
        if release:
            room.sessions.pop(entry["seat_token"], None)
        if not room.sessions:
            self.rooms.pop(room.code, None)
            return
        if room.clients:
            await self._broadcast_state(room)
            if release:
                await self._start_if_ready(room)   # a seat that leaves before the start may have been the only one not ready


async def _run() -> None:
    logging.basicConfig(level=os.getenv("PK_RELAY_LOG_LEVEL", "WARNING"))
    relay = RelayServer(os.getenv("HOST", "127.0.0.1"), int(os.getenv("PORT", "8765")))
    await relay.start()
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    await stop.wait()
    await relay.close()


if __name__ == "__main__":
    asyncio.run(_run())
