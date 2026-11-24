#!/usr/bin/env python3
"""Open a room on this Mac so a phone can join it: starts a headless Chrome (the computer version of the game), opens the page, presses Create room, prints the room code and the join address, and stays alive (the room lives as long as this runs; Ctrl-C ends it).

  python3 -B scripts/host_room.py [--team 3] [--claim 1] [--relay-port 8765] [--page-port 8080]

The page server and the relay must already run (python3 -B scripts/dev_server.py 8080 --with-relay). The phone opens the printed join address (adb reverse tcp:8765 tcp:8765 and tcp:8080 tcp:8080 first).
Never reads a key or token. Log: logs_local/host_room.log.
"""
import argparse, asyncio, json, os, shutil, subprocess, sys, tempfile, time, urllib.request
import websockets

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
LOG = os.path.join(ROOT, "logs_local", "host_room.log")
CHROME = next((c for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Chromium.app/Contents/MacOS/Chromium") if os.path.exists(c)), "")


def log(message):
    line = "%s %s" % (time.strftime("%H:%M:%S"), message); print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as handle: handle.write(line + "\n")
    except OSError:
        pass


async def main_async(args):
    if not CHROME:
        log("ERROR no Chrome found"); return 2
    profile = tempfile.mkdtemp(prefix="pk-host-")
    proc = subprocess.Popen([CHROME, "--headless=new", "--remote-debugging-port=%d" % args.cdp_port, "--user-data-dir=" + profile, "--no-first-run", "--hide-scrollbars", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        tab = None
        for _ in range(60):
            try:
                tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/json" % args.cdp_port, timeout=2).read().decode("utf-8"))
                tab = next((t for t in tabs if t.get("type") == "page"), None)
                if tab: break
            except Exception: pass
            await asyncio.sleep(0.3)
        if not tab:
            log("ERROR Chrome did not start"); return 3
        sock = await websockets.connect(tab["webSocketDebuggerUrl"], max_size=8 * 1024 * 1024)
        counter = [0]
        async def call(method, params):
            counter[0] += 1; await sock.send(json.dumps({"id": counter[0], "method": method, "params": params}))
            while True:
                message = json.loads(await asyncio.wait_for(sock.recv(), 30))
                if message.get("id") == counter[0]: return message
        async def ev(expression):
            reply = await call("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})
            return reply.get("result", {}).get("result", {}).get("value")
        await call("Emulation.setDeviceMetricsOverride", {"width": 923, "height": 415, "deviceScaleFactor": 2, "mobile": False})
        claim = "" if args.claim >= args.team else "&claim=%d" % args.claim
        page = "http://localhost:%d/index.html?relay=ws://localhost:%d&team=%d%s" % (args.page_port, args.relay_port, args.team, claim)
        await call("Page.navigate", {"url": page}); await asyncio.sleep(3.5)
        await ev("document.getElementById('friends-btn').click(); buildRoomControls(); document.getElementById('room-create').onclick(); 1")
        code = ""
        for _ in range(40):
            code = await ev("(document.getElementById('room-code') || {}).textContent || ''")
            if code: break
            await asyncio.sleep(0.5)
        if not code:
            log("ERROR the room was not created (is the relay running on port %d?)" % args.relay_port); return 4
        join = "http://localhost:%d/index.html?relay=ws://localhost:%d&team=%d&room=%s&seat=red%s" % (args.page_port, args.relay_port, args.team, code, "&claim=1" if args.team > 1 else "")
        log("ROOM %s created by the computer version (red seat, claims %d). Join from the phone with: %s" % (code, min(args.claim, args.team), join))
        log("version of this page: %s" % await ev("JSON.stringify({ title: document.title, cache: (typeof caches !== 'undefined') ? null : null })"))
        while True:
            await asyncio.sleep(5)
            state = await ev("JSON.stringify({ status: relayClient && relayClient.state().status, seats: (relaySeats || []).map(s => s.seat_id + ':' + s.team + ':' + (s.units || []).length) })")
            log("room state: %s" % state)
    finally:
        proc.terminate(); shutil.rmtree(profile, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--team", type=int, default=3, choices=[1, 2, 3]); parser.add_argument("--claim", type=int, default=1)
    parser.add_argument("--relay-port", type=int, default=8765); parser.add_argument("--page-port", type=int, default=8080); parser.add_argument("--cdp-port", type=int, default=9555)
    args = parser.parse_args()
    try: return asyncio.run(main_async(args))
    except KeyboardInterrupt: log("ended by Ctrl-C"); return 0


if __name__ == "__main__":
    sys.exit(main())
