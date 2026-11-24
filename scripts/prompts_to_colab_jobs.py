#!/usr/bin/env python3
"""Turn the image2 prompt files written by Kiro into one Colab job queue (owner 2026-11-15: "just give the prompts Kiro wrote to Colab").

Reads docs/*_image2_prompts_20261115.md: a heading with the picture id in backticks, an optional "Attach"/"WHAT to attach" line, then the first fenced block = the prompt.
Writes colab/jobs_queue_round3_20261115.json (refs table + jobs). One reference per job (the L4 runs out of memory with two).
Usage: python3 -B scripts/prompts_to_colab_jobs.py [--out PATH]
"""
import argparse, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = [  # (file, ids to take or None for all, kind)
    ("docs/hag_image2_prompts_20261115.md", {"hag_idle1", "hag_front", "proj_cross", "fx_cross_rain", "fx_cross_rain_heal", "fx_black_smoke"}, "char"),   # the other nun frames need the chosen idle picture first
    ("docs/scene_image2_prompts_20261115.md", None, "scene"),
    ("docs/gap_image2_prompts_20261115.md", None, "gap"),
]
STAGE2 = {"hag_idle2", "hag_charge1", "hag_charge2", "hag_charge3", "hag_release", "hag_empty", "hag_hit",
          "hand_1_reach_to_chest", "hand_2_grip_cross", "hand_3_pull_back", "hand_4_snap_forward", "hand_5_release_open", "hand_6_empty_relaxed"}
SKIP_NOTES = ("(conditional)",)
HEAD = re.compile(r"^#{2,3}\s+`([A-Za-z0-9_]+)`(.*)$")
PATH = re.compile(r"`([^`\s]+\.(?:png|webp|jpg))`")
LOG = []


def find_path(name):
    if os.path.exists(os.path.join(ROOT, name)):
        return name
    base = os.path.basename(name)
    alias = {"ref_bg_graveyard.png": "assets/env/bg_graveyard.png", "ref_concept_mockup.png": "docs/ref/concept_mockup.png"}
    if base in alias:
        return alias[base]
    for d in ("assets/units", "assets/poses", "assets/weapons", "assets/fx/sprites", "assets/ui", "assets/portraits", "assets/env"):
        if os.path.exists(os.path.join(ROOT, d, base)):
            return d + "/" + base
    return None


def choose_ref(attach_line):
    cands = []
    for seg in re.split(r";", attach_line):
        for m in PATH.findall(seg):
            p = find_path(m)
            if p:
                cands.append((p, ("identity" in seg.lower() or "exact" in seg.lower())))
    if not cands:
        return None
    for p, ident in cands:
        if ident:
            return p
    return cands[0][0]


def parse(path, only, kind):
    lines = open(os.path.join(ROOT, path), encoding="utf-8").read().split("\n")
    jobs, i = [], 0
    while i < len(lines):
        m = HEAD.match(lines[i])
        if not m:
            i += 1
            continue
        jid, tail = m.group(1), m.group(2)
        j = i + 1
        attach = ""
        while j < len(lines) and not lines[j].startswith("```") and not HEAD.match(lines[j]) and not lines[j].startswith("## "):
            if "ttach" in lines[j]:
                attach += " " + lines[j]
            j += 1
        if j < len(lines) and lines[j].startswith("```"):
            k = j + 1
            body = []
            while k < len(lines) and not lines[k].startswith("```"):
                body.append(lines[k]); k += 1
            prompt = " ".join(x.strip() for x in body).strip()
            skip = any(s in tail for s in SKIP_NOTES) or (only is not None and jid not in only)
            if skip or not prompt:
                LOG.append("skip %s" % jid)
            else:
                jobs.append({"id": jid, "kind": kind, "prompt": prompt, "attach": attach})
            i = k + 1
        else:
            i = j
    return jobs


def stage2(a):
    jobs = []
    for pj in parse("docs/hag_image2_prompts_20261115.md", STAGE2, "char"):
        jobs.append({"id": pj["id"], "tier": "Q3", "ref": "out:" + a.stage2_idle, "prompt": pj["prompt"], "style": " ", "negative": " "})
    out = {"refs": {}, "style": " ", "jobs": jobs}
    json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=1)
    print("stage 2 jobs", len(jobs), "reference out:" + a.stage2_idle)
    for j in jobs:
        print(" ", j["id"])
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "colab/jobs_queue_round3_20261115.json"))
    ap.add_argument("--stage2-idle", default="", help="file name of the chosen idle picture in the Drive out folder (for example hag_idle1_v1_p3.png): writes ONLY the nun pose and hand jobs that use it as their reference")
    a = ap.parse_args()
    if a.stage2_idle:
        return stage2(a)
    base = json.load(open(os.path.join(ROOT, "colab/jobs_apple_hag_20261115.json")))
    refs = {"style_wizard_unit": "assets/units/unit_wizard.png"}
    jobs, seen = [], set()
    for path, only, kind in SOURCES:
        for pj in parse(path, only, kind):
            if pj["id"] in seen:
                LOG.append("duplicate %s" % pj["id"]); continue
            seen.add(pj["id"])
            ref = choose_ref(pj["attach"]) or "assets/units/unit_wizard.png"
            name = "ref_" + re.sub(r"[^a-z0-9]+", "_", ref.lower()).strip("_")
            refs[name] = ref
            job = {"id": pj["id"], "tier": "Q3", "ref": name, "prompt": pj["prompt"], "style": " ", "negative": " "}
            if pj["kind"] == "scene":
                job["w"], job["h"] = 1024, 576   # 16:9, small enough for the L4
            jobs.append(job)
    out = {"refs": refs, "style": " ", "jobs": jobs}
    json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=1)
    print("jobs", len(jobs), "refs", len(refs))
    for j in jobs:
        print(" ", j["id"], "->", refs[j["ref"]])
    for l in LOG:
        print(" ", l)
    miss = [p for p in refs.values() if not os.path.exists(os.path.join(ROOT, p))]
    if miss:
        print("MISSING refs", miss); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
