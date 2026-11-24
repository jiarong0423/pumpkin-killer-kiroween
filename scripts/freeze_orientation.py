#!/usr/bin/env python3
"""Freeze the confirmed orientation decisions (owner 2026-11-16: "fix the objects you are sure of so nothing needs another horizontal flip").
Writes shared/orientation_frozen.json: (1) ART_FACES_RIGHT as it is in index.html, (2) the sha256 of every picture under assets/poses and assets/units
(the pictures whose facing matters), (3) the code markers of the wind ghost binding. scripts/test_orientation_frozen.js compares the repository with this file.
If a picture is replaced ON PURPOSE: check its facing first (native art faces LEFT; the page mirrors the player's side), then run
`python3 -B scripts/freeze_orientation.py --write`. Without --write it only prints the differences (exit 1 when there are any)."""
import glob, hashlib, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "shared", "orientation_frozen.json")

def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()

def current():
    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = re.search(r"const ART_FACES_RIGHT = \{([^}]*)\}", html)
    faces = {k: v == "true" for k, v in re.findall(r"(\w+):\s*(true|false)", m.group(1))}
    pics = {}
    for folder in ("assets/poses", "assets/units"):
        for p in sorted(glob.glob(os.path.join(ROOT, folder, "*.png"))):
            pics[os.path.relpath(p, ROOT)] = sha(p)
    markers = ["ctx.scale(dir, 1);   // bound to the wind", "dir = effWind() >= 0 ? 1 : -1"]
    return {"version": 1, "note": "native art faces LEFT; the page mirrors the player's side; hunchback frames were mirrored on 2026-11-16 (ART_FACES_RIGHT.unit_hunchback true and assets/poses/hunchback_windup.png flipped)",
            "art_faces_right": faces, "pictures": pics, "wind_ghost_markers": markers}

def main():
    cur = current()
    if "--write" in sys.argv:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump(cur, open(OUT, "w", encoding="utf-8"), indent=1, sort_keys=True); open(OUT, "a").write("\n")
        print("wrote", OUT, "pictures:", len(cur["pictures"])); return 0
    old = json.load(open(OUT, encoding="utf-8"))
    bad = 0
    if old["art_faces_right"] != cur["art_faces_right"]:
        print("DIFF ART_FACES_RIGHT", old["art_faces_right"], cur["art_faces_right"]); bad += 1
    for k in sorted(set(old["pictures"]) | set(cur["pictures"])):
        if old["pictures"].get(k) != cur["pictures"].get(k):
            print("DIFF picture", k); bad += 1
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
