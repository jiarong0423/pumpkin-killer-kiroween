#!/usr/bin/env python3
"""Fill the open unit slots of a team room (docs/ADR_unit_slot_fill_20261124.md, stage 3).

Seats are independent: every human seat names only its own units. This helper is one more independent seat that is computed last:
for each team, remainder = team size - (units named by the human seats of that team). It fills that remainder and nothing else.

How it works (against the unchanged room protocol, plus the relay's start check after a seat leaves):
  1. It joins the room with one placeholder seat per team (no units, never ready). The relay does not start while a player seat is not ready,
     so the humans can press Start without the match beginning behind the helper's back.
  2. It waits until every human seat is ready and nothing has changed for --settle seconds (the host pressed Start, every guest is in).
  3. It subtracts per team. A team with remainder 0 gets no filler. A team with remainder k gets a seat that names k heroes drawn at random
     from the heroes the team has not taken (seeded from the room code, so the draw is reproducible and is recorded in the start message's `heroes`).
  4. --filler computer: the seat is a headless page of this project (scripts/hybrid_seat_headless.js --claim k): the page's own computer shot.
     --filler agent: NOT supported yet (the MCP bridge cannot take part of a team); the helper refuses before it joins anything.
  5. When the filler seats are ready the placeholders leave; the relay then starts the match. The helper stays until the filler seats finish.

Usage (needs a relay socket, so run it from your own terminal; the Claude sandbox cannot listen or connect):
  python3 -B scripts/fill_room.py --relay ws://localhost:8765 --code ABC234 --filler computer
  python3 -B scripts/fill_room.py --selftest [--scenario split|both|none]   no phone: a spectator-made room of 3 with headless human seats; split = red 1+2 and the filler takes white

Start ONE helper per room (two helpers would hold each other's start back). The relay allows 8 connections per address by default (PK_RELAY_MAX_PER_ADDR): the humans on this machine, the helper's three sockets and the filler seats all count.
Log: logs_local/fill_room.log (the last run) and logs_local/fill_room_<date>_<time>.log (kept per run). Exit code 0 only when every filler seat finished its match with reason game_over and no error. Never reads a key or token.
"""
import argparse
import asyncio
import json
import os
import random
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import websockets  # noqa: E402

HEROES = ["skeleton", "wizard", "bat", "knight", "bride", "hunchback", "reaper", "hag"]   # the same list as run_hybrid_room.HEROES (a test pins that)
TEAMS = ("red", "white")
RUN_ID = time.strftime("%Y%m%d_%H%M%S")
LOG_PATH = os.path.join(ROOT, "logs_local", "fill_room.log")   # the last run (truncated by whoever starts a run)
RUN_LOG_PATH = os.path.join(ROOT, "logs_local", "fill_room_%s.log" % RUN_ID)   # this run, kept (red-team R1 B1: an evidence file must cite a log that is not overwritten)
EXIT_OK, EXIT_FAIL, EXIT_USAGE, EXIT_JOIN, EXIT_WAIT, EXIT_AGENT, EXIT_START, EXIT_CHANGED = 0, 1, 2, 3, 4, 5, 6, 7
JOIN_REPLY_SECONDS = 10      # how long a seat waits for the relay's room_state after it joined
START_WAIT_SECONDS = 20      # how long the helper waits for the relay's start after the placeholders left
POLL_SECONDS = 0.2           # poll step of every wait loop
HOLD_ON_CHANGE_SECONDS = 60  # a changed formation: keep the placeholders connected this long so the host can see the error, then exit without calling leave() (relay grace expiry applies after)


def log(message: str) -> None:
    line = "%s %s" % (time.strftime("%H:%M:%S"), message)
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        for path in (LOG_PATH, RUN_LOG_PATH):
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
    except OSError:
        pass   # a log that cannot be written must not stop the fill; the line is on the screen


def base_url(relay: str) -> str:
    """ws://host:port without a path (the headless seat adds its own); the Python sockets add /ws."""
    text = relay.strip()
    if text.endswith("/ws"):
        text = text[:-3]
    return text.rstrip("/")


def team_remainders(team_size: int, seats: List[Dict[str, Any]], holder_ids: Set[str]) -> Dict[str, int]:
    """remainder = team size - units named by the human seats of the team. A ready human seat with no unit list counts as the whole team (the relay then has no owners for that team, so nothing may be added)."""
    out = {team: team_size for team in TEAMS}
    for seat in seats:
        team = seat.get("team")
        if seat.get("seat_id") in holder_ids or team not in out:
            continue
        units = seat.get("units") or []
        named = len(units) if units else (team_size if seat.get("ready") else 0)
        out[team] = max(0, out[team] - named)
    return out


