#!/usr/bin/env python3
"""Check a hosted static game page and every referenced asset URL."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin
from urllib.request import urlopen

from check_asset_refs import missing, scan


def fetch(url: str, timeout: float) -> tuple[int | None, bytes]:
    """Fetch one URL once and return its status and body."""
    try:
        with urlopen(url, timeout=timeout) as response:  # nosec B310: caller supplies the smoke-test URL
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()
    except (URLError, OSError, ValueError):
        return None, b""


def check(base_url: str, timeout: float, root: Path) -> int:
    """Print the four-line smoke-test result and return its exit status."""
    base = base_url.rstrip("/") + "/"
    references = scan(root)
    # Keep the scanner's local existence check in this path so the script stays
    # coupled to the same reference source as the release checker.
    missing(root)

    index_status, index_body = fetch(base, timeout)
    title_found = b"Pumpkin Killer" in index_body
    failed_paths: list[str] = []
    for relative_path in references:
        status, _body = fetch(urljoin(base, quote(relative_path, safe="/")), timeout)
        if status != 200:
            failed_paths.append(relative_path)

    index_ok = index_status == 200 and title_found
    overall_ok = index_ok and not failed_paths
    status_text = str(index_status) if index_status is not None else "ERROR"
    first_five = ", ".join(failed_paths[:5]) or "-"

    print(f"INDEX status={status_text} title={'yes' if title_found else 'no'}")
    print(f"PATHS checked={len(references)}")
    print(f"NON_200 count={len(failed_paths)} first_five={first_five}")
    print(f"OVERALL {'PASS' if overall_ok else 'FAIL'}")
    return 0 if overall_ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url")
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    return check(args.base_url, args.timeout, Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
