#!/usr/bin/env python3
"""The whole unit-slot-fill flow on a real phone, in one command (docs/ADR_unit_slot_fill_20261124.md).

What it does, in order (every step is logged to logs_local/run_slot_room.log):
  1. checks the phone is on adb (USB or Wi-Fi), starts the page server (scripts/dev_server.py) and an in-process relay (loopback, 40 connections per address),
  2. adb reverse for the relay and page ports, adb forward for the phone Chrome's DevTools socket,
  3. opens the game on the phone's Chrome with ?team=3 and the number of units the phone claims (?claim=N, 1 to 3),
  4. over DevTools: opens Friends and presses Create room on the phone, reads the room code,
  5. starts the slot filler (scripts/fill_room.py: placeholders, subtraction, one computer seat per team with open slots),
  6. the phone presses Start Battle: you tap it, or --press-start lets the script tap it; the phone then plays only its own claimed units,
  7. --autoplay lets the script throw for the phone's units (a smoke test; without it you play them yourself),
  8. prints one verdict line: the match reached its end on the phone and on every filler seat, no relay error, no hash difference.

Run it from your own terminal (it listens on sockets and talks to adb; the Claude sandbox cannot). Example, the phone takes 1 of the 6 slots and computers fill the other 5:
  python3 -B scripts/run_slot_room.py --claim 1 --autoplay --press-start
Never reads a key or token.
"""
import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import websockets  # noqa: E402

import fill_room as fr  # noqa: E402

RUN_ID = time.strftime("%Y%m%d_%H%M%S")
LOG_PATH = os.path.join(ROOT, "logs_local", "run_slot_room.log")   # the last run
RUN_LOG_PATH = os.path.join(ROOT, "logs_local", "run_slot_room_%s.log" % RUN_ID)   # this run, kept (red-team R1 B1)
ADB_CANDIDATES = ["/opt/homebrew/bin/adb", "/usr/local/bin/adb"]


def log(message: str) -> None:
    line = "%s %s" % (time.strftime("%H:%M:%S"), message)
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        for path in (LOG_PATH, RUN_LOG_PATH):
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
    except OSError:
        pass


def find_adb() -> str:
    for path in ADB_CANDIDATES:
        if os.path.exists(path):
            return path
    return shutil.which("adb") or "adb"


class Adb:
    def __init__(self, serial: str) -> None:
        self.binary, self.serial = find_adb(), serial

    def run(self, *args: str, timeout: int = 20) -> subprocess.CompletedProcess:
        return subprocess.run([self.binary, "-s", self.serial, *args], capture_output=True, text=True, timeout=timeout)


def pick_serial(requested: str) -> Optional[str]:
    result = subprocess.run([find_adb(), "devices"], capture_output=True, text=True, timeout=20)
    devices = [line.split("\t")[0] for line in result.stdout.splitlines()[1:] if line.strip().endswith("\tdevice")]
    if requested:
        return requested if requested in devices else None
    return devices[0] if len(devices) == 1 else None