def taken_heroes(team: str, seats: List[Dict[str, Any]], holder_ids: Set[str]) -> List[str]:
    out: List[str] = []
    for seat in seats:
        if seat.get("team") == team and seat.get("seat_id") not in holder_ids:
            out.extend(str(unit) for unit in (seat.get("units") or []))
    return out


def draw_heroes(code: str, team: str, count: int, taken: List[str], team_size: int) -> Tuple[List[str], List[str]]:
    """The heroes the filler names (count of them, none taken by a teammate) and the full team list the headless page needs (the named ones first, then the rest, team_size long)."""
    rng = random.Random("%s:%s" % (code, team))
    pool = [hero for hero in HEROES if hero not in taken]
    rng.shuffle(pool)
    named = pool[:count]
    rest = [hero for hero in pool[count:]] + [hero for hero in HEROES if hero in taken]
    full = (named + rest)[:team_size]
    return named, full


def seed_from(code: str, team: str) -> int:
    return sum(ord(ch) * (index + 3) for index, ch in enumerate(code + team)) % 2147483647 or 1


def formation_unchanged(humans_before: List[Dict[str, Any]], seats_now: List[Dict[str, Any]], holder_ids: Set[str], filler_ids: Set[str]) -> Tuple[bool, str]:
    """Red-team R1 B4: the fill was planned from the human seats at one moment. Before the placeholders let the match start, the human seats must still be exactly those (same seats, same unit lists, all ready) and no new human seat may have come in."""
    before = {s["seat_id"]: (s.get("team"), list(s.get("units") or [])) for s in humans_before}
    now = {s["seat_id"]: (s.get("team"), list(s.get("units") or [])) for s in seats_now if s.get("team") in TEAMS and s.get("seat_id") not in holder_ids and s.get("seat_id") not in filler_ids}
    ready_now = {s["seat_id"]: bool(s.get("ready")) for s in seats_now}
    if before != now:
        gone = sorted(set(before) - set(now)); new = sorted(set(now) - set(before)); changed = sorted(k for k in set(before) & set(now) if before[k] != now[k])
        return False, "human seats changed: left=%s new=%s changed=%s" % (gone, new, changed)
    waiting = sorted(k for k in before if not ready_now.get(k))
    if waiting:
        return False, "human seats no longer ready: %s" % waiting
    return True, "unchanged"


class Holder:
    """A placeholder seat: it joins a team with no units and never readies, so the relay cannot start before the helper has decided."""

    def __init__(self, url: str, code: str, team: str, state: Dict[str, Any]) -> None:
        self.url, self.code, self.team, self.state = url, code, team, state
        self.socket: Any = None
        self.seat_id = ""
        self.task: Any = None

    async def join(self) -> None:
        self.socket = await websockets.connect(self.url + "/ws", max_size=64 * 1024)
        await self.socket.send(json.dumps({"type": "join", "code": self.code, "seat": self.team, "client_version": "pk-fill-room"}))
        deadline = time.monotonic() + JOIN_REPLY_SECONDS
        while time.monotonic() < deadline:
            message = json.loads(await asyncio.wait_for(self.socket.recv(), JOIN_REPLY_SECONDS))
            if message.get("type") == "error":
                raise RuntimeError("join refused (%s): %s" % (message.get("code"), message.get("message", "")))
            if message.get("type") == "room_state" and message.get("seat_id"):
                self.seat_id = str(message["seat_id"])
                self.observe(message)
                self.task = asyncio.ensure_future(self.pump())
                return
        raise RuntimeError("no room_state after the join")

    def observe(self, message: Dict[str, Any]) -> None:
        if message.get("type") == "room_state":
            self.state["seats"] = list(message.get("seats") or [])
            self.state["team_size"] = int(message.get("team_size") or 1)
            if message.get("started"):
                self.state["started"] = True
        elif message.get("type") == "start":
            self.state["started"] = True
        elif message.get("type") == "error":
            self.state["errors"].append(str(message.get("code")))

    async def pump(self) -> None:
        try:
            async for raw in self.socket:
                try:
                    self.observe(json.loads(raw))
                except ValueError:
                    continue
        except Exception as error:  # noqa: BLE001 - the connection ending is reported by the waiting loops through the state
            self.state["errors"].append("holder_%s_closed:%s" % (self.team, type(error).__name__))

    async def leave(self) -> None:
        try:
            if self.socket is not None:
                await self.socket.send(json.dumps({"type": "leave"}))
                await asyncio.sleep(0.05)
                await self.socket.close()
        except Exception as error:  # noqa: BLE001
            log("WARN holder %s leave: %s" % (self.team, error))
        if self.task is not None:
            self.task.cancel()


