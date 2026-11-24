#!/usr/bin/env python3
"""Exercise a relay reconnect and compare the replayed ordered log."""
import asyncio
import hashlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import websockets

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from pk_relay_client import RelayClient  # noqa: E402


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


async def wait_for_relay(port: int) -> None:
    for _ in range(100):
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.close()
            await writer.wait_closed()
            return
        except OSError:
            await asyncio.sleep(0.02)
    raise RuntimeError("relay did not open its local port")


async def receive(client: Any, log: List[Dict[str, Any]]) -> Dict[str, Any]:
    reader = client.receive if hasattr(client, "receive") else client.recv
    message = await asyncio.wait_for(reader(), 1)
    if isinstance(message, str):
        message = json.loads(message)
    if isinstance(message.get("seq"), int):
        log.append(message)
    return message


async def receive_until_type(client: Any, log: List[Dict[str, Any]], wanted: str) -> Dict[str, Any]:
    for _ in range(20):
        message = await receive(client, log)
        if message.get("type") == wanted:
            return message
    raise RuntimeError("did not receive %s" % wanted)


async def send_end(sender: RelayClient, round_number: int, phase: str,
                   clients: List[Any], logs: List[List[Dict[str, Any]]]) -> None:
    await sender.send({"type": "end_turn", "round": round_number, "phase": phase})
    for client, log in zip(clients, logs):
        await receive_until_type(client, log, "end_turn")


def digest(log: List[Dict[str, Any]]) -> str:
    canonical = json.dumps(log, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:8]


async def run(url: str) -> None:
    red = RelayClient(url, None, "red")
    white = None
    resumed = None
    try:
        red_bootstrap = await red.connect()
        red_log: List[Dict[str, Any]] = []
        white = RelayClient(url, red_bootstrap["code"], "white")
        await white.connect()
        white_log: List[Dict[str, Any]] = []
        await red.send({"type": "ready"})
        await white.send({"type": "ready"})
        await receive_until_type(red, red_log, "start")
        await receive_until_type(white, white_log, "start")

        # Complete relay rounds 1 and 2 under the alternating schedule: red then white in round 1, white then red in round 2.
        await send_end(red, 1, "red", [red, white], [red_log, white_log])
        await send_end(white, 1, "white", [red, white], [red_log, white_log])
        await send_end(red, 2, "red", [red, white], [red_log, white_log])   # the first team (red) opens every round since 2026-11-17 (pk_relay.py first-team rule): no team acts twice in a row
        await send_end(white, 2, "white", [red, white], [red_log, white_log])
        assert red_log == white_log

        last_seq = red_log[-1]["seq"]
        token = red_bootstrap["seat_token"]
        await red.close()
        await receive_until_type(white, white_log, "room_state")

        resumed = await websockets.connect(url, max_size=16 * 1024)
        await resumed.send(json.dumps({"type": "resume", "seat_token": token, "last_seq": last_seq}))
        bootstrap = await receive(resumed, [])
        assert bootstrap["type"] == "room_state"
        assert bootstrap["seat_token"] == token

        resumed_log = list(red_log)
        # Disconnect state, then the resume presence update, are the only missing events.
        await receive_until_type(resumed, resumed_log, "room_state")
        await receive_until_type(resumed, resumed_log, "room_state")
        await receive_until_type(white, white_log, "room_state")
        assert resumed_log == white_log

        # Complete two more relay rounds after red resumes.
        await resumed.send(json.dumps({"type": "end_turn", "round": 3, "phase": "red"}))
        await receive_until_type(resumed, resumed_log, "end_turn")
        await receive_until_type(white, white_log, "end_turn")
        await send_end(white, 3, "white", [resumed, white], [resumed_log, white_log])
        await resumed.send(json.dumps({"type": "end_turn", "round": 4, "phase": "red"}))
        await receive_until_type(resumed, resumed_log, "end_turn")
        await receive_until_type(white, white_log, "end_turn")
        await send_end(white, 4, "white", [resumed, white], [resumed_log, white_log])

        final_hash = digest(resumed_log)
        assert final_hash == digest(white_log)
        await resumed.send(json.dumps({"type": "round_hash", "round": 4, "hash": final_hash}))
        await receive_until_type(resumed, resumed_log, "round_hash")
        await receive_until_type(white, white_log, "round_hash")
        await white.send({"type": "round_hash", "round": 4, "hash": final_hash})
        await receive_until_type(resumed, resumed_log, "round_hash")
        await receive_until_type(white, white_log, "round_hash")
        assert resumed_log == white_log
        assert final_hash == digest(resumed_log[:-2]) == digest(white_log[:-2])
    finally:
        await red.close()
        if white is not None:
            await white.close()
        if resumed is not None:
            await resumed.close()


