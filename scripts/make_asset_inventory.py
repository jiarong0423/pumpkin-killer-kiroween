#!/usr/bin/env python3
"""Write docs/asset_inventory.json: every asset folder with file counts and names, plus the open-art list, so a model can draw an overview diagram from DATA.
Read-only on assets/. Logs to docs/audition/asset_inventory.log. Exit 1 on any failure."""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "asset_inventory.json")
LOG = os.path.join(ROOT, "docs", "audition", "asset_inventory.log")

# open art (owner decisions of 2026-11-10); status words: done / in_progress / waiting_owner / not_started
OPEN_ART = [
    {"item": "wind ghost 8-frame blowing loop", "status": "in_progress", "route": "Colab (5 single frames running) or image2 (8-cell sheet prompt written)", "prompt_file": "docs/image2_ghost_blow_prompt.md"},
    {"item": "feet chain for the slow status", "status": "in_progress", "route": "Colab job queued", "prompt_file": "colab/jobs_chain_20261110.json"},
    {"item": "blue twin of the purple floating coffin", "status": "not_started", "route": "Colab or image2", "prompt_file": "docs/top_hud_art_jobs.md"},
    {"item": "broken / damaged fence art (currently solid black slabs)", "status": "not_started", "route": "image2", "prompt_file": "docs/kiro_69_art_optimization.md"},
    {"item": "front portraits: bride, hunchback, necromancer", "status": "waiting_owner", "route": "image2 via owner", "prompt_file": "docs/kiro_69_art_optimization.md"},
    {"item": "39 redo pose pictures", "status": "waiting_owner", "route": "image2 via owner", "prompt_file": "colab/jobs_retry2_20261110.json"},
]

# modules of the game with an honest status (owner 2026-11-10: "modular, like completed"); done = built AND looked at on screen or tested; built_unseen = built but not looked at; in_progress; not_started
MODULES = [
    {"module": "core physics and turns", "status": "done", "note": "fixed step, wind, 12 s turn, countdown bar"},
    {"module": "AI opponent", "status": "built_unseen", "note": "no-simulator aiming with wind rule; hit rate after the wind rule not re-measured"},
    {"module": "classes: skeleton, wizard, bat, knight", "status": "done", "note": "playable, 8-frame pose standard for skeleton and bat"},
    {"module": "classes: bride, hunchback, necromancer, reaper", "status": "in_progress", "note": "not playable yet; art partly done, portraits pending"},
    {"module": "ultimates", "status": "in_progress", "note": "bat built; skeleton, wizard, knight designed but not built"},
    {"module": "top HUD (banners, centre piece, countdown)", "status": "done", "note": "round, countdown and distance in the centre piece"},
    {"module": "top controls: sound, reset, help", "status": "done", "note": "right edge middle column, faded until the pointer is near"},
    {"module": "wind ghost", "status": "in_progress", "note": "works with a 4-frame fallback; the continuous blowing art is being generated"},
    {"module": "floating coffin platforms", "status": "built_unseen", "note": "both sides use the purple art; a true blue twin is not drawn yet"},
    {"module": "status effects: bleed, poison, frost, slow, stun", "status": "built_unseen", "note": "frost blinks blue and slows motion; slow chain waits for its picture"},
    {"module": "central wall", "status": "built_unseen", "note": "sturdier (8 per hit); damaged and broken art are black slabs, needs redraw"},
    {"module": "bottom dock", "status": "done", "note": "no health numbers; right end empty"},
    {"module": "start screen and name input", "status": "in_progress", "note": "name module written and tested, not wired in"},
    {"module": "Kiro scripts: ingest, continuity, pose animation", "status": "done", "note": "tests re-run in main; pose_anim.js not integrated"},
    {"module": "audio", "status": "built_unseen", "note": "impact sounds wired; not reviewed this round"},
]


def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    try:
        folders = {}
        base = os.path.join(ROOT, "assets")
        for dp, dn, fn in os.walk(base):
            dn[:] = sorted(d for d in dn if not d.startswith("."))
            files = sorted(f for f in fn if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp3", ".wav", ".ogg", ".json")))
            if files:
                folders[os.path.relpath(dp, ROOT)] = {"count": len(files), "files": files}
        data = {"generated": time.strftime("%Y-%m-%d %H:%M"), "folders": folders, "modules": MODULES, "open_art": OPEN_ART,
                "totals": {"folders": len(folders), "files": sum(v["count"] for v in folders.values())}}
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        log("OK wrote %s: %d folders, %d files, %d open art items" % (OUT, data["totals"]["folders"], data["totals"]["files"], len(OPEN_ART)))
        return 0
    except Exception as e:
        log("ERROR %r" % (e,))
        return 1


if __name__ == "__main__":
    sys.exit(main())
