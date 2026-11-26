#!/usr/bin/env python3
"""Integration tests for the localhost-only Pumpkin Killer room relay."""
import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import websockets

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pk_relay import MAX_MESSAGE_BYTES, RelayServer, Room  # noqa: E402
from pk_relay_client import RelayClient  # noqa: E402


class RelayTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.relay = RelayServer("127.0.0.1", 0)
        await self.relay.start()
        self.url = f"ws://127.0.0.1:{self.relay.bound_port}/ws"
        self.clients = []

    async def asyncTearDown(self):
        for client in self.clients:
            await client.close()
        await self.relay.close()

    async def client(self, seat, code=None, **options):
        client = RelayClient(self.url, code, seat, **options)
        self.clients.append(client)
        return client, await client.connect()

    async def create_host(self, host_side_choice):
        socket = await websockets.connect(self.url, max_size=MAX_MESSAGE_BYTES)
        self.clients.append(socket)
        message = {"type": "create_room", "seat": "red", "client_version": "test"}
        if host_side_choice is not None:
            message["host_side_choice"] = host_side_choice
        await socket.send(json.dumps(message))
        return socket, json.loads(await asyncio.wait_for(socket.recv(), 1))

    async def read_socket_type(self, socket, message_type):
        for _ in range(20):
            message = json.loads(await asyncio.wait_for(socket.recv(), 1))
            if message.get("type") == message_type:
                return message
        self.fail(f"did not receive {message_type}")

    async def read_type(self, client, message_type):
        for _ in range(20):
            message = await asyncio.wait_for(client.receive(), 1)
            if message.get("type") == message_type:
                return message
        self.fail(f"did not receive {message_type}")

    async def start_pair(self):
        red, state = await self.client("red")
        code = state["code"]
        white, _ = await self.client("white", code)
        await red.send({"type": "ready"})
        await white.send({"type": "ready"})
        red_start = await self.read_type(red, "start")
        white_start = await self.read_type(white, "start")
        self.assertEqual(red_start["seed"], white_start["seed"])
        self.assertIsInstance(red_start["seed"], int)
        self.assertGreaterEqual(red_start["seed"], 1)
        self.assertLessEqual(red_start["seed"], (1 << 31) - 1)
        self.assertEqual(red_start["scene"], "graveyard")
        self.assertEqual(red_start["first_team"], "red")
        return red, white, code, red_start

    async def health(self):
        reader, writer = await asyncio.open_connection("127.0.0.1", self.relay.bound_port)
        writer.write(b"GET /health HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
        await writer.drain()
        response = await reader.read()
        writer.close()
        await writer.wait_closed()
        self.assertIn(b"200", response.split(b"\r\n", 1)[0])
        self.assertTrue(response.endswith(b"ok\n"))

    async def test_create_join_and_wrong_code(self):
        red, state = await self.client("red")
        self.assertEqual(state["type"], "room_state")
        code = state["code"]
        white, joined = await self.client("white", code)
        self.assertEqual(joined["code"], code)
        bad, error = await self.client("spectator", "BAD999")
        self.assertEqual(error, {"type": "error", "code": "unknown_code"})
        await red.close()
        await white.close()
        await bad.close()

    async def test_start_requires_both_teams_unless_the_room_is_solo(self):
        red, state = await self.client("red")
        await red.send({"type": "ready"})
        await asyncio.sleep(0)
        self.assertFalse(self.relay.rooms[state["code"]].started)
        white, _ = await self.client("white", state["code"])
        await white.send({"type": "ready"})
        await self.read_type(red, "start")

        solo, solo_state = await self.client("red", solo=True, scene="belltower")
        await solo.send({"type": "ready"})
        solo_start = await self.read_type(solo, "start")
        self.assertEqual(solo_start["scene"], "belltower")
        self.assertTrue(self.relay.rooms[solo_state["code"]].started)

    async def test_a_seat_that_leaves_before_the_start_lets_the_ready_seats_start(self):
        # unit slot fill (docs/ADR_unit_slot_fill_20261124.md): a placeholder seat holds the start back, then leaves; nobody sends another `ready`
        red, state = await self.client("red")
        holder, _ = await self.client("white", state["code"])
        white, _ = await self.client("white", state["code"])
        await red.send({"type": "ready"})
        await white.send({"type": "ready"})
        await asyncio.sleep(0.05)
        self.assertFalse(self.relay.rooms[state["code"]].started, "the unready placeholder holds the start back")
        await holder.send({"type": "leave"})
        start = await self.read_type(red, "start")
        self.assertEqual(start["type"], "start")
        self.assertTrue(self.relay.rooms[state["code"]].started)

    async def test_a_leaving_seat_does_not_start_a_room_without_both_teams(self):
        red, state = await self.client("red")
        holder, _ = await self.client("white", state["code"])
        await red.send({"type": "ready"})
        await asyncio.sleep(0.05)
        await holder.send({"type": "leave"})
        await asyncio.sleep(0.1)
        self.assertFalse(self.relay.rooms[state["code"]].started, "only red is left: no start")

    async def test_a_leave_after_the_start_changes_nothing_about_the_start(self):
        red, state = await self.client("red")
        white, _ = await self.client("white", state["code"])
        await red.send({"type": "ready"})
        await white.send({"type": "ready"})
        await self.read_type(red, "start")
        seed = self.relay.rooms[state["code"]].seed
        await white.send({"type": "leave"})
        await asyncio.sleep(0.1)
        self.assertEqual(self.relay.rooms[state["code"]].seed, seed, "no second start, the seed is unchanged")

    async def test_host_side_choice_is_resolved_once_by_the_relay(self):
        host, state = await self.create_host("left")
        white, _ = await self.client("white", state["code"])
        await host.send(json.dumps({"type": "ready"}))
        await white.send({"type": "ready"})
        host_start = await self.read_socket_type(host, "start")
        white_start = await self.read_type(white, "start")
        self.assertEqual(host_start["host_side_choice"], "left")
        self.assertEqual(white_start["host_side_choice"], "left")
        self.assertIsNone(self.relay.rooms[state["code"]].host_side_coin)

        computer_host, computer_state = await self.create_host("computer")
        computer_white, _ = await self.client("white", computer_state["code"])
        with patch("pk_relay.secrets.randbits", side_effect=[123456, 2]):
            await computer_host.send(json.dumps({"type": "ready"}))
            await computer_white.send({"type": "ready"})
            computer_start = await self.read_socket_type(computer_host, "start")
        computer_room = self.relay.rooms[computer_state["code"]]
        self.assertEqual(computer_start["host_side_choice"], "left")
        self.assertEqual(computer_room.host_side_coin, 2)
        self.assertEqual(computer_room.resolved_host_side, "left")
        self.assertNotEqual(computer_room.host_side_coin, computer_room.seed)

    async def test_host_side_choice_ready_override_and_invalid_values_are_ignored(self):
        host, state = await self.create_host("not-a-side")
        white, _ = await self.client("white", state["code"])
        await host.send(json.dumps({"type": "ready", "host_side_choice": "right"}))
        await white.send({"type": "ready"})
        self.assertEqual((await self.read_socket_type(host, "start"))["host_side_choice"], "right")

        old_host, old_state = await self.create_host(None)
        old_white, _ = await self.client("white", old_state["code"])
        await old_host.send(json.dumps({"type": "ready", "host_side_choice": "invalid"}))
        await old_white.send({"type": "ready"})
        old_start = await self.read_socket_type(old_host, "start")
        self.assertNotIn("host_side_choice", old_start)

    async def test_start_has_shared_seed_and_increasing_sequence(self):
        red, white, _, started = await self.start_pair()
        await red.send({"type": "action", "round": 1, "phase": "red", "unit": "red_1",
                        "kind": "throw", "angle": 54, "power": 50, "path": [[1, 2]]})
        action = await self.read_type(white, "action")
        self.assertGreater(action["seq"], started["seq"])
        self.assertEqual((action["angle"], action["power"]), (54, 50))   # changed 2026-11-15: the target device needs the numbers to recompute the flight (hiding them from an agent is the MCP view's job)
        self.assertNotIn("path", action)
        self.assertEqual(action["unit"], "red_1")

    async def test_replayed_end_turn_and_duplicate_action_category_are_dropped(self):
        red, white, _, _ = await self.start_pair()
        await red.send({"type": "end_turn", "round": 1, "phase": "red"})
        ended = await self.read_type(white, "end_turn")
        self.assertEqual(ended["next_phase"], "white")
        await red.send({"type": "end_turn", "round": 1, "phase": "red"})
        self.assertEqual((await self.read_type(red, "error"))["code"], "stale_or_out_of_turn")
        await white.send({"type": "action", "round": 1, "phase": "white", "unit": "white_1",
                          "kind": "move", "die": 4})
        moved = await self.read_type(red, "action")
        self.assertEqual(moved["die"], 4)
        await white.send({"type": "action", "round": 1, "phase": "white", "unit": "white_2",
                          "kind": "throw", "bounce": 2})
        attacked = await self.read_type(red, "action")
        self.assertEqual(attacked["bounce"], 2)
        await white.send({"type": "action", "round": 1, "phase": "white", "unit": "white_3",
                          "kind": "move", "die": 1})
        self.assertEqual((await self.read_type(white, "error"))["code"], "action_already_submitted")
        await white.send({"type": "action", "round": 1, "phase": "white", "unit": "white_3",
                          "kind": "throw", "bounce": 3})
        self.assertEqual((await self.read_type(white, "error"))["code"], "action_already_submitted")

    async def test_action_forwards_flight_numbers_and_sender_gets_the_stamp(self):
        # protocol section 2 (2026-11-15): angle, power, start and claimed_landing reach the target; the sender gets action_ack with the same seq
        red, white, _, _ = await self.start_pair()
        await red.send({"type": "action", "round": 1, "phase": "red", "unit": "red_1", "kind": "throw",
                        "angle": 54, "power": 62.5, "start": {"x": 320, "y": 700}, "claimed_landing": {"x": 1190, "y": 860}, "dirX": 1})
        got = await self.read_type(white, "action")
        ack = await self.read_type(red, "action_ack")
        self.assertEqual((got["angle"], got["power"], got["start"], got["claimed_landing"]), (54, 62.5, {"x": 320, "y": 700}, {"x": 1190, "y": 860}))
        self.assertEqual(got["seq"], ack["seq"])
        self.assertNotIn("path", got)

    async def test_action_rejects_out_of_range_die_and_bounce(self):
        red, _, _, _ = await self.start_pair()
        await red.send({"type": "action", "round": 1, "phase": "red", "unit": "red_1",
                        "kind": "move", "die": 0})
        error = await self.read_type(red, "error")
        self.assertEqual(error["code"], "invalid_die")
        self.assertIn("integer from 1 to 6", error["message"])
        await red.send({"type": "action", "round": 1, "phase": "red", "unit": "red_1",
                        "kind": "throw", "bounce": 6.0})
        error = await self.read_type(red, "error")
        self.assertEqual(error["code"], "invalid_bounce")
        self.assertIn("integer from 1 to 6", error["message"])

    async def test_judge_hashes_and_spectator_permissions(self):
        red, white, code, _ = await self.start_pair()
        spectator, _ = await self.client("spectator", code)
        await red.send({"type": "action", "round": 1, "phase": "red", "unit": "red_1",
                        "kind": "throw", "path": [[1, 2]]})
        action = await self.read_type(white, "action")
        await white.send({"type": "judge", "ref": action["seq"], "hit": True, "unit": "red_1",
                          "damage": 10, "hp_after": 80, "statuses": []})
        judge = await self.read_type(red, "judge")
        self.assertEqual(judge["ref"], action["seq"])
        await red.send({"type": "round_hash", "round": 1, "hash": "aaaa"})
        await white.send({"type": "round_hash", "round": 1, "hash": "bbbb"})
        self.assertEqual((await self.read_type(red, "out_of_sync"))["round"], 1)
        await spectator.send({"type": "action", "round": 1, "phase": "red", "unit": "x", "kind": "throw"})
        self.assertEqual((await self.read_type(spectator, "error"))["code"], "stale_or_out_of_turn")

    async def test_resume_reclaims_the_same_token_and_replays_the_ordered_log(self):
        red, initial = await self.client("red")
        token = initial["seat_token"]
        code = initial["code"]
        white, _ = await self.client("white", code)
        await red.send({"type": "ready"})
        await white.send({"type": "ready"})
        await self.read_type(red, "start")
        await self.read_type(white, "start")
        await red.close()
        await asyncio.sleep(0)
        resumed = await websockets.connect(self.url, max_size=MAX_MESSAGE_BYTES)
        self.addAsyncCleanup(resumed.close)
        await resumed.send(json.dumps({"type": "resume", "seat_token": token, "last_seq": 0}))
        bootstrap = json.loads(await asyncio.wait_for(resumed.recv(), 1))
        self.assertEqual(bootstrap["type"], "room_state")
        self.assertEqual(bootstrap["seat_token"], token)
        self.assertEqual(bootstrap["seat"], "red")
        replay = []
        for _ in range(10):
            replay.append(json.loads(await asyncio.wait_for(resumed.recv(), 1)))
            if any(message.get("type") == "start" for message in replay):
                break
        self.assertTrue(any(message.get("type") == "start" for message in replay))
        self.assertEqual([message["seq"] for message in replay], sorted(message["seq"] for message in replay))

    async def test_join_rejects_unit_lists_longer_than_three(self):
        red, state = await self.client("red")
        oversized = await websockets.connect(self.url, max_size=MAX_MESSAGE_BYTES)
        self.clients.append(oversized)
        await oversized.send(json.dumps({"type": "join", "code": state["code"], "seat": "white",
                                         "units": ["one", "two", "three", "four"], "client_version": "test"}))
        error = json.loads(await asyncio.wait_for(oversized.recv(), 1))
        self.assertEqual(error, {"type": "error", "code": "invalid_units"})
        await red.close()
        await oversized.close()

    async def test_limits_health_room_expiry_and_seat_capacity(self):
        red, white, code, _ = await self.start_pair()
        await asyncio.sleep(1.05)
        for _ in range(11):
            await red.send({"type": "round_hash", "round": 1, "hash": "same"})
        self.assertEqual((await self.read_type(red, "error"))["code"], "rate_limited")
        bad_socket = await websockets.connect(self.url, max_size=MAX_MESSAGE_BYTES * 2)
        with self.assertRaises(websockets.exceptions.ConnectionClosed):
            await bad_socket.send("x" * (MAX_MESSAGE_BYTES + 1))
            await bad_socket.recv()
        await self.health()
        await asyncio.sleep(1.05)
        await red.send({"type": "leave"})
        await white.send({"type": "leave"})
        await red.close()
        await white.close()
        await asyncio.sleep(0)
        rejected, error = await self.client("red", code)
        self.assertEqual(error["code"], "unknown_code")
        await rejected.close()

        owner, state = await self.client("red")
        room_code = state["code"]
        for _ in range(3):
            await self.client("red", room_code)
        for _ in range(4):
            await self.client("white", room_code)
        self.assertEqual(len(self.relay.rooms[room_code].clients), 8)
        self.assertEqual(self.relay.rooms[room_code].team_count("red"), 4)
        self.assertEqual(self.relay.rooms[room_code].team_count("white"), 4)
        await owner.close()


    # ---- team battle over real sockets (2026-11-17); the same rules are checked socket-free in RelayTeamLogicTests
    async def create_team_host(self, team_size, units=None, seat="red"):
        socket = await websockets.connect(self.url, max_size=MAX_MESSAGE_BYTES)
        self.clients.append(socket)
        message = {"type": "create_room", "seat": seat, "team_size": team_size, "client_version": "test"}
        if units is not None:
            message["units"] = units
        await socket.send(json.dumps(message))
        return socket, json.loads(await asyncio.wait_for(socket.recv(), 1))

    async def test_team_start_carries_size_heroes_and_owners(self):
        host, state = await self.create_team_host(2, ["skeleton", "wizard"])
        self.assertEqual(state["team_size"], 2)
        white = await websockets.connect(self.url, max_size=MAX_MESSAGE_BYTES)
        self.clients.append(white)
        await white.send(json.dumps({"type": "join", "code": state["code"], "seat": "white", "units": ["bat"]}))
        await host.send(json.dumps({"type": "ready"}))
        await white.send(json.dumps({"type": "ready"}))
        start = await self.read_socket_type(host, "start")
        self.assertEqual(start["team_size"], 2)
        self.assertEqual(start["heroes"], {"left": ["skeleton", "wizard"], "right": ["bat", None]})
        self.assertEqual(start["owners"], {"left_0": "red-1", "left_1": "red-1", "right_0": "white-1", "right_1": "white-1"})
        await host.send(json.dumps({"type": "action", "round": 1, "phase": "red", "unit": "left_1", "kind": "throw",
                                    "angle": 54, "power": 50}))
        forwarded = await self.read_socket_type(white, "action")
        self.assertEqual(forwarded["unit"], "left_1")
        await host.send(json.dumps({"type": "action", "round": 1, "phase": "red", "unit": "left_2", "kind": "move", "die": 2}))
        self.assertEqual((await self.read_socket_type(host, "error"))["code"], "invalid_unit")

    async def test_one_versus_one_start_is_unchanged_on_the_wire(self):
        _, _, _, started = await self.start_pair()
        self.assertEqual(set(started), {"type", "seed", "scene", "first_team", "round", "phase", "seq"})


class FakeSocket:
    """Records what the relay sends; lets the dispatch logic run without a network socket."""

    def __init__(self):
        self.sent = []

    async def send(self, text):
        self.sent.append(json.loads(text))


class Peer:
    def __init__(self, relay):
        self.relay = relay
        self.socket = FakeSocket()
        self.room = None
        self.entry = None
        self.wrong_codes = []

    async def say(self, **message):
        self.room, self.entry = await self.relay._dispatch(self.socket, self.room, self.entry, message, self.wrong_codes)
        return self

    def of_type(self, message_type):
        return [message for message in self.socket.sent if message.get("type") == message_type]

    def last(self, message_type):
        found = self.of_type(message_type)
        return found[-1] if found else None

    def error_codes(self):
        return [message["code"] for message in self.of_type("error")]


class RelayTeamLogicTests(unittest.IsolatedAsyncioTestCase):
    """Team-battle protocol (2026-11-17). Socket-free: these run where local binding is refused."""

    async def asyncSetUp(self):
        self.relay = RelayServer("127.0.0.1", 0)

    async def room_of(self, team_size=None, red_units=None, white_units=None, *, start=True):
        red, white = Peer(self.relay), Peer(self.relay)
        create = {"seat": "red", "client_version": "test"}
        if team_size is not None:
            create["team_size"] = team_size
        if red_units is not None:
            create["units"] = red_units
        await red.say(type="create_room", **create)
        code = red.last("room_state")["code"]
        join = {"code": code, "seat": "white"}
        if white_units is not None:
            join["units"] = white_units
        await white.say(type="join", **join)
        if start:
            await red.say(type="ready")
            await white.say(type="ready")
        return red, white

    @staticmethod
    def act(unit, kind="throw", phase="red", **extra):
        return dict(type="action", round=1, phase=phase, unit=unit, kind=kind, **extra)

    async def test_one_versus_one_wire_is_unchanged(self):
        red, white = await self.room_of()
        self.assertEqual(red.room.team_size, 1)
        for peer in (red, white):
            self.assertNotIn("team_size", peer.last("room_state"))
        start = red.last("start")
        self.assertEqual(set(start), {"type", "seed", "scene", "first_team", "round", "phase", "seq"})
        # Legacy unit ids stay accepted exactly as before: any string.
        await red.say(**self.act("red_1", "move", die=2))
        await red.say(**self.act("anything", "throw", angle=54, power=40))
        self.assertEqual(red.error_codes(), [])
        self.assertEqual([m["unit"] for m in white.of_type("action")], ["red_1", "anything"])
        await red.say(**self.act("left_0", "throw"))
        self.assertEqual(red.error_codes(), ["action_already_submitted"])
        # A one-versus-one round hash is not format-checked.
        await red.say(type="round_hash", round=1, hash="aaaa")
        await white.say(type="round_hash", round=1, hash="bbbb")
        self.assertEqual(white.last("out_of_sync")["round"], 1)

    async def test_team_size_is_validated_when_the_room_is_created(self):
        for bad in (0, 4, -1, 2.0, "2", True, None, [2]):
            peer = Peer(self.relay)
            await peer.say(type="create_room", seat="red", team_size=bad)
            self.assertEqual(peer.error_codes(), ["invalid_team_size"], repr(bad))
            self.assertIsNone(peer.room)
        self.assertEqual(self.relay.rooms, {})
        for good in (1, 2, 3):
            peer = Peer(self.relay)
            await peer.say(type="create_room", seat="red", team_size=good)
            bootstrap = peer.last("room_state")
            self.assertEqual(bootstrap.get("team_size"), None if good == 1 else good)

    async def test_start_names_size_heroes_and_owners_only_for_team_matches(self):
        red, white = await self.room_of(2, ["skeleton", "wizard"], ["bat"])
        start = red.last("start")
        self.assertEqual(start["team_size"], 2)
        self.assertEqual(start["heroes"], {"left": ["skeleton", "wizard"], "right": ["bat", None]})
        self.assertEqual(start["owners"], {"left_0": "red-1", "left_1": "red-1", "right_0": "white-1", "right_1": "white-1"})
        self.assertEqual(start, white.last("start"))
        self.assertEqual(red.room.state()["team_size"], 2)
        three, _ = await self.room_of(3)
        self.assertEqual(three.last("start")["heroes"], {"left": [None] * 3, "right": [None] * 3})
        self.assertEqual(len(three.last("start")["owners"]), 6)

    async def test_host_sets_team_size_and_units_on_ready_and_mistakes_are_loud(self):
        red, white = await self.room_of(2, start=False)
        guest = Peer(self.relay)
        await guest.say(type="join", code=red.room.code, seat="spectator")
        await guest.say(type="ready", team_size=3)        # only the host may change the size; others are ignored
        self.assertEqual(red.room.team_size, 2)
        await red.say(type="ready", team_size=5)
        self.assertEqual(red.error_codes(), ["invalid_team_size"])
        self.assertFalse(red.entry["ready"])
        await red.say(type="ready", units=["a", "b", "c"])  # more units than the team has room for
        self.assertEqual(red.error_codes(), ["invalid_team_size", "invalid_units"])
        self.assertFalse(red.entry["ready"])
        await red.say(type="ready", units=["a", ""])
        self.assertEqual(red.error_codes()[-1], "invalid_units")
        await red.say(type="ready", team_size=3, units=["a", "b", "c"])
        self.assertTrue(red.entry["ready"])
        self.assertEqual((red.room.team_size, red.entry["units"]), (3, ["a", "b", "c"]))
        await white.say(type="ready", units=["z"])
        start = red.last("start")
        self.assertEqual((start["team_size"], start["heroes"]), (3, {"left": ["a", "b", "c"], "right": ["z", None, None]}))
        # after the start nothing about the roster can change any more
        await red.say(type="ready", team_size=1, units=["q"])
        self.assertEqual((red.room.team_size, red.entry["units"]), (3, ["a", "b", "c"]))

    async def test_join_rejects_more_units_than_the_team_size(self):
        red, _ = await self.room_of(2, start=False)
        late = Peer(self.relay)
        await late.say(type="join", code=red.room.code, seat="white", units=["a", "b", "c"])
        self.assertEqual(late.error_codes(), ["invalid_units"])
        spectator = Peer(self.relay)
        await spectator.say(type="join", code=red.room.code, seat="spectator", units=["a", "b", "c"])
        self.assertEqual(spectator.error_codes(), [])

    async def test_actions_need_a_world_unit_id_of_the_senders_side(self):
        red, white = await self.room_of(2)
        for bad, code in (("left_2", "invalid_unit"), ("red_1", "invalid_unit"), ("left", "invalid_unit"),
                          ("left_01", "invalid_unit"), ("right_0", "unit_not_yours"), ("right_1", "unit_not_yours")):
            await red.say(**self.act(bad, "move", die=3))
            self.assertEqual(red.error_codes()[-1], code, bad)
        self.assertEqual(len(white.of_type("action")), 0)
        await red.say(**self.act("left_1", "move", die=3))
        await red.say(**self.act("left_1", "throw", angle=54, power=30, start={"x": 1, "y": 2}))
        self.assertEqual([m["unit"] for m in white.of_type("action")], ["left_1", "left_1"])
        self.assertEqual(len(red.of_type("action_ack")), 2)

    async def test_one_unit_acts_per_team_turn(self):
        red, white = await self.room_of(3)
        await red.say(**self.act("left_0", "move", die=1))
        await red.say(**self.act("left_2", "throw", angle=54, power=30))
        self.assertEqual(red.error_codes(), ["unit_changed_in_turn"])
        await red.say(**self.act("left_0", "throw", angle=54, power=30))
        self.assertEqual(red.error_codes(), ["unit_changed_in_turn"])
        await red.say(**self.act("left_0", "throw", angle=54, power=30))
        self.assertEqual(red.error_codes(), ["unit_changed_in_turn", "action_already_submitted"])
        # the next turn may use another unit
        await red.say(type="end_turn", round=1, phase="red")
        await white.say(**self.act("right_2", "throw", phase="white", angle=54, power=30))
        self.assertEqual(white.error_codes(), [])
        await white.say(type="end_turn", round=1, phase="white")      # round 2 starts with red again: the first team is fixed (owner 2026-11-17)
        self.assertEqual(white.last("end_turn")["next_phase"], "red")
        await red.say(type="action", round=2, phase="red", unit="left_0", kind="throw", angle=54, power=30)
        self.assertEqual(red.error_codes(), ["unit_changed_in_turn", "action_already_submitted"])

    async def test_one_unit_acts_per_team_turn_across_seats(self):
        # LIVE-3V3-1 (2026-11-26, live room XTA54P): an agent seat threw for left_1 and, before it sent end_turn, the computer seat of the same team threw
        # for left_2 in the same round and phase; the relay forwarded both and the two devices then disagreed on whose turn it was (the match stalled).
        red = Peer(self.relay)
        await red.say(type="create_room", seat="red", team_size=2, claim=1, units=["skeleton"], client_version="test")
        code = red.last("room_state")["code"]
        mate, white = Peer(self.relay), Peer(self.relay)
        await mate.say(type="join", code=code, seat="red", claim=1, units=["wizard"], client_version="test")
        await white.say(type="join", code=code, seat="white", units=["hag", "reaper"], client_version="test")
        for peer in (red, mate, white):
            await peer.say(type="ready")
        self.assertIsNotNone(red.last("start"))
        owners = red.last("start").get("owners") or {}
        first, second = ("left_0", "left_1") if owners.get("left_0") == red.entry["seat_id"] else ("left_1", "left_0")
        await red.say(**self.act(first, "throw", angle=54, power=30))
        self.assertEqual(red.error_codes(), [])
        await mate.say(**self.act(second, "throw", angle=54, power=30))
        self.assertEqual(mate.error_codes(), ["unit_changed_in_turn"])
        self.assertEqual([m["unit"] for m in white.of_type("action")], [first])
        # the team's next turn may use the other unit
        await red.say(type="end_turn", round=1, phase="red")
        await white.say(**self.act("right_0", "throw", phase="white", angle=54, power=30))
        await white.say(type="end_turn", round=1, phase="white")
        await mate.say(type="action", round=2, phase="red", unit=second, kind="throw", angle=54, power=30)
        self.assertEqual(mate.error_codes(), ["unit_changed_in_turn"])

    async def test_judge_names_a_unit_of_its_own_side_once(self):
        red, white = await self.room_of(2)
        await red.say(**self.act("left_0", "throw", angle=54, power=30))
        ref = red.last("action_ack")["seq"]
        await white.say(type="judge", ref=ref, hit=True, damage=5)
        self.assertEqual(white.error_codes(), ["invalid_unit"])
        await white.say(type="judge", ref=ref, hit=True, unit="left_0", damage=5)       # an enemy unit
        self.assertEqual(white.error_codes(), ["invalid_unit", "unit_not_yours"])
        await white.say(type="judge", ref=ref, hit=True, unit="right_2", damage=5)       # beyond the team size
        self.assertEqual(white.error_codes()[-1], "invalid_unit")
        await white.say(type="judge", ref=ref, hit=True, unit="right_0", damage=5, hp_after=95, statuses=[])
        await white.say(type="judge", ref=ref, hit=True, unit="right_1", damage=5, hp_after=95, statuses=[])  # an area effect hit two units
        self.assertEqual(len(red.of_type("judge")), 2)
        await white.say(type="judge", ref=ref, hit=True, unit="right_0", damage=5, hp_after=90, statuses=[])
        self.assertEqual(white.error_codes()[-1], "duplicate_judge")
        self.assertEqual(len(red.of_type("judge")), 2)
        await white.say(type="judge", ref=ref, hit=False)
        await white.say(type="judge", ref=ref, hit=False)
        self.assertEqual(white.error_codes()[-1], "duplicate_judge")
        await red.say(type="judge", ref=ref, hit=True, unit="left_0")                    # the attacker cannot judge its own throw
        self.assertEqual(red.error_codes(), ["invalid_judge"])

    async def test_several_seats_on_a_team_own_their_slices(self):
        red, white = Peer(self.relay), Peer(self.relay)
        await red.say(type="create_room", seat="red", team_size=3, units=["skeleton", "wizard"])
        code = red.last("room_state")["code"]
        second = Peer(self.relay)
        await second.say(type="join", code=code, seat="red", units=["bat"])
        await white.say(type="join", code=code, seat="white")
        for peer in (red, second, white):
            await peer.say(type="ready")
        start = red.last("start")
        self.assertEqual(start["heroes"]["left"], ["skeleton", "wizard", "bat"])
        self.assertEqual(start["owners"], {"left_0": "red-1", "left_1": "red-1", "left_2": "red-2",
                                           "right_0": "white-1", "right_1": "white-1", "right_2": "white-1"})
        await red.say(**self.act("left_2", "move", die=2))
        self.assertEqual(red.error_codes(), ["unit_not_yours"])
        await second.say(**self.act("left_0", "move", die=2))
        self.assertEqual(second.error_codes(), ["unit_not_yours"])
        await second.say(**self.act("left_2", "move", die=2))        # its own unit: accepted
        self.assertEqual(second.error_codes(), ["unit_not_yours"])   # still only the one error from left_0
        self.assertEqual([m["unit"] for m in white.of_type("action")], ["left_2"])

    async def test_unknown_owners_stay_lenient(self):
        red, white = Peer(self.relay), Peer(self.relay)
        await red.say(type="create_room", seat="red", team_size=2)
        code = red.last("room_state")["code"]
        second = Peer(self.relay)
        await second.say(type="join", code=code, seat="red")        # two seats, no unit lists: the split is unknown
        await white.say(type="join", code=code, seat="white")
        for peer in (red, second, white):
            await peer.say(type="ready")
        self.assertEqual(red.last("start")["owners"], {"right_0": "white-1", "right_1": "white-1"})
        await second.say(**self.act("left_1", "move", die=2))
        self.assertEqual(second.error_codes(), [])

    async def test_team_round_hash_must_be_eight_hex_characters(self):
        red, white = await self.room_of(2)
        for bad in ("aaaa", "ABCDEF01", "0123456g", "0123456789", 12345678):
            await red.say(type="round_hash", round=1, hash=bad)
        self.assertEqual(red.error_codes(), ["invalid_round_hash"] * 5)
        await red.say(type="round_hash", round=1, hash="0123abcd")
        await white.say(type="round_hash", round=1, hash="0123abcd")
        self.assertEqual(red.of_type("out_of_sync"), [])
        await white.say(type="round_hash", round=1, hash="0123abce")
        self.assertEqual(red.last("out_of_sync")["round"], 1)

    async def test_two_devices_agree_over_five_rounds_of_two_and_three_units(self):
        import e2e_local   # the same play loop that runs over real sockets in e2e_local.py
        loop = asyncio.get_running_loop()
        for size in (2, 3):
            result = await loop.run_in_executor(None, e2e_local.run_team_match_in_process, size, 5)
            self.assertEqual(len(result["round_hashes"]), 5)
            self.assertGreaterEqual(result["dead_units"], 1)   # fallen units stay in the hash and are skipped by the rotation

    async def test_resume_replays_the_team_start(self):
        red, white = await self.room_of(2, ["skeleton", "wizard"])
        token = red.entry["seat_token"]
        await self.relay._remove_client(red.room, red.socket)
        back = Peer(self.relay)
        await back.say(type="resume", seat_token=token, last_seq=0)
        self.assertEqual(back.socket.sent[0]["team_size"], 2)
        replayed = [m for m in back.socket.sent if m.get("type") == "start"]
        self.assertEqual(replayed[0]["heroes"]["left"], ["skeleton", "wizard"])


if __name__ == "__main__":
    unittest.main()
