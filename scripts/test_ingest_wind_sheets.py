#!/usr/bin/env python3
"""Offline synthetic tests for scripts/ingest_wind_sheets.py."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
SCRIPT = ROOT / "scripts" / "ingest_wind_sheets.py"
MAGENTA = (255, 0, 255)


def command(*args):
    return subprocess.run([PYTHON, "-B", str(SCRIPT), *map(str, args)], cwd=ROOT, text=True, capture_output=True)


def assert_ok(result, context):
    if result.returncode:
        raise AssertionError("%s failed (%d)\nstdout:\n%s\nstderr:\n%s" % (
            context, result.returncode, result.stdout, result.stderr))


def ghost(frame=1, empty=False, edge=False, drift=0):
    image = Image.new("RGB", (512, 512), MAGENTA)
    if empty:
        return image
    draw = ImageDraw.Draw(image)
    left = 0 if edge else 180 + drift
    # The outside silhouette never changes. Interior mouth marks provide a small,
    # continuous frame change without moving the feet or changing the scale.
    draw.ellipse((left + 20, 130, left + 130, 240), fill=(230, 240, 245), outline=(25, 30, 50), width=4)
    draw.rectangle((left, 210, left + 150, 400), fill=(220, 235, 240), outline=(25, 30, 50), width=4)
    mouth = 5 + (frame % 4) * 3
    draw.ellipse((left + 75 - mouth, 190, left + 75 + mouth, 190 + mouth), fill=(25, 30, 50))
    return image


def effect(kind):
    image = Image.new("RGB", (512, 512), MAGENTA)
    draw = ImageDraw.Draw(image)
    offset = {"s": 0, "m": 18, "l": 36, "swirl": 54}[kind]
    draw.ellipse((145 - offset, 210, 330 + offset, 300), fill=(180, 235, 250), outline=(25, 30, 50), width=4)
    return image


def make_sheets(directory, *, empty_cell=None, edge_cell=None, drift_frame=None):
    directory.mkdir(parents=True, exist_ok=True)
    ghost_sheet = Image.new("RGB", (2048, 1024), MAGENTA)
    for index in range(8):
        frame = index + 1
        cell = ghost(frame, empty=frame == empty_cell, edge=frame == edge_cell,
                     drift=7 if frame == drift_frame else 0)
        ghost_sheet.paste(cell, ((index % 4) * 512, (index // 4) * 512))
    ghost_path = directory / "ghost_sheet.png"
    ghost_sheet.save(ghost_path)

    fx_sheet = Image.new("RGB", (2048, 512), MAGENTA)
    for index, kind in enumerate(("s", "m", "l", "swirl")):
        fx_sheet.paste(effect(kind), (index * 512, 0))
    fx_path = directory / "fx_sheet.png"
    fx_sheet.save(fx_path)
    return ghost_path, fx_path


def make_picture_dirs(directory):
    ghost_dir, fx_dir = directory / "ghosts", directory / "fx"
    ghost_dir.mkdir(parents=True)
    fx_dir.mkdir()
    for number in range(1, 9):
        ghost(number).save(ghost_dir / ("wind_ghost_%d.png" % number))
    for kind in ("s", "m", "l", "swirl"):
        effect(kind).save(fx_dir / ("wind_gust_%s.png" % kind if kind != "swirl" else "wind_swirl.png"))
    return ghost_dir, fx_dir


def paths(temp):
    return temp / "output", temp / "audition", temp / "ingest.log"


def run():
    with tempfile.TemporaryDirectory(prefix="pk-wind-ingest-test-") as work:
        temp = Path(work)
        output, audition, log = paths(temp)

        good_ghost_sheet, good_fx_sheet = make_sheets(temp / "good-sheet")
        dry = command("--ghost-sheet", good_ghost_sheet, "--fx-sheet", good_fx_sheet,
                      "--output-dir", output, "--audition-dir", audition, "--log", log)
        assert_ok(dry, "good sheet dry run")
        assert not output.exists(), "dry run wrote an output directory"
        assert "WOULD WRITE wind_ghost_f1.png" in dry.stdout, "dry run did not list its preview files"
        assert log.exists() and "DRY-RUN" in log.read_text(encoding="utf-8"), "dry-run audit log missing"

        for label, kwargs, expected in (
            ("empty", {"empty_cell": 3}, "empty after tight magenta keying"),
            ("edge", {"edge_cell": 4}, "touches its picture edge"),
            ("drift", {"drift_frame": 5}, "bbox centre drifts"),
        ):
            ghost_sheet, fx_sheet = make_sheets(temp / label, **kwargs)
            result = command("--ghost-sheet", ghost_sheet, "--fx-sheet", fx_sheet,
                             "--output-dir", temp / (label + "-out"), "--audition-dir", audition,
                             "--log", temp / (label + ".log"))
            assert result.returncode != 0, "%s sheet was accepted" % label
            assert expected in result.stderr, "%s rejection reason missing: %s" % (label, result.stderr)

        ghost_dir, fx_dir = make_picture_dirs(temp / "pictures")
        applied = command("--ghost-dir", ghost_dir, "--fx-dir", fx_dir, "--apply",
                          "--output-dir", output, "--audition-dir", audition, "--log", log)
        assert_ok(applied, "single-picture apply")
        installed = sorted(output.iterdir())
        assert len(installed) == 13, "apply should write 12 PNGs plus manifest, got %d" % len(installed)
        assert all((output / name).exists() for name in [
            *["wind_ghost_f%d.png" % n for n in range(1, 9)],
            "wind_gust_s.png", "wind_gust_m.png", "wind_gust_l.png", "wind_swirl.png",
            "wind_ghost_manifest.json",
        ]), "apply did not install every expected output"
        manifest = json.loads((output / "wind_ghost_manifest.json").read_text(encoding="utf-8"))
        assert manifest["frame_count"] == 8 and manifest["canvas_size"] == [512, 512], "incorrect manifest"

        # A second apply must preserve the installed material before replacement.
        overwritten = command("--ghost-dir", ghost_dir, "--fx-dir", fx_dir, "--apply",
                              "--output-dir", output, "--audition-dir", audition, "--log", log)
        assert_ok(overwritten, "overwrite apply")
        backups = list(audition.glob("backup_wind_*"))
        assert backups, "overwrite did not create an audit backup directory"
        assert (backups[0] / "wind_ghost_f1.png").exists(), "backup did not retain overwritten ghost output"


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:  # Keep failures useful when run directly from the repository root.
        print("ERROR " + str(exc), file=sys.stderr)
        sys.exit(1)
    print("test_ingest_wind_sheets: OK")
