#!/usr/bin/env python3
"""Render dark-backdrop GIF previews and labelled contact sheets for pose strips."""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from check_continuity import ordered_strips  # noqa: E402

BACKGROUND = (29, 25, 48)


def log(message, handle):
    handle.write(message + "\n")
    handle.flush()
    print(message, file=sys.stderr)


def composited(path):
    source = Image.open(path).convert("RGBA")
    background = Image.new("RGBA", source.size, BACKGROUND + (255,))
    background.alpha_composite(source)
    return background.convert("RGB")


def flags_by_frame(report):
    flags = {}
    for step in report.get("steps", []):
        if step.get("flags"):
            flags.setdefault(step["to"], []).extend(step["flags"])
    closing = report.get("loop_close")
    if closing and closing.get("flags"):
        flags.setdefault(closing["from"], []).extend(closing["flags"])
    for copy in report.get("copies", []):
        flags.setdefault(copy["from"], []).extend(copy["flags"])
        flags.setdefault(copy["to"], []).extend(copy["flags"])
    return {key: sorted(set(value)) for key, value in flags.items()}


def make_contact(paths, report, destination):
    frames = [composited(path) for path in paths]
    thumb_size = 256
    label_height = 42
    width = thumb_size * len(frames)
    sheet = Image.new("RGB", (width, thumb_size + label_height), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    flags = flags_by_frame(report)
    for index, (frame, path) in enumerate(zip(frames, paths)):
        frame.thumbnail((thumb_size - 8, thumb_size - 8), Image.Resampling.LANCZOS)
        x = index * thumb_size + (thumb_size - frame.width) // 2
        y = (thumb_size - frame.height) // 2
        sheet.paste(frame, (x, y))
        name = os.path.splitext(os.path.basename(path))[0]
        label = name + (" " + "/".join(flags[name]) if name in flags else "")
        colour = (255, 116, 117) if name in flags else (230, 226, 255)
        draw.text((index * thumb_size + 5, thumb_size + 5), label, fill=colour, font=font)
    sheet.save(destination)


def write_thumbnails(paths, directory):
    os.makedirs(directory, exist_ok=True)
    for path in paths:
        image = composited(path)
        image.thumbnail((360, 360), Image.Resampling.LANCZOS)
        name = os.path.splitext(os.path.basename(path))[0] + ".jpg"
        image.save(os.path.join(directory, name), quality=84)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--poses-dir", default=os.path.join(ROOT, "assets", "poses"))
    parser.add_argument("--class", dest="class_name", default="")
    parser.add_argument("--strip", default="")
    parser.add_argument("--continuity-json", default="continuity.json")
    parser.add_argument("--output-dir", default="strip_previews")
    parser.add_argument("--thumbnail-dir", default="", help="optional make_review_html-compatible dark JPG thumbnails")
    parser.add_argument("--duration", type=int, default=120, help="milliseconds per frame")
    parser.add_argument("--loop", type=int, default=0, help="GIF loop count; 0 means forever")
    parser.add_argument("--log", default="")
    args = parser.parse_args(argv)
    if args.duration <= 0 or args.loop < 0:
        print("ERROR --duration must be positive and --loop cannot be negative", file=sys.stderr)
        return 1
    try:
        with open(args.continuity_json, encoding="utf-8") as handle:
            continuity = json.load(handle).get("strips", {})
    except FileNotFoundError:
        continuity = {}
    except (OSError, json.JSONDecodeError) as exc:
        print("ERROR unable to read continuity JSON: %s" % exc, file=sys.stderr)
        return 1
    os.makedirs(args.output_dir, exist_ok=True)
    log_path = args.log or os.path.join(args.output_dir, "make_strip_gif.log")
    bad = 0
    with open(log_path, "a", encoding="utf-8") as handle:
        strips = ordered_strips(args.poses_dir, args.class_name, args.strip)
        if not strips:
            log("ERROR no matching installed strips in " + args.poses_dir, handle)
            return 1
        for (cls, strip), paths in sorted(strips.items()):
            key = cls + ":" + strip
            try:
                frames = [composited(path) for path in paths]
                gif = os.path.join(args.output_dir, "%s_%s.gif" % (cls, strip))
                contact = os.path.join(args.output_dir, "%s_%s_contact.png" % (cls, strip))
                frames[0].save(gif, save_all=True, append_images=frames[1:], duration=args.duration, loop=args.loop, disposal=2)
                make_contact(paths, continuity.get(key, {}), contact)
                if args.thumbnail_dir:
                    write_thumbnails(paths, args.thumbnail_dir)
                log("OK %s: %s, %s" % (key, gif, contact), handle)
            except Exception as exc:  # one corrupt strip must not hide the others
                log("ERROR %s: %s" % (key, exc), handle)
                bad += 1
        log("done, %d failed strip(s)" % bad, handle)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