async def wait_for_humans(state: Dict[str, Any], holder_ids: Set[str], settle: float, max_wait: float) -> Optional[List[Dict[str, Any]]]:
    """Every human seat ready and unchanged for `settle` seconds: the host pressed Start and every guest is in. None on timeout or when the room started without us."""
    deadline = time.monotonic() + max_wait
    last_sig: Optional[str] = None
    stable_since = 0.0
    while time.monotonic() < deadline:
        if state["started"]:
            return None
        humans = [seat for seat in state["seats"] if seat.get("team") in TEAMS and seat.get("seat_id") not in holder_ids]
        signature = json.dumps([(seat.get("seat_id"), seat.get("ready"), seat.get("units")) for seat in humans])
        if humans and all(seat.get("ready") for seat in humans):
            if signature != last_sig:
                last_sig, stable_since = signature, time.monotonic()
            elif time.monotonic() - stable_since >= settle:
                return humans
        else:
            last_sig = None
        await asyncio.sleep(POLL_SECONDS)
    return None


async def wait_until(predicate: Any, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.2)
    return False


async def fill(args: argparse.Namespace, relay_results: Optional[Dict[str, Any]] = None) -> int:
    if args.filler == "agent":
        log("ERROR filler=agent is not supported yet: the MCP bridge owns a whole side and cannot take part of a team (docs/ADR_unit_slot_fill_20261124.md). Use --filler computer, or join with an agent yourself and do not run this helper.")
        return EXIT_AGENT
    url = base_url(args.relay)
    code = args.code.strip().upper()
    state: Dict[str, Any] = {"seats": [], "team_size": 1, "started": False, "errors": []}
    holders = {team: Holder(url, code, team, state) for team in TEAMS}
    watcher = Holder(url, code, "spectator", state)   # a spectator does not hold the start back and stays after the placeholders left, so the helper sees the `start`
    tasks: Dict[str, Any] = {}
    release_placeholders = False   # red-team R2B-P1-1: only release placeholders after formation_unchanged passes; failure paths keep them until relay grace expires
    released_holders: Set[str] = set()
    try:
        try:
            await watcher.join()
        except Exception as error:  # noqa: BLE001
            log("ERROR the watching spectator seat could not join room %s: %s" % (code, error))
            return EXIT_JOIN
        for team in TEAMS:
            try:
                await holders[team].join()
            except Exception as error:  # noqa: BLE001
                log("ERROR placeholder seat %s could not join room %s: %s; placeholders kept; they expire by the relay's grace period and the room then starts without a fill" % (team, code, error))
                return EXIT_JOIN
        holder_ids = {holder.seat_id for holder in holders.values()}
        log("placeholders joined room %s as %s; waiting for every human seat to be ready (settle %.1f s, at most %d s)" % (code, sorted(holder_ids), args.settle, args.max_wait))
        humans = await wait_for_humans(state, holder_ids, args.settle, args.max_wait)
        if humans is None:
            log("ERROR %s; placeholders kept; they expire by the relay's grace period and the room then starts without a fill" % ("the room started without the helper" if state["started"] else "the human seats were not all ready in time"))
            return EXIT_WAIT
        size = int(state["team_size"])
        remainder = team_remainders(size, state["seats"], holder_ids)
        log("FORMATION team_size=%d humans=%s remainder=%s" % (size, [(s["seat_id"], s["team"], s.get("units")) for s in humans], remainder))
        named: Dict[str, List[str]] = {}
        for team in TEAMS:
            count = remainder[team]
            if count <= 0:
                continue
            picks, full = draw_heroes(code, team, count, taken_heroes(team, state["seats"], holder_ids), size)
            named[team] = picks
            log("FILL team=%s count=%d heroes=%s (seeded from the room code)" % (team, count, picks))
            command = ["node", os.path.join("scripts", "hybrid_seat_headless.js"), "--relay", url, "--code", code, "--team", team, "--heroes", ",".join(full),
                       "--claim", str(count), "--level", args.level, "--rng", str(seed_from(code, team)), "--speed", str(args.speed), "--max-s", str(args.max_seconds), "--gap-ms", "130"]
            import run_hybrid_room as hybrid   # heavy import, only when a filler is really needed
            tasks[team] = asyncio.ensure_future(hybrid.run_process_seat("headless", team, command, args.max_seconds + 60, os.path.join(ROOT, "logs_local", "fill_room_%s.log" % team)))
        known = holder_ids | {seat["seat_id"] for seat in humans}

        def fillers_ready() -> bool:
            for team, picks in named.items():
                seat = next((s for s in state["seats"] if s.get("team") == team and s.get("seat_id") not in known and s.get("ready")), None)
                if seat is None or list(seat.get("units") or []) != picks:
                    return False
            return True
        if named and not await wait_until(fillers_ready, args.join_wait):
            log("ERROR the filler seats were not ready in %d s (relay errors so far: %s); placeholders kept; they expire by the relay's grace period and the room then starts without a fill" % (args.join_wait, state["errors"]))
            return EXIT_WAIT
        filler_ids = {s["seat_id"] for s in state["seats"] if s.get("team") in TEAMS and s.get("seat_id") not in known}
        unchanged, why = formation_unchanged(humans, state["seats"], holder_ids, filler_ids)
        if not unchanged:
            log("ERROR the formation changed after the fill was planned (%s). Holding %d s, then giving up (exit %d); placeholders kept; they expire by the relay's grace period and the room then starts without a fill." % (why, HOLD_ON_CHANGE_SECONDS, EXIT_CHANGED))
            await asyncio.sleep(HOLD_ON_CHANGE_SECONDS)
            return EXIT_CHANGED
        release_placeholders = True
        for team in TEAMS:   # teams with nothing to fill first; the last placeholder to leave lets the relay start (it re-checks the start after a leave)
            if team not in named:
                released_holders.add(team)
                await holders[team].leave()
        for team in named:
            released_holders.add(team)
            await holders[team].leave()
        if not await wait_until(lambda: state["started"], START_WAIT_SECONDS):
            log("ERROR the relay did not start the match after the placeholders left (relay errors: %s)" % state["errors"])
            return EXIT_START
        log("match started; fillers: %s" % (sorted(tasks) or "none (every slot was claimed by a human)"))
        failed = False
        for team, task in tasks.items():
            result = await task
            data = result.data or {}
            ok = result.error is None and data.get("reason") == "game_over" and not data.get("errors")
            log("FILL RESULT team=%s ok=%s reason=%s winner=%s errors=%s error=%s" % (team, ok, data.get("reason"), data.get("winner", data.get("gameOver")), data.get("errors"), result.error))
            failed = failed or not ok
        if relay_results is not None:
            relay_results["state_errors"] = list(state["errors"])
        return EXIT_FAIL if failed else EXIT_OK
    except Exception as error:  # noqa: BLE001
        if not release_placeholders:
            log("ERROR fill failed: %s: %s; placeholders kept; they expire by the relay's grace period and the room then starts without a fill" % (type(error).__name__, error))
        else:
            log("ERROR fill failed: %s: %s" % (type(error).__name__, error))
        return EXIT_FAIL
    finally:
        for task in tasks.values():
            if not task.done():
                task.cancel()
        for team, holder in holders.items():
            if release_placeholders:
                if team not in released_holders:
                    released_holders.add(team)
                    await holder.leave()
            else:
                if getattr(holder, "task", None) is not None:
                    holder.task.cancel()
                if getattr(holder, "socket", None) is not None:
                    try:
                        await holder.socket.close()
                    except Exception:  # noqa: BLE001
                        pass
        await watcher.leave()


