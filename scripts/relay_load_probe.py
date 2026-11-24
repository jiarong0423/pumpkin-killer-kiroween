#!/usr/bin/env python3
"""Measures what the relay costs per room and per message, so the capacity caps (PK_RELAY_MAX_ROOMS and friends) come from numbers, not guesses
(owner 2026-11-17: 'if the traffic is too high the resources may not be enough'; docs/THREAT_MODEL_20261117.md T1).

Starts the relay as a child process, opens ROOMS rooms with two seats each (real WebSocket connections on 127.0.0.1), keeps every seat sending a small valid message
every PERIOD seconds for SECONDS, samples the relay's resident memory and CPU time, and prints memory per room, CPU per message and a capacity estimate for a server of
the size you give (--server-gb, --server-cores). Run it in the owner's terminal (sockets do not open in the Claude sandbox) after `ulimit -n 4096`.

  python3 -B scripts/relay_load_probe.py --rooms 100 --seconds 20 --period 2 --server-gb 2 --server-cores 2
Exit code 1 on a failure, 2 on bad arguments. Log: logs_local/relay_load_probe.log
"""
import argparse
import asyncio
import json
import os
import subprocess
import sys
import time

import websockets

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "logs_local", "relay_load_probe.log")


def rss_mb(pid):
    out = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    return int(out) / 1024.0 if out.isdigit() else 0.0


def cpu_seconds(pid):
    out = subprocess.run(["ps", "-o", "cputime=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    parts = out.replace(":", " ").replace(".", " ").split()
    if len(parts) < 3:
        return 0.0
    minutes, seconds, hundredths = int(parts[-3]), int(parts[-2]), int(parts[-1])
    return minutes * 60 + seconds + hundredths / 100.0


async def room(url, period, stop, counters, started):
    async with websockets.connect(url, max_size=16 * 1024) as host:
        await host.send(json.dumps({"type": "create_room", "seat": "red", "client_version": "probe"}))
        state = json.loads(await host.recv())
        code = state["code"]
        counters["connected"] += 1
        async with websockets.connect(url, max_size=16 * 1024) as guest:
            await guest.send(json.dumps({"type": "join", "code": code, "seat": "white"}))
            await guest.recv()
            counters["connected"] += 1
            started.set()

            async def drain(sock):
                try:
                    async for _ in sock:
                        counters["received"] += 1
                except Exception:  # noqa: BLE001
                    pass
            tasks = [asyncio.ensure_future(drain(host)), asyncio.ensure_future(drain(guest))]
            try:
                while not stop.is_set():
                    await host.send(json.dumps({"type": "ready"}))
                    await guest.send(json.dumps({"type": "ready"}))
                    counters["sent"] += 2
                    await asyncio.sleep(period)
            finally:
                for t in tasks:
                    t.cancel()


async def main_async(args):
    port = args.port
    env = dict(os.environ, PORT=str(port), HOST="127.0.0.1", PK_RELAY_MAX_ROOMS="100000", PK_RELAY_MAX_CONNECTIONS="100000", PK_RELAY_MAX_PER_ADDR="100000")
    child = subprocess.Popen([sys.executable, "-B", os.path.join(ROOT, "scripts", "pk_relay.py")], env=env, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = "ws://127.0.0.1:%d/ws" % port
    try:
        for _ in range(50):
            try:
                async with websockets.connect(url):
                    break
            except OSError:
                await asyncio.sleep(0.2)
        base_mb = rss_mb(child.pid)
        stop = asyncio.Event()
        counters = {"connected": 0, "sent": 0, "received": 0}
        tasks = []
        samples = [(0, base_mb)]
        for index in range(args.rooms):
            started = asyncio.Event()
            tasks.append(asyncio.ensure_future(room(url, args.period, stop, counters, started)))
            await asyncio.wait_for(started.wait(), 10)
            if (index + 1) % max(1, args.rooms // 4) == 0:
                samples.append((index + 1, rss_mb(child.pid)))
        cpu0, t0, sent0 = cpu_seconds(child.pid), time.time(), counters["sent"]
        await asyncio.sleep(args.seconds)
        cpu1, t1, sent1 = cpu_seconds(child.pid), time.time(), counters["sent"]
        peak_mb = rss_mb(child.pid)
        stop.set()
        await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        child.terminate()
        child.wait(timeout=10)
    per_room = (peak_mb - base_mb) / max(1, args.rooms)
    msgs = max(1, sent1 - sent0)
    cpu_per_msg_us = (cpu1 - cpu0) / msgs * 1e6
    cpu_pct = 100.0 * (cpu1 - cpu0) / max(0.001, t1 - t0)
    lines = ["relay base %.0f MB; samples (rooms, MB): %s" % (base_mb, ", ".join("%d: %.0f" % s for s in samples)),
             "%d rooms (%d connections), %d messages sent in %.0f s (%.0f per second), %d received" % (args.rooms, counters["connected"], msgs, t1 - t0, msgs / (t1 - t0), counters["received"]),
             "memory per room %.2f MB (peak %.0f MB); relay CPU %.1f%% of one core, %.0f microseconds per message" % (per_room, peak_mb, cpu_pct, cpu_per_msg_us)]
    by_memory = int((args.server_gb * 1024 * 0.6 - base_mb) / max(0.01, per_room))   # keep 40 percent of the server memory for the system and the rest
    by_cpu = int(args.server_cores * 0.6 * 1e6 / max(1.0, cpu_per_msg_us) / (2.0 / args.period))   # 60 percent of the cores, two seats per room sending every period
    lines.append("server %.1f GB, %d cores: rooms by memory %d, by CPU %d -> PK_RELAY_MAX_ROOMS about %d" % (args.server_gb, args.server_cores, by_memory, by_cpu, min(by_memory, by_cpu)))
    text = "\n".join(lines)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(time.strftime("%Y-%m-%dT%H:%M:%S") + "\n" + text + "\n")
    print(text)
    return 0 if counters["connected"] >= 2 * args.rooms else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rooms", type=int, default=100)
    parser.add_argument("--seconds", type=float, default=20)
    parser.add_argument("--period", type=float, default=2.0, help="seconds between the messages of one seat")
    parser.add_argument("--port", type=int, default=18765)
    parser.add_argument("--server-gb", type=float, default=2.0)
    parser.add_argument("--server-cores", type=float, default=2.0)
    args = parser.parse_args()
    if args.rooms < 1 or args.seconds <= 0 or args.period <= 0:
        print("ERROR: bad arguments")
        return 2
    try:
        return asyncio.run(main_async(args))
    except Exception as error:  # noqa: BLE001
        print("ERROR:", type(error).__name__, error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
