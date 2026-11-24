#!/usr/bin/env python3
"""Tests for the deterministic local-play package builder."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path


SCRIPT = Path(__file__).with_name("make_download_package.py")
SPEC = importlib.util.spec_from_file_location("make_download_package", SCRIPT)
assert SPEC and SPEC.loader
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


class DownloadPackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "tree"
        self.root.mkdir()
        (self.root / "index.html").write_text("<title>Pumpkin Killer</title>\n", encoding="utf-8")
        (self.root / "private-notes.md").write_text("do not publish\n", encoding="utf-8")
        (self.root / "PLAY.md").write_text("Play locally.\n", encoding="utf-8")
        (self.root / "requirements.txt").write_text("websockets>=15\n", encoding="utf-8")
        (self.root / "docs").mkdir()
        (self.root / "docs/EXPORT_EXCLUDE_20261116.md").write_text(
            "| `private-notes.md` | test exclusion |\n", encoding="utf-8"
        )
        package_dir = self.root / "deploy/package"
        package_dir.mkdir(parents=True)
        for name in ("start_game.sh", "start_game.bat", "start_agent.sh", "start_agent.bat"):
            (package_dir / name).write_text(f"{name}\n", encoding="utf-8")
        self.manifest = self.root / "manifest.json"
        self.write_manifest([{"match": "index.html", "decision": "INCLUDE"}])
        self.terms = self.root / "terms.txt"
        self.terms.write_text("unlikely-owner-term\n", encoding="utf-8")
        self.old_terms = os.environ.get("PK_TERMS")
        os.environ["PK_TERMS"] = str(self.terms)

    def tearDown(self) -> None:
        if self.old_terms is None:
            os.environ.pop("PK_TERMS", None)
        else:
            os.environ["PK_TERMS"] = self.old_terms
        self.temp.cleanup()

    def write_manifest(self, rules: list[dict[str, str]]) -> None:
        document = {"rules": rules + [{"match": "*", "decision": "EXCLUDE"}]}
        self.manifest.write_text(json.dumps(document), encoding="utf-8")

    def arguments(self, output: Path, *extra: str) -> list[str]:
        return [
            "--source", str(self.root), "--manifest", str(self.manifest), "--kit-root", str(self.root),
            "--out", str(output), *extra,
        ]

    def test_dry_run_writes_nothing_without_terms_or_gate(self) -> None:
        output = self.root / "package.zip"
        os.environ.pop("PK_TERMS", None)
        with redirect_stdout(io.StringIO()) as captured:
            status = package.main(self.arguments(output, "--dry-run"))
        self.assertEqual(status, 0)
        self.assertIn("FILE requirements.txt", captured.getvalue())
        self.assertIn("privacy gate was not run", captured.getvalue())
        self.assertFalse(output.exists())

    def test_zip_lists_expected_files_and_excludes_documented_private_note(self) -> None:
        self.write_manifest([
            {"match": "index.html", "decision": "INCLUDE"},
            {"match": "private-notes.md", "decision": "INCLUDE"},
        ])
        output = self.root / "package.zip"
        with redirect_stdout(io.StringIO()):
            status = package.main(self.arguments(output))
        self.assertEqual(status, 0)
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.namelist(), [
                "PLAY.md", "SHA256SUMS.txt", "docs/kiro_evidence/EXPORT_NOTES.md", "index.html",
                "requirements.txt", "start_agent.bat", "start_agent.sh", "start_game.bat", "start_game.sh",
            ])
            self.assertNotIn("private-notes.md", archive.namelist())

    def test_gate_blocks_private_marker(self) -> None:
        (self.root / "marker.txt").write_text("AK" + "IA1234567890ABCDEF\n", encoding="utf-8")
        self.write_manifest([
            {"match": "index.html", "decision": "INCLUDE"},
            {"match": "marker.txt", "decision": "INCLUDE"},
        ])
        output = self.root / "blocked.zip"
        with redirect_stdout(io.StringIO()):
            status = package.main(self.arguments(output))
        self.assertEqual(status, 2)
        self.assertFalse(output.exists())

    def test_two_runs_have_identical_sha256(self) -> None:
        first = self.root / "first.zip"
        second = self.root / "second.zip"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(package.main(self.arguments(first)), 0)
            self.assertEqual(package.main(self.arguments(second)), 0)
        digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(digest(first), digest(second))

    def test_checksum_manifest_matches_each_payload_file(self) -> None:
        output = self.root / "package.zip"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(package.main(self.arguments(output)), 0)
        with zipfile.ZipFile(output) as archive:
            rows = archive.read("SHA256SUMS.txt").decode("utf-8").splitlines()
            actual = {name: digest for digest, name in (row.split("  ", 1) for row in rows)}
            names = set(archive.namelist()) - {"SHA256SUMS.txt"}
            self.assertEqual(set(actual), names)
            for name, digest in actual.items():
                self.assertEqual(digest, hashlib.sha256(archive.read(name)).hexdigest())


if __name__ == "__main__":
    unittest.main()
