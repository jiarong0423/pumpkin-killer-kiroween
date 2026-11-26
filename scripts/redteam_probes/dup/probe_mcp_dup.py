#!/usr/bin/env python3
"""Red-team probe: an MCP agent in a 2v2 lobby locks a hero its inviter already locked. Can it recover?"""
import asyncio
import json
import sys
import threading
import time

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
import mcp_stdio_server as mcp_srv  # noqa: E402
import websockets  # noqa: E402
from pk_relay import RelayServer  # noqa: E402


def call(server, name, args):
    res = server._call_tool(name, args)
    return res["isError"], json.loads(res["content"][0]["text"])


loop = asyncio.new_event_loop()
relay = RelayServer(host="127.0.0.1", port=0, agent_pick_seconds=2.0, countdown_seconds=0.2)
ready = threading.Event()
port = [0]


def run_relay():
    asyncio.set_event_loop(loop)

    async def start():
        await relay.start()
        port[0] = relay._server.sockets[0].getsockname()[1]
        ready.set()
        await asyncio.Future()
    try:
        loop.run_until_complete(start())
    except asyncio.CancelledError:
        pass


threading.Thread(target=run_relay, daemon=True).start()
assert ready.wait(5)
url = f"ws://127.0.0.1:{port[0]}/ws"


async def flow():
    host = await websockets.connect(url)
    inbox = []

    async def pump():
        try:
            async for raw in host:
                inbox.append(json.loads(raw))
        except Exception:
            pass
    asyncio.ensure_future(pump())
    await host.send(json.dumps({"type": "create_room", "seat": "red", "team_size": 2, "claim": 1, "lobby": True}))
    await asyncio.sleep(0.3)
    code = next(m for m in inbox if m.get("type") == "room_state")["code"]
    await host.send(json.dumps({"type": "room_options", "allow_mcp": True}))
    await asyncio.sleep(0.15)
    await host.send(json.dumps({"type": "ready", "units": ["hag"]}))
    await asyncio.sleep(0.15)
    await host.send(json.dumps({"type": "invite"}))
    await asyncio.sleep(0.3)
    ticket = next(m for m in inbox if m.get("type") == "invite_created")["invite"]
    white = await websockets.connect(url)
    await white.send(json.dumps({"type": "join", "code": code, "seat": "white", "claim": 2, "units": ["skeleton", "wizard"]}))
    await asyncio.sleep(0.15)
    await white.send(json.dumps({"type": "ready"}))
    server = mcp_srv.McpServer(mcp_srv.Session(seed=1), enable_room_tools=True, default_relay_url=url, page_judge_mode="off")
    ev = asyncio.get_running_loop()
    try:
        err, joined = await ev.run_in_executor(None, call, server, "join_room", {"room": code, "units": 2, "invite": ticket})
        print("join_room err=%s heroes_offered=%s" % (err, joined.get("briefing", {}).get("heroes")))
        err, locked = await ev.run_in_executor(None, call, server, "lock_hero", {"hero": "hag"})
        print("lock_hero(hag, taken by inviter) err=%s %s" % (err, locked))
        await asyncio.sleep(0.5)
        print("relay.failure after refusal:", server.relay.failure)
        err, retry = await ev.run_in_executor(None, call, server, "lock_hero", {"hero": "bat"})
        print("lock_hero(bat) retry err=%s %s" % (err, retry))
        err, wait = await ev.run_in_executor(None, call, server, "wait_for_turn", {"timeout_seconds": 1})
        print("wait_for_turn err=%s status=%s error=%s" % (err, wait.get("status"), wait.get("error")))
        await host.send(json.dumps({"type": "begin"}))
        await asyncio.sleep(3.5)   # pick sweep (2 s) readies the agent with a free hero, then countdown
        start = next((m for m in inbox if m.get("type") == "start"), None)
        print("start heroes=%s owners=%s" % (start and start.get("heroes"), start and start.get("owners")))
        print("bridge started=%s failure=%s" % (server.relay.started, server.relay.failure))
        err, wait = await ev.run_in_executor(None, call, server, "wait_for_turn", {"timeout_seconds": 1})
        print("wait_for_turn after start err=%s status=%s error=%s" % (err, wait.get("status"), wait.get("error")))
        err, rejoin = await ev.run_in_executor(None, call, server, "join_room", {"room": code, "units": 2, "invite": ticket})
        print("join_room again err=%s %s" % (err, rejoin))
    finally:
        await ev.run_in_executor(None, server.close)
        await host.close()
        await white.close()


fut = asyncio.run_coroutine_threadsafe(flow(), loop)
fut.result(timeout=60)
