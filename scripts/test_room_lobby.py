#!/usr/bin/env python3
"""ROOM-FLOW R12/R13: a lobby room starts only when the host asks and every place has a locked hero, after a countdown; a player moves between places.
Real relay on a free port, real sockets (listed with the socket tests in run_full_suite.sh). Both team sizes and one versus one."""
import asyncio
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_room_invite import Base, HEROES  # noqa: E402


def is_type(*kinds):
    return lambda m: m.get("type") in kinds


class LobbyTests(Base):
    limits = {"countdown_seconds": 0.3, "invite_seconds": 600}

    async def room(self, n, **extra):
        return await self.host(n, lobby=True, **extra)

    async def full_room(self, n):
        host, st = await self.room(n, claim=n)
        guest, _ = await self.join(st["code"], seat="white", claim=n)
        return host, guest, st

    async def nothing_starts(self, s, seconds=0.7):
        seen = []
        try:
            while True:
                seen.append(json.loads(await asyncio.wait_for(s.recv(), seconds)))
        except asyncio.TimeoutError:
            pass
        self.assertNotIn("start", [m["type"] for m in seen], seen)
        return seen

    async def test_everyone_ready_does_not_start_a_lobby_room_by_itself(self):
        for n in (1, 2, 3):
            with self.subTest(team_size=n):
                host, guest, st = await self.full_room(n)
                await self.send(host, type="ready", units=HEROES[:n])
                await self.send(guest, type="ready", units=HEROES[:n])
                await self.nothing_starts(host)

    async def test_the_hosts_begin_counts_down_and_starts_a_full_locked_room(self):
        for n in (1, 2, 3):
            with self.subTest(team_size=n):
                host, guest, st = await self.full_room(n)
                self.assertEqual((st["lobby"], st["begin"]), (True, False))
                await self.send(guest, type="ready", units=HEROES[:n])
                await self.send(host, type="ready", units=HEROES[:n])
                loop = asyncio.get_running_loop()
                await self.send(host, type="begin")
                count = await self.until(guest, is_type("countdown", "start"))
                self.assertEqual((count["type"], count["seconds"]), ("countdown", 0.3), count)
                began = loop.time()
                start = await self.until(guest, is_type("start"))
                self.assertGreaterEqual(loop.time() - began, 0.2)
                self.assertEqual(start["phase"], "red")

    async def test_begin_waits_for_the_last_lock_and_unlocking_stops_the_countdown(self):
        host, guest, _ = await self.full_room(2)
        await self.send(host, type="ready", units=HEROES[:2])
        await self.send(host, type="begin")
        state = await self.state_where(guest, lambda m: m.get("begin"))
        self.assertFalse(state["started"])
        await self.nothing_starts(guest, 0.5)
        await self.send(guest, type="ready", units=HEROES[:2])
        await self.until(guest, is_type("countdown"))
        await self.send(guest, type="unready")
        stop = await self.until(guest, is_type("countdown", "start"))
        self.assertEqual((stop["type"], stop["seconds"]), ("countdown", None), stop)
        await self.nothing_starts(guest)
        await self.send(guest, type="ready", units=HEROES[:2])   # an unlock released the heroes (red team polish P7): the lock names them again, as the page does
        await self.until(guest, is_type("start"))

    async def test_begin_needs_a_full_room_unless_ai_may_fill_it(self):
        host, st = await self.room(2)
        await self.send(host, type="room_options", allow_ai=False)
        await self.send(host, type="begin")
        self.assertEqual(await self.error_of(host), "not_full")
        await self.send(host, type="room_options", allow_ai=True)
        await self.send(host, type="ready", units=HEROES[:1])
        await self.send(host, type="begin")
        await self.state_where(host, lambda m: m.get("begin"))
        await self.nothing_starts(host, 0.5)
        ai_red, _ = await self.join(st["code"], seat="red", claim=1, units=HEROES[1:2], ai_host_token=st["seat_token"])
        ai_white, _ = await self.join(st["code"], seat="white", claim=2, units=HEROES[:2], ai_host_token=st["seat_token"])
        await self.send(ai_red, type="ready")
        await self.send(ai_white, type="ready")
        start = await self.until(host, is_type("start"))
        self.assertNotIn(None, start["heroes"]["left"] + start["heroes"]["right"])

    async def test_a_place_without_a_hero_holds_the_start(self):
        host, guest, _ = await self.full_room(2)
        await self.send(host, type="ready", units=HEROES[:2])
        await self.send(guest, type="ready", units=HEROES[:1])
        await self.send(host, type="begin")
        await self.nothing_starts(host)
        await self.send(guest, type="ready", units=HEROES[:2])
        await self.until(host, is_type("start"))

    async def test_only_the_host_begins_and_only_in_a_lobby_room(self):
        host, guest, _ = await self.full_room(2)
        await self.send(guest, type="begin")
        self.assertEqual(await self.error_of(guest), "host_only")
        old, _ = await self.host(2)
        await self.send(old, type="begin")
        self.assertEqual(await self.error_of(old), "invalid_state")
        await self.send(host, type="begin", on="yes")
        self.assertEqual(await self.error_of(host), "invalid_options")
        await self.send(host, type="begin")
        await self.state_where(host, lambda m: m.get("begin"))
        await self.send(host, type="begin", on=False)
        await self.state_where(host, lambda m: m.get("begin") is False)

    async def test_a_new_host_and_a_lobby_reset_start_with_begin_off(self):
        host, guest, _ = await self.full_room(2)
        await self.send(host, type="begin")
        await self.state_where(guest, lambda m: m.get("begin"))
        await self.send(host, type="leave")
        await self.state_where(guest, lambda m: m.get("host_seat_id") == "white-1" and m.get("begin") is False)
        host, guest, _ = await self.full_room(2)
        await self.send(host, type="ready", units=HEROES[:2])
        await self.send(guest, type="ready", units=HEROES[:2])
        await self.send(host, type="begin")
        await self.until(host, is_type("start"))
        await self.send(host, type="reset_lobby")
        back = await self.state_where(host, lambda m: m.get("started") is False)
        self.assertEqual((back["begin"], back["lobby"]), (False, True))

    async def test_a_lobby_room_starts_with_agents_off_until_the_host_ticks_it(self):
        host, st = await self.room(2)
        self.assertEqual((st["allow_mcp"], st["allow_ai"]), (False, True), st)
        self.assertEqual((await self.invite(host))["code"], "mcp_disabled")
        _, old = await self.host(2)
        self.assertTrue(old["allow_mcp"], "a room without lobby keeps agents on (MCP join_room of old rooms)")
        await self.send(host, type="room_options", allow_mcp=True)
        await self.state_where(host, lambda m: m.get("allow_mcp") is True)
        self.assertEqual((await self.invite(host))["type"], "invite_created")

    async def test_when_the_host_left_during_the_match_any_player_reopens_the_lobby_and_becomes_host(self):
        host, guest, _ = await self.full_room(2)
        await self.send(host, type="ready", units=HEROES[:2])
        await self.send(guest, type="ready", units=HEROES[:2])
        await self.send(host, type="begin")
        await self.until(guest, is_type("start"))
        await self.send(guest, type="reset_lobby")
        self.assertEqual(await self.error_of(guest), "host_only", "while the host is still here only the host reopens")
        await self.send(host, type="leave")
        await self.until(guest, is_type("seat_left"))
        await self.send(guest, type="reset_lobby")
        back = await self.state_where(guest, lambda m: m.get("started") is False)
        self.assertEqual(back["host_seat_id"], "white-1", back)

    async def test_a_one_versus_one_lobby_has_one_seat_per_side(self):   # red team A3 (old rooms keep several devices per side)
        host, st = await self.room(1)
        _, white = await self.join(st["code"], seat="white")
        _, extra = await self.join(st["code"], seat="red")
        self.assertEqual((white["type"], extra.get("code")), ("room_state", "team_full"), (white, extra))

    async def test_reopening_after_the_host_left_drops_the_old_hosts_computer_seats(self):   # cross-check A, new item 1
        host, st = await self.room(2, claim=1)
        guest, _ = await self.join(st["code"], seat="white", claim=1)
        ai_red, _ = await self.join(st["code"], seat="red", claim=1, ai_host_token=st["seat_token"])
        ai_white, _ = await self.join(st["code"], seat="white", claim=1, ai_host_token=st["seat_token"])
        for sock, units in ((host, HEROES[:1]), (guest, HEROES[:1]), (ai_red, HEROES[1:2]), (ai_white, HEROES[1:2])):
            await self.send(sock, type="ready", units=units)
        await self.send(host, type="begin")
        await self.until(guest, is_type("start"))
        await self.send(host, type="leave")
        await self.send(guest, type="reset_lobby")
        back = await self.state_where(guest, lambda m: m.get("started") is False)
        self.assertEqual([s["seat_id"] for s in back["seats"]], ["white-1"], back["seats"])

    async def test_reset_before_the_start_does_not_hand_the_host_over(self):
        host, guest, _ = await self.full_room(2)
        await self.send(host, type="leave")
        await self.state_where(guest, lambda m: m.get("host_seat_id") == "white-1")
        other, st2 = await self.room(2)
        g2, _ = await self.join(st2["code"], seat="white", claim=1)
        await self.send(g2, type="reset_lobby")
        self.assertEqual(await self.error_of(g2), "host_only")

    # ---- external review (GLM-5.3, DeepSeek V4 Pro on Nebius, 2026-11-26), each checked in the code first
    async def test_a_spectator_round_hash_is_refused(self):
        host, guest, st = await self.full_room(2)
        await self.send(host, type="ready", units=HEROES[:2]); await self.send(guest, type="ready", units=HEROES[:2])
        await self.send(host, type="begin"); await self.until(guest, is_type("start"))
        watcher, _ = await self.join(st["code"], seat="spectator")
        await self.send(watcher, type="round_hash", round=1, hash="deadbeef")
        self.assertEqual(await self.error_of(watcher), "invalid_round_hash")

    async def test_in_a_lobby_room_ready_must_name_every_held_place(self):
        host, st = await self.room(3, claim=2)
        await self.send(host, type="ready", units=HEROES[:1])
        self.assertEqual(await self.error_of(host), "invalid_units")
        await self.send(host, type="ready")
        self.assertEqual(await self.error_of(host), "invalid_units")
        await self.send(host, type="ready", units=HEROES[:2])
        await self.state_where(host, lambda m: self.seat(m, "red-1")["ready"])

    async def test_an_mcp_client_may_create_a_lobby_room(self):
        _, st = await self.host(2, lobby=True, client_kind="mcp")
        self.assertEqual((st["type"], st["allow_mcp"]), ("room_state", False), st)

    async def test_a_countdown_is_not_replayed_to_a_newcomer(self):
        host, guest, st = await self.full_room(2)
        await self.send(host, type="ready", units=HEROES[:2]); await self.send(guest, type="ready", units=HEROES[:2])
        self.relay.countdown_seconds = 5
        await self.send(host, type="begin"); await self.until(guest, is_type("countdown"))
        await self.send(host, type="begin", on=False); await self.until(guest, lambda m: m.get("type") == "countdown" and m["seconds"] is None)
        watcher, _ = await self.join(st["code"], seat="spectator")
        seen = await self.nothing_starts(watcher, 0.4)
        self.assertNotIn("countdown", [m["type"] for m in seen], seen)

    async def test_a_ping_keeps_a_quiet_lobby_alive_and_answers_nothing(self):
        host, st = await self.room(2)
        await self.send(host, type="ping")
        seen = await self.nothing_starts(host, 0.3)
        self.assertEqual([m for m in seen if m.get("type") == "error"], [], seen)

    def test_the_default_origin_rule_is_exact_localhost(self):   # external review (GLM-5.3): a prefix match let http://localhost.evil.com in
        from pk_relay import RelayServer
        r = RelayServer("127.0.0.1", 0, origin_allowlist="")
        for origin, want in (("http://localhost:8080", True), ("http://127.0.0.1", True), ("http://localhost", True), ("http://localhost.evil.com", False),
                             ("http://127.0.0.1.evil.com:80", False), ("http://localhostx", False), ("https://evil.com", False)):
            self.assertEqual(r._origin_allowed(origin), want, origin)

    # ---- R13: move
    async def test_take_and_release_places_of_the_own_team(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                host, st = await self.room(n)
                await self.send(host, type="ready", units=HEROES[:1])
                await self.send(host, type="move", claim=n)
                state = await self.state_where(host, lambda m: self.seat(m, "red-1")["claim"] == n)
                self.assertFalse(self.seat(state, "red-1")["ready"], "new places need new heroes")
                await self.send(host, type="move", claim=1)
                state = await self.state_where(host, lambda m: self.seat(m, "red-1")["claim"] == 1)
                self.assertEqual(self.seat(state, "red-1")["units"], HEROES[:1])
                await self.send(host, type="move", claim=3)
                state = await self.state_where(host, lambda m: self.seat(m, "red-1")["claim"] > 1)
                self.assertEqual(self.seat(state, "red-1")["claim"], n, "never more than the team has")

    async def test_changing_side_moves_the_whole_player_with_a_new_seat_id_and_keeps_the_host(self):
        for n in (1, 2, 3):
            with self.subTest(team_size=n):
                host, st = await self.room(n, name="房主")
                await self.send(host, type="move", team="white")
                mine = await self.until(host, lambda m: m.get("type") == "room_state" and m.get("seat_id") == "white-1")
                self.assertEqual((mine["seat"], mine["host_seat_id"], mine["seat_token"]), ("white", "white-1", st["seat_token"]))
                self.assertEqual([(x["seat_id"], x["name"], x["ready"]) for x in mine["seats"]], [("white-1", "房主", False)])
                red, joined = await self.join(st["code"], seat="red", claim=1)
                self.assertEqual(joined["seat_id"], "red-1")

    async def test_moves_that_are_not_possible_are_refused(self):
        host, guest, st = await self.full_room(2)
        await self.send(guest, type="move", team="red")
        self.assertEqual(await self.error_of(guest), "team_full")
        for bad in ({"team": "blue"}, {"claim": 0}, {"claim": "2"}, {"claim": True}):
            await self.send(guest, type="move", **bad)
            self.assertEqual(await self.error_of(guest), "invalid_options", bad)
        watcher, _ = await self.join(st["code"], seat="spectator")
        await self.send(watcher, type="move", team="red")
        self.assertEqual(await self.error_of(watcher), "move_not_allowed")
        solo_host, solo_st = await self.room(1)
        other, _ = await self.join(solo_st["code"], seat="white")
        await self.send(other, type="move", team="red")
        self.assertEqual(await self.error_of(other), "team_full")
        await self.send(host, type="ready", units=HEROES[:2])
        await self.send(guest, type="ready", units=HEROES[:2])
        await self.send(host, type="begin")
        await self.until(host, is_type("start"))
        await self.send(host, type="move", claim=1)
        self.assertEqual(await self.error_of(host), "room_started")

    async def test_changing_side_takes_back_the_own_agent_and_invite(self):
        host, st = await self.room(3)
        await self.send(host, type="room_options", allow_mcp=True)
        await self.state_where(host, lambda m: m.get("allow_mcp") is True)
        made = await self.invite(host)
        agent, _ = await self.join(st["code"], invite=made["invite"])
        await self.send(host, type="move", team="white")
        self.assertEqual((await self.until(agent, is_type("kicked")))["reason"], "inviter_left")
        state = await self.state_where(host, lambda m: [x["seat_id"] for x in m["seats"]] == ["white-1"])
        self.assertEqual(state["invites"], [])

    async def test_an_unlock_in_a_lobby_releases_the_heroes(self):   # red team (polish) page P7: an unlocked pick blocked a teammate
        host, st = await self.room(3, claim=1)
        mate, _ = await self.join(st["code"], seat="red", claim=1)
        await self.send(host, type="ready", units=["knight"])
        await self.state_where(mate, lambda m: self.seat(m, "red-1")["units"] == ["knight"])
        await self.send(host, type="unready")
        await self.state_where(mate, lambda m: self.seat(m, "red-1")["units"] == [])
        await self.send(mate, type="ready", units=["knight"])
        await self.state_where(mate, lambda m: self.seat(m, "red-2")["ready"])

    async def test_host_handover_prefers_connected_seat_over_disconnected_earlier_seat(self):
        host, st = await self.room(3)
        g1, _ = await self.join(st["code"], seat="white", claim=1)
        g2, _ = await self.join(st["code"], seat="white", claim=1)
        await g1.close()
        await asyncio.sleep(0.05)
        await self.send(host, type="leave")
        state = await self.state_where(g2, lambda m: m.get("host_seat_id") != "red-1")
        self.assertEqual(state["host_seat_id"], "white-2")

    async def test_lobby_refuses_duplicate_heroes_on_same_team_and_clears_units_on_side_switch(self):
        host, st = await self.room(2, claim=1)
        mate, _ = await self.join(st["code"], seat="red", claim=1)
        # Self-duplicate on a 2-unit claim is refused
        await self.send(mate, type="leave")
        await self.send(host, type="move", claim=2)
        await self.state_where(host, lambda m: self.seat(m, "red-1")["claim"] == 2)
        await self.send(host, type="ready", units=["wizard", "wizard"])
        self.assertEqual(await self.error_of(host), "invalid_units")
        # Teammate duplicate is refused
        await self.send(host, type="move", claim=1)
        await self.state_where(host, lambda m: self.seat(m, "red-1")["claim"] == 1)
        mate2, _ = await self.join(st["code"], seat="red", claim=1)
        await self.send(host, type="ready", units=["wizard"])
        await self.state_where(host, lambda m: self.seat(m, "red-1")["ready"])
        await self.send(mate2, type="ready", units=["wizard"])
        self.assertEqual(await self.error_of(mate2), "invalid_units")
        await self.send(mate2, type="ready", units=["skeleton"])
        await self.state_where(mate2, lambda m: self.seat(m, "red-2")["ready"])
        # Side switch clears units so no stale hero carries over to the new team
        await self.send(mate2, type="move", team="white")
        moved = await self.until(mate2, lambda m: m.get("type") == "room_state" and m.get("seat_id") == "white-1")
        self.assertEqual(self.seat(moved, "white-1")["units"], [])


if __name__ == "__main__":
    unittest.main()
