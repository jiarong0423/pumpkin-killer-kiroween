#!/usr/bin/env python3
"""ROOM-FLOW R11: a player invites an agent into their own team with a one-use ticket; the agent gets a briefing and is locked after the pick time.
Real relay on a free port, real sockets (listed with the socket tests in run_full_suite.sh). Both team sizes."""
import asyncio
import json
import sys
import unittest
from pathlib import Path

import websockets

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pk_relay import MAX_MESSAGE_BYTES, RelayServer  # noqa: E402

HEROES = ["skeleton", "wizard", "bat"]


class Base(unittest.IsolatedAsyncioTestCase):
    limits: dict = {}

    async def asyncSetUp(self):
        self.relay = RelayServer("127.0.0.1", 0, max_per_addr=100, max_connects_per_min=100000, max_wrong_per_addr=100000, **self.limits)
        await self.relay.start()
        self.url = f"ws://127.0.0.1:{self.relay.bound_port}/ws"
        self.sockets = []

    async def asyncTearDown(self):
        for s in self.sockets:
            await s.close()
        await self.relay.close()

    async def say(self, message):
        s = await websockets.connect(self.url, max_size=MAX_MESSAGE_BYTES)
        self.sockets.append(s)
        await s.send(json.dumps(message))
        return s, await self.until(s, lambda m: m.get("type") in ("room_state", "error"))

    async def until(self, s, wanted, tries=30):
        for _ in range(tries):
            m = json.loads(await asyncio.wait_for(s.recv(), 3))
            if wanted(m):
                return m
        raise AssertionError("message never came")

    async def host(self, size, claim=1, **extra):
        return await self.say(dict({"type": "create_room", "seat": "red", "team_size": size, "claim": claim}, **extra))

    async def join(self, code, **extra):
        return await self.say(dict({"type": "join", "code": code}, **extra))

    async def invite(self, s, **extra):
        await s.send(json.dumps(dict({"type": "invite"}, **extra)))
        return await self.until(s, lambda m: m.get("type") in ("invite_created", "error"))

    async def send(self, s, **message):
        await s.send(json.dumps(message))

    async def state_where(self, s, predicate):
        return await self.until(s, lambda m: m.get("type") == "room_state" and predicate(m))

    async def error_of(self, s):
        return (await self.until(s, lambda m: m.get("type") == "error"))["code"]

    @staticmethod
    def seat(state, seat_id):
        return next(x for x in state["seats"] if x["seat_id"] == seat_id)


