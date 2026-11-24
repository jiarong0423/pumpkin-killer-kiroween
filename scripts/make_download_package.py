#!/usr/bin/env python3
"""Build a deterministic local-play ZIP from the public export selection."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable

_RELEASE_DIR = Path(__file__).resolve().parent / "release"
if str(_RELEASE_DIR) not in sys.path:
    sys.path.insert(0, str(_RELEASE_DIR))

from export_tree import ExportError, apply_export, destination_for, load_manifest, prepare  # noqa: E402

PLAY_KIT = (
    ("PLAY.md", "PLAY.md"),
    ("requirements.txt", "requirements.txt"),
    ("deploy/package/start_game.sh", "start_game.sh"),
    ("deploy/package/start_game.bat", "start_game.bat"),
    ("deploy/package/start_agent.sh", "start_agent.sh"),
    ("deploy/package/start_agent.bat", "start_agent.bat"),
)
EXCLUSIONS_DOCUMENT = "docs/EXPORT_EXCLUDE_20261116.md"
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class PackageError(Exception):
    """The requested package cannot be safely built."""


def relative_files(root: Path) -> list[str]:
    """Return package members in a stable order without following symlinks."""
    names: list[str] = []
    for path in root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            names.append(path.relative_to(root).as_posix())
    return sorted(names)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def export_exclusions(source: Path) -> set[str]:
    """Read the explicit public-export exclusions without relying on a duplicate list."""
    document = source / EXCLUSIONS_DOCUMENT
    if not document.is_file():
        raise PackageError(f"export exclusions document is unavailable: {EXCLUSIONS_DOCUMENT}")
    exclusions = set(re.findall(r"`([^`]+)`", document.read_text(encoding="utf-8")))
    valid = {path for path in exclusions if path and not path.startswith("/") and ".." not in Path(path).parts}
    if not valid:
        raise PackageError("export exclusions document lists no relative files")
    return valid


def add_play_kit(stage: Path, kit_root: Path) -> None:
    """Copy the fixed local-launch files after the public export is staged."""
    for source_name, destination_name in PLAY_KIT:
        source = kit_root / source_name
        if not source.is_file() or source.is_symlink():
            raise PackageError(f"required play-kit file is unavailable: {source_name}")
        destination = stage / destination_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def remove_excluded_files(stage: Path, exclusions: set[str]) -> None:
    for name in exclusions:
        target = stage / name
        if target.is_file() or target.is_symlink():
            target.unlink()


def write_checksums(stage: Path) -> None:
    """Write hashes for every payload file; a checksum manifest cannot hash itself."""
    rows = [f"{sha256_file(stage / name)}  {name}" for name in relative_files(stage)
            if name != "SHA256SUMS.txt"]
    (stage / "SHA256SUMS.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")


def run_privacy_gate(stage: Path, gate: Path) -> None:
    """Fail closed when the existing release gate cannot approve the staged files."""
    if not gate.is_file():
        raise PackageError("privacy gate is unavailable")
    completed = subprocess.run(
        [sys.executable, str(gate), "--tree", str(stage)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if completed.returncode:
        detail = completed.stdout.strip()
        if detail.startswith("ERROR PK_TERMS"):
            raise PackageError("privacy gate could not read its required terms file")
        if detail:
            raise PackageError(f"privacy gate blocked the staged package:\n{detail}")
        raise PackageError("privacy gate blocked the staged package")


def stage_package(source: Path, manifest: Path, kit_root: Path, gate: Path) -> Path:
    """Create a temporary public-export tree plus local play kit and checksums."""
    rules = load_manifest(manifest)
    selected, _grouped, _skipped = prepare(source, rules)
    temporary = Path(tempfile.mkdtemp(prefix="pumpkin-killer-package-"))
    try:
        apply_export(source, temporary, selected)
        remove_excluded_files(temporary, export_exclusions(source))
        add_play_kit(temporary, kit_root)
        write_checksums(temporary)
        run_privacy_gate(temporary, gate)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return temporary


def dry_run_plan(source: Path, manifest: Path, kit_root: Path) -> tuple[list[str], int]:
    """List the intended package without staging files or requiring PK_TERMS."""
    rules = load_manifest(manifest)
    selected, _grouped, _skipped = prepare(source, rules)
    exclusions = export_exclusions(source)
    members: dict[str, int] = {}
    for name, _index, rule in selected:
        destination = destination_for(name, rule.get("transform"))
        if name not in exclusions:
            members[destination] = (source / name).stat().st_size
    for source_name, destination in PLAY_KIT:
        source_file = kit_root / source_name
        if not source_file.is_file() or source_file.is_symlink():
            raise PackageError(f"required play-kit file is unavailable: {source_name}")
        members[destination] = source_file.stat().st_size
    members["docs/kiro_evidence/EXPORT_NOTES.md"] = 0
    members["SHA256SUMS.txt"] = 0
    return sorted(members), sum(members.values())


def write_zip(stage: Path, output: Path) -> None:
    """Write a reproducible ZIP without source mtimes or platform-specific modes."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in relative_files(stage):
            info = zipfile.ZipInfo(name, FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (stage / name).read_bytes(), compress_type=zipfile.ZIP_DEFLATED,
                             compresslevel=9)


def build(source: Path, manifest: Path, kit_root: Path, gate: Path, output: Path) -> tuple[list[str], int, str]:
    """Stage, validate, and package the selected public files."""
    stage = stage_package(source, manifest, kit_root, gate)
    try:
        names = relative_files(stage)
        total_size = sum((stage / name).stat().st_size for name in names)
        if output.exists():
            raise PackageError("output already exists; choose a new --out path")
        write_zip(stage, output)
        return names, total_size, sha256_file(output)
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=".", help="repository root to package")
    parser.add_argument("--manifest", help="public export manifest (default: source manifest)")
    parser.add_argument("--kit-root", help="root containing PLAY.md, requirements.txt, and deploy/package")
    parser.add_argument("--gate", help="privacy_gate.py to run on the staged tree")
    parser.add_argument("--out", required=True, help="output ZIP path")
    parser.add_argument("--dry-run", action="store_true", help="list the package without writing or running the gate")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    source = Path(args.source).resolve()
    manifest = Path(args.manifest).resolve() if args.manifest else source / "scripts/release/export_manifest.json"
    kit_root = Path(args.kit_root).resolve() if args.kit_root else source
    gate = Path(args.gate).resolve() if args.gate else _RELEASE_DIR / "privacy_gate.py"
    output = Path(args.out).resolve()
    try:
        if not source.is_dir():
            raise PackageError("source tree is unavailable")
        if args.dry_run:
            names, total_size = dry_run_plan(source, manifest, kit_root)
            zip_hash = None
        else:
            names, total_size, zip_hash = build(source, manifest, kit_root, gate, output)
        for name in names:
            print(f"FILE {name}")
        print(f"SUMMARY files={len(names)} bytes={total_size}")
        if args.dry_run:
            print("DRY RUN: wrote nothing; privacy gate was not run")
        else:
            print(f"ZIP bytes={output.stat().st_size} sha256={zip_hash}")
        return 0
    except (ExportError, OSError, PackageError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
