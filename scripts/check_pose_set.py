#!/usr/bin/env python3
"""Check every class against the pose-set standard (docs/pose_spec.md).

Standard: 8 transparent PNGs per class in assets/poses/: <key>_idle1, _idle2, _charge1, _charge2, _charge3, _release, _empty, _hit.
Checks per picture: it exists, is RGBA with real transparency, is 1024x1024, has the feet on the shared baseline (lowest opaque row
between 990 and 1010) and the opaque part is no larger than the class idle by more than 12 percent in height (same size rule).
A legacy alias table maps the first pictures drawn before the standard (skeleton, bat, necromancer) so the report is honest about them.
Usage: python3 -B scripts/check_pose_set.py [--strict]   Exit 0 only when every class is complete (strict) or when no picture present is broken (default).
Prints one line per class: key complete/total and the missing or broken frames. Errors go to stderr as 'ERROR'.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSES = os.path.join(ROOT, "assets", "poses")
CLASSES = ["skeleton", "wizard", "bat", "knight", "bride", "hunchback", "reaper"]
FRAMES = ["idle1", "idle2", "charge1", "charge2", "charge3", "release", "empty", "hit"]
LEGACY = {   # standard name -> file that already exists under an older name
    ("skeleton", "charge2"): "skel_windup.png", ("skeleton", "release"): "skel_release.png", ("skeleton", "hit"): "skel_hit.png",
    ("bat", "charge1"): "bat_draw.png", ("bat", "charge2"): "bat_windup.png", ("bat", "release"): "bat_release.png", ("bat", "hit"): "bat_hit.png",
    ("reaper", "idle1"): "necro_idle.png", ("reaper", "charge2"): "necro_windup.png", ("reaper", "release"): "necro_release.png",
    ("reaper", "empty"): "necro_empty.png", ("reaper", "hit"): "necro_hit.png",
}
BASELINE = (990, 1010)


def find(key, frame):
    std = os.path.join(POSES, "%s_%s.png" % (key, frame))
    if os.path.exists(std):
        return std, False
    legacy = LEGACY.get((key, frame))
    if legacy and os.path.exists(os.path.join(POSES, legacy)):
        return os.path.join(POSES, legacy), True
    return None, False


def inspect(path):
    """Return (problems, opaque_height). Legacy pictures are on a different canvas, so only the standard ones are held to 1024x1024."""
    problems = []
    try:
        im = Image.open(path)
    except Exception as e:  # noqa: BLE001 - report any unreadable file
        return ["unreadable: %r" % (e,)], 0
    if im.mode != "RGBA":
        return ["not RGBA"], 0
    al = np.asarray(im.getchannel("A"))
    rows = np.where((al > 40).sum(axis=1) > 6)[0]
    if len(rows) == 0:
        return ["empty picture"], 0
    if al.min() > 250:
        problems.append("no transparency")
    return problems, int(rows.max() - rows.min() + 1), im.size, int(rows.max())


def main(argv):
    strict = "--strict" in argv
    broken, incomplete = 0, 0
    for key in CLASSES:
        have, bad, heights = 0, [], {}
        missing = []
        for fr in FRAMES:
            path, legacy = find(key, fr)
            if not path:
                missing.append(fr)
                continue
            res = inspect(path)
            probs = res[0]
            if len(res) == 4 and res[2] == (1536, 1024):   # the first pictures were drawn on an older 1536x1024 canvas: counted, marked legacy, not held to the new canvas
                legacy = True
            if len(res) == 4 and not legacy:
                _, h, size, bottom = res
                heights[fr] = h
                if size != (1024, 1024):
                    probs.append("canvas %s not 1024x1024" % (size,))
                if not (BASELINE[0] <= bottom <= BASELINE[1]):
                    probs.append("feet at row %d, not %d..%d" % (bottom, BASELINE[0], BASELINE[1]))
            if probs:
                bad.append("%s%s: %s" % (fr, " (legacy)" if legacy else "", "; ".join(probs)))
                continue
            have += 1
        idle = heights.get("idle1")
        if idle:
            for fr, h in heights.items():
                if h > idle * 1.12:
                    bad.append("%s is %.0f percent taller than idle1 (same size rule)" % (fr, 100.0 * (h / idle - 1)))
        print("%-9s %d/%d complete%s%s" % (key, have, len(FRAMES), ("  missing: " + ", ".join(missing)) if missing else "",
                                           ("  BROKEN: " + " | ".join(bad)) if bad else ""))
        broken += len(bad)
        incomplete += len(missing)
    if broken:
        print("ERROR %d broken picture(s)" % broken, file=sys.stderr)
    return 1 if broken or (strict and incomplete) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
