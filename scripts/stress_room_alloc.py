#!/usr/bin/env python3
"""ROOM-FLOW R10: seeded, reproducible stress test of the lobby logic of scripts/pk_relay.py (in-process relay, real sockets).

Many rooms of 1v1, 2v2 and 3v3 get a seeded random mix of: join (red, white, auto, spectator, no seat, bad seat), claim and unit lists, ready and
unready, room options, kick, leave, abrupt close, reset_lobby, MCP-declared joins. After every step the relay's own state is checked:
 - held places of a team never exceed the team size (team matches; a seat that sent no claim holds nothing until it lists units);
 - seat ids and tokens are unique; the host is a real player seat while the match has not started and players exist;
 - no unhandled exception was logged.
Then a race: many clients ask for the last free place at the same moment: exactly one may get it.
Same seed = same action sequence.   usage: stress_room_alloc.py [--seed 1] [--steps 3000] [--rooms 6] [--relay path]   exit 1 on any violation
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import logging
import os
import random
import sys

import websockets

HERE = os.path.dirname(os.path.abspath(__file__))
HEROES = ["skeleton", "wizard", "bat", "hag", "knight"]


def load_relay(path):
    spec = importlib.util.spec_from_file_location("pk_relay_under_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def plan(seed, steps, rooms):
    rng = random.Random(seed)
    out = []
    for step in range(steps):
        kind = rng.choice(["join", "join", "join", "ai", "invite", "invite", "accept", "accept", "cancel", "move", "move", "begin", "begin", "ready", "ready", "unready", "options", "kick", "leave", "drop", "reset", "create"])
        out.append({"step": step, "kind": kind, "room": rng.randrange(rooms), "actor": rng.randrange(5), "seat": rng.choice(["red", "white", "auto", "spectator", None, "blue"]),
                    "claim": rng.choice([None, None, 1, 2, 3, 0, 99]), "units": rng.sample(HEROES, rng.randint(0, 3)), "size": rng.choice([1, 2, 2, 3, 3]),
                    "mcp": rng.random() < 0.2, "opt": rng.choice([True, False, "x"]), "target": rng.choice(["red-1", "red-2", "red-3", "white-1", "white-2", "white-3", "nobody"])})
    return out


def check(relay):
    problems = []
    for code, room in relay.rooms.items():
        seen_ids, seen_tokens = set(), set()
        for token, seat in room.sessions.items():
            if seat["seat_id"] in seen_ids or token in seen_tokens:
                problems.append("%s: duplicate seat id or token (%s)" % (code, seat["seat_id"]))
            seen_ids.add(seat["seat_id"])
            seen_tokens.add(token)
        if room.team_match:
            for team in ("red", "white"):
                held = room.held_places(team)
                if held > room.team_size:
                    problems.append("%s: team %s holds %d places, size %d" % (code, team, held, room.team_size))
        players = [seat["seat_id"] for seat in room.sessions.values() if seat["team"] != "spectator"]
        if players and not room.started and room.host_seat_id not in players:
            problems.append("%s: host %r is not a player seat %s" % (code, room.host_seat_id, players))
        agents = [seat for seat in room.sessions.values() if seat.get("agent")]
        if not room.started:
            inviters = [ticket["by"] for ticket in room.invites.values()] + [seat["invited_by"] for seat in agents]
            people = {seat["seat_id"]: seat["team"] for seat in room.sessions.values() if seat["team"] != "spectator" and not seat.get("ai") and not seat.get("agent")}
            if len(inviters) != len(set(inviters)):
                problems.append("%s: a player holds more than one invite or agent %s" % (code, inviters))
            for ticket in room.invites.values():
                if people.get(ticket["by"]) != ticket["team"]:
                    problems.append("%s: invite of %s for team %s, the inviter is %s" % (code, ticket["by"], ticket["team"], people.get(ticket["by"])))
            for seat in agents:
                if people.get(seat["invited_by"]) != seat["team"]:
                    problems.append("%s: agent %s without its inviter on its team" % (code, seat["seat_id"]))
        elif room.invites:
            problems.append("%s: open invites in a started match" % code)
        if room.countdown is not None and not room.countdown.done() and not relay._lobby_due(room):
            problems.append("%s: a countdown runs although the room is not due" % code)
        if room.lobby and room.started and room.team_match and not hasattr(room, "_checked_start"):
            room._checked_start = True
            if len(room.owners) != 2 * room.team_size:
                problems.append("%s: a lobby room started with places nobody owns %s" % (code, room.owners))
        if room.host_seat_id in [seat["seat_id"] for seat in agents]:
            problems.append("%s: an agent is the host" % code)
        ai = [seat["seat_id"] for seat in room.sessions.values() if seat.get("ai")]
        if ai and not room.started and (room.host_seat_id in ai or room.host_seat_id not in players):
            problems.append("%s: AI seats %s without a person as host (host %r)" % (code, ai, room.host_seat_id))
    return problems


class LogCatcher(logging.Handler):
    def __init__(self):
        super().__init__(logging.ERROR)
        self.records = []

    def emit(self, record):
        self.records.append(self.format(record))


async def run(args):
    module = load_relay(args.relay)
    relay = module.RelayServer("127.0.0.1", 0, max_per_addr=100000, max_connects_per_min=10 ** 7, max_connections=100000, max_rooms=10000, seat_grace_seconds=0, max_wrong_per_addr=10 ** 7, countdown_seconds=0.005)
    catcher = LogCatcher()
    logging.getLogger().addHandler(catcher)
    await relay.start()
    url = "ws://127.0.0.1:%d/ws" % relay.bound_port
    actions = plan(args.seed, args.steps, args.rooms)
    sockets = {}   # (room, actor) -> socket
    codes = {}     # room -> code
    failures = []

    readers = []

    async def drain(sock):
        try:
            async for _ in sock:
                pass
        except Exception:  # noqa: BLE001  (a closed socket is part of the test)
            pass

    def listen(sock):   # a real client reads what it is sent; one that does not makes the relay's send wait and stalls the run
        readers.append(asyncio.ensure_future(drain(sock)))

    async def open_socket():
        return await websockets.connect(url, max_size=module.MAX_MESSAGE_BYTES)

    async def send(key, message):
        sock = sockets.get(key)
        if sock is None:
            return
        try:
            await sock.send(json.dumps(message))
        except Exception:  # noqa: BLE001  (a closed socket is part of the test)
            sockets.pop(key, None)

    try:
        for action in actions:
            key = (action["room"], action["actor"])
            kind = action["kind"]
            try:
                if kind == "create" or (kind == "join" and action["room"] not in codes):
                    sock = await open_socket()
                    sockets[key] = sock
                    message = {"type": "create_room", "seat": "red", "team_size": action["size"], "client_version": "stress", "lobby": not action["mcp"] and action["step"] % 2 == 0}
                    if action["claim"] is not None:
                        message["claim"] = action["claim"]
                    if action["units"]:
                        message["units"] = action["units"]
                    await sock.send(json.dumps(message))
                    reply = json.loads(await asyncio.wait_for(sock.recv(), 2))
                    if reply.get("type") == "room_state" and reply.get("code"):
                        codes[action["room"]] = reply["code"]
                    listen(sock)
                elif kind == "join":
                    if key in sockets:
                        continue
                    sock = await open_socket()
                    sockets[key] = sock
                    message = {"type": "join", "code": codes[action["room"]], "client_version": "stress"}
                    if action["seat"] is not None:
                        message["seat"] = action["seat"]
                    if action["claim"] is not None:
                        message["claim"] = action["claim"]
                    if action["units"]:
                        message["units"] = action["units"]
                    if action["mcp"]:
                        message["client_kind"] = "mcp"
                    await sock.send(json.dumps(message))
                    listen(sock)
                elif kind == "ai":
                    # ROOM-FLOW R9: the host's filler joins with the host's token (read from the in-process relay); now and then with a wrong one
                    if key in sockets or action["room"] not in codes:
                        continue
                    target = relay.rooms.get(codes[action["room"]])
                    if target is None:
                        continue
                    proof = next((token for token, seat in target.sessions.items() if seat["seat_id"] == target.host_seat_id), "none")
                    sock = await open_socket()
                    sockets[key] = sock
                    message = {"type": "join", "code": target.code, "seat": action["seat"] or "auto", "client_version": "stress",
                               "ai_host_token": "wrong" if action["mcp"] else proof}
                    if action["units"]:
                        message["units"] = action["units"]
                    await sock.send(json.dumps(message))
                    listen(sock)
                elif kind == "invite":
                    await send(key, {"type": "invite", "note": "go"})
                elif kind == "cancel":
                    await send(key, {"type": "invite_cancel"})
                elif kind == "accept":
                    # ROOM-FLOW R11: an agent takes an open ticket (read from the in-process relay); now and then a stale or made-up one
                    if key in sockets or action["room"] not in codes:
                        continue
                    target = relay.rooms.get(codes[action["room"]])
                    if target is None:
                        continue
                    open_ids = sorted(target.invites, key=lambda ticket_id: target.invites[ticket_id]["by"])
                    ticket_id = "red.made-up" if action["mcp"] or not open_ids else open_ids[action["actor"] % len(open_ids)]
                    sock = await open_socket()
                    sockets[key] = sock
                    message = {"type": "join", "code": target.code, "client_version": "stress", "client_kind": "mcp", "invite": ticket_id}
                    if action["units"]:
                        message["units"] = action["units"][:1]
                    await sock.send(json.dumps(message))
                    listen(sock)
                elif kind == "move":
                    await send(key, {"type": "move", **({"team": action["seat"]} if action["seat"] is not None and action["step"] % 2 else {}), **({"claim": action["claim"]} if action["claim"] is not None else {})})
                elif kind == "begin":
                    # the actor who is the host (read from the in-process relay) presses start or cancels it
                    target = relay.rooms.get(codes.get(action["room"], ""))
                    host_key = None
                    if target is not None:
                        host_sock = next((sock for sock, seat in target.clients.items() if seat["seat_id"] == target.host_seat_id), None)
                        if host_sock is not None:
                            await relay._dispatch(host_sock, target, target.clients[host_sock], {"type": "begin", "on": action["actor"] != 0}, [])
                elif kind == "ready":
                    await send(key, {"type": "ready", **({"units": action["units"]} if action["units"] else {})})
                elif kind == "unready":
                    await send(key, {"type": "unready"})
                elif kind == "options":
                    await send(key, {"type": "room_options", "allow_ai": action["opt"], "allow_mcp": action["opt"]})
                elif kind == "kick":
                    await send(key, {"type": "kick", "seat_id": action["target"]})
                elif kind == "leave":
                    await send(key, {"type": "leave"})
                    sockets.pop(key, None)
                elif kind == "drop":
                    sock = sockets.pop(key, None)
                    if sock is not None:
                        await sock.close()
                elif kind == "reset":
                    await send(key, {"type": "reset_lobby"})
            except (OSError, asyncio.TimeoutError, websockets.exceptions.WebSocketException):
                sockets.pop(key, None)
            await asyncio.sleep(0.004)
            for problem in check(relay):
                failures.append({"step": action["step"], "action": {k: v for k, v in action.items() if k != "units"}, "problem": problem})
            if failures or catcher.records:
                break
        if catcher.records and not failures:
            failures.append({"step": "log", "problem": "unhandled error logged: " + catcher.records[0][:300]})
        # the race for the last free place
        if not failures:
            host = await open_socket()
            await host.send(json.dumps({"type": "create_room", "seat": "red", "team_size": 2, "units": ["skeleton"], "client_version": "race"}))
            code = json.loads(await asyncio.wait_for(host.recv(), 2))["code"]
            listen(host)

            async def racer(i):
                sock = await open_socket()
                await sock.send(json.dumps({"type": "join", "code": code, "seat": "red", "units": ["wizard"], "client_version": "race%d" % i}))
                for _ in range(10):
                    m = json.loads(await asyncio.wait_for(sock.recv(), 2))
                    if m.get("type") in ("room_state", "error"):
                        return sock, m
                return sock, {}

            results = await asyncio.gather(*(racer(i) for i in range(12)))
            winners = [m for _, m in results if m.get("type") == "room_state"]
            losers = [m for _, m in results if m.get("type") == "error" and m.get("code") == "team_full"]
            if len(winners) != 1 or len(winners) + len(losers) != 12:
                failures.append({"step": "race", "problem": "12 clients raced for 1 free place: %d won, %d refused with team_full" % (len(winners), len(losers))})
            for sock, _ in results:
                await sock.close()
            await host.close()
    finally:
        for sock in list(sockets.values()):
            try:
                await sock.close()
            except Exception:  # noqa: BLE001
                pass
        for task in readers:
            task.cancel()
        await relay.close()
        logging.getLogger().removeHandler(catcher)
    return actions, failures


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--rooms", type=int, default=6)
    ap.add_argument("--relay", default=os.path.join(HERE, "pk_relay.py"))
    ap.add_argument("--selfcheck", action="store_true")
    args = ap.parse_args()
    if json.dumps(plan(args.seed, args.steps, args.rooms), sort_keys=True) != json.dumps(plan(args.seed, args.steps, args.rooms), sort_keys=True) or \
            json.dumps(plan(args.seed, args.steps, args.rooms)) == json.dumps(plan(args.seed + 1, args.steps, args.rooms)):
        print("RESULT FAIL the sequence is not reproducible or not seed-dependent")
        return 1
    if args.selfcheck:
        print("RESULT PASS seed %d reproducible" % args.seed)
        return 0
    actions, failures = asyncio.run(run(args))
    print(json.dumps({"seed": args.seed, "steps": len(actions), "failures": len(failures)}))
    for failure in failures[:5]:
        print("FAILURE", json.dumps(failure, default=str)[:400])
    if failures:
        print("REPRODUCE python3 -B scripts/stress_room_alloc.py --seed %d --steps %d --rooms %d" % (args.seed, args.steps, args.rooms))
    print("RESULT " + ("FAIL" if failures else "PASS"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
