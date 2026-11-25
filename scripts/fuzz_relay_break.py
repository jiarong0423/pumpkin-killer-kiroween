#!/usr/bin/env python3
"""Seeded abuse fuzzer for the room relay (scripts/pk_relay.py), local only, reproducible.

Starts its OWN relay on a free loopback port (flood limits raised so the abuse itself is not blocked; the flood block is covered by
test_relay_reconnect_block.py), then sends a seeded sequence of hostile or unexpected traffic: invalid JSON, wrong types, unknown and
out-of-order message types, oversized and binary frames, truncated frames, abrupt closes, bursts, garbage room codes and seat fields.
Pass criteria: the relay process stays alive, a normal create_room still works after every 100 steps and at the end, stderr has no
Traceback, resident memory grows by less than 120 MB.
Reproduce a failure:  python3 -B scripts/fuzz_relay_break.py --seed <seed>   (same seed = same action sequence; the sequence hash is printed)
usage: fuzz_relay_break.py [--seed 1] [--steps 2000] [--json out.json] [--selfcheck]   exit 1 on any failure
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import socket
import struct
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Raw:
    """Tiny WebSocket client that can send any frame, including broken ones."""

    def __init__(self, port: int, timeout: float = 2.0) -> None:
        self.sock = socket.create_connection(("127.0.0.1", port), timeout)
        self.sock.settimeout(timeout)
        key = "dGhlIHNhbXBsZSBub25jZQ=="
        self.sock.sendall((f"GET /ws HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                           f"Sec-WebSocket-Version: 13\r\nSec-WebSocket-Key: {key}\r\n\r\n").encode())
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise OSError("handshake closed")
            head += chunk
        if b" 101 " not in head.split(b"\r\n", 1)[0] + b" ":
            raise OSError("handshake refused: " + head.split(b"\r\n", 1)[0].decode("latin1"))
        self.buffer = head.split(b"\r\n\r\n", 1)[1]

    def frame(self, opcode: int, payload: bytes, fin: bool = True, claim: int | None = None) -> bytes:
        mask = os.urandom(4)
        size = len(payload) if claim is None else claim
        first = (0x80 if fin else 0) | opcode
        if size < 126:
            header = bytes((first, 0x80 | size))
        elif size < 65536:
            header = bytes((first, 0x80 | 126)) + struct.pack("!H", size)
        else:
            header = bytes((first, 0x80 | 127)) + struct.pack("!Q", size)
        return header + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload))

    def send(self, data: bytes) -> None:
        self.sock.sendall(data)

    def drain(self) -> list:
        """Read whatever the relay sent, as decoded JSON objects (non-JSON ignored)."""
        out = []
        self.sock.settimeout(0.05)
        try:
            while True:
                chunk = self.sock.recv(65536)
                if not chunk:
                    break
                self.buffer += chunk
        except (socket.timeout, OSError):
            pass
        buf = self.buffer
        while len(buf) >= 2:
            op, ln = buf[0] & 0x0F, buf[1] & 0x7F
            pos = 2
            if ln == 126:
                if len(buf) < 4:
                    break
                ln, pos = struct.unpack("!H", buf[2:4])[0], 4
            elif ln == 127:
                if len(buf) < 10:
                    break
                ln, pos = struct.unpack("!Q", buf[2:10])[0], 10
            if len(buf) < pos + ln:
                break
            payload, buf = buf[pos:pos + ln], buf[pos + ln:]
            if op == 1:
                try:
                    out.append(json.loads(payload.decode("utf-8")))
                except (ValueError, UnicodeDecodeError):
                    pass
        self.buffer = buf
        return out

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


WEIRD = [None, True, False, 0, -1, 2 ** 63, 1e308, float("inf") if False else 1e999, "", " ", "A" * 200, "\u0000", "😀", "../../etc/passwd",
         "__proto__", "constructor", "<script>alert(1)</script>", [], {}, [[]], {"a": {"b": {"c": 1}}}, "ABCDEF", "000000", "ZZZZZZ"]
TYPES = ["create_room", "join", "ready", "action", "judge", "end_turn", "round_hash", "resume", "leave", "ping", "fill", "claim", "spectate", "start",
         "", "CREATE_ROOM", "create_room ", "__proto__", "constructor", None, 7, ["join"], {"type": "join"}]
KEYS = ["type", "code", "seat", "seat_token", "team", "size", "name", "claim", "units", "heroes", "payload", "round", "hash", "turn", "angle", "power", "id"]


def plan(seed: int, steps: int) -> list:
    """The whole attack sequence as data: the same seed always gives the same list (this is what makes a failure reproducible)."""
    rng = random.Random(seed)
    out = []
    for step in range(steps):
        kind = rng.choice(["valid_create", "bad_json", "wrong_types", "unknown_type", "out_of_order", "oversized", "binary", "truncated", "abrupt",
                           "burst", "garbage_join", "nested", "ping_close", "fragment"])
        msg = {k: rng.choice(WEIRD) for k in rng.sample(KEYS, rng.randint(0, 6))}
        msg["type"] = rng.choice(TYPES) if kind != "valid_create" else "create_room"
        if kind == "garbage_join":
            msg = {"type": "join", "code": rng.choice(WEIRD), "seat": rng.choice(WEIRD)}
        depth = rng.choice([50, 400, 3000])
        out.append({"step": step, "kind": kind, "conn": rng.randint(0, 5), "msg": msg, "n": rng.randint(2, 40), "depth": depth,
                    "junk": rng.getrandbits(32), "size": rng.choice([16 * 1024 + 1, 70000, 300000])})
    return out


def sequence_hash(actions: list) -> str:
    return hashlib.sha256(json.dumps(actions, sort_keys=True, default=str).encode()).hexdigest()[:16]


def rss_mb(pid: int) -> float:
    try:
        return int(subprocess.check_output(["ps", "-o", "rss=", "-p", str(pid)]).split()[0]) / 1024
    except (subprocess.CalledProcessError, IndexError, ValueError):
        return -1.0


def probe(port: int) -> bool:
    """A normal client must still be able to open a room."""
    try:
        c = Raw(port, timeout=3.0)
        c.send(c.frame(1, json.dumps({"type": "create_room", "seat": "red", "solo": False, "client_version": "fuzz"}).encode()))
        for _ in range(30):
            for m in c.drain():
                if isinstance(m, dict) and m.get("type") == "room_state" and m.get("code"):
                    c.close()
                    return True
            time.sleep(0.1)
        c.close()
    except OSError:
        pass
    return False


def apply(action: dict, conns: dict, port: int) -> None:
    rng = random.Random(action["junk"])
    idx = action["conn"]
    c = conns.get(idx)
    if c is None or action["kind"] == "abrupt":
        if c is not None:
            c.close()
        c = conns[idx] = Raw(port)
    kind, msg = action["kind"], action["msg"]
    text = json.dumps(msg, default=str).encode()
    if kind in ("valid_create", "wrong_types", "unknown_type", "out_of_order", "garbage_join"):
        c.send(c.frame(1, text))
    elif kind == "bad_json":
        bad = rng.choice([b"{", b"[1,2", b"{'type':'join'}", b"\xff\xfe\x00", b"null", b"[]", b"123", b'"join"', b'{"type":"join","type":"create_room"}', text[: max(1, len(text) // 2)]])
        c.send(c.frame(1, bad))
    elif kind == "oversized":
        c.send(c.frame(1, b'{"type":"action","p":"' + b"x" * action["size"] + b'"}'))
    elif kind == "binary":
        c.send(c.frame(2, bytes(rng.getrandbits(8) for _ in range(rng.randint(0, 600)))))
    elif kind == "truncated":
        data = c.frame(1, text)
        c.send(data[: max(2, len(data) // 2)])
        c.close()
        conns.pop(idx, None)
    elif kind == "abrupt":
        c.send(c.frame(1, text)[:5])
        c.close()
        conns.pop(idx, None)
    elif kind == "burst":
        for _ in range(action["n"]):
            c.send(c.frame(1, text))
    elif kind == "nested":
        d = action["depth"]
        c.send(c.frame(1, b'{"type":"join","code":' + b"[" * d + b"]" * d + b"}"))
    elif kind == "ping_close":
        c.send(c.frame(9, b"ping"))
        c.send(c.frame(8, struct.pack("!H", 1000) + b"bye"))
        c.close()
        conns.pop(idx, None)
    elif kind == "fragment":
        c.send(c.frame(1, text[:3], fin=False))
        c.send(c.frame(0, text[3:]))
    if idx in conns:
        conns[idx].drain()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--steps", type=int, default=2000)
    ap.add_argument("--json")
    ap.add_argument("--relay", default=os.path.join(ROOT, "scripts", "pk_relay.py"), help="relay script to attack (the negative control passes a broken copy)")
    ap.add_argument("--selfcheck", action="store_true", help="only check that the same seed gives the same sequence (no network)")
    args = ap.parse_args(argv)
    a1, a2 = plan(args.seed, args.steps), plan(args.seed, args.steps)
    h = sequence_hash(a1)
    if h != sequence_hash(a2) or sequence_hash(plan(args.seed + 1, args.steps)) == h:
        print("RESULT FAIL the sequence is not reproducible or not seed-dependent")
        return 1
    if args.selfcheck:
        print(f"RESULT PASS seed {args.seed} sequence {h} reproducible")
        return 0
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    err = tempfile.NamedTemporaryFile("w+", suffix=".relay.err", delete=False)
    env = dict(os.environ, HOST="127.0.0.1", PORT=str(port), PK_RELAY_MAX_CONNECTS_PER_MIN="1000000", PK_RELAY_MAX_BAD_RESUMES_PER_MIN="1000000",
               PK_RELAY_MAX_PER_ADDR="100000", PK_RELAY_MAX_WRONG_PER_ADDR="1000000", PK_RELAY_MAX_CONNECTIONS="100000")
    relay = subprocess.Popen([sys.executable, "-B", args.relay], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=err)
    failures, conns, step_at = [], {}, 0
    try:
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", port), 0.2).close()
                break
            except OSError:
                time.sleep(0.1)
        base = rss_mb(relay.pid)
        if not probe(port):
            failures.append("probe failed before any abuse")
        for action in a1:
            step_at = action["step"]
            try:
                apply(action, conns, port)
            except (OSError, ValueError) as error:   # the relay closing on bad input is the right answer
                conns.pop(action["conn"], None)
            if relay.poll() is not None:
                failures.append(f"relay process died at step {step_at} ({action['kind']}) exit {relay.returncode}")
                break
            if step_at % 100 == 99 and not probe(port):
                failures.append(f"relay stopped serving normal clients after step {step_at} ({action['kind']})")
                break
        for c in conns.values():
            c.close()
        time.sleep(0.5)
        if relay.poll() is None and not probe(port):
            failures.append("final probe failed")
        grow = rss_mb(relay.pid) - base if relay.poll() is None else 0.0
        if grow > 120:
            failures.append(f"relay memory grew {grow:.0f} MB")
    finally:
        if relay.poll() is None:
            relay.terminate()
            try:
                relay.wait(5)
            except subprocess.TimeoutExpired:
                relay.kill()
        err.flush()
        err.seek(0)
        log = err.read()
        err.close()
        os.unlink(err.name)
    if "Traceback" in log:
        i = log.index("Traceback")
        failures.append("relay stderr has a Traceback: " + log[i:i + 400].replace("\n", " | "))
    result = {"seed": args.seed, "steps": args.steps, "sequence_sha256_16": h, "failures": failures, "last_step": step_at,
              "kinds": {k: sum(1 for a in a1 if a["kind"] == k) for k in sorted({a['kind'] for a in a1})}}
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1)
    print(json.dumps({k: v for k, v in result.items() if k != "kinds"}))
    for f in failures:
        print("FAILURE " + f)
        print(f"REPRODUCE python3 -B scripts/fuzz_relay_break.py --seed {args.seed} --steps {args.steps}   (fails at step {step_at})")
    print("RESULT " + ("FAIL" if failures else "PASS"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
