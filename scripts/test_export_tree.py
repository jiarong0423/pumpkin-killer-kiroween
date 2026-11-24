#!/usr/bin/env python3
"""Tests for the manifest-controlled release export."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parent / "release" / "export_tree.py"
sys.path.insert(0, str(SCRIPT.parent))
from export_tree import choose_rule, load_manifest, local_reference_target, matches, source_files, unpublish_refs

MANIFEST = SCRIPT.parent / "export_manifest.json"
REPO_ROOT = Path(__file__).resolve().parents[1]
CREDIT_SENTENCE = "Credits: about 2,500 left, plenty (docs/KIRO_LEDGER.md has the history)."


class ToyTree:
    def __init__(self, temp: tempfile.TemporaryDirectory[str], root: Path, manifest: Path) -> None:
        self.temp = temp
        self.root = root
        self.manifest = manifest

    def __enter__(self) -> tuple[str, Path, Path]:
        return self.temp.name, self.root, self.manifest

    def __exit__(self, *_args: object) -> None:
        self.temp.cleanup()


class ExportTreeTests(unittest.TestCase):
    def test_empty_link_target_does_not_crash(self):
        # 2026-11-15: "[x]()" or "<>" raised IndexError and stopped the whole export
        for empty in ("", "  ", "<>", "< >"):
            self.assertEqual(local_reference_target(empty), "")
        self.assertEqual(local_reference_target("docs/a.md:12#x"), "docs/a.md")

    def make_tree(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name) / "source"
        root.mkdir()
        (root / "assets").mkdir()
        (root / "docs").mkdir()
        (root / ".kiro/steering").mkdir(parents=True)
        (root / ".kiro/specs/x").mkdir(parents=True)
        (root / "assets/used.png").write_bytes(b"used")
        (root / "assets/unused.png").write_bytes(b"unused")
        (root / "index.html").write_text('<img src="assets/used.png">', encoding="utf-8")
        (root / ".gitignore").write_text("*.log\ndata/\nkeep-me\n", encoding="utf-8")
        (root / ".kiro/steering/kiro_assignment.md").write_text(
            "Read HANDOFF.md and docs/owner_feedback_log.md.", encoding="utf-8"
        )
        (root / ".kiro/specs/x/tasks.md").write_text(
            "`docs/hidden-code.md` [hidden](docs/hidden-link.md) [kept](../../../docs/published.md)",
            encoding="utf-8",
        )
        (root / "docs/published.md").write_text("published", encoding="utf-8")
        (root / "docs/kiro_queue_20261110.md").write_text(
            f"Before. {CREDIT_SENTENCE} After. `docs/queue-hidden.md`", encoding="utf-8"
        )
        (root / "docs/links.md").write_text(
            "[kept](../index.html) [missing](missing.md) `docs/hidden.md` `docs/links.md`",
            encoding="utf-8",
        )
        (root / "kiro_route_kiro_task_8.log").write_text("proof", encoding="utf-8")
        manifest = root / "manifest.json"
        manifest.write_text(json.dumps({"rules": self.rules()}), encoding="utf-8")
        return ToyTree(temp, root, manifest)

    @staticmethod
    def rules() -> list[dict[str, str]]:
        return [
            {"match": ".gitignore", "decision": "TRANSFORM", "transform": "gitignore"},
            {"match": ".kiro/steering/kiro_assignment.md", "decision": "TRANSFORM", "transform": "unpublish_refs"},
            {"match": ".kiro/specs/", "decision": "TRANSFORM", "transform": "unpublish_refs"},
            {"match": ".kiro/", "decision": "INCLUDE"},
            {"match": "docs/kiro_queue_20261110.md", "decision": "TRANSFORM", "transform": ["drop_credit_sentence", "unpublish_refs"]},
            {"match": "docs/*.md", "decision": "TRANSFORM", "transform": "unpublish_refs"},
            {"match": "docs/", "decision": "INCLUDE"},
            {"match": "kiro_route_kiro_task_*.log", "decision": "TRANSFORM", "transform": "route_log_txt"},
            {"match": "index.html", "decision": "INCLUDE"},
            {"match": "assets/", "decision": "INCLUDE", "only_if": "referenced"},
            {"match": "assets/", "decision": "EXCLUDE"},
            {"match": "manifest.json", "decision": "EXCLUDE"},
            {"match": "*", "decision": "EXCLUDE"},
        ]

    def run_export(self, root: Path, manifest: Path, out: Path, *mode: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--source", str(root), "--manifest", str(manifest), "--out", str(out), *mode],
            capture_output=True,
            text=True,
            check=False,
        )

    @staticmethod
    def _specificity(pattern: str) -> int:
        literal = re.sub(r"\[[^]]*\]|[*?]", "", pattern)
        return len(literal)

    @staticmethod
    def _rule_probes(pattern: str) -> set[str]:
        probe = re.sub(r"\[[^]]*\]", "x", pattern)
        probe = probe.replace("?", "x").replace("*", "probe")
        if probe.endswith("/"):
            probe += "item"
        return {
            probe,
            f"{probe}.md",
            f"{probe}.json",
            f"{probe}.txt",
            f"{probe}.png",
            f"{probe}.log",
        }

    def test_real_manifest_keeps_private_docs_excluded(self) -> None:
        rules = load_manifest(MANIFEST)
        expected = [
            ("docs/owner_feedback_log.md", "EXCLUDE", None),
            ("docs/GAP_QUEUE_20261115.md", "EXCLUDE", None),
            ("docs/agent_memory_paths.md", "EXCLUDE", None),
            ("docs/gemini_asset_prompt.txt", "EXCLUDE", None),
            ("docs/vfx_reference_hearthstone.md", "EXCLUDE", None),
            ("docs/briefing_for_kiro_20261110.md", "EXCLUDE", None),
            ("docs/official/COMPLIANCE_CHECK_20261110.md", "EXCLUDE", None),
            ("docs/handoff/x.md", "EXCLUDE", None),
            ("docs/ref/x.png", "EXCLUDE", None),
            ("HANDOFF.md", "EXCLUDE", None),
            ("docs/game_mode.md", "TRANSFORM", "unpublish_refs"),
            ("docs/anything.md", "TRANSFORM", "unpublish_refs"),
            (".kiro/specs/anything/tasks.md", "TRANSFORM", "unpublish_refs"),
            (".kiro/steering/kiro_assignment.md", "TRANSFORM", "unpublish_refs"),
            (".kiro/steering/product.md", "TRANSFORM", "unpublish_refs"),
            (".kiro/steering/tech.md", "TRANSFORM", "unpublish_refs"),
            (".claude/skills/kiro-record/SKILL.md", "EXCLUDE", None),
            ("docs/release_drafts/BLOG_AND_POSTS_DRAFT.md", "EXCLUDE", None),
            ("relay-config.js", "INCLUDE", None),
            ("docs/fonts_sample.html", "INCLUDE", None),
            ("docs/audio_event_map.json", "INCLUDE", None),
            ("docs/kiro_evidence/raw/README.md", "INCLUDE", None),
            ("deploy/Dockerfile.coolify", "INCLUDE", None),
            ("deploy/entrypoint.sh", "INCLUDE", None),
            ("assets/audio/music/alt_haunted_track.ogg", "EXCLUDE", None),
            ("assets/audio/music/alt_music_box_waltz.ogg", "EXCLUDE", None),
        ]
        for path, decision, transform in expected:
            _index, rule = choose_rule(rules, path, set())
            self.assertEqual(rule["decision"], decision, path)
            self.assertEqual(rule.get("transform"), transform, path)

        source_paths, _skipped_symlinks = source_files(REPO_ROOT)
        candidates = set(source_paths)
        candidates.update(path for path, _decision, _transform in expected)
        for rule in rules:
            candidates.update(self._rule_probes(rule["match"]))

        offenders: list[str] = []
        for excluded_index, excluded in enumerate(rules):
            if excluded["decision"] != "EXCLUDE":
                continue
            for earlier_index, earlier in enumerate(rules[:excluded_index]):
                if earlier["decision"] == "EXCLUDE":
                    continue
                if self._specificity(earlier["match"]) >= self._specificity(excluded["match"]):
                    continue
                overlapping_path = next(
                    (
                        path
                        for path in sorted(candidates)
                        if matches(earlier["match"], path) and matches(excluded["match"], path)
                    ),
                    None,
                )
                if overlapping_path:
                    offenders.append(
                        f"rules {earlier_index + 1} ({earlier['match']!r}, {earlier['decision']}) "
                        f"and {excluded_index + 1} ({excluded['match']!r}, EXCLUDE) "
                        f"both match {overlapping_path!r}"
                    )
        self.assertFalse(offenders, "Manifest ordering conflicts:\n" + "\n".join(offenders))

    def test_unpublish_refs_handles_line_suffixes_and_bare_table_paths(self) -> None:
        text = (
            "[linked](docs/linked-hidden.md:8) `docs/code-hidden.md:9` | docs/table-hidden.md:10 | "
            "`tools/list` `prompts/*.md` `js/` `.kiro/specs/`"
        )
        rendered, count = unpublish_refs(
            text,
            "docs/source.md",
            {"docs/source.md", "js/app.js", ".kiro/specs/foo/tasks.md"},
        )
        self.assertEqual(count, 3)
        self.assertNotIn("docs/linked-hidden.md", rendered)
        self.assertNotIn("docs/code-hidden.md", rendered)
        self.assertNotIn("docs/table-hidden.md", rendered)
        self.assertIn("`tools/list`", rendered)
        self.assertIn("`prompts/*.md`", rendered)
        self.assertIn("`js/`", rendered)
        self.assertIn("`.kiro/specs/`", rendered)
        self.assertEqual(rendered.count("(not published)"), 3)

    def test_unpublish_refs_rewrites_only_globs_that_match_nothing(self) -> None:
        # RECHECK-2 (2026-11-25): a glob under a known local prefix that matches no published file would be a dangling path in the public tree.
        text = "`docs/kept_*.md` `docs/gone_*.md` `docs/a/*` `prompts/*.md`"
        published = {"docs/source.md", "docs/kept_one.md", "docs/a/x.md"}
        rendered, count = unpublish_refs(text, "docs/source.md", published)
        self.assertEqual(count, 1)
        self.assertIn("`docs/kept_*.md`", rendered)
        self.assertNotIn("docs/gone_*.md", rendered)
        self.assertIn("`docs/a/*`", rendered)
        self.assertIn("`prompts/*.md`", rendered)

    def test_dry_run_writes_nothing(self) -> None:
        with self.make_tree() as (temp, root, manifest):
            output = Path(temp) / "output"
            result = self.run_export(root, manifest, output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(output.exists())
            self.assertIn("DRY RUN: wrote nothing", result.stdout)

    def test_apply_copies_and_applies_all_transforms(self) -> None:
        with self.make_tree() as (temp, root, manifest):
            output = Path(temp) / "output"
            result = self.run_export(root, manifest, output, "--apply")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((output / "assets/used.png").read_bytes(), b"used")
            self.assertFalse((output / "assets/unused.png").exists())
            self.assertEqual((output / ".gitignore").read_text(encoding="utf-8"), "keep-me\n")
            steering = (output / ".kiro/steering/kiro_assignment.md").read_text(encoding="utf-8")
            self.assertNotIn("HANDOFF.md", steering)
            self.assertEqual(steering.count("(not published)"), 2)
            spec_tasks = (output / ".kiro/specs/x/tasks.md").read_text(encoding="utf-8")
            self.assertNotIn("docs/hidden-code.md", spec_tasks)
            self.assertNotIn("docs/hidden-link.md", spec_tasks)
            self.assertEqual(spec_tasks.count("(not published)"), 2)
            self.assertIn("[kept](../../../docs/published.md)", spec_tasks)
            queue = (output / "docs/kiro_queue_20261110.md").read_text(encoding="utf-8")
            self.assertNotIn(CREDIT_SENTENCE, queue)
            self.assertIn("(not published)", queue)
            self.assertNotIn("docs/queue-hidden.md", queue)
            links = (output / "docs/links.md").read_text(encoding="utf-8")
            self.assertIn("[kept](../index.html)", links)
            self.assertEqual(links.count("(not published)"), 2)
            self.assertNotIn("docs/hidden.md", links)
            self.assertTrue((output / "docs/kiro_evidence/raw/route_logs/kiro_route_kiro_task_8.txt").is_file())
            notes = (output / "docs/kiro_evidence/EXPORT_NOTES.md").read_text(encoding="utf-8")
            self.assertIn("remaining-credits sentence", notes)
            self.assertIn("docs/links.md", notes)
            self.assertIn("replaced 2 references", notes)

    def test_apply_refuses_nonempty_output(self) -> None:
        with self.make_tree() as (temp, root, manifest):
            output = Path(temp) / "output"
            output.mkdir()
            (output / "keep.txt").write_text("keep", encoding="utf-8")
            result = self.run_export(root, manifest, output, "--apply")
            self.assertEqual(result.returncode, 2)
            self.assertIn("--out must be empty", result.stderr)
            self.assertEqual((output / "keep.txt").read_text(encoding="utf-8"), "keep")

    def test_apply_refuses_output_inside_source(self) -> None:
        with self.make_tree() as (_temp, root, manifest):
            output = root / "nested-output"
            result = self.run_export(root, manifest, output, "--apply")
            self.assertEqual(result.returncode, 2)
            self.assertIn("cannot be inside --source", result.stderr)
            self.assertFalse(output.exists())

    def test_manifest_without_catch_all_is_an_error(self) -> None:
        with self.make_tree() as (temp, root, manifest):
            document = json.loads(manifest.read_text(encoding="utf-8"))
            document["rules"].pop()
            manifest.write_text(json.dumps(document), encoding="utf-8")
            result = self.run_export(root, manifest, Path(temp) / "output")
            self.assertEqual(result.returncode, 2)
            self.assertIn("final rule must be the catch-all", result.stderr)


if __name__ == "__main__":
    unittest.main()
