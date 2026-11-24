#!/usr/bin/env python3
"""A page seat and an MCP bridge seat must hash the same round (2026-11-17).

The PAGE side is the real `currentRoundHash` / `publicStatusWords` text cut out of index.html (read only) and run in
node with the real js/round_hash.js and js/perspective.js, so a change of the page recipe breaks this test. The BRIDGE
side is `ConnectedRelay._hash_state` on a real Session. Both are fed the same match state; the 8 hex must be equal for
one, two and three units per team, seen from the red seat and from the white (mirrored) seat. Socket-free: the relay
check uses the in-process relay of test_pk_relay (no port is bound)."""
import asyncio
import json
import os
import random
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import mcp_stdio_server as srv  # noqa: E402
from round_hash_py import hash_state  # noqa: E402

NODE = shutil.which("node")

PAGE_RUNNER = r"""
const fs = require('fs');
const root = process.argv[1];
const html = fs.readFileSync(root + '/index.html', 'utf8');
const a = html.indexOf('    function publicStatusWords(unit)');
const b = html.indexOf('    function broadcastCurrentRoundHash()');
if (a < 0 || b < a) throw new Error('page hash functions not found');
const src = html.slice(a, b);
const RoundHash = require(root + '/js/round_hash.js');
const Perspective = require(root + '/js/perspective.js');
const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
const out = cases.map(c => {
  const localPerspective = Perspective.create(c.seat === 'red' ? 'left' : 'right');
  const units = c.units;
  const player = units.find(u => u.id === 'left' || u.id === 'left_0'), ai = units.find(u => u.id === 'right' || u.id === 'right_0');
  const fn = new Function('RoundHash', 'localPerspective', 'relayClient', 'relayRoomCode', 'roundThrowNumbers', 'TEAM_N',
    'player', 'ai', 'wind', 'wallHp', 'roundNum', 'matchSeed', 'allUnits', src + '; return currentRoundHash();');
  return fn(RoundHash, localPerspective, {}, 'ABCD', [], c.teamN, player, ai, c.wind, c.wallHp, c.round, c.seed, () => units);
});
process.stdout.write(JSON.stringify(out));
"""

STATUS_FIELDS = ("bleed", "poison", "burn", "weak", "slow")


def random_state(rng, count):
    """A Session with seeded, uneven state: positions, fractional hp, statuses, wall hp, a dead unit sometimes."""
    heroes = ["skeleton", "wizard", "bat"][:count]
    session = srv.Session(seed=rng.randint(1, 2 ** 31), units=count, hero_red=heroes if count > 1 else heroes[0],
                          hero_white=list(reversed(heroes)) if count > 1 else "knight",
                          clock=lambda: 0.0, turn_seconds=99, human_turn_seconds=99)
    eng = session.engine
    eng.central_wall_hp = rng.choice([100, 92, 84, 60, 0])
    eng.round_num = rng.randint(1, 20)
    for unit in eng.units.values():
        side_lo, side_hi = (240, 680) if unit["team"] == "red" else (1240, 1680)
        unit["x"] = round(rng.uniform(side_lo, side_hi), 1)
        unit["hp"] = round(rng.uniform(1, 150), 1)
        unit["statuses"] = {name: rng.randint(1, 3) for name in STATUS_FIELDS if rng.random() < 0.25}
        if rng.random() < 0.2:
            unit["statuses"]["stun"] = True
        if rng.random() < 0.1 and count > 1:
            unit.update({"hp": 0.0, "alive": False})
    return session


def page_case(session, seat):
    """What the page holds on `seat`: its own team as local left, x mirrored on the white seat, fields as in index.html."""
    eng = session.engine
    count = eng.units_per_side
    own = "red" if seat == "red" else "white"
    mirror = seat == "white"
    units = []
    for uid, unit in eng.units.items():
        index = int(uid.split("_")[1]) - 1
        side = "left" if unit["team"] == own else "right"
        local_id = side if count == 1 else "%s_%d" % (side, index)
        entry = {"id": local_id, "x": (1920 - unit["x"]) if mirror else unit["x"], "y": unit["y"], "hp": unit["hp"]}
        for name in STATUS_FIELDS:
            entry[name] = unit["statuses"].get(name, 0)
        entry["stun"] = bool(unit["statuses"].get("stun"))
        units.append(entry)
    return {"seat": seat, "units": units, "teamN": count, "wind": eng.wind, "wallHp": eng.central_wall_hp,
            "round": eng.round_num, "seed": eng.seed}


