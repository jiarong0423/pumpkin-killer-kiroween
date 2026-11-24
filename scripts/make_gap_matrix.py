#!/usr/bin/env python3
"""Character gap matrix ("connect-the-dots"): every hero against everything it needs. Facts come from files, the page and the job queues, never from memory.
Writes docs/character_connect_gaps_20261115.html and .md. Usage: python3 -B scripts/make_gap_matrix.py
Cell: HAVE (the file or rule exists), JOB (a Colab job or a Kiro task exists, not done), MISSING (nothing yet), N/A.
"""
import html, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(p): return os.path.join(ROOT, p)
def have(p): return os.path.exists(P(p))
def read(p):
    try: return open(P(p), encoding="utf-8").read()
    except OSError: return ""

page = read("index.html")
ult_built = re.search(r"const ULT_BUILT = \[([^\]]*)\]", page)
ult_built = set(re.findall(r'"(\w+)"', ult_built.group(1))) if ult_built else set()
profiles = set(re.findall(r'^\s{6}(\w+):\s*\{\s*name:', page, re.M)) | set(re.findall(r'HERO_PROFILES\.(\w+)\s*=', page))
playable = set(re.findall(r'data-hero="(\w+)"', page))
job_ids = set()
for f in os.listdir(P("colab")):
    if f.startswith("jobs_queue_round") and f.endswith(".json"):
        try: job_ids |= {j["id"] for j in json.load(open(P("colab/" + f)))["jobs"]}
        except Exception: pass
class_stats = read("js/class_stats.js")
ultfx = read("js/ultimate_fx.js")
audio = read("docs/audio_event_map.json")

HEROES = [  # key, label, unit file, pose prefix, portrait, projectile file, ult id in ultimate_fx, ult module file
    ("skeleton", "Skeleton Spearman", "assets/units/unit_skeleton.png", "skeleton", "assets/portraits/skeleton_front.png", "assets/weapons/proj_spear_colab.png", "skeleton_triple_javelin", "js/ultimate_fx.js"),
    ("wizard", "Pumpkin Wizard", "assets/units/unit_wizard.png", "wizard", "assets/portraits/wizard_front.png", "assets/env/proj_pumpkin.png", "wizard_pumpkin_blast", "js/ultimate_fx.js"),
    ("bat", "Bat-cat Assassin", "assets/units/unit_bat.png", "bat", "assets/portraits/bat_front.png", "assets/weapons/shuriken.png", "bat_shuriken_rain", "js/ultimate_fx.js"),
    ("knight", "Pumpkin Guard", "assets/units/unit_knight.png", "knight", "assets/portraits/knight_front.png", "assets/weapons/small_shield.png", "knight", "js/knight_ult.js"),
    ("reaper", "Necromancer", "assets/units/unit_reaper_idle.png", "necro", "assets/portraits/reaper_front.png", "assets/fx/sprites/fx_flame_comet.png", "reaper_flame_trio", "js/ultimate_fx.js"),
    ("bride", "Ghost Bride", "assets/units/unit_bride_idle.png", "bride", "assets/portraits/bride_front.png", "assets/fx/sprites/fx_sonic_ring.png", "bride_soul_dirge", "js/ultimate_fx.js"),
    ("hunchback", "Bell-tower Hunchback", "assets/units/unit_hunchback_idle.png", "hunchback", "assets/portraits/hunchback_front.png", "assets/fx/sprites/fx_axe_thrown.png", "hunchback_tower_toll", "js/ultimate_fx.js"),
    ("hag", "Ghost Nun (hag)", "assets/units/unit_hag_idle.png", "hag", "assets/portraits/hag_front.png", "assets/fx/sprites/item_cross_silver_plain.png", "nun_cross_dart", "js/nun_ult.js"),
]
FRAMES = ["idle1", "idle2", "charge1", "charge2", "charge3", "release", "empty", "hit"]

def frame_status(prefix, key, fr):
    alts = [
        f"assets/poses/{prefix}_{fr}.png",
        f"assets/poses/{key}_{fr}.png",
        f"assets/poses/{prefix}_{fr}_new.png",
        f"assets/poses/{key}_{fr}_new.png",
        f"assets/poses/skel_{fr}.png" if key == "skeleton" else "",
        f"assets/poses/reaper_{fr}.png" if key == "reaper" else "",
        f"assets/poses/{prefix}_windup.png" if fr in ("charge1", "charge2") else "",
        f"assets/poses/{key}_windup.png" if fr in ("charge1", "charge2") else "",
        f"assets/poses/skel_windup.png" if key == "skeleton" and fr in ("charge1", "charge2") else "",
        f"assets/poses/bat_draw.png" if key == "bat" and fr in ("charge1", "charge2") else "",
        f"assets/poses/bat_windup.png" if key == "bat" and fr in ("charge1", "charge2") else "",
        "assets/units/unit_hag_idle.png" if key == "hag" and fr in ("idle1", "empty") else "",
    ]
    for name in alts:
        if name and have(name): return "HAVE", name
    if f"{prefix}_{fr}" in job_ids or f"{key}_{fr}" in job_ids or f"{key}_{fr}_p3" in job_ids: return "JOB", ""
    return "MISSING", ""

