#!/usr/bin/env python3
"""Tests for scripts/release/check_missing_mapped.py. Run: python3 -B scripts/test_check_missing_mapped.py"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "release" / "check_missing_mapped.py"


def run(root: Path, *extra: str) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-B", str(CHECKER), "--root", str(root), *extra], capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


class CheckMissingMapped(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs").mkdir()
        (self.root / "index.html").write_text(
            '<img src="assets/env/there.png"><img src="assets/env/gone.png"><img src="assets/fx/sprites/also_gone.png">\n',
            encoding="utf-8",
        )
        (self.root / "assets" / "env").mkdir(parents=True)
        (self.root / "assets" / "env" / "there.png").write_bytes(b"x")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def doc(self, text: str) -> None:
        (self.root / "docs" / "ingest_mapping_20261115.md").write_text(text, encoding="utf-8")

    def test_every_missing_path_mapped_passes(self) -> None:
        self.doc("| `assets/env/gone.png` | job a |\n| `assets/fx/sprites/also_gone.png` | job b |\n")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        self.assertIn("MAPPED assets/env/gone.png", out)
        self.assertIn("SUMMARY missing=2 unmapped=0", out)

    def test_unmapped_path_fails(self) -> None:
        self.doc("| `assets/env/gone.png` | job a |\n")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("UNMAPPED assets/fx/sprites/also_gone.png", out)
        self.assertIn("SUMMARY missing=2 unmapped=1", out)

    def test_existing_file_is_not_required_in_the_document(self) -> None:
        self.doc("`assets/env/gone.png` `assets/fx/sprites/also_gone.png`\n")
        code, out = run(self.root)
        self.assertNotIn("there.png", out)

    def test_missing_document_is_an_error(self) -> None:
        code, out = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("mapping document not found", out)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=0).result
    if result.wasSuccessful():
        print("OK")
        sys.exit(0)
    sys.exit(1)
