#!/usr/bin/env python3
"""Verify the files and HTTP settings required by the static deployment image."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "deploy" / "Dockerfile"
NGINX_CONF = ROOT / "deploy" / "nginx.conf"
MANIFEST = ROOT / "manifest.webmanifest"


def docker_copy_sources(source: str) -> set[str]:
    return {
        match.group(1)
        for match in re.finditer(r"^COPY\s+([^\s]+)", source, flags=re.MULTILINE)
    }


def types_block(source: str) -> str:
    match = re.search(r"\btypes\s*\{(?P<body>.*?)\n\s*\}", source, flags=re.DOTALL)
    if not match:
        raise AssertionError("nginx.conf has no types block")
    return match.group("body")


def validate(dockerfile: Path = DOCKERFILE, nginx_conf: Path = NGINX_CONF,
             manifest: Path = MANIFEST) -> None:
    """Raise AssertionError when the static image misses PWA files or MIME settings."""
    docker = dockerfile.read_text(encoding="utf-8")
    nginx = nginx_conf.read_text(encoding="utf-8")
    icons = json.loads(manifest.read_text(encoding="utf-8")).get("icons", [])
    expected = {"sw.js", "manifest.webmanifest"}
    expected.update(icon["src"] for icon in icons)
    missing = sorted(expected - docker_copy_sources(docker))
    if missing:
        raise AssertionError("Dockerfile does not copy: " + ", ".join(missing))

    # nginx rejects a types block nested in another one: /etc/nginx/mime.types has its own `types { }` wrapper, so the
    # block here must include a copy WITHOUT the wrapper, which the Dockerfile makes from the original.
    if "include /etc/nginx/pk_mime_body.types;" not in types_block(nginx):
        raise AssertionError("nginx types block must include /etc/nginx/pk_mime_body.types (the wrapper-less copy)")
    if "pk_mime_body.types" not in docker:
        raise AssertionError("Dockerfile must create /etc/nginx/pk_mime_body.types from /etc/nginx/mime.types")
    if not re.search(r"location\s*=\s*/sw\.js\s*\{[^}]*default_type\s+application/javascript;",
                     nginx, flags=re.DOTALL):
        raise AssertionError("sw.js must be served as application/javascript")
    if not re.search(r"location\s*=\s*/sw\.js\s*\{[^}]*Cache-Control\s+\"[^\"]*no-cache",
                     nginx, flags=re.DOTALL):
        raise AssertionError("sw.js must have a no-cache policy")
    if not re.search(r"location\s+/assets/\s*\{[^}]*max-age=31536000[^}]*immutable",
                     nginx, flags=re.DOTALL):
        raise AssertionError("assets must have a long immutable cache policy")


def main() -> int:
    try:
        validate()
    except (AssertionError, OSError, json.JSONDecodeError, KeyError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK deploy Dockerfile and nginx configuration are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
