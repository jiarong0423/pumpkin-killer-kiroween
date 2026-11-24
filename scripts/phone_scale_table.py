#!/usr/bin/env python3 -B
"""Phone scale table: for every phone in docs/device_specs/phone_viewports_20261117.csv (landscape), how big the stage and every game object are in CSS px.

Formulas come from index.html (read, not guessed): the world is 1920 x 1080; the stage height is fixed and the width follows the picture, but a screen narrower than 16:9 (foldable main screens) is fitted by width instead; the dock strip below the stage is 52 CSS px;
the canvas widens to at most 2.6 x the stage height (MAX_VIEW_ASPECT 2.6, the rest of a wider screen stays empty); the scale s = min((viewport height - 52) / 1080, viewport width / 1920).
Objects in world px (original spec, shared/size_frozen.json and shared/heroes.json): unit frame 220, hit box 140 x 190 (half-width 70), hp bar 150 x 13, crate 64, spear 210 x 33.
Browser chrome cases use the numbers measured on the owner's phone: nav bar takes 44 CSS px of width, the address bar takes 94 CSS px of height.
Writes docs/PHONE_SCALE_TABLE_20261117.md and logs_local/phone_scale_table.log; exit code 1 if the CSV is missing or a row is invalid.
"""
import csv, os, sys, logging
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "docs", "device_specs", "phone_viewports_20261117.csv")
OUT = os.path.join(ROOT, "docs", "PHONE_SCALE_TABLE_20261117.md")
os.makedirs(os.path.join(ROOT, "logs_local"), exist_ok=True)
logging.basicConfig(filename=os.path.join(ROOT, "logs_local", "phone_scale_table.log"), level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
WORLD_W, WORLD_H, DOCK, MAX_ASPECT = 1920, 1080, 52, 2.6
UNIT, HIT_W, HIT_H, HPBAR_W, CRATE, SPEAR_L = 220, 140, 190, 150, 64, 210
NAV_W, BAR_H = 44, 94
MIN_UNIT_PX, MIN_TOUCH = 60, 44

def layout(w, h):
    avail_h = h - DOCK
    s = min(avail_h / WORLD_H, w / WORLD_W)   # height fixed unless the screen is narrower than 16:9 (foldable main screens, tablets): then the width decides
    core_w, core_h = WORLD_W * s, WORLD_H * s
    view_w = max(core_w, min(w, MAX_ASPECT * core_h))
    return dict(stage_h=core_h, s=s, aspect=w / avail_h, stage_w=view_w, pad=(view_w - core_w) / 2, empty=max(0, w - view_w), unused_h=max(0, avail_h - core_h), fits=True)

def main():
    try:
        rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    except OSError as e:
        logging.error("ERROR cannot read %s: %s", CSV, e); print("ERROR", e); return 1
    lines = []
    ref = None
    for r in rows:
        try:
            pw, ph = float(r["css_w_portrait"]), float(r["css_h_portrait"])
        except (ValueError, KeyError) as e:
            logging.error("ERROR bad row %s: %s", r, e); print("ERROR bad row", r); return 1
        W, H = ph, pw   # landscape
        for case, (cw, ch) in (("fullscreen", (W, H)), ("address bar", (W - NAV_W, H - BAR_H))):
            L = layout(cw, ch)
            if "owner phone" in r["model"] and case == "fullscreen": ref = L["s"]
            lines.append((r["brand"] + " " + r["model"], case, cw, ch, L))
    ref = ref or 1.0
    md = ["# Phone scale table (landscape), 2026-11-17", "",
          "Source of the sizes: `docs/device_specs/phone_viewports_20261117.csv` (third-party aggregator, every value labelled unverified by the page; the owner's phone is measured). Formulas and constants: `scripts/phone_scale_table.py` header. World 1920 x 1080, stage height = viewport height - 52 (dock strip), scale s = stage height / 1080, canvas width at most 2.6 x stage height.", "",
          "Object sizes on screen = world size x s (CSS px). Unit = 220 frame, hit = 140 x 190 box, bar = 150 wide HP bar, crate = 64, spear = 210 long. 'x phone' = s divided by the owner's phone s (fullscreen). Flags: SMALL = unit under %d px; EMPTY = unused screen width beyond the 2.6 aspect cap." % MIN_UNIT_PX, "",
          "| Phone | Case | Viewport | Stage w x h | s | x phone | Unit | Hit box | HP bar | Crate | Spear | Pad each side | Flags |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    small = 0
    for name, case, cw, ch, L in lines:
        s = L["s"]
        flags = []
        if UNIT * s < MIN_UNIT_PX: flags.append("SMALL"); small += 1
        if L["empty"] > 1: flags.append("EMPTY W %dpx" % round(L["empty"]))
        if L["unused_h"] > 1: flags.append("LETTERBOX H %dpx" % round(L["unused_h"]))
        md.append("| %s | %s | %dx%d | %dx%d | %.3f | %.2f | %d | %dx%d | %d | %d | %d | %d | %s |" % (name, case, round(cw), round(ch), round(L["stage_w"]), round(L["stage_h"]), s, s / ref, round(UNIT * s), round(HIT_W * s), round(HIT_H * s), round(HPBAR_W * s), round(CRATE * s), round(SPEAR_L * s), round(L["pad"] * 1.0), " ".join(flags) or "-"))
    # the one formula the owner asked for: what stage size do you need for a given unit size
    md += ["", "## Reverse formula", "", "For a wanted unit size U (CSS px): s = U / 220, stage height = 1080 x s, viewport height = 1080 x s + 52, stage width = min(2.6 x stage height, viewport width). Examples: U = 60 needs viewport height >= %d; U = 70 needs >= %d; U = 80 needs >= %d." % (round(1080 * 60 / 220 + DOCK), round(1080 * 70 / 220 + DOCK), round(1080 * 80 / 220 + DOCK))]
    open(OUT, "w", encoding="utf-8").write("\n".join(md) + "\n")
    logging.info("wrote %s rows=%d small=%d ref_s=%.4f", OUT, len(lines), small, ref)
    print("OK wrote", OUT, "rows", len(lines), "SMALL rows", small)
    return 0

if __name__ == "__main__":
    sys.exit(main())