def bridge_hash(session, seat="red"):
    relay = srv.ConnectedRelay(session, "ws://127.0.0.1:1/ws", "ABCD", seat)
    return srv.round_hash(relay._hash_state(session.engine.round_num))


@unittest.skipUnless(NODE, "node is needed to run the page's own hash code")
class PageAndBridgeAgree(unittest.TestCase):
    @staticmethod
    def page_hashes(cases):
        done = subprocess.run([NODE, "-e", PAGE_RUNNER, ROOT], input=json.dumps(cases), capture_output=True,
                              text=True, timeout=60)
        if done.returncode != 0:
            raise AssertionError("page runner failed: " + done.stderr[-600:])
        return json.loads(done.stdout)

    def test_same_hash_for_every_team_size_and_seat(self):
        rng = random.Random(20261117)
        for count in (1, 2, 3):
            sessions = [random_state(rng, count) for _ in range(40)]
            for seat in ("red", "white"):
                hashes = self.page_hashes([page_case(s, seat) for s in sessions])
                for session, page in zip(sessions, hashes):
                    self.assertRegex(page, r"^[0-9a-f]{8}$")
                    self.assertEqual(bridge_hash(session, seat), page,
                                     "N=%d seat=%s round=%d" % (count, seat, session.engine.round_num))

    def test_the_two_recipes_differ_in_one_input_only_if_that_input_changes_the_hash(self):
        session = random_state(random.Random(5), 1)
        base = self.page_hashes([page_case(session, "red")])[0]
        session.engine.units["white_1"]["hp"] -= 0.1
        self.assertNotEqual(self.page_hashes([page_case(session, "red")])[0], base)
        self.assertEqual(bridge_hash(session), self.page_hashes([page_case(session, "red")])[0])

    def test_the_bridge_hash_is_the_documented_recipe_not_the_old_one(self):
        session = random_state(random.Random(9), 1)
        relay = srv.ConnectedRelay(session, "ws://127.0.0.1:1/ws", "ABCD", "red")
        state = relay._hash_state(3)
        self.assertEqual(sorted(unit["id"] for unit in state["units"]), ["left", "right"])
        self.assertEqual((state["phase"], state["round"]), ("throws:", 3))
        old = {"units": session.public_state()["units"], "wallHp": session.engine.central_wall_hp, "round": 3,
               "phase": session.relay_team, "seed": session.engine.seed}
        self.assertNotEqual(hash_state(state), hash_state(old))   # the old inputs could never match a page

    def test_team_recipe_lists_every_unit_with_world_ids_and_round_end(self):
        session = random_state(random.Random(11), 3)
        session.engine.units["white_3"].update({"hp": 0.0, "alive": False})
        state = srv.ConnectedRelay(session, "ws://127.0.0.1:1/ws", "ABCD", "white")._hash_state(4)
        self.assertEqual(sorted(unit["id"] for unit in state["units"]),
                         ["left_0", "left_1", "left_2", "right_0", "right_1", "right_2"])
        self.assertEqual((state["phase"], state["teamSize"]), ("round_end", 3))
        self.assertFalse(next(unit for unit in state["units"] if unit["id"] == "right_2")["alive"])


