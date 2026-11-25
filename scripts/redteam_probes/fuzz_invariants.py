"""Seeded random lobby fuzzer against the real relay (in-process, real sockets). Known breaks F2/F3/F5 are avoided on purpose
(1v1 joins use seat=auto, ready never sends team_size, the host is always a red player).
Run: python3 -B scripts/redteam_probes/fuzz_invariants.py SEED [OPS]"""
import os
import asyncio
import json
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h import H  # noqa: E402

HEROES = ["skeleton", "wizard", "bat", "knight", "bride", "hunchback", "reaper", "hag"]


def check(relay, note):
    bad = []
    for code, room in relay.rooms.items():
        players = [s for s in room.sessions.values() if s["team"] in ("red", "white")]
        for team in ("red", "white"):
            if room.team_match and room.held_places(team) > room.team_size:
                bad.append("held %s=%d > size %d" % (team, room.held_places(team), room.team_size))
            if not room.team_match and room.team_count(team) > 1:
                bad.append("1v1 team %s has %d seats" % (team, room.team_count(team)))
        if not room.started and players:
            host = next((s for s in room.sessions.values() if s["seat_id"] == room.host_seat_id), None)
            humans = [s for s in players if not s.get("ai") and not s.get("agent")]
            if humans and (host is None or host.get("ai") or host.get("agent") or host["team"] == "spectator"):
                bad.append("host %s is not a person player (humans=%s)" % (room.host_seat_id, [s["seat_id"] for s in humans]))
        if room.started and room.invites:
            bad.append("open invite after start")
        by = {}
        for s in room.sessions.values():
            if s.get("invited_by"):
                by[s["invited_by"]] = by.get(s["invited_by"], 0) + 1
        for t in room.invites.values():
            by[t["by"]] = by.get(t["by"], 0) + 1
        for k, v in by.items():
            if v > 1:
                bad.append("player %s has %d agents/invites" % (k, v))
            if k not in {s["seat_id"] for s in room.sessions.values()} and not room.started:
                bad.append("agent/invite of absent player %s" % k)
        ids = [s["seat_id"] for s in room.sessions.values()]
        if len(ids) != len(set(ids)):
            bad.append("duplicate seat ids %s" % ids)
    return ["%s: %s" % (note, b) for b in bad]


async def main(seed, ops):
    rng = random.Random(seed)
    size = rng.choice([1, 2, 3])
    found = []
    async with H(seat_grace_seconds=1.5, invite_seconds=3, agent_pick_seconds=2, countdown_seconds=0.4) as h:
        host, code, _ = await h.create(team_size=size, claim=1, lobby=rng.random() < 0.6, units=[rng.choice(HEROES)])
        clients = [host]
        tokens = {}
        tickets = []
        for i in range(ops):
            c = rng.choice(clients)
            op = rng.choice(["join", "join", "ready", "unready", "move", "invite", "ticket", "cancel", "kick", "leave", "drop", "resume",
                             "begin", "options", "name", "reset", "spectate"])
            st = c.last("room_state", lambda m: "seat_token" in m)
            if st:
                tokens[st["seat_token"]] = True
            try:
                if op == "join":
                    n = await h.join(code, seat="auto" if size == 1 or rng.random() < 0.5 else rng.choice(["red", "white"]), claim=rng.randint(1, 3),
                                     units=rng.sample(HEROES, rng.randint(0, size)))
                    clients.append(n)
                elif op == "spectate":
                    clients.append(await h.join(code, seat="spectator"))
                elif op == "ready":
                    await c.send(type="ready", units=rng.sample(HEROES, rng.randint(1, size)))
                elif op == "unready":
                    await c.send(type="unready")
                elif op == "move":
                    m = {"type": "move"}
                    if rng.random() < 0.5:
                        m["team"] = rng.choice(["red", "white"])
                    if rng.random() < 0.6:
                        m["claim"] = rng.randint(1, 3)
                    await c.send(**m)
                elif op == "invite":
                    await c.send(type="invite", note="n")
                    t = c.last("invite_created")
                    if t:
                        tickets.append(t["invite"])
                elif op == "ticket" and tickets:
                    clients.append(await h.join(code, invite=rng.choice(tickets)))
                elif op == "cancel":
                    await c.send(type="invite_cancel")
                elif op == "kick":
                    room = h.room(code)
                    if room and room.sessions:
                        await host.send(type="kick", seat_id=rng.choice([s["seat_id"] for s in room.sessions.values()]))
                elif op == "leave":
                    if c is not host or rng.random() < 0.2:
                        await c.send(type="leave")
                elif op == "drop":
                    if c is not host or rng.random() < 0.2:
                        await c.close()
                elif op == "resume" and tokens:
                    n = await h.open()
                    await n.send(type="resume", seat_token=rng.choice(list(tokens)), last_seq=0)
                    clients.append(n)
                elif op == "begin":
                    for x in clients:
                        await x.send(type="begin", on=rng.random() < 0.8)
                        break
                elif op == "options":
                    await c.send(type="room_options", allow_ai=rng.random() < 0.7, allow_mcp=rng.random() < 0.7)
                elif op == "name":
                    await c.send(type="set_name", name="".join(chr(rng.randint(0x20, 0x2FFF)) for _ in range(12)))
                elif op == "reset":
                    await c.send(type="reset_lobby")
            except Exception as exc:  # noqa: BLE001 - a closed socket is part of the game
                if "ConnectionClosed" not in type(exc).__name__ and "closed" not in str(exc).lower():
                    found.append("op %d %s raised %r" % (i, op, exc))
            for b in check(h.relay, "seed %d op %d (%s, size %d)" % (seed, i, op, size)):
                if b.split(": ", 1)[1] not in {x.split(": ", 1)[1] for x in found}:
                    found.append(b)
            if code not in h.relay.rooms:
                break
        await asyncio.sleep(0.2)
        room = h.room(code)
        print("ops run=%d room alive=%s seats=%s started=%s" % (i + 1, room is not None, room and [(s["seat_id"], s["claim"], len(s["units"]), s.get("agent"), s.get("ai")) for s in room.sessions.values()], room and room.started))
    print("seed %d size %d: %d distinct invariant breaks" % (seed, size, len(found)))
    for b in found[:8]:
        print("   ", b)


asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 1, int(sys.argv[2]) if len(sys.argv) > 2 else 120))
