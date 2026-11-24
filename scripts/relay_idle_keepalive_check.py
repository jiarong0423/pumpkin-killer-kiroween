#!/usr/bin/env python3
"""Does an idle room keep its connections? (gap: cloud idle heartbeat; Cloudflare drops an idle WebSocket after about 100 seconds)

Two seats join one room (red creates, white joins) and then NOTHING is sent for --seconds (default 150, longer than 100). Only the websockets library's own keep-alive
pings run. At the end both sockets must still be open, answer a ping, and (local mode) the relay must still hold the room with both seats connected.

The relay (`scripts/pk_relay.py`) calls `websockets.legacy.server.serve` without ping arguments, so the installed library's defaults apply: ping_interval 20 s and
ping_timeout 20 s (measured by this script and by `--defaults`). A ping every 20 s is traffic on the wire, which is what keeps a proxy's idle timer from firing.

Local (relay started inside this process, needs a localhost socket, so run it in a normal terminal, not the Claude sandbox):
    python3 -B scripts/relay_idle_keepalive_check.py --seconds 150
Against a deployed relay (owner only; it creates one empty room on that relay, nothing is stored):
    python3 -B scripts/relay_idle_keepalive_check.py --url wss://YOUR-HOST/ws --seconds 150 --label cloud
Print the installed library's keep-alive defaults without any connection:
    python3 -B scripts/relay_idle_keepalive_check.py --defaults

Output: one progress line every 10 s, summary JSON in redteam/evidence/relay_idle_keepalive_<label>_<date>.json, last line RESOURCE_RELEASED.
Exit code: 0 = both seats alive after the idle time, 1 = a socket closed or stopped answering, 2 = setup problem.
"""
import argparse
import asyncio
import inspect
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
EVIDENCE = ROOT / "redteam" / "evidence"


def library_defaults():
    import websockets
    from websockets.legacy import server
    sig = inspect.signature(server.serve.__init__)
    out = {"websockets": websockets.__version__, "server_legacy_serve": {k: sig.parameters[k].default for k in ("ping_interval", "ping_timeout", "close_timeout") if k in sig.parameters}}
    try:
        from websockets.asyncio.client import connect
        csig = inspect.signature(connect.__init__)
        out["client_asyncio_connect"] = {k: csig.parameters[k].default for k in ("ping_interval", "ping_timeout", "close_timeout") if k in csig.parameters}
    except Exception as exc:  # older library
        out["client_asyncio_connect"] = "unavailable: %s" % exc
    return out


def state_of(socket):
    state = getattr(socket, "state", None)
    return getattr(state, "name", str(state))


async def first_message(socket, wanted=("room_created", "room_state", "joined")):
    deadline = time.monotonic() + 5
    last = None
    while time.monotonic() < deadline:
        raw = await asyncio.wait_for(socket.recv(), 5)
        last = json.loads(raw)
        if last.get("code") or last.get("type") in wanted:
            return last
    return last


async def run(args):
    import websockets
    relay = None
    url = args.url
    if not url:
        from pk_relay import RelayServer
        relay = RelayServer("127.0.0.1", 0)
        await relay.start()
        url = "ws://127.0.0.1:%d/ws" % relay.bound_port
    summary = {"label": args.label, "url_kind": "local" if relay else "remote", "seconds": args.seconds, "library": library_defaults(), "samples": [], "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    red = await websockets.connect(url, max_size=16 * 1024)
    try:
        await red.send(json.dumps({"type": "create_room", "seat": "red", "client_version": "idle-keepalive-check"}))
        created = await first_message(red)
        code = (created or {}).get("code")
        if not code:
            summary["error"] = "no room code in %r" % (created,)
            return summary, 2
        white = await websockets.connect(url, max_size=16 * 1024)
        try:
            await white.send(json.dumps({"type": "join", "code": code, "seat": "white", "client_version": "idle-keepalive-check"}))
            await first_message(white)
            print(time.strftime("%H:%M:%S"), "room %s joined by both seats; idle for %d s (nothing is sent)" % (code, args.seconds), flush=True)
            began = time.monotonic()
            while time.monotonic() - began < args.seconds:
                await asyncio.sleep(min(10.0, args.seconds - (time.monotonic() - began)))
                t = round(time.monotonic() - began)
                sample = {"t": t, "red": state_of(red), "white": state_of(white),
                          "red_latency": round(getattr(red, "latency", 0.0) or 0.0, 4), "white_latency": round(getattr(white, "latency", 0.0) or 0.0, 4)}
                summary["samples"].append(sample)
                print(time.strftime("%H:%M:%S"), "t=%ds red=%s white=%s latency red %.3fs white %.3fs" % (t, sample["red"], sample["white"], sample["red_latency"], sample["white_latency"]), flush=True)
                if sample["red"] != "OPEN" or sample["white"] != "OPEN":
                    summary["error"] = "a socket left OPEN at t=%ds" % t
                    summary["close"] = {"red": getattr(red, "close_code", None), "white": getattr(white, "close_code", None)}
                    return summary, 1
            alive = {}
            for name, socket in (("red", red), ("white", white)):
                try:
                    pong = await socket.ping()
                    await asyncio.wait_for(pong, 10)
                    alive[name] = True
                except Exception as exc:
                    alive[name] = False
                    summary.setdefault("ping_errors", {})[name] = repr(exc)
            summary["alive_after_idle"] = alive
            if relay is not None:
                room = relay.rooms.get(code)
                summary["relay_room_present"] = room is not None
                summary["relay_seats_connected"] = sorted(seat_id for seat_id, entry in (room.sessions.items() if room else []) if entry.get("connected"))
                if room is None or len(summary["relay_seats_connected"]) < 2:
                    summary["error"] = "the relay lost the room or a seat while idle"
                    return summary, 1
            if not all(alive.values()):
                summary["error"] = "a socket did not answer a ping after the idle time"
                return summary, 1
            return summary, 0
        finally:
            await white.close()
    finally:
        await red.close()
        if relay is not None:
            await relay.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seconds", type=int, default=150)
    ap.add_argument("--url", default="", help="ws:// or wss:// URL of a relay (default: start one inside this process)")
    ap.add_argument("--label", default="local")
    ap.add_argument("--defaults", action="store_true", help="print the library's keep-alive defaults and exit")
    args = ap.parse_args()
    if args.defaults:
        print(json.dumps(library_defaults(), indent=1))
        return 0
    if args.seconds < 1:
        print("ERROR --seconds must be at least 1", file=sys.stderr)
        return 2
    try:
        summary, code = asyncio.run(run(args))
    except Exception as exc:
        print("ERROR setup or run failed: %r" % (exc,), file=sys.stderr)
        return 2
    summary["exit"] = code
    summary["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    out = EVIDENCE / ("relay_idle_keepalive_%s_%s.json" % (args.label, time.strftime("%Y%m%d")))
    out.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print("RESULT %s %s (%s)" % ("PASS" if code == 0 else "FAIL", summary.get("error", "both seats alive after %d s idle" % args.seconds), out.relative_to(ROOT)))
    print("RESOURCE_RELEASED")
    return code


if __name__ == "__main__":
    sys.exit(main())