async def run_team(url: str) -> None:
    """A 3 v 3 room: the start message, unit ids in actions and judges all survive a reconnect and its replay."""
    sockets: List[Any] = []
    try:
        red = await websockets.connect(url, max_size=16 * 1024)
        sockets.append(red)
        await red.send(json.dumps({"type": "create_room", "seat": "red", "team_size": 3,
                                   "units": ["skeleton", "wizard", "bat"], "client_version": "test"}))
        red_bootstrap = await receive(red, [])
        assert red_bootstrap["team_size"] == 3, red_bootstrap
        white = await websockets.connect(url, max_size=16 * 1024)
        sockets.append(white)
        await white.send(json.dumps({"type": "join", "code": red_bootstrap["code"], "seat": "white",
                                     "units": ["hag", "knight", "nun"], "client_version": "test"}))
        assert (await receive(white, []))["team_size"] == 3
        red_log: List[Dict[str, Any]] = []
        white_log: List[Dict[str, Any]] = []
        await red.send(json.dumps({"type": "ready"}))
        await white.send(json.dumps({"type": "ready"}))
        start = await receive_until_type(red, red_log, "start")
        await receive_until_type(white, white_log, "start")
        assert start["team_size"] == 3 and start["heroes"]["left"] == ["skeleton", "wizard", "bat"], start
        assert len(start["owners"]) == 6, start

        await red.send(json.dumps({"type": "action", "round": 1, "phase": "red", "unit": "left_2", "kind": "throw",
                                   "angle": 54, "power": 40, "start": {"x": 300, "y": 760},
                                   "claimed_landing": {"x": 1200, "y": 860}, "dirX": 1}))
        action = await receive_until_type(red, red_log, "action")
        await receive_until_type(white, white_log, "action")
        assert action["unit"] == "left_2", action
        await white.send(json.dumps({"type": "judge", "ref": action["seq"], "hit": True, "unit": "right_1",
                                     "damage": 20, "hp_after": 80, "statuses": []}))
        await receive_until_type(red, red_log, "judge")
        await receive_until_type(white, white_log, "judge")
        await red.send(json.dumps({"type": "action", "round": 1, "phase": "red", "unit": "left_0", "kind": "move", "die": 2}))
        assert (await receive_until_type(red, red_log, "error"))["code"] == "unit_changed_in_turn"

        token = red_bootstrap["seat_token"]
        await red.close()
        resumed = await websockets.connect(url, max_size=16 * 1024)
        sockets.append(resumed)
        await resumed.send(json.dumps({"type": "resume", "seat_token": token, "last_seq": start["seq"]}))
        bootstrap = await receive(resumed, [])
        assert bootstrap["type"] == "room_state" and bootstrap["team_size"] == 3 and bootstrap["seat_token"] == token
        replay: List[Dict[str, Any]] = []
        await receive_until_type(resumed, replay, "action")
        judge = await receive_until_type(resumed, replay, "judge")
        assert [m["seq"] for m in replay] == sorted(m["seq"] for m in replay)
        assert judge["unit"] == "right_1" and judge["hp_after"] == 80, judge
        # the unit lock of the turn survived the reconnect: the same seat still may not change unit
        await resumed.send(json.dumps({"type": "action", "round": 1, "phase": "red", "unit": "left_1", "kind": "move", "die": 2}))
        for _ in range(10):
            message = json.loads(await asyncio.wait_for(resumed.recv(), 1))
            if message.get("type") == "error":
                assert message["code"] == "unit_changed_in_turn", message
                break
        else:
            raise RuntimeError("expected unit_changed_in_turn after resume")
    finally:
        for socket_ in sockets:
            await socket_.close()


async def main() -> None:
    port = free_port()
    process = subprocess.Popen([sys.executable, "-B", str(ROOT / "scripts" / "pk_relay.py")],
                               cwd=str(ROOT), env=dict(os.environ, PORT=str(port), HOST="127.0.0.1"))
    try:
        await wait_for_relay(port)
        await run("ws://127.0.0.1:%d/ws" % port)
        print("relay reconnect ordered log: ok")
        await run_team("ws://127.0.0.1:%d/ws" % port)
        print("relay reconnect team match (3 v 3 unit ids replayed): ok")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as error:
        print("relay reconnect failed: %s" % error, file=sys.stderr)
        raise SystemExit(1)
