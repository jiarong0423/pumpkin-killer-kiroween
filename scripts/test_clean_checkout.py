#!/usr/bin/env python3
"""Tests for the isolated clean-checkout verifier."""

from __future__ import annotations

import shutil
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "release" / "clean_checkout.sh"
CHECKER = ROOT / "scripts" / "release" / "check_asset_refs.py"


class CleanCheckoutTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", 0))
        except OSError as error:
            self.skipTest(f"Local ports are unavailable: {error}")

    def make_project(self, root: Path) -> Path:
        project = root / "project"
        (project / "assets").mkdir(parents=True)
        (project / "scripts" / "release").mkdir(parents=True)
        (project / "assets" / "present.png").write_bytes(b"present")
        (project / "index.html").write_text(
            '<img src="assets/present.png"><img src="assets/missing.png">',
            encoding="utf-8",
        )
        (project / "scripts" / "test_toy.py").write_text(
            'print("toy test passed")\n', encoding="utf-8"
        )
        shutil.copy2(CHECKER, project / "scripts" / "release" / "check_asset_refs.py")
        return project

    def run_clean_checkout(self, project: Path, log: Path) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["bash", str(SCRIPT), "--src", str(project), "--worktree", "--log", str(log)],
            capture_output=True,
            text=True,
            check=False,
        )
        if "server 200: no" in log.read_text(encoding="utf-8"):
            self.skipTest("Clean checkout static server could not bind to a local port.")
        return result

    def test_worktree_mode_reports_missing_references(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = self.make_project(root)
            log = root / "clean_checkout.log"

            missing = self.run_clean_checkout(project, log)
            missing_log = log.read_text(encoding="utf-8")
            self.assertEqual(missing.returncode, 1, missing.stdout + missing.stderr + missing_log)
            self.assertIn("copy mode: worktree", missing_log)
            self.assertIn("missing references: 1", missing_log)
            self.assertIn("missing reference paths: assets/missing.png", missing_log)

            (project / "assets" / "missing.png").write_bytes(b"now present")
            passing = self.run_clean_checkout(project, log)
            passing_log = log.read_text(encoding="utf-8")
            self.assertEqual(passing.returncode, 0, passing.stdout + passing.stderr + passing_log)
            self.assertIn("missing references: 0", passing_log)


if __name__ == "__main__":
    unittest.main()
