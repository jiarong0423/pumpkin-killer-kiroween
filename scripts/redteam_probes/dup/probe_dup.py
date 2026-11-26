#!/usr/bin/env python3
"""Red-team probes for the lobby duplicate-hero rule, host hand-over and move cap. Run from the repo root."""
import asyncio
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
import websockets  # noqa: E402
from pk_relay import MAX_MESSAGE_BYTES, RelayServer  # noqa: E402

OUT = []


def verdict(name, broken, observed, expected):
    OUT.append((name, broken))
    print("[%s] %s\n    observed: %s\n    expected: %s" % ("BREAK" if broken else "HELD", name, observed, expected))


class C:
    def __init__(self, ws):
        self.ws, self.inbox = ws, []
        self.task = asyncio.ensure_future(self._pump())

    async def _pump(self):
        try:
            async for raw in self.ws:
                self.inbox.append(json.loads(raw))
        except Exception:
            pass

    async def send(self, **m):
        await self.ws.send(json.dumps(m))
        await asyncio.sleep(0.12)

    def last_state(self):
        return next((m for m in reversed(self.inbox) if m.get("type") == "room_state"), None)

    def my_id(self):
        return next((m["seat_id"] for m in reversed(self.inbox) if m.get("type") == "room_state" and m.get("seat_id")), None)

    def errors(self):
        return [m.get("code") for m in self.inbox if m.get("type") == "error"]

    def got(self, kind):
        return next((m for m in self.inbox if m.get("type") == kind), None)


async def relay(**limits):
    r = RelayServer("127.0.0.1", 0, max_per_addr=100, max_connects_per_min=100000, max_wrong_per_addr=100000, **limits)
    await r.start()
    return r, f"ws://127.0.0.1:{r.bound_port}/ws"


async def client(url, **first):
    c = C(await websockets.connect(url, max_size=MAX_MESSAGE_BYTES))
    await c.send(**first)
    return c


def seat(state, sid):
    return next((x for x in state["seats"] if x["seat_id"] == sid), None)


async def p1_join_with_units_bypass():
    r, url = await relay(countdown_seconds=0.2)
    host = await client(url, type="create_room", seat="red", team_size=2, claim=1, units=["bat"], lobby=True)
    code = host.last_state()["code"]
    mate = await client(url, type="join", code=code, seat="red", claim=1, units=["bat"])
    white = await client(url, type="join", code=code, seat="white", claim=2, units=["skeleton", "wizard"])
    for c in (host, mate, white):
        await c.send(type="ready")
    await host.send(type="begin")
    await asyncio.sleep(0.5)
    start = host.got("start")
    verdict("P1 teammates both join with units=[bat] then ready without units",
            bool(start) and start["heroes"]["left"] == ["bat", "bat"],
            "start heroes=%s errors=%s" % (start and start["heroes"], host.errors() + mate.errors()), "second join or its ready refused duplicate_hero/invalid_units")
    await r.close()


async def p1b_create_with_self_duplicate():
    r, url = await relay(countdown_seconds=0.2)
    host = await client(url, type="create_room", seat="red", team_size=2, claim=2, units=["bat", "bat"], lobby=True)
    code = host.last_state()["code"]
    white = await client(url, type="join", code=code, seat="white", claim=2, units=["skeleton", "wizard"])
    await host.send(type="ready")
    await white.send(type="ready")
    await host.send(type="begin")
    await asyncio.sleep(0.5)
    start = host.got("start")
    verdict("P1b create_room units=[bat,bat] claim 2 then bare ready",
            bool(start) and start["heroes"]["left"] == ["bat", "bat"],
            "start heroes=%s errors=%s" % (start and start["heroes"], host.errors()), "create refused or ready refused")
    await r.close()


async def p2_ai_filler_join_bypass():
    r, url = await relay(countdown_seconds=0.2)
    host = await client(url, type="create_room", seat="red", team_size=2, claim=1, lobby=True)
    st = host.last_state()
    code, token = st["code"], st["seat_token"]
    await host.send(type="ready", units=["bat"])
    filler = await client(url, type="join", code=code, seat="red", claim=1, units=["bat"], ai_host_token=token)
    fs = filler.last_state()
    mine = fs and seat(fs, filler.my_id())
    verdict("P2 AI filler joins (ai_host_token) with a hero the host already locked",
            bool(mine) and mine["units"] == ["bat"],
            "filler seat=%s errors=%s" % (mine, filler.errors()), "join refused, or units not stored")
    await filler.send(type="ready", units=["bat"])
    verdict("P2b that filler's page ready (index.html:1533 sends its join heroes) is then refused and never retried -> start held",
            "invalid_units" in filler.errors(), "filler errors=%s ready=%s" % (filler.errors(), seat(filler.last_state(), mine["seat_id"])["ready"] if mine else None),
            "consistent: join and ready apply the same rule")
    await r.close()


