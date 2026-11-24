#!/usr/bin/env python3
"""Build a deterministic, manifest-controlled export tree."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import posixpath
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from check_asset_refs import scan as scan_asset_refs
except ImportError:  # pragma: no cover - supports module invocation
    from scripts.release.check_asset_refs import scan as scan_asset_refs

CREDIT_SENTENCE = "Credits: about 2,500 left, plenty (docs/KIRO_LEDGER.md has the history)."
TEXT_EXPORT_SUFFIXES = {".md", ".txt"}
KNOWN_LOCAL_PREFIXES = (
    "docs/", ".kiro/", ".claude/", "assets/", "scripts/", "js/", "css/",
    "shared/", "redteam/", "deploy/", "colab/", ".github/", "build/",
    "data/", "logs_local/", "./", "../",
)
KNOWN_ROOT_FILES_RE = re.compile(r"^(?:HANDOFF(?:_[0-9]+)?|STATE|CLAUDE|PLAY|README|LICENSE|JUDGES|CREDITS)\.md$")
MARKDOWN_LINK_TARGET_RE = re.compile(r"(\[[^\]]*\]\()([^)]+)(\))")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
BARE_LOCAL_REFERENCE_RE = re.compile(
    r"(?<![\w/])((?:\.{1,2}/)?(?:docs|\.kiro|assets|scripts|js|css|shared)/[A-Za-z0-9_./-]+|"
    r"(?:HANDOFF(?:_[0-9]+)?|STATE|README|LICENSE|JUDGES|CREDITS)\.md)(?::\d+(?:-\d+)?)?(?![A-Za-z0-9_./-]*[*?\[])"
)


class ExportError(Exception):
    """A bad manifest or unsafe export request."""


def load_manifest(path: Path) -> list[dict[str, Any]]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExportError(f"manifest error: {error}") from error
    rules = document.get("rules") if isinstance(document, dict) else None
    if not isinstance(rules, list) or not rules:
        raise ExportError("manifest error: rules must be a non-empty list")
    for number, rule in enumerate(rules, 1):
        if not isinstance(rule, dict) or not isinstance(rule.get("match"), str):
            raise ExportError(f"manifest error: rule {number} has no string match")
        if rule.get("decision") not in {"INCLUDE", "EXCLUDE", "TRANSFORM"}:
            raise ExportError(f"manifest error: rule {number} has an invalid decision")
        transform = rule.get("transform")
        if rule["decision"] == "TRANSFORM" and not (
            isinstance(transform, str)
            or (
                isinstance(transform, list)
                and transform
                and all(isinstance(name, str) for name in transform)
            )
        ):
            raise ExportError(f"manifest error: rule {number} has no transform name or transform list")
    last = rules[-1]
    if last.get("match") != "*" or last.get("decision") != "EXCLUDE":
        raise ExportError("manifest error: final rule must be the catch-all '*' EXCLUDE")
    return rules


def matches(pattern: str, relative: str) -> bool:
    """Match exact paths, directory prefixes, and case-sensitive fnmatch globs."""
    pattern = pattern.replace("\\", "/")
    if pattern.endswith("/"):
        return relative.startswith(pattern)
    if not any(token in pattern for token in "*?["):
        return relative == pattern or relative.startswith(pattern + "/")
    return fnmatch.fnmatchcase(relative, pattern)


def choose_rule(rules: list[dict[str, Any]], relative: str, references: set[str]) -> tuple[int, dict[str, Any]]:
    for index, rule in enumerate(rules):
        if not matches(rule["match"], relative):
            continue
        if rule.get("only_if") == "referenced" and relative not in references:
            continue
        return index, rule
    raise ExportError(f"manifest error: uncovered path {relative}")


def source_files(root: Path) -> tuple[list[str], int]:
    """Return regular files under root without .git or any symlink target."""
    files: list[str] = []
    skipped_symlinks = 0
    for current, dirs, names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        keep_dirs: list[str] = []
        for name in sorted(dirs):
            path = current_path / name
            if name == ".git":
                continue
            if path.is_symlink():
                skipped_symlinks += 1
                continue
            keep_dirs.append(name)
        dirs[:] = keep_dirs
        for name in sorted(names):
            path = current_path / name
            if path.is_symlink():
                skipped_symlinks += 1
                continue
            if not path.is_file():
                continue
            files.append(path.relative_to(root).as_posix())
    return files, skipped_symlinks


def local_reference_target(target: str) -> str:
    """Normalize a local reference target before export-membership checks."""
    parts = target.strip().strip("<>").split(maxsplit=1)
    if not parts:   # an empty link target such as "[x]()" or "<>" has nothing to check (found 2026-11-15: it crashed the export with IndexError)
        return ""
    target = parts[0]
    target = target.split("#", 1)[0].split("?", 1)[0]
    return re.sub(r":\d+(?:-\d+)?$", "", target)


def _published_dirs(published: set[str]) -> set[str]:
    dirs: set[str] = set()
    for item in published:
        cur = posixpath.dirname(item)
        while cur and cur != ".":
            dirs.add(cur)
            cur = posixpath.dirname(cur)
    return dirs


def glob_matches(pattern: str, path: str) -> bool:
    """Segment-wise glob match like pathlib.glob: `*` never crosses a slash, same rule as the privacy gate."""
    pattern_parts = pattern.rstrip("/").split("/")
    path_parts = path.split("/")
    return len(pattern_parts) == len(path_parts) and all(
        fnmatch.fnmatchcase(part, pat) for part, pat in zip(path_parts, pattern_parts)
    )


def is_unpublished_reference(
    source: str,
    target: str,
    published: set[str],
    published_dirs: set[str] | None = None,
    *,
    strict_prefix: bool = False,
) -> bool:
    """Return whether a local path-like reference has no export destination."""
    raw = target.strip()
    if strict_prefix and any(ch in raw for ch in (" ", "\t")):
        return False
    target = local_reference_target(target)
    if not target or target.startswith(("#", "//", "/")) or re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target):
        return False
    if any(ch in target for ch in ("*", "?", "[")):
        # RECHECK-2 (2026-11-25): a glob is kept when it matches something that is published, and rewritten when it matches nothing
        # (only for a known local prefix in backticks; a glob inside a link target or under an unknown prefix stays as written).
        if not (strict_prefix and target.startswith(KNOWN_LOCAL_PREFIXES)):
            return False
        dirs = published_dirs if published_dirs is not None else _published_dirs(published)
        return not any(glob_matches(target, item) for item in published | dirs)
    if strict_prefix:
        if not (target.startswith(KNOWN_LOCAL_PREFIXES) or KNOWN_ROOT_FILES_RE.match(target)):
            return False
    elif "/" not in target and Path(target).suffix.lower() not in TEXT_EXPORT_SUFFIXES:
        return False
    dirs = published_dirs if published_dirs is not None else _published_dirs(published)
    trimmed = target.rstrip("/")
    root_candidate = posixpath.normpath(trimmed)
    relative_candidate = posixpath.normpath(posixpath.join(posixpath.dirname(source), trimmed))
    if (
        root_candidate in published
        or relative_candidate in published
        or root_candidate in dirs
        or relative_candidate in dirs
    ):
        return False
    return True


def unpublish_refs(text: str, relative: str, published: set[str]) -> tuple[str, int]:
    """Replace excluded local links without changing source documentation or fenced code blocks."""
    count = 0
    published_dirs = _published_dirs(published)

    def replace_link(match: re.Match[str]) -> str:
        nonlocal count
        if is_unpublished_reference(relative, match.group(2), published, published_dirs):
            count += 1
            return f"{match.group(1)}(not published){match.group(3)}"
        return match.group(0)

    def replace_backtick(match: re.Match[str]) -> str:
        nonlocal count
        if is_unpublished_reference(relative, match.group(1), published, published_dirs, strict_prefix=True):
            count += 1
            return "`(not published)`"
        return match.group(0)

    def replace_bare_reference(match: re.Match[str]) -> str:
        nonlocal count
        if is_unpublished_reference(relative, match.group(1), published, published_dirs):
            count += 1
            return "(not published)"
        return match.group(0)

    def rewrite_chunk(chunk: str) -> str:
        chunk = MARKDOWN_LINK_TARGET_RE.sub(replace_link, chunk)
        chunk = BACKTICK_RE.sub(replace_backtick, chunk)
        return BARE_LOCAL_REFERENCE_RE.sub(replace_bare_reference, chunk)

    # Preserve fenced code blocks (e.g. JSON manifest examples in docs/visual_quality_plan.md).
    parts = re.split(r"(^```[^\n]*\n[\s\S]*?^```[ \t]*$)", text, flags=re.MULTILINE)
    out = [part if idx % 2 == 1 else rewrite_chunk(part) for idx, part in enumerate(parts)]
    return "".join(out), count


def apply_transform(name: str, relative: str, text: str, published: set[str]) -> tuple[str, str]:
    if name == "gitignore":
        lines = text.splitlines(keepends=True)
        if any(".kiro" in line for line in lines):
            raise ExportError("transform error: .gitignore mentions .kiro")
        blocked = {"*.log", "data/", "docs/audition/"}
        return "".join(line for line in lines if line.strip() not in blocked), "rewrote .gitignore without excluded-tree ignores"
    if name == "drop_credit_sentence":
        count = text.count(CREDIT_SENTENCE)
        if count != 1:
            raise ExportError("transform error: remaining-credits sentence did not match exactly once")
        return text.replace(CREDIT_SENTENCE, ""), "removed the remaining-credits sentence"
    if name == "unpublish_refs":
        if Path(relative).suffix.lower() not in TEXT_EXPORT_SUFFIXES:
            return text, "checked no non-text references"
        rendered, count = unpublish_refs(text, relative, published)
        return rendered, f"replaced {count} references to paths not in the export"
    raise ExportError(f"transform error: unknown transform {name!r} for {relative}")


def transform_content(names: str | list[str], relative: str, text: str, published: set[str]) -> tuple[str, str]:
    """Apply one or more manifest transforms in listed order."""
    transforms = [names] if isinstance(names, str) else names
    reasons: list[str] = []
    for name in transforms:
        text, reason = apply_transform(name, relative, text, published)
        reasons.append(reason)
    return text, "; ".join(reasons)


def destination_for(relative: str, transforms: str | list[str] | None) -> str:
    names = [transforms] if isinstance(transforms, str) else (transforms or [])
    if "route_log_txt" in names:
        return f"docs/kiro_evidence/raw/route_logs/{Path(relative).stem}.txt"
    return relative


def prepare(root: Path, rules: list[dict[str, Any]]) -> tuple[list[tuple[str, int, dict[str, Any]]], dict[int, list[str]], int]:
    files, skipped_symlinks = source_files(root)
    references = set(scan_asset_refs(root))
    selected: list[tuple[str, int, dict[str, Any]]] = []
    grouped: dict[int, list[str]] = defaultdict(list)
    for relative in files:
        index, rule = choose_rule(rules, relative, references)
        grouped[index].append(relative)
        if rule["decision"] != "EXCLUDE":
            selected.append((relative, index, rule))
    return selected, grouped, skipped_symlinks


def write_notes(output: Path, changes: list[tuple[str, str]]) -> None:
    notes = ["# Export notes", "", "This file is generated by scripts/release/export_tree.py.", ""]
    if changes:
        notes.extend(f"- `{path}`: {reason}." for path, reason in changes)
    else:
        notes.append("- No manifest transforms were applied.")
    notes.append("")
    target = output / "docs/kiro_evidence/EXPORT_NOTES.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(notes), encoding="utf-8")


def apply_export(root: Path, output: Path, selected: list[tuple[str, int, dict[str, Any]]]) -> None:
    if output.exists() and any(output.iterdir()):
        raise ExportError("apply error: --out must be empty")
    output.mkdir(parents=True, exist_ok=True)
    published = {
        destination_for(relative, rule.get("transform"))
        for relative, _index, rule in selected
    }
    published.update({"README.md", "JUDGES.md", "CREDITS.md", "docs/kiro_evidence/EXPORT_NOTES.md"})
    changes: list[tuple[str, str]] = []
    for relative, _index, rule in selected:
        transform = rule.get("transform")
        target_relative = destination_for(relative, transform)
        target = output / target_relative
        target.parent.mkdir(parents=True, exist_ok=True)
        transform_names = [transform] if isinstance(transform, str) else (transform or [])
        if transform_names == ["route_log_txt"]:
            shutil.copy2(root / relative, target)
            changes.append((target_relative, "renamed the Kiro route log from .log to .txt"))
        elif transform_names:
            try:
                text = (root / relative).read_text(encoding="utf-8")
            except UnicodeDecodeError as error:
                raise ExportError(f"transform error: {relative} is not UTF-8 text") from error
            rendered, reason = transform_content(transform, relative, text, published)
            target.write_text(rendered, encoding="utf-8")
            if rendered != text:
                changes.append((target_relative, reason))
        else:
            shutil.copy2(root / relative, target)
        src_mode = (root / relative).stat().st_mode
        os.chmod(target, 0o755 if (src_mode & 0o111) else 0o644)
    write_notes(output, changes)


def is_inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=".")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", default="../pk-release")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="print the plan without writing (default)")
    mode.add_argument("--apply", action="store_true", help="write the export tree")
    args = parser.parse_args(argv)
    root = Path(args.source).resolve()
    output = Path(args.out).resolve()
    try:
        rules = load_manifest(Path(args.manifest).resolve())
        selected, grouped, skipped_symlinks = prepare(root, rules)
        for index, rule in enumerate(rules):
            paths = grouped.get(index, [])
            size = sum((root / path).stat().st_size for path in paths)
            print(f"RULE {rule['match']} {rule['decision']} files={len(paths)} bytes={size}")
        print(f"SUMMARY selected={len(selected)} skipped_symlinks={skipped_symlinks}")
        if args.apply:
            if is_inside(output, root):
                raise ExportError("apply error: --out cannot be inside --source")
            apply_export(root, output, selected)
            print(f"APPLY {output}")
        else:
            print("DRY RUN: wrote nothing")
        return 0
    except ExportError as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
