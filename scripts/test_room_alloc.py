#!/usr/bin/env python3
"""ROOM-FLOW R1: seat allocation. A seat may never hold more units than its team has free, and a team with no free unit refuses more seats.
Real relay on a free port, real sockets (listed with the socket tests in run_full_suite.sh)."""
import asyncio
import json
import sys
import unittest
from pathlib import Path

import websockets

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pk_relay import MAX_MESSAGE_BYTES, RelayServer  # noqa: E402


class RoomAllocTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.relay = RelayServer("127.0.0.1", 0, max_per_addr=100, max_connects_per_min=100000)   # one test opens many sockets from 127.0.0.1
        await self.relay.start()
        self.url = f"ws://127.0.0.1:{self.relay.bound_port}/ws"
        self.sockets = []

    async def asyncTearDown(self):
        for s in self.sockets:
            await s.close()
        await self.relay.close()

    async def open(self):
        s = await websockets.connect(self.url, max_size=MAX_MESSAGE_BYTES)
        self.sockets.append(s)
        return s

    async def first(self, s, types=("room_state", "error")):
        for _ in range(10):
            m = json.loads(await asyncio.wait_for(s.recv(), 2))
            if m.get("type") in types:
                return m
        raise AssertionError("no %s message" % (types,))

    async def host(self, team_size, units=None, seat="red"):
        s = await self.open()
        msg = {"type": "create_room", "seat": seat, "team_size": team_size, "client_version": "test"}
        if units is not None:
            msg["units"] = units
        await s.send(json.dumps(msg))
        return s, await self.first(s)

    async def join(self, code, seat, units=None):
        s = await self.open()
        msg = {"type": "join", "code": code, "seat": seat, "client_version": "test"}
        if units is not None:
            msg["units"] = units
        await s.send(json.dumps(msg))
        return s, await self.first(s)

    @staticmethod
    def units_of(state, team):
        return [seat["units"] for seat in state["seats"] if seat["team"] == team]

    async def test_second_seat_units_are_trimmed_to_the_free_space(self):
        _, st = await self.host(2, ["skeleton"])
        _, joined = await self.join(st["code"], "red", ["wizard", "bat"])
        self.assertEqual(joined["type"], "room_state", joined)
        self.assertEqual(self.units_of(joined, "red"), [["skeleton"], ["wizard"]])

    async def test_a_full_team_refuses_more_seats(self):
        _, st = await self.host(2, ["skeleton", "wizard"])
        _, joined = await self.join(st["code"], "red", [])
        self.assertEqual((joined["type"], joined.get("code")), ("error", "team_full"), joined)

    async def test_the_other_team_is_not_affected(self):
        _, st = await self.host(2, ["skeleton", "wizard"])
        _, joined = await self.join(st["code"], "white", ["bat"])
        self.assertEqual(joined["type"], "room_state", joined)
        self.assertEqual(self.units_of(joined, "white"), [["bat"]])

    async def test_one_seat_over_the_team_size_is_still_invalid_units(self):
        s = await self.open()
        await s.send(json.dumps({"type": "create_room", "seat": "red", "team_size": 2, "units": ["a", "b", "c"], "client_version": "test"}))
        m = await self.first(s)
        self.assertEqual((m["type"], m.get("code")), ("error", "invalid_units"), m)

    async def test_an_invalid_seat_string_is_still_invalid_seat(self):
        _, st = await self.host(2, ["skeleton"])
        _, joined = await self.join(st["code"], "blue", [])
        self.assertEqual((joined["type"], joined.get("code")), ("error", "invalid_seat"), joined)

    async def test_a_plain_one_versus_one_room_is_unchanged(self):
        _, st = await self.host(1)
        _, joined = await self.join(st["code"], "red", [])
        self.assertEqual(joined["type"], "room_state", joined)


    # ---- R2: `seat` missing or "auto" on a join = the relay picks the team that still has room
    async def join_auto(self, code, units=None, seat="__omit__"):
        s = await self.open()
        msg = {"type": "join", "code": code, "client_version": "test"}
        if seat != "__omit__":
            msg["seat"] = seat
        if units is not None:
            msg["units"] = units
        await s.send(json.dumps(msg))
        return s, await self.first(s)

    @staticmethod
    def teams_of(state):
        return sorted(seat["team"] for seat in state["seats"])

    async def test_auto_seat_goes_to_the_team_with_free_units(self):
        _, st = await self.host(2, ["skeleton", "wizard"])
        _, joined = await self.join_auto(st["code"], ["bat"])
        self.assertEqual(joined["type"], "room_state", joined)
        self.assertEqual(self.teams_of(joined), ["red", "white"])

    async def test_auto_keyword_works_like_a_missing_seat(self):
        _, st = await self.host(2, ["skeleton"])
        _, joined = await self.join_auto(st["code"], ["wizard"], seat="auto")
        self.assertEqual(joined["type"], "room_state", joined)
        self.assertEqual(self.teams_of(joined), ["red", "white"])   # the emptier team gets the new seat

    async def test_auto_seat_with_no_room_anywhere_is_team_full(self):
        _, st = await self.host(1)
        await self.join(st["code"], "white", [])
        _, joined = await self.join_auto(st["code"])
        self.assertEqual((joined["type"], joined.get("code")), ("error", "team_full"), joined)

    async def test_auto_seat_in_a_one_versus_one_room_takes_the_empty_side(self):
        _, st = await self.host(1)
        _, joined = await self.join_auto(st["code"])
        self.assertEqual(joined["type"], "room_state", joined)
        self.assertEqual(self.teams_of(joined), ["red", "white"])

    async def test_any_other_seat_string_is_still_invalid_seat(self):
        _, st = await self.host(2, ["skeleton"])
        for bad in ("blue", "", "RED", 7, None):
            _, joined = await self.join_auto(st["code"], seat=bad)
            self.assertEqual((joined["type"], joined.get("code")), ("error", "invalid_seat"), (bad, joined))


    # ---- 2v2 AND 3v3 (owner 2026-11-25: both sizes must be checked)
    HEROES = ["skeleton", "wizard", "bat"]

    async def test_trim_full_and_auto_for_both_team_sizes(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                _, st = await self.host(n, self.HEROES[:1])
                # R1: the second red seat asks for the whole team and gets what is left (n - 1)
                _, joined = await self.join(st["code"], "red", self.HEROES[:n])
                self.assertEqual(self.units_of(joined, "red"), [self.HEROES[:1], self.HEROES[:n - 1]])
                # the team has nothing left now: another red seat is refused
                _, refused = await self.join(st["code"], "red", [])
                self.assertEqual((refused["type"], refused.get("code")), ("error", "team_full"), refused)
                # R2: an auto seat goes to the empty team and is trimmed to the team size; then nothing is left anywhere
                _, auto = await self.join_auto(st["code"], self.HEROES[:n])
                self.assertEqual(self.units_of(auto, "white"), [self.HEROES[:n]])
                _, none_left = await self.join_auto(st["code"])
                self.assertEqual((none_left["type"], none_left.get("code")), ("error", "team_full"), none_left)

    async def test_three_versus_three_splits_the_team_over_three_seats(self):
        _, st = await self.host(3, ["skeleton"])
        _, second = await self.join(st["code"], "red", ["wizard"])
        _, third = await self.join(st["code"], "red", ["bat", "hag"])
        self.assertEqual(self.units_of(third, "red"), [["skeleton"], ["wizard"], ["bat"]])
        _, fourth = await self.join(st["code"], "red", ["x"])
        self.assertEqual((fourth["type"], fourth.get("code")), ("error", "team_full"), fourth)

    # ---- R3: `unready`
    async def drain_until(self, s, predicate, tries=12):
        for _ in range(tries):
            m = json.loads(await asyncio.wait_for(s.recv(), 2))
            if predicate(m):
                return m
        raise AssertionError("expected message never came")

    async def test_unready_clears_the_ready_flag_for_both_team_sizes(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                host, st = await self.host(n, self.HEROES[:n])
                await self.join(st["code"], "white", self.HEROES[:n])
                await host.send(json.dumps({"type": "ready"}))
                await self.drain_until(host, lambda m: m.get("type") == "room_state" and any(x["seat_id"] == "red-1" and x["ready"] for x in m["seats"]))
                await host.send(json.dumps({"type": "unready"}))
                state = await self.drain_until(host, lambda m: m.get("type") == "room_state" and any(x["seat_id"] == "red-1" and not x["ready"] for x in m["seats"]))
                self.assertFalse(state["started"])

    async def test_unready_after_the_start_is_refused(self):
        host, st = await self.host(2, self.HEROES[:2])
        white, _ = await self.join(st["code"], "white", self.HEROES[:2])
        await host.send(json.dumps({"type": "ready"}))
        await white.send(json.dumps({"type": "ready"}))
        await self.drain_until(host, lambda m: m.get("type") == "start")
        await host.send(json.dumps({"type": "unready"}))
        err = await self.drain_until(host, lambda m: m.get("type") == "error")
        self.assertEqual(err.get("code"), "room_started", err)


    # ---- R1b: a seat reserves `claim` places (default 1) at join time, even before it has picked heroes
    async def join_claim(self, code, seat, claim=None, units=None):
        s = await self.open()
        msg = {"type": "join", "code": code, "seat": seat, "client_version": "test"}
        if claim is not None:
            msg["claim"] = claim
        if units is not None:
            msg["units"] = units
        await s.send(json.dumps(msg))
        return s, await self.first(s)

    async def test_empty_seats_with_an_explicit_claim_reserve_that_place_for_both_sizes(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                s = await self.open()
                await s.send(json.dumps({"type": "create_room", "seat": "red", "team_size": n, "claim": 1, "client_version": "test"}))
                st = await self.first(s)
                for _ in range(n - 1):
                    _, ok = await self.join_claim(st["code"], "red", claim=1)
                    self.assertEqual(ok["type"], "room_state", ok)
                _, refused = await self.join_claim(st["code"], "red", claim=1)
                self.assertEqual((refused["type"], refused.get("code")), ("error", "team_full"), refused)

    async def test_a_join_without_claim_reserves_nothing_so_the_old_placeholder_flow_still_works(self):
        # scripts/fill_room.py puts placeholder seats into a room; real players list their units only when they press ready
        for n in (2, 3):
            with self.subTest(team_size=n):
                _, st = await self.host(n)
                for _ in range(n):      # the host plus n placeholders: more than the team has places, still under the 4-seat cap
                    _, ok = await self.join_claim(st["code"], "red")
                    self.assertEqual(ok["type"], "room_state", ok)
                    self.assertTrue(all(seat["claim"] == 0 for seat in ok["seats"] if seat["team"] == "red"), ok["seats"])

    async def test_a_big_claim_leaves_less_for_the_others(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                s = await self.open()
                await s.send(json.dumps({"type": "create_room", "seat": "red", "team_size": n, "claim": n - 1, "client_version": "test"}))
                st = await self.first(s)
                _, ok = await self.join_claim(st["code"], "red", claim=3)      # asks for 3, only 1 is left
                self.assertEqual(ok["type"], "room_state", ok)
                self.assertEqual(sorted(seat["claim"] for seat in ok["seats"] if seat["team"] == "red"), [1, n - 1])
                _, refused = await self.join_claim(st["code"], "red")
                self.assertEqual((refused["type"], refused.get("code")), ("error", "team_full"), refused)

    async def test_a_bad_claim_is_invalid_units(self):
        _, st = await self.host(2)
        for bad in (0, -1, "2", 2.5, True, 99):
            _, m = await self.join_claim(st["code"], "red", claim=bad)
            self.assertEqual((m["type"], m.get("code")), ("error", "invalid_units"), (bad, m))


    # ---- R4: host-only commands and host hand-over (2v2 and 3v3)
    async def test_only_the_host_can_set_room_options_for_both_sizes(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                host, st = await self.host(n)
                guest, _ = await self.join(st["code"], "white")
                await guest.send(json.dumps({"type": "room_options", "allow_ai": True, "allow_mcp": False}))
                err = await self.drain_until(guest, lambda m: m.get("type") == "error")
                self.assertEqual(err.get("code"), "host_only", err)
                await host.send(json.dumps({"type": "room_options", "allow_ai": True, "allow_mcp": False}))
                state = await self.drain_until(host, lambda m: m.get("type") == "room_state" and m.get("allow_mcp") is False)
                self.assertTrue(state["allow_ai"])
                self.assertEqual(state["host_seat_id"], "red-1")

    async def test_bad_room_options_are_refused(self):
        host, _ = await self.host(2)
        for bad in ({"allow_ai": "yes"}, {"allow_mcp": 1}, {}):
            await host.send(json.dumps(dict(type="room_options", **bad)))
            err = await self.drain_until(host, lambda m: m.get("type") == "error")
            self.assertEqual(err.get("code"), "invalid_options", (bad, err))

    async def test_only_the_host_can_kick_and_never_itself(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                host, st = await self.host(n)
                guest, _ = await self.join(st["code"], "red")
                await guest.send(json.dumps({"type": "kick", "seat_id": "red-1"}))
                err = await self.drain_until(guest, lambda m: m.get("type") == "error")
                self.assertEqual(err.get("code"), "host_only", err)
                await host.send(json.dumps({"type": "kick", "seat_id": "red-1"}))
                err = await self.drain_until(host, lambda m: m.get("type") == "error")
                self.assertEqual(err.get("code"), "invalid_target", err)
                await host.send(json.dumps({"type": "kick", "seat_id": "red-2"}))
                gone = await self.drain_until(guest, lambda m: m.get("type") == "kicked")
                self.assertEqual(gone["type"], "kicked")
                state = await self.drain_until(host, lambda m: m.get("type") == "room_state" and all(x["seat_id"] != "red-2" for x in m["seats"]))
                self.assertEqual([x["seat_id"] for x in state["seats"]], ["red-1"])

    async def test_host_leaving_before_the_start_hands_over_to_the_earliest_seat(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                host, st = await self.host(n)
                _, _ = await self.join(st["code"], "white")
                third, _ = await self.join(st["code"], "red")
                await host.send(json.dumps({"type": "leave"}))
                state = await self.drain_until(third, lambda m: m.get("type") == "room_state" and m.get("host_seat_id") not in (None, "red-1") and all(x["seat_id"] != "red-1" for x in m["seats"]))
                self.assertEqual(state["host_seat_id"], "white-1")      # the seat that joined right after the host

    async def test_after_the_start_nobody_takes_over_and_options_are_refused(self):
        host, st = await self.host(2, self.HEROES[:2])
        white, _ = await self.join(st["code"], "white", self.HEROES[:2])
        await host.send(json.dumps({"type": "ready"}))
        await white.send(json.dumps({"type": "ready"}))
        await self.drain_until(host, lambda m: m.get("type") == "start")
        await host.send(json.dumps({"type": "room_options", "allow_ai": False, "allow_mcp": False}))
        err = await self.drain_until(host, lambda m: m.get("type") == "error")
        self.assertEqual(err.get("code"), "room_started", err)


    # ---- R5: allow_mcp gate (agents declare client_kind "mcp"; the hosted gateway proves itself with its token)
    async def join_kind(self, code, seat, kind=None, headers=None, relay_url=None):
        s = await websockets.connect(relay_url or self.url, max_size=MAX_MESSAGE_BYTES, additional_headers=headers)
        self.sockets.append(s)
        msg = {"type": "join", "code": code, "seat": seat, "client_version": "test"}
        if kind is not None:
            msg["client_kind"] = kind
        await s.send(json.dumps(msg))
        return s, await self.first(s)

    async def test_allow_mcp_false_blocks_declared_mcp_clients_for_both_sizes(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                host, st = await self.host(n)
                await host.send(json.dumps({"type": "room_options", "allow_mcp": False}))
                await self.drain_until(host, lambda m: m.get("type") == "room_state" and m.get("allow_mcp") is False)
                _, blocked = await self.join_kind(st["code"], "white", "mcp")
                self.assertEqual((blocked["type"], blocked.get("code")), ("error", "mcp_disabled"), blocked)
                _, plain = await self.join_kind(st["code"], "white")                 # a browser (or a browser-driven agent) is not an MCP client
                self.assertEqual(plain["type"], "room_state", plain)
                _, watcher = await self.join_kind(st["code"], "spectator", "mcp")    # spectators are never blocked
                self.assertEqual(watcher["type"], "room_state", watcher)

    async def test_allow_mcp_true_and_the_default_let_mcp_in(self):
        _, st = await self.host(2)
        _, first = await self.join_kind(st["code"], "white", "mcp")
        self.assertEqual(first["type"], "room_state", first)

    async def test_allow_mcp_false_blocks_the_gateway_connection_too(self):
        relay = RelayServer("127.0.0.1", 0, gateway_token="secret-token", max_per_addr=100, max_connects_per_min=100000)
        await relay.start()
        try:
            url = f"ws://127.0.0.1:{relay.bound_port}/ws"
            host = await websockets.connect(url, max_size=MAX_MESSAGE_BYTES)
            self.sockets.append(host)
            await host.send(json.dumps({"type": "create_room", "seat": "red", "team_size": 2, "client_version": "test"}))
            st = await self.first(host)
            await host.send(json.dumps({"type": "room_options", "allow_mcp": False}))
            await self.drain_until(host, lambda m: m.get("type") == "room_state" and m.get("allow_mcp") is False)
            gw = {"X-PK-Gateway-Token": "secret-token", "X-PK-Client-Addr": "203.0.113.9"}
            _, blocked = await self.join_kind(st["code"], "white", headers=gw, relay_url=url)
            self.assertEqual((blocked["type"], blocked.get("code")), ("error", "mcp_disabled"), blocked)
            wrong = {"X-PK-Gateway-Token": "wrong", "X-PK-Client-Addr": "203.0.113.9"}
            _, ok = await self.join_kind(st["code"], "white", headers=wrong, relay_url=url)   # a wrong token is just a normal client
            self.assertEqual(ok["type"], "room_state", ok)
        finally:
            await relay.close()


    # ---- R6: reset_lobby (host only, after a match started): back to the lobby with the same seats
    async def start_match(self, n):
        host, st = await self.host(n, self.HEROES[:n])
        white, _ = await self.join(st["code"], "white", self.HEROES[:n])
        await host.send(json.dumps({"type": "ready"}))
        await white.send(json.dumps({"type": "ready"}))
        await self.drain_until(host, lambda m: m.get("type") == "start")
        await self.drain_until(white, lambda m: m.get("type") == "start")
        return host, white, st

    async def test_reset_lobby_returns_everyone_to_an_unstarted_room_for_both_sizes(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                host, white, st = await self.start_match(n)
                await host.send(json.dumps({"type": "reset_lobby"}))
                for sock in (host, white):
                    await self.drain_until(sock, lambda m: m.get("type") == "lobby_reset")
                state = await self.drain_until(host, lambda m: m.get("type") == "room_state" and m.get("started") is False)
                self.assertEqual([x["seat_id"] for x in state["seats"]], ["red-1", "white-1"])
                self.assertTrue(all(x["ready"] is False and x["units"] == [] and x["claim"] >= 1 for x in state["seats"]), state["seats"])
                self.assertEqual(state["host_seat_id"], "red-1")
                # the same room can start a second match
                await host.send(json.dumps({"type": "ready", "units": self.HEROES[:n]}))
                await white.send(json.dumps({"type": "ready", "units": self.HEROES[:n]}))
                again = await self.drain_until(host, lambda m: m.get("type") == "start")
                self.assertEqual(again["team_size"], n) if n > 1 else None

    async def test_only_the_host_resets_and_only_after_a_start(self):
        host, white, _ = await self.start_match(2)
        await white.send(json.dumps({"type": "reset_lobby"}))
        err = await self.drain_until(white, lambda m: m.get("type") == "error")
        self.assertEqual(err.get("code"), "host_only", err)
        h2, st2 = await self.host(2)
        await h2.send(json.dumps({"type": "reset_lobby"}))
        err2 = await self.drain_until(h2, lambda m: m.get("type") == "error")
        self.assertEqual(err2.get("code"), "invalid_state", err2)


    async def test_a_player_joining_a_room_without_a_host_becomes_the_host(self):
        # found by stress_room_alloc.py seed 4: the host left, only a spectator stayed, the room lived on with no host at all
        for n in (2, 3):
            with self.subTest(team_size=n):
                host, st = await self.host(n)
                _, _ = await self.join(st["code"], "spectator")
                await host.send(json.dumps({"type": "leave"}))
                await asyncio.sleep(0.1)
                _, joined = await self.join(st["code"], "white")
                self.assertEqual(joined["type"], "room_state", joined)
                self.assertEqual(joined["host_seat_id"], "white-1", joined)


    # ---- R9: the host's AI filler seats are marked and never fall under the "a seat that leaves forfeits" rule
    async def join_ai(self, code, seat, token, units=None):
        s = await self.open()
        msg = {"type": "join", "code": code, "seat": seat, "client_version": "test", "ai_host_token": token}
        if units is not None:
            msg["units"] = units
        await s.send(json.dumps(msg))
        return s, await self.first(s)

    async def test_the_host_token_marks_a_filler_seat_as_ai_for_both_sizes(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                _, st = await self.host(n, self.HEROES[:1])
                _, ai = await self.join_ai(st["code"], "white", st["seat_token"], self.HEROES[:n])
                self.assertEqual(ai["type"], "room_state", ai)
                self.assertEqual({x["seat_id"]: x["ai"] for x in ai["seats"]}, {"red-1": False, "white-1": True})

    async def test_only_the_host_can_add_an_ai_seat_and_only_when_allowed(self):
        host, st = await self.host(3, self.HEROES[:1])
        _, guest = await self.join(st["code"], "white", self.HEROES[:1])
        for token in (guest["seat_token"], "wrong", 7, ""):
            with self.subTest(token=token):
                _, answer = await self.join_ai(st["code"], "white", token)
                self.assertEqual(answer.get("code"), "host_only", answer)
        _, watcher = await self.join_ai(st["code"], "spectator", st["seat_token"])
        self.assertEqual(watcher.get("code"), "host_only", watcher)
        await host.send(json.dumps({"type": "room_options", "allow_ai": False}))
        await self.drain_until(host, lambda m: m.get("type") == "room_state" and m.get("allow_ai") is False)
        _, off = await self.join_ai(st["code"], "red", st["seat_token"])
        self.assertEqual(off.get("code"), "ai_disabled", off)

    async def test_the_host_leaving_before_the_start_takes_the_ai_seats_along_for_both_sizes(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                host, st = await self.host(n, self.HEROES[:1])
                ai, _ = await self.join_ai(st["code"], "white", st["seat_token"], self.HEROES[:n])
                await ai.send(json.dumps({"type": "ready"}))
                guest, _ = await self.join(st["code"], "red", self.HEROES[:1])
                await host.send(json.dumps({"type": "leave"}))
                state = await self.drain_until(guest, lambda m: m.get("type") == "room_state" and [x["seat_id"] for x in m["seats"]] == ["red-2"])
                self.assertEqual(state["host_seat_id"], "red-2", state)
                self.assertFalse(state.get("started"))
                self.assertEqual((await self.drain_until(ai, lambda m: m.get("type") == "kicked"))["reason"], "host_left")

    async def test_an_ai_seat_never_becomes_the_host(self):
        host, st = await self.host(2, self.HEROES[:1])
        _, _ = await self.join(st["code"], "spectator")
        _, _ = await self.join_ai(st["code"], "white", st["seat_token"], self.HEROES[:2])
        await host.send(json.dumps({"type": "leave"}))
        await asyncio.sleep(0.1)
        _, joined = await self.join(st["code"], "red")
        self.assertEqual(joined["host_seat_id"], joined["seat_id"], joined)
        self.assertNotIn(True, [x["ai"] for x in joined["seats"]])

    async def start_with_ai(self, n, human_mate):
        """red = the host (plus, when human_mate is False, an AI teammate filling the rest), white = one AI filler for the whole team.
        When human_mate is True the AI sits on white next to a human white seat holding one unit."""
        host, st = await self.host(n, self.HEROES[:n] if human_mate else self.HEROES[:1])
        if human_mate:
            mate, _ = await self.join(st["code"], "white", self.HEROES[:1])
            ai, _ = await self.join_ai(st["code"], "white", st["seat_token"], self.HEROES[1:n])
            players = [host, mate, ai]
        else:
            mate, _ = await self.join_ai(st["code"], "red", st["seat_token"], self.HEROES[1:n])
            ai, _ = await self.join_ai(st["code"], "white", st["seat_token"], self.HEROES[:n])
            players = [host, mate, ai]
        for sock in players:
            await sock.send(json.dumps({"type": "ready"}))
        start = await self.drain_until(host, lambda m: m.get("type") == "start")
        return host, mate, ai, st, start

    async def lose(self, code, seat_id):
        """Expire one seat as the grace sweep does: drop it, then let its time run out."""
        room = self.relay.rooms[code]
        token, entry = next((t, e) for t, e in room.sessions.items() if e["seat_id"] == seat_id)
        sock = next(k for k, e in room.clients.items() if e is entry)
        await self.relay._remove_client(room, sock)
        await self.relay._expire_seat(room, token)

    async def test_a_lost_ai_seat_hands_its_units_to_the_human_teammate_for_both_sizes(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                host, mate, _, st, start = await self.start_with_ai(n, True)
                ai_units = [u for u, s in start["owners"].items() if s == "white-2"]
                self.assertTrue(ai_units, start["owners"])
                await self.lose(st["code"], "white-2")
                left = await self.drain_until(host, lambda m: m.get("type") == "seat_left")
                self.assertEqual((left["ai"], left["team_empty"]), (True, False), left)
                self.assertEqual({left["owners"][u] for u in ai_units}, {"white-1"}, left)
                await host.send(json.dumps({"type": "end_turn", "round": 1, "phase": "red"}))
                await self.drain_until(mate, lambda m: m.get("type") == "end_turn")
                await mate.send(json.dumps({"type": "action", "round": 1, "phase": "white", "unit": ai_units[0], "kind": "defend"}))
                answer = await self.drain_until(mate, lambda m: m.get("type") in ("action", "error"))
                self.assertEqual(answer["type"], "action", answer)

    async def test_an_ai_seat_that_was_the_whole_team_is_reported_as_team_empty_for_both_sizes(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                host, _, _, st, _ = await self.start_with_ai(n, False)
                await self.lose(st["code"], "white-1")
                left = await self.drain_until(host, lambda m: m.get("type") == "seat_left")
                self.assertEqual((left["ai"], left["team_empty"], left["team"]), (True, True, "white"), left)

    async def test_an_ai_seat_that_sends_leave_after_the_start_is_handed_over_too(self):
        host, mate, ai, _, _ = await self.start_with_ai(2, True)
        await ai.send(json.dumps({"type": "leave"}))
        left = await self.drain_until(host, lambda m: m.get("type") == "seat_left")
        self.assertEqual((left["ai"], left["seat_id"]), (True, "white-2"), left)

    async def test_a_lost_human_seat_is_reported_as_before(self):
        host, _, _, st, _ = await self.start_with_ai(2, True)
        await self.lose(st["code"], "white-1")
        left = await self.drain_until(host, lambda m: m.get("type") == "seat_left")
        self.assertNotIn("ai", left)
        self.assertNotIn("owners", left)
    # ---- R9b: a person who leaves a started match is announced, so the other devices can apply the leave rule
    async def test_a_person_who_leaves_a_started_match_is_announced_after_their_last_turn_for_both_sizes(self):
        for n in (2, 3):
            for kind in ("leave", "timeout"):
                with self.subTest(team_size=n, kind=kind):
                    host, white, _ = await self.start_match(n)
                    await host.send(json.dumps({"type": "end_turn", "round": 1, "phase": "red"}))
                    await host.send(json.dumps({"type": kind}))
                    turn = await self.drain_until(white, lambda m: m.get("type") in ("end_turn", "seat_left"))
                    left = await self.drain_until(white, lambda m: m.get("type") in ("end_turn", "seat_left"))
                    self.assertEqual((turn["type"], left["type"]), ("end_turn", "seat_left"), (turn, left))
                    self.assertEqual((left["seat_id"], left["team"], left["reason"]), ("red-1", "red", "left"), left)
                    self.assertLess(turn["seq"], left["seq"])
                    self.assertNotIn("ai", left)

    async def test_nobody_is_announced_for_a_spectator_or_before_the_start(self):
        host, st = await self.host(2, self.HEROES[:2])
        white, _ = await self.join(st["code"], "white", self.HEROES[:2])
        early, _ = await self.join(st["code"], "red")
        await early.send(json.dumps({"type": "leave"}))
        watcher, _ = await self.join(st["code"], "spectator")
        await host.send(json.dumps({"type": "ready"}))
        await white.send(json.dumps({"type": "ready"}))
        await self.drain_until(white, lambda m: m.get("type") == "start")
        await watcher.send(json.dumps({"type": "leave"}))
        await host.send(json.dumps({"type": "end_turn", "round": 1, "phase": "red"}))
        seen = []
        while not seen or seen[-1]["type"] != "end_turn":
            seen.append(await self.drain_until(white, lambda m: m.get("type") in ("end_turn", "seat_left")))
        self.assertEqual([m["type"] for m in seen], ["end_turn"], seen)


    # ---- R7/R8: a seat may carry a name; the relay cleans it and every room_state shows it
    @staticmethod
    def names_of(state):
        return {seat["seat_id"]: seat["name"] for seat in state["seats"]}

    async def test_names_are_cleaned_and_listed_for_both_sizes(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                host = await self.open()
                await host.send(json.dumps({"type": "create_room", "seat": "red", "team_size": n, "name": " 南瓜殺手王五六 "}))
                st = await self.first(host)
                self.assertEqual(self.names_of(st), {"red-1": "南瓜殺手王"}, st)
                guest = await self.open()
                await guest.send(json.dumps({"type": "join", "code": st["code"], "name": "a\u202eb\U0001f600"}))
                joined = await self.first(guest)
                self.assertEqual(self.names_of(joined)[joined["seat_id"]], "ab\U0001f600", joined)
                _, plain = await self.join(st["code"], "auto")
                self.assertEqual(self.names_of(plain)[plain["seat_id"]], "", plain)

    async def test_set_name_before_the_start_only_and_names_survive_a_lobby_reset(self):
        host, st = await self.host(2, self.HEROES[:2])
        white, _ = await self.join(st["code"], "white", self.HEROES[:2])
        await white.send(json.dumps({"type": "set_name", "name": "小白"}))
        state = await self.drain_until(host, lambda m: m.get("type") == "room_state" and self.names_of(m).get("white-1") == "小白")
        self.assertEqual(self.names_of(state)["red-1"], "")
        await host.send(json.dumps({"type": "ready", "name": "房主"}))
        await white.send(json.dumps({"type": "ready"}))
        await self.drain_until(white, lambda m: m.get("type") == "start")
        await white.send(json.dumps({"type": "set_name", "name": "改"}))
        err = await self.drain_until(white, lambda m: m.get("type") == "error")
        self.assertEqual(err.get("code"), "room_started", err)
        await host.send(json.dumps({"type": "reset_lobby"}))
        back = await self.drain_until(host, lambda m: m.get("type") == "room_state" and m.get("started") is False)
        self.assertEqual(self.names_of(back), {"red-1": "房主", "white-1": "小白"})

    async def test_a_name_that_is_not_text_is_refused(self):
        host, st = await self.host(2)
        bad = await self.open()
        await bad.send(json.dumps({"type": "join", "code": st["code"], "name": 7}))
        answer = await self.first(bad)
        self.assertEqual(answer.get("code"), "invalid_name", answer)
        await host.send(json.dumps({"type": "set_name", "name": ["x"]}))
        err = await self.drain_until(host, lambda m: m.get("type") == "error")
        self.assertEqual(err.get("code"), "invalid_name", err)
        make = await self.open()
        await make.send(json.dumps({"type": "create_room", "seat": "red", "name": {}}))
        self.assertEqual((await self.first(make)).get("code"), "invalid_name")

if __name__ == "__main__":
    unittest.main()
