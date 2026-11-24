#!/usr/bin/env python3
"""Pose audit (owner 2026-11-16: every hero needs a wind-up and a charge animation).

For every hero: which animation states the PAGE can show (read from POSE_SETS in index.html: windup = wind-up, charge2 = late charge frame, release, hit, idle2, ult),
which picture files exist, and whether each pose picture really differs from the hero's idle (silhouette difference, feet aligned; a value under 0.04 = a copy of the idle).
Writes docs/POSE_AUDIT_20261116.md. Exit code 1 when a hero lacks wind-up, release or hit in the page, or a pose picture is a copy. One summary line per hero.
Usage: python3 -B scripts/pose_audit.py
"""
import os
import re
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEROES = {   # hero id -> (imgKey in the page, idle picture, files that count as its action pictures)
    "skeleton": ("unit_skeleton", "assets/units/unit_skeleton.png", ["assets/poses/skel_windup.png", "assets/poses/skel_release.png", "assets/poses/skel_hit.png"]),
    "wizard": ("unit_wizard", "assets/units/unit_wizard.png", ["assets/poses/wizard_charge1.png", "assets/poses/wizard_charge2.png", "assets/poses/wizard_charge3.png", "assets/poses/wizard_hit.png"]),
    "bat": ("unit_bat", "assets/units/unit_bat.png", ["assets/poses/bat_draw.png", "assets/poses/bat_windup.png", "assets/poses/bat_release.png", "assets/poses/bat_hit.png"]),
    "knight": ("unit_knight", "assets/units/unit_knight.png", ["assets/poses/knight_unarmed_windup.png", "assets/poses/knight_unarmed_release.png", "assets/poses/knight_unarmed_hit.png"]),
    "reaper": ("unit_reaper", "assets/poses/necro_idle.png", ["assets/poses/necro_windup.png", "assets/poses/necro_charge2.png", "assets/poses/necro_release.png", "assets/poses/necro_hit.png"]),
    "bride": ("unit_bride", "assets/poses/bride_idle1.png", ["assets/poses/bride_windup.png", "assets/poses/bride_release_new.png", "assets/poses/bride_hit_new.png"]),
    "hunchback": ("unit_hunchback", "assets/poses/hunchback_idle1.png", ["assets/poses/hunchback_unarmed.png", "assets/poses/hunchback_windup.png", "assets/poses/hunchback_release_new.png", "assets/poses/hunchback_hit_new.png"]),
    "hag": ("unit_hag", "assets/units/unit_hag_idle.png", ["assets/poses/hag_charge1.png", "assets/poses/hag_charge2.png", "assets/poses/hag_charge3.png", "assets/poses/hag_release.png", "assets/poses/hag_hit.png"]),
}
NEED = ("windup", "release", "hit")


def silhouette(path):
    a = np.asarray(Image.open(path).convert("RGBA").getchannel("A")) > 24
    ys, xs = np.where(a)
    if not len(ys):
        return None
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def pose_diff(idle_path, pose_path):
    a, b = silhouette(idle_path), silhouette(pose_path)
    if a is None or b is None:
        return None
    h = max(a.shape[0], b.shape[0]); w = max(a.shape[1], b.shape[1])
    def pad(m):   # feet aligned (bottom), centred horizontally
        out = np.zeros((h, w), bool)
        y0 = h - m.shape[0]; x0 = (w - m.shape[1]) // 2
        out[y0:y0 + m.shape[0], x0:x0 + m.shape[1]] = m
        return out
    pa, pb = pad(a), pad(b)
    union = (pa | pb).sum()
    return 1.0 - ((pa & pb).sum() / union if union else 1.0)


def main():
    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = re.search(r"const POSE_SETS = \{(.*?)\n    \};", html, re.S)
    sets = {}
    for line in (m.group(1).splitlines() if m else []):
        mm = re.match(r"\s*(unit_\w+):\s*\{(.*?)\}", line)
        if mm:
            sets[mm.group(1)] = set(re.findall(r"(\w+):\s*\"(?:pose|unit)_", mm.group(2)))
    rows, bad = [], 0
    for hero, (key, idle, files) in HEROES.items():
        states = sets.get(key, set())
        missing = [n for n in NEED if n not in states]
        diffs = []
        for f in files:
            p = os.path.join(ROOT, f)
            d = pose_diff(os.path.join(ROOT, idle), p) if os.path.exists(p) and os.path.exists(os.path.join(ROOT, idle)) else None
            diffs.append((os.path.basename(f), d))
        copies = [n for n, d in diffs if d is not None and d < 0.04]
        absent = [n for n, d in diffs if d is None]
        if missing or copies:
            bad += 1
        rows.append((hero, sorted(states), missing, diffs, copies, absent))
        print("%-9s page states: %-40s missing in page: %-22s copies: %s" % (hero, ",".join(sorted(states)) or "none", ",".join(missing) or "-", ",".join(copies) or "-"))
    lines = ["# Pose audit 2026-11-16 (scripts/pose_audit.py, facts from index.html and the picture files)", "",
             "windup = wind-up frame, charge2 = late charge frame; 'diff' = how much the picture's silhouette differs from the idle (under 0.04 = a copy of the idle).", "",
             "| Hero | States the page can show | Missing in the page | Picture files: diff against idle | Copies / absent |", "|---|---|---|---|---|"]
    for hero, states, missing, diffs, copies, absent in rows:
        lines.append("| %s | %s | %s | %s | %s |" % (hero, ", ".join(states) or "none", ", ".join(missing) or "-",
                     "; ".join("%s %s" % (n, "-" if d is None else "%.2f" % d) for n, d in diffs), ", ".join(copies + absent) or "-"))
    open(os.path.join(ROOT, "docs", "POSE_AUDIT_20261116.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