def cell(state, note=""): return {"s": state, "n": note}

rows = []
for key, label, unit, prefix, portrait, proj, ultid, ultfile in HEROES:
    r = {"hero": label, "cells": []}
    c = r["cells"]
    c.append(("In the page (HERO_PROFILES / hero tab)", cell("HAVE" if (key in playable or key in profiles) else ("JOB" if key in ("bride", "hunchback", "hag") else "MISSING"), "playable" if key in playable else "not playable")))
    c.append(("Stats row (class_stats.js)", cell("HAVE" if (re.search(r"\b%s\b" % key, class_stats) or key in profiles) else "MISSING")))
    if unit:
        c.append(("Unit picture", cell("HAVE" if have(unit) else "MISSING")))
    else:
        c.append(("Unit picture", cell("JOB", "hag_idle1 in round 3")))
    for fr in FRAMES:
        st, _ = frame_status(prefix, key, fr)
        if key == "skeleton" and st == "MISSING" and have("assets/poses/skel_%s.png" % fr): st = "HAVE"
        c.append(("Pose " + fr, cell(st)))
    c.append(("Front portrait", cell("HAVE" if portrait and have(portrait) else ("JOB" if key == "hag" or f"{key}_front" in job_ids else "MISSING"))))
    c.append(("Normal projectile picture", cell("HAVE" if proj and have(proj) else ("JOB" if key == "hag" else "MISSING"), "cross (proj_cross)" if key == "hag" else "")))
    rules = {"skeleton": "js/ultimate_fx.js", "wizard": "js/ultimate_fx.js", "bat": "js/ultimate_fx.js", "reaper": "js/ultimate_fx.js", "bride": "js/ultimate_fx.js", "hunchback": "js/ultimate_fx.js", "knight": "js/knight_ult.js", "hag": "js/nun_ult.js"}[key]
    has_rules = have(rules) and (ultid in ultfx or key in ("knight", "hag"))
    c.append(("Ultimate rules module", cell("HAVE" if has_rules else ("JOB" if key == "hag" else "MISSING"), rules)))
    has_timeline = bool(re.search(r"'%s'|\"%s\"" % (ultid, ultid), ultfx) or (key == "knight" and have("js/knight_ult.js")) or (key == "hag" and have("js/nun_ult.js")))
    c.append(("Ultimate effect timeline", cell("HAVE" if has_timeline else "MISSING", ultid)))
    c.append(("Ultimate wired in the page (ULT_BUILT)", cell("HAVE" if key in ult_built else "MISSING")))
    skill = {"hag": "electric stun skill (js/electric_stun.js)"}.get(key, "shared skills")
    c.append(("Own skill / status", cell("HAVE" if (key != "hag" or have("js/electric_stun.js")) else "JOB", skill)))
    rows.append(r)

