#!/usr/bin/env python3
"""Validate and install generated wind-ghost and wind-effect pictures.

By default this is a dry run.  Use --apply only after the generated artwork has
passed the per-frame checks; existing installed files are copied to the audit
backup directory before replacement.
"""
import argparse
import datetime as dt
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

# Reuse the project's established tight chroma key and alpha-bbox rules.
from ingest_queue import box_of, key_full, touches_edge  # noqa: E402

GHOST_NAMES = tuple("wind_ghost_f%d.png" % number for number in range(1, 9))
FX_SOURCES = ("wind_gust_s.png", "wind_gust_m.png", "wind_gust_l.png", "wind_swirl.png")
FX_NAMES = FX_SOURCES
GHOST_SIZE = (2048, 1024)
FX_SIZE = (2048, 512)
CELL_SIZE = (512, 512)
EDGE_MARGIN = 4
MAX_CENTRE_DRIFT = 6.0


class IngestError(Exception):
    """An expected bad input or installation precondition."""


class Reporter:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a", encoding="utf-8")

    def line(self, message):
        stamp = dt.datetime.now().isoformat(timespec="seconds")
        text = "%s %s" % (stamp, message)
        self.handle.write(text + "\n")
        self.handle.flush()
        print(message, file=sys.stderr)

    def close(self):
        self.handle.close()


def require_file(path, description):
    path = Path(path)
    if not path.is_file():
        raise IngestError("missing %s: %s" % (description, path))
    return path


def keyed_image(path):
    """Run ingest_queue.key_full once, then reopen its keyed result safely."""
    try:
        # key_full accepts paths, which keeps this script on the shared keyer.
        return key_full(str(path))
    except (OSError, ValueError) as exc:
        raise IngestError("could not open %s: %s" % (path, exc)) from exc


def validate_picture(image, label):
    box = box_of(image)
    if box is None:
        raise IngestError("%s is empty after tight magenta keying" % label)
    if touches_edge(box, image.size, EDGE_MARGIN):
        raise IngestError("%s touches its picture edge (cut off): %s" % (label, box))
    return box


def crop_equal_cells(image, expected_size, columns, rows, label):
    if image.size != expected_size:
        raise IngestError("%s must be %dx%d, got %dx%d" % (
            label, expected_size[0], expected_size[1], image.width, image.height))
    cells = []
    for row in range(rows):
        for column in range(columns):
            left, top = column * CELL_SIZE[0], row * CELL_SIZE[1]
            cells.append(image.crop((left, top, left + CELL_SIZE[0], top + CELL_SIZE[1])))
    return cells


def load_sheet_mode(ghost_sheet, fx_sheet):
    ghost = keyed_image(require_file(ghost_sheet, "ghost sheet"))
    fx = keyed_image(require_file(fx_sheet, "effect sheet"))
    return crop_equal_cells(ghost, GHOST_SIZE, 4, 2, "ghost sheet"), crop_equal_cells(fx, FX_SIZE, 4, 1, "effect sheet")


def load_directory_mode(ghost_dir, fx_dir):
    ghost_dir, fx_dir = Path(ghost_dir), Path(fx_dir)
    if not ghost_dir.is_dir():
        raise IngestError("ghost directory does not exist: %s" % ghost_dir)
    if not fx_dir.is_dir():
        raise IngestError("effect directory does not exist: %s" % fx_dir)
    ghosts, effects = [], []
    for number in range(1, 9):
        path = require_file(ghost_dir / ("wind_ghost_%d.png" % number), "ghost frame %d" % number)
        image = keyed_image(path)
        if image.size != CELL_SIZE:
            raise IngestError("ghost frame %d must be 512x512, got %dx%d" % (number, image.width, image.height))
        ghosts.append(image)
    for name in FX_SOURCES:
        path = require_file(fx_dir / name, "effect " + name)
        image = keyed_image(path)
        if image.size != CELL_SIZE:
            raise IngestError("effect %s must be 512x512, got %dx%d" % (name, image.width, image.height))
        effects.append(image)
    return ghosts, effects


