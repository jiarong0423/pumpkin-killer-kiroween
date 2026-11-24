#!/usr/bin/env python3
"""Fail safely when a tracked text file resembles a provider credential."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY_PATTERNS = (
    re.compile(rb"AIza[A-Za-z0-9_-]{35}"),
    re.compile(rb"AQ\.[A-Za-z0-9_-]{20,}"),
    re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
)
# Scan assignments, rather than arbitrary 40-character text, so SHA-1 comments
# and commit IDs are not false positives.
ASSIGNED_BASE64_SECRET = re.compile(
    rb"(?im)\b[A-Za-z_][A-Za-z0-9_.-]*(?:secret|key)[A-Za-z0-9_.-]*\b\s*(?:=|:)\s*['\"]?[A-Za-z0-9+/]{40}(?:['\"]|\b)"
)


def tracked_files():
    if (ROOT / ".git").exists():
        completed = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True)
        return [Path(name.decode("utf-8")) for name in completed.stdout.split(b"\0") if name]
    return sorted(p.relative_to(ROOT) for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts)


def text_content(path):
    try:
        content = path.read_bytes()
    except OSError:
        return None
    if b"\0" in content:
        return None
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return content


def finding_lines(content):
    """Return unique 1-indexed lines for credential-like content, never values."""
    starts = set()
    for pattern in (*KEY_PATTERNS, ASSIGNED_BASE64_SECRET):
        starts.update(match.start() for match in pattern.finditer(content))
    return sorted(content.count(b"\n", 0, start) + 1 for start in starts)


def self_test():
    """Exercise runtime-built credentials without placing them in a tracked file."""
    fake_aws = b"AK" + b"IA" + b"A" * 16
    fake_secret = b"session_" + b"secret" + b' = "' + b"Q" * 40 + b'"'
    normal_hash_comment = b"# sha1 used for hashing: " + b"a" * 40
    findings = finding_lines(fake_aws + b"\n" + fake_secret + b"\n" + normal_hash_comment)
    if findings != [1, 2]:
        raise AssertionError("credential scanner self-test failed")


def main() -> int:
    self_test()
    findings = []
    for relative_path in tracked_files():
        content = text_content(ROOT / relative_path)
        if content is None:
            continue
        findings.extend(f"{relative_path.as_posix()}:{line_number}" for line_number in finding_lines(content))
    if findings:
        for finding in findings:
            print(finding)
        return 1
    print("test_no_secrets_in_tree: no secrets detected in tracked text files (self-test passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