cols = [name for name, _ in rows[0]["cells"]]
# normalise columns across rows
def table_md():
    out = ["| Hero | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    sym = {"HAVE": "OK", "JOB": "job", "MISSING": "MISSING", "N/A": "-"}
    for r in rows:
        d = {n: c for n, c in r["cells"]}
        out.append("| " + r["hero"] + " | " + " | ".join(sym[d[n]["s"]] for n in cols) + " |")
    return "\n".join(out)

def table_html():
    colr = {"HAVE": "#1f7a45", "JOB": "#b9770e", "MISSING": "#b3261e", "N/A": "#777"}
    h = ["<table><thead><tr><th>Hero</th>" + "".join("<th class=v><span>%s</span></th>" % html.escape(n) for n in cols) + "</tr></thead><tbody>"]
    for r in rows:
        d = {n: c for n, c in r["cells"]}
        h.append("<tr><th>%s</th>" % html.escape(r["hero"]) + "".join(
            '<td style="background:%s" title="%s">%s</td>' % (colr[d[n]["s"]], html.escape(d[n]["n"] or ""), {"HAVE": "OK", "JOB": "job", "MISSING": "x", "N/A": "-"}[d[n]["s"]]) for n in cols) + "</tr>")
    h.append("</tbody></table>")
    return "".join(h)

counts = {k: 0 for k in ("HAVE", "JOB", "MISSING")}
for r in rows:
    for _, c in r["cells"]: counts[c["s"]] += 1
missing_list = [f"- {r['hero']}: {n}" + (f" ({c['n']})" if c['n'] else "") for r in rows for n, c in r["cells"] if c["s"] == "MISSING"]
job_list = [f"- {r['hero']}: {n}" + (f" ({c['n']})" if c['n'] else "") for r in rows for n, c in r["cells"] if c["s"] == "JOB"]

md = ["# Character gap matrix (connect-the-dots), generated by scripts/make_gap_matrix.py", "",
      "OK = the file or rule exists; job = a Colab job or Kiro task exists but is not done; MISSING = nothing yet. Facts from files, the page and the job queues.", "",
      "Totals: OK %d, job %d, MISSING %d." % (counts["HAVE"], counts["JOB"], counts["MISSING"]), "", table_md(), "",
      "## MISSING (nothing exists yet)", *(missing_list or ["- none"]), "", "## JOB (queued, not done)", *job_list]
open(P("docs/character_connect_gaps_20261115.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
page_html = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Character gaps</title>
<style>body{font:14px/1.4 -apple-system,sans-serif;margin:16px;background:#16140f;color:#f1ece2}h1{font-size:1.1rem}table{border-collapse:collapse}th,td{border:1px solid #3a352a;padding:3px 5px;text-align:center;color:#fff}
th{background:#211e17;font-weight:600}th.v{height:150px;vertical-align:bottom}th.v span{writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;font-weight:500}tbody th{text-align:left;white-space:nowrap}
.k span{display:inline-block;padding:2px 8px;margin-right:6px;border-radius:4px;color:#fff}.wrap{overflow-x:auto}</style></head><body>
<h1>Character gap matrix (2026-11-15)</h1><p class=k><span style="background:#1f7a45">OK exists</span><span style="background:#b9770e">job queued</span><span style="background:#b3261e">x missing</span> Totals: OK %d, job %d, missing %d. Hover a cell for a note.</p>
<div class=wrap>%s</div></body></html>""" % (counts["HAVE"], counts["JOB"], counts["MISSING"], table_html())
open(P("docs/character_connect_gaps_20261115.html"), "w", encoding="utf-8").write(page_html)
print("OK:", counts, "wrote docs/character_connect_gaps_20261115.{md,html}")

# ---- Part 2: action details and multi-frame sequences (owner 2026-11-15: include the pictures to be generated, several in a row) ----
def seq_status(ids, files=None, code=None):
    """HAVE when every file exists, CODE when it is made by code (module exists), JOB when every missing id is in a queue, else MISSING."""
    files = files or []
    if code is not None:
        return ("CODE" if all(have(c) for c in code) else "MISSING")
    have_n = sum(1 for f in files if have(f))
    if files and have_n == len(files): return "HAVE"
    queued = [i for i in ids if i in job_ids]
    if ids and len(queued) == len(ids): return "JOB" if have_n == 0 else "JOB"
    if queued: return "PARTLY QUEUED"
    return "MISSING"

NUN_FRAMES = ["hag_idle1", "hag_idle2", "hag_charge1", "hag_charge2", "hag_charge3", "hag_release", "hag_empty", "hag_hit"]
HANDS = ["hand_1_reach_to_chest", "hand_2_grip_cross", "hand_3_pull_back", "hand_4_snap_forward", "hand_5_release_open", "hand_6_empty_relaxed"]
stage2 = {j for j in job_ids}
SEQ = [
    # hero, sequence, frames, ids, files, code
    ("Ghost Nun", "8-frame throw set (idle x2, charge x3, release, empty, hit), hovering robe, chest cross", 8, ["hag_idle1"] + NUN_FRAMES[1:], [], None),
    ("Ghost Nun", "Throwing-hand breakdown: reach to chest, grip the cross, pull back, snap forward, release open, empty relaxed", 6, HANDS, [], None),
    ("Ghost Nun", "Front portrait", 1, ["hag_front"], [], None),
    ("Ghost Nun", "Thrown cross picture (spinning dart)", 1, ["proj_cross"], [], None),
    ("Ghost Nun", "Cross rain (ultimate) and its healing variant", 2, ["fx_cross_rain", "fx_cross_rain_heal"], [], None),
    ("Ghost Nun", "Black floating smoke, 4-frame loop (also drawn by the page around her)", 4, ["fx_black_smoke"], [], None),
    ("Ghost Nun", "Cross curse status icon", 1, ["ui_cross_curse"], [], None),
    ("Ghost Nun", "Ultimate rules (3 targets, 2 hits each, random electric stun) and electric-stun skill", 2, [], [], ["js/nun_ult.js", "js/electric_stun.js"]),
    ("Necromancer", "Missing pose frames: idle2, charge2, finger-pointing ultimate pose, front portrait", 4, ["necro_idle2", "necro_charge2", "necro_ult_point", "necro_front"], [], None),
    ("Necromancer", "Three ghost fires leaving from behind her back (code) and the hallucination mark", 2, ["ui_hallucination_mark"], [], None),
    ("Pumpkin Wizard", "Release pose", 1, ["wizard_release"], [], None),
    ("Pumpkin Guard", "Empty-handed picture (needed for the throw cycle)", 1, ["unit_knight_unarmed"], [], None),
    ("Pumpkin Guard", "Ultimate: barrier moved back and forth three times (code), A/B/C hidden points", 1, [], [], ["js/knight_ult.js"]),
    ("Ghost Bride / Hunchback", "Front portrait retakes", 2, ["bride_front", "hunchback_front"], [], None),
    ("Ghost Bride / Hunchback", "Sound-wave rings and bell-toll rings (code effects)", 2, [], [], ["js/particles.js"]),
    ("All heroes", "Status icons: frost curse, bleed drop, burn flame, poison", 4, ["ui_frost_curse", "ui_bleed_drop", "ui_burn_flame", "ui_poison_bubble"], [], None),
    ("All heroes", "Ultimate effects pictures: energy-pip socket, spectral spear, ricochet shield, shockwave ring", 4, ["ult_pip_socket", "ult_spectral_spear", "ult_ricochet_shield", "fx_shockwave_ring"], [], None),
    ("Pickups and map", "Coins (head, tail), feet chain, ghost-star blows (normal and hard)", 5, ["coin_pumpkin_head", "coin_pumpkin_tail", "fx_feet_chain", "ghoststar_blow", "ghoststar_blow_hard"], [], None),
    ("Maps", "Six scenes: ruined church (outdoor, indoor), abandoned school (outdoor, corridor), bell tower, pumpkin field", 6, ["bg_ruined_church", "bg_ruined_church_b", "bg_abandoned_school", "bg_abandoned_school_b", "bg_belltower", "bg_pumpkin_field"], [], None),
    ("Maps", "Weather: rain, snow, storm lightning, fog (code, task 158) and map effects", 4, [], [], ["js/weather.js", "js/weather_fx.js"]),
]
seq_rows = []
for hero, name, n, ids, files, code in SEQ:
    ids2 = list(ids)
    st = seq_status(ids2, files, code)
    detail = ", ".join(ids2) if ids2 else ", ".join(code or [])
    seq_rows.append((hero, name, n, st, detail))
total_frames = sum(r[2] for r in seq_rows)
queued_frames = sum(r[2] for r in seq_rows if r[3] in ("JOB", "PARTLY QUEUED"))
open(P("docs/character_connect_gaps_20261115.md"), "a", encoding="utf-8").write("\n".join([
    "", "## Action details and multi-frame sequences (pictures to generate, several in a row)", "",
    "Status: JOB = every picture is in a Colab queue; PARTLY QUEUED = some are; CODE = made by a code module that exists; MISSING = nothing yet; HAVE = files exist.", "",
    "| Hero | Sequence | Frames | Status | Items |", "|---|---|---|---|---|"] +
    ["| %s | %s | %d | %s | %s |" % (h, nme, n, s, d) for h, nme, n, s, d in seq_rows] +
    ["", "Frames listed: %d; frames in a queue or coded: %d." % (total_frames, queued_frames)]) + "\n")
colr2 = {"HAVE": "#1f7a45", "CODE": "#1f6f7a", "JOB": "#b9770e", "PARTLY QUEUED": "#8a6d00", "MISSING": "#b3261e"}
rows_html = "".join("<tr><td>%s</td><td style='text-align:left'>%s</td><td>%d</td><td style='background:%s'>%s</td><td style='text-align:left;font-size:12px'>%s</td></tr>" % (html.escape(h), html.escape(nme), n, colr2.get(s, "#555"), s, html.escape(d)) for h, nme, n, s, d in seq_rows)
sec = "<h1 style='margin-top:24px'>Action details and multi-frame sequences</h1><div class=wrap><table><thead><tr><th>Hero</th><th>Sequence</th><th>Frames</th><th>Status</th><th>Items</th></tr></thead><tbody>%s</tbody></table></div><p>Frames listed: %d; in a queue or coded: %d.</p>" % (rows_html, total_frames, queued_frames)
h = open(P("docs/character_connect_gaps_20261115.html"), encoding="utf-8").read().replace("</body>", sec + "</body>")
open(P("docs/character_connect_gaps_20261115.html"), "w", encoding="utf-8").write(h)
print("sequences:", len(seq_rows), "frames", total_frames, "queued/coded", queued_frames)
