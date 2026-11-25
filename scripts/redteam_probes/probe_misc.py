"""Misc probes. Run: python3 -B scripts/redteam_probes/probe_misc.py [probe ...]"""
import os
import asyncio
import json
import random
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h import H, run, verdict  # noqa: E402
import pk_relay  # noqa: E402


async def wrong_addr_growth():
    """F11: wrong_by_addr is never trimmed (connect_times etc. are capped by max_tracked_addrs)."""
    async with H(trust_proxy=True, max_tracked_addrs=50) as h:
        for i in range(200):
            c = await h.open(headers={"CF-Connecting-IP": "2001:db8::%x" % (i + 1)})
            await c.ws.send(json.dumps({"type": "join", "code": "ZZZZZZ", "seat": "red"}))
            await asyncio.sleep(0.005)
            await c.ws.close()
        await asyncio.sleep(0.3)
        verdict("F11 wrong_by_addr grows past max_tracked_addrs", len(h.relay.wrong_by_addr) > 50,
                "connect_times=%d (cap 50), wrong_by_addr=%d" % (len(h.relay.connect_times), len(h.relay.wrong_by_addr)),
                "every per-address table bounded by max_tracked_addrs")


async def kick_disconnected_no_start():
    """F12: kicking a disconnected seat does not call _start_if_ready: the last unready seat is gone but the match never starts."""
    async with H(seat_grace_seconds=60) as h:
        host, code, _ = await h.create(team_size=2, claim=1, units=["wizard"])
        r2 = await h.join(code, seat="red", claim=1, units=["bat"])
        w1 = await h.join(code, seat="white", claim=1, units=["knight"])
        w2 = await h.join(code, seat="white", claim=1, units=["bride"])
        await w2.close()
        for s in (host, r2, w1):
            await s.send(type="ready")
        await host.send(type="kick", seat_id="white-2")
        await asyncio.sleep(0.5)
        room = h.room(code)
        ready_all = room.all_players_ready()
        verdict("F12 kick of the last (disconnected) unready seat leaves the room ready but not started", ready_all and not room.started,
                "all_players_ready=%s started=%s" % (ready_all, room.started), "start sent at once (like leave/expire, which call _start_if_ready)")


async def countdown_ghost():
    """F12b: lobby room; a countdown is announced, then the host kicks a disconnected seat; nobody hears `countdown: null` and no start comes."""
    async with H(seat_grace_seconds=60, countdown_seconds=1.0) as h:
        host, code, _ = await h.create(team_size=1, lobby=True)
        w = await h.join(code, seat="white")
        spec = await h.join(code, seat="spectator")
        await host.send(type="ready")
        await w.send(type="ready")
        await host.send(type="begin", on=True)
        got = host.last("countdown")
        await w.close()
        await host.send(type="kick", seat_id="white-1")
        await asyncio.sleep(1.5)
        cds = [m.get("seconds") for m in host.inbox if m.get("type") == "countdown"]
        room = h.room(code)
        verdict("F12b countdown announced, seat kicked during it, no cancel broadcast", got is not None and cds[-1] is not None and not room.started,
                "countdown messages=%s started=%s" % (cds, room.started), "a `countdown: null` when the room stops being due")


async def host_left_after_start():
    """F13: the host leaves a started match; nobody is host afterwards, so nobody can reset_lobby (rematch) or kick."""
    async with H() as h:
        host, code, _ = await h.create(team_size=2, claim=1, units=["wizard"])
        r2 = await h.join(code, seat="red", claim=1, units=["bat"])
        w = await h.join(code, seat="white", claim=2, units=["knight", "bride"])
        for s in (host, r2, w):
            await s.send(type="ready")
        await host.send(type="leave")
        await r2.send(type="reset_lobby")
        await w.send(type="reset_lobby")
        room = h.room(code)
        verdict("F13 after the host leaves a started match no seat can reopen the lobby", room.host_seat_id == "red-1" and r2.errors().count("host_only") == 1,
                "host_seat_id=%s (gone); r2 errors=%s w errors=%s" % (room.host_seat_id, r2.errors(), w.errors()),
                "a remaining player can reopen the lobby (host handed over when the match is over)")


