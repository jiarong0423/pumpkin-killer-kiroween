#!/usr/bin/env python3
"""Needs localhost sockets (listed with the other socket tests in run_full_suite.sh). ROOM-FLOW R10.
(1) the stress sequence is reproducible; (2) the real relay survives seeded lobby stress, 2v2 and 3v3 included, and the last-place race has one winner;
(3) four deliberately broken copies of the relay (places over-claimed, the host never handed over, AI seats left behind by the host, agents left behind by their inviter) MUST be reported, otherwise the stress test proves nothing."""
import os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
STRESS = os.path.join(HERE, "stress_room_alloc.py")


def run(*args, timeout=300):
    return subprocess.run([sys.executable, "-B", STRESS, *args], capture_output=True, text=True, timeout=timeout)


def mutant(old, new):
    src = open(os.path.join(HERE, "pk_relay.py"), encoding="utf-8").read()
    assert src.count(old) == 1, "mutation point moved: " + old[:50]
    handle = tempfile.NamedTemporaryFile("w", suffix="_broken_relay.py", dir=HERE, delete=False, encoding="utf-8")
    handle.write(src.replace(old, new, 1))
    handle.close()
    return handle.name


class RoomStressTests(unittest.TestCase):
    def assert_caught(self, path):   # a broken relay must be reported by at least one of the first six seeds (which one depends on the operation mix)
        for seed in range(1, 7):
            r = run("--seed", str(seed), "--steps", "1500", "--relay", path)
            if r.returncode == 1:
                return
            self.assertEqual(r.returncode, 0, r.stdout[-500:] + r.stderr[-300:])
        self.fail("no seed reported the broken relay")

    def test_sequence_is_reproducible(self):
        self.assertEqual(run("--seed", "5", "--selfcheck").returncode, 0)

    def test_real_relay_survives_the_stress(self):
        for seed in ("1", "2"):
            r = run("--seed", seed, "--steps", "1200")
            self.assertEqual(r.returncode, 0, r.stdout[-900:] + r.stderr[-300:])

    def test_overclaiming_places_is_caught(self):
        path = mutant("claim = min(max(raw or 0, len(units)), free)", "claim = max(raw or 0, len(units))")
        try:
            self.assert_caught(path)
        finally:
            os.unlink(path)

    def test_a_host_that_is_never_handed_over_is_caught(self):
        path = mutant('room.host_seat_id = min(players, key=lambda seat: seat.get("joined", 0))["seat_id"] if players else None', "pass")
        try:
            self.assert_caught(path)
        finally:
            os.unlink(path)

    def test_ai_seats_left_behind_by_the_host_are_caught(self):
        path = mutant('if room.started or gone["seat_id"] != room.host_seat_id:\n            return\n        for token, seat', 'if True:\n            return\n        for token, seat')
        try:
            self.assert_caught(path)
        finally:
            os.unlink(path)

    def test_agents_left_behind_by_their_inviter_are_caught(self):
        path = mutant('        if room.started:\n            return\n        for ticket_id, ticket', '        if True:\n            return\n        for ticket_id, ticket')
        try:
            self.assert_caught(path)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
