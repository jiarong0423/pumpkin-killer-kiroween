#!/usr/bin/env python3
"""Check that every repository path named in backticks in Markdown drafts exists and is export-visible.

A path is export-visible when it exists in the source tree and the export manifest (the same rules as
scripts/release/export_tree.py) does not EXCLUDE it. A path that exists locally but is excluded would be a dead
link for a judge reading the public repository.

Usage: python3 -B scripts/release/check_draft_paths.py [--root DIR] [--manifest FILE] FILE [FILE ...]
Output per path: OK, MISSING or EXCLUDED, then a final SUMMARY line. Exit 1 if anything is missing or excluded.
README.md, JUDGES.md, CREDITS.md at the top level mean the drafts in docs/release_drafts/ that the main line
copies to the release root, so they count as present when that draft exists.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import export_tree
except ImportError:  # pragma: no cover - module invocation
    from scripts.release import export_tree  # type: ignore

BACKTICK = re.compile(r"`([^`\n]+)`")
TOP_FOLDERS = ("docs", ".kiro", "assets", "scripts", "js", "css", "shared", "colab", "deploy", "build")
ROOT_FILES = {"README.md", "JUDGES.md", "CREDITS.md", "LICENSE", "index.html", "STATE.md", "HANDOFF.md"}
DRAFT_ROOT_NAMES = {"README.md", "JUDGES.md", "CREDITS.md"}
LINE_SUFFIX = re.compile(r":\d+(?:-\d+)?$")


def looks_like_path(token: str) -> bool:
    token = token.strip()
    if not token or any(c in token for c in " *<>{}$|") or "://" in token:
        return False
    token = LINE_SUFFIX.sub("", token)
    if token in ROOT_FILES:
        return True
    first = token.split("/", 1)[0]
    return "/" in token and first in TOP_FOLDERS


def collect(text: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), 1):
        for match in BACKTICK.finditer(line):
            token = match.group(1).strip()
            if looks_like_path(token):
                found.append((number, LINE_SUFFIX.sub("", token)))
    return found


def check_file(draft: Path, root: Path, rules, references, files_set: set[str]) -> list[tuple[str, str, str, int]]:
    results = []
    text = draft.read_text(encoding="utf-8")
    seen: set[str] = set()
    for number, token in collect(text):
        if token in seen:
            continue
        seen.add(token)
        relative = token
        if token in DRAFT_ROOT_NAMES and (root / "docs" / "release_drafts" / token).is_file():
            results.append(("OK", token, "root copy of docs/release_drafts/" + token, number))
            continue
        if token.endswith("/") or (root / token).is_dir():
            token_dir = token if token.endswith("/") else token + "/"
            members = [f for f in files_set if f.startswith(token_dir)]
            if not (root / token).is_dir() or not members:
                results.append(("MISSING", token, "", number))
                continue
            kept = [f for f in members if rules[export_tree.choose_rule(rules, f, references)[0]]["decision"] != "EXCLUDE"]
            if kept:
                results.append(("OK", token, f"{len(kept)} of {len(members)} files exported", number))
            else:
                results.append(("EXCLUDED", token, "every file in it", number))
            continue
        if relative not in files_set:
            results.append(("MISSING", token, "", number))
            continue
        index, rule = export_tree.choose_rule(rules, relative, references)
        if rule["decision"] == "EXCLUDE":
            results.append(("EXCLUDED", token, "rule: " + rule["match"], number))
        else:
            results.append(("OK", token, "", number))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    parser.add_argument("--manifest", default=None, help="export manifest (default: scripts/release/export_manifest.json under root)")
    parser.add_argument("files", nargs="+", help="Markdown files to check")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    manifest = Path(args.manifest) if args.manifest else root / "scripts" / "release" / "export_manifest.json"
    try:
        rules = export_tree.load_manifest(manifest)
    except export_tree.ExportError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 2
    files, _ = export_tree.source_files(root)
    files_set = set(files)
    references = set(export_tree.scan_asset_refs(root))
    checked = missing = excluded = 0
    for name in args.files:
        draft = Path(name)
        if not draft.is_absolute():
            draft = root / name
        if not draft.is_file():
            print(f"ERROR draft not found: {name}", file=sys.stderr)
            return 2
        print(f"FILE {name}")
        for status, token, note, number in check_file(draft, root, rules, references, files_set):
            checked += 1
            if status == "MISSING":
                missing += 1
            elif status == "EXCLUDED":
                excluded += 1
            suffix = f" ({note})" if note else ""
            print(f"{status} {token}{suffix} [{name}:{number}]" if status != "OK" else f"OK {token}{suffix}")
    print(f"SUMMARY checked={checked} missing={missing} excluded={excluded}")
    return 1 if missing or excluded else 0


if __name__ == "__main__":
    sys.exit(main())
