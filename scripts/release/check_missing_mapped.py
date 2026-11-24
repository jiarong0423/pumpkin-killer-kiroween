#!/usr/bin/env python3
"""Fail if a reference that check_asset_refs.py reports as missing is not named in the mapping document.

Usage: python3 -B scripts/release/check_missing_mapped.py [--root DIR] [--doc FILE]
Default document: docs/ingest_mapping_20261115.md. Output: one MAPPED or UNMAPPED line per missing path and
SUMMARY missing=N unmapped=M. Exit 1 if any path is unmapped. Read only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import check_asset_refs
except ImportError:  # pragma: no cover - module invocation
    from scripts.release import check_asset_refs  # type: ignore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="repository root")
    parser.add_argument("--doc", default="docs/ingest_mapping_20261115.md", help="mapping document, relative to the root")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    doc = root / args.doc
    if not doc.is_file():
        print(f"ERROR mapping document not found: {args.doc}", file=sys.stderr)
        return 2
    text = doc.read_text(encoding="utf-8")
    failures = check_asset_refs.missing(root)
    unmapped = 0
    for kind, path in failures:
        if path in text:
            print(f"MAPPED {path} ({kind})")
        else:
            unmapped += 1
            print(f"UNMAPPED {path} ({kind})")
    print(f"SUMMARY missing={len(failures)} unmapped={unmapped}")
    return 1 if unmapped else 0


if __name__ == "__main__":
    sys.exit(main())