async def ai_after_allow_ai_off():
    """F14: switching allow_ai off leaves existing AI seats; switching allow_mcp off leaves seated agents."""
    async with H() as h:
        host, code, st = await h.create(team_size=2, claim=1, units=["wizard"])
        token = host.last("room_state", lambda m: "seat_token" in m)["seat_token"]
        ai = await h.join(code, seat="white", claim=1, ai_host_token=token)
        await host.send(type="invite")
        ticket = host.last("invite_created")["invite"]
        ag = await h.join(code, invite=ticket)
        await host.send(type="room_options", allow_ai=False, allow_mcp=False)
        seats = host.state()["seats"]
        verdict("F14 allow_ai/allow_mcp off keeps AI and agent seats", any(s["ai"] for s in seats) and any(s["agent"] for s in seats),
                "seats after options off: %s" % [(s["seat_id"], s["ai"], s["agent"]) for s in seats],
                "seats the option forbids are released (or the option is refused while they sit)")


def name_parity():
    """F15: clean_name (Python) and cleanName (JS) must agree; fuzz 20000 strings from risky ranges."""
    rng = random.Random(7)
    pools = [(0x20, 0x7E), (0x300, 0x36F), (0x200B, 0x200F), (0x202A, 0x202E), (0x2066, 0x2069), (0x1100, 0x11FF), (0xAC00, 0xAC20),
             (0x1F300, 0x1F6FF), (0x1F3FB, 0x1F3FF), (0x1F1E6, 0x1F1FF), (0xFE00, 0xFE0F), (0x2600, 0x27BF), (0x3000, 0x3005), (0xE0020, 0xE007F),
             (0x1FA70, 0x1FAFF), (0x0600, 0x06FF), (0xFDFD, 0xFDFD), (0x12000, 0x12400), (0x2E80, 0x2EFF), (0x31350, 0x323AF), (0x1B000, 0x1B16F),
             (0xD7B0, 0xD7FF), (0x0E00, 0x0E7F), (0x115F, 0x1160), (0x3164, 0x3164), (0x00A0, 0x00AD)]
    cases = []
    for _ in range(20000):
        s = "".join(chr(rng.randint(*rng.choice(pools))) for _ in range(rng.randint(1, 14)))
        cases.append(s)
    js = subprocess.run(["node", "-e", "const R=require(" + json.dumps(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "js", "relay_client.js")) + ");let d='';process.stdin.on('data',c=>d+=c).on('end',()=>{process.stdout.write(JSON.stringify(JSON.parse(d).map(R.cleanName)))})"],
                        input=json.dumps(cases), capture_output=True, text=True, check=True)
    out = json.loads(js.stdout)
    diffs = [(c, pk_relay.clean_name(c), o) for c, o in zip(cases, out) if pk_relay.clean_name(c) != o]
    wide = pk_relay.clean_name("﷽" * 12)
    verdict("F15 Python/JS name rules disagree", bool(diffs),
            "%d of %d differ; first: %s" % (len(diffs), len(cases), [(ascii(a), ascii(b), ascii(c)) for a, b, c in diffs[:3]]),
            "identical output (scripts/name_vectors.json claims both pinned)")
    verdict("F15b a very wide glyph counts as 1 display unit", len(wide) == 10,
            "clean_name('\\ufdfd'*12) keeps %d glyphs (each draws ~3-4 CJK widths)" % len(wide), "width table covers wide So/Lo glyphs (U+FDFD, cuneiform)")


async def main():
    names = sys.argv[1:] or ["wrong_addr_growth", "kick_disconnected_no_start", "countdown_ghost", "host_left_after_start", "ai_after_allow_ai_off", "name_parity"]
    for n in names:
        try:
            r = globals()[n]()
            if asyncio.iscoroutine(r):
                await r
        except Exception as exc:  # noqa: BLE001
            verdict(n + " CRASHED", True, repr(exc), "probe runs")


run(main())
