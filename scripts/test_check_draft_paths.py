#!/usr/bin/env python3
"""Tests for scripts/release/check_draft_paths.py. Run: python3 -B scripts/test_check_draft_paths.py"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "release" / "check_draft_paths.py"
MANIFEST = {
    "version": 1,
    "rules": [
        {"match": "docs/private/", "decision": "EXCLUDE", "reason": "test"},
        {"match": "docs/", "decision": "INCLUDE", "reason": "test"},
        {"match": "scripts/", "decision": "INCLUDE", "reason": "test"},
        {"match": ".kiro/", "decision": "INCLUDE", "reason": "test"},
        {"match": "*", "decision": "EXCLUDE", "reason": "catch-all"},
    ],
}


def run(root: Path, *files: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-B", str(CHECKER), "--root", str(root), "--manifest", str(root / "manifest.json"), *files],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


class CheckDraftPaths(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "manifest.json").write_text(json.dumps(MANIFEST), encoding="utf-8")
        for name in ("docs/a.md", "docs/private/secret.md", "scripts/tool.py", ".kiro/specs/x/tasks.md", "docs/release_drafts/JUDGES.md"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def draft(self, text: str) -> str:
        (self.root / "draft.md").write_text(text, encoding="utf-8")
        return "draft.md"

    def test_present_and_exported_paths_pass(self) -> None:
        code, out = run(self.root, self.draft("See `docs/a.md`, `scripts/tool.py:3-9` and `.kiro/specs/x/tasks.md`.\n"))
        self.assertEqual(code, 0, out)
        self.assertIn("SUMMARY checked=3 missing=0 excluded=0", out)

    def test_missing_path_fails_with_file_and_line(self) -> None:
        code, out = run(self.root, self.draft("ok\n`docs/nothing.md`\n"))
        self.assertEqual(code, 1)
        self.assertIn("MISSING docs/nothing.md [draft.md:2]", out)
        self.assertIn("missing=1", out)

    def test_excluded_path_fails(self) -> None:
        code, out = run(self.root, self.draft("`docs/private/secret.md`\n"))
        self.assertEqual(code, 1)
        self.assertIn("EXCLUDED docs/private/secret.md (rule: docs/private/)", out)

    def test_non_paths_are_ignored(self) -> None:
        text = "`python3 -B scripts/tool.py` `HOSTED_URL` `https://x.dev/docs/a.md` `docs/*.md` `a < b` `node`\n"
        code, out = run(self.root, self.draft(text))
        self.assertEqual(code, 0, out)
        self.assertIn("checked=0", out)

    def test_root_document_names_resolve_to_the_draft(self) -> None:
        code, out = run(self.root, self.draft("Read `JUDGES.md`.\n"))
        self.assertEqual(code, 0, out)

    def test_directory_without_trailing_slash_is_checked_as_a_directory(self) -> None:
        code, out = run(self.root, self.draft("`.kiro/specs/x` and `docs/private`\n"))
        self.assertEqual(code, 1)
        self.assertIn("OK .kiro/specs/x (1 of 1 files exported)", out)
        self.assertIn("EXCLUDED docs/private (every file in it)", out)

    def test_duplicate_path_is_counted_once(self) -> None:
        code, out = run(self.root, self.draft("`docs/a.md` and again `docs/a.md`\n"))
        self.assertIn("checked=1", out)

    def test_missing_draft_is_an_error(self) -> None:
        code, out = run(self.root, "nope.md")
        self.assertEqual(code, 2)
        self.assertIn("draft not found", out)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=0).result
    if result.wasSuccessful():
        print("OK")
        sys.exit(0)
    sys.exit(1)
