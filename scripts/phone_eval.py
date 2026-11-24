#!/usr/bin/env python3
"""Run a JavaScript expression in the game tab of the phone's Chrome over DevTools (adb forward), or open a page there first.

  python3 -B scripts/phone_eval.py --open 'http://localhost:8080/index.html?team=3' --expr 'document.title'
  python3 -B scripts/phone_eval.py --expr 'JSON.stringify({ round: roundNum })'
  python3 -B scripts/phone_eval.py --screenshot logs_local/phone.png

The expression may be async (a promise is awaited). Needs adb and a phone with USB debugging; run it from your own terminal (the Claude sandbox cannot talk to adb).
Exit code 0 on success, non-zero with an ERROR line otherwise. Never reads a key or token.
"""
import argparse
import asyncio
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request

import websockets

ADB = next((p for p in ("/opt/homebrew/bin/adb", "/usr/local/bin/adb") if os.path.exists(p)), "adb")


def adb(serial, *args):
    return subprocess.run([ADB, "-s", serial, *args], capture_output=True, text=True, timeout=30)


def pick_serial(requested):
    out = subprocess.run([ADB, "devices"], capture_output=True, text=True, timeout=20).stdout.splitlines()[1:]
    devices = [line.split("\t")[0] for line in out if line.strip().endswith("\tdevice")]
    if requested:
        return requested if requested in devices else None
    return devices[0] if len(devices) == 1 else None


def pages(port):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/json" % port, timeout=3) as response:
            return [t for t in json.loads(response.read().decode("utf-8")) if t.get("type") == "page"]
    except Exception:  # noqa: BLE001
        return []


async def main_async(args):
    serial = pick_serial(args.serial)
    if not serial:
        print("ERROR no single adb device (or the given serial is not connected)", file=sys.stderr)
        return 3
    if adb(serial, "forward", "tcp:%d" % args.port, "localabstract:chrome_devtools_remote").returncode != 0:
        print("ERROR adb forward failed", file=sys.stderr)
        return 4
    try:
        if args.open:
            adb(serial, "shell", "am start -a android.intent.action.VIEW -d '%s' com.android.chrome" % args.open)
            time.sleep(1.5)
        base = (args.open or args.match).split("?")[0]
        tab = None
        for _ in range(40):
            tab = next((t for t in pages(args.port) if str(t.get("url", "")).startswith(base)), None)
            if tab:
                break
            await asyncio.sleep(0.5)
        if not tab:
            print("ERROR no phone Chrome tab shows %s" % base, file=sys.stderr)
            return 5
        socket = await websockets.connect(tab["webSocketDebuggerUrl"], max_size=16 * 1024 * 1024)
        counter = [0]

        async def call(method, params):
            counter[0] += 1
            await socket.send(json.dumps({"id": counter[0], "method": method, "params": params}))
            while True:
                message = json.loads(await asyncio.wait_for(socket.recv(), 60))
                if message.get("id") == counter[0]:
                    return message
        if args.expr:
            reply = await call("Runtime.evaluate", {"expression": args.expr, "returnByValue": True, "awaitPromise": True})
            result = reply.get("result", {})
            if result.get("exceptionDetails"):
                print("ERROR page exception: %s" % json.dumps(result["exceptionDetails"])[:400], file=sys.stderr)
                return 6
            print(json.dumps(result.get("result", {}).get("value")) if not isinstance(result.get("result", {}).get("value"), str) else result["result"]["value"])
        if args.screenshot:
            reply = await call("Page.captureScreenshot", {"format": "png"})
            with open(args.screenshot, "wb") as handle:
                handle.write(base64.b64decode(reply["result"]["data"]))
            print("saved %s" % args.screenshot)
        await socket.close()
        return 0
    finally:
        if not args.keep_forward:
            adb(serial, "forward", "--remove", "tcp:%d" % args.port)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--serial", default=os.environ.get("PHONE_SERIAL", ""))
    parser.add_argument("--port", type=int, default=9333)
    parser.add_argument("--open", default="", help="open this URL in the phone's Chrome first")
    parser.add_argument("--match", default="http://localhost:8080/index.html", help="the tab to act on starts with this URL (without a query)")
    parser.add_argument("--expr", default="")
    parser.add_argument("--screenshot", default="")
    parser.add_argument("--keep-forward", action="store_true")
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
