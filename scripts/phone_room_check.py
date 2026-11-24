#!/usr/bin/env python3
"""Phone room check (gap G1, owner 2026-11-18: "is the MCP really connected?").

The phone PAGE is the host: you tap Friends -> Create room and Start Battle on the real phone. This script runs the relay on a fixed port (the phone reaches it through
`adb reverse tcp:8765 tcp:8765`), waits for the first room, and joins it as the white seat with one of two opponents:
  --white headless   the page's own computer seat (scripts/hybrid_seat_headless.js): proves phone <-> page
  --white mcp        the real MCP bridge over stdio (scripts/mcp_stdio_server.py --connect), driven through its public tools only (run_hybrid_room.McpSeat); the bridge judges with the real page (scripts/page_judge_seat.js), so this proves phone <-> MCP bridge, not a human-run agent
It counts every relay error and every round-hash mismatch and prints one verdict line. Exit code 0 only when: the match reached its end with reason game_over and no seat error, or (with --turns N) at
least N turns were played; AND no relay error; AND at least one round where both seats sent a round_hash and all hashes are equal.
--selftest plumbing   no phone: a Python client sends create_room and ready; stops at the relay's start (checks the plumbing only)
--selftest stall      no phone: the phone only creates the room and readies, never plays; the real path runs and the verdict must be FAIL (negative control for a seat that times out)
--selftest full       no phone: a headless RED page seat stands in for the phone host in a spectator-made room of 2 units; then the normal path runs with a played match
With --require-phone the red seat's User-Agent must be a mobile browser; without it a PASS does NOT show that the red seat is a phone (the selftests use a headless page as red).
NOT proven by this script: a real tap on the real phone, the phone page's own UI flow, a human-run agent, the speed of a real phone page (the stand-in seats run at speed 8 or 0, a phone runs at speed 1: a full match at that speed was never run here), and anything the phone does while the screen is off. A phone that disconnects mid-match is detected only after --max-seconds (disconnect counts as leaving).

Run it from your own terminal (sockets cannot start in the Claude sandbox):
  adb reverse tcp:8765 tcp:8765 ; adb reverse tcp:8080 tcp:8080        (page server: python3 -B scripts/dev_server.py 8080)
  python3 -B scripts/phone_room_check.py --white mcp --turns 6
  then on the phone open http://localhost:8080/index.html , Friends -> Create room, Start Battle, play a few turns.
The room code and the join command for a real agent are printed too, so the same room can be joined by hand (scripts/make_agent_join_config.py).
Log: logs_local/phone_room_check.log. Never reads a key or token.
"""
import argparse
import asyncio
import json
import os
import re
import signal
import sys
import time
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import run_hybrid_room as hybrid  # noqa: E402  (CountingRelay, McpSeat, seat_command helpers)