def ghost_anchor(box):
    return {
        "row": box[3] - 1,
        "bbox_center": [round((box[0] + box[2]) / 2.0, 2), round((box[1] + box[3]) / 2.0, 2)],
        "bbox_size": [box[2] - box[0], box[3] - box[1]],
    }


def validate_ghosts(frames):
    boxes = [validate_picture(frame, "ghost frame %d" % (index + 1)) for index, frame in enumerate(frames)]
    first = boxes[0]
    first_anchor = ghost_anchor(first)
    first_cx, first_cy = first_anchor["bbox_center"]
    first_size = tuple(first_anchor["bbox_size"])
    for index, box in enumerate(boxes[1:], 2):
        anchor = ghost_anchor(box)
        cx, cy = anchor["bbox_center"]
        distance = ((cx - first_cx) ** 2 + (cy - first_cy) ** 2) ** 0.5
        if distance > MAX_CENTRE_DRIFT:
            raise IngestError("ghost frame %d bbox centre drifts %.2f px from frame 1 (maximum %.0f px)" % (
                index, distance, MAX_CENTRE_DRIFT))
        if anchor["row"] != first_anchor["row"]:
            raise IngestError("ghost frame %d anchor row %d differs from frame 1 row %d" % (
                index, anchor["row"], first_anchor["row"]))
        if tuple(anchor["bbox_size"]) != first_size:
            raise IngestError("ghost frame %d scale %s differs from frame 1 scale %s" % (
                index, tuple(anchor["bbox_size"]), first_size))
    return boxes, first_anchor


def validate_effects(frames):
    for name, frame in zip(FX_NAMES, frames):
        validate_picture(frame, name)


def continuity_report(frames, reporter):
    """Use check_continuity's metrics when its optional CV stack is available."""
    try:
        continuity = importlib.import_module("check_continuity")
    except ImportError as exc:
        reporter.line("WARN continuity check unavailable: %s" % exc)
        return
    try:
        with tempfile.TemporaryDirectory(prefix="pk-wind-continuity-") as temp:
            paths = []
            for index, frame in enumerate(frames, 1):
                path = Path(temp) / ("wind_ghost_f%d.png" % index)
                frame.save(path)
                paths.append(str(path))
            report = continuity.analyse_strip(paths, True)
    except Exception as exc:  # check_continuity's optional packages or image parser failed
        raise IngestError("continuity check failed: %s" % exc) from exc

    fatal = {"ERROR", "FACE", "SCALE", "FEET", "JUMP"}
    entries = report["steps"] + ([report["loop_close"]] if report["loop_close"] else [])
    bad = []
    for entry in entries:
        flags = set(entry.get("flags", []))
        if flags & fatal:
            bad.append("%s -> %s (%s)" % (entry["from"], entry["to"], ",".join(sorted(flags & fatal))))
    if bad:
        raise IngestError("continuity check rejected ghost sequence: " + "; ".join(bad))
    reporter.line("OK continuity check: %d steps, median motion %.4f" % (len(report["steps"]), report["median_step"]))


def build_outputs(ghosts, effects, anchor):
    outputs = list(zip(GHOST_NAMES, ghosts)) + list(zip(FX_NAMES, effects))
    manifest = {
        "frame_count": len(ghosts),
        "canvas_size": list(CELL_SIZE),
        "anchor": anchor,
    }
    return outputs, manifest


