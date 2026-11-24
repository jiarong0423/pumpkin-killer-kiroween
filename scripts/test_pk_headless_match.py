#!/usr/bin/env python3
"""Tests for the public-tool-only built-in practice seat and match runner."""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import mcp_stdio_server as srv  # noqa: E402
import pk_headless_match as runner  # noqa: E402


class HeadlessMatchTest(unittest.TestCase):
    SEED = 7351829

    def test_same_seed_writes_identical_public_transcripts(self):
        with tempfile.TemporaryDirectory() as directory:
            first = os.path.join(directory, "first.jsonl")
            second = os.path.join(directory, "second.jsonl")
            one = runner.run_match(self.SEED, "scripted", "builtin:hard", first)
            two = runner.run_match(self.SEED, "scripted", "builtin:hard", second)
            with open(first, encoding="utf-8") as handle:
                first_text = handle.read()
            with open(second, encoding="utf-8") as handle:
                second_text = handle.read()
        self.assertEqual(one, two)
        self.assertEqual(first_text, second_text)

    def test_transcript_redacts_private_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "match.jsonl")
            runner.run_match(self.SEED, "scripted", "builtin:normal", path)
            with open(path, encoding="utf-8") as handle:
                transcript = handle.read()
        self.assertNotIn(str(self.SEED), transcript)
        self.assertNotIn('"seed"', transcript)
        self.assertNotIn('"angle"', transcript)
        self.assertNotIn('"power"', transcript)
        self.assertNotIn(os.path.expanduser("~"), transcript)

    def test_builtin_receives_exactly_its_seat_view(self):
        session = srv.Session(mode="human_vs_agent", seed=self.SEED, clock=lambda: 0.0,
                              human_turn_seconds=0, turn_seconds=0, seat="red")
        builtin = srv.BuiltinPracticeSeat(session, session.seats["white"], "adaptive")
        session.call("end_turn", {"round": 1, "phase": "human"}, session.seats["red"])
        builtin.drive(session)
        self.assertEqual(session.engine.round_num, 2)
        self.assertEqual(builtin.last_view, session.view_for(session.seats["white"]))
        state = session.call("get_public_state", {}, session.seats["red"])
        self.assertEqual(state["engine"], "py-practice")
        self.assertIn(state["ai_level"], ("easy", "normal", "hard"))
        self.assertTrue(state["ai_reason"])

    def test_match_ends(self):
        with tempfile.TemporaryDirectory() as directory:
            result = runner.run_match(self.SEED, "builtin:easy", "scripted",
                                      os.path.join(directory, "match.jsonl"))
        self.assertIn(result["winner"], ("red", "white", "draw"))
        self.assertGreater(result["rounds"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