async def p3_old_room_unchanged():
    r, url = await relay()
    host = await client(url, type="create_room", seat="red", team_size=2, claim=1)
    code = host.last_state()["code"]
    mate = await client(url, type="join", code=code, seat="red", claim=1)
    white = await client(url, type="join", code=code, seat="white", claim=2)
    await white.send(type="ready", units=["skeleton", "skeleton"])
    await host.send(type="ready", units=["bat"])
    await mate.send(type="ready", units=["bat"])
    await asyncio.sleep(0.3)
    start = host.got("start")
    verdict("P3 old non-lobby room still allows duplicates (regression check)", not (start and start["heroes"]["left"] == ["bat", "bat"]),
            "start=%s errors=%s" % (start and start["heroes"], host.errors() + mate.errors() + white.errors()), "old behaviour: start with duplicates")
    await r.close()


async def p4_move_then_ready_and_switch_back():
    r, url = await relay()
    host = await client(url, type="create_room", seat="red", team_size=2, claim=1, lobby=True)
    code = host.last_state()["code"]
    w = await client(url, type="join", code=code, seat="white", claim=1)
    await host.send(type="ready", units=["bat"])
    await w.send(type="ready", units=["bat"])          # cross-team same hero: allowed
    await w.send(type="move", team="red")              # switches into red, units cleared
    st = w.last_state()
    me = seat(st, w.my_id())
    await w.send(type="ready", units=["bat"])
    verdict("P4 white(bat) switches to red(host bat), units cleared and re-ready bat refused",
            not (me["units"] == [] and "invalid_units" in w.errors()),
            "after move units=%s errors=%s" % (me["units"], w.errors()), "units [] and invalid_units")
    await r.close()


async def p5_host_handover_all_disconnected():
    r, url = await relay(seat_grace_seconds=60)
    host = await client(url, type="create_room", seat="red", team_size=3, claim=1, lobby=True)
    code = host.last_state()["code"]
    g1 = await client(url, type="join", code=code, seat="white", claim=1)
    await g1.ws.close()
    await asyncio.sleep(0.1)
    await host.send(type="leave")
    newbie = await client(url, type="join", code=code, seat="white", claim=1)
    st = newbie.last_state(); st["seat_id"] = newbie.my_id()
    await newbie.send(type="begin")
    verdict("P5 host leaves while the only other player is in grace; a connected newcomer joins",
            st["host_seat_id"] == "white-1",
            "host_seat_id=%s newcomer=%s newcomer begin errors=%s" % (st["host_seat_id"], st["seat_id"], newbie.errors()),
            "connected newcomer hosts (or hand-over on reconnect)")
    await r.close()


async def p6_join_ignores_invites_in_seat_cap():
    r, url = await relay()
    host = await client(url, type="create_room", seat="red", team_size=3, claim=1, lobby=True)
    code = host.last_state()["code"]
    await host.send(type="room_options", allow_mcp=True)
    await host.ws.send(json.dumps({"type": "invite"}))
    await asyncio.sleep(0.2)
    ticket = host.got("invite_created")["invite"]
    extras = [await client(url, type="join", code=code, seat="red") for _ in range(3)]   # no claim -> claim 0 seats
    agent = await client(url, type="join", code=code, invite=ticket, client_kind="mcp")
    st = host.last_state()
    verdict("P6 claim-0 joins fill red to 4 seats while an invite is open (join does not count invites, move now does)",
            "team_full" in agent.errors(),
            "red seats=%s agent errors=%s open invites=%s" % ([x["seat_id"] for x in st["seats"] if x["team"] == "red"], agent.errors(), st["invites"]),
            "the plain join is refused like a move would be, so the ticket stays usable")
    await r.close()


async def p7_sweep_with_join_dup():
    r, url = await relay(agent_pick_seconds=0.3)
    host = await client(url, type="create_room", seat="red", team_size=2, claim=1, lobby=True)
    code = host.last_state()["code"]
    await host.send(type="room_options", allow_mcp=True)
    await host.send(type="ready", units=["bat"])
    await host.ws.send(json.dumps({"type": "invite"}))
    await asyncio.sleep(0.2)
    ticket = host.got("invite_created")["invite"]
    agent = await client(url, type="join", code=code, invite=ticket, units=["bat"])
    await asyncio.sleep(2.5)   # sweep runs about once a second
    st = host.last_state()
    ag = next(x for x in st["seats"] if x["agent"])
    verdict("P7 invited agent joins with units=[bat] (host holds bat); the pick sweep then readies it as is",
            ag["units"] == ["bat"] and ag["ready"], "agent seat units=%s ready=%s" % (ag["units"], ag["ready"]), "join refused or sweep repicks a free hero")
    await r.close()


async def main():
    for p in (p1_join_with_units_bypass, p1b_create_with_self_duplicate, p2_ai_filler_join_bypass, p3_old_room_unchanged,
              p4_move_then_ready_and_switch_back, p5_host_handover_all_disconnected, p6_join_ignores_invites_in_seat_cap, p7_sweep_with_join_dup):
        try:
            await p()
        except Exception as exc:  # noqa: BLE001
            print("[ERROR] %s: %r" % (p.__name__, exc))
    print("breaks:", sum(1 for _, b in OUT if b), "of", len(OUT))


asyncio.run(main())
