#!/usr/bin/env python3
"""ROOM-FLOW R7: the relay's name cleaner against the golden vectors shared with js/relay_client.js (test_name_rules.js). No sockets."""
import json
import random
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pk_relay import clean_name  # noqa: E402

VECTORS = json.loads((HERE / "name_vectors.json").read_text(encoding="ascii"))
POOL = ["a", "Z", "9", " ", "\u3000", "小", "Ａ", "é", "e", "\u0301", "\u200b", "\u200d", "\u202e", "\ufe0f", "\U0001f600", "\U0001f3fd", "\U0001f1f9", "\u2764",
        "\u3164", "\u2800", "\n", "\ud800", "\ue000", "<", "&", "'", "한", "\u1100", "\u1161", "ｱ", "\u00a0", "\U00020000", "\u2b50", "\u231a"]


class NameRuleTests(unittest.TestCase):
    def test_golden_vectors(self):
        for v in VECTORS:
            with self.subTest(case=v["case"]):
                self.assertEqual(clean_name(v["in"]), v["out"])

    def test_not_a_string_is_empty(self):
        for value in (None, 5, [], {}, True):
            self.assertEqual(clean_name(value), "")

    def test_the_page_cleaner_agrees_on_random_input_and_both_are_stable(self):
        rng = random.Random(20261126)
        names = ["".join(rng.choice(POOL) for _ in range(rng.randint(0, 24))) for _ in range(4000)]
        script = "const R=require('../js/relay_client.js');let s='';process.stdin.on('data',d=>s+=d).on('end',()=>process.stdout.write(JSON.stringify(JSON.parse(s).map(R.cleanName))))"
        out = subprocess.run(["node", "-e", script], cwd=str(HERE), input=json.dumps(names), capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr[-500:])
        for raw, js in zip(names, json.loads(out.stdout)):
            mine = clean_name(raw)
            self.assertEqual(mine, js, repr(raw))
            self.assertEqual(clean_name(mine), mine, "cleaning twice changes %r" % (raw,))


if __name__ == "__main__":
    unittest.main()
