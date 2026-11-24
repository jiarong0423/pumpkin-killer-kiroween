#!/usr/bin/env python3
"""Score magenta-background ghost test images without third-party packages.

Usage:
  python3 -B scripts/score_ghost_tests.py --reference REF.png \
    --model A=out/testA_puff.png,out/testA_hard.png --metadata out/testA_metrics.json

Each metadata file is optional.  Cells write {"model": "B", "records":
[{"file": "testB_puff.png", "seconds": 1.2, "peak_vram_mb": 1234}]}; a
clip may instead use top-level run_seconds and peak_vram_mb.
"""
import argparse
import json
import math
import os
import struct
import sys
import zlib
from collections import Counter

MAGENTA = (251, 0, 247)
# These are deliberately conservative gates for a first, cross-model audition.
LIMITS = {
    "background_noise": 8.0,
    "halo_width": 12.0,
    "palette_distance": 0.35,
    "scale_min": 0.70,
    "scale_max": 1.45,
    "min_foreground_pixels": 64,
}


def read_png(path):
    """Return RGB rows for an 8-bit, non-interlaced RGB/RGBA PNG.

    Generated audition files are PNGs. Keeping this reader stdlib-only makes the
    scorer and its synthetic test runnable where Pillow/numpy are unavailable.
    """
    raw = open(path, "rb").read()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("expected PNG")
    pos, chunks = 8, []
    while pos < len(raw):
        length = struct.unpack(">I", raw[pos:pos + 4])[0]
        kind = raw[pos + 4:pos + 8]
        data = raw[pos + 8:pos + 8 + length]
        pos += 12 + length
        chunks.append((kind, data))
        if kind == b"IEND":
            break
    ihdr = next((data for kind, data in chunks if kind == b"IHDR"), None)
    if ihdr is None:
        raise ValueError("missing IHDR")
    width, height, depth, colour, compression, filt, interlace = struct.unpack(">IIBBBBB", ihdr)
    if depth != 8 or colour not in (2, 6) or compression or filt or interlace:
        raise ValueError("only 8-bit non-interlaced RGB/RGBA PNG is supported")
    channels = 4 if colour == 6 else 3
    data = zlib.decompress(b"".join(part for kind, part in chunks if kind == b"IDAT"))
    stride, previous, rows, offset = width * channels, [0] * (width * channels), [], 0
    for _ in range(height):
        filter_type = data[offset]
        source = list(data[offset + 1:offset + 1 + stride])
        offset += stride + 1
        row = [0] * stride
        for i, value in enumerate(source):
            left = row[i - channels] if i >= channels else 0
            up = previous[i]
            up_left = previous[i - channels] if i >= channels else 0
            if filter_type == 0:
                result = value
            elif filter_type == 1:
                result = (value + left) & 255
            elif filter_type == 2:
                result = (value + up) & 255
            elif filter_type == 3:
                result = (value + ((left + up) // 2)) & 255
            elif filter_type == 4:
                p, pa, pb, pc = left + up - up_left, 0, 0, 0
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - up_left)
                result = (value + (left if pa <= pb and pa <= pc else up if pb <= pc else up_left)) & 255
            else:
                raise ValueError("unknown PNG row filter")
            row[i] = result
        previous = row
        pixels = []
        for x in range(width):
            start = x * channels
            r, g, b = row[start:start + 3]
            if channels == 4 and row[start + 3] < 128:
                r, g, b = MAGENTA
            pixels.append((r, g, b))
        rows.append(pixels)
    return rows


def magentaness(pixel):
    return (pixel[0] + pixel[2]) / 2.0 - pixel[1]


def alpha_tight(pixel):
    return max(0.0, min(1.0, (160.0 - magentaness(pixel)) / 50.0))


def foreground_mask(rows, threshold):
    return [[alpha_tight(pixel) >= threshold for pixel in row] for row in rows]


def bbox(mask):
    points = [(x, y) for y, row in enumerate(mask) for x, present in enumerate(row) if present]
    if not points:
        return None
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def background_noise(rows):
    """RMS RGB standard deviation over pixels close to the known flat matte."""
    samples = [p for row in rows for p in row if max(abs(p[i] - MAGENTA[i]) for i in range(3)) <= 45]
    if len(samples) < 64:
        return float("inf")
    means = [sum(p[i] for p in samples) / len(samples) for i in range(3)]
    variances = [sum((p[i] - means[i]) ** 2 for p in samples) / len(samples) for i in range(3)]
    return math.sqrt(sum(variances) / 3.0)


def halo_width(rows):
    """95th-percentile local soft-edge width after the ingest_queue tight key.

    Only soft pixels within 24 px of the opaque silhouette count. This prevents a
    deliberately separate mist puff from being reported as a violet edge halo.
    """
    loose, solid = foreground_mask(rows, 0.05), foreground_mask(rows, 0.95)
    height, width, far = len(rows), len(rows[0]), 25
    distance = [[0 if solid[y][x] else far for x in range(width)] for y in range(height)]
    for y in range(height):
        for x in range(width):
            if distance[y][x]:
                neighbours = []
                if x:
                    neighbours.append(distance[y][x - 1])
                if y:
                    neighbours.extend((distance[y - 1][x], distance[y - 1][x - 1] if x else far,
                                       distance[y - 1][x + 1] if x + 1 < width else far))
                if neighbours:
                    distance[y][x] = min(distance[y][x], min(neighbours) + 1)
    for y in range(height - 1, -1, -1):
        for x in range(width - 1, -1, -1):
            if distance[y][x]:
                neighbours = []
                if x + 1 < width:
                    neighbours.append(distance[y][x + 1])
                if y + 1 < height:
                    neighbours.extend((distance[y + 1][x], distance[y + 1][x - 1] if x else far,
                                       distance[y + 1][x + 1] if x + 1 < width else far))
                if neighbours:
                    distance[y][x] = min(distance[y][x], min(neighbours) + 1)
    widths = [distance[y][x] for y in range(height) for x in range(width)
              if loose[y][x] and not solid[y][x] and distance[y][x] < far]
    if not widths:
        return 0.0
    widths.sort()
    return float(widths[min(len(widths) - 1, int(len(widths) * 0.95))])


def palette_histogram(rows):
    foreground = foreground_mask(rows, 0.95)
    bins = Counter()
    count = 0
    for row, mask_row in zip(rows, foreground):
        for pixel, included in zip(row, mask_row):
            if included:
                bins[tuple(channel * 6 // 256 for channel in pixel)] += 1
                count += 1
    if not count:
        return None
    return {key: value / count for key, value in bins.items()}


def palette_distance(reference, candidate):
    a, b = palette_histogram(reference), palette_histogram(candidate)
    if not a or not b:
        return float("inf")
    return 0.5 * sum(abs(a.get(key, 0.0) - b.get(key, 0.0)) for key in set(a) | set(b))


def scale_ratio(reference, candidate):
    rb, cb = bbox(foreground_mask(reference, 0.95)), bbox(foreground_mask(candidate, 0.95))
    if not rb or not cb or rb[3] == rb[1]:
        return 0.0
    return (cb[3] - cb[1]) / float(rb[3] - rb[1])


def score_image(reference, candidate):
    candidate_mask = foreground_mask(candidate, 0.95)
    foreground_count = sum(sum(row) for row in candidate_mask)
    reference_count = sum(sum(row) for row in foreground_mask(reference, 0.95))
    result = {
        "background_noise": background_noise(candidate),
        "halo_width": halo_width(candidate),
        "palette_distance": palette_distance(reference, candidate),
        "silhouette_ratio": foreground_count / float(reference_count) if reference_count else 0.0,
        "scale_ratio": scale_ratio(reference, candidate),
        "foreground_pixels": foreground_count,
    }
    failures = []
    if result["background_noise"] > LIMITS["background_noise"]:
        failures.append("background-noise")
    if result["halo_width"] > LIMITS["halo_width"]:
        failures.append("halo-width")
    if result["palette_distance"] > LIMITS["palette_distance"]:
        failures.append("palette")
    if not LIMITS["scale_min"] <= result["scale_ratio"] <= LIMITS["scale_max"]:
        failures.append("scale")
    if foreground_count < LIMITS["min_foreground_pixels"]:
        failures.append("empty-after-tight-key")
    result["pass"] = not failures
    result["failures"] = failures
    return result


def parse_model(value):
    if "=" not in value:
        raise argparse.ArgumentTypeError("--model needs NAME=IMAGE[,IMAGE...]")
    name, images = value.split("=", 1)
    if not name or not images:
        raise argparse.ArgumentTypeError("--model needs a name and at least one image")
    return name, images.split(",")


def load_metadata(paths):
    records, runs = {}, {}
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        model = data.get("model", "")
        if "run_seconds" in data or "peak_vram_mb" in data:
            runs[model] = (data.get("run_seconds"), data.get("peak_vram_mb"))
        for record in data.get("records", []):
            records[record.get("file", "")] = record
    return records, runs


def fmt(value, digits=2):
    return "n/a" if value is None or math.isinf(value) else ("%%.%df" % digits) % value


def main(argv=None):
    parser = argparse.ArgumentParser(description="Gate ghost outputs against a magenta reference.")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--model", action="append", type=parse_model, required=True)
    parser.add_argument("--metadata", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        reference = read_png(args.reference)
    except Exception as error:  # noqa: BLE001 - command-line diagnostic
        print("ERROR reference: %s" % error, file=sys.stderr)
        return 2
    records, runs = load_metadata(args.metadata)
    total_failed, summary = 0, []
    for model, images in args.model:
        passed, seconds, vram = 0, [], []
        for path in images:
            try:
                result = score_image(reference, read_png(path))
                record = records.get(os.path.basename(path), {})
                if record.get("seconds") is not None:
                    seconds.append(float(record["seconds"]))
                if record.get("peak_vram_mb") is not None:
                    vram.append(float(record["peak_vram_mb"]))
                status = "PASS" if result["pass"] else "FAIL " + ",".join(result["failures"])
                print("%s %s: bg_std=%s halo_px=%s palette=%s silhouette=%s scale=%s keyable=%s seconds=%s vram_mb=%s" % (
                    model, os.path.basename(path), fmt(result["background_noise"]), fmt(result["halo_width"]),
                    fmt(result["palette_distance"], 3), fmt(result["silhouette_ratio"], 3), fmt(result["scale_ratio"], 3), status,
                    fmt(record.get("seconds")), fmt(record.get("peak_vram_mb"), 0)))
                passed += int(result["pass"])
                total_failed += int(not result["pass"])
            except Exception as error:  # noqa: BLE001 - keep remaining candidates visible
                print("%s %s: ERROR %s" % (model, os.path.basename(path), error))
                total_failed += 1
        run_seconds, run_vram = runs.get(model, (None, None))
        summary.append((model, sum(seconds) if seconds else run_seconds,
                        max(vram) if vram else run_vram, "%d/%d" % (passed, len(images))))
    print("\nmodel | seconds | peak VRAM MB | passes")
    print("------|---------|--------------|-------")
    for model, seconds, vram, passed in summary:
        print("%s | %s | %s | %s" % (model, fmt(seconds), fmt(vram, 0), passed))
    return 1 if total_failed else 0


if __name__ == "__main__":
    sys.exit(main())