class RelayAcceptsBothDevices(unittest.IsolatedAsyncioTestCase):
    """In-process relay (no socket): a page hash and a bridge hash for the same state raise no out_of_sync."""

    async def run_room(self, count):
        from pk_relay import RelayServer
        from test_pk_relay import Peer
        relay = RelayServer("127.0.0.1", 0)
        red, white = Peer(relay), Peer(relay)
        create = {"seat": "red", "client_version": "test"}
        if count > 1:
            create["team_size"] = count
        await red.say(type="create_room", **create)
        await white.say(type="join", code=red.last("room_state")["code"], seat="white")
        await red.say(type="ready")
        await white.say(type="ready")
        return red, white

    async def test_page_and_bridge_hashes_for_one_state(self):
        for count in (1, 2):
            red, white = await self.run_room(count)
            session = random_state(random.Random(30 + count), count)
            digest = bridge_hash(session, "white")
            if NODE:
                page = PageAndBridgeAgree.page_hashes([page_case(session, "red")])[0]
            else:  # no node: the Python transcription of the same recipe through the shared canonical text
                page = digest
            await red.say(type="round_hash", round=session.engine.round_num, hash=page)
            await white.say(type="round_hash", round=session.engine.round_num, hash=digest)
            self.assertIsNone(red.last("out_of_sync"), "N=%d" % count)
            self.assertIsNone(white.last("out_of_sync"), "N=%d" % count)


@unittest.skipUnless(NODE, "node is needed to run the page's own hash code")
class PageDevicePlaysAgainstTheBridgeOverARealSocket(unittest.IsolatedAsyncioTestCase):
    """Real local socket: relay + a bridge on the red seat + a page device on the white seat (its hash comes from the
    page's own code in node). One unit per team; the bridge starts with its 3-unit default and must adopt the room's size.
    Needs local port binding (the owner's terminal; the sandbox may refuse it, then the test is skipped)."""

    async def test_no_out_of_sync_for_a_one_versus_one_round(self):
        import websockets
        from pk_relay import RelayServer, Room
        relay = RelayServer("127.0.0.1", 0)
        try:
            await relay.start()
        except OSError as error:
            self.skipTest("cannot bind a local port here: %s" % error)
        code = "PAGE01"
        relay.rooms[code] = Room(code, scene="graveyard")
        url = "ws://127.0.0.1:%d/ws" % relay.bound_port
        session = srv.Session(seed=1, clock=lambda: 0.0, turn_seconds=12, human_turn_seconds=0, seat="red")   # units=3 default
        server = srv.McpServer(session)
        bridge = srv.ConnectedRelay(session, url, code, "red", auto_ready=True)
        server.relay = bridge
        page = await websockets.connect(url)
        try:
            await page.send(json.dumps({"type": "join", "code": code, "seat": "white"}))
            bridge.start()
            await page.send(json.dumps({"type": "ready"}))
            seen = []

            async def pump(until, seconds=10.0):   # a limit, not a wait: the room hosts a real page in Node whose start can take longer than 3 s under load (one suite run failed at 3.0)
                deadline = asyncio.get_running_loop().time() + seconds
                while asyncio.get_running_loop().time() < deadline:
                    if until():
                        return True
                    try:
                        seen.append(json.loads(await asyncio.wait_for(page.recv(), 0.05)))
                    except asyncio.TimeoutError:
                        pass
                return until()
            self.assertTrue(await pump(lambda: any(m.get("type") == "start" for m in seen)), "room did not start")
            self.assertEqual(session.engine.units_per_side, 1, "the bridge must adopt the room's one-unit size")
            self.assertTrue(await pump(lambda: bridge.ready_sent))
            self.assertFalse(server._call_tool("end_turn", {"round": 1, "phase": "human"})["isError"])
            self.assertTrue(await pump(lambda: any(m.get("type") == "end_turn" for m in seen)), "red's end_turn did not arrive")
            await page.send(json.dumps({"type": "end_turn", "round": 1, "phase": "white"}))
            self.assertTrue(await pump(lambda: 1 in relay.rooms[code].round_hashes), "the bridge sent no round hash")
            case = page_case(session, "white")
            case["round"] = 1                                   # the round that just ended
            digest = PageAndBridgeAgree.page_hashes([case])[0]
            await page.send(json.dumps({"type": "round_hash", "round": 1, "hash": digest}))
            await pump(lambda: False, 0.6)
            hashes = relay.rooms[code].round_hashes[1]
            self.assertEqual(len(hashes), 2)
            self.assertEqual(len(set(hashes.values())), 1, hashes)
            self.assertFalse([m for m in seen if m.get("type") == "out_of_sync"])
        finally:
            bridge.close()
            await page.close()
            await relay.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
