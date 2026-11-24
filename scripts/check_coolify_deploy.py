#!/usr/bin/env python3
"""Static checks for the Coolify container (deploy/Dockerfile.coolify, deploy/entrypoint.sh, deploy/nginx.conf).
Each rule comes from a pre-push audit finding (redteam/PREPUSH_AUDIT_20261124.md). No network, no Docker needed."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def copy_destinations(dockerfile: str) -> set[str]:
    dests = set()
    for match in re.finditer(r"^COPY\s+(?:--\S+\s+)*(\S+)\s+(\S+)\s*$", dockerfile, flags=re.MULTILINE):
        dests.add(match.group(2).rstrip("/"))
    return dests


def validate(root: Path = ROOT) -> list[str]:
    """Return a list of problems; an empty list means every rule holds."""
    problems: list[str] = []
    docker = (root / "deploy" / "Dockerfile.coolify").read_text(encoding="utf-8")
    entry = (root / "deploy" / "entrypoint.sh").read_text(encoding="utf-8")
    nginx = (root / "deploy" / "nginx.conf").read_text(encoding="utf-8")

    dests = copy_destinations(docker)
    for path in sorted(set(re.findall(r"python3\s+(/app/\S+\.py)", entry))):
        if path not in dests:
            problems.append("entrypoint.sh starts %s but Dockerfile.coolify never copies a file to that path" % path)

    health = re.search(r"^HEALTHCHECK.*?(?=^\S|\Z)", docker, flags=re.MULTILINE | re.DOTALL)
    if not health or "/mcp/health" not in health.group(0):
        problems.append("HEALTHCHECK does not probe /mcp/health")

    if not re.search(r"location\s+/assets/i18n/\s*\{[^}]*no-cache", nginx, flags=re.DOTALL):
        problems.append("nginx.conf: assets/i18n/ files must not get the one-year immutable cache (no hash in the file name)")

    ai = re.search(r"location\s*=\s*/ai\s*\{(.*?)\n    \}", nginx, flags=re.DOTALL)
    if not ai or "$proxy_add_x_forwarded_for" in ai.group(1):
        problems.append("nginx.conf: /ai must set X-Forwarded-For to $remote_addr (the client can forge the appended header)")

    # FLOOD-2 (2026-11-25): per-client limits need the real client address, and slow-client timeouts
    if not re.search(r"real_ip_header\s+CF-Connecting-IP\s*;", nginx) or not re.search(r"set_real_ip_from\s+(172\.16\.0\.0/12|10\.0\.0\.0/8)", nginx):
        problems.append("nginx.conf: take the client address from CF-Connecting-IP (real_ip_header) and trust it only from private ranges (set_real_ip_from), or every limit counts the tunnel")
    if "set_real_ip_from 0.0.0.0/0" in nginx or re.search(r"set_real_ip_from\s+all", nginx):
        problems.append("nginx.conf: set_real_ip_from must never trust every address")
    for zone in ("pk_page", "pk_ws", "pk_mcp"):
        if not re.search(r"limit_req_zone\s+\$binary_remote_addr\s+zone=%s:" % zone, nginx) or not re.search(r"limit_req\s+zone=%s\b" % zone, nginx):
            problems.append("nginx.conf: limit_req_zone and limit_req for %s are missing (per-client request rate)" % zone)
    if not re.search(r"limit_conn_zone\s+\$binary_remote_addr\s+zone=pk_conn:", nginx) or not re.search(r"limit_conn\s+pk_conn\s+\d+", nginx):
        problems.append("nginx.conf: limit_conn_zone and limit_conn for pk_conn are missing (per-client open connections)")
    if not re.search(r"limit_req_status\s+429\s*;", nginx) or not re.search(r"limit_conn_status\s+429\s*;", nginx):
        problems.append("nginx.conf: answer over-limit requests with 429")
    for directive in ("client_header_timeout", "client_body_timeout", "send_timeout", "reset_timedout_connection"):
        if directive not in nginx:
            problems.append("nginx.conf: %s is missing (slow-client protection)" % directive)

    if not re.search(r"gzip_types[^;]*text/javascript", nginx):
        problems.append("nginx.conf: gzip_types lacks text/javascript")

    if "PK_ALLOWED_ORIGINS" not in entry or not re.search(r"ERROR[^\n]*PK_ALLOWED_ORIGINS|PK_ALLOWED_ORIGINS[^\n]*ERROR", entry):
        problems.append("entrypoint.sh: no ERROR line when PK_ALLOWED_ORIGINS is empty")
    if not re.search(r"PK_AI_PRICE_IN_PER_M", entry) or not re.search(r"ERROR[^\n]*PK_AI_PRICE", entry):
        problems.append("entrypoint.sh: the AI gateway may start without PK_AI_PRICE_IN_PER_M and PK_AI_PRICE_OUT_PER_M, which makes the dollar caps blind (only the call cap would hold); it must refuse with an ERROR line")
    if "kill -0" not in entry:
        problems.append("entrypoint.sh: nothing watches the relay and MCP processes; if one dies the container keeps running")

    ignore = root / ".dockerignore"
    if not ignore.exists():
        problems.append(".dockerignore is missing")
    else:
        lines = {line.strip().rstrip("/") for line in ignore.read_text(encoding="utf-8").splitlines()}
        for name in ("docs", "redteam", "colab", "build", "logs_local"):
            if name not in lines:
                problems.append(".dockerignore does not list %s" % name)

    if not re.search(r"chmod\s+-R\s+a\+rX\s+/usr/share/nginx/html", docker):
        problems.append("Dockerfile.coolify: files copied from a 0600 checkout stay unreadable for the nginx worker (403); add chmod -R a+rX /usr/share/nginx/html")

    req = (root / "requirements.txt").read_text(encoding="utf-8")
    if not re.search(r"^websockets==\d", req, flags=re.MULTILINE):
        problems.append("requirements.txt: websockets is not pinned with ==")
    return problems


def main() -> int:
    problems = validate()
    for problem in problems:
        print("ERROR " + problem, file=sys.stderr)
    if problems:
        return 1
    print("OK coolify deploy files hold every rule")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
