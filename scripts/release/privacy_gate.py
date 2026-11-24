#!/usr/bin/env python3
"""Check a release tree and its rebuilt history for private material.

The gate deliberately reports locations, never the material that matched.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import zipfile
import zlib


BLOCK = "BLOCK"
REVIEW = "REVIEW"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z.]{2,}")
LOCAL_PATH_RE = re.compile(r"/Use" r"rs/[^/ ]+|/home/[a-z][^/ ]*/|[A-Z]:\\\\Users")
SECRET_SHAPE_RE = re.compile(
    r"AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,}|"
    r"sk-[A-Za-z0-9]{20,}|BEGIN [A-Z ]*PRIVATE KEY"
)
ASSIGNED_SECRET_RE = re.compile(
    r"(secret|token|passw(?:or)?d|api[_-]?key)[A-Za-z_]*[\"' ]*[:=][\"' ]*"
    r"[A-Za-z0-9/+_-]{16,}",
    re.IGNORECASE,
)
SECRET_NAME_RE = re.compile(r"secret|token|passw(?:or)?d|api[_-]?key", re.IGNORECASE)
BALANCE_RE = re.compile(
    r"credits? (?:left|remaining|balance)|balance|NT\$|剩餘|餘額|已使用|運算元|compute units?",
    re.IGNORECASE,
)
DRIVE_RE = re.compile(r"drive\.google\.com|/content/drive|MyDrive|rclone|folder[_-]?id")
PLACEHOLDER_RE = re.compile(r"HOSTED_URL|TODO_OWNER|<PLACEHOLDER>")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
DOCS_CODE_RE = re.compile(r"`(docs/[^`\s]+)`")


class Reporter:
    def __init__(self) -> None:
        self.block_count = 0

    def hit(self, classification: str, check: str, location: str) -> None:
        # Locations are the only evidence emitted. Do not add matched text here.
        print(f"{classification} {check} {location}")
        if classification == BLOCK:
            self.block_count += 1


def read_terms() -> list[str] | None:
    """Return non-empty fixed terms from PK_TERMS without exposing its path."""
    name = os.environ.get("PK_TERMS")
    if not name:
        return None
    try:
        terms = [line.strip() for line in Path(name).read_text(encoding="utf-8").splitlines()]
    except (OSError, UnicodeError):
        return None
    terms = [term for term in terms if term]
    return terms or None


def is_text(data: bytes) -> bool:
    return b"\x00" not in data


def text_lines(data: bytes) -> list[str]:
    if not is_text(data):
        return []
    return data.decode("utf-8", errors="ignore").splitlines()


def line_numbers(lines: list[str], predicate) -> list[int]:
    return [number for number, line in enumerate(lines, 1) if predicate(line)]


def is_allowed_email(line: str) -> bool:
    """P1 permits the noreply and redacted addresses named in the plan."""
    return bool(EMAIL_RE.search(line)) and all(
        match.endswith("noreply.github.com") or re.search(r"@[0-9]x\.", match)
        for match in EMAIL_RE.findall(line)
    )


def p1_matches(lines: list[str]) -> list[int]:
    return line_numbers(lines, lambda line: bool(EMAIL_RE.search(line)) and not is_allowed_email(line))


def p2_matches(lines: list[str]) -> list[int]:
    return line_numbers(lines, LOCAL_PATH_RE.search)


def p3_matches(lines: list[str]) -> list[int]:
    return line_numbers(lines, SECRET_SHAPE_RE.search)


def p4_matches(lines: list[str]) -> list[int]:
    return line_numbers(lines, ASSIGNED_SECRET_RE.search)


def p5_matches(lines: list[str]) -> list[int]:
    return line_numbers(lines, SECRET_NAME_RE.search)


def is_allowed_p7_owner_copyright(relative: str, line: str) -> bool:
    """Keep the owner-selected copyright holder in the root MIT licence only."""
    return relative == "LICENSE" and line.startswith("Copyright (c)")


def p7_matches(lines: list[str], terms: list[str], relative: str = "") -> list[int]:
    folded = [term.casefold() for term in terms]
    return line_numbers(
        lines,
        lambda line: not is_allowed_p7_owner_copyright(relative, line)
        and any(term in line.casefold() for term in folded),
    )


def p8_matches(lines: list[str]) -> list[int]:
    return line_numbers(lines, BALANCE_RE.search)


def p9_matches(lines: list[str]) -> list[int]:
    return line_numbers(lines, DRIVE_RE.search)


def p10_matches(lines: list[str]) -> list[int]:
    return line_numbers(lines, CJK_RE.search)


def p14_matches(lines: list[str]) -> list[int]:
    return line_numbers(lines, PLACEHOLDER_RE.search)


def relative_files(tree: Path):
    for base, directories, files in os.walk(tree):
        directories[:] = sorted(name for name in directories if name != ".git")
        for name in sorted(files):
            path = Path(base, name)
            if path.is_symlink():
                continue
            try:
                relative = path.relative_to(tree).as_posix()
            except ValueError:
                continue
            yield path, relative


def forbidden_filename(relative: str) -> bool:
    name = PurePosixPath(relative).name
    return (
        name.startswith(".env")
        or name.endswith(".pem")
        or name.endswith(".key")
        or name.startswith("id_rsa")
        or name == ".netrc"
        or name.endswith(".p12")
        or name == ".DS_Store"
    )


def location(relative: str, line: int) -> str:
    return f"{relative}:{line}"


def is_font_license(relative: str) -> bool:
    """Preserve font-author copyright notices required by their OFL licences."""
    path = PurePosixPath(relative)
    return path.parent == PurePosixPath("assets/fonts") and fnmatch.fnmatchcase(path.name, "OFL-*.txt")


def scan_text_checks(tree: Path, terms: list[str], reporter: Reporter, checks: set[str]) -> None:
    for path, relative in relative_files(tree):
        try:
            data = path.read_bytes()
        except OSError:
            # A disappearing unreadable file is a reviewable release problem,
            # but does not reveal a path outside the release tree.
            continue
        lines = text_lines(data)
        if not lines:
            continue
        for check, classification, matches in (
            ("P1", BLOCK, [] if is_font_license(relative) else p1_matches(lines)),
            ("P2", BLOCK, p2_matches(lines)),
            ("P3", BLOCK, p3_matches(lines)),
            ("P4", BLOCK, p4_matches(lines)),
            ("P5", REVIEW, p5_matches(lines)),
            ("P7", BLOCK, p7_matches(lines, terms, relative)),
            ("P8", REVIEW, p8_matches(lines)),
            ("P9", REVIEW, p9_matches(lines)),
        ):
            if check not in checks:
                continue
            for line in matches:
                reporter.hit(classification, check, location(relative, line))


def scan_p6(tree: Path, reporter: Reporter) -> None:
    for _path, relative in relative_files(tree):
        if forbidden_filename(relative):
            reporter.hit(BLOCK, "P6", location(relative, 0))


def scan_p7_filenames(tree: Path, terms: list[str], reporter: Reporter) -> None:
    folded = [term.casefold() for term in terms]
    for _path, relative in relative_files(tree):
        if any(term in relative.casefold() for term in folded):
            reporter.hit(BLOCK, "P7", location(relative, 0))


def scan_p10(tree: Path, reporter: Reporter) -> None:
    allowed = {"index.html", "assets/fonts/charset.txt"}
    for path, relative in relative_files(tree):
        if relative in allowed or relative.startswith("js/") or relative.startswith("css/"):
            continue
        try:
            lines = text_lines(path.read_bytes())
        except OSError:
            continue
        for line in p10_matches(lines):
            reporter.hit(REVIEW, "P10", location(relative, line))


def metadata_has_block(data: bytes, terms: list[str]) -> bool:
    lines = text_lines(data) or [data.decode("latin-1", errors="ignore")]
    return bool(
        p1_matches(lines)
        or p2_matches(lines)
        or p3_matches(lines)
        or p4_matches(lines)
        or p7_matches(lines, terms)
    )


def png_metadata(path: Path) -> list[bytes]:
    """Read only PNG textual and EXIF chunks without an image dependency."""
    try:
        data = path.read_bytes()
    except OSError:
        return []
    if not data.startswith(PNG_SIGNATURE):
        return []
    chunks: list[bytes] = []
    position = len(PNG_SIGNATURE)
    while position + 12 <= len(data):
        length = int.from_bytes(data[position : position + 4], "big")
        kind = data[position + 4 : position + 8]
        end = position + 8 + length
        if end + 4 > len(data):
            break
        payload = data[position + 8 : end]
        if kind == b"tEXt" or kind == b"eXIf":
            chunks.append(payload)
        elif kind == b"zTXt":
            try:
                _key, compressed = payload.split(b"\0", 1)
                chunks.append(zlib.decompress(compressed[1:]))
            except (ValueError, zlib.error):
                chunks.append(payload)
        elif kind == b"iTXt":
            try:
                _key, remainder = payload.split(b"\0", 1)
                compressed = remainder[0] == 1
                text = remainder[2:]
                _language, text = text.split(b"\0", 1)
                _translated, text = text.split(b"\0", 1)
                chunks.append(zlib.decompress(text) if compressed else text)
            except (IndexError, ValueError, zlib.error):
                chunks.append(payload)
        position = end + 4
    return chunks


def jpeg_exif(path: Path) -> list[bytes]:
    try:
        data = path.read_bytes()
    except OSError:
        return []
    if not data.startswith(b"\xff\xd8"):
        return []
    chunks: list[bytes] = []
    position = 2
    while position + 4 <= len(data) and data[position] == 0xFF:
        marker = data[position + 1]
        if marker in (0xD8, 0xD9):
            position += 2
            continue
        length = int.from_bytes(data[position + 2 : position + 4], "big")
        if length < 2 or position + 2 + length > len(data):
            break
        payload = data[position + 4 : position + 2 + length]
        if marker == 0xE1 and payload.startswith(b"Exif\0\0"):
            chunks.append(payload)
        position += 2 + length
    return chunks


def scan_p11(tree: Path, terms: list[str], reporter: Reporter) -> None:
    for path, relative in relative_files(tree):
        suffix = path.suffix.lower()
        chunks: list[bytes] = []
        if suffix == ".png":
            chunks = png_metadata(path)
        elif suffix in {".jpg", ".jpeg"}:
            chunks = jpeg_exif(path)
        if any(metadata_has_block(chunk, terms) for chunk in chunks):
            reporter.hit(BLOCK, "P11", location(relative, 0))
        if suffix == ".zip":
            try:
                with zipfile.ZipFile(path) as archive:
                    names = archive.namelist()
            except (OSError, zipfile.BadZipFile):
                continue
            if any(metadata_has_block(name.encode("utf-8", "ignore"), terms) for name in names):
                reporter.hit(BLOCK, "P11", location(relative, 0))


def scan_p12(tree: Path, reporter: Reporter) -> None:
    for path, relative in relative_files(tree):
        try:
            if path.stat().st_size > 20 * 1024 * 1024:
                reporter.hit(BLOCK, "P12", location(relative, 0))
        except OSError:
            continue


def local_target_exists(tree: Path, source: Path, target: str) -> bool:
    parts = target.strip().strip("<>").split(maxsplit=1)
    if not parts:   # an empty target such as "[x]()" has nothing to check (the same IndexError that broke the export, 2026-11-15)
        return True
    target = parts[0]
    target = target.split("#", 1)[0].split("?", 1)[0]
    target = re.sub(r":\d+(?:-\d+)?$", "", target)   # "path:line" is a reference to the file, same rule as export_tree.local_reference_target
    if not target or target.startswith("#") or target.startswith("//") or re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target):
        return True
    if target.startswith("docs/"):
        candidate = tree / target
    else:
        candidate = source.parent / target
    if any(ch in target for ch in ("*", "?", "[")):
        # RECHECK-2 (2026-11-25): a glob such as `docs/kiro_task_*.md` is not a link; it is fine when it matches at least one file or folder.
        base = tree if target.startswith("docs/") else source.parent
        try:
            return next(iter(base.glob(target)), None) is not None
        except (ValueError, NotImplementedError, OSError):
            return False
    try:
        candidate.resolve().relative_to(tree.resolve())
    except ValueError:
        return False
    return candidate.exists()


def scan_p13(tree: Path, reporter: Reporter) -> None:
    for path, relative in relative_files(tree):
        if path.suffix.lower() not in {".md", ".markdown"}:
            continue
        try:
            lines = text_lines(path.read_bytes())
        except OSError:
            continue
        for number, line in enumerate(lines, 1):
            targets = MARKDOWN_LINK_RE.findall(line) + DOCS_CODE_RE.findall(line)
            if any(not local_target_exists(tree, path, target) for target in targets):
                reporter.hit(BLOCK, "P13", location(relative, number))


def scan_p14(tree: Path, reporter: Reporter) -> None:
    for name in ("README.md", "JUDGES.md", "CREDITS.md"):
        path = tree / name
        if not path.is_file():
            continue
        try:
            lines = text_lines(path.read_bytes())
        except OSError:
            continue
        for line in p14_matches(lines):
            reporter.hit(BLOCK, "P14", location(name, line))


def scan_tree(tree: Path, terms: list[str], selected: str, reporter: Reporter) -> None:
    if selected == "cjk":
        scan_p10(tree, reporter)
        return
    if selected == "png-text":
        scan_p11(tree, terms, reporter)
        return
    if selected == "links":
        scan_p13(tree, reporter)
        return

    checks = {"P1", "P2", "P3", "P4", "P5", "P7", "P8", "P9"}
    scan_text_checks(tree, terms, reporter, checks)
    scan_p6(tree, reporter)
    scan_p7_filenames(tree, terms, reporter)
    scan_p10(tree, reporter)
    scan_p11(tree, terms, reporter)
    scan_p12(tree, reporter)
    scan_p13(tree, reporter)
    scan_p14(tree, reporter)


def git(repo: Path, *args: str) -> bytes | None:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout
    except OSError:
        return None


def history_files(repo: Path, commit: str) -> list[str]:
    output = git(repo, "ls-tree", "-r", "--name-only", commit)
    return output.decode("utf-8", "surrogateescape").splitlines() if output is not None else []


def history_contents(repo: Path, commit: str, filename: str) -> bytes:
    output = git(repo, "show", f"{commit}:{filename}")
    return output or b""


def scan_history_patterns(repo: Path, terms: list[str], reporter: Reporter) -> None:
    commits_output = git(repo, "rev-list", "--all")
    if commits_output is None:
        reporter.hit(BLOCK, "P15", "HEAD:.git/P15")
        return
    for commit in commits_output.decode("ascii", "ignore").splitlines():
        for filename in history_files(repo, commit):
            data = history_contents(repo, commit, filename)
            lines = text_lines(data)
            if lines:
                for check, matches in (
                    ("P1", p1_matches(lines)),
                    ("P2", p2_matches(lines)),
                    ("P3", p3_matches(lines)),
                    ("P4", p4_matches(lines)),
                    ("P7", p7_matches(lines, terms, filename)),
                ):
                    if matches:
                        reporter.hit(BLOCK, check, f"{commit}:{filename}")
            if forbidden_filename(filename):
                reporter.hit(BLOCK, "P6", f"{commit}:{filename}")
            if any(term.casefold() in filename.casefold() for term in terms):
                reporter.hit(BLOCK, "P7", f"{commit}:{filename}")


def scan_p15(repo: Path, terms: list[str], reporter: Reporter) -> None:
    commits_output = git(repo, "rev-list", "--all")
    if commits_output is None:
        reporter.hit(BLOCK, "P15", "HEAD:.git/P15")
        return
    commits = commits_output.decode("ascii", "ignore").splitlines()
    identities = git(repo, "log", "--all", "--format=%an%x1f%ae%x1f%cn%x1f%ce")
    identity_rows = identities.decode("utf-8", "replace").splitlines() if identities is not None else []
    valid_identity = len(set(identity_rows)) == 1 and len(identity_rows) > 0
    if valid_identity:
        parts = identity_rows[0].split("\x1f")
        valid_identity = (
            len(parts) == 4
            and parts[0] == parts[2]
            and parts[1] == parts[3]
            and parts[1].endswith("noreply.github.com")
        )
    if not valid_identity:
        reporter.hit(BLOCK, "P15", f"{commits[0] if commits else 'HEAD'}:.git/P15")

    messages = git(repo, "log", "--all", "--format=%H%x1f%B%x1e")
    if messages is None:
        reporter.hit(BLOCK, "P15", "HEAD:.git/P15")
        return
    for record in messages.decode("utf-8", "replace").split("\x1e"):
        if not record.strip() or "\x1f" not in record:
            continue
        commit, message = record.split("\x1f", 1)
        if re.search(r"^co-authored-by", message, re.IGNORECASE | re.MULTILINE) or any(
            term.casefold() in message.casefold() for term in terms
        ):
            reporter.hit(BLOCK, "P15", f"{commit}:.git/P15")


def scan_p16(repo: Path, reporter: Reporter) -> None:
    try:
        ignored = subprocess.run(
            ["git", "-C", str(repo), "check-ignore", "-q", ".kiro"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0
    except OSError:
        reporter.hit(BLOCK, "P16", "HEAD:.git/P16")
        return
    files = git(repo, "ls-files")
    names = files.decode("utf-8", "surrogateescape").splitlines() if files is not None else []
    if ignored or sum(name.startswith(".kiro/") for name in names) < 73 or any(name.startswith("docs/audition/") for name in names):
        head = git(repo, "rev-parse", "HEAD")
        commit = head.decode("ascii", "ignore").strip() if head else "HEAD"
        reporter.hit(BLOCK, "P16", f"{commit}:.git/P16")


def scan_history(repo: Path, terms: list[str], reporter: Reporter) -> None:
    scan_history_patterns(repo, terms, reporter)
    scan_p15(repo, terms, reporter)
    scan_p16(repo, reporter)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", required=True, help="release tree to scan")
    parser.add_argument("--check", choices=("cjk", "png-text", "links", "all"), default="all")
    parser.add_argument("--history", help="rebuilt repository whose history to scan")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    terms = read_terms()
    if terms is None:
        print("ERROR PK_TERMS is missing or empty")
        return 1
    tree = Path(args.tree)
    if not tree.is_dir():
        print("ERROR tree is unavailable")
        return 1
    reporter = Reporter()
    scan_tree(tree, terms, args.check, reporter)
    if args.history:
        repo = Path(args.history)
        if not repo.is_dir():
            print("ERROR history repository is unavailable")
            return 1
        scan_history(repo, terms, reporter)
    return 1 if reporter.block_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
