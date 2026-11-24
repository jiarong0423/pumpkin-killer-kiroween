#!/usr/bin/env python3
"""Offline tests for scripts/kiro_route.py (no Kiro, no network, no sleeping)."""
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kiro_route as kr  # noqa: E402


class Fake:
    def __init__(self, script):
        self.script, self.calls = list(script), []

    def __call__(self, model, brief, agent, cwd, timeout):
        self.calls.append(model)
        r = self.script.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


class RouteTests(unittest.TestCase):
    def go(self, script, route=("m1", "m2", "m3"), expect="", retries=1, cwd=None):
        f, logs, naps = Fake(script), [], []
        st = kr.route_run(list(route), "b.md", expect, "researcher", cwd or tempfile.gettempdir(), retries, 5, 10, logs.append, runner=f, sleep=naps.append)
        return st, f.calls, logs, naps

    def test_classify(self):
        self.assertEqual(kr.classify("Error: claude-sonnet-5.5 is experiencing high traffic ModelThrottleError", 1), "throttled")
        self.assertEqual(kr.classify("unknown model foo", 1), "bad_model")
        self.assertEqual(kr.classify("done", 0), "ok")
        self.assertEqual(kr.classify("crash", 3), "failed")
        self.assertEqual(kr.classify("", 0), "ok")
        self.assertEqual(kr.classify("a file that does not exist was skipped", 0), "ok")   # exit 0 wins over words in the text
        self.assertEqual(kr.classify("the high traffic section", 0), "ok")

    def test_first_model_ok(self):
        st, calls, _, naps = self.go([(0, "fine")])
        self.assertEqual(st, ("ok", "m1")); self.assertEqual(calls, ["m1"]); self.assertEqual(naps, [])

    def test_throttle_retries_then_switches(self):
        st, calls, _, naps = self.go([(1, "THROTTLING"), (1, "THROTTLING"), (0, "fine")])
        self.assertEqual(st, ("ok", "m2")); self.assertEqual(calls, ["m1", "m1", "m2"]); self.assertEqual(naps, [5])

    def test_throttle_then_recovers_same_model(self):
        st, calls, _, _ = self.go([(1, "high traffic"), (0, "fine")])
        self.assertEqual(st, ("ok", "m1")); self.assertEqual(calls, ["m1", "m1"])

    def test_bad_model_skips_without_retry(self):
        st, calls, _, naps = self.go([(1, "unknown model"), (0, "fine")])
        self.assertEqual(st, ("ok", "m2")); self.assertEqual(calls, ["m1", "m2"]); self.assertEqual(naps, [])

    def test_all_fail_is_failed(self):
        st, calls, logs, _ = self.go([(1, "boom"), (1, "boom"), (1, "boom")])
        self.assertEqual(st, ("failed", None)); self.assertEqual(calls, ["m1", "m2", "m3"])

    def test_timeout_moves_on(self):
        st, calls, logs, _ = self.go([subprocess.TimeoutExpired("x", 1), (0, "fine")])
        self.assertEqual(st, ("ok", "m2")); self.assertTrue(any("ERROR timeout" in l for l in logs))

    def test_missing_expected_file_is_not_success(self):
        with tempfile.TemporaryDirectory() as d:
            st, calls, logs, _ = self.go([(0, "fine"), (0, "fine"), (0, "fine")], expect="out.md", cwd=d)
            self.assertEqual(st, ("failed", None)); self.assertTrue(any("expected file is missing" in l for l in logs))
            open(os.path.join(d, "out.md"), "w").write("x")
            st, calls, _, _ = self.go([(0, "fine")], expect="out.md", cwd=d)
            self.assertEqual(st, ("ok", "m1"))

    def test_expected_file_glob(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "out_gpt-5.6-terra.json"), "w").write("x")
            st, calls, _, _ = self.go([(0, "fine")], expect="out_*.json", cwd=d)
            self.assertEqual(st, ("ok", "m1"))

    def test_cli_missing_fails_loudly(self):
        st, calls, logs, _ = self.go([FileNotFoundError("kiro-cli")])
        self.assertEqual(st, ("failed", None)); self.assertTrue(any("cannot start kiro-cli" in l for l in logs))

    def test_config_loading(self):
        route, retries, pause = kr.load_route("design", os.path.join(os.path.dirname(os.path.abspath(__file__)), "kiro_models.json"))
        self.assertEqual(route[0], "gpt-5.6-terra"); self.assertGreaterEqual(retries, 1)
        with self.assertRaises(ValueError):
            kr.load_route("nope", os.path.join(os.path.dirname(os.path.abspath(__file__)), "kiro_models.json"))

    def test_main_bad_config_returns_2(self):
        self.assertEqual(kr.main(["--brief", "b.md", "--route", "nope"]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
