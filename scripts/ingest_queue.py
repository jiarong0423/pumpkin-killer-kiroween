#!/usr/bin/env python3
"""Ingest the overnight Colab outputs (tag q1) into the repo: key the magenta, align, name per docs/pose_spec.md.

Reads <Drive>/PumpkinKiller/out/<job id>_v1_q1.png and writes:
  pose_<class>_<frame>   -> assets/poses/<class>_<frame>.png     (1024x1024 RGBA, same scale, feet on row 1000, centred on the opaque box)
  portrait_front_<class> -> assets/portraits/<class>_front.png   (tight crop)
  fx_*                   -> assets/fx/sprites/<name>.png          (tight crop)
  ui_*                   -> assets/ui/<name>.png                  (tight crop)
A picture whose opaque box touches the picture edge is REJECTED (cut off, the owner's rule); a missing file is reported. One log line each.
Also keeps a review contact sheet in docs/audition/queue_q1_*.png. Exit 1 when anything was rejected or missing.
Usage: python3 -B scripts/ingest_queue.py [--tag q1] [--drive-out DIR]
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.environ.get("PK_DRIVE_DIR", "<DRIVE_DIR>")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import key_magenta_items as K  # noqa: E402


def key_full(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(float)
    mag = (a[..., 0] + a[..., 2]) / 2 - a[..., 1]
    alpha = np.clip((160 - mag) / 50, 0, 1)   # tight keying: the flat background has faint texture noise that the loose ramp mistook for art
    spill = np.maximum(0, mag) * 0.95 * (1 - alpha)
    rgb = a.copy()
    rgb[..., 0] = np.clip(a[..., 0] - spill, 0, 255)
    rgb[..., 2] = np.clip(a[..., 2] - spill, 0, 255)
    return Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA")


def box_of(im):
    al = np.asarray(im.getchannel("A"))
    rows = np.where((al > 128).sum(axis=1) > 6)[0]
    cols = np.where((al > 128).sum(axis=0) > 6)[0]
    if len(rows) == 0:
        return None
    return int(cols.min()), int(rows.min()), int(cols.max()) + 1, int(rows.max()) + 1


def touches_edge(box, size, margin=4):
    return box[0] <= margin or box[1] <= margin or box[2] >= size[0] - margin or box[3] >= size[1] - margin


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="q1")
    ap.add_argument("--drive-out", default=DEFAULT_OUT)
    ap.add_argument("--jobs", default=os.path.join(ROOT, "colab", "jobs_queue_20261109.json"))
    a = ap.parse_args(argv)
    with open(a.jobs, encoding="utf-8") as f:
        jobs = json.load(f)["jobs"]
    bad = 0
    sheet = {"pose": [], "portrait": [], "fx": [], "ui": []}
    for j in jobs:
        jid = j["id"]
        src = os.path.join(a.drive_out, "%s_v1_%s.png" % (jid, a.tag))
        if not os.path.exists(src):
            print("MISSING %s" % jid)
            bad += 1
            continue
        try:
            im = key_full(src)
            box = box_of(im)
            if box is None:
                raise ValueError("nothing left after keying")
            wide_ok = jid.startswith("ui_top_banner")   # the banner pieces are meant to run to the picture edge
            if jid.startswith("portrait_front_"):   # a bust portrait is cut at the bottom on purpose: only the top and the sides must be clear
                edge = box[0] <= 4 or box[1] <= 4 or box[2] >= im.size[0] - 4
            else:
                edge = touches_edge(box, im.size)
            if edge and not wide_ok:
                print("REJECT %s: the picture touches the edge (cut off) %s" % (jid, box))
                bad += 1
                continue
            crop = im.crop(box)
            if jid.startswith("pose_"):
                _, cls, frame = jid.split("_", 2)
                canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
                if crop.width > 1024 or crop.height > 1000:
                    raise ValueError("too large for the 1024 canvas %s" % (crop.size,))
                canvas.paste(crop, ((1024 - crop.width) // 2, 1000 - crop.height), crop)
                dst = os.path.join(ROOT, "assets", "poses", "%s_%s.png" % (cls, frame))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                canvas.save(dst)
                sheet["pose"].append((jid, canvas))
            else:
                if jid.startswith("portrait_front_"):
                    dst = os.path.join(ROOT, "assets", "portraits", jid.replace("portrait_front_", "") + "_front.png"); kind = "portrait"
                elif jid.startswith("fx_"):
                    dst = os.path.join(ROOT, "assets", "fx", "sprites", jid + ".png"); kind = "fx"
                else:
                    dst = os.path.join(ROOT, "assets", "ui", jid + ".png"); kind = "ui"
                pad = 6
                crop = im.crop((max(0, box[0] - pad), max(0, box[1] - pad), min(im.width, box[2] + pad), min(im.height, box[3] + pad)))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                crop.save(dst)
                sheet[kind].append((jid, crop))
            print("OK %s -> %s" % (jid, os.path.relpath(dst, ROOT)))
        except Exception as e:  # noqa: BLE001 - one bad picture must not stop the rest
            print("ERROR %s: %r" % (jid, e))
            bad += 1
    units = {"skeleton": "unit_skeleton.png", "wizard": "unit_wizard.png", "bat": "unit_bat.png", "knight": "unit_knight.png", "bride": "unit_bride_idle.png", "hunchback": "unit_hunchback_idle.png"}
    for cls, fn in units.items():   # idle1 = the existing approved unit picture, put on the standard canvas
        try:
            im = Image.open(os.path.join(ROOT, "assets", "units", fn)).convert("RGBA")
            box = box_of(im)
            crop = im.crop(box)
            canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
            if crop.width <= 1024 and crop.height <= 1000:
                canvas.paste(crop, ((1024 - crop.width) // 2, 1000 - crop.height), crop)
                canvas.save(os.path.join(ROOT, "assets", "poses", "%s_idle1.png" % cls))
                print("OK idle1 %s <- %s (existing unit picture)" % (cls, fn))
            else:
                print("ERROR idle1 %s: unit picture too large %s" % (cls, crop.size)); bad += 1
        except Exception as e:  # noqa: BLE001
            print("ERROR idle1 %s: %r" % (cls, e)); bad += 1
    os.makedirs(os.path.join(ROOT, "docs", "audition"), exist_ok=True)
    for kind, items in sheet.items():
        if not items:
            continue
        cell = 220
        cols = 6
        rows = (len(items) + cols - 1) // cols
        W = Image.new("RGB", (cols * cell, rows * cell), (40, 36, 70))
        for i, (_, im) in enumerate(items):
            t = im.copy()
            t.thumbnail((cell - 8, cell - 8))
            W.paste(t, ((i % cols) * cell + 4, (i // cols) * cell + 4), t)
        W.save(os.path.join(ROOT, "docs", "audition", "queue_%s_%s.png" % (a.tag, kind)))
    print("done, %d problem(s)" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
