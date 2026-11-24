#!/usr/bin/env python3
"""Generate the service-worker precache block and version from tracked page assets.

The default --check mode returns 0 when the worker is current and 3 when it is
stale. --apply updates only CACHE_NAME and the lines between precache markers.
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
WORKER = ROOT / "sw.js"
BEGIN = "// PWA-PRECACHE-BEGIN"
END = "// PWA-PRECACHE-END"
CACHE_NAME_PATTERN = re.compile(r'^const CACHE_NAME = "[^"]+";$', re.MULTILINE)
PRELOAD_PATTERN = re.compile(
    r'<link\s+rel="preload"\s+as="image"\s+href="([^"]+)"\s*>'
)


NOT_PRECACHED = {"js/relay_client.js"}   # a network feature: offline play does not need it, and the worker must never name the relay (scripts/test_pwa_files.py)


def static_files(directory):
    return [
        path.relative_to(ROOT).as_posix()
        for path in sorted(directory.rglob("*"))
        if path.is_file() and not path.name.startswith(".") and path.relative_to(ROOT).as_posix() not in NOT_PRECACHED
    ]


def preload_files():
    html = INDEX.read_text(encoding="utf-8")
    start = html.index("<!-- PRELOAD-BEGIN -->")
    end = html.index("<!-- PRELOAD-END -->", start)
    paths = PRELOAD_PATTERN.findall(html[start:end])
    if len(paths) < 20:
        raise ValueError("expected at least 20 image preloads, found %d" % len(paths))
    if len(paths) != len(set(paths)):
        raise ValueError("preload list contains duplicate paths")
    return paths


def wanted_files():
    paths = ["index.html"]
    for directory in (ROOT / "css", ROOT / "js", ROOT / "shared"):
        paths.extend(static_files(directory))
    paths.extend(
        path.relative_to(ROOT).as_posix()
        for path in sorted((ROOT / "assets" / "fonts").glob("*.woff2"))
        if path.is_file()
    )
    paths.extend(static_files(ROOT / "assets" / "i18n"))
    paths.append("relay-config.js")
    paths.extend(preload_files())
    if len(paths) != len(set(paths)):
        raise ValueError("precache list contains duplicate paths")
    missing = [path for path in paths if not (ROOT / path).is_file()]
    if missing:
        raise ValueError("precache paths are missing: %s" % ", ".join(missing))
    return paths


def cache_name(paths):
    """Derive a cache version from the ordered asset list and their byte sizes."""
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str((ROOT / path).stat().st_size).encode("ascii"))
        digest.update(b"\n")
    return "pk-" + digest.hexdigest()[:10]


def generated_block(paths):
    rows = [BEGIN]
    rows.extend('  "%s",' % path for path in paths)
    rows.append(END)
    return "\n".join(rows)


def replace_block(worker, replacement):
    start = worker.find(BEGIN)
    end = worker.find(END, start)
    if start < 0 or end < 0:
        raise ValueError("sw.js is missing precache markers")
    end += len(END)
    return worker[:start] + replacement + worker[end:]


def replace_cache_name(worker, name):
    replacement = 'const CACHE_NAME = "%s";' % name
    updated, count = CACHE_NAME_PATTERN.subn(replacement, worker, count=1)
    if count != 1:
        raise ValueError("sw.js is missing a valid CACHE_NAME declaration")
    return updated


def main(argv=None):
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="check the generated worker (default)")
    mode.add_argument("--apply", action="store_true", help="write the generated worker")
    args = parser.parse_args(argv)
    try:
        paths = wanted_files()
        replacement = generated_block(paths)
        worker = WORKER.read_text(encoding="utf-8")
        start = worker.find(BEGIN)
        end = worker.find(END, start)
        if start < 0 or end < 0:
            raise ValueError("sw.js is missing precache markers")
        current_block = worker[start:end + len(END)]
        current_cache = CACHE_NAME_PATTERN.search(worker)
        if not current_cache:
            raise ValueError("sw.js is missing a valid CACHE_NAME declaration")
        expected_cache = cache_name(paths)
        if current_block == replacement and current_cache.group(0) == 'const CACHE_NAME = "%s";' % expected_cache:
            print("OK sw precache is up to date (%d files; %d preload assets; %s)" % (
                len(paths), len(preload_files()), expected_cache))
            return 0
        print("STALE sw precache: would write %d files; %d preload assets; %s" % (
            len(paths), len(preload_files()), expected_cache))
        if not args.apply:
            return 3
        worker = replace_block(worker, replacement)
        WORKER.write_text(replace_cache_name(worker, expected_cache), encoding="utf-8")
        print("OK wrote sw precache and cache name")
        return 0
    except (OSError, ValueError) as error:
        print("ERROR %s" % error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
