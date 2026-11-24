#!/usr/bin/env python3
"""Report discontinuities in installed animation strips; this is advisory, never a gate."""
import argparse
import json
import os
import re
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import pose_similarity as similarity  # noqa: E402

FACE_SIM_MIN = similarity.TH["face_sim"]
FACE_ORB_MIN = similarity.TH["face_orb"]
SCALE_LO = similarity.TH["scale_lo"]
SCALE_HI = similarity.TH["scale_hi"]
FEET_SHIFT_MAX = 10
COPY_DIFF_MAX = similarity.TH["copy_diff"]
COPY_SHIFT_MAX = 3.0


def log(message, handle):
    handle.write(message + "\n")
    handle.flush()
    print(message, file=sys.stderr)


def ordered_strips(poses_dir, wanted_class="", wanted_strip=""):
    pattern = re.compile(r"([A-Za-z0-9-]+)_(idle_loop|charge|throw|hit)_(\d+)\.png$")
    groups = {}
    if not os.path.isdir(poses_dir):
        return groups
    for name in os.listdir(poses_dir):
        match = pattern.fullmatch(name)
        if not match:
            continue
        cls, strip, number = match.groups()
        if (wanted_class and cls != wanted_class) or (wanted_strip and strip != wanted_strip):
            continue
        groups.setdefault((cls, strip), []).append((int(number), os.path.join(poses_dir, name)))
    return {key: [path for _, path in sorted(items)] for key, items in groups.items()}


def metrics(first, second):
    result = similarity.compare(first, second)
    if "error" in result:
        return result
    _, first_mask = similarity.load_keyed(first)
    _, second_mask = similarity.load_keyed(second)
    first_box, second_box = similarity.bbox(first_mask), similarity.bbox(second_mask)
    if not first_box or not second_box:
        return {"error": "empty silhouette"}
    first_bottom, second_bottom = first_box[3] - 1, second_box[3] - 1
    first_centre = ((first_box[0] + first_box[2]) / 2.0, (first_box[1] + first_box[3]) / 2.0)
    second_centre = ((second_box[0] + second_box[2]) / 2.0, (second_box[1] + second_box[3]) / 2.0)
    result["feet_shift_px"] = round(second_bottom - first_bottom, 2)
    result["opaque_box_centre_shift_px"] = round(float(np.hypot(second_centre[0] - first_centre[0], second_centre[1] - first_centre[1])), 2)
    result["motion_score"] = round(result["pose_diff"] + abs(result["scale"] - 1.0) + abs(result["feet_shift_px"]) / 100.0 + result["opaque_box_centre_shift_px"] / 100.0, 4)
    return result


def violation_flags(record):
    if "error" in record:
        return ["ERROR"]
    flags = []
    if record["face_sim"] < FACE_SIM_MIN and record["face_orb"] < FACE_ORB_MIN:
        flags.append("FACE")
    if not SCALE_LO <= record["scale"] <= SCALE_HI:
        flags.append("SCALE")
    if abs(record["feet_shift_px"]) > FEET_SHIFT_MAX:
        flags.append("FEET")
    return flags


def analyse_strip(paths, loop):
    names = [os.path.splitext(os.path.basename(path))[0] for path in paths]
    steps = []
    for index in range(len(paths) - 1):
        result = metrics(paths[index], paths[index + 1])
        result.update({"from": names[index], "to": names[index + 1], "kind": "step", "flags": violation_flags(result)})
        steps.append(result)
    valid_scores = [step["motion_score"] for step in steps if "motion_score" in step]
    median = float(np.median(valid_scores)) if valid_scores else 0.0
    threshold = median * 3.0
    for step in steps:
        if "motion_score" in step and step["motion_score"] > max(threshold, 0.001):
            step["flags"].append("JUMP")
    loop_step = None
    if loop and len(paths) > 1:
        loop_step = metrics(paths[-1], paths[0])
        loop_step.update({"from": names[-1], "to": names[0], "kind": "loop_close", "flags": violation_flags(loop_step)})
        if "motion_score" in loop_step and loop_step["motion_score"] > max(threshold, 0.001):
            loop_step["flags"].append("JUMP")
    copies = []
    for first in range(len(paths)):
        for second in range(first + 2, len(paths)):
            # A loop's last-to-first similarity belongs to its closing report, not COPY.
            if loop and first == 0 and second == len(paths) - 1:
                continue
            result = metrics(paths[first], paths[second])
            if "error" not in result and result["pose_diff"] <= COPY_DIFF_MAX and abs(result["feet_shift_px"]) <= COPY_SHIFT_MAX and result["opaque_box_centre_shift_px"] <= COPY_SHIFT_MAX:
                result.update({"from": names[first], "to": names[second], "kind": "copy", "flags": ["COPY"]})
                copies.append(result)
    return {"frames": names, "median_step": round(median, 4), "steps": steps, "loop_close": loop_step, "copies": copies}


def print_table(key, report, handle):
    log("%s  median step %.4f" % (key, report["median_step"]), handle)
    log("  from -> to                         face  orb  palette scale head pose  feet centre flags", handle)
    rows = report["steps"] + ([report["loop_close"]] if report["loop_close"] else []) + report["copies"]
    for row in rows:
        if "error" in row:
            log("  %-34s ERROR %s" % (row["from"] + " -> " + row["to"], row["error"]), handle)
            continue
        log("  %-34s %5.2f %4d %7.2f %5.2f %4.2f %4.2f %5.1f %6.1f %s" % (
            row["from"] + " -> " + row["to"], row["face_sim"], row["face_orb"], row["palette_sim"], row["scale"], row["head_scale"], row["pose_diff"], row["feet_shift_px"], row["opaque_box_centre_shift_px"], ",".join(row["flags"]) or "-"), handle)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--poses-dir", default=os.path.join(ROOT, "assets", "poses"))
    parser.add_argument("--class", dest="class_name", default="")
    parser.add_argument("--strip", default="")
    parser.add_argument("--json", default="continuity.json")
    parser.add_argument("--log", default="")
    args = parser.parse_args(argv)
    log_path = args.log or os.path.splitext(args.json)[0] + ".log"
    os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
    result = {"strips": {}}
    with open(log_path, "a", encoding="utf-8") as handle:
        strips = ordered_strips(args.poses_dir, args.class_name, args.strip)
        if not strips:
            log("ERROR no matching installed strips in " + args.poses_dir, handle)
        for (cls, strip), paths in sorted(strips.items()):
            report = analyse_strip(paths, strip == "idle_loop")
            key = cls + ":" + strip
            result["strips"][key] = report
            print_table(key, report, handle)
    with open(args.json, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
