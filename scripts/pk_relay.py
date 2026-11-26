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
import unicodedata
from http import HTTPStatus
from typing import Any, Dict, Optional

from websockets.exceptions import ConnectionClosed
from websockets.legacy.server import serve as websocket_serve

def _env_number(name: str, default: Any, cast: Any = int) -> Any:
    """Read a number from the environment. A typo or a negative value in a deploy variable must not crash the relay at start-up (a crash loop takes the page down):
    the default is used and one warning line says so (FLOOD-1 fool-proofing, 2026-11-25)."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return cast(default)
    try:
        value = cast(raw.strip())
        if value != value or value < 0:   # NaN or negative
            raise ValueError(raw)
        return value
    except (ValueError, OverflowError):
        logging.warning("relay: ignoring %s=%r (not a non-negative number); using %s", name, raw, default)
        return cast(default)


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
MAX_ROOMS = max(1, _env_number("PK_RELAY_MAX_ROOMS", 200))   # the free open test: 200 rooms (owner 2026-11-17); the relay itself would carry far more, raise it after watching the real load
MAX_CONNECTIONS = max(1, _env_number("PK_RELAY_MAX_CONNECTIONS", 520))   # two seats per room plus a few spectators, under the default open-file limit of 1024
MAX_CONNECTIONS_PER_ADDR = max(1, _env_number("PK_RELAY_MAX_PER_ADDR", 8))
MAX_ROOMS_PER_ADDR = max(1, _env_number("PK_RELAY_MAX_ROOMS_PER_ADDR", 8))   # red team A11: one address could hold every room slot with dropped sockets
UNIT_ID = re.compile(r"^[a-z][a-z0-9_]{0,23}$")   # red team A4/A14: a hero id is a short lowercase word; the pages look it up safely
MAX_SPECTATORS_PER_ROOM = _env_number("PK_RELAY_MAX_SPECTATORS", 12)
MAX_WRONG_CODES_PER_MINUTE_PER_ADDR = _env_number("PK_RELAY_MAX_WRONG_PER_ADDR", 20)
ROOM_IDLE_SECONDS = _env_number("PK_RELAY_ROOM_IDLE_SECONDS", 1800, float)
SEAT_GRACE_SECONDS = _env_number("PK_RELAY_SEAT_GRACE_SECONDS", 60, float)   # a disconnected seat is kept this long for its resume; after it the seat is removed, an empty room is deleted and the remaining seats are told (red-team R6A-3; the lazy check in resume used a hard-coded 60)
GATEWAY_TOKEN = os.getenv("PK_RELAY_GATEWAY_TOKEN", "")   # MCP-RISK-A: the hosted MCP gateway proves itself with this one-time random token and then names the real client address; empty = feature off
TRUST_PROXY = os.getenv("PK_RELAY_TRUST_PROXY", "") == "1"   # behind the Cloudflare tunnel the peer address is the tunnel: take CF-Connecting-IP instead
# FLOOD-1 (2026-11-25): reconnect storms. The per-address cap above counts OPEN connections only; these count attempts, so a client that connects and drops in a loop,
# or sends wrong `resume` tokens in a loop, is blocked for a while (answered at once with `temporarily_blocked`, no state kept). Repeat offenders wait twice as long each time.
MAX_CONNECTS_PER_MIN = _env_number("PK_RELAY_MAX_CONNECTS_PER_MIN", 40)
MAX_BAD_RESUMES_PER_MIN = _env_number("PK_RELAY_MAX_BAD_RESUMES_PER_MIN", 10)
BLOCK_SECONDS = _env_number("PK_RELAY_BLOCK_SECONDS", 300, float)
MAX_BLOCK_SECONDS = 3600.0
MAX_TRACKED_ADDRS = _env_number("PK_RELAY_MAX_TRACKED_ADDRS", 4096)
UNTRACKED_ADDRS = {"", "unknown", "127.0.0.1", "::1"}   # no real client address (a loopback peer is nginx or a local test): never blocked, the open-connection cap still applies
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


# ROOM-FLOW R11: a player invites an agent into their own team.
INVITE_SECONDS = 600.0               # an unused ticket is dropped after this
AGENT_PICK_SECONDS = 30.0            # an agent that has not readied by then is given a free hero and locked
INVITE_NOTE_LENGTH = 80
HERO_IDS = ("skeleton", "wizard", "bat", "knight", "bride", "hunchback", "reaper", "hag")
AGENT_TURN_SECONDS = 12
COUNTDOWN_SECONDS = 3.0              # ROOM-FLOW R12: a lobby room starts this long after the last condition is met

# ROOM-FLOW R7: seat names. The same rule as RelayClient.cleanName (js/relay_client.js); scripts/name_vectors.json pins both.
NAME_WIDTH = 10                      # display units: a CJK or full-width character is 2, anything else 1
NAME_INPUT = 64                      # code points looked at
EMOJI_RANGES = ((0x1F000, 0x1FAFF), (0x2600, 0x27BF), (0x2B00, 0x2BFF), (0x2300, 0x23FF))
WIDE_RANGES = ((0x1100, 0x115F), (0x2E80, 0x303E), (0x3041, 0x33FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xA000, 0xA4CF), (0xA960, 0xA97F),
               (0xAC00, 0xD7A3), (0xF900, 0xFAFF), (0xFE10, 0xFE19), (0xFE30, 0xFE6F), (0xFF00, 0xFF60), (0xFFE0, 0xFFE6), (0x20000, 0x2FFFD), (0x30000, 0x3FFFD))
BLANK_LETTERS = (0x115F, 0x1160, 0x2800, 0x3164, 0xFFA0)   # drawn as nothing: an invisible name


def clean_name(value: Any) -> str:
    """NFC; no control, format (zero width, bidi), private, unassigned, combining or blank characters; one space between words; at most
    NAME_WIDTH display units of text plus one emoji (with its skin tone or presentation selector, or a two-letter flag). Not a string = "".
    Dropping a character can put two letters side by side that NFC then joins (Hangul jamo), so it repeats until nothing changes."""
    if not isinstance(value, str):
        return ""
    result = _clean_name_once(value)
    while True:
        again = _clean_name_once(result)
        if again == result:
            return result
        result = again


def _clean_name_once(value: str) -> str:
    text = unicodedata.normalize("NFC", value[:NAME_INPUT * 2])[:NAME_INPUT]
    out: list = []
    width, full, have_emoji, attach = 0, False, False, ""
    for char in text:
        point = ord(char)
        if any(low <= point <= high for low, high in EMOJI_RANGES):
            tone = 0x1F3FB <= point <= 0x1F3FF
            flag = 0x1F1E6 <= point <= 0x1F1FF
            if not have_emoji and not tone:
                have_emoji, attach = True, "flag" if flag else "base"
                out.append(char)
            elif (tone and "base" in attach) or (flag and attach == "flag"):
                out.append(char)
                attach = attach.replace("base", "") if tone else ""
            else:
                attach = ""
            continue
        if point == 0xFE0F and "base" in attach and out[-1] != char:
            out.append(char)
            continue
        attach = ""
        category = unicodedata.category(char)
        if point in BLANK_LETTERS or category[0] == "C" or category in ("Mn", "Me", "Zl", "Zp"):
            continue
        if category == "Zs":
            if not out or out[-1] == " ":
                continue
            char, point = " ", 32
        size = 2 if any(low <= point <= high for low, high in WIDE_RANGES) else 1
        if full or width + size > NAME_WIDTH:
            full = True
            continue
        out.append(char)
        width += size
    return "".join(out).strip(" ")


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
        self.allow_ai = True      # ROOM-FLOW R4: lobby options set by the host (both default to allowed so old clients are unaffected)
        self.allow_mcp = True
        self.join_seq = 0
        self.creator_addr = ""
        self.invites: Dict[str, Dict[str, Any]] = {}   # ROOM-FLOW R11: ticket id -> {by, team, note, expires}
        self.lobby = False       # ROOM-FLOW R12: a lobby room starts only after the host's `begin`, with every place holding a locked hero
        self.begin = False
        self.countdown: Any = None
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
             "units": entry["units"], "claim": max(entry.get("claim", 0), len(entry["units"])), "ai": bool(entry.get("ai")),
             "name": entry.get("name", ""), "agent": bool(entry.get("agent")), "invited_by": entry.get("invited_by")}
            for entry in sorted(self.sessions.values(), key=lambda item: item["seat_id"])
        ]

    def state(self, include_code: bool = False) -> Dict[str, Any]:
        message: Dict[str, Any] = {
            "type": "room_state",
            "seats": self.seats(),
            "rules_version": RULES_VERSION,
            "started": self.started,
            "host_seat_id": self.host_seat_id,
            "allow_ai": self.allow_ai,
            "allow_mcp": self.allow_mcp,
            "lobby": self.lobby,
            "begin": self.begin,
            "invites": [{"by": ticket["by"], "team": ticket["team"], "expires_in": max(0, int(round(ticket["expires"] - time.monotonic())))}
                        for ticket in self.invites.values()],   # who is waiting for an agent; the ticket ids are never broadcast
        }
        if include_code:
            message["code"] = self.code
        if self.team_size > 1:
            message["team_size"] = self.team_size
        if self.started:
            message.update({"seed": self.seed, "round": self.round,
                            "phase": self.phase, "first_team": self.first_team})
        return message

    def held_places(self, team: str) -> int:
        """Places of a team that are taken: each seat holds its reserved `claim`, never fewer than the heroes it listed; an open invite holds one."""
        return sum(max(seat.get("claim", 0), len(seat["units"])) for seat in self.team_seats(team)) + self.invited_places(team)

    def invited_places(self, team: str) -> int:
        return sum(1 for ticket in self.invites.values() if ticket["team"] == team)

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

    def places_taken(self) -> bool:
        """Both sides have all their places held by seats (one versus one: both sides have their player)."""
        if not self.team_match:
            return all(self.team_count(team) >= 1 for team in ("red", "white"))
        return all(self.held_places(team) - self.invited_places(team) >= self.team_size for team in ("red", "white"))

    def places_locked(self) -> bool:
        """ROOM-FLOW R12: nothing is left open: every seat names a hero for each place it holds and the heroes fill both teams."""
        if not self.team_match:
            return self.places_taken()
        for team in ("red", "white"):
            seats = self.team_seats(team)
            if any(not seat["units"] or len(seat["units"]) < seat.get("claim", 0) for seat in seats) or sum(len(seat["units"]) for seat in seats) != self.team_size:
                return False
        return True

    def all_players_ready(self) -> bool:
        players = [entry for entry in self.sessions.values() if entry["team"] in ("red", "white")]
        if not players or self.invites or not all(entry["ready"] for entry in players):   # an open invite holds the start (cancel it or let it expire)
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
        self.max_rooms_per_addr = int(limits.get("max_rooms_per_addr", MAX_ROOMS_PER_ADDR))
        self.max_spectators = int(limits.get("max_spectators", MAX_SPECTATORS_PER_ROOM))
        self.max_wrong_per_addr = int(limits.get("max_wrong_per_addr", MAX_WRONG_CODES_PER_MINUTE_PER_ADDR))
        self.room_idle_seconds = float(limits.get("room_idle_seconds", ROOM_IDLE_SECONDS))
        self.seat_grace_seconds = float(limits.get("seat_grace_seconds", SEAT_GRACE_SECONDS))
        self.invite_seconds = float(limits.get("invite_seconds", INVITE_SECONDS))
        self.agent_pick_seconds = float(limits.get("agent_pick_seconds", AGENT_PICK_SECONDS))
        self.countdown_seconds = float(limits.get("countdown_seconds", COUNTDOWN_SECONDS))
        self.trust_proxy = bool(limits.get("trust_proxy", TRUST_PROXY))
        self.gateway_token = str(limits.get("gateway_token", GATEWAY_TOKEN) or "")
        self.max_connects_per_min = int(limits.get("max_connects_per_min", MAX_CONNECTS_PER_MIN))
        self.max_bad_resumes_per_min = int(limits.get("max_bad_resumes_per_min", MAX_BAD_RESUMES_PER_MIN))
        self.block_seconds = float(limits.get("block_seconds", BLOCK_SECONDS))
        self.max_tracked_addrs = int(limits.get("max_tracked_addrs", MAX_TRACKED_ADDRS))
        self.connect_times: Dict[str, list] = {}
        self._error_logged: Dict[str, float] = {}
        self.bad_resume_times: Dict[str, list] = {}
        self.blocked_until: Dict[str, float] = {}
        self.block_strikes: Dict[str, tuple] = {}   # addr -> (number of blocks, time of the last one)
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
        if any(value > 0 for value in (self.room_idle_seconds, self.seat_grace_seconds, self.invite_seconds, self.agent_pick_seconds)):
            self._reaper = asyncio.ensure_future(self._reap_idle_rooms())

    async def _reap_idle_rooms(self) -> None:
        """Close the sockets of rooms that have been silent for room_idle_seconds, so an idle room cannot hold memory for ever."""
        periods = [value for value in (self.room_idle_seconds, self.seat_grace_seconds, self.invite_seconds, self.agent_pick_seconds) if value > 0]
        interval = max(0.05, min(2.0, min(periods) / 4.0))
        while True:
            await asyncio.sleep(interval)
            now = time.monotonic()
            await self._sweep_disconnected_seats(now)
            await self._sweep_agents(now)
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
        await self._release_host_fillers(room, entry)
        await self._release_invited(room, entry)
        self._reassign_host(room, entry)
        if not room.sessions:
            self.rooms.pop(room.code, None)
            self.last_seen.pop(room.code, None)
            return
        await self._broadcast(room, self._seat_left_message(room, entry, "disconnect_timeout"))
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

    def is_blocked(self, addr: str, now: Optional[float] = None) -> bool:
        until = self.blocked_until.get(addr)
        if until is None:
            return False
        if (time.monotonic() if now is None else now) >= until:
            self.blocked_until.pop(addr, None)
            return False
        return True

    def _trim_tracking(self) -> None:
        """Keep the tracking tables bounded when many different addresses connect: the oldest entries go first."""
        for table in (self.connect_times, self.bad_resume_times, self.blocked_until, self.block_strikes, self.wrong_by_addr):
            while len(table) > self.max_tracked_addrs:
                table.pop(next(iter(table)))

    def _block(self, addr: str, now: float) -> None:
        count, last = self.block_strikes.get(addr, (0, now))
        count = count + 1 if now - last < 3600.0 else 1
        seconds = min(self.block_seconds * (2 ** (count - 1)), max(self.block_seconds, MAX_BLOCK_SECONDS))
        self.blocked_until[addr] = now + seconds
        self.block_strikes[addr] = (count, now)
        self.connect_times.pop(addr, None)      # counting starts again after the block
        self.bad_resume_times.pop(addr, None)
        self._trim_tracking()
        logging.warning("relay: address blocked for %.0f s (strike %d)", seconds, count)

    def note_connect_attempt(self, addr: str, now: Optional[float] = None) -> bool:
        """Record one connection attempt; False when this address is blocked or has just gone over the per-minute limit."""
        if addr in UNTRACKED_ADDRS or self.max_connects_per_min <= 0:
            return True
        now = time.monotonic() if now is None else now
        if self.is_blocked(addr, now):
            return False
        times = [value for value in self.connect_times.get(addr, []) if now - value < 60.0]
        times.append(now)
        self.connect_times[addr] = times
        self._trim_tracking()
        if len(times) > self.max_connects_per_min:
            self._block(addr, now)
            return False
        return True

    def note_bad_resume(self, addr: str, now: Optional[float] = None) -> None:
        """Record one `resume` with a token that does not work; too many in a minute from one address blocks it like a reconnect storm."""
        if addr in UNTRACKED_ADDRS or self.max_bad_resumes_per_min <= 0:
            return
        now = time.monotonic() if now is None else now
        times = [value for value in self.bad_resume_times.get(addr, []) if now - value < 60.0]
        times.append(now)
        self.bad_resume_times[addr] = times
        self._trim_tracking()
        if len(times) > self.max_bad_resumes_per_min:
            self._block(addr, now)

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
        for room in self.rooms.values():
            if room.countdown is not None:
                room.countdown.cancel()
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
        host = re.match(r"^https?://([^/:]+)(:\d+)?$", normalized)   # external review: the old prefix test let http://localhost.evil.com in
        return bool(host) and normalized.startswith("http://") and host.group(1) in ("localhost", "127.0.0.1")

    async def _send(self, websocket: Any, message: Dict[str, Any]) -> None:
        try:
            await websocket.send(json_bytes(message))
        except ConnectionClosed:
            pass

    async def _error(self, websocket: Any, code: str, message: Optional[str] = None) -> None:
        now = time.monotonic()
        if now - self._error_logged.get(code, -10.0) >= 1.0:   # FLOOD-1: under attack the same error would fill the log; one line per code per second is enough
            self._error_logged[code] = now
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
                        "seat_token": entry["seat_token"], "last_seq": room.next_seq - 1,
                        "first_seq": room.log[0]["seq"] if room.log else room.next_seq})
        if entry.get("briefing") and not room.started:
            message["briefing"] = entry["briefing"]   # private to the invited seat (ROOM-FLOW R11)
        await self._send(websocket, message)

    async def _replay(self, room: Room, websocket: Any, last_seq: int) -> None:
        for message in room.log:
            if message["seq"] > last_seq:
                await self._send(websocket, message)

    async def _tell(self, room: Room, message: Dict[str, Any]) -> None:
        """Send an unsequenced notice to every socket of the room (not in the replay log)."""
        await asyncio.gather(*[self._send(client, message) for client in list(room.clients)], return_exceptions=True)

    async def _broadcast_state(self, room: Room) -> None:
        # Red team A4/B5: a room state is a snapshot, not an event: it is sent unsequenced and not kept in the log, so the log stays small and a newcomer
        # does not replay old states (a joiner gets the current one in its bootstrap). Clients already treat an unsequenced room_state as current.
        state = room.state()
        await asyncio.gather(*[self._send(client, state) for client in list(room.clients)], return_exceptions=True)

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
        if not isinstance(value, list) or len(value) > MAX_UNITS_PER_TEAM or any(not isinstance(unit, str) or not UNIT_ID.match(unit) for unit in value):
            raise ValueError
        return list(value)

    @staticmethod
    def _check_team_units(room: Room, entry: Dict[str, Any], units: list) -> None:
        """Team matches only: a seat may not list more units than the team has room for, nor repeat a hero already named on its team in a lobby room."""
        if entry.get("agent") and len(units) > 1:
            raise ValueError("too_many_units")   # red team A6: an invited agent plays the one place of its ticket
        if not room.team_match:
            return
        others = sum(max(seat.get("claim", 0), len(seat["units"])) for seat in room.team_seats(entry["team"]) if seat is not entry) + room.invited_places(entry["team"])
        if len(units) + others > room.team_size:
            raise ValueError("too_many_units")
        if room.lobby:
            if len(set(units)) != len(units):
                raise ValueError("duplicate_hero")
            taken = {hero for seat in room.team_seats(entry["team"]) if seat is not entry for hero in seat["units"]}
            if any(hero in taken for hero in units):
                raise ValueError("duplicate_hero")

    async def _handle_socket(self, websocket: Any, path: Optional[str] = None) -> None:
        room: Optional[Room] = None
        entry: Optional[Dict[str, Any]] = None
        timestamps: list = []
        wrong_code_times: list = []
        addr = self._addr(websocket)
        if not self.note_connect_attempt(addr):
            await self._error(websocket, "temporarily_blocked", "too many connection attempts from this address; wait a few minutes and try again")
            await websocket.close(code=1013, reason="temporarily blocked")
            return
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
                if room is not None and room.clients.get(websocket) is not entry:
                    room, entry = None, None   # red team A1: this socket was removed (kicked, or its host or inviter left): it speaks for no seat any more
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
                self.note_bad_resume(self._addr(websocket))
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
                    self.note_bad_resume(self._addr(websocket))
                    return None, None
                if last_seq > candidate.next_seq - 1:
                    await self._error(websocket, "invalid_resume")
                    self.note_bad_resume(self._addr(websocket))
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
            self.note_bad_resume(self._addr(websocket))
            return None, None
        if message_type == "create_room":
            if room is not None:
                await self._error(websocket, "already_joined")
                return room, entry
            if len(self.rooms) >= self.max_rooms or (self._addr(websocket) not in UNTRACKED_ADDRS and sum(1 for other in self.rooms.values() if other.creator_addr == self._addr(websocket)) >= self.max_rooms_per_addr):   # behind nginx without proxy trust every browser is 127.0.0.1: never cap that
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
            room.lobby = message.get("lobby") is True
            room.creator_addr = self._addr(websocket)
            if room.lobby:
                room.allow_mcp = False   # owner 2026-11-25: the invite button appears only after the host ticks "allow agents"; old rooms keep agents on
            self.rooms[room.code] = room
            entry = await self._join(room, websocket, message)
            if entry is None:
                self.rooms.pop(room.code, None)
                self.last_seen.pop(room.code, None)
                return None, None
            room.host_seat_id = entry["seat_id"] if entry["team"] != "spectator" else None   # red team A7: a spectator never hosts; the first player who sits does
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
            self._trim_tracking()   # red team A10: bounded like the other tables
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
                await self._start_if_ready(room)
                return room, entry
            return None, None
        if room is None or entry is None:
            await self._error(websocket, "join_required")
            return room, entry
        if message_type == "reset_lobby":
            # ROOM-FLOW R6: after a match, the host sends everybody back to the lobby of the same room: seats, names, claims and the host stay;
            # the match state, the heroes and the ready flags are cleared so the same room can start again.
            host_here = any(seat["seat_id"] == room.host_seat_id for seat in room.sessions.values())
            if entry["seat_id"] != room.host_seat_id and (host_here or entry["team"] not in ("red", "white") or entry.get("ai") or entry.get("agent")):
                await self._error(websocket, "host_only", "only the host can reopen the lobby")
                return room, entry
            if not room.started:
                await self._error(websocket, "invalid_state", "the match has not started")
                return room, entry
            if not host_here:
                room.host_seat_id = entry["seat_id"]   # DESIGN-1: the host left during or after the match; the player who reopens the lobby hosts it
                for seat in list(room.sessions.values()):
                    if seat.get("ai"):
                        await self._evict(room, seat, "host_left")   # cross-check: those computer seats lived in the old host's browser; the new host fills again
            room.started = False
            room.begin = False
            for seat in room.sessions.values():
                if seat.get("agent"):
                    seat["joined_at"] = time.monotonic()   # a rematch gives an agent the full pick time again
            room.seed = None
            room.first_team = None
            room.round = 1
            room.phase = None
            room.actions = {}
            room.action_by_turn = set()
            room.turn_unit = {}
            room.judged = set()
            room.round_hashes = {}
            room.reported_mismatches = set()
            room.owners = {}
            room.log = []   # R6b: the sequence keeps counting (a client drops numbers it has passed); a new joiner learns where the log starts (first_seq)
            room.host_side_coin = None
            room.resolved_host_side = None
            for seat in room.sessions.values():
                seat["ready"] = False
                seat["units"] = []
            await self._broadcast(room, {"type": "lobby_reset"})
            await self._broadcast_state(room)
            return room, entry
        if message_type == "room_options":
            # ROOM-FLOW R4: lobby options; only the host, only before the match starts.
            if entry["seat_id"] != room.host_seat_id:
                await self._error(websocket, "host_only", "only the host can change the room options")
                return room, entry
            if room.started:
                await self._error(websocket, "room_started", "the match has already started")
                return room, entry
            keys = [key for key in ("allow_ai", "allow_mcp") if key in message]
            if not keys or any(not isinstance(message[key], bool) for key in keys):
                await self._error(websocket, "invalid_options", "allow_ai and allow_mcp must be true or false")
                return room, entry
            for key in keys:
                setattr(room, key, message[key])
            if not room.allow_mcp:
                room.invites.clear()   # R11: switching agents off withdraws every open invite
            for seat in list(room.sessions.values()):   # red team A13: the seats an option forbids leave with it
                if (seat.get("ai") and not room.allow_ai) or (seat.get("agent") and not room.allow_mcp):
                    await self._evict(room, seat, "ai_off" if seat.get("ai") else "agents_off")
            await self._broadcast_state(room)
            await self._start_if_ready(room)
            return room, entry
        if message_type == "kick":
            if entry["seat_id"] != room.host_seat_id:
                await self._error(websocket, "host_only", "only the host can remove a seat")
                return room, entry
            if room.started:
                await self._error(websocket, "room_started", "the match has already started")
                return room, entry
            target = next((seat for seat in room.sessions.values() if seat["seat_id"] == message.get("seat_id")), None)
            if target is None or target is entry:
                await self._error(websocket, "invalid_target", "no such seat, or it is your own")
                return room, entry
            target_socket = next((sock for sock, seat in room.clients.items() if seat is target), None)
            if target_socket is not None:
                await self._send(target_socket, {"type": "kicked", "reason": "removed_by_host"})
                await self._remove_client(room, target_socket, release=True)
                try:
                    await target_socket.close(code=1000, reason="removed_by_host")   # red team A1
                except Exception:  # noqa: BLE001 - already gone
                    pass
            else:
                room.sessions.pop(target["seat_token"], None)   # red team A8: a seat in its grace period gets the same releases and start check
                await self._release_invited(room, target)
                await self._broadcast_state(room)
                await self._start_if_ready(room)
            return room, entry
        if message_type == "unready":
            # ROOM-FLOW R3: take the ready flag back (change hero or seat); only before the match starts.
            if room.started:
                await self._error(websocket, "room_started", "the match has already started")
                return room, entry
            entry["ready"] = False
            if room.lobby and room.team_match:
                entry["units"] = []   # red team (polish) page P7: an unlocked pick no longer holds a hero a teammate may want (the page sends its picks again at the next lock)
            await self._broadcast_state(room)
            await self._start_if_ready(room)   # R12: an unlock stops a running countdown
            return room, entry
        if message_type == "ping":
            return room, entry   # a quiet lobby page says it is still here, so the idle sweep does not close a room people are waiting in (external review)
        if message_type == "begin":
            if entry["seat_id"] != room.host_seat_id:
                await self._error(websocket, "host_only", "only the host can start the match")
                return room, entry
            if room.started:
                await self._error(websocket, "room_started", "the match has already started")
                return room, entry
            if not room.lobby:
                await self._error(websocket, "invalid_state", "this room starts when everybody is ready")
                return room, entry
            on = message.get("on", True)
            if not isinstance(on, bool):
                await self._error(websocket, "invalid_options", "on must be true or false")
                return room, entry
            if on and not room.allow_ai and not room.places_taken():
                await self._error(websocket, "not_full", "some places are still free and AI seats are off")
                return room, entry
            room.begin = on
            await self._broadcast_state(room)
            await self._start_if_ready(room)
            return room, entry
        if message_type == "move":
            await self._move(room, websocket, entry, message)
            return room, entry
        if message_type == "invite":
            await self._invite(room, websocket, entry, message)
            return room, entry
        if message_type == "invite_cancel":
            if room.started:
                await self._error(websocket, "room_started", "the match has already started")
                return room, entry
            by = message.get("by", entry["seat_id"])
            if by != entry["seat_id"] and entry["seat_id"] != room.host_seat_id:
                await self._error(websocket, "host_only", "only the host can cancel another player's invite")
                return room, entry
            mine = [key for key, ticket in room.invites.items() if ticket["by"] == by]
            if not mine:
                await self._error(websocket, "invalid_target", "there is no open invite to cancel")
                return room, entry
            for key in mine:
                room.invites.pop(key, None)
            await self._broadcast_state(room)
            await self._start_if_ready(room)
            return room, entry
        if message_type == "set_name":
            if room.started:
                await self._error(websocket, "room_started", "the match has already started")
                return room, entry
            if not isinstance(message.get("name"), str):
                await self._error(websocket, "invalid_name", "a name is text")
                return room, entry
            entry["name"] = clean_name(message["name"])
            await self._broadcast_state(room)
            return room, entry
        if message_type == "ready":
            if not room.started:
                if "name" in message:
                    if not isinstance(message["name"], str):
                        await self._error(websocket, "invalid_name", "a name is text")
                        return room, entry
                    entry["name"] = clean_name(message["name"])
                # Optional team-battle fields, honoured only before the match starts. The host may set the
                # team size; a seat may replace its unit list. A bad value is an explicit error and the
                # seat does not become ready, so a mistake can never start a different match.
                if entry["seat_id"] == room.host_seat_id and "team_size" in message:
                    try:
                        size = self._parse_team_size(message["team_size"])
                    except ValueError as exc:
                        await self._error(websocket, str(exc), "team_size must be an integer from 1 to 3")
                        return room, entry
                    held = max(room.held_places(team) for team in ("red", "white")) if room.team_match else 0
                    if size != room.team_size and (held > size or room.team_match != (size > 1)):
                        await self._error(websocket, "invalid_team_size", "the seats already hold more places than that")   # red team A5: checked before anything changes
                        return room, entry
                    room.team_size = size
                if "units" in message and entry["team"] != "spectator":
                    try:
                        units = self._parse_units(message["units"])
                        self._check_team_units(room, entry, units)
                    except ValueError as exc:
                        await self._error(websocket, "invalid_units", "that hero is already on your team" if str(exc) == "duplicate_hero" else "too many heroes for your places")   # red team (polish) P7: say why
                        return room, entry
                    entry["units"] = units
                if room.lobby and room.team_match and entry["team"] in ("red", "white") and len(entry["units"]) < max(1, entry.get("claim", 0)):
                    await self._error(websocket, "invalid_units", "name a hero for every place you hold")   # external review: a ready seat with unnamed places held the start with no visible cause
                    return room, entry
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
        ticket_id, ticket = None, None
        if message.get("type") == "join" and "invite" in message:
            # ROOM-FLOW R11: the ticket decides the side and the single place; the `seat` field is ignored.
            ticket_id = message.get("invite")
            ticket = room.invites.get(ticket_id) if isinstance(ticket_id, str) else None
            if ticket is None or ticket["expires"] <= time.monotonic() or room.started:
                self.wrong_by_addr.setdefault(self._addr(websocket), []).append(time.monotonic())   # guessing tickets counts like guessing room codes
                await self._error(websocket, "invalid_invite", "this invitation does not exist, was used, or has expired")
                return None
            team = ticket["team"]
        elif message.get("type") == "join" and ("seat" not in message or team == "auto"):
            # ROOM-FLOW R2: no side named (or "auto"): the relay picks the team with the most free units (red on a tie); a plain room takes the
            # empty side. Any other value, an explicit null included, is still `invalid_seat`.
            if room.team_match:
                free = {name: room.team_size - room.held_places(name) for name in ("red", "white")}
                best = max(("red", "white"), key=lambda name: free[name])
                team = best if free[best] > 0 else None
            else:
                team = next((name for name in ("red", "white") if room.team_count(name) == 0), None)
            if team is None:
                await self._error(websocket, "team_full", "no side of this room has a free place")
                return None
        if team not in ("red", "white", "spectator"):
            await self._error(websocket, "invalid_seat")
            return None
        if team != "spectator" and message.get("type") != "create_room" and not room.allow_mcp and (str(message.get("client_kind", "")).lower() == "mcp" or self._addr(websocket).startswith("mcp:")):
            # ROOM-FLOW R5: the host switched agents off. An MCP client says so itself (client_kind) or comes through the hosted gateway (its token, see _addr).
            # Both are hints, not a security boundary: a browser-driven agent looks like a person and is not caught here.
            await self._error(websocket, "mcp_disabled", "the host does not allow MCP agents in this room")
            return None
        if "name" in message and not isinstance(message.get("name"), str):
            await self._error(websocket, "invalid_name", "a name is text")
            return None
        is_ai = False
        if "ai_host_token" in message:
            # ROOM-FLOW R9: the host's built-in AI filler proves itself with the host's own seat token. Only such a seat is marked `ai`
            # (it may disappear without costing its team the match), so nobody else can claim it: a person could otherwise quit for free.
            proof = message.get("ai_host_token")
            host = room.sessions.get(proof) if isinstance(proof, str) else None
            if team == "spectator" or host is None or host["seat_id"] != room.host_seat_id:
                await self._error(websocket, "host_only", "only the host can add an AI seat")
                return None
            if not room.allow_ai:
                await self._error(websocket, "ai_disabled", "the host does not allow AI seats in this room")
                return None
            is_ai = True
        if team != "spectator" and room.started:
            # LATE-JOIN-1: a player seat created after the start never receives `start` and cannot take part. Refuse it with a clear code;
            # `resume` of an existing seat and spectators are unchanged.
            await self._error(websocket, "room_started", "the match has already started; ask the host for a new room")
            return None
        if team != "spectator" and (room.team_count(team) + max(0, room.invited_places(team) - (1 if ticket is not None else 0)) >= MAX_TEAM_SEATS   # red team (polish) P6: open invites hold seats too
                                    or (room.lobby and not room.team_match and room.team_count(team) >= 1)):   # red team A3: one seat per side in a 1v1 lobby room (old rooms keep their several devices per side)
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
        claim = 0
        if team != "spectator" and room.team_match:
            # ROOM-FLOW R1/R1b: places are a shared pool. A seat reserves `claim` places at join time (default 1, never fewer than the heroes it
            # lists), even before it has picked heroes. Earlier seats keep theirs; this one gets at most what is still free, and a team with
            # nothing free refuses another seat (a seat with no place could never be ready and the whole room would wait for ever).
            raw = 1 if ticket is not None else message.get("claim")
            if raw is not None and (isinstance(raw, bool) or not isinstance(raw, int) or not 1 <= raw <= MAX_UNITS_PER_TEAM):
                await self._error(websocket, "invalid_units")
                return None
            free = room.team_size - room.held_places(team) + (1 if ticket is not None else 0)   # the ticket's own place becomes this seat's
            if ticket is not None:
                units = units[:1]
                free = min(free, 1)
            if free <= 0:
                await self._error(websocket, "team_full", "every place of this team is already taken")
                return None
            claim = min(max(raw or 0, len(units)), free)   # no claim sent = nothing reserved (old clients and the slot filler's placeholders list their units at ready)
            units = units[:claim]
            if room.lobby:   # red team (polish) P1: no hero twice on a team, at join too; a repeated or taken hero is dropped (the seat still sits and picks again at ready)
                taken = {hero for mate in room.team_seats(team) for hero in mate["units"]}
                units = [hero for i, hero in enumerate(units) if hero not in taken and hero not in units[:i]]
        room.join_seq += 1
        entry = {"seat_id": self._allocate_seat(room, team), "team": team, "units": units, "claim": claim, "joined": room.join_seq,
                 "ready": False, "client_version": message.get("client_version", ""), "ai": is_ai, "name": clean_name(message.get("name")),
                 "seat_token": secrets.token_urlsafe(24), "connected": True}
        if ticket is not None:
            room.invites.pop(ticket_id, None)
            inviter = next((seat for seat in room.sessions.values() if seat["seat_id"] == ticket["by"]), None)
            entry.update({"agent": True, "invited_by": ticket["by"], "joined_at": time.monotonic(), "name": entry["name"] or "Agent"})
            entry["briefing"] = self._briefing(room, entry, inviter, ticket)
        room.sessions[entry["seat_token"]] = entry
        room.clients[websocket] = entry
        if team != "spectator" and not is_ai and ticket is None and not room.started and not any(seat["seat_id"] == room.host_seat_id for seat in room.sessions.values()):
            room.host_seat_id = entry["seat_id"]   # the host left and only spectators stayed: the next player seat is the host (create_room sets it again right after)
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
            unit_key = (entry["team"], room.round, room.phase)   # per team, not per seat: a teammate's seat cannot act for another unit in the same turn (LIVE-3V3-1)
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
        if not room.started or entry["team"] not in ("red", "white") or not isinstance(round_number, int) or not isinstance(digest, str) or not digest:
            await self._error(websocket, "invalid_round_hash")   # external review: a spectator's hash could put every page out of sync
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
        if room.started:
            return
        if not room.lobby:
            if room.all_players_ready():
                await self._start(room)
            return
        due = self._lobby_due(room)
        if due and room.countdown is None:
            room.countdown = asyncio.ensure_future(self._count_down(room))
            await self._tell(room, {"type": "countdown", "seconds": self.countdown_seconds})   # a passing notice, not logged: a newcomer must not replay an old one (external review)
        elif not due and room.countdown is not None:
            room.countdown.cancel()
            room.countdown = None
            await self._tell(room, {"type": "countdown", "seconds": None})

    @staticmethod
    def _lobby_due(room: Room) -> bool:
        return not room.started and room.begin and room.all_players_ready() and room.places_locked()

    async def _count_down(self, room: Room) -> None:
        await asyncio.sleep(self.countdown_seconds)
        room.countdown = None
        if self.rooms.get(room.code) is room and self._lobby_due(room):
            await self._start(room)

    async def _start(self, room: Room) -> None:
        room.started = True
        room.begin = False
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

    @staticmethod
    def _reassign_host(room: Room, gone: Dict[str, Any]) -> None:
        """ROOM-FLOW R4: if the host's seat is gone before the start, the earliest remaining player seat becomes the host. After the start nobody takes over."""
        if room.started or gone.get("seat_id") != room.host_seat_id:
            return
        room.begin = False   # the next host decides when to start
        players = [seat for seat in room.sessions.values() if seat["team"] != "spectator" and not seat.get("ai") and not seat.get("agent")]
        room.host_seat_id = min(players, key=lambda seat: (not seat.get("connected"), seat.get("joined", 0)))["seat_id"] if players else None

    async def _evict(self, room: Room, seat: Dict[str, Any], reason: str) -> None:
        """Take a seat out of the room for good: its session and socket go, the socket is told why and closed (red team A1: a removed socket must not keep acting)."""
        room.sessions.pop(seat["seat_token"], None)
        socket = next((sock for sock, other in room.clients.items() if other is seat), None)
        if socket is None:
            return
        room.clients.pop(socket, None)
        await self._send(socket, {"type": "kicked", "reason": reason})
        try:
            await socket.close(code=1000, reason=reason)
        except Exception:  # noqa: BLE001 - a socket that is already gone is fine
            pass

    async def _release_host_fillers(self, room: Room, gone: Dict[str, Any]) -> None:
        """ROOM-FLOW R9: the AI fillers live in the host's browser. A host who leaves before the start takes them along, so the next host does not
        inherit seats that would start a match and never act."""
        if room.started or gone["seat_id"] != room.host_seat_id:
            return
        for token, seat in list(room.sessions.items()):
            if not seat.get("ai"):
                continue
            await self._evict(room, seat, "host_left")

    async def _release_invited(self, room: Room, gone: Dict[str, Any]) -> None:
        """ROOM-FLOW R11: before the start an agent and an open invite go with the player who invited them. After the start the leave rule applies as usual."""
        if room.started:
            return
        for ticket_id, ticket in list(room.invites.items()):
            if ticket["by"] == gone["seat_id"]:
                room.invites.pop(ticket_id, None)
        for token, seat in list(room.sessions.items()):
            if seat.get("invited_by") != gone["seat_id"]:
                continue
            await self._evict(room, seat, "inviter_left")

    async def _sweep_agents(self, now: float) -> None:
        """ROOM-FLOW R11: drop expired invites; lock an agent that did not pick in time with a hero nobody on its team named."""
        for room in list(self.rooms.values()):
            if room.started:
                continue
            changed = False
            for ticket_id, ticket in list(room.invites.items()):
                if ticket["expires"] <= now:
                    room.invites.pop(ticket_id, None)
                    changed = True
            for seat in list(room.sessions.values()):
                if not seat.get("agent") or seat["ready"] or self.agent_pick_seconds <= 0 or now - seat.get("joined_at", now) < self.agent_pick_seconds:
                    continue
                named = {hero for mate in room.team_seats(seat["team"]) if mate is not seat for hero in mate["units"]}
                if not seat["units"] or (room.lobby and any(hero in named for hero in seat["units"])):   # external review: a 1v1 agent got none; red team (polish) P7: or one a teammate holds
                    seat["units"] = [next((hero for hero in HERO_IDS if hero not in named), HERO_IDS[0])]
                seat["ready"] = True
                changed = True
            if changed:
                await self._broadcast_state(room)
                await self._start_if_ready(room)

    def _briefing(self, room: Room, seat: Dict[str, Any], inviter: Optional[Dict[str, Any]], ticket: Dict[str, Any]) -> Dict[str, Any]:
        """What a joining agent is told: whose side it is on, what to do, and the rules that matter to it."""
        return {
            "team": seat["team"], "places": 1, "invited_by": {"seat_id": ticket["by"], "name": (inviter or {}).get("name", "")},
            "note": ticket["note"], "heroes": list(HERO_IDS), "pick_within_seconds": int(self.agent_pick_seconds), "turn_seconds": AGENT_TURN_SECONDS,
            "goal": "Knock out every unit of the other team.",
            "steps": ["Pick one hero for your unit and lock it within the pick time; otherwise one is picked for you.",
                      "Then play every turn of your unit on your own, without waiting to be asked."],
            "rules": ["Use only the information the game shows to every player.",
                      "A turn left unplayed when its time runs out is skipped.",
                      "Leaving after the match starts loses the match for your team."],
        }

    async def _move(self, room: Room, websocket: Any, entry: Dict[str, Any], message: Dict[str, Any]) -> None:
        """ROOM-FLOW R13: before the start a player takes or releases places, or changes side, without leaving the room."""
        if room.started:
            await self._error(websocket, "room_started", "the match has already started")
            return
        if entry["team"] not in ("red", "white") or entry.get("ai") or entry.get("agent"):
            await self._error(websocket, "move_not_allowed", "only a player can change places")
            return
        team = message.get("team", entry["team"])
        claim = message.get("claim")
        if team not in ("red", "white") or (claim is not None and (isinstance(claim, bool) or not isinstance(claim, int) or not 1 <= claim <= MAX_UNITS_PER_TEAM)):
            await self._error(websocket, "invalid_options", "team is red or white and claim is 1 to 3")
            return
        switching = team != entry["team"]
        mine = max(entry.get("claim", 0), len(entry["units"]))
        if room.team_match:
            free = room.team_size - room.held_places(team) + (0 if switching else mine)
            if free <= 0 or (switching and room.team_count(team) + room.invited_places(team) >= MAX_TEAM_SEATS):
                await self._error(websocket, "team_full", "that team has no free place")
                return
            want = min(claim or mine or 1, free)
        else:
            if switching and room.team_count(team) >= 1:
                await self._error(websocket, "team_full", "that side is taken")
                return
            want = mine
        if switching or want != mine:
            if switching:
                await self._release_invited(room, entry)   # an agent plays on its inviter's team, so it cannot stay behind
                old = entry["seat_id"]
                entry["seat_id"], entry["team"] = self._allocate_seat(room, team), team
                if room.host_seat_id == old:
                    room.host_seat_id = entry["seat_id"]
            entry["claim"], entry["units"], entry["ready"] = want, ([] if switching else entry["units"][:want]), False
        await self._send_state(room, websocket, entry, include_code=True)   # the mover learns its seat id
        await self._broadcast_state(room)
        await self._start_if_ready(room)

    async def _invite(self, room: Room, websocket: Any, entry: Dict[str, Any], message: Dict[str, Any]) -> None:
        """ROOM-FLOW R11: one open invite or one seated agent per player, for the player's own team."""
        if room.started:
            await self._error(websocket, "room_started", "the match has already started")
            return
        if entry["team"] not in ("red", "white") or entry.get("ai") or entry.get("agent"):
            await self._error(websocket, "invite_not_allowed", "only a player can invite an agent")
            return
        if not room.allow_mcp:
            await self._error(websocket, "mcp_disabled", "the host does not allow agents in this room")
            return
        note = message.get("note", "")
        if not isinstance(note, str):
            await self._error(websocket, "invalid_invite", "a note is text")
            return
        ticket_id = next((key for key, ticket in room.invites.items() if ticket["by"] == entry["seat_id"]), None)
        if ticket_id is None:
            if any(seat.get("invited_by") == entry["seat_id"] for seat in room.sessions.values()):
                await self._error(websocket, "invite_limit", "one agent per player")
                return
            team = entry["team"]
            free = (room.team_size - room.held_places(team)) if room.team_match else (1 - room.team_count(team))
            if free <= 0 or room.team_count(team) + room.invited_places(team) >= MAX_TEAM_SEATS:
                await self._error(websocket, "team_full", "your team has no free place")
                return
            note = " ".join("".join(char for char in note[:INVITE_NOTE_LENGTH * 2] if unicodedata.category(char)[0] != "C" or char in "\n\t").split())[:INVITE_NOTE_LENGTH]
            ticket_id = "%s.%s" % (team, secrets.token_urlsafe(9))
            room.invites[ticket_id] = {"by": entry["seat_id"], "team": team, "note": note, "expires": time.monotonic() + self.invite_seconds}
        left = room.invites[ticket_id]["expires"] - time.monotonic()
        await self._send(websocket, {"type": "invite_created", "invite": ticket_id, "team": room.invites[ticket_id]["team"], "expires_in": max(0, int(round(left)))})
        await self._broadcast_state(room)
        await self._start_if_ready(room)   # an open invite holds the start

    @staticmethod
    def _seat_left_message(room: Room, gone: Dict[str, Any], reason: str) -> Dict[str, Any]:
        """`seat_left` for a seat already removed from the room. For an AI seat in a started match (ROOM-FLOW R9) its units go to a teammate
        (a person before another AI, a connected seat before one in grace, then join order) and the message carries the new owners; when its
        team has no seat left `team_empty` says so. For a person the message is unchanged: the pages apply the leave rule."""
        message: Dict[str, Any] = {"type": "seat_left", "seat_id": gone["seat_id"], "team": gone["team"], "reason": reason}
        if not (gone.get("ai") and room.started):
            return message
        mates = room.team_seats(gone["team"])
        if mates:
            heir = min(mates, key=lambda seat: (bool(seat.get("ai")), not seat.get("connected"), seat.get("joined", 0)))
            for unit, owner in list(room.owners.items()):
                if owner == gone["seat_id"]:
                    room.owners[unit] = heir["seat_id"]
        message.update({"ai": True, "team_empty": not mates, "owners": dict(room.owners)})
        return message

    async def _remove_client(self, room: Room, websocket: Any, *, release: bool = False) -> None:
        entry = room.clients.pop(websocket, None)
        if entry is None:
            return
        entry["connected"] = False
        entry["disconnected_at"] = time.monotonic()
        if release:
            room.sessions.pop(entry["seat_token"], None)
            await self._release_host_fillers(room, entry)
            await self._release_invited(room, entry)
            self._reassign_host(room, entry)
        if not room.sessions:
            self.rooms.pop(room.code, None)
            self.last_seen.pop(room.code, None)   # red team A9
            return
        if release and room.started and entry["team"] in ("red", "white"):
            await self._broadcast(room, self._seat_left_message(room, entry, "left"))   # R9/R9b: a player who leaves a started match is announced, like one whose grace ran out
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
