#!/usr/bin/env python3
"""Tests for the release privacy gate. All sensitive-looking values are runtime seeds."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "release" / "privacy_gate.py"


def run_gate(tree: Path, terms: Path | None, *extra: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    if terms is None:
        environment.pop("PK_TERMS", None)
    else:
        environment["PK_TERMS"] = str(terms)
    return subprocess.run(
        [sys.executable, "-B", str(GATE), "--tree", str(tree), *extra],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        check=False,
    )


def png_text(payload: str) -> bytes:
    chunk = b"note\0" + payload.encode("utf-8")
    return b"\x89PNG\r\n\x1a\n" + len(chunk).to_bytes(4, "big") + b"tEXt" + chunk + b"\0\0\0\0"


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class PrivacyGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.tree = self.root / "tree"
        self.tree.mkdir()
        self.terms = self.root / "terms.txt"
        self.private_term = "private" + "-" + "marker"
        self.terms.write_text(self.private_term + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_all_checks_report_seeded_locations_without_values(self) -> None:
        email = "sample" + "@" + "example" + ".invalid"
        local_path = "/" + "Users" + "/" + "person" + "/work"
        access_key = "AK" + "IA" + "A" * 16
        assigned = "api" + "_key = '" + "q" * 16 + "'"
        metadata_email = "image" + "@" + "example" + ".invalid"

        (self.tree / "p1.txt").write_text(email + "\n", encoding="utf-8")
        (self.tree / "p2.txt").write_text(local_path + "\n", encoding="utf-8")
        (self.tree / "p3.txt").write_text(access_key + "\n", encoding="utf-8")
        (self.tree / "p4.txt").write_text(assigned + "\n", encoding="utf-8")
        (self.tree / "p5.txt").write_text("token label only\n", encoding="utf-8")
        (self.tree / ".env.local").write_text("ordinary\n", encoding="utf-8")
        (self.tree / "p7.txt").write_text(self.private_term + "\n", encoding="utf-8")
        (self.tree / "p8.txt").write_text("compute units\n", encoding="utf-8")
        (self.tree / "p9.txt").write_text("My" + "Drive\n", encoding="utf-8")
        (self.tree / "p10.txt").write_text(chr(0x4E2D) + "\n", encoding="utf-8")
        (self.tree / "p11.png").write_bytes(png_text(metadata_email))
        with (self.tree / "p12.bin").open("wb") as handle:
            handle.truncate(20 * 1024 * 1024 + 1)
        (self.tree / "p13.md").write_text("[missing](docs/no-such-file.md)\n", encoding="utf-8")
        (self.tree / "README.md").write_text("HOSTED" + "_URL\n", encoding="utf-8")

        result = run_gate(self.tree, self.terms)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, output)
        for check in range(1, 15):
            self.assertIn(f"P{check}", output)
        for value in (email, local_path, access_key, assigned, self.private_term, metadata_email):
            self.assertNotIn(value, output)
        for line in output.splitlines():
            if line.startswith(("BLOCK", "REVIEW")):
                self.assertRegex(line, r"^(BLOCK|REVIEW) P\d+ [^:]+:\d+$")

    def test_clean_tree_exits_zero(self) -> None:
        (self.tree / "clean.md").write_text("A plain English release note.\n", encoding="utf-8")
        result = run_gate(self.tree, self.terms)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")

    def test_font_license_email_allowlist_is_narrow(self) -> None:
        email = "font" + "@" + "example" + ".invalid"
        font_license = self.tree / "assets" / "fonts" / "OFL-Test.txt"
        font_license.parent.mkdir(parents=True)
        font_license.write_text(email + "\n", encoding="utf-8")
        (self.tree / "notice.txt").write_text(email + "\n", encoding="utf-8")

        result = run_gate(self.tree, self.terms)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, output)
        self.assertNotIn("BLOCK P1 assets/fonts/OFL-Test.txt:1", output)
        self.assertIn("BLOCK P1 notice.txt:1", output)
        self.assertNotIn(email, output)

    def test_font_license_p1_exception_uses_real_subprocess_tree(self) -> None:
        email = "font" + "@" + "example" + ".invalid"
        ofl = self.tree / "assets" / "fonts" / "OFL-Test.txt"
        docs_file = self.tree / "docs" / "x.md"
        clean_file = self.tree / "clean.txt"
        ofl.parent.mkdir(parents=True)
        ofl.write_text(email + "\n", encoding="utf-8")
        clean_file.write_text("ordinary clean file\n", encoding="utf-8")

        allowed = run_gate(self.tree, self.terms, "--check", "all")
        self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)
        self.assertNotIn("P1 assets/fonts/OFL-Test.txt", allowed.stdout + allowed.stderr)
        self.assertNotIn("clean.txt:", allowed.stdout + allowed.stderr)
        self.assertNotIn("Traceback", allowed.stderr)

        docs_file.parent.mkdir()
        docs_file.write_text(email + "\n", encoding="utf-8")
        blocked = run_gate(self.tree, self.terms, "--check", "all")
        output = blocked.stdout + blocked.stderr
        self.assertEqual(blocked.returncode, 1, output)
        self.assertIn("BLOCK P1 docs/x.md:1", output)
        self.assertNotIn("P1 assets/fonts/OFL-Test.txt", output)
        self.assertNotIn("clean.txt:", output)
        self.assertNotIn("Traceback", blocked.stderr)

    def test_non_ofl_font_file_does_not_crash_gate(self) -> None:
        font_file = self.tree / "assets" / "fonts" / "NOTICE.txt"
        font_file.parent.mkdir(parents=True)
        font_file.write_text("ordinary clean file\n", encoding="utf-8")

        result = run_gate(self.tree, self.terms, "--check", "all")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_license_copyright_p7_exception_is_narrow(self) -> None:
        (self.tree / "LICENSE").write_text(
            f"MIT License\n\nCopyright (c) 2026 {self.private_term}\n", encoding="utf-8"
        )
        docs_file = self.tree / "docs" / "x.md"
        docs_file.parent.mkdir()
        docs_file.write_text(self.private_term + "\n", encoding="utf-8")

        result = run_gate(self.tree, self.terms)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, output)
        self.assertNotIn("BLOCK P7 LICENSE:3", output)
        self.assertIn("BLOCK P7 docs/x.md:1", output)
        self.assertNotIn(self.private_term, output)

    def test_missing_and_empty_terms_fail(self) -> None:
        missing = run_gate(self.tree, None)
        self.assertEqual(missing.returncode, 1)
        self.assertIn("PK_TERMS", missing.stdout)

        empty = self.root / "empty-terms.txt"
        empty.write_text("\n", encoding="utf-8")
        empty_result = run_gate(self.tree, empty)
        self.assertEqual(empty_result.returncode, 1)
        self.assertIn("PK_TERMS", empty_result.stdout)

    @unittest.skipUnless(shutil.which("git"), "git is required for the mandated temporary history test")
    def test_history_checks_report_p1_to_p7_p15_and_p16_without_values(self) -> None:
        repo = self.root / "history"
        repo.mkdir()
        git(repo, "init")
        for number in range(73):
            path = repo / ".kiro" / f"proof-{number}.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("safe\n", encoding="utf-8")
        (repo / "safe.txt").write_text("safe\n", encoding="utf-8")
        git(repo, "add", ".")
        name = "release" + " bot"
        email = "123" + "+" + "release" + "@users.noreply.github.com"
        git(repo, "-c", f"user.name={name}", "-c", f"user.email={email}", "commit", "-m", "initial")

        private_email = "history" + "@" + "example" + ".invalid"
        (repo / "leak.txt").write_text(private_email + "\n", encoding="utf-8")
        (repo / ".env.history").write_text("safe\n", encoding="utf-8")
        (repo / "docs" / "audition").mkdir(parents=True)
        (repo / "docs" / "audition" / "leak.txt").write_text("safe\n", encoding="utf-8")
        git(repo, "add", ".")
        trailer = "Co" + "-" + "authored" + "-" + "by: test"
        git(repo, "-c", f"user.name={name}", "-c", f"user.email={email}", "commit", "-m", trailer)

        result = run_gate(repo, self.terms, "--history", str(repo))
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, output)
        for check in ("P1", "P6", "P15", "P16"):
            self.assertIn(check, output)
        self.assertNotIn(private_email, output)
        for line in output.splitlines():
            if line.startswith("BLOCK"):
                self.assertRegex(line, r"^BLOCK P[\d-]+(?:/P\d+)? [^:]+:.+$")


class LocalTargetTests(unittest.TestCase):
    def test_empty_and_line_suffixed_targets(self):
        import tempfile
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent / "release"))
        import privacy_gate as gate
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            (tree / "docs").mkdir()
            (tree / "docs" / "a.md").write_text("x\n")
            source = tree / "docs" / "b.md"
            self.assertTrue(gate.local_target_exists(tree, source, ""))        # empty link: nothing to check, no crash
            self.assertTrue(gate.local_target_exists(tree, source, "docs/a.md:12"))   # path:line refers to the file
            self.assertFalse(gate.local_target_exists(tree, source, "docs/missing.md:3"))
            (tree / "docs" / "kiro_task_1.md").write_text("x\n")
            self.assertTrue(gate.local_target_exists(tree, source, "docs/kiro_task_*.md"))      # a glob that matches a file is not dangling
            self.assertFalse(gate.local_target_exists(tree, source, "docs/nothing_*.md"))        # a glob that matches nothing still is


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PrivacyGateTests)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(LocalTargetTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("OK")
