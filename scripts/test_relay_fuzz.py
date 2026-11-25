#!/usr/bin/env python3
"""Needs localhost sockets (listed with the other socket tests in run_full_suite.sh).
(1) the sequence is reproducible and seed-dependent; (2) the real relay survives 300 hostile steps; (3) a deliberately broken copy of the
relay (every message type parsing raises) MUST be reported as a failure, otherwise the fuzzer proves nothing."""
import os, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUZZ = os.path.join(ROOT, "scripts", "fuzz_relay_break.py")


def run(*args, timeout=240):
    return subprocess.run([sys.executable, "-B", FUZZ, *args], capture_output=True, text=True, timeout=timeout)


class RelayFuzzTests(unittest.TestCase):
    def test_sequence_is_reproducible(self):
        r = run("--seed", "5", "--selfcheck")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_real_relay_survives_hostile_traffic(self):
        r = run("--seed", "7", "--steps", "300")
        self.assertEqual(r.returncode, 0, r.stdout[-800:] + r.stderr[-400:])

    def test_a_broken_relay_is_caught(self):
        src = open(os.path.join(ROOT, "scripts", "pk_relay.py"), encoding="utf-8").read()
        needle = 'message_type = message["type"]\n        if message_type == "resume":'
        self.assertEqual(src.count(needle), 1, "the mutation point moved: update this test")
        broken = src.replace(needle, 'message_type = message["type"] + 1\n        if message_type == "resume":')
        with tempfile.NamedTemporaryFile("w", suffix="_broken_relay.py", dir=os.path.join(ROOT, "scripts"), delete=False, encoding="utf-8") as f:
            f.write(broken)
        try:
            r = run("--seed", "7", "--steps", "200", "--relay", f.name)
            self.assertEqual(r.returncode, 1, "the fuzzer must FAIL on a broken relay: " + r.stdout[-500:])
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
