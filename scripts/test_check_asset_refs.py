#!/usr/bin/env python3
"""Tests for the literal asset-reference checker."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parent / "release" / "check_asset_refs.py"


class CheckAssetRefsTests(unittest.TestCase):
    def make_tree(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "assets").mkdir()
        (root / "js").mkdir()
        (root / "css").mkdir()
        return temp

    def run_check(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--root", str(root)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_finds_page_js_and_css_references(self) -> None:
        with self.make_tree() as temp:
            root = Path(temp)
            (root / "assets/page.png").write_bytes(b"page")
            (root / "assets/script.png").write_bytes(b"script")
            (root / "assets/style.png").write_bytes(b"style")
            (root / "index.html").write_text('<img src="assets/page.png">', encoding="utf-8")
            (root / "js/game.js").write_text('const image = "assets/script.png";', encoding="utf-8")
            (root / "css/game.css").write_text('body { background: url("../assets/style.png"); }', encoding="utf-8")
            result = self.run_check(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("REF assets/page.png", result.stdout)
            self.assertIn("REF assets/script.png", result.stdout)
            self.assertIn("REF assets/style.png", result.stdout)
            self.assertIn("SUMMARY refs=3 missing=0", result.stdout)

    def test_directory_prefix_is_not_a_missing_file(self) -> None:
        with self.make_tree() as temp:
            root = Path(temp)
            (root / "assets/fonts").mkdir()
            (root / "index.html").write_text('"assets/fonts"', encoding="utf-8")
            result = self.run_check(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("REF assets/fonts", result.stdout)
            self.assertNotIn("MISSING assets/fonts", result.stdout)

    def test_existing_directory_prefix_prints_dir(self) -> None:
        with self.make_tree() as temp:
            root = Path(temp)
            (root / "assets/audio").mkdir()
            (root / "index.html").write_text('"assets/audio/"', encoding="utf-8")
            result = self.run_check(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("DIR assets/audio", result.stdout)
            self.assertIn("SUMMARY refs=0 missing=0", result.stdout)

    def test_missing_directory_prefix_does_not_fail(self) -> None:
        with self.make_tree() as temp:
            root = Path(temp)
            (root / "index.html").write_text('"assets/not-created"', encoding="utf-8")
            result = self.run_check(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("DIR_MISSING assets/not-created", result.stdout)

    def test_missing_file_returns_one(self) -> None:
        with self.make_tree() as temp:
            root = Path(temp)
            (root / "index.html").write_text('"assets/missing.png"', encoding="utf-8")
            result = self.run_check(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("MISSING assets/missing.png", result.stdout)

    def test_case_mismatch_is_reported_as_missing(self) -> None:
        with self.make_tree() as temp:
            root = Path(temp)
            (root / "assets/hero.png").write_bytes(b"hero")
            (root / "index.html").write_text('"assets/Hero.png"', encoding="utf-8")
            result = self.run_check(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("CASE assets/Hero.png", result.stdout)


if __name__ == "__main__":
    unittest.main()
