#!/usr/bin/env python3
"""Check installed picture assets and generate their manifest.

Pillow is the only non-stdlib dependency. The checker deliberately parses only
literal page data: it never imports or executes browser JavaScript.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path("docs/ASSET_MANIFEST.json")
LOG_PATH = Path("docs/audition/asset_pipeline.log")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
MANAGED_DIRS = (
    "assets/avatars",
    "assets/portraits",
    "assets/poses",
    "assets/units",
    "assets/ui",
    "assets/fx",
    "assets/env",
    "assets/weapons",
)
ASSET_PATH = re.compile(r"assets/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+")
IMAGE_VALUE = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\s*:\s*"(assets/[^"]+)"')
POSE_ENTRY = re.compile(r"(unit_[a-z0-9_]+)\s*:\s*\{([^{}]*)\}", re.DOTALL)
POSE_VALUE = re.compile(r"([a-z][a-z0-9_]*)\s*:\s*\"([a-z][a-z0-9_]*)\"")
MAGENTA = (255, 0, 255)


class Problems:
    def __init__(self) -> None:
        self.rows: list[dict[str, str]] = []
        self._seen: set[tuple[str, str]] = set()

    def add(self, path: str, rule: str) -> None:
        path = path.replace("\\", "/")
        key = (path, rule)
        if key not in self._seen:
            self._seen.add(key)
            self.rows.append({"path": path, "rule": rule})

    def for_path(self, path: str) -> list[str]:
        return sorted(row["rule"] for row in self.rows if row["path"] == path)


def relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def object_block(source: str, marker: str) -> str:
    start = source.find(marker)
    if start < 0:
        return ""
    start = source.find("{", start)
    if start < 0:
        return ""
    depth = 0
    for index in range(start, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start + 1:index]
    return ""


def page_data(root: Path, problems: Problems) -> tuple[dict[str, str], dict[str, dict[str, str]], dict[str, str]]:
    index = root / "index.html"
    if not index.is_file():
        problems.add("index.html", "missing-index")
        return {}, {}, {}
    source = index.read_text(encoding="utf-8")
    images = dict(IMAGE_VALUE.findall(object_block(source, "const imgList")))
    portraits = dict(IMAGE_VALUE.findall(object_block(source, "const DOCK_PORTRAIT")))
    poses: dict[str, dict[str, str]] = {}
    for unit_key, values in POSE_ENTRY.findall(object_block(source, "const POSE_SETS")):
        poses[unit_key] = dict(POSE_VALUE.findall(values))
    return images, poses, portraits


def load_heroes(root: Path, problems: Problems) -> list[str]:
    source = root / "shared/heroes.json"
    if not source.is_file():
        problems.add("shared/heroes.json", "missing-hero-list")
        return []
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        problems.add("shared/heroes.json", "invalid-hero-list")
        return []
    if not isinstance(data, dict):
        problems.add("shared/heroes.json", "invalid-hero-list")
        return []
    return sorted(key for key in data if re.fullmatch(r"[a-z][a-z0-9_]*", key))


def required_files(hero: str, images: dict[str, str], poses: dict[str, dict[str, str]], portraits: dict[str, str], problems: Problems) -> dict[str, str]:
    files = {
        "avatar": f"assets/avatars/avatar_{hero}.png",
    }
    portrait = portraits.get(hero)
    if portrait is None:
        problems.add(f"assets/portraits/{hero}_front.png", "missing-dock-portrait-key")
    else:
        files["portrait"] = portrait
    unit_key = f"unit_{hero}"
    if unit_key not in images:
        problems.add(f"assets/units/unit_{hero}.png", "missing-unit-image-key")
    else:
        files["unit"] = images[unit_key]
    pose_set = poses.get(unit_key)
    if pose_set is None:
        problems.add(f"assets/poses/{hero}_windup.png", "missing-pose-set")
        return files
    for action in ("windup", "release", "hit"):
        image_key = pose_set.get(action)
        if image_key is None:
            problems.add(f"assets/poses/{hero}_{action}.png", f"missing-pose-{action}")
        elif image_key not in images:
            problems.add(f"assets/poses/{hero}_{action}.png", f"unresolved-pose-{action}")
        else:
            files[action] = images[image_key]
    return files


def filename_rule(rel: str, hero_ids: set[str], legacy_paths: set[str]) -> str | None:
    path = Path(rel)
    name = path.name
    parent = path.parent.as_posix()
    if rel in legacy_paths:
        return None
    if parent == "assets/avatars":
        if not re.fullmatch(r"avatar_[a-z][a-z0-9_]*\.png", name):
            return "filename-avatar"
        hero = name[len("avatar_"):-4]
        if hero not in hero_ids:
            return "filename-unknown-hero"
    elif parent == "assets/portraits" and not re.fullmatch(r"[a-z][a-z0-9_]*_front\.png", name):
        return "filename-portrait"
    elif parent == "assets/units" and not re.fullmatch(r"unit_[a-z][a-z0-9_]*(?:_[a-z0-9_]+)*\.png", name):
        return "filename-unit"
    elif parent == "assets/poses" and not re.fullmatch(r"(?:pose_)?[a-z][a-z0-9_]*_[a-z][a-z0-9_]*\.png", name):
        return "filename-pose"
    elif parent.startswith("assets/fx") and name.startswith("fx_") and not re.fullmatch(r"fx_[a-z0-9_]+\.png", name):
        return "filename-fx"
    elif parent == "assets/env" and name.startswith("bg_") and not re.fullmatch(r"bg_[a-z0-9_]+\.png", name):
        return "filename-background"
    return None


def magenta_percent(image: Image.Image) -> float:
    rgba = image.convert("RGBA")
    total = 0
    matches = 0
    limit_sq = 60 * 60
    for red, green, blue, alpha in rgba.get_flattened_data():
        if alpha == 0:
            continue
        total += 1
        distance_sq = (red - MAGENTA[0]) ** 2 + (green - MAGENTA[1]) ** 2 + (blue - MAGENTA[2]) ** 2
        if distance_sq <= limit_sq:
            matches += 1
    return 0.0 if total == 0 else 100.0 * matches / total


def requires_rgba(rel: str) -> bool:
    path = Path(rel)
    scene_background = path.parent.as_posix() == "assets/env" and path.name.startswith("bg_") and path.suffix == ".png"
    raw_unit_source = path.parent.as_posix() == "assets/units" and path.name.endswith("_raw.png")
    return not (scene_background or raw_unit_source)


def check_picture(root: Path, path: Path, problems: Problems, hero_ids: set[str], legacy_paths: set[str]) -> dict[str, Any] | None:
    rel = relative(root, path)
    if not path.is_file():
        problems.add(rel, "missing-file")
        return None
    rule = filename_rule(rel, hero_ids, legacy_paths)
    if rule:
        problems.add(rel, rule)
    try:
        with Image.open(path) as image:
            image.load()
            size = list(image.size)
            mode = image.mode
            if mode != "RGBA" and requires_rgba(rel):
                problems.add(rel, "not-rgba")
            if image.width < 128 or image.height < 128:
                problems.add(rel, "smaller-than-128")
            magenta = magenta_percent(image)
            if magenta > 10.0:
                problems.add(rel, "magenta-pixels-%.2f-percent" % magenta)
            if path.parent.name == "avatars":
                if image.size != (256, 256):
                    problems.add(rel, "avatar-size-not-256-square")
                corners = ((0, 0), (image.width - 1, 0), (0, image.height - 1), (image.width - 1, image.height - 1))
                rgba = image.convert("RGBA")
                if any(rgba.getpixel(corner)[3] != 0 for corner in corners):
                    problems.add(rel, "avatar-corners-not-transparent")
    except (OSError, UnidentifiedImageError) as error:
        problems.add(rel, "unreadable-image-%s" % type(error).__name__.lower())
        return None
    return {"size": size, "mode": mode, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "magenta_percent": round(magenta, 4)}


def managed_pictures(root: Path) -> list[Path]:
    files: list[Path] = []
    for directory in MANAGED_DIRS:
        base = root / directory
        if base.is_dir():
            files.extend(path for path in base.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)
    return sorted(set(files))


def referenced_assets(root: Path) -> set[str]:
    sources = [root / "index.html", root / "sw.js"]
    for directory in (root / "js", root / "css"):
        if directory.is_dir():
            sources.extend(path for path in directory.rglob("*") if path.is_file())
    refs: set[str] = set()
    for source in sources:
        if source.is_file():
            refs.update(ASSET_PATH.findall(source.read_text(encoding="utf-8")))
    return refs


def check_references(root: Path, problems: Problems) -> None:
    for ref in sorted(referenced_assets(root)):
        if not (root / ref).is_file():
            problems.add(ref, "referenced-file-missing")


def manifest_data(root: Path, hero_files: dict[str, dict[str, str]], metadata: dict[str, dict[str, Any] | None], problems: Problems) -> dict[str, Any]:
    heroes: dict[str, Any] = {}
    for hero, files in sorted(hero_files.items()):
        file_rows: dict[str, Any] = {}
        passed = True
        for role, rel in sorted(files.items()):
            errors = problems.for_path(rel)
            file_rows[role] = {"path": rel, "metadata": metadata.get(rel), "passed": not errors, "errors": errors}
            passed = passed and not errors
        heroes[hero] = {"files": file_rows, "passed": passed}
    pictures = {
        rel: {"metadata": record, "passed": not problems.for_path(rel), "errors": problems.for_path(rel)}
        for rel, record in sorted(metadata.items())
    }
    return {"version": 1, "heroes": heroes, "pictures": pictures}


def write_log(root: Path, error_count: int, checked: int, mode: str) -> None:
    log = root / LOG_PATH
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as handle:
        handle.write("%s mode=%s checked=%d errors=%d\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), mode, checked, error_count))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hero", help="check one hero's required picture set")
    parser.add_argument("--path", help="check one picture path")
    parser.add_argument("--json", action="store_true", help="write machine-readable output")
    parser.add_argument("--manifest", action="store_true", help="write the generated asset manifest")
    parser.add_argument("--check", action="store_true", help="with --manifest, check whether it is current")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.check and not args.manifest:
        parser.error("--check requires --manifest")
    if args.hero and args.path:
        parser.error("--hero and --path are mutually exclusive")

    root = args.root.resolve()
    problems = Problems()
    heroes = load_heroes(root, problems)
    hero_ids = set(heroes)
    images, poses, portraits = page_data(root, problems)
    all_required = {} if args.path and not args.manifest else {
        hero: required_files(hero, images, poses, portraits, problems) for hero in heroes
    }
    selected_heroes = [] if args.path else ([args.hero] if args.hero else heroes)
    if args.hero and args.hero not in hero_ids:
        problems.add("shared/heroes.json", "unknown-hero-%s" % args.hero)
        selected_heroes = []
    selected_files = {hero: all_required[hero] for hero in selected_heroes}
    legacy_paths = set(images.values()) | set(portraits.values())
    metadata: dict[str, dict[str, Any] | None] = {}

    if args.path:
        candidate = Path(args.path)
        path = candidate if candidate.is_absolute() else root / candidate
        metadata[relative(root, path)] = check_picture(root, path, problems, hero_ids, legacy_paths)
    else:
        if args.hero:
            paths = {rel for files in selected_files.values() for rel in files.values()}
        else:
            paths = {relative(root, path) for path in managed_pictures(root)}
            paths.update(rel for files in selected_files.values() for rel in files.values())
            check_references(root, problems)
        for rel in sorted(paths):
            metadata[rel] = check_picture(root, root / rel, problems, hero_ids, legacy_paths)

    if args.hero and args.hero in selected_files:
        for rel in selected_files[args.hero].values():
            if not (root / rel).is_file():
                problems.add(rel, "required-hero-picture-missing")
    elif not args.path:
        for files in selected_files.values():
            for rel in files.values():
                if not (root / rel).is_file():
                    problems.add(rel, "required-hero-picture-missing")

    output_manifest: dict[str, Any] | None = None
    manifest_stale = False
    if args.manifest:
        output_manifest = manifest_data(root, all_required, metadata, problems)
        manifest_text = json.dumps(output_manifest, indent=2, sort_keys=True) + "\n"
        manifest_path = root / MANIFEST_PATH
        existing = manifest_path.read_text(encoding="utf-8") if manifest_path.is_file() else None
        manifest_stale = existing != manifest_text
        if args.check:
            if manifest_stale:
                problems.add(MANIFEST_PATH.as_posix(), "manifest-stale")
        else:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(manifest_text, encoding="utf-8")

    problems.rows.sort(key=lambda row: (row["path"], row["rule"]))
    mode = "path" if args.path else ("hero" if args.hero else "repository")
    write_log(root, len(problems.rows), len(metadata), mode)
    result = {"errors": problems.rows, "summary": {"checked": len(metadata), "errors": len(problems.rows), "manifest_stale": manifest_stale}}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for row in problems.rows:
            print("ERROR %s %s" % (row["path"], row["rule"]))
        print("SUMMARY checked=%d errors=%d" % (len(metadata), len(problems.rows)))
    if args.manifest and args.check and manifest_stale:
        return 3
    return 1 if problems.rows else 0


if __name__ == "__main__":
    sys.exit(main())
