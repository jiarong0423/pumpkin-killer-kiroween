#!/usr/bin/env python3
"""scripts/event_tally_backend.py: the comparison logic and a tiny real run (no sockets, a few seconds)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = str(HERE / "event_tally_backend.py")


class TallyTest(unittest.TestCase):
    def run_script(self, *args):
        env = dict(os.environ, PK_SIM_LOG=os.path.join(tempfile.gettempdir(), "pk_tally_test_sim.log"))
        return subprocess.run([sys.executable, "-B", SCRIPT] + list(args), capture_output=True, text=True, timeout=240, env=env)

    def test_selftest(self):
        result = self.run_script("--selftest")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("selftest OK", result.stdout)

    def test_tiny_run_produces_events_and_no_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "tally.json")
            result = self.run_script("--matches-per-size", "6", "--chunk", "3", "--label", "unittest_tiny", "--out", out)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(Path(out).read_text(encoding="utf-8"))
            self.assertEqual(data["matches"], 18)
            self.assertEqual(data["exceptions"], 0)
            for name in ("throw.total", "round.end", "unit.ko", "match.end.ko"):
                self.assertGreater(data["events"][name]["fired"], 0, name)
            # identical data compares clean
            same = self.run_script("--compare", out, "--baseline", out)
            self.assertEqual(same.returncode, 0, same.stdout)
        chunk_dir = HERE.parent / "logs_local" / "event_tally_backend" / "unittest_tiny"
        for path in chunk_dir.glob("*.json"):
            path.unlink()


if __name__ == "__main__":
    unittest.main(verbosity=2)
