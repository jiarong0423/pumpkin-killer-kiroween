#!/usr/bin/env python3
"""Execute break-it cases written by an external model (scripts/llm_review.py --task attack) against the real relay, in process, on a free local port.

After every step the relay's internal state is checked with the invariants of scripts/stress_room_alloc.py (places per team, unique seat ids and tokens,
host is a person, AI and agent seats never host, invites only before the start, one agent per player, no countdown that is not due, a started lobby room
owns every place) plus: no unhandled exception in the relay's log. The model's own "expect" sentence is not machine-checked; every case's messages are
written to the transcript so a person can compare. Placeholders: $CODE, $TOKEN:X, $SEAT:X, $INVITE:X (see scripts/llm_review.py).

Usage: python3 -B scripts/llm_attack_runner.py docs/llm/glm_attack_20261126.json [--transcript out.jsonl]
Prints one line per case and a RESULT line; exit 1 on any invariant break or relay exception, 2 on a bad case file. Needs local sockets.
"""
import argparse
import asyncio
import json
import logging
import os
import sys

import websockets

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pk_relay  # noqa: E402
from stress_room_alloc import check, LogCatcher  # noqa: E402


class Client:
    def __init__(self, name):
        self.name, self.sock, self.inbox, self.task = name, None, [], None

    async def reader(self):
        try:
            async for raw in self.sock:
                try:
                    self.inbox.append(json.loads(raw))
                except ValueError:
                    self.inbox.append({"type": "<not json>"})
        except Exception:  # noqa: BLE001 - a closed socket ends the reader
            pass

    def last(self, kind, key=None):
        for m in reversed(self.inbox):
            if m.get("type") == kind and (key is None or key in m):
                return m
        return None


def fill(value, clients, code):
    if isinstance(value, str):
        if value == "$CODE":
            return code or "NOCODE"
        for prefix, kind, field in (("$TOKEN:", "room_state", "seat_token"), ("$SEAT:", "room_state", "seat_id"), ("$INVITE:", "invite_created", "invite")):
            if value.startswith(prefix):
                c = clients.get(value[len(prefix):])
                m = c.last(kind, field) if c else None
                return m[field] if m else "none"
        return value
    if isinstance(value, list):
        return [fill(v, clients, code) for v in value]
    if isinstance(value, dict):
        return {k: fill(v, clients, code) for k, v in value.items()}
    return value


async def run_case(case, transcript):
    relay = pk_relay.RelayServer("127.0.0.1", 0, max_per_addr=1000, max_connects_per_min=10 ** 6, max_wrong_per_addr=10 ** 6, max_rooms_per_addr=1000,
                                 seat_grace_seconds=60, countdown_seconds=0.05, invite_seconds=600, agent_pick_seconds=30)
    catcher = LogCatcher()
    logging.getLogger().addHandler(catcher)
    await relay.start()
    url = "ws://127.0.0.1:%d/ws" % relay.bound_port
    clients, code, problems = {}, None, []
    try:
        for index, step in enumerate(case.get("steps", [])[:40]):
            if not isinstance(step, dict):
                continue
            name = step.get("client")
            try:
                if "sleep" in step:
                    await asyncio.sleep(min(1.0, max(0.0, float(step["sleep"]))))
                elif step.get("connect"):
                    c = clients.setdefault(name, Client(name))
                    c.sock = await websockets.connect(url, max_size=pk_relay.MAX_MESSAGE_BYTES)
                    c.task = asyncio.ensure_future(c.reader())
                elif step.get("close") and name in clients and clients[name].sock is not None:
                    await clients[name].sock.close()
                elif "expire" in step:
                    target = clients.get(step["expire"])
                    if target is not None and target.sock is not None:
                        await target.sock.close()
                        await asyncio.sleep(0.05)
                        for room in list(relay.rooms.values()):
                            for token, seat in list(room.sessions.items()):
                                m = target.last("room_state", "seat_token")
                                if m and token == m["seat_token"]:
                                    await relay._expire_seat(room, token)
                elif "send" in step and name in clients and clients[name].sock is not None:
                    message = step["send"]
                    payload = json.dumps(fill(message, clients, code)) if isinstance(message, (dict, list)) else str(message)
                    await clients[name].sock.send(payload)
            except Exception as exc:  # noqa: BLE001 - a socket the relay closed is part of the attack
                transcript.append({"case": case.get("id"), "step": index, "client_error": type(exc).__name__})
            await asyncio.sleep(0.03)
            if code is None:
                for c in clients.values():
                    m = c.last("room_state", "code")
                    if m:
                        code = m["code"]
                        break
            for problem in check(relay):
                problems.append("step %d: %s" % (index, problem))
            if catcher.records:
                problems.append("step %d: relay logged an error: %s" % (index, catcher.records[0][:240]))
                catcher.records.clear()
            if problems:
                break
        await asyncio.sleep(0.1)
        for problem in check(relay):
            problems.append("end: " + problem)
    finally:
        for c in clients.values():
            transcript.append({"case": case.get("id"), "client": c.name, "received": [m.get("type") + (":" + str(m.get("code") or m.get("reason") or "")) for m in c.inbox][:60]})
            try:
                if c.sock is not None:
                    await c.sock.close()
            except Exception:  # noqa: BLE001
                pass
            if c.task is not None:
                c.task.cancel()
        await relay.close()
        logging.getLogger().removeHandler(catcher)
    return problems


async def main_async(args):
    try:
        with open(args.cases, encoding="utf-8") as handle:
            data = json.load(handle)
        cases = data["cases"]
    except (OSError, ValueError, KeyError) as exc:
        print("ERROR bad case file: %s" % exc)
        return 2
    transcript, broken = [], 0
    for case in cases:
        problems = await run_case(case, transcript)
        if problems:
            broken += 1
            print("BREAK %s | %s | %s" % (case.get("id"), case.get("why", "")[:120], problems[0][:300]))
        else:
            print("held  %s | %s" % (case.get("id"), case.get("why", "")[:120]))
    if args.transcript:
        with open(args.transcript, "w", encoding="utf-8") as handle:
            for row in transcript:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("RESULT %s %d cases, %d broke an invariant or crashed the relay (model %s)" % ("FAIL" if broken else "PASS", len(cases), broken, data.get("model")))
    return 1 if broken else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases")
    ap.add_argument("--transcript", default="")
    return asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    sys.exit(main())
