#!/usr/bin/env python3
"""Red-team H1 R2-A1 & R3A P2-1: the room's claimed landing and judge must treat the bride's wave like the page (cut at the ground). Pins (1) both simulate_flight call sites of scripts/mcp_stdio_server.py carry the uncommented wave flag taken
from the exact unit/attacker variable, (2) ConnectedRelay.send_action and _judge_action in mcp_stdio_server exercise the wave flag and diverge from non-wave landings by more than the 4 px sync tolerance."""
import os, re, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import flight_py
import mcp_stdio_server as srv

class StdioWaveFlag(unittest.TestCase):
    def test_both_call_sites_pass_the_wave_flag(self):
        with open(os.path.join(HERE, "mcp_stdio_server.py"), encoding="utf-8") as f:
            src = f.read()
        sites = [m.start() for m in re.finditer(r"simulate_flight\(\{", src)]
        self.assertEqual(len(sites), 3, "three simulate_flight call sites (send_action, teammate wall-hit, judge)")
        expected = [
            (r'"wave":\s*unit\.get\("weapon"\)\s*==\s*"proj_soundwave"',
             r'"wall":\s*self\.session\.engine\.central_wall_hp\s*>\s*0'),
            (r'"wave":\s*attacker\.get\("weapon"\)\s*==\s*"proj_soundwave"',
             r'"wall":\s*self\.session\.engine\.central_wall_hp\s*>\s*0'),
            (r'"wave":\s*attacker\.get\("weapon"\)\s*==\s*"proj_soundwave"',
             r'"wall":\s*self\.session\.engine\.central_wall_hp\s*>\s*0'),
        ]
        for at, (wave_pat, wall_pat) in zip(sites, expected):
            call = src[at:at + 480]
            call_no_comments = re.sub(r"#[^\n]*", "", call)
            self.assertRegex(call_no_comments, wave_pat, call)
            self.assertRegex(call_no_comments, wall_pat, call)

    def test_the_flag_changes_a_typical_wave_landing_in_stdio_relay(self):
        sess = srv.Session(mode="agent_vs_agent", seed=7, units=1, hero_red=["bride"], hero_white=["knight"])
        sess.engine.wind = 0.0
        unit = sess.engine.units["red_1"]
        unit["x"] = 300.0
        start_x = float(unit["x"] + unit["launch"]["fwd"] * unit["facing"])
        start_y = float(unit["y"] - unit["launch"]["up"])
        base = {"startX": start_x, "startY": start_y, "dirX": unit["facing"], "angleDeg": 55, "power": 85, "wind": 0.0}
        uncut = flight_py.simulate(base)
        cut = flight_py.simulate(dict(base, wave=True))
        self.assertGreater(abs(uncut["landingX"] - cut["landingX"]), 4.0)

        relay = srv.ConnectedRelay(sess, "ws://127.0.0.1:0", "ROOM", "white")
        sess.sync = {"status": "pending", "round": sess.engine.round_num}
        relay.send_action({"unit": "red_1", "action": {"type": "throw", "angle": 55, "power": 85}})
        claimed = relay.last_sent_action["claimed_landing"]
        self.assertAlmostEqual(claimed["x"], cut["landingX"], places=2)
        self.assertAlmostEqual(claimed["y"], cut["landingY"], places=2)

        # Judge accepts the wave-cut landing and flags an uncut landing as out_of_sync.
        relay._judge_action({"seq": 1, "start": {"x": start_x, "y": start_y}, "dirX": unit["facing"], "angle": 55, "power": 85,
                             "round": sess.engine.round_num, "claimed_landing": {"x": cut["landingX"], "y": cut["landingY"]}}, unit_id="red_1")
        self.assertNotEqual(sess.sync["status"], "out_of_sync")
        relay._judge_action({"seq": 2, "start": {"x": start_x, "y": start_y}, "dirX": unit["facing"], "angle": 55, "power": 85,
                             "round": sess.engine.round_num, "claimed_landing": {"x": uncut["landingX"], "y": uncut["landingY"]}}, unit_id="red_1")
        self.assertEqual(sess.sync["status"], "out_of_sync")

    def test_broken_wall_lets_flat_shots_pass_through(self):
        sess = srv.Session(mode="agent_vs_agent", seed=7, units=1, hero_red=["skeleton"], hero_white=["knight"])
        sess.engine.wind = 0.0
        unit = sess.engine.units["red_1"]
        unit["x"] = 600.0
        start_x = float(unit["x"] + unit["launch"]["fwd"] * unit["facing"])
        start_y = float(unit["y"] - unit["launch"]["up"])
        # Flat shot that hits the standing fence, then passes straight through once wall_hp == 0.
        standing = flight_py.simulate({"startX": start_x, "startY": start_y, "dirX": 1, "angleDeg": 15, "power": 55, "wind": 0.0, "wall": True})
        broken = flight_py.simulate({"startX": start_x, "startY": start_y, "dirX": 1, "angleDeg": 15, "power": 55, "wind": 0.0, "wall": False})
        self.assertEqual(standing["hit"], "wall")
        self.assertEqual(broken["hit"], "ground")
        self.assertGreater(broken["landingX"], 1100.0)

        sess.engine.central_wall_hp = 0
        relay = srv.ConnectedRelay(sess, "ws://127.0.0.1:0", "ROOM", "white")
        sess.sync = {"status": "pending", "round": sess.engine.round_num}
        relay.send_action({"unit": "red_1", "action": {"type": "throw", "angle": 15, "power": 55}})
        claimed = relay.last_sent_action["claimed_landing"]
        self.assertAlmostEqual(claimed["x"], broken["landingX"], places=2)
        relay._judge_action({"seq": 3, "start": {"x": start_x, "y": start_y}, "dirX": 1, "angle": 15, "power": 55,
                             "round": sess.engine.round_num, "claimed_landing": {"x": broken["landingX"], "y": broken["landingY"]}}, unit_id="red_1")
        self.assertNotEqual(sess.sync["status"], "out_of_sync")
        relay._judge_action({"seq": 4, "start": {"x": start_x, "y": start_y}, "dirX": 1, "angle": 15, "power": 55,
                             "round": sess.engine.round_num, "claimed_landing": {"x": standing["landingX"], "y": standing["landingY"]}}, unit_id="red_1")
        self.assertEqual(sess.sync["status"], "out_of_sync")

    def test_standing_wall_stops_flat_shots_and_damages_in_1v1(self):
        sess = srv.Session(mode="agent_vs_agent", seed=7, units=1, hero_red=["skeleton"], hero_white=["knight"])
        sess.engine.wind = 0.0
        unit = sess.engine.units["red_1"]
        unit["x"] = 600.0
        start_x = float(unit["x"] + unit["launch"]["fwd"] * unit["facing"])
        start_y = float(unit["y"] - unit["launch"]["up"])
        standing = flight_py.simulate({"startX": start_x, "startY": start_y, "dirX": 1, "angleDeg": 15, "power": 55, "wind": 0.0, "wall": True})
        broken = flight_py.simulate({"startX": start_x, "startY": start_y, "dirX": 1, "angleDeg": 15, "power": 55, "wind": 0.0, "wall": False})

        relay = srv.ConnectedRelay(sess, "ws://127.0.0.1:0", "ROOM", "white")
        sess.sync = {"status": "pending", "round": sess.engine.round_num}
        relay.send_action({"unit": "red_1", "action": {"type": "throw", "angle": 15, "power": 55}})
        claimed = relay.last_sent_action["claimed_landing"]
        self.assertAlmostEqual(claimed["x"], standing["landingX"], places=2)
        self.assertAlmostEqual(claimed["y"], standing["landingY"], places=2)
        self.assertEqual(sess.engine.central_wall_hp, 92)

        relay._judge_action({"seq": 1, "start": {"x": start_x, "y": start_y}, "dirX": 1, "angle": 15, "power": 55,
                             "round": sess.engine.round_num, "claimed_landing": {"x": standing["landingX"], "y": standing["landingY"]}}, unit_id="red_1")
        self.assertEqual(sess.engine.central_wall_hp, 84)
        self.assertNotEqual(sess.sync["status"], "out_of_sync")
        relay._judge_action({"seq": 2, "start": {"x": start_x, "y": start_y}, "dirX": 1, "angle": 15, "power": 55,
                             "round": sess.engine.round_num, "claimed_landing": {"x": broken["landingX"], "y": broken["landingY"]}}, unit_id="red_1")
        self.assertEqual(sess.sync["status"], "out_of_sync")

if __name__ == "__main__": unittest.main()
