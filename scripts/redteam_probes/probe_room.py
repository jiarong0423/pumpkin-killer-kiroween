"""Room/lobby invariant probes. Run: python3 -B scripts/redteam_probes/probe_room.py"""
import os
import asyncio
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h import H, run, verdict  # noqa: E402


async def kicked_zombie():
    """F1: a kicked socket keeps its handler-local room/entry and can still act (and, after the start, end the turn of its old team)."""
    async with H() as h:
        host, code, _ = await h.create(team_size=2, claim=1, units=["wizard"])
        guest = await h.join(code, seat="red", claim=1, units=["bat"])
        w = await h.join(code, seat="white", claim=2, units=["knight", "bride"])
        await host.send(type="kick", seat_id="red-2")
        kicked = guest.last("kicked") is not None
        n_before = len(host.inbox)
        try:   # 2026-11-26 fix: the relay closes a kicked socket; a send then fails, which is the wanted outcome
            await guest.send(type="set_name", name="ghost")
            await guest.send(type="invite", note="zombie")
        except Exception:  # noqa: BLE001
            pass
        inv = guest.last("invite_created")
        st = host.state()
        zombie_invites = [t for t in st["invites"] if t["by"] == "red-2"]
        verdict("F1a kicked socket can still mint an invite in the room", bool(kicked and inv and zombie_invites),
                "kicked=%s; zombie got invite_created=%s; host room_state invites=%s" % (kicked, bool(inv), st["invites"]),
                "after `kicked` every further message from that socket is refused (join_required) and nothing reaches the room")
        await host.send(type="invite_cancel", by="red-2")
        # host takes the free place again and both sides ready -> match starts
        await host.send(type="ready", units=["wizard", "hunchback"])
        await w.send(type="ready")
        await asyncio.sleep(0.2)
        room = h.room(code)
        started = room.started
        errs_before = len(guest.errors())
        try:
            await guest.send(type="end_turn", round=1, phase="red")
        except Exception:  # noqa: BLE001 - closed socket: it cannot act
            pass
        await asyncio.sleep(0.2)
        ended = host.last("end_turn")
        verdict("F1b kicked socket ends the red turn of a started match", bool(started and ended and ended.get("seat_id") == "red-2"),
                "started=%s; host received end_turn=%s; zombie errors=%s" % (started, ended, guest.errors()[errs_before:]),
                "stale_or_out_of_turn / join_required: a removed seat has no say in the match")


async def one_v_one_extra_seat():
    """F2: in a 1v1 room an explicit `seat` joins an occupied side (up to MAX_TEAM_SEATS=4); move and invite refuse the same thing."""
    async with H() as h:
        host, code, _ = await h.create()
        b = await h.join(code, seat="red")
        c = await h.join(code, seat="white")
        st = host.state()
        reds = [s["seat_id"] for s in st["seats"] if s["team"] == "red"]
        verdict("F2 1v1 room accepts a second red seat by explicit seat", len(reds) > 1,
                "red seats=%s errors(b)=%s" % (reds, b.errors()), "team_full for the second red (move already says 'that side is taken')")
        for s in (host, b, c):
            await s.send(type="ready")
        await asyncio.sleep(0.2)
        verdict("F2b 1v1 match starts with two red players", h.room(code).started and len(reds) > 1,
                "started=%s with %d red seats" % (h.room(code).started, len(reds)), "never more than one seat per side in 1v1")


async def team_size_shrink():
    """F3: the host's `ready` may change team_size after places are held, leaving a team above its size."""
    async with H() as h:
        host, code, _ = await h.create(team_size=3, claim=1)
        a = await h.join(code, seat="red", claim=1)
        b = await h.join(code, seat="red", claim=1)
        await host.send(type="ready", team_size=2, units=["wizard"])
        room = h.room(code)
        held = room.held_places("red")
        verdict("F3 host shrinks team_size below places already held", room.team_size == 2 and held > room.team_size,
                "team_size=%s red held=%s errors=%s" % (room.team_size, held, host.errors()),
                "invalid_team_size (or refuse) when seats already hold more places than the new size")


async def agent_grows():
    """F4: an invited agent (one place by ticket) takes more places with `ready.units`."""
    async with H() as h:
        host, code, _ = await h.create(team_size=3, claim=1, units=["wizard"])
        await host.send(type="invite", note="hi")
        ticket = host.last("invite_created")["invite"]
        agent = await h.join(code, invite=ticket, client_kind="mcp")
        await agent.send(type="ready", units=["bat", "knight"])
        st = host.state()
        mine = [s for s in st["seats"] if s.get("agent")]
        verdict("F4 agent seat lists two heroes though its ticket gives one place", bool(mine) and len(mine[0]["units"]) == 2,
                "agent seat=%s errors=%s" % (mine, agent.errors()), "invalid_units: a ticket seat keeps exactly one place")


