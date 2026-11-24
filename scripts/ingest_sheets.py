#!/usr/bin/env python3
"""Install image2 animation sheets after keying and validating each cell.

The input directory contains <class>_sheet.png, <class>_strip_<name>.png and
<class>_portrait.png.  Sheet cells are ordered row-major.  This program never
resizes a figure: it only places its keyed opaque box on the pose canvas.
"""
import argparse
import datetime as dt
import os
import re
import shutil
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEET_FRAMES = ("idle1", "idle2", "charge1", "charge2", "charge3", "release", "empty", "hit")
STRIP_FRAMES = {
    "idle_loop": ("idle_loop_1", "idle_loop_2", "idle_loop_3", "idle_loop_4"),
    "charge": ("charge_1", "charge_2", "charge_3", "charge_4", "charge_5", "charge_6"),
    "throw": ("throw_1", "throw_2", "throw_3", "throw_4", "throw_5"),
    "hit": ("hit_1", "hit_2", "hit_3"),
}


def key_magenta(image):
    """Use the deliberately tight alpha ramp used by ingest_queue.py."""
    rgb = np.asarray(image.convert("RGB")).astype(float)
    mag = (rgb[..., 0] + rgb[..., 2]) / 2 - rgb[..., 1]
    alpha = np.clip((160 - mag) / 50, 0, 1)
    spill = np.maximum(0, mag) * 0.95 * (1 - alpha)
    rgb[..., 0] = np.clip(rgb[..., 0] - spill, 0, 255)
    rgb[..., 2] = np.clip(rgb[..., 2] - spill, 0, 255)
    return Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA")


def opaque_box(image):
    alpha = np.asarray(image.getchannel("A"))
    rows = np.where((alpha > 128).sum(axis=1) > 6)[0]
    cols = np.where((alpha > 128).sum(axis=0) > 6)[0]
    if not len(rows) or not len(cols):
        return None
    return int(cols.min()), int(rows.min()), int(cols.max()) + 1, int(rows.max()) + 1


def touches_edge(box, size, margin=4):
    return box[0] <= margin or box[1] <= margin or box[2] >= size[0] - margin or box[3] >= size[1] - margin


def parse_grid(value):
    match = re.fullmatch(r"(\d+)x(\d+)", value.lower())
    if not match or min(map(int, match.groups())) < 1:
        raise ValueError("grid must have the form ROWSxCOLS, for example 4x2")
    return tuple(map(int, match.groups()))