class Cdp:
    """A DevTools session to one tab of the phone's Chrome (through adb forward)."""

    def __init__(self, port: int) -> None:
        self.port, self.socket, self.next_id = port, None, 0
        self.errors: List[str] = []   # page exceptions and console errors seen while a call was waiting

    def pages(self) -> List[Dict[str, Any]]:
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json" % self.port, timeout=3) as response:
                return [tab for tab in json.loads(response.read().decode("utf-8")) if tab.get("type") == "page"]
        except Exception:  # noqa: BLE001 - Chrome is not running on the phone, or the forward is not up yet
            return []

    async def open(self, url: str) -> None:
        """Attach to the tab that shows `url` (Chrome was started with it), or open a new tab when Chrome is already running."""
        base = url.split("?")[0]
        tab = next((t for t in self.pages() if str(t.get("url", "")).startswith(base)), None)
        if tab is None:
            request = urllib.request.Request("http://127.0.0.1:%d/json/new?%s" % (self.port, url), method="PUT")
            with urllib.request.urlopen(request, timeout=10) as response:
                tab = json.loads(response.read().decode("utf-8"))
        self.socket = await websockets.connect(tab["webSocketDebuggerUrl"], max_size=8 * 1024 * 1024)
        self.tab_id = tab["id"]
        await self.socket.send(json.dumps({"id": 9000, "method": "Runtime.enable"}))

    async def send(self, method: str, params: Dict[str, Any]) -> Any:
        self.next_id += 1
        call_id = self.next_id
        await self.socket.send(json.dumps({"id": call_id, "method": method, "params": params}))
        while True:
            message = json.loads(await asyncio.wait_for(self.socket.recv(), 15))
            self.note(message)
            if message.get("id") == call_id:
                return message

    def note(self, message: Dict[str, Any]) -> None:
        method = message.get("method")
        if method == "Runtime.exceptionThrown":
            detail = message["params"]["exceptionDetails"]
            self.errors.append("EXC " + str((detail.get("exception") or {}).get("description") or detail.get("text"))[:400])
        elif method == "Runtime.consoleAPICalled" and message["params"].get("type") == "error":
            self.errors.append("CONSOLE " + " ".join(str(a.get("value", a.get("description", ""))) for a in message["params"].get("args", []))[:400])

    async def drain(self) -> None:
        """Read pending protocol events without waiting (so page errors are collected even between calls)."""
        while True:
            try:
                self.note(json.loads(await asyncio.wait_for(self.socket.recv(), 0.05)))
            except asyncio.TimeoutError:
                return

    async def evaluate(self, expression: str) -> Any:
        self.next_id += 1
        call_id = self.next_id
        await self.socket.send(json.dumps({"id": call_id, "method": "Runtime.evaluate", "params": {"expression": expression, "returnByValue": True, "awaitPromise": False}}))
        while True:
            message = json.loads(await asyncio.wait_for(self.socket.recv(), 15))
            self.note(message)
            if message.get("id") == call_id:
                if "error" in message:
                    raise RuntimeError("devtools: %s" % message["error"])
                result = message.get("result", {})
                if result.get("exceptionDetails"):
                    raise RuntimeError("page exception: %s" % json.dumps(result["exceptionDetails"])[:300])
                return result.get("result", {}).get("value")

    async def close(self) -> None:
        try:
            if self.socket is not None:
                await self.socket.close()
            urllib.request.urlopen("http://127.0.0.1:%d/json/close/%s" % (self.port, self.tab_id), timeout=5).read()
        except Exception:  # noqa: BLE001 - a tab that is already gone is fine
            pass