LOG_PATH = os.path.join(ROOT, "logs_local", "phone_room_check.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)


def log(message: str) -> None:
    line = "%s %s" % (time.strftime("%H:%M:%S"), message)
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def default_heroes(size: int) -> List[str]:
    pool = ["wizard", "knight", "hag"]
    return pool[:max(1, size)]


async def wait_for_room(relay: Any, timeout: float) -> Optional[Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for room in relay.rooms.values():
            if any(entry.get("team") == "red" and entry.get("connected") and entry.get("ready") for entry in room.sessions.values()):
                return room   # red is ready: its units are known (a 1v1 page sends them with ready)
        await asyncio.sleep(0.5)
    return None


def is_phone_client(user_agent: Optional[str]) -> bool:
    """True for a mobile browser's User-Agent (Chrome on Android, Safari on iPhone). Node's WebSocket, Python's websockets and desktop Chrome are not phones."""
    return bool(re.search(r"Android|iPhone|iPad|Mobile", user_agent or ""))


def decide(finished: bool, reached: bool, turns: int, relay_errors: int, out_of_sync: int, hash_rounds_both: int, hash_disagree: List[Any],
           seat_error: Optional[str], red_user_agent: Optional[str], require_phone: bool) -> Dict[str, Any]:
    """The verdict as a pure function (red-team R10A-2: eight of nine mutants of the inline version survived). PASS only when every reason list entry below is absent."""
    reasons: List[str] = []
    if not (finished or reached):
        reasons.append("the match neither finished with game_over nor reached the requested number of turns")
    if turns < 1:
        reasons.append("no turn was played")
    if relay_errors > 0:
        reasons.append("%d relay error(s)" % relay_errors)
    if out_of_sync > 0:
        reasons.append("%d out_of_sync message(s)" % out_of_sync)
    if hash_rounds_both < 1:
        reasons.append("no round had a round_hash from both seats: the two pages were never compared")
    if hash_disagree:
        reasons.append("round hashes disagree in round(s) %s" % hash_disagree)
    if seat_error:
        reasons.append("white seat: %s" % seat_error)
    if require_phone and not is_phone_client(red_user_agent):
        reasons.append("the red seat is not a phone browser (User-Agent: %s)" % (red_user_agent or "none"))
    return {"ok": not reasons, "reasons": reasons}


class PhoneRelay(hybrid.CountingRelay):
    """The counting relay that also remembers the User-Agent of the connection that created or joined each team (the relay itself records no client identity)."""
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.user_agent_by_team: Dict[str, str] = {}

    async def _dispatch(self, websocket: Any, room: Any, entry: Any, message: Dict[str, Any], wrong_code_times: list) -> tuple:
        result = await super()._dispatch(websocket, room, entry, message, wrong_code_times)
        if message.get("type") in ("create_room", "join", "resume") and result[1] is not None:
            headers = getattr(getattr(websocket, "request", None), "headers", None)
            agent = headers.get("User-Agent") if headers is not None else None
            if agent:
                self.user_agent_by_team[str(result[1].get("team"))] = str(agent)[:200]
        return result


async def _stop(task: Any) -> None:
    if task is None:
        return
    if not task.done():
        task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):  # noqa: BLE001 - a seat stopped on purpose
        pass


def _hash_rounds(room: Any) -> Dict[str, Any]:
    """Rounds where BOTH seats sent a round_hash, and which of them disagree (pk_relay.Room.round_hashes: round -> seat_id -> hash)."""
    both = {number: hashes for number, hashes in getattr(room, "round_hashes", {}).items() if len(hashes) >= 2}
    bad = [number for number, hashes in both.items() if len(set(hashes.values())) > 1]
    return {"rounds_with_two": len(both), "disagree": bad}


async def main_async(args: argparse.Namespace) -> int:
    relay = PhoneRelay("127.0.0.1", args.relay_port)
    await relay.start()
    port = relay.bound_port
    url = "ws://127.0.0.1:%d" % port
    log("relay listening on %s. Phone side: adb reverse tcp:%d tcp:%d ; open http://localhost:8080/index.html?relay=ws://localhost:%d on the phone" % (url, port, port, port))
    fake_phone: Any = None
    red_task: Any = None
    seat_task: Any = None
    if args.selftest in ("plumbing", "stall"):   # a Python client plays the phone's first two messages (create_room, ready); "stall" then runs the real path with a phone that never plays (must FAIL)
        from pk_relay_client import RelayClient
        fake_phone = RelayClient(url + "/ws", None, "red")
        await fake_phone.connect()
        await fake_phone.send({"type": "ready"})
        log("SELFTEST plumbing: a Python client created the room and is ready; no phone involved")
    elif args.selftest == "full":     # a spectator makes a room of 2 units; a headless RED page seat stands in for the phone host
        import websockets
        spectator = await websockets.connect(url + "/ws", max_size=16 * 1024)
        create = {"type": "create_room", "seat": "spectator", "scene": "graveyard"}
        if args.selftest_size > 1:
            create["team_size"] = args.selftest_size   # size 1 is the default room the phone creates: no team_size field at all
        await spectator.send(json.dumps(create))
        first = json.loads(await asyncio.wait_for(spectator.recv(), 5))
        fake_phone = spectator
        red_cmd = ["node", os.path.join("scripts", "hybrid_seat_headless.js"), "--relay", url, "--code", first["code"], "--team", "red", "--heroes", ",".join(["skeleton", "bat", "knight"][:args.selftest_size]),
                   "--level", args.level, "--rng", "5", "--speed", "8", "--max-s", str(args.max_seconds), "--gap-ms", "130"]
        red_task = asyncio.ensure_future(hybrid.run_process_seat("headless", "red", red_cmd, args.max_seconds + 30, os.path.join(ROOT, "logs_local", "phone_room_red.log")))
        log("SELFTEST full: a spectator made room %s and a headless RED page seat stands in for the phone host" % first["code"])
    log("waiting up to %d s for the phone to Create room and press Start Battle ..." % args.wait_room)
    try:
        room = await wait_for_room(relay, args.wait_room)
        if room is None:
            log("ERROR no room with a ready red seat appeared in time (is adb reverse set, is the page opened from http://localhost:8080, did you press Start Battle ?)")
            return 1
        size = int(getattr(room, "team_size", 1) or 1)
        code = room.code
        log("room %s found (team size %d). Join command for a real agent: python3 -B scripts/make_agent_join_config.py --relay ws://localhost:%d/ws --code %s" % (code, size, port, code))
        heroes = default_heroes(size)
        red_units: List[str] = []
        for entry in room.sessions.values():
            if entry.get("team") == "red":
                red_units = list(entry.get("units") or [])
        red_heroes = (red_units + ["skeleton"] * size)[:size]
        log("red units from the room: %s" % (red_units or "none sent (a 1v1 page may send none: skeleton is assumed for the MCP seat's hero list)"))
        started = time.monotonic()
        white_log = os.path.join(ROOT, "logs_local", "phone_room_white.log")
        if args.white == "headless":
            cmd = ["node", os.path.join("scripts", "hybrid_seat_headless.js"), "--relay", url, "--code", code, "--team", "white", "--heroes", ",".join(heroes),
                   "--level", args.level, "--rng", "7", "--speed", "8" if args.selftest == "full" else "0", "--max-s", str(args.max_seconds), "--gap-ms", "130"]
            seat_task = asyncio.ensure_future(hybrid.run_process_seat("headless", "white", cmd, args.max_seconds + 30, white_log))
        else:
            mcp = hybrid.McpSeat("white", url, code, {"red": red_heroes, "white": heroes}, args.level, 7, 0.4, white_log, claude=False, page_judge="on", page_speed=8.0)
            seat_task = asyncio.ensure_future(mcp.play(args.max_seconds))

        if args.selftest == "plumbing":
            deadline = time.monotonic() + 40
            while time.monotonic() < deadline and not getattr(room, "started", False) and not seat_task.done():
                await asyncio.sleep(0.5)
            white_in = any(e.get("team") == "white" and e.get("connected") for e in room.sessions.values())
            started_ok = bool(getattr(room, "started", False)) and white_in
            await _stop(seat_task)
            await fake_phone.close()
            errors = list(relay.error_log)
            log("SELFTEST RESULT room_started=%s white_joined=%s relay_errors=%d (white=%s)" % (getattr(room, "started", False), white_in, len(errors), args.white))
            log("VERDICT %s (plumbing only: the room was found, the white seat joined, the relay started the match; no turn was played)" % ("PASS" if started_ok and not errors else "FAIL"))
            return 0 if started_ok and not errors else 1

        reached = False
        while not seat_task.done():
            if _count(room, "end_turn") >= args.turns:
                reached = True
                break
            await asyncio.sleep(1.0)
        finished = False
        seat_error: Optional[str] = None
        if reached:
            await _stop(seat_task)
        else:
            result = seat_task.result()
            data = result.data or {}
            finished = result.error is None and data.get("reason") == "game_over" and not data.get("errors")
            if not finished:
                seat_error = result.error or "white seat ended with reason=%s errors=%s exit_code=%s" % (data.get("reason"), data.get("errors"), result.exit_code)
        await _stop(red_task)
        if fake_phone is not None:
            try:
                await fake_phone.close()
            except Exception:  # noqa: BLE001
                pass
        errors = list(relay.error_log)
        turns = _count(room, "end_turn")
        actions = _count(room, "action")
        out_of_sync = _hash_mismatch(room)
        hashes = _hash_rounds(room)
        log("RESULT white=%s turns=%d actions=%d relay_errors=%d out_of_sync=%d hash_rounds_with_both_seats=%d hash_disagreements=%s seat_error=%s seconds=%d" % (
            args.white, turns, actions, len(errors), len(out_of_sync), hashes["rounds_with_two"], hashes["disagree"], seat_error, time.monotonic() - started))
        for item in errors[:5]:
            log("ERROR relay %s while %s" % (item.get("code"), json.dumps(item.get("while"))))
        red_agent = relay.user_agent_by_team.get("red")
        log("red seat client: %s%s" % (red_agent or "unknown", " (a mobile browser)" if is_phone_client(red_agent) else " (NOT a mobile browser)"))
        verdict = decide(finished, reached, turns, len(errors), len(out_of_sync), hashes["rounds_with_two"], hashes["disagree"], seat_error, red_agent, args.require_phone)
        for reason in verdict["reasons"]:
            log("ERROR %s" % reason)
        log("VERDICT %s (%s)" % ("PASS" if verdict["ok"] else "FAIL", "match finished with game_over" if finished else ("%d turns played" % turns if reached else "stopped early")))
        ok = verdict["ok"]
        return 0 if ok else 1
    finally:
        await _stop(seat_task)
        await _stop(red_task)
        await relay.close()


def _count(room: Any, kind: str) -> int:
    return sum(1 for message in getattr(room, "log", []) if message.get("type") == kind)


def _hash_mismatch(room: Any) -> List[Dict[str, Any]]:
    return [m for m in getattr(room, "log", []) if m.get("type") == "out_of_sync"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--white", choices=["headless", "mcp"], default="headless")
    parser.add_argument("--level", default="normal", choices=["easy", "normal", "hard"])
    parser.add_argument("--relay-port", type=int, default=8765)
    parser.add_argument("--wait-room", type=int, default=300, help="seconds to wait for the phone to create the room")
    parser.add_argument("--max-seconds", type=int, default=600)
    parser.add_argument("--turns", type=int, default=6, help="pass after this many turns even if the match is not over")
    parser.add_argument("--require-phone", action="store_true", help="FAIL unless the red seat connected with a mobile browser User-Agent (use it for the real phone run)")
    parser.add_argument("--selftest-size", type=int, default=1, choices=[1, 2, 3], help="selftest full: units per team of the stand-in room; 1 is the default room the phone creates")
    parser.add_argument("--selftest", nargs="?", const="plumbing", choices=["plumbing", "full", "stall"], default=None, help="no phone: plumbing = a Python client plays create_room and ready, stops at the relay's start; full = a headless RED page seat stands in for the phone host and a match is played; stall = the phone only readies and never plays, the verdict must be FAIL (negative control)")
    args = parser.parse_args()
    async def runner() -> int:
        loop = asyncio.get_running_loop()
        task = asyncio.current_task()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, task.cancel)   # the finally blocks of main_async stop the seat processes
        return await main_async(args)
    try:
        return asyncio.run(runner())
    except (KeyboardInterrupt, asyncio.CancelledError):
        log("stopped by the user")
        return 130
    except Exception as error:  # noqa: BLE001 - the verdict must say why
        log("ERROR %s: %s" % (type(error).__name__, error))
        return 1


if __name__ == "__main__":
    sys.exit(main())
