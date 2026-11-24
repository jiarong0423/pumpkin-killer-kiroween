#!/usr/bin/env python3
"""Real-relay tests of the slot filler (needs sockets, so the full-suite runner skips it in the sandbox): three scenarios of scripts/fill_room.py --selftest.
Each runs a real in-process relay and real headless page seats, takes about half a minute, and must print VERDICT PASS."""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


class FillRoomSelftest(unittest.TestCase):
    def run_scenario(self, scenario):
        result = subprocess.run([sys.executable, "-B", os.path.join("scripts", "fill_room.py"), "--selftest", "--scenario", scenario, "--max-seconds", "300"],
                                cwd=ROOT, capture_output=True, text=True, timeout=420)
        verdict = [line for line in result.stdout.splitlines() if "VERDICT" in line]
        self.assertTrue(verdict, "no verdict line; stdout tail: %s" % result.stdout[-400:])
        self.assertIn("VERDICT PASS", verdict[-1], verdict[-1])
        self.assertEqual(result.returncode, 0)

    def test_red_split_between_two_humans_and_the_filler_takes_white(self):
        self.run_scenario("split")

    def test_open_slots_on_both_teams_get_a_filler_each(self):
        self.run_scenario("both")

    def test_six_humans_start_no_filler_and_the_relay_starts_after_the_placeholders_leave(self):
        self.run_scenario("none")


if __name__ == "__main__":
    unittest.main()
