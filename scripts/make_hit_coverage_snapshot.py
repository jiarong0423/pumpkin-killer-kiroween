#!/usr/bin/env python3
"""Compress the hit-trace data (angle x power, both directions, wall destroyed) into ONE snapshot chart (SVG) and a small JSON, so the big jsonl dry-run files can be deleted.
Input: the files of scripts/trace_ult_down.js (--plain and ultimate) and scripts/trace_match_hits.js (--wall natural/down/mid). Judge counts come from the same independent rule as scripts/check_match_hits.py.
usage: python3 -B scripts/make_hit_coverage_snapshot.py --dir logs_local/hit_trace --out docs/hit_coverage_20261119"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hit_mask_py import HitMasks
M = HitMasks(); A = sys.argv
D = A[A.index("--dir") + 1] if "--dir" in A else "logs_local/hit_trace"; OUT = A[A.index("--out") + 1] if "--out" in A else "docs/hit_coverage_20261119"
def touch(prof, dx, dy, r, side):
    hw, hh = (57, 165) if prof == "reaper" else (70, 190)
    return abs(dx) <= hw + r and -hh - r <= dy <= r and M.touches(prof, dx, dy, r, side == "left", True)
def rows(name):
    return [json.loads(l) for l in open(os.path.join(D, name))]
summary = {"files": {}, "rank": {}}; panels = {}
for name, label in (("plain_down.jsonl", "plain"), ("ult_down.jsonl", "ultimate")):
    rs = rows(name); throws = collections.defaultdict(lambda: [0, 0]); hit = {}
    for o in rs:
        k = (o["dir"], o["ang"], o["pw"], o["hero"], o["c"])
        hit[k] = hit.get(k, False) or (o["hp1"] < o["hp0"])
    cell = collections.defaultdict(lambda: [0, 0])
    for (d, a, p, h, c), v in hit.items(): cell[(d, a, p)][0] += 1 if v else 0
    n_per = 24   # 8 roles x 3 formations per cell (every throw makes at least one record near the targets or none: missing throws count as no damage)
    panels[label] = {d: {(a, p): cell[(d, a, p)][0] / n_per for (dd, a, p) in list(cell) if dd == d} for d in ("L2R", "R2L")}
    rank = collections.defaultdict(lambda: [0, 0])   # touched rule true: [touched steps, damaged steps], by rank of the unit from the shooter (0 front .. 2 rear = bottom of the formation)
    per_tick = collections.defaultdict(list)
    for o in rs: per_tick[(o["c"], o["tick"])].append(o)
    for key, tk in per_tick.items():
        if any(o["area"] or o.get("ret") or o["blocked"] for o in tk): continue
        side = tk[0]["side"]; units = sorted({o["i"]: o["ux"] for o in tk}.items(), key=lambda kv: kv[1], reverse=(side == "left"))
        order = {i: r for r, (i, _) in enumerate(units)}
        for o in tk:
            if touch(o["prof"], o["px"] - o["ux"], o["py"] - o["uy"], o["hitR"], o["side"]) and not o["cool"] and not o["pierced"]:
                rank[order[o["i"]]][0] += 1; rank[order[o["i"]]][1] += 1 if o["hp1"] < o["hp0"] else 0
    summary["rank"][label] = {str(r): {"touched": t, "damaged": d} for r, (t, d) in sorted(rank.items())}
    summary["files"][name] = {"records": len(rs), "throws": len(hit)}
cnt = {}
for name in ("full_natural.jsonl", "full_down.jsonl", "full_mid.jsonl", "plain_down.jsonl", "ult_down.jsonl"):
    summary["files"].setdefault(name, {"records": len(rows(name))})
json.dump(summary, open(OUT + ".json", "w"), indent=1)
# ---- SVG: 4 panels (plain/ultimate x L2R/R2L), angle 5..85 down, power 10..100 across; colour = share of the 24 throws (8 roles x 3 formations) that damaged somebody
angs = list(range(5, 90, 5)); pws = list(range(10, 101, 6)); cw, ch, ox, oy, pw_, gap = 20, 16, 60, 70, len(pws) * 20, 70
W = ox * 2 + 2 * pw_ + gap; H = oy + len(angs) * ch + 330
def col(v): g = int(235 - 200 * v); return "rgb(%d,%d,%d)" % (int(245 - 215 * v), g, int(240 - 150 * v))
svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" font-family="sans-serif" font-size="12"><rect width="100%%" height="100%%" fill="#fff"/>' % (W, H),
       '<text x="20" y="26" font-size="18" font-weight="bold">Hit coverage, wall destroyed: angle x power, both sides (%s)</text>' % (re.search(r"(\d{4})(\d{2})(\d{2})$", OUT) and "-".join(re.search(r"(\d{4})(\d{2})(\d{2})$", OUT).groups()) or "date unknown"),
       '<text x="20" y="46" fill="#444">Colour = share of the 24 throws (8 roles x 3 formations) that damaged an enemy unit. Judge result in the table below. Source: real page physics, data only.</text>']
for pi, label in enumerate(("plain", "ultimate")):
    for di, d in enumerate(("L2R", "R2L")):
        x0 = ox + di * (pw_ + gap) + 0; y0 = oy + pi * 0   # two columns; plain and ultimate stacked below
        y0 = oy + pi * (len(angs) * ch + 50) if False else oy
        pass
rowsH = len(angs) * ch + 70
H = oy + 2 * rowsH + 300; svg[0] = svg[0].replace('viewBox="0 0 %d %d"' % (W, 0), "") if False else svg[0]
svg[0] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" font-family="sans-serif" font-size="12"><rect width="100%%" height="100%%" fill="#fff"/>' % (W, H)
for pi, label in enumerate(("plain", "ultimate")):
    for di, d in enumerate(("L2R", "R2L")):
        x0 = ox + di * (pw_ + gap); y0 = oy + pi * rowsH
        svg.append('<text x="%d" y="%d" font-weight="bold">%s, %s</text>' % (x0, y0 - 8, label, "left team shoots right" if d == "L2R" else "right team shoots left"))
        for ai, a in enumerate(angs):
            if di == 0: svg.append('<text x="%d" y="%d" text-anchor="end" fill="#444">%d</text>' % (x0 - 6, y0 + ai * ch + 12, a))
            for pj, p in enumerate(pws):
                v = panels[label][d].get((a, p), 0.0)
                svg.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="#fff"/>' % (x0 + pj * cw, y0 + ai * ch, cw, ch, col(v)))
        for pj, p in enumerate(pws):
            if pj % 2 == 0: svg.append('<text x="%d" y="%d" text-anchor="middle" fill="#444">%d</text>' % (x0 + pj * cw + 10, y0 + len(angs) * ch + 14, p))
        svg.append('<text x="%d" y="%d" fill="#444">power</text>' % (x0, y0 + len(angs) * ch + 30))
svg.append('<text x="14" y="%d" fill="#444" transform="rotate(-90 14 %d)">angle (deg)</text>' % (oy + 120, oy + 120))
ty = oy + 2 * rowsH + 10
res = [("natural matches (120)", "full_natural"), ("wall held down (120 matches)", "full_down"), ("wall forced down mid-match (120)", "full_mid"), ("all angles x powers, plain, wall down", "plain_down"), ("all angles x powers, ultimate, wall down", "ult_down"), ("all ultimates, wall one hit left", "ult_break")]
svg.append('<text x="20" y="%d" font-weight="bold">Judge (box AND binary mask; damage without contact = FALSE_HIT, contact without damage = MISSED_HIT)</text>' % ty)
J = json.load(open(os.path.join(D, "judge_counts.json"))) if os.path.exists(os.path.join(D, "judge_counts.json")) else {}
for i, (t, k) in enumerate(res):
    j = J.get(k, {}); svg.append('<text x="30" y="%d">%s: steps %s, FALSE_HIT %s, MISSED_HIT %s</text>' % (ty + 22 + i * 18, t, j.get("steps", "?"), j.get("FALSE_HIT", "?"), j.get("MISSED_HIT", "?")))
ry = ty + 22 + len(res) * 18 + 16
svg.append('<text x="20" y="%d" font-weight="bold">Touched shots that damaged, by rank from the shooter (0 front, 2 rear)</text>' % ry)
for i, label in enumerate(("plain", "ultimate")):
    parts = ", ".join("rank %s %d/%d" % (r, v["damaged"], v["touched"]) for r, v in summary["rank"][label].items())
    svg.append('<text x="30" y="%d">%s: %s</text>' % (ry + 22 + i * 18, label, parts))
svg.append('</svg>'); open(OUT + ".svg", "w").write("\n".join(svg))
print(json.dumps(summary["rank"]))
