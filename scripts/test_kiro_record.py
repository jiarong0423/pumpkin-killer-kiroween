#!/usr/bin/env python3
"""Offline test for scripts/kiro_record.py: validation and the json written (uses a temporary file, not the real record)."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kiro_record as kr  # noqa: E402


class T(unittest.TestCase):
    def test_writes_entry(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "v.json")
            kr.LOG = os.path.join(d, "x.log")
            e = kr.record("80", "verified", "python3 -B scripts/test_mcp_game.py OK", "2026-11-10", p)
            self.assertEqual(e["status"], "verified")
            self.assertEqual(json.load(open(p, encoding="utf-8"))["80"]["date"], "2026-11-10")

    def test_rejects_bad_input(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "v.json")
            kr.LOG = os.path.join(d, "x.log")
            with self.assertRaises(ValueError):
                kr.record("x", "verified", "python3 -B scripts/t.py ok", None, p)
            with self.assertRaises(ValueError):
                kr.record("1", "great", "python3 -B scripts/t.py ok", None, p)
            with self.assertRaises(ValueError):
                kr.record("1", "verified", "looks fine to me", None, p)   # no command or file named


if __name__ == "__main__":
    unittest.main(verbosity=1)