async def selftest(args: argparse.Namespace) -> int:
    """No phone: a spectator-made room of 3, two headless human seats on red (claim 1 and claim 2), the filler takes all of white. PASS needs every seat to finish with game_over and no relay error or hash difference."""
    import phone_room_check as pc
    import run_hybrid_room as hybrid
    relay = pc.PhoneRelay("127.0.0.1", 0, max_per_addr=40)   # the default allows 8 connections per address; six page seats plus the helper's three sockets are loopback peers of one machine (a phone through adb reverse is too)
    await relay.start()
    url = "ws://127.0.0.1:%d" % relay.bound_port
    spectator = await websockets.connect(url + "/ws", max_size=16 * 1024)
    await spectator.send(json.dumps({"type": "create_room", "seat": "spectator", "scene": "graveyard", "team_size": 3}))
    code = json.loads(await asyncio.wait_for(spectator.recv(), 5))["code"]
    log("SELFTEST room %s on %s" % (code, url))
    fill_args = argparse.Namespace(relay=url, code=code, filler="computer", settle=1.0, max_wait=120, join_wait=90, level=args.level, speed=8, max_seconds=args.max_seconds)
    fill_task = asyncio.ensure_future(fill(fill_args))
    room = relay.rooms[code]
    if not await wait_until(lambda: sum(1 for e in room.sessions.values() if e.get("team") in TEAMS) >= 2, 20):
        log("ERROR SELFTEST the placeholders did not join")
        return EXIT_FAIL

    scenarios = {   # (team, hero list of the page, units claimed); the heroes of one team never repeat
        "split": [("red", ["skeleton", "bat", "knight"], 1), ("red", ["wizard", "reaper", "bride"], 2)],   # red split 1+2, the filler takes all of white
        "both": [("red", ["skeleton", "bat", "knight"], 2), ("white", ["wizard", "reaper", "bride"], 1)],   # both teams have open slots: a filler on each team
        "none": [("red", ["skeleton", "bat", "knight"], 1), ("red", ["wizard", "reaper", "bride"], 1), ("red", ["hunchback", "hag", "bat"], 1),
                 ("white", ["knight", "bride", "skeleton"], 1), ("white", ["reaper", "hag", "wizard"], 1), ("white", ["bat", "hunchback", "knight"], 1)],   # six humans: no filler at all
    }

    def human(team: str, heroes: List[str], claim: int, name: str) -> Any:
        command = ["node", os.path.join("scripts", "hybrid_seat_headless.js"), "--relay", url, "--code", code, "--team", team, "--heroes", ",".join(heroes), "--claim", str(claim),
                   "--level", args.level, "--rng", "5", "--speed", "8", "--max-s", str(args.max_seconds), "--gap-ms", "130"]
        return asyncio.ensure_future(hybrid.run_process_seat("headless", team, command, args.max_seconds + 60, os.path.join(ROOT, "logs_local", "fill_room_selftest_%s.log" % name)))
    human_tasks = []
    for index, (team, heroes, claim) in enumerate(scenarios[args.scenario]):
        human_tasks.append(human(team, heroes, claim, "%s_%d" % (args.scenario, index)))
        await asyncio.sleep(1.0)
    code_fill = await fill_task
    results = [await task for task in human_tasks]
    errors = list(relay.error_log)
    mismatches = pc._hash_mismatch(room)
    seats = [(e.get("seat_id"), e.get("team"), e.get("units")) for e in room.sessions.values() if e.get("team") in TEAMS]
    owners = dict(getattr(room, "owners", {}) or {})
    human_ok = all(r.error is None and (r.data or {}).get("reason") == "game_over" and not (r.data or {}).get("errors") for r in results)
    for item in errors[:6]:
        log("SELFTEST relay error %s while %s" % (item.get("code"), json.dumps(item.get("while"))))
    log("SELFTEST RESULT fill_exit=%d humans_ok=%s relay_errors=%d out_of_sync=%d seats=%s owners=%s" % (code_fill, human_ok, len(errors), len(mismatches), seats, owners))
    expected_owner_count = sum(1 for value in owners.values() if value)
    ok = code_fill == EXIT_OK and human_ok and not errors and not mismatches and expected_owner_count == 6
    log("VERDICT %s (scenario %s, a 3v3 room: every seat reached game_over, 6 unit owners named, no relay error, no hash difference)" % ("PASS" if ok else "FAIL", args.scenario))
    try:
        await spectator.close()
    except Exception:  # noqa: BLE001
        pass
    return EXIT_OK if ok else EXIT_FAIL


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--relay", default="ws://localhost:8765", help="relay address without a path")
    parser.add_argument("--code", default="", help="the room code (not needed with --selftest)")
    parser.add_argument("--filler", choices=["computer", "agent"], default="computer")
    parser.add_argument("--settle", type=float, default=3.0, help="seconds every human seat must stay ready and unchanged before the remainder is computed")
    parser.add_argument("--max-wait", type=int, default=900, help="seconds to wait for the humans")
    parser.add_argument("--join-wait", type=int, default=90, help="seconds to wait for the filler seats to be ready")
    parser.add_argument("--level", choices=["easy", "normal", "hard"], default="normal")
    parser.add_argument("--speed", type=float, default=0, help="page clock speed of the headless filler (0 = real time)")
    parser.add_argument("--max-seconds", type=int, default=600)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--scenario", choices=["split", "both", "none"], default="split", help="selftest scenario: split = red 1+2 humans and the filler takes white; both = open slots on both teams; none = six humans, no filler")
    args = parser.parse_args()
    if not args.selftest and not args.code.strip():
        print("ERROR --code is required (or use --selftest)", file=sys.stderr)
        return EXIT_USAGE
    try:
        return asyncio.run(selftest(args) if args.selftest else fill(args))
    except KeyboardInterrupt:
        log("ERROR interrupted")
        return EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
