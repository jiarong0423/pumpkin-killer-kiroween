#!/usr/bin/env python3
"""Count the Kiro evidence in this repository. Read only: it opens files and writes nothing.

Usage: python3 -B scripts/release/tech_evidence_counts.py [--root DIR]
Prints one line per area (ledger, specs, hooks, steering, agents, powers, mcp, briefs, evidence). Exit 0.
The numbers come from the files, never from memory; docs/kiro_evidence/TECH_EVIDENCE_20261115.md quotes this output.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

EVIDENCE_FILES = [
    "docs/kiro_evidence/raw/ide_hook_run_20261115.txt",
    "docs/kiro_evidence/raw/ide_hook_run_20261115.jpg",
    "docs/kiro_evidence/raw/ide_mcp_attempt_20261115.txt",
    "docs/kiro_evidence/raw/ide_mcp_attempt_20261115.jpg",
    "docs/kiro_evidence/raw/mcp_health_20261115.log",
    "docs/kiro_evidence/raw/powers_install_20261115.txt",
    "docs/kiro_evidence/raw/hook_runs.log",
    "docs/kiro_evidence/IDE_SESSION_20261115.md",
    "docs/kiro_evidence/2026-11-15_tests.md",
    "docs/KIRO_LEDGER.md",
    "docs/kiro_verified.json",
    "docs/PROMPT_LOG.md",
]


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def ledger(root: Path) -> str:
    try:
        data = json.loads(read(root / "docs/kiro_verified.json"))
    except json.JSONDecodeError:
        return "ledger entries=? (docs/kiro_verified.json is not valid JSON)"
    entries = {k: v for k, v in data.items() if not k.startswith("_")}
    counts = Counter(str(v.get("status", "?")) if isinstance(v, dict) else "?" for v in entries.values())
    parts = " ".join(f"{name}={counts[name]}" for name in sorted(counts))
    return f"ledger entries={len(entries)} {parts}"


def specs(root: Path) -> list[str]:
    base = root / ".kiro" / "specs"
    folders = sorted(p for p in base.iterdir() if p.is_dir()) if base.is_dir() else []
    triples = ticked = opened = 0
    lines = []
    for folder in folders:
        has = [(folder / f"{name}.md").is_file() for name in ("requirements", "design", "tasks")]
        triples += all(has)
        text = read(folder / "tasks.md")
        t = len(re.findall(r"^\s*[-*] \[x\]", text, re.M | re.I))
        o = len(re.findall(r"^\s*[-*] \[ \]", text, re.M))
        ticked += t
        opened += o
        if not all(has):
            lines.append(f"specs incomplete folder={folder.name} requirements/design/tasks={has}")
    return [f"specs folders={len(folders)} with_requirements_design_tasks={triples} boxes_ticked={ticked} boxes_open={opened}"] + lines


def hooks(root: Path) -> list[str]:
    base = root / ".kiro" / "hooks"
    json_files = sorted(base.glob("*.json")) if base.is_dir() else []
    old_format = sorted(base.glob("*.kiro.hook")) if base.is_dir() else []
    triggers: Counter[str] = Counter()
    names = []
    for path in json_files:
        try:
            data = json.loads(read(path))
        except json.JSONDecodeError:
            continue
        for hook in data.get("hooks", []):
            triggers[str(hook.get("trigger", "?"))] += 1
            names.append(str(hook.get("name", path.stem)))
    trig = " ".join(f"{k}={v}" for k, v in sorted(triggers.items()))
    return [f"hooks json_files={len(json_files)} hooks={len(names)} triggers: {trig} old_format_kiro_hook_files={len(old_format)}"]


def steering(root: Path) -> str:
    base = root / ".kiro" / "steering"
    files = sorted(base.glob("*.md")) if base.is_dir() else []
    always = [f.name for f in files if re.search(r"inclusion:\s*always", read(f)[:400])]
    return f"steering files={len(files)} inclusion_always={len(always)} ({', '.join(always)})"


def agents(root: Path) -> str:
    base = root / ".kiro" / "agents"
    files = sorted(base.glob("*.json")) if base.is_dir() else []
    mcp_attached = 0
    for f in files:
        try:
            if json.loads(read(f)).get("mcpServers"):
                mcp_attached += 1
        except json.JSONDecodeError:
            pass
    return f"agents files={len(files)} names={','.join(f.stem for f in files)} attach_mcp_server={mcp_attached}"


def powers(root: Path) -> str:
    base = root / ".kiro" / "powers"
    folders = sorted(p for p in base.iterdir() if p.is_dir()) if base.is_dir() else []
    return f"powers folders={len(folders)} names={','.join(p.name for p in folders)}"


def mcp(root: Path) -> str:
    try:
        data = json.loads(read(root / ".kiro" / "settings" / "mcp.json"))
    except json.JSONDecodeError:
        return "mcp servers=? (.kiro/settings/mcp.json is not valid JSON)"
    servers = data.get("mcpServers", {})
    tools = len(re.findall(r'"name":\s*"(?:get_public_state|get_history|submit_action|end_turn|set_notes|get_notes)"', read(root / "scripts" / "mcp_stdio_server.py")))
    return f"mcp servers={len(servers)} names={','.join(sorted(servers))} tool_names_found_in_server_file={tools}"


def briefs(root: Path) -> str:
    docs = root / "docs"
    task_files = len(list(docs.glob("kiro_task_*.md")))
    results = len(list(docs.glob("kiro_*_result_*.md")))
    return f"briefs task_files={task_files} result_files={results}"


def evidence(root: Path) -> list[str]:
    have = [p for p in EVIDENCE_FILES if (root / p).is_file()]
    lines = [f"evidence files_present={len(have)} of {len(EVIDENCE_FILES)}"]
    lines += [f"evidence missing {p}" for p in EVIDENCE_FILES if p not in have]
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="repository root")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    lines = [ledger(root), *specs(root), *hooks(root), steering(root), agents(root), powers(root), mcp(root), briefs(root), *evidence(root)]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