async def spectator_host():
    """F5: create_room with seat=spectator makes a spectator the host; the first player who joins never becomes host."""
    async with H() as h:
        host, code, st0 = await h.create(seat="spectator", team_size=2, lobby=True)
        p = await h.join(code, seat="red", claim=2)
        st = host.state()
        verdict("F5 spectator is host of a room (players cannot become host)", st["host_seat_id"].startswith("spectator"),
                "host_seat_id=%s" % st["host_seat_id"], "create_room as spectator refused, or the first player seat becomes the host")
        await host.send(type="kick", seat_id="red-1")
        verdict("F5b spectator host kicks a player", p.last("kicked") is not None, "player kicked=%s" % (p.last("kicked") is not None,),
                "only a player host may kick")


async def kick_disconnected():
    """F6: kicking a disconnected seat skips _release_invited: its agent stays, a new joiner reusing the seat id inherits it."""
    async with H(seat_grace_seconds=60) as h:
        host, code, _ = await h.create(team_size=3, claim=1, units=["wizard"])
        p = await h.join(code, seat="red", claim=1, units=["bat"])
        await p.send(type="invite")
        ticket = p.last("invite_created")["invite"]
        agent = await h.join(code, invite=ticket)
        await p.close()           # transient drop, seat kept for grace
        await asyncio.sleep(0.2)
        await host.send(type="kick", seat_id="red-2")
        st = host.state()
        orphan = [s for s in st["seats"] if s.get("invited_by") == "red-2"]
        newbie = await h.join(code, seat="red")
        own = newbie.last("room_state", lambda m: "seat_id" in m)
        sid = own["seat_id"] if own else newbie.errors()
        await newbie.send(type="invite")
        verdict("F6 kick of a disconnected seat leaves its agent; seat id reused, newcomer inherits it",
                bool(orphan) and sid == "red-2" and "invite_limit" in newbie.errors(),
                "agent invited_by red-2 still seated=%s; newcomer seat_id=%s; newcomer invite errors=%s" % (bool(orphan), sid, newbie.errors()),
                "the agent leaves with the kicked inviter (kicked: inviter_left), like leave/expire")
        kicked_before = agent.last("kicked")   # 2026-11-26: the agent now goes with its kicked inviter, before the newcomer arrives
        await newbie.send(type="leave")
        await asyncio.sleep(0.2)
        late = agent.last("kicked") is not None and kicked_before is None
        verdict("F6b agent is kicked when an unrelated newcomer leaves", late,
                "agent kicked before the newcomer came=%s, kicked only when the newcomer left=%s" % (kicked_before, late), "the newcomer never invited it")


async def last_seen_leak():
    """F7: a room deleted in _remove_client leaves its code in relay.last_seen for ever (create + leave on one socket in a loop)."""
    async with H() as h:
        c = await h.open()
        for _ in range(30):
            await c.send(type="create_room", seat="red")
            await c.send(type="leave")
        verdict("F7 last_seen grows with every created-and-left room", len(h.relay.last_seen) >= 25 and not h.relay.rooms,
                "rooms=%d last_seen=%d after 30 create+leave" % (len(h.relay.rooms), len(h.relay.last_seen)), "last_seen has no entry for a deleted room")


async def log_growth():
    """F8: room.log keeps every broadcast room_state; one seat spamming set_name grows it without bound and every joiner gets the full replay."""
    async with H() as h:
        try:
            big, big_code, _ = await h.create(team_size=3, claim=1, units=["x" * 4000, "y" * 4000, "z" * 4000])
        except TypeError:   # no room_state came back: refused
            big_code = None
        verdict("F8a 4 KB hero ids accepted", big_code is not None, "create with 4000-char unit ids gave code=%s" % big_code, "invalid_units (a hero id is a short word)")
        host, code, _ = await h.create(team_size=3, claim=1, units=["wizard"])
        for i in range(60):
            await host.send(type="set_name", name="n%d" % i)
        room = h.room(code)
        import json
        size = sum(len(json.dumps(m)) for m in room.log)
        j = await h.join(code, seat="white")
        await asyncio.sleep(0.5)
        replay = sum(1 for m in j.inbox if m.get("type") == "room_state" and "seq" in m)
        verdict("F8 log grows by one full room_state per set_name; joiner replays it all", len(room.log) >= 60,
                "log entries=%d, %.1f KB after ~7 s from one socket (unit strings up to 16 KB accepted); joiner got %d replayed room_states" % (len(room.log), size / 1024, replay),
                "room_state not kept in the replay log (or log bounded), hero ids validated/short")


async def main():
    for probe in [globals()[n] for n in (sys.argv[1:] or ["kicked_zombie", "one_v_one_extra_seat", "team_size_shrink", "agent_grows", "spectator_host", "kick_disconnected", "last_seen_leak", "log_growth"])]:
        try:
            await probe()
        except Exception as exc:  # noqa: BLE001
            verdict(probe.__name__ + " CRASHED", True, repr(exc), "probe runs")


run(main())
