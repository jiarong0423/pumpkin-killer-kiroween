#!/usr/bin/env python3
"""Audit public/release docs in dev and v3 for stale claims, old UI wording, broken links, or leaked local paths."""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

BANNED_RULES = [
    ("OLD_MCP_TOOL_COUNT", re.compile(r"\b(?:3|three)\s+room\s+tools\b", re.I)),
    ("OLD_TEST_COUNT_184", re.compile(r"\b184\s+(?:`?test_\*`?\s+)?(?:scripts|tests|automated\s+test\s+scripts)\b|\b184\s+tests\b", re.I)),
    ("OLD_BATCH_COUNT_178", re.compile(r"\b178\s+run\b|\b6\s+local-socket\s+tests\s+skipped\b", re.I)),
    ("OLD_RESULT_COUNT_112", re.compile(r"\b(?:across\s+)?112\s+result(?:s|\s+reports)\b|\b112\s+results\s+are\s+recorded\b", re.I)),
    ("OLD_LOBBY_FILL_BUTTON", re.compile(r"Fill\s+open\s+slots\s*\(AI\)|#slot-fill-ai", re.I)),
    ("OLD_FRIENDS_PANEL_UI", re.compile(r"Friends\s*&\s*Seats\s*panel|Set\s+a\s+seat\s+to\s+\*\*Agent\s*\(MCP\)\*\*|pick\s+\*\*Agent\*\*\s+for\s+the\s+other\s+seat", re.I)),
    ("OLD_HOSTED_PAGE_JUDGE_OFF", re.compile(r"off\s+by\s+default\s+when\s+hosted", re.I)),
    ("OLD_NOT_DEPLOYED_CLAIM", re.compile(r"remote\s+public\s+/mcp\s+deployment\s+is\s+pending|NOT\s+deployed,\s*NOT\s+VERIFIED|nothing\s+is\s+live", re.I)),
    ("OLD_NODE_18_CLAIM", re.compile(r"Node\.js\s+18\s+or\s+newer", re.I)),
    ("OLD_POWER_0_100", re.compile(r"throw\s+\{[^}]*power\s+0-100\b", re.I)),
    ("OLD_REF_BAR_CREDITS", re.compile(r"ref_bar_from_video\.png.*source\s+and\s+licence\s+unknown", re.I)),
    ("OLD_ALL_CC0_CREDITS", re.compile(r"Files\s+from\s+Kenney,\s+OpenGameArt\s+authors\s+and\s+BigSoundBank,\s+all\s+CC0", re.I)),
    ("OLD_PROTOTYPE_GIF", re.compile(r"all_heroes_idle_quad\.gif|svg_scene_gameplay_showcase\.gif", re.I)),
    ("MANGLED_NOT_PUBLISHED_TESTS", re.compile(r"200\+\s+`?\(not\s+published\)`?\s+files", re.I)),
    ("LAN_IP_LEAK", re.compile(r"\b192\.168\.\d+\.\d+\b")),
    ("LOCAL_USER_PATH", re.compile(r"/Use" r"rs/[^/\s\"')]+")),
]


def iter_targets(root: Path, include_drafts: bool) -> list[Path]:
    candidates = [
        root / "README.md",
        root / "JUDGES.md",
        root / "CREDITS.md",
        root / "docs" / "KIRO_USAGE_20261116.md",
        root / "docs" / "ARCHITECTURE_FULL_20261124.md",
        root / "docs" / "mcp_agent_protocol.md",
        root / "docs" / "HOST_AGENT_HOWTO.md",
        root / "docs" / "ASSET_PROVENANCE.md",
        root / "docs" / "room_flow_gap_table_20261125.md",
        root / ".kiro" / "powers" / "pumpkin-killer-seat" / "skills" / "play" / "SKILL.md",
    ]
    if include_drafts:
        drafts = root / "docs" / "release_drafts"
        if drafts.is_dir():
            candidates.extend(sorted(drafts.glob("*.md")))
            gallery = drafts / "gallery"
            if gallery.is_dir():
                candidates.extend(sorted(gallery.glob("*.svg")))
    return [p for p in candidates if p.is_file()]


def scan_root(root: Path, include_drafts: bool) -> list[str]:
    findings: list[str] = []
    for path in iter_targets(root, include_drafts):
        rel = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for lineno, line in enumerate(lines, 1):
            for tag, rx in BANNED_RULES:
                if rx.search(line):
                    # Allow explicit historical explanation mentioning ref_bar_from_video was removed
                    if tag == "OLD_REF_BAR_CREDITS" and "deleted" in line.lower():
                        continue
                    findings.append(f"{rel}:{lineno} [{tag}] {line.strip()[:140]}")
        if path.name == "mcp.json":
            pass
    mcp_json = root / ".kiro" / "powers" / "pumpkin-killer-seat" / "mcp.json"
    if mcp_json.is_file() and "--room-tools" not in mcp_json.read_text(encoding="utf-8"):
        findings.append(".kiro/powers/pumpkin-killer-seat/mcp.json:1 [MISSING_ROOM_TOOLS_FLAG] --room-tools absent")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--v3", default="")
    args = ap.parse_args()
    all_findings = []
    dev_root = Path(args.root).resolve()
    for f in scan_root(dev_root, include_drafts=True):
        all_findings.append(f"dev/{f}")
    if args.v3:
        v3_root = Path(args.v3).resolve()
        for f in scan_root(v3_root, include_drafts=False):
            all_findings.append(f"v3/{f}")
    if all_findings:
        for line in all_findings:
            print("FAIL", line)
        print(f"AUDIT FAILED: {len(all_findings)} findings")
        return 1
    print("AUDIT PASS: 0 findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
