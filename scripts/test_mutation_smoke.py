#!/usr/bin/env python3
"""Prove five important constants are detected when a temporary copy drifts."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def copy_minimal_repo(destination):
    (destination / "scripts").mkdir(parents=True)
    for source in (ROOT / "scripts").glob("*.py"):
        shutil.copy2(source, destination / "scripts" / source.name)
    shutil.copytree(ROOT / "shared", destination / "shared")
    shutil.copy2(ROOT / "index.html", destination / "index.html")
    (destination / "assets").mkdir()
    shutil.copytree(ROOT / "assets" / "i18n", destination / "assets" / "i18n")


def replace_once(path, old, new):
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise AssertionError("expected one %r in %s, found %d" % (old, path, text.count(old)))
    path.write_text(text.replace(old, new), encoding="utf-8")


def mutate_json(path, key_path, value):
    data = json.loads(path.read_text(encoding="utf-8"))
    target = data
    for key in key_path[:-1]:
        target = target[key]
    target[key_path[-1]] = value
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def check(name, mutate, command):
    with tempfile.TemporaryDirectory(prefix="pk-mutation-") as raw:
        repo = Path(raw) / "repo"
        copy_minimal_repo(repo)
        mutate(repo)
        result = subprocess.run(command, cwd=repo, text=True, capture_output=True)
        if result.returncode == 0:
            raise AssertionError("%s mutation escaped %s" % (name, " ".join(command)))
    print("MUTATION FAIL DETECTED: %s" % name)


def main():
    checks = [
        ("ultimate multiplier", lambda repo: replace_once(
            repo / "scripts" / "mcp_game_server.py", "1.5 / 3", "1.4 / 3"),
         [sys.executable, "-B", "scripts/test_mcp_skills_ultimates.py"]),
        ("shield wall expiry", lambda repo: mutate_json(
            repo / "shared" / "constants.json", ["SHIELD_WALL_EXPIRES_AFTER_ATTACKS"], 2),
         [sys.executable, "-B", "scripts/test_shield_wall.py"]),
        ("burn turns", lambda repo: mutate_json(
            repo / "shared" / "heroes.json", ["reaper", "statusOnHit", "burn", "turns"], 2),
         [sys.executable, "-B", "scripts/test_mcp_game.py"]),
        ("lifesteal share", lambda repo: replace_once(
            repo / "index.html", "LIFESTEAL_SHARE = 0.05", "LIFESTEAL_SHARE = 0.06"),
         ["node", "scripts/test_decisions_frozen.js"]),
        ("reaper hit half-width", lambda repo: mutate_json(
            repo / "shared" / "heroes.json", ["reaper", "hitBox", "halfWidth"], 58),
         [sys.executable, "-B", "scripts/test_mcp_game.py"]),
    ]
    for name, mutate, command in checks:
        check(name, mutate, command)
    print("test_mutation_smoke: 5/5 mutations detected")


if __name__ == "__main__":
    main()
