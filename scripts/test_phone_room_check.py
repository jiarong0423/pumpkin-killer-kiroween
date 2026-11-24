#!/usr/bin/env python3
"""Regression test for scripts/phone_room_check.py (red-team R9A F1..F3). Needs localhost sockets and Node 22+ (listed with the other socket tests in run_full_suite.sh).
Truth-table cases for the verdict plus four runs, about 70 seconds in all (the first two are the original pair): (1) --selftest stall: the stand-in phone readies and never plays, the white seat times out: the verdict must be FAIL (exit 1) and must say why;
(2) --selftest full: a headless red page seat stands in for the phone host, 4 turns are played: PASS (exit 0) with at least one round where both seats' hashes were compared."""
import os, re, subprocess, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "phone_room_check.py")

def run(*extra):
    return subprocess.run([sys.executable, "-B", SCRIPT, "--relay-port", "0"] + list(extra), capture_output=True, text=True, timeout=200, cwd=ROOT)

sys.path.insert(0, os.path.join(ROOT, "scripts"))
import phone_room_check as prc  # noqa: E402

ANDROID = "Mozilla/5.0 (Linux; Android 14; RMX2075) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
DESKTOP = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

def good(**over):
    base = dict(finished=True, reached=False, turns=8, relay_errors=0, out_of_sync=0, hash_rounds_both=3, hash_disagree=[], seat_error=None, red_user_agent=ANDROID, require_phone=True)
    base.update(over)
    return prc.decide(**base)

class VerdictTruthTable(unittest.TestCase):
    """The verdict is a pure function: every condition has its own case, so a verdict that forgets one of them is caught (red-team R10A-2: 8 of 9 mutants of the inline version survived)."""
    def test_a_clean_run_passes(self):
        self.assertTrue(good()["ok"])
        self.assertTrue(good(finished=False, reached=True)["ok"])

    def test_each_condition_alone_fails_the_verdict(self):
        cases = {
            "neither finished nor reached": dict(finished=False, reached=False),
            "no turn": dict(turns=0),
            "relay error": dict(relay_errors=1),
            "out of sync": dict(out_of_sync=1),
            "no round compared by both seats": dict(hash_rounds_both=0),
            "hashes disagree": dict(hash_disagree=[2]),
            "seat error": dict(seat_error="timeout"),
            "red seat is not a phone": dict(red_user_agent=DESKTOP),
            "red seat unknown": dict(red_user_agent=None),
        }
        for name, over in cases.items():
            with self.subTest(name):
                verdict = good(**over)
                self.assertFalse(verdict["ok"], name)
                self.assertEqual(len(verdict["reasons"]), 1, verdict["reasons"])

    def test_the_phone_check_is_only_demanded_with_require_phone(self):
        self.assertTrue(good(red_user_agent=DESKTOP, require_phone=False)["ok"])

    def test_phone_user_agents(self):
        self.assertTrue(prc.is_phone_client(ANDROID))
        self.assertTrue(prc.is_phone_client("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148"))
        self.assertFalse(prc.is_phone_client(DESKTOP))
        self.assertFalse(prc.is_phone_client("Python/3.12 websockets/13.1"))
        self.assertFalse(prc.is_phone_client("undici"))
        self.assertFalse(prc.is_phone_client(None))


class PhoneRoomCheckTests(unittest.TestCase):
    def test_a_seat_that_times_out_is_a_fail(self):
        p = run("--selftest", "stall", "--white", "headless", "--max-seconds", "6")
        self.assertEqual(p.returncode, 1, p.stdout[-400:])
        self.assertIn("VERDICT FAIL", p.stdout)
        self.assertIn("reason=timeout", p.stdout)
        self.assertNotIn("VERDICT PASS", p.stdout)

    def test_a_played_match_is_a_pass_and_compares_both_pages(self):
        p = run("--selftest", "full", "--white", "headless", "--turns", "4", "--max-seconds", "150")
        self.assertEqual(p.returncode, 0, p.stdout[-600:])
        self.assertIn("VERDICT PASS", p.stdout)
        m = re.search(r"hash_rounds_with_both_seats=(\d+) hash_disagreements=\[\]", p.stdout)
        self.assertIsNotNone(m, p.stdout[-400:])
        self.assertGreaterEqual(int(m.group(1)), 1)
        self.assertRegex(p.stdout, r"relay_errors=0 out_of_sync=0")

    def test_the_default_one_versus_one_room_works_with_the_mcp_bridge(self):
        """Red-team R10A-1: at one unit per team (the room the phone creates) the MCP bridge used to raise KeyError 'hero' in the page snapshot and FAIL after the full timeout."""
        p = run("--selftest", "full", "--selftest-size", "1", "--white", "mcp", "--turns", "4", "--max-seconds", "150")
        self.assertEqual(p.returncode, 0, p.stdout[-600:])
        self.assertIn("VERDICT PASS", p.stdout)
        self.assertRegex(p.stdout, r"relay_errors=0 out_of_sync=0")

    def test_require_phone_fails_when_the_red_seat_is_a_headless_page(self):
        p = run("--selftest", "full", "--selftest-size", "1", "--white", "headless", "--turns", "4", "--max-seconds", "150", "--require-phone")
        self.assertEqual(p.returncode, 1, p.stdout[-600:])
        self.assertIn("NOT a mobile browser", p.stdout)
        self.assertIn("VERDICT FAIL", p.stdout)

if __name__ == "__main__":
    unittest.main()
