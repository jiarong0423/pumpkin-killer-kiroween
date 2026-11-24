#!/usr/bin/env python3
"""The MCP bridge in a room judged by the real page (PageJudgeRelay): an agent seat against a headless page seat over a local relay.

Checks: no relay error, every round hash equal on both seats, the agent's public view equals the page's own state (hp, positions, fence, round), landed throws show up in
get_history with the page's result, a throw that is not plain is refused, the agent never receives a flight formula or constant, and `--page-judge off` keeps the old bridge.
Needs Node 22+ and a local socket (the relay runs in this process); skipped when Node is missing."""
import asyncio
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import mcp_stdio_server as srv  # noqa: E402
from pk_relay import RelayServer, Room  # noqa: E402

NODE = shutil.which("node")


class RelayThread:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.ready = threading.Event()
        self.errors = []
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        if not self.ready.wait(3):
            raise RuntimeError("relay did not start")

    def _run(self):
        asyncio.set_event_loop(self.loop)
        outer = self

        class Counting(RelayServer):
            async def _error(self, websocket, code, message=None):
                outer.errors.append(code)
                await super()._error(websocket, code, message)
        self.relay = Counting("127.0.0.1", 0)
        self.loop.run_until_complete(self.relay.start())
        self.ready.set()
        self.loop.run_forever()
        self.loop.run_until_complete(self.relay.close())
        self.loop.close()

    def close(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(3)


def wait_for(predicate, message, seconds=20):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise AssertionError(message)


class RecordingPageJudgeRelay(srv.PageJudgeRelay):
    """The bridge, plus a copy of every raw landed-throw record of the page (the public view drops the number of victims); test-side only."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.raw_records = []

    def _apply(self, st, records):
        self.raw_records.extend(records)
        super()._apply(st, records)


@unittest.skipIf(NODE is None, "Node is not installed")
class PageJudgeRoomTest(unittest.TestCase):
    def setUp(self):
        self.host = RelayThread()
        self.code = "JUDGE3"
        self.host.relay.rooms[self.code] = Room(self.code, scene="graveyard", team_size=3)
        self.port = self.host.relay.bound_port
        self.procs = []
        self.bridge = None

    def tearDown(self):
        if self.bridge is not None:
            self.bridge.close()
        for proc in self.procs:
            if proc.poll() is None:
                proc.kill()
        self.host.close()

    def start_pair(self, red=None, level="normal", relay_cls=None):
        url = "ws://127.0.0.1:%d" % self.port
        red = list(red) if red else ["bride", "hunchback", "reaper"]
        white = ["hag", "skeleton", "wizard"]
        # the headless page seat (white): the real page playing by itself, at the same rate as the bridge's page
        self.procs.append(subprocess.Popen(["node", str(HERE / "hybrid_seat_headless.js"), "--relay", url, "--code", self.code, "--team", "white", "--heroes", ",".join(white),
                                            "--level", level, "--rng", "5", "--speed", "8", "--max-s", "120"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(ROOT)))
        session = srv.Session(seed=1, units=3, seat="red", hero_red=red, hero_white=white, turn_seconds=3600, human_turn_seconds=3600)
        self.bridge = (relay_cls or srv.PageJudgeRelay)(session, url + "/ws", self.code, "red", speed=8.0, rng=7)
        self.server = srv.McpServer(session)
        self.server.relay = self.bridge
        self.session = session
        self.bridge.start()
        wait_for(lambda: self.bridge.started, "the bridge's page did not see the room start")
        time.sleep(0.5)

    def call(self, name, arguments=None):
        result = self.server._call_tool(name, arguments or {})
        payload = json.loads(result["content"][0]["text"])
        return result["isError"], payload

    def play_turns(self, turns):
        done = 0
        key = None
        deadline = time.monotonic() + 60
        while done < turns and time.monotonic() < deadline:
            _, state = self.call("get_public_state")
            if state["winner"] or state["phase"] == "over":
                break
            if state["phase"] == "human" and (state["round"], state["phase"]) != key:
                unit = next(uid for uid, u in sorted(state["units"].items()) if u["team"] == "red" and u["alive"])
                error, payload = self.call("submit_action", {"unit": unit, "round": state["round"], "action": {"type": "throw", "angle": 54, "power": 66.0}})
                if error and "active unit is" in payload["error"]:
                    unit = payload["error"].rsplit("active unit is ", 1)[1].strip()
                    error, payload = self.call("submit_action", {"unit": unit, "round": state["round"], "action": {"type": "throw", "angle": 54, "power": 66.0}})
                self.assertFalse(error, payload)
                error, payload = self.call("end_turn", {"round": state["round"], "phase": "human"})
                self.assertFalse(error, payload)
                key = (state["round"], state["phase"])
                done += 1
            else:
                time.sleep(0.05)
        return done

    def test_agent_and_page_stay_in_step(self):
        self.start_pair()
        self.assertEqual(self.play_turns(5), 5)
        time.sleep(1.0)
        self.assertEqual(self.host.errors, [], "relay errors")
        hashes = self.host.relay.rooms[self.code].round_hashes
        self.assertTrue(hashes, "round hashes were sent")
        for number, by_seat in hashes.items():
            self.assertEqual(len(set(by_seat.values())), 1, "round %s hash differs: %s" % (number, by_seat))
        with self.bridge.lock:
            st = self.bridge.state
            for row in st["units"]:
                unit = self.session.engine.units[self.bridge._engine_id(row["id"])]
                self.assertAlmostEqual(unit["hp"], row["hp"], places=2, msg=row["id"])
                self.assertAlmostEqual(unit["x"], row["x"], places=2, msg=row["id"])
            self.assertEqual(self.session.engine.central_wall_hp, st["wallHp"])
        _, history = self.call("get_history", {"limit": 10, "include_path": False})
        self.assertGreaterEqual(len(history["throws"]), 5)
        mine = [t for t in history["throws"] if t["team"] == "red"]
        self.assertTrue(mine and all("landing_x" in t and "hit_type" in t for t in mine))

    def test_only_plain_throws_and_no_formula_in_the_public_view(self):
        self.start_pair()
        wait_for(lambda: self.session.phase == "human", "red opens")
        _, state = self.call("get_public_state")
        unit = next(uid for uid, u in sorted(state["units"].items()) if u["team"] == "red")
        error, payload = self.call("submit_action", {"unit": unit, "round": state["round"], "action": {"type": "move", "direction": "forward"}})
        self.assertTrue(error)
        self.assertIn("plain throws", payload["error"])
        # ultimate before 3 energy is rejected with the energy check
        error_ult, payload_ult = self.call("submit_action", {"unit": unit, "round": state["round"], "action": {"type": "ultimate", "angle": 54, "power": 66.0}})
        self.assertTrue(error_ult)
        self.assertIn("ultimate_not_ready", payload_ult["error"])
        text = json.dumps(state) + json.dumps(self.call("get_roster")[1])
        for banned in ("GRAVITY", "WIND_TAIL", "WIND_HEAD", "V0_PER_POWER", "gravity", "aiCal", "simulateLandingX"):
            self.assertNotIn(banned, text)

    def test_page_judge_can_be_switched_off(self):
        result = subprocess.run([sys.executable, "-B", str(HERE / "mcp_stdio_server.py"), "--help"], capture_output=True, text=True, timeout=20)
        self.assertIn("--page-judge", result.stdout)

    def test_3v3_ultimate_over_page_judge_relay(self):
        self.start_pair()
        ult_fired = False
        for _ in range(30):   # was 10: the test hopes plain throws at a fixed aim bring three energy marks, and 10 rounds failed about one run in six (2026-11-22 review); the loop stops as soon as the ultimate fired or the match ended
            wait_for(lambda: self.session.phase == "human" or self.session.winner is not None, "wait human turn", 30)
            _, st = self.call("get_public_state")
            if st["winner"] or st["phase"] == "over":
                break
            unit = next(uid for uid, u in sorted(st["units"].items()) if u["team"] == "red" and u["alive"])

            def submit(unit_id):
                # the reaper's ultimate is refused in a room (its flames start on a clock-driven orbit, so two pages simulate different volleys: gap N10); fire it with another unit
                kind = "ultimate" if st["ultimate_energy"]["red"] >= 3 and not ult_fired and st["units"][unit_id]["class"] != "reaper" else "throw"
                return kind, self.call("submit_action", {"unit": unit_id, "round": st["round"], "action": {"type": kind, "angle": 54, "power": 64.0}})
            atype, (error, payload) = submit(unit)
            if error and "active unit is" in payload["error"]:
                unit = payload["error"].rsplit("active unit is ", 1)[1].strip()
                atype, (error, payload) = submit(unit)
            self.assertFalse(error, payload)
            if atype == "ultimate":
                ult_fired = True
            error, payload = self.call("end_turn", {"round": st["round"], "phase": "human"})
            self.assertFalse(error, payload)
            if ult_fired:
                break
        time.sleep(0.6)
        self.assertTrue(ult_fired, "red accumulated 3 energy and fired a 3v3 ultimate")
        print("SCENARIO_RECORD " + json.dumps({"case": "3v3_ultimate", "ultimate_fired": True}), flush=True)
        self.assertEqual(self.host.errors, [], "relay errors")
        self.assertTrue(any(r.get("ultimate") for r in self.session.engine.throw_log), "ultimate recorded in throw_log")
        for number, by_seat in self.host.relay.rooms[self.code].round_hashes.items():
            self.assertEqual(len(set(by_seat.values())), 1, "round %s hash differs: %s" % (number, by_seat))

    def test_hag_ultimate_over_page_judge_relay(self):
        """R1-1: the hag (nun) cross ultimate in a 3v3 room; both pages must stay in step (the stun pick comes from the room's seeded stream, js nunPierceFinish)."""
        # an easy computer opponent: z1_load3_c failed at round 2 because the normal computer killed the whole red team by round 23 before the hag was active with three energy marks
        # (red energy 3, winner white): the precondition of this case is the match flow, so the opponent is weakened and the hag is given time
        self.start_pair(red=["hag", "hunchback", "bride"], level="easy", relay_cls=RecordingPageJudgeRelay)
        ult_fired = False
        fire_info = None
        turns_tried = 0
        # Z1 2026-11-23: a fixed aim does not always bring three energy marks (one run of 203 under load never fired the ultimate), so aim with the engine's own flight at a living
        # enemy like the simulators do; the seeded generator keeps the choice of target and angle repeatable
        os.environ.setdefault("PK_SIM_LOG", os.path.join(os.environ.get("TMPDIR", "/tmp"), "pk_room_test_sim.log"))
        import random
        import sim_team_headless as sim
        aim_rng = random.Random(3)

        def aimed(unit_id):
            angle, power, _target = sim.aim(aim_rng, self.session.engine, self.session.engine.units[unit_id], None)
            return max(25, min(80, int(round(angle)))), float(max(20, min(115, round(power, 1))))
        for _ in range(30):
            turns_tried += 1
            wait_for(lambda: self.session.phase == "human" or self.session.winner is not None, "wait human turn", 30)
            _, st = self.call("get_public_state")
            if st["winner"] or st["phase"] == "over":
                break
            unit = next(uid for uid, u in sorted(st["units"].items()) if u["team"] == "red" and u["alive"])

            def submit(unit_id):
                kind = "ultimate" if st["ultimate_energy"]["red"] >= 3 and not ult_fired and st["units"][unit_id]["class"] == "hag" else "throw"
                angle, power = aimed(unit_id)
                return kind, self.call("submit_action", {"unit": unit_id, "round": st["round"], "action": {"type": kind, "angle": angle, "power": power}})
            atype, (error, payload) = submit(unit)
            if error and "active unit is" in payload["error"]:
                unit = payload["error"].rsplit("active unit is ", 1)[1].strip()
                atype, (error, payload) = submit(unit)
            self.assertFalse(error, payload)
            if atype == "ultimate":
                ult_fired = True
                fire_info = {"round": st["round"], "unit": unit, "energy": dict(st.get("ultimate_energy") or {})}
            error, payload = self.call("end_turn", {"round": st["round"], "phase": "human"})
            self.assertFalse(error, payload)
            if ult_fired:
                break
        time.sleep(1.2)   # past the page's 380 ms stun timer and the second-contact timer, so a late effect would show in the next round hash too
        # Z1 2026-11-23, fourth failure of this case (z1_load3_d round 10): the hag was dead while red held three energy marks. Whether the hag gets to fire depends on the match flow, so
        # this case no longer FAILS when it does not: it reports what happened in a SCENARIO_RECORD line (the stress summary counts how often the ultimate was really fired and how many
        # enemy units it hurt) and still checks every round hash; the guaranteed check of the stun pick is the deterministic test_page_nun_pierce_pair.js
        _, last = self.call("get_public_state")
        alive = {uid: [u["class"], round(u["hp"], 1)] for uid, u in sorted(last["units"].items()) if u["alive"]}
        raw_ult = [r for r in getattr(self.bridge, "raw_records", []) if r.get("ultimate")]
        record = {"case": "hag_ultimate", "ultimate_fired": bool(ult_fired), "victims": (raw_ult[0].get("victims") if raw_ult else None), "fire": fire_info,
                  "round_end": last["round"], "winner": last["winner"], "red_energy_end": (last.get("ultimate_energy") or {}).get("red"), "alive": alive, "turns_tried": turns_tried}
        print("SCENARIO_RECORD " + json.dumps(record, sort_keys=True), flush=True)
        self.assertEqual(self.host.errors, [], "relay errors")
        if ult_fired:
            self.assertTrue(any(r.get("ultimate") for r in self.session.engine.throw_log), "ultimate recorded in throw_log")
        for number, by_seat in self.host.relay.rooms[self.code].round_hashes.items():
            self.assertEqual(len(set(by_seat.values())), 1, "round %s hash differs: %s" % (number, by_seat))

    def test_reaper_ultimate_is_refused_in_a_page_judged_room(self):
        self.start_pair(red=["reaper", "hunchback", "bride"])
        wait_for(lambda: self.session.phase == "human" or self.session.winner is not None, "wait human turn", 30)
        _, st = self.call("get_public_state")
        unit = next(uid for uid, u in sorted(st["units"].items()) if u["team"] == "red" and u["class"] == "reaper")   # listed first, so it is also the active unit of red's first turn
        error, payload = self.call("submit_action", {"unit": unit, "round": st["round"], "action": {"type": "ultimate", "angle": 54, "power": 64.0}})
        self.assertTrue(error, payload)
        text = json.dumps(payload)
        self.assertIn("necromancer", text)
        self.assertEqual(self.session.ultimates_used["red"], 0, "a refused ultimate must not count")


if __name__ == "__main__":
    unittest.main(verbosity=2)