def write_preview(outputs, manifest, reporter):
    # Keep the preview directory available to the caller for manual art review.
    preview = Path(tempfile.mkdtemp(prefix="pk-wind-preview-"))
    for name, image in outputs:
        image.save(preview / name)
    (preview / "wind_ghost_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    reporter.line("DRY-RUN preview directory: %s" % preview)
    for name, _ in outputs:
        path = preview / name
        print("WOULD WRITE %s (%d bytes)" % (name, path.stat().st_size))
    manifest_path = preview / "wind_ghost_manifest.json"
    print("WOULD WRITE %s (%d bytes)" % (manifest_path.name, manifest_path.stat().st_size))


def install(outputs, manifest, output_dir, audition_dir, reporter):
    output_dir, audition_dir = Path(output_dir), Path(audition_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audition_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_dir = audition_dir / ("backup_wind_" + stamp)
    manifest_name = "wind_ghost_manifest.json"
    names = [name for name, _ in outputs] + [manifest_name]

    with tempfile.TemporaryDirectory(prefix="pk-wind-stage-") as temp:
        stage = Path(temp)
        for name, image in outputs:
            image.save(stage / name)
        (stage / manifest_name).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        existing = [name for name in names if (output_dir / name).exists()]
        if existing:
            backup_dir.mkdir(parents=True, exist_ok=False)
            try:
                for name in existing:
                    shutil.copy2(output_dir / name, backup_dir / name)
            except OSError as exc:
                raise IngestError("could not make overwrite backup in %s: %s" % (backup_dir, exc)) from exc
            reporter.line("BACKUP %d file(s) -> %s" % (len(existing), backup_dir))
        try:
            for name in names:
                os.replace(stage / name, output_dir / name)
        except OSError as exc:
            raise IngestError("could not install staged output: %s" % exc) from exc
    for name in names:
        reporter.line("WROTE %s (%d bytes)" % (output_dir / name, (output_dir / name).stat().st_size))


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--ghost-sheet", help="2048x1024, four-by-two ghost sheet")
    source.add_argument("--ghost-dir", help="directory containing wind_ghost_1.png through wind_ghost_8.png")
    parser.add_argument("--fx-sheet", help="2048x512 gust and swirl sheet (required with --ghost-sheet)")
    parser.add_argument("--fx-dir", help="directory containing wind_gust_s/m/l.png and wind_swirl.png (required with --ghost-dir)")
    parser.add_argument("--apply", action="store_true", help="install validated files; default is a non-destructive dry run")
    parser.add_argument("--output-dir", default=str(ROOT / "assets" / "fx" / "sprites"), help=argparse.SUPPRESS)
    parser.add_argument("--audition-dir", default=str(ROOT / "docs" / "audition"), help=argparse.SUPPRESS)
    parser.add_argument("--log", default=str(ROOT / "docs" / "audition" / "ingest_wind.log"), help="audit log path")
    args = parser.parse_args(argv)
    if bool(args.ghost_sheet) != bool(args.fx_sheet):
        parser.error("--ghost-sheet requires --fx-sheet")
    if bool(args.ghost_dir) != bool(args.fx_dir):
        parser.error("--ghost-dir requires --fx-dir")
    return args


def main(argv=None):
    args = parse_args(argv)
    reporter = Reporter(args.log)
    try:
        reporter.line("START mode=%s apply=%s" % ("sheets" if args.ghost_sheet else "pictures", args.apply))
        if args.ghost_sheet:
            ghosts, effects = load_sheet_mode(args.ghost_sheet, args.fx_sheet)
        else:
            ghosts, effects = load_directory_mode(args.ghost_dir, args.fx_dir)
        boxes, anchor = validate_ghosts(ghosts)
        validate_effects(effects)
        continuity_report(ghosts, reporter)
        outputs, manifest = build_outputs(ghosts, effects, anchor)
        reporter.line("OK validated 8 ghost frames; anchor row %d, bbox %s" % (anchor["row"], anchor["bbox_size"]))
        if args.apply:
            install(outputs, manifest, args.output_dir, args.audition_dir, reporter)
        else:
            write_preview(outputs, manifest, reporter)
        reporter.line("DONE")
        return 0
    except IngestError as exc:
        reporter.line("REJECT %s" % exc)
        return 1
    except Exception as exc:  # Last-resort guard: callers must receive a non-zero failure.
        reporter.line("ERROR unexpected %s: %s" % (type(exc).__name__, exc))
        return 1
    finally:
        reporter.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