def magenta_runs(image, axis):
    """Return broad full-magenta bands; image2 grid gutters are solid bands."""
    a = np.asarray(image.convert("RGB"))
    mag = ((a[..., 0].astype(int) + a[..., 2].astype(int)) // 2 - a[..., 1].astype(int)) > 160
    full = mag.mean(axis=axis) >= 0.995
    runs, start = [], None
    for index, value in enumerate(full):
        if value and start is None:
            start = index
        elif not value and start is not None:
            if index - start >= 2:
                runs.append((start, index))
            start = None
    if start is not None and len(full) - start >= 2:
        runs.append((start, len(full)))
    return runs


def boundaries_from_gutters(runs, length, parts):
    """Put each equal-grid separator at the centre of its nearest magenta band."""
    if parts == 1:
        return [0, length]
    boundaries = [0]
    tolerance = length / parts * 0.30
    for index in range(1, parts):
        expected = length * index / parts
        candidates = [run for run in runs if run[0] - tolerance <= expected <= run[1] + tolerance]
        if not candidates:
            return None
        run = min(candidates, key=lambda item: abs((item[0] + item[1]) / 2.0 - expected))
        boundary = int(round((run[0] + run[1]) / 2.0))
        if boundary <= boundaries[-1] or boundary >= length:
            return None
        boundaries.append(boundary)
    boundaries.append(length)
    return boundaries


def detect_grid(image):
    """Detect the standard eight-cell layout from periodic full-magenta gutters."""
    horizontal, vertical = magenta_runs(image, 1), magenta_runs(image, 0)
    # 4x2 is the documented sheet shape. The alternatives support square-ish exports.
    for row_count, col_count in ((4, 2), (2, 4), (8, 1), (1, 8)):
        ys = boundaries_from_gutters(horizontal, image.height, row_count)
        xs = boundaries_from_gutters(vertical, image.width, col_count)
        if ys and xs:
            return list(zip(ys, ys[1:])), list(zip(xs, xs[1:]))
    raise ValueError("could not detect an eight-cell grid from magenta gutters; pass --grid ROWSxCOLS")


def equal_cells(image, grid):
    rows, cols = grid
    if image.height % rows or image.width % cols:
        raise ValueError("sheet dimensions are not evenly divisible by --grid")
    return ([(r * image.height // rows, (r + 1) * image.height // rows) for r in range(rows)],
            [(c * image.width // cols, (c + 1) * image.width // cols) for c in range(cols)])


def normalize_pose(keyed, box):
    crop = keyed.crop(box)
    if crop.width > 1024 or crop.height > 1000:
        raise ValueError("opaque figure %sx%s does not fit the 1024x1024 standard canvas" % crop.size)
    canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    canvas.paste(crop, ((1024 - crop.width) // 2, 1000 - crop.height), crop)
    return canvas


class Reporter:
    def __init__(self, log_path):
        os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
        self.file = open(log_path, "a", encoding="utf-8")

    def line(self, text):
        self.file.write(text + "\n")
        self.file.flush()
        print(text, file=sys.stderr)

    def close(self):
        self.file.close()


def backup_then_save(image, destination, force, poses_dir):
    if os.path.exists(destination):
        if not force:
            raise FileExistsError("destination already exists (use --force): " + destination)
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup_root = os.path.join(poses_dir, "_replaced", stamp)
        relative = os.path.relpath(destination, poses_dir)
        # Portraits live beside poses, so never let a relative '..' escape the timestamped backup folder.
        if relative == os.pardir or relative.startswith(os.pardir + os.sep):
            relative = os.path.join("external", os.path.basename(destination))
        backup = os.path.join(backup_root, relative)
        os.makedirs(os.path.dirname(backup), exist_ok=True)
        shutil.copy2(destination, backup)
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    image.save(destination)


def install_cell(cell, destination, force, poses_dir):
    keyed = key_magenta(cell)
    box = opaque_box(keyed)
    if box is None:
        raise ValueError("nothing left after magenta keying")
    if touches_edge(box, cell.size):
        raise ValueError("opaque figure touches its cell edge (cut off): %s" % (box,))
    backup_then_save(normalize_pose(keyed, box), destination, force, poses_dir)


def install_portrait(image, destination, force, poses_dir):
    keyed = key_magenta(image)
    box = opaque_box(keyed)
    if box is None:
        raise ValueError("portrait has nothing left after magenta keying")
    if touches_edge(box, image.size):
        raise ValueError("portrait touches its image edge (cut off): %s" % (box,))
    backup_then_save(keyed.crop(box), destination, force, poses_dir)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", help="folder containing image2 sheets and strips")
    parser.add_argument("--grid", default="", help="sheet grid as ROWSxCOLS; detect solid gutters when omitted")
    parser.add_argument("--poses-dir", default=os.path.join(ROOT, "assets", "poses"))
    parser.add_argument("--portraits-dir", default=os.path.join(ROOT, "assets", "portraits"))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--log", default="", help="log path (default: INPUT_DIR/ingest_sheets.log)")
    args = parser.parse_args(argv)
    input_dir = os.path.abspath(args.input_dir)
    log_path = args.log or os.path.join(input_dir, "ingest_sheets.log")
    reporter = Reporter(log_path)
    bad = 0
    try:
        if not os.path.isdir(input_dir):
            reporter.line("ERROR input folder does not exist: " + input_dir)
            return 1
        try:
            grid = parse_grid(args.grid) if args.grid else None
        except ValueError as exc:
            reporter.line("ERROR " + str(exc))
            return 1
        files = sorted(os.listdir(input_dir))
        inputs = [name for name in files if re.fullmatch(r"[A-Za-z0-9-]+_(?:sheet|portrait)\.png", name) or re.fullmatch(r"[A-Za-z0-9-]+_strip_[A-Za-z0-9_]+\.png", name)]
        if not inputs:
            reporter.line("ERROR no recognised sheet, strip, or portrait PNG files in " + input_dir)
            return 1
        for name in inputs:
            path = os.path.join(input_dir, name)
            try:
                image = Image.open(path).convert("RGB")
                sheet = re.fullmatch(r"([A-Za-z0-9-]+)_sheet\.png", name)
                strip = re.fullmatch(r"([A-Za-z0-9-]+)_strip_([A-Za-z0-9_]+)\.png", name)
                portrait = re.fullmatch(r"([A-Za-z0-9-]+)_portrait\.png", name)
                if sheet:
                    cls = sheet.group(1)
                    row_spans, col_spans = equal_cells(image, grid) if grid else detect_grid(image)
                    if len(row_spans) * len(col_spans) != len(SHEET_FRAMES):
                        raise ValueError("sheet has %d cells; the standard sheet requires %d" % (len(row_spans) * len(col_spans), len(SHEET_FRAMES)))
                    for index, (ys, ye) in enumerate(row_spans):
                        for col, (xs, xe) in enumerate(col_spans):
                            frame = SHEET_FRAMES[index * len(col_spans) + col]
                            destination = os.path.join(args.poses_dir, "%s_%s.png" % (cls, frame))
                            try:
                                install_cell(image.crop((xs, ys, xe, ye)), destination, args.force, args.poses_dir)
                                reporter.line("OK %s cell %d,%d -> %s" % (name, index + 1, col + 1, destination))
                            except Exception as exc:  # keep processing all frames
                                reporter.line("ERROR %s cell %d,%d: %s" % (name, index + 1, col + 1, exc))
                                bad += 1
                elif strip:
                    cls, strip_name = strip.groups()
                    frames = STRIP_FRAMES.get(strip_name)
                    if not frames:
                        raise ValueError("unknown strip name %r; expected one of %s" % (strip_name, ", ".join(sorted(STRIP_FRAMES))))
                    if image.width % len(frames):
                        raise ValueError("strip width is not evenly divisible by its %d frames" % len(frames))
                    width = image.width // len(frames)
                    for index, frame in enumerate(frames):
                        destination = os.path.join(args.poses_dir, "%s_%s.png" % (cls, frame))
                        try:
                            install_cell(image.crop((index * width, 0, (index + 1) * width, image.height)), destination, args.force, args.poses_dir)
                            reporter.line("OK %s cell %d -> %s" % (name, index + 1, destination))
                        except Exception as exc:
                            reporter.line("ERROR %s cell %d: %s" % (name, index + 1, exc))
                            bad += 1
                elif portrait:
                    cls = portrait.group(1)
                    destination = os.path.join(args.portraits_dir, "%s_portrait.png" % cls)
                    install_portrait(image, destination, args.force, args.poses_dir)
                    reporter.line("OK %s -> %s" % (name, destination))
            except Exception as exc:
                reporter.line("ERROR %s: %s" % (name, exc))
                bad += 1
        reporter.line("done, %d rejected or failed cell(s)" % bad)
        return 1 if bad else 0
    finally:
        reporter.close()


if __name__ == "__main__":
    sys.exit(main())
