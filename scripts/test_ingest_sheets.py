#!/usr/bin/env python3
"""Synthetic end-to-end tests for the image2 sheet ingestion tools."""
import glob
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable


def command(*args):
    return subprocess.run([PYTHON, "-B", *map(str, args)], cwd=ROOT, text=True, capture_output=True)


def assert_ok(result, context):
    if result.returncode:
        raise AssertionError("%s failed (%d)\nstdout:\n%s\nstderr:\n%s" % (context, result.returncode, result.stdout, result.stderr))


def cell(variant=0, edge=False):
    image = Image.new("RGB", (160, 180), (255, 0, 255))
    draw = ImageDraw.Draw(image)
    left = 0 if edge else 42
    # A body plus head gives the decoupled face and silhouette measurements data.
    draw.rectangle((left, 45, left + 65, 150), fill=(40, 180, 100))
    draw.ellipse((left + 12, 20, left + 53, 62), fill=(230, 170, 40))
    if variant:
        draw.rectangle((left + 65, 85, min(159, left + 76 + variant * 3), 98), fill=(40, 180, 100))
    return image


def sheet(path, edge_at=None):
    out = Image.new("RGB", (320, 720), (255, 0, 255))
    for row in range(4):
        for col in range(2):
            out.paste(cell(row * 2 + col, edge=(row, col) == edge_at), (col * 160, row * 180))
    out.save(path)


def strip(path):
    jump = cell(0)
    ImageDraw.Draw(jump).rectangle((20, 5, 140, 174), fill=(40, 180, 100))
    frames = [cell(0), cell(1), cell(0), jump]
    out = Image.new("RGB", (160 * len(frames), 180), (255, 0, 255))
    for index, frame in enumerate(frames):
        out.paste(frame, (index * 160, 0))
    out.save(path)


def alpha_bottom(path):
    alpha = np.asarray(Image.open(path).convert("RGBA").getchannel("A"))
    rows = np.where((alpha > 128).sum(axis=1) > 6)[0]
    return int(rows.max())


def run():
    with tempfile.TemporaryDirectory(prefix="pk-sheet-test-") as temp:
        temp = Path(temp)
        input_dir, poses, portraits = temp / "input", temp / "poses", temp / "portraits"
        input_dir.mkdir()
        sheet(input_dir / "test_sheet.png")
        strip(input_dir / "test_strip_idle_loop.png")
        portrait = cell(0)
        portrait.save(input_dir / "test_portrait.png")
        base = ["scripts/ingest_sheets.py", input_dir, "--grid", "4x2", "--poses-dir", poses, "--portraits-dir", portraits]
        assert_ok(command(*base), "initial ingestion")

        expected = ["idle1", "idle2", "charge1", "charge2", "charge3", "release", "empty", "hit"]
        for frame in expected:
            path = poses / ("test_%s.png" % frame)
            assert path.exists(), "missing table-mapped frame " + frame
            assert Image.open(path).size == (1024, 1024), "wrong standard canvas for " + frame
            assert alpha_bottom(path) == 999, "feet were not aligned to row 1000 for " + frame
        for number in range(1, 5):
            assert (poses / ("test_idle_loop_%d.png" % number)).exists(), "missing strip frame"
        assert (portraits / "test_portrait.png").exists(), "portrait was not installed"

        denied = command(*base)
        assert denied.returncode == 1 and "destination already exists" in denied.stderr, "ingestion overwrote without --force"
        forced = command(*base, "--force")
        assert_ok(forced, "forced ingestion")
        backups = glob.glob(str(poses / "_replaced" / "**" / "test_idle1.png"), recursive=True)
        portrait_backups = glob.glob(str(poses / "_replaced" / "**" / "test_portrait.png"), recursive=True)
        assert backups, "--force did not preserve replaced pose under _replaced"
        assert portrait_backups, "--force did not preserve replaced portrait under _replaced"

        auto_input, auto_poses = temp / "auto-input", temp / "auto-poses"
        auto_input.mkdir()
        sheet(auto_input / "auto_sheet.png")
        assert_ok(command("scripts/ingest_sheets.py", auto_input, "--poses-dir", auto_poses, "--portraits-dir", temp / "auto-portraits"), "magenta-gutter grid detection")
        assert (auto_poses / "auto_hit.png").exists(), "auto-detected sheet did not map all frames"

        edge_input, edge_poses = temp / "edge-input", temp / "edge-poses"
        edge_input.mkdir()
        sheet(edge_input / "edge_sheet.png", edge_at=(0, 0))
        rejected = command("scripts/ingest_sheets.py", edge_input, "--grid", "4x2", "--poses-dir", edge_poses, "--portraits-dir", temp / "edge-portraits")
        assert rejected.returncode == 1 and "touches its cell edge" in rejected.stderr, "cut-off cell was not rejected"

        continuity = temp / "continuity.json"
        checked = command("scripts/check_continuity.py", "--poses-dir", poses, "--class", "test", "--strip", "idle_loop", "--json", continuity)
        assert_ok(checked, "continuity report")
        report = json.loads(continuity.read_text(encoding="utf-8"))["strips"]["test:idle_loop"]
        all_flags = [flag for entry in report["steps"] for flag in entry["flags"]]
        assert "JUMP" in all_flags, "large strip discontinuity was not marked JUMP"
        assert report["copies"], "non-adjacent repeated frame was not marked COPY"
        assert report["loop_close"] is not None, "idle loop close was not measured"

        previews = temp / "previews"
        rendered = command("scripts/make_strip_gif.py", "--poses-dir", poses, "--class", "test", "--strip", "idle_loop", "--continuity-json", continuity, "--output-dir", previews, "--duration", "70")
        assert_ok(rendered, "GIF preview")
        assert (previews / "test_idle_loop.gif").exists(), "GIF preview was not written"
        assert (previews / "test_idle_loop_contact.png").exists(), "contact sheet was not written"


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:  # keep the test's failed reason compact for shell users
        print("ERROR " + str(exc), file=sys.stderr)
        sys.exit(1)
    print("test_ingest_sheets: OK")