async def run(args: argparse.Namespace) -> int:
    import phone_room_check as pc
    serial = pick_serial(args.serial)
    if not serial:
        log("ERROR no single adb device found (or %r is not connected). Plug the phone in with USB debugging on, or run: adb connect IP:PORT" % (args.serial or "the given serial"))
        return 3
    adb = Adb(serial)
    log("phone %s on adb" % serial)
    server: Optional[subprocess.Popen] = None
    relay = None
    cdp = Cdp(args.cdp_port)
    desktop: Optional[Cdp] = None
    chrome_proc: Optional[subprocess.Popen] = None
    chrome_profile = ""
    fill_task: Any = None
    started_at = time.monotonic()
    try:
        server = subprocess.Popen([sys.executable, "-B", os.path.join("scripts", "dev_server.py"), str(args.page_port)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        relay = pc.PhoneRelay("127.0.0.1", args.relay_port, max_per_addr=40)
        await relay.start()
        port = relay.bound_port
        for remote in (port, args.page_port):
            if adb.run("reverse", "tcp:%d" % remote, "tcp:%d" % remote).returncode != 0:
                log("ERROR adb reverse tcp:%d failed (is the phone authorised for USB debugging?)" % remote)
                return 4
        if adb.run("forward", "tcp:%d" % args.cdp_port, "localabstract:chrome_devtools_remote").returncode != 0:
            log("ERROR adb forward for the phone Chrome failed (open Chrome once on the phone and keep it running)")
            return 5
        await asyncio.sleep(1.0)
        claim = "" if args.claim >= args.team else "&claim=%d" % args.claim
        page = "http://localhost:%d/index.html?relay=ws://localhost:%d&team=%d%s" % (args.page_port, port, args.team, claim)
        log("opening %s on the phone" % page)
        started = adb.run("shell", "am start -a android.intent.action.VIEW -d '%s' com.android.chrome" % page)   # works whether Chrome is running or not (the phone must be awake and unlocked)
        log("asked Chrome on the phone to open the page: %s" % (started.stdout.strip().splitlines()[-1] if started.stdout.strip() else started.stderr.strip()[:120]))
        base = page.split("?")[0]
        for _ in range(60):
            if any(str(t.get("url", "")).startswith(base) for t in cdp.pages()):
                break
            await asyncio.sleep(0.5)
        else:
            log("ERROR no Chrome tab on the phone shows the game (wake and unlock the phone, then run again)")
            return 5
        await cdp.open(page)
        for _ in range(60):
            if await cdp.evaluate("typeof buildRoomControls === 'function' && !!document.getElementById('room-create') && document.readyState === 'complete'"):
                break
            await asyncio.sleep(0.5)
        else:
            log("ERROR the game page did not load on the phone (is the page server reachable through adb reverse?)")
            return 6
        await cdp.evaluate("window.__fc = 0; (function f() { window.__fc++; requestAnimationFrame(f); })(); 1")   # counts animation frames: a page whose frames stop cannot finish a throw
        log("phone claim state: %s" % await cdp.evaluate("JSON.stringify({ team: TEAM_N, claim: relayClaimCount })"))
        panel = await cdp.evaluate("(function () { document.getElementById('friends-btn').click(); buildRoomControls(); const b = document.getElementById('room-create'), r = b.getBoundingClientRect(); const out = { disabled: b.disabled, w: Math.round(r.width), h: Math.round(r.height), top: Math.round(r.top), vw: innerWidth, vh: innerHeight, start: document.getElementById('start-screen').className }; try { b.onclick(); } catch (e) { out.err = String(e && e.stack || e).slice(0, 300); } out.created = relayCreateSent; out.client = relayClient ? relayClient.state().status : null; out.status = (document.getElementById('room-status') || {}).textContent; return JSON.stringify(out); })()")
        log("room panel on the phone: %s" % panel)
        code = ""
        for _ in range(40):
            if relay.rooms:
                code = next(iter(relay.rooms))
                break
            await asyncio.sleep(0.5)
        if not code:
            try:
                detail = await cdp.evaluate("JSON.stringify({ status: (document.getElementById('room-status') || {}).textContent, hidden: (document.getElementById('room-picker') || {}).hidden, address: typeof relayAddress === 'undefined' ? null : relayAddress, client: (typeof relayClient !== 'undefined' && relayClient) ? relayClient.state().status : null, href: location.href })")
            except Exception as error:  # noqa: BLE001
                detail = "unreadable: %s" % error
            log("ERROR the phone did not create a room (relay errors: %s; phone page: %s)" % (list(relay.error_log)[:3], detail))
            return 7
        log("room %s created by the phone; starting the slot filler" % code)
        fill_args = argparse.Namespace(relay="ws://127.0.0.1:%d" % port, code=code, filler=args.filler, settle=args.settle, max_wait=args.max_wait, join_wait=90, level=args.level, speed=args.speed, max_seconds=args.max_seconds)
        fill_task = asyncio.ensure_future(fr.fill(fill_args))
        room = relay.rooms[code]
        for _ in range(60):
            if sum(1 for e in room.sessions.values() if e.get("team") in fr.TEAMS) >= 3:   # the phone host plus the two placeholders
                break
            await asyncio.sleep(0.5)
        else:
            log("ERROR the filler's placeholder seats did not join")
            return 8
        if args.with_desktop:
            chrome_path = next((c for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Chromium.app/Contents/MacOS/Chromium") if os.path.exists(c)), "")
            if not chrome_path:
                log("ERROR no Chrome found for the desktop seat")
                return 9
            import tempfile
            chrome_profile = tempfile.mkdtemp(prefix="pk-desktop-")
            chrome_proc = subprocess.Popen([chrome_path, "--headless=new", "--remote-debugging-port=%d" % args.desktop_cdp_port, "--user-data-dir=" + chrome_profile, "--no-first-run", "--hide-scrollbars", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            desktop = Cdp(args.desktop_cdp_port)
            for _ in range(50):
                if desktop.pages():
                    break
                await asyncio.sleep(0.2)
            guest = "http://localhost:%d/index.html?relay=ws://localhost:%d&team=%d&room=%s&seat=red&claim=1" % (args.page_port, port, args.team, code)
            request = urllib.request.Request("http://127.0.0.1:%d/json/new?about:blank" % args.desktop_cdp_port, method="PUT")   # a URL with several & in /json/new is cut short: open a blank tab and navigate it
            with urllib.request.urlopen(request, timeout=10) as response:
                tab = json.loads(response.read().decode("utf-8"))
            desktop.socket = await websockets.connect(tab["webSocketDebuggerUrl"], max_size=8 * 1024 * 1024)
            desktop.tab_id = tab["id"]
            await desktop.send("Runtime.enable", {})
            await desktop.send("Emulation.setDeviceMetricsOverride", {"width": 923, "height": 415, "deviceScaleFactor": 2, "mobile": False})
            await desktop.send("Page.navigate", {"url": guest})
            await asyncio.sleep(4)
            log("desktop seat: %s" % await desktop.evaluate("JSON.stringify({ seat: relayClient && relayClient.state().seat, status: relayClient && relayClient.state().status, claim: relayClaimCount, queue: typeof relayDrain })"))
        async def shoot(label: str) -> None:
            if not args.shots:
                return
            os.makedirs(args.shots, exist_ok=True)
            for name, page_cdp in (("phone", cdp), ("desktop", desktop)):
                if page_cdp is None:
                    continue
                try:
                    reply = await page_cdp.send("Page.captureScreenshot", {"format": "png"})
                    with open(os.path.join(args.shots, "%s_%s.png" % (name, label)), "wb") as handle:
                        import base64
                        handle.write(base64.b64decode(reply["result"]["data"]))
                except Exception as error:  # noqa: BLE001
                    log("WARN screenshot %s %s failed: %s" % (name, label, error))
            for name, page_cdp in (("phone", cdp), ("desktop", desktop)):
                if page_cdp is not None:
                    try:
                        log("DOM %s %s: %s" % (name, label, await page_cdp.evaluate("JSON.stringify({ startDisplay: getComputedStyle(document.getElementById('start-screen')).display, startClass: document.getElementById('start-screen').className, startHidden: document.getElementById('start-screen').hidden, curtainHidden: (document.getElementById('turn-curtain') || {}).hidden, matchStarted: matchStarted, relayPlaying: relayPlaying, round: roundNum, vw: innerWidth, vh: innerHeight, dpr: devicePixelRatio, docHidden: document.hidden, fs: !!document.fullscreenElement })")))
                    except Exception as error:  # noqa: BLE001
                        log("WARN DOM %s unreadable: %s" % (name, error))
            log("screenshots %s saved to %s" % (label, args.shots))
        await shoot("1_before_start")
        if args.press_start:
            log("pressing Start Battle on the phone%s" % (" and on the desktop seat" if desktop else ""))
            await cdp.evaluate("document.getElementById('start-go').click(); 1")
            if desktop:
                await desktop.evaluate("document.getElementById('start-go').click(); 1")
        else:
            log("press Start Battle on the phone now (you have %d s)" % args.max_wait)
        game_over: Any = None
        deadline = time.monotonic() + args.max_seconds + args.max_wait
        await asyncio.sleep(4)
        await shoot("2_after_start")
        shot_late = False
        last_state = 0.0
        while time.monotonic() < deadline and not fill_task.done():
            if args.shots and not shot_late and time.monotonic() - started_at > 40:
                shot_late = True
                await shoot("3_during_play")
            if time.monotonic() - last_state > 10:   # a trace of the phone page every 10 s, so a stall shows where the phone is waiting
                last_state = time.monotonic()
                try:
                    await cdp.drain()
                    if cdp.errors:
                        log("PHONE page errors so far (%d): %s" % (len(cdp.errors), cdp.errors[:4]))
                    if desktop:
                        log("DESKTOP %s" % await desktop.evaluate("JSON.stringify({ round: roundNum, turn: turn, active: unitOf('left').id, over: gameOver || null, inbox: relayInbox.length, hpL: unitsOf('left').map(u => Math.round(u.hp)), hpR: unitsOf('right').map(u => Math.round(u.hp)) })"))
                    log("PHONE %s relay_phase=%s" % (await cdp.evaluate("JSON.stringify({ round: roundNum, turn: turn, active: unitOf('left').id, myUnit: relayMyUnitActive(), proj: projectiles.length, dice: !!diceRoll, over: gameOver || null, wait: !!relayWait, remoteOpen: relayRemoteOpen, mateOpen: relayMateOpen, mateFlight: relayMateFlight, incoming: relayIncoming, hidden: document.hidden, vis: document.visibilityState, frames: window.__fc, hitStop: typeof hitStop === 'undefined' ? null : hitStop, right: unitsOf('right').map(x => x.id + ':' + x.animState + ':' + Math.round((x.animProgress || 0) * 100) + ':' + Math.round(x.hp)).join(' '), paused: typeof paused === 'undefined' ? null : paused })"), room.phase))
                except Exception as error:  # noqa: BLE001
                    log("WARN phone state unreadable: %s" % error)
            if args.autoplay:
                for name, page_cdp in (("phone", cdp), ("desktop", desktop)):
                    if page_cdp is None:
                        continue
                    try:
                        await page_cdp.evaluate("(function () { if (relayLive() && turn === 'player' && !projectiles.length && !diceRoll && !gameOver) { executeThrow('player', 70, 54); return 1; } return 0; })()")
                    except Exception as error:  # noqa: BLE001
                        log("WARN autoplay step failed on the %s: %s" % (name, error))
            await asyncio.sleep(1.5)
        fill_exit = await asyncio.wait_for(fill_task, 30) if fill_task.done() else 1
        for _ in range(60):   # the computer seats play fast; give the phone (and the desktop seat) time to reach the same end
            ended = [await cdp.evaluate("!!gameOver")]
            if desktop:
                ended.append(await desktop.evaluate("!!gameOver"))
            if all(ended):
                break
            if args.autoplay:
                for page_cdp in [cdp] + ([desktop] if desktop else []):
                    try:
                        await page_cdp.evaluate("(function () { if (relayLive() && turn === 'player' && !projectiles.length && !diceRoll && !gameOver) { executeThrow('player', 70, 54); return 1; } return 0; })()")
                    except Exception:  # noqa: BLE001
                        pass
            await asyncio.sleep(1.5)
        try:
            game_over = await cdp.evaluate("gameOver || null")
        except Exception as error:  # noqa: BLE001
            log("WARN could not read the phone's result: %s" % error)
        trace = [(m.get("seq"), m.get("type"), m.get("seat_id"), m.get("unit"), m.get("round"), m.get("phase"), m.get("kind"), m.get("next_phase")) for m in getattr(room, "log", []) if m.get("type") in ("action", "end_turn", "judge", "start")]
        log("RELAY LOG (seq, type, seat, unit, round, phase, kind, next_phase), first 40 of %d: %s" % (len(trace), trace[:40]))
        desktop_ok = True
        if desktop:
            desktop_ok = False
            try:
                both = await asyncio.gather(cdp.evaluate("JSON.stringify({ over: gameOver || null, round: roundNum, hpL: unitsOf('left').map(u => Math.round(u.hp * 10)), hpR: unitsOf('right').map(u => Math.round(u.hp * 10)) })"), desktop.evaluate("JSON.stringify({ over: gameOver || null, round: roundNum, hpL: unitsOf('left').map(u => Math.round(u.hp * 10)), hpR: unitsOf('right').map(u => Math.round(u.hp * 10)) })"))
                phone_final, desktop_final = json.loads(both[0]), json.loads(both[1])
                same_hp = phone_final["hpL"] == desktop_final["hpL"] and phone_final["hpR"] == desktop_final["hpR"]
                desktop_ok = bool(desktop_final["over"]) and same_hp and desktop_final["over"] == phone_final["over"]   # red-team R1 B6: the desktop seat must end too, with the same result and hit points
                log("FINAL phone=%s desktop=%s same_hp=%s desktop_ok=%s" % (both[0], both[1], same_hp, desktop_ok))
            except Exception as error:  # noqa: BLE001
                log("WARN could not compare the two pages: %s" % error)
        errors = list(relay.error_log)
        mismatches = pc._hash_mismatch(room)
        owners = dict(getattr(room, "owners", {}) or {})
        for item in errors[:6]:
            log("relay error %s while %s" % (item.get("code"), json.dumps(item.get("while"))))
        log("RESULT fill_exit=%s phone_game_over=%s relay_errors=%d out_of_sync=%d owners=%s seconds=%d" % (fill_exit, game_over, len(errors), len(mismatches), owners, time.monotonic() - started_at))
        ok = fill_exit == 0 and bool(game_over) and desktop_ok and not errors and not mismatches and len(owners) == args.team * 2
        log("VERDICT %s (phone claimed %d of %d slots%s; the filler took the rest; the match reached its end on the phone%s and on every filler seat, owners named for every unit, no relay error, no hash difference)" % ("PASS" if ok else "FAIL", min(args.claim, args.team), args.team * 2, ", the desktop seat claimed %d more" % 1 if desktop else "", " and on the desktop seat with the same result and hit points" if desktop else ""))
        return 0 if ok else 1
    except Exception as error:  # noqa: BLE001
        log("ERROR the flow failed: %s: %s" % (type(error).__name__, error))
        return 1
    finally:
        if fill_task is not None and not fill_task.done():
            fill_task.cancel()
        await cdp.close()
        try:
            if desktop is not None and desktop.socket is not None:
                await desktop.socket.close()
            if chrome_proc is not None:
                chrome_proc.terminate()
                chrome_proc.wait(timeout=10)
            if chrome_profile:
                shutil.rmtree(chrome_profile, ignore_errors=True)   # red-team R1 B9: the throw-away browser profile
        except Exception:  # noqa: BLE001
            pass
        for remote in (args.page_port,):
            adb.run("reverse", "--remove", "tcp:%d" % remote)
        if relay is not None:
            adb.run("reverse", "--remove", "tcp:%d" % relay.bound_port)
        adb.run("forward", "--remove", "tcp:%d" % args.cdp_port)
        if server is not None:
            server.terminate()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--serial", default=os.environ.get("PHONE_SERIAL", ""), help="adb serial (default: the only connected device)")
    parser.add_argument("--team", type=int, default=3, choices=[2, 3], help="units per side")
    parser.add_argument("--claim", type=int, default=1, help="units the phone takes (the rest of every team is filled)")
    parser.add_argument("--filler", choices=["computer", "agent"], default="computer")
    parser.add_argument("--relay-port", type=int, default=8765)
    parser.add_argument("--page-port", type=int, default=8080)
    parser.add_argument("--cdp-port", type=int, default=9333)
    parser.add_argument("--settle", type=float, default=3.0)
    parser.add_argument("--max-wait", type=int, default=300, help="seconds to wait for the Start press")
    parser.add_argument("--max-seconds", type=int, default=600)
    parser.add_argument("--level", choices=["easy", "normal", "hard"], default="normal")
    parser.add_argument("--speed", type=float, default=0, help="page clock speed of the filler seats (0 = real time)")
    parser.add_argument("--press-start", action="store_true", help="let the script press Start Battle on the phone")
    parser.add_argument("--with-desktop", action="store_true", help="add a second human seat on red: a headless Chrome on this Mac (the computer version of the game), controlled like the phone")
    parser.add_argument("--desktop-cdp-port", type=int, default=9444)
    parser.add_argument("--shots", default="", help="folder for screenshots of the phone and the desktop seat (before Start, just after Start, a little later)")
    parser.add_argument("--autoplay", action="store_true", help="let the script throw for the phone's units (smoke test); without it you play them")
    args = parser.parse_args()
    if not 1 <= args.claim <= args.team:
        print("ERROR --claim must be from 1 to --team", file=sys.stderr)
        return 2
    try:
        return asyncio.run(run(args))
    except KeyboardInterrupt:
        log("ERROR interrupted")
        return 1


if __name__ == "__main__":
    sys.exit(main())
