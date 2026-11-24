#!/usr/bin/env python3
"""List literal asset references used by the playable page."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Iterable

ASSET_LITERAL = re.compile(r"assets/[A-Za-z0-9_./-]+")
CSS_URL = re.compile(r"url\(\s*(['\"]?)([^'\")]+)\1\s*\)", re.IGNORECASE)


def _source_files(root: Path) -> Iterable[Path]:
    page = root / "index.html"
    if page.is_file():
        yield page
    for folder, pattern in ((root / "js", "*.js"), (root / "css", "*.css")):
        if folder.is_dir():
            yield from sorted(folder.glob(pattern))


def _clean_path(path: str) -> str:
    return path.split("?", 1)[0].split("#", 1)[0].replace("\\", "/")


def _normalise(path: str) -> str:
    return PurePosixPath(_clean_path(path)).as_posix()


def _is_file_reference(path: str) -> bool:
    clean = _clean_path(path)
    return not clean.endswith("/") and bool(re.search(r"\.[A-Za-z0-9]+$", clean))


def _scan(root: str | Path) -> tuple[list[str], list[str]]:
    """Return literal file references and directory prefixes in source order."""
    root = Path(root).resolve()
    files: list[str] = []
    directories: list[str] = []
    seen: set[str] = set()

    def add(candidate: str) -> None:
        is_file = _is_file_reference(candidate)
        candidate = _normalise(candidate)
        if candidate != "assets" and not candidate.startswith("assets/"):
            return
        if candidate in seen:
            return
        seen.add(candidate)
        (files if is_file else directories).append(candidate)

    for source in _source_files(root):
        text = source.read_text(encoding="utf-8", errors="replace")
        for match in ASSET_LITERAL.finditer(text):
            add(match.group(0))
        if source.suffix == ".css":
            for match in CSS_URL.finditer(text):
                value = match.group(2).strip()
                if value.startswith(("data:", "http:", "https:", "#")):
                    continue
                candidate = (source.parent / value).resolve()
                try:
                    add(candidate.relative_to(root).as_posix())
                except ValueError:
                    continue
    return files, directories


def scan(root: str | Path) -> list[str]:
    """Return unique literal asset file paths (plus existing .webp companions) in deterministic source order."""
    root_path = Path(root).resolve()
    files = _scan(root_path)[0]
    seen = set(files)
    expanded = list(files)
    for rel in files:
        if rel.lower().endswith(".png"):
            webp = rel[:-4] + ".webp"
            if webp not in seen and (root_path / webp).is_file():
                seen.add(webp)
                expanded.append(webp)
    return expanded


def _failure_kind(root: Path, relative: str) -> str | None:
    """Check each component so macOS's case-insensitive filesystem is caught."""
    current = root
    for part in PurePosixPath(relative).parts:
        if not current.is_dir():
            return "MISSING"
        names = {entry.name for entry in current.iterdir()}
        if part not in names:
            return "CASE" if part.casefold() in {name.casefold() for name in names} else "MISSING"
        current /= part
    return None if current.is_file() else "MISSING"


def _directory_kind(root: Path, relative: str) -> str:
    """Classify a directory prefix without making it a checker failure."""
    current = root
    for part in PurePosixPath(relative).parts:
        if not current.is_dir():
            return "DIR_MISSING"
        names = {entry.name for entry in current.iterdir()}
        if part not in names:
            return "DIR_MISSING"
        current /= part
    return "DIR" if current.is_dir() else "DIR_MISSING"


def missing(root: str | Path) -> list[tuple[str, str]]:
    """Return ``(kind, path)`` failures, where kind is MISSING or CASE."""
    root = Path(root).resolve()
    failures: list[tuple[str, str]] = []
    for relative in scan(root):
        kind = _failure_kind(root, relative)
        if kind:
            failures.append((kind, relative))
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="project root (default: current directory)")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    refs, directories = _scan(root)
    failures = missing(root)
    for relative in refs:
        print(f"REF {relative}")
    for relative in directories:
        print(f"{_directory_kind(root, relative)} {relative}")
    for kind, relative in failures:
        print(f"{kind} {relative}")
    print(f"SUMMARY refs={len(refs)} missing={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