class InviteTests(Base):
    async def test_a_ticket_holds_one_place_of_the_inviters_team_and_its_id_stays_private(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                host, st = await self.host(n)
                guest, _ = await self.join(st["code"], seat="white", claim=1)
                made = await self.invite(host)
                self.assertEqual((made["type"], made["team"], made["expires_in"]), ("invite_created", "red", 600), made)
                self.assertTrue(made["invite"].startswith("red.") and len(made["invite"]) > 12, made)
                state = await self.state_where(guest, lambda m: m.get("invites"))
                self.assertEqual([(t["by"], t["team"]) for t in state["invites"]], [("red-1", "red")])
                self.assertNotIn(made["invite"].split(".")[1], json.dumps(state), "the ticket id is not broadcast")
                other, joined = await self.join(st["code"], seat="red", claim=n)
                if n == 2:
                    self.assertEqual(joined.get("code"), "team_full", joined)
                else:
                    self.assertEqual(self.seat(joined, "red-2")["claim"], 1, joined)

    async def test_the_agent_takes_the_place_with_a_briefing_and_the_ticket_is_used_up(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                host, st = await self.host(n, name="房主")
                made = await self.invite(host, note="focus the wizard\u202e\n now")
                agent, state = await self.join(st["code"], invite=made["invite"], seat="white", units=HEROES[:1])
                self.assertEqual(state["type"], "room_state", state)
                mine = self.seat(state, state["seat_id"])
                self.assertEqual((mine["team"], mine["claim"], mine["agent"], mine["invited_by"], mine["name"]), ("red", 1, True, "red-1", "Agent"), mine)
                self.assertEqual(state.get("invites"), [])
                brief = state["briefing"]
                self.assertEqual((brief["team"], brief["places"], brief["invited_by"], brief["note"]),
                                 ("red", 1, {"seat_id": "red-1", "name": "房主"}, "focus the wizard now"), brief)
                self.assertEqual((brief["pick_within_seconds"], brief["turn_seconds"], len(brief["heroes"])), (30, 12, 8), brief)
                self.assertTrue(brief["goal"] and brief["steps"] and brief["rules"])
                _, again = await self.join(st["code"], invite=made["invite"])
                self.assertEqual(again.get("code"), "invalid_invite", again)
                _, watcher_view = await self.join(st["code"], seat="spectator")
                self.assertNotIn("briefing", watcher_view)

    async def test_bad_tickets_are_refused(self):
        host, st = await self.host(3)
        made = await self.invite(host)
        for bad in ("red.nope", "white." + made["invite"].split(".")[1], "", 7, None):
            with self.subTest(invite=bad):
                _, answer = await self.join(st["code"], invite=bad)
                self.assertEqual(answer.get("code"), "invalid_invite", answer)
        _, other_room = await self.host(3)
        _, answer = await self.join(other_room["code"], invite=made["invite"])
        self.assertEqual(answer.get("code"), "invalid_invite", answer)
        _, good = await self.join(st["code"], invite=made["invite"])
        self.assertEqual(good["type"], "room_state", good)

    async def test_one_agent_per_player_and_who_may_invite(self):
        host, st = await self.host(3)
        first = await self.invite(host)
        self.assertEqual((await self.invite(host))["invite"], first["invite"], "asking again gives the same open ticket")
        agent, _ = await self.join(st["code"], invite=first["invite"])
        self.assertEqual((await self.invite(host))["code"], "invite_limit")
        self.assertEqual((await self.invite(agent))["code"], "invite_not_allowed")
        watcher, _ = await self.join(st["code"], seat="spectator")
        self.assertEqual((await self.invite(watcher))["code"], "invite_not_allowed")
        ai, _ = await self.join(st["code"], seat="white", ai_host_token=st["seat_token"], claim=1)
        self.assertEqual((await self.invite(ai))["code"], "invite_not_allowed")
        guest, _ = await self.join(st["code"], seat="white", claim=1)
        self.assertEqual((await self.invite(guest))["team"], "white")

    async def test_no_free_place_or_agents_switched_off_means_no_ticket(self):
        for n in (2, 3):
            host, st = await self.host(n, claim=n)
            self.assertEqual((await self.invite(host))["code"], "team_full")
        one, _ = await self.host(1)
        self.assertEqual((await self.invite(one))["code"], "team_full")
        host, st = await self.host(2)
        made = await self.invite(host)
        await self.send(host, type="room_options", allow_mcp=False)
        await self.state_where(host, lambda m: m.get("allow_mcp") is False and m.get("invites") == [])
        _, answer = await self.join(st["code"], invite=made["invite"])
        self.assertEqual(answer.get("code"), "invalid_invite", answer)
        self.assertEqual((await self.invite(host))["code"], "mcp_disabled")

    async def test_cancel_by_the_inviter_or_the_host_only(self):
        host, st = await self.host(3)
        guest, _ = await self.join(st["code"], seat="white", claim=1)
        third, _ = await self.join(st["code"], seat="white", claim=1)
        await self.invite(guest)
        await self.send(third, type="invite_cancel", by="white-1")
        self.assertEqual(await self.error_of(third), "host_only")
        await self.send(host, type="invite_cancel", by="white-1")
        await self.state_where(host, lambda m: m.get("invites") == [])
        made = await self.invite(guest)
        await self.send(guest, type="invite_cancel")
        await self.state_where(guest, lambda m: m.get("invites") == [])
        _, answer = await self.join(st["code"], invite=made["invite"])
        self.assertEqual(answer.get("code"), "invalid_invite", answer)
        await self.send(guest, type="invite_cancel")
        self.assertEqual(await self.error_of(guest), "invalid_target")

    async def test_an_open_ticket_holds_the_start_and_nothing_is_invited_after_it(self):
        for how in ("join", "cancel"):
            host, st = await self.host(2, claim=1)
            guest, _ = await self.join(st["code"], seat="white", claim=2)
            made = await self.invite(host)
            await self.send(host, type="ready", units=HEROES[:1])
            await self.send(guest, type="ready", units=HEROES[:2])
            state = await self.state_where(host, lambda m: all(x["ready"] for x in m["seats"]))
            self.assertFalse(state["started"], state)
            if how == "join":
                agent, _ = await self.join(st["code"], invite=made["invite"])
                await self.send(agent, type="ready", units=HEROES[1:2])
            else:
                await self.send(host, type="invite_cancel")
            start = await self.until(host, lambda m: m.get("type") == "start")
            if how == "join":
                self.assertEqual(start["owners"]["left_1"], "red-2", start)
            self.assertEqual((await self.invite(host))["code"], "room_started")

    async def test_the_agent_goes_when_its_inviter_goes_before_the_start(self):
        for how in ("leave", "kick", "expire"):
            with self.subTest(how=how):
                host, st = await self.host(3)
                guest, _ = await self.join(st["code"], seat="white", claim=1)
                made = await self.invite(guest)
                agent, _ = await self.join(st["code"], invite=made["invite"])
                late, _ = await self.join(st["code"], seat="red", claim=1)
                if how == "leave":
                    await self.send(guest, type="leave")
                elif how == "kick":
                    await self.send(host, type="kick", seat_id="white-1")
                else:
                    room = self.relay.rooms[st["code"]]
                    token, entry = next((t, e) for t, e in room.sessions.items() if e["seat_id"] == "white-1")
                    sock = next(k for k, e in room.clients.items() if e is entry)
                    await self.relay._remove_client(room, sock)
                    await self.relay._expire_seat(room, token)
                self.assertEqual((await self.until(agent, lambda m: m.get("type") == "kicked"))["reason"], "inviter_left")
                state = await self.state_where(host, lambda m: sorted(x["seat_id"] for x in m["seats"]) == ["red-1", "red-2"])
                self.assertEqual(state["invites"], [])

    async def test_an_agent_is_never_the_host(self):
        host, st = await self.host(3)
        guest, _ = await self.join(st["code"], seat="white", claim=1)
        agent, _ = await self.join(st["code"], invite=(await self.invite(guest))["invite"])
        await self.send(host, type="leave")
        state = await self.state_where(guest, lambda m: m.get("host_seat_id") != "red-1")
        self.assertEqual(state["host_seat_id"], "white-1", state)

    async def test_auto_seat_counts_reserved_places(self):
        host, st = await self.host(2, claim=2)
        _, joined = await self.join(st["code"])
        self.assertEqual(joined.get("seat_id"), "white-1", joined)


class InviteTimeTests(Base):
    limits = {"invite_seconds": 0.3, "agent_pick_seconds": 0.4}

    async def test_a_ticket_expires_and_frees_its_place(self):
        host, st = await self.host(2)
        made = await self.invite(host)
        await self.state_where(host, lambda m: m.get("invites") == [])
        _, answer = await self.join(st["code"], invite=made["invite"])
        self.assertEqual(answer.get("code"), "invalid_invite", answer)
        _, other = await self.join(st["code"], seat="red", claim=1)
        self.assertEqual(other["type"], "room_state", other)

    async def test_an_agent_that_does_not_pick_is_given_a_free_hero_and_locked(self):
        for n in (2, 3):
            with self.subTest(team_size=n):
                host, st = await self.host(n, claim=n - 1)
                guest, _ = await self.join(st["code"], seat="white", claim=n)
                made = await self.invite(host)   # the open ticket holds the start while the others get ready
                await self.send(host, type="ready", units=["skeleton", "wizard"][:n - 1])
                await self.send(guest, type="ready", units=HEROES[:n])
                agent, _ = await self.join(st["code"], invite=made["invite"])
                start = await self.until(host, lambda m: m.get("type") == "start", tries=60)
                self.assertEqual(len(set(start["heroes"]["left"])), n, start)
                self.assertNotIn(None, start["heroes"]["left"])

    async def test_a_one_versus_one_room_has_no_place_for_an_agent(self):   # external review (GLM-5.3) feared a 1v1 agent with no hero: the inviter holds the only place of the side
        host, st = await self.host(1, lobby=True)
        await self.send(host, type="room_options", allow_mcp=True)
        await self.state_where(host, lambda m: m.get("allow_mcp") is True)
        self.assertEqual((await self.invite(host))["code"], "team_full")

    async def test_an_agent_that_picked_keeps_its_hero(self):
        host, st = await self.host(2)
        agent, _ = await self.join(st["code"], invite=(await self.invite(host))["invite"])
        await self.send(agent, type="ready", units=["hag"])
        await asyncio.sleep(0.8)
        room = self.relay.rooms[st["code"]]
        self.assertEqual([e["units"] for e in room.sessions.values() if e.get("agent")], [["hag"]])


if __name__ == "__main__":
    unittest.main()
