#!/usr/bin/env python3
"""Three-round local relay check using the same bridge behind --connect."""
import asyncio
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import mcp_stdio_server as srv  # noqa: E402
from pk_relay_client import RelayClient  # noqa: E402


class RelayTrace:
    """Record the bridge boundary without retaining private bootstrap values."""

    _PRIVATE_KEYS = {"code", "seat_token"}

    def __init__(self):
        descriptor, name = tempfile.mkstemp(prefix="pk-e2e-", suffix=".jsonl")
        os.close(descriptor)
        self.path = Path(name)
        self._lock = threading.Lock()

    @classmethod
    def _redact(cls, value):
        if isinstance(value, dict):
            return {key: ("<redacted>" if key in cls._PRIVATE_KEYS else cls._redact(item))
                    for key, item in value.items()}
        if isinstance(value, list):
            return [cls._redact(item) for item in value]
        return value

    def record(self, direction, seat, message):
        entry = {"time": round(time.monotonic(), 6), "direction": direction,
                 "seat": seat, "message": self._redact(message)}
        with self._lock:
            with self.path.open("a", encoding="utf-8") as output:
                output.write(json.dumps(entry, sort_keys=True) + "\n")


class TracedQueue:
    """Keep the bridge queue behaviour while recording every relay send."""

    def __init__(self, queue, trace, seat):
        self._queue = queue
        self._trace = trace
        self._seat = seat

    def put(self, message, block=True, timeout=None):
        self._trace.record("send", self._seat, message)
        if timeout is None:
            return self._queue.put(message, block)
        return self._queue.put(message, block, timeout)

    def get_nowait(self):
        return self._queue.get_nowait()


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def relay_reachable(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.1):
            return True
    except OSError:
        return False


def wait_for(predicate, message, seconds=5):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError(message)


async def create_room(url):
    # A disconnected spectator preserves the invitation-room session while the
    # two --connect bridges take the red and white player seats.
    host = RelayClient(url, None, "spectator")
    state = await host.connect()
    await host.close()
    return state["code"]


def call(server, name, arguments):
    response = server._call_tool(name, arguments)
    if response["isError"]:
        raise AssertionError("%s failed (phase=%s, round=%s): %s" % (
            name, server.session.phase, server.session.engine.round_num,
            response["content"][0]["text"]))


def private_slots_hidden(view):
    encoded = repr(view).lower()
    return "item_slot" not in encoded and "itemslots" not in encoded


def _turn_from_message(message):
    message_type = message.get("type")
    if message_type == "end_turn":
        round_number, team = message.get("next_round"), message.get("next_phase")
    elif message_type == "start" or (message_type == "room_state" and message.get("started")):
        round_number, team = message.get("round"), message.get("phase")
    else:
        return None
    if isinstance(round_number, int) and team in ("red", "white"):
        return round_number, team
    return None


def trace_bridge(bridge, seat, trace, relay_turns, turns_lock):
    """Trace and retain only public turn metadata from relay messages."""
    receive = bridge._receive

    def traced_receive(message):
        trace.record("receive", seat, message)
        turn = _turn_from_message(message)
        if turn is not None:
            with turns_lock:
                relay_turns[seat] = turn
        receive(message)

    bridge._receive = traced_receive
    bridge.outgoing = TracedQueue(bridge.outgoing, trace, seat)


def agreed_relay_turn(relay_turns, turns_lock):
    with turns_lock:
        red_turn = relay_turns.get("red")
        white_turn = relay_turns.get("white")
    return red_turn if red_turn is not None and red_turn == white_turn else None


def run_e2e(rounds=3):
    port = free_port()
    url = "ws://127.0.0.1:%d/ws" % port
    env = dict(os.environ, HOST="127.0.0.1", PORT=str(port))
    relay = subprocess.Popen([sys.executable, "-B", str(HERE / "pk_relay.py")],
                             cwd=str(HERE.parent), env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    bridges = []
    trace = RelayTrace()
    relay_turns = {}
    turns_lock = threading.Lock()
    try:
        wait_for(lambda: relay.poll() is None, "relay subprocess exited early")
        wait_for(lambda: relay_reachable(port), "relay subprocess did not listen")
        code = asyncio.run(create_room(url))
        sessions = {}
        servers = {}
        for seat in ("red", "white"):
            session = srv.Session(seed=1, units=1, hero_red="skeleton", hero_white="wizard",
                                  seat=seat, turn_seconds=30, human_turn_seconds=30)
            server = srv.McpServer(session)
            bridge = srv.ConnectedRelay(session, url, code, seat, auto_ready=True)
            trace_bridge(bridge, seat, trace, relay_turns, turns_lock)
            server.relay = bridge
            bridge.start()
            sessions[seat], servers[seat] = session, server
            bridges.append(bridge)
        red_bridge, white_bridge = bridges
        wait_for(lambda: red_bridge.ready.is_set() and white_bridge.ready.is_set(), "bridges did not join")
        wait_for(lambda: agreed_relay_turn(relay_turns, turns_lock) is not None,
                 "bridges did not receive one relay start state")
        wait_for(lambda: sessions["red"].engine.seed == sessions["white"].engine.seed,
                 "bridges did not receive one match seed")

        hashes = []
        while len(hashes) < rounds:
            relay_turn = agreed_relay_turn(relay_turns, turns_lock)
            if relay_turn is None:
                raise AssertionError("bridges disagree about the relay turn; trace=%s" % trace.path)
            relay_round, actor = relay_turn
            actor_phase = "human" if actor == "red" else "agent"
            wait_for(lambda: all(session.engine.round_num == relay_round and
                                 session.relay_team == actor and session.phase == actor_phase
                                 for session in sessions.values()),
                     "%s bridges did not apply relay round %d before its action; trace=%s" %
                     (actor, relay_round, trace.path))
            actor_bridge = red_bridge if actor == "red" else white_bridge
            call(servers[actor], "submit_action", {"unit": actor + "_1", "round": relay_round,
                                                     "action": {"type": "throw", "angle": 54, "power": 25}})
            try:
                wait_for(lambda: not actor_bridge.unacked and not actor_bridge.outbound,
                         "%s action was not acknowledged and judged" % actor)
            except AssertionError as error:
                raise AssertionError("%s; red=%s/%s white=%s/%s bridge=%s trace=%s" % (
                    error, sessions["red"].phase, sessions["red"].engine.round_num,
                    sessions["white"].phase, sessions["white"].engine.round_num,
                    actor_bridge.failure, trace.path))
            call(servers[actor], "end_turn", {"round": relay_round, "phase": actor_phase})
            wait_for(lambda: (agreed_relay_turn(relay_turns, turns_lock) is not None and
                              agreed_relay_turn(relay_turns, turns_lock) != relay_turn),
                     "%s end turn was not applied by both bridges; trace=%s" % (actor, trace.path))
            next_turn = agreed_relay_turn(relay_turns, turns_lock)
            time.sleep(0.5)   # a real turn lasts seconds; the relay limits a seat to 10 messages per second and answers faster traffic with rate_limited
            next_round, next_actor = next_turn
            next_phase = "human" if next_actor == "red" else "agent"
            wait_for(lambda: all(session.engine.round_num == next_round and
                                 session.relay_team == next_actor and session.phase == next_phase
                                 for session in sessions.values()),
                     "relay advanced to round %d/%s but a bridge did not apply its opponent end turn; trace=%s" %
                     (next_round, next_actor, trace.path))
            if next_round > relay_round:
                wait_for(lambda: (relay_round in red_bridge.local_hashes and
                                  relay_round in white_bridge.local_hashes),
                         "round %d hashes were not both sent" % relay_round)
                self_hashes = (red_bridge.local_hashes[relay_round], white_bridge.local_hashes[relay_round])
                if self_hashes[0] != self_hashes[1]:
                    raise AssertionError("round %d hash mismatch: %r" % (relay_round, self_hashes))
                hashes.append(self_hashes[0])
                red_view = sessions["red"].view_for(sessions["red"].seats["red"])
                white_view = sessions["white"].view_for(sessions["white"].seats["white"])
                if not private_slots_hidden(red_view) or not private_slots_hidden(white_view):
                    raise AssertionError("private item slots leaked in a seat view")
        return {"code": code, "round_hashes": hashes, "rounds": rounds}
    finally:
        for bridge in bridges:
            bridge.close()
        if relay.poll() is None:
            relay.terminate()
            try:
                relay.wait(timeout=2)
            except subprocess.TimeoutExpired:
                relay.kill()
                relay.wait(timeout=2)


# ---------------------------------------------------------------------------
# Team battle over the relay (2026-11-17): 2 v 2 and 3 v 3 with unit ids and the round hash over every unit.
# Two "devices" (a red seat and a white seat) each keep their own copy of the match and apply relay messages
# in seq order. The same play loop runs over real sockets (run_team_relay_e2e, needs loopback permission) and
# over the relay's dispatch function in one process (run_team_match_in_process, runs anywhere).
# ---------------------------------------------------------------------------
TEAM_SIDES = {"red": "left", "white": "right"}
TEAM_DAMAGE = 45.0


class TeamDevice:
    """One seat's local copy of the public match state, driven only by ordered relay messages."""

    def __init__(self, team_size):
        self.team_size = team_size
        self.units = {}
        for side, base_x in (("left", 250.0), ("right", 1670.0)):
            for index in range(team_size):
                self.units["%s_%d" % (side, index)] = {
                    "id": "%s_%d" % (side, index), "x": base_x + (120.0 if side == "left" else -120.0) * index,
                    "y": 860.0, "hp": 100.0, "alive": True, "statuses": []}
        self.applied_seq = 0
        self.actions = {}
        self.out_of_sync = []

    def apply(self, message):
        seq = message.get("seq")
        if isinstance(seq, int):
            if seq <= self.applied_seq:
                return
            self.applied_seq = seq
        kind = message.get("type")
        if kind == "action":
            self.actions[seq] = message
        elif kind == "judge" and message.get("hit"):
            unit = self.units[message["unit"]]
            unit["hp"] = float(message["hp_after"])
            unit["alive"] = unit["hp"] > 0
        elif kind == "out_of_sync":
            self.out_of_sync.append(message["round"])

    def living(self, side):
        return [unit for unit_id, unit in sorted(self.units.items()) if unit_id.startswith(side + "_") and unit["alive"]]

    def hash_state(self, round_number, seed):
        import round_hash_py
        return round_hash_py.hash_state({
            "teamSize": self.team_size, "units": [dict(unit) for unit in self.units.values()], "wallHp": 100,
            "round": round_number, "phase": "round_end", "seed": seed})


class WebSocketSeat:
    def __init__(self, url):
        self.url = url
        self.socket = None
        self.bootstrap = None

    async def open(self, message):
        import websockets
        self.socket = await websockets.connect(self.url, max_size=16 * 1024)
        await self.send(message)
        self.bootstrap = json.loads(await asyncio.wait_for(self.socket.recv(), 2))
        return self.bootstrap

    async def send(self, message):
        await self.socket.send(json.dumps(message, separators=(",", ":")))

    async def drain(self, idle=0.12):
        received = []
        while True:
            try:
                received.append(json.loads(await asyncio.wait_for(self.socket.recv(), idle)))
            except asyncio.TimeoutError:
                return received

    async def close(self):
        if self.socket is not None:
            await self.socket.close()


class ProcessSeat:
    """The same seat interface, but calling the relay's dispatch function directly (no socket)."""

    class _Socket:
        def __init__(self):
            self.sent = []

        async def send(self, text):
            self.sent.append(json.loads(text))

    def __init__(self, relay):
        self.relay = relay
        self.socket = self._Socket()
        self.room = None
        self.entry = None
        self.bootstrap = None

    async def open(self, message):
        await self.send(message)
        self.bootstrap = self.socket.sent.pop(0)
        return self.bootstrap

    async def send(self, message):
        self.room, self.entry = await self.relay._dispatch(self.socket, self.room, self.entry, message, [])

    async def drain(self, idle=0.0):
        received, self.socket.sent = self.socket.sent, []
        return received

    async def close(self):
        if self.room is not None and self.socket in self.room.clients:
            await self.relay._remove_client(self.room, self.socket)


async def play_team_match(red, white, team_size, rounds, pause=0.0):
    """Create a team room, play `rounds` full rounds, and check that both devices agree after each one."""
    state = await red.open({"type": "create_room", "seat": "red", "team_size": team_size,
                            "units": ["skeleton", "wizard", "bat"][:team_size], "client_version": "e2e-team"})
    assert state["team_size"] == team_size, state
    await white.open({"type": "join", "code": state["code"], "seat": "white",
                      "units": ["wizard", "skeleton", "hag"][:team_size], "client_version": "e2e-team"})
    seats = {"red": red, "white": white}
    devices = {"red": TeamDevice(team_size), "white": TeamDevice(team_size)}
    errors = []

    async def pump():
        batches = {team: await seat.drain() for team, seat in seats.items()}
        for team, batch in batches.items():
            errors.extend(message for message in batch if message.get("type") == "error")
            for message in sorted((m for m in batch if isinstance(m.get("seq"), int)), key=lambda m: m["seq"]):
                devices[team].apply(message)
        return batches

    async def say(team, message):
        await seats[team].send(message)
        await asyncio.sleep(pause)
        return await pump()

    await red.send({"type": "ready"})
    await white.send({"type": "ready"})
    await asyncio.sleep(pause)
    batches = await pump()
    start = next(m for batch in batches.values() for m in batch if m.get("type") == "start")
    # start.team_size, heroes and owners reach every seat. The batches above were consumed by pump, so look at the log.
    assert start["team_size"] == team_size and set(start["heroes"]) == {"left", "right"}, start
    assert len(start["owners"]) == 2 * team_size, start
    seed = start["seed"]
    last_actor = {"left": -1, "right": -1}
    hashes = []
    for round_number in range(1, rounds + 1):
        order = ("red", "white")   # the first team is fixed (owner 2026-11-17): red opens every round
        for team in order:
            side, enemy = TEAM_SIDES[team], TEAM_SIDES["white" if team == "red" else "red"]
            actor_device = devices[team]
            living = actor_device.living(side)
            # fixed id order: the first living unit after the one that acted last, wrapping around
            candidates = [unit for unit in living if int(unit["id"].split("_")[1]) > last_actor[side]] or living
            actor = candidates[0]
            last_actor[side] = int(actor["id"].split("_")[1])
            if round_number == 1 and team == "red":
                await say(team, {"type": "action", "round": round_number, "phase": team, "unit": actor["id"],
                                 "kind": "move", "die": 3, "dirX": 1, "result": {"x": actor["x"] + 60, "y": actor["y"]}})
                actor_device.units[actor["id"]]["x"] += 60
                devices["white"].units[actor["id"]]["x"] += 60
            batches = await say(team, {"type": "action", "round": round_number, "phase": team, "unit": actor["id"],
                                       "kind": "throw", "angle": 54, "power": 40,
                                       "start": {"x": actor["x"], "y": actor["y"] - 100},
                                       "claimed_landing": {"x": 1000, "y": 860}, "dirX": 1})
            action = next(m for m in batches[team] if m.get("type") == "action")
            other = "white" if team == "red" else "red"
            victim = devices[other].living(enemy)[0]            # the first living enemy unit is the one hit
            hp_after = max(0.0, victim["hp"] - TEAM_DAMAGE)
            await say(other, {"type": "judge", "ref": action["seq"], "hit": True, "unit": victim["id"],
                              "damage": TEAM_DAMAGE, "hp_after": hp_after, "statuses": []})
            await say(team, {"type": "end_turn", "round": round_number, "phase": team})
        digests = {team: devices[team].hash_state(round_number, seed) for team in seats}
        assert digests["red"] == digests["white"], "round %d devices disagree: %r" % (round_number, digests)
        for team in seats:
            await say(team, {"type": "round_hash", "round": round_number, "hash": digests[team]})
        hashes.append(digests["red"])
        assert not errors, "relay errors: %r" % errors
        assert not devices["red"].out_of_sync and not devices["white"].out_of_sync, "unexpected out_of_sync"
        await asyncio.sleep(pause)
    # A device that forgot a unit or kept a different hp must be caught: send different hashes for one more round.
    await say("red", {"type": "round_hash", "round": rounds + 1, "hash": hashes[-1]})
    await say("white", {"type": "round_hash", "round": rounds + 1, "hash": "%08x" % ((int(hashes[-1], 16) + 1) & 0xffffffff)})
    await asyncio.sleep(pause)
    await pump()
    assert devices["red"].out_of_sync == [rounds + 1] and devices["white"].out_of_sync == [rounds + 1], "divergence not reported"
    assert not errors, "relay errors: %r" % errors
    dead = sum(1 for unit in devices["red"].units.values() if not unit["alive"])
    return {"team_size": team_size, "rounds": rounds, "round_hashes": hashes, "dead_units": dead}


def run_team_match_in_process(team_size, rounds=5):
    """Socket-free: the relay's dispatch function with in-memory seats."""
    from pk_relay import RelayServer
    relay = RelayServer("127.0.0.1", 0)
    return asyncio.run(play_team_match(ProcessSeat(relay), ProcessSeat(relay), team_size, rounds))


def run_team_relay_e2e(team_size, rounds=5):
    """Real relay subprocess and real WebSocket clients; needs loopback permission."""
    port = free_port()
    env = dict(os.environ, HOST="127.0.0.1", PORT=str(port))
    relay = subprocess.Popen([sys.executable, "-B", str(HERE / "pk_relay.py")], cwd=str(HERE.parent), env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_for(lambda: relay.poll() is None, "relay subprocess exited early")
        wait_for(lambda: relay_reachable(port), "relay subprocess did not listen")
        url = "ws://127.0.0.1:%d/ws" % port

        async def run():
            red, white = WebSocketSeat(url), WebSocketSeat(url)
            try:
                return await play_team_match(red, white, team_size, rounds, pause=0.15)   # a seat may send 10 messages a second; each step here takes more than 0.35 s
            finally:
                await red.close()
                await white.close()
        return asyncio.run(run())
    finally:
        if relay.poll() is None:
            relay.terminate()
            try:
                relay.wait(timeout=2)
            except subprocess.TimeoutExpired:
                relay.kill()
                relay.wait(timeout=2)


if __name__ == "__main__":
    result = run_e2e()
    print("e2e_local: %d rounds agree; private item slots hidden" % result["rounds"])
    for size in (2, 3):
        team_result = run_team_relay_e2e(size)
        print("e2e_local: %d v %d team match, %d rounds agree (%d units fell); divergence reported" % (
            size, size, team_result["rounds"], team_result["dead_units"]))
