#!/usr/bin/env python3
"""Install the eight pending 2026-11-15 Colab pictures after local review.

The command is a dry run unless --apply is supplied.  It never contacts Drive:
callers provide a folder containing the downloaded PNG files.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import key_magenta_items as keyer  # noqa: E402
from ingest_queue import box_of, key_full  # noqa: E402

BACKGROUND_IDS = {
    "bg_belltower", "bg_pumpkin_field", "bg_ruined_church", "bg_abandoned_school",
    "bg_ruined_church_b", "bg_abandoned_school_b",
}
ITEM_IDS = {"unit_knight_unarmed", "coin_pumpkin_head", "coin_pumpkin_tail",
            "ghoststar_blow", "ghoststar_blow_hard"}
KNOWN_IDS = BACKGROUND_IDS | ITEM_IDS | {"fx_feet_chain"}


class IngestError(Exception):
    """A generated picture or installation precondition is unacceptable."""


def checksum(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def newest_output(folder, job_id):
    matches = list(Path(folder).glob(job_id + "_v1_*.png"))
    if not matches:
        return None
    return max(matches, key=lambda path: (path.stat().st_mtime_ns, path.name))


def background_image(source, job_id):
    try:
        image = Image.open(source)
        image.load()
    except OSError as exc:
        raise IngestError("%s could not be opened: %s" % (job_id, exc)) from exc
    if image.width <= 0 or image.height <= 0 or image.width * 9 != image.height * 16:
        raise IngestError("%s must be a 16:9 background, got %dx%d" % (
            job_id, image.width, image.height))
    return image


def keyed_item(source, job_id):
    try:
        return keyer.key_and_crop(source)
    except (OSError, ValueError) as exc:
        raise IngestError("%s could not be magenta-keyed: %s" % (job_id, exc)) from exc


def keyed_queue_effect(source, job_id):
    """Preserve ingest_queue's existing FX mapping and tight keying rules."""
    try:
        image = key_full(str(source))
        box = box_of(image)
    except (OSError, ValueError) as exc:
        raise IngestError("%s could not be magenta-keyed: %s" % (job_id, exc)) from exc
    if box is None:
        raise IngestError("%s is empty after magenta keying" % job_id)
    pad = 6
    return image.crop((max(0, box[0] - pad), max(0, box[1] - pad),
                       min(image.width, box[2] + pad), min(image.height, box[3] + pad)))


def destination(repo_root, job_id):
    if job_id in BACKGROUND_IDS:
        return repo_root / "assets" / "env" / (job_id + ".png")
    if job_id == "unit_knight_unarmed":
        return repo_root / "assets" / "units" / "unit_knight_unarmed.png"
    return repo_root / "assets" / "fx" / "sprites" / (job_id + ".png")


def prepare(job_id, source, repo_root):
    target = destination(repo_root, job_id)
    if job_id in BACKGROUND_IDS:
        background_image(source, job_id)
        return {"job_id": job_id, "source": source, "target": target, "kind": "copy", "image": None}
    if job_id == "fx_feet_chain":
        image = keyed_queue_effect(source, job_id)
    else:
        image = keyed_item(source, job_id)
    return {"job_id": job_id, "source": source, "target": target, "kind": "key", "image": image}


def stage(plan, directory):
    staged = Path(directory)
    outputs = []
    for entry in plan:
        output = staged / (entry["job_id"] + ".png")
        if entry["kind"] == "copy":
            shutil.copy2(entry["source"], output)
        else:
            entry["image"].save(output)
        outputs.append((entry, output))
    return outputs


def relative_path(repo_root, path):
    return path.relative_to(repo_root)


def backup_targets(repo_root, paths, backup_dir):
    recorded = {}
    for path in paths:
        if not path.exists():
            continue
        if not path.is_file():
            raise IngestError("refusing to replace non-file %s" % path)
        target = backup_dir / relative_path(repo_root, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        recorded[path] = checksum(path)
    return recorded


def require_unchanged(recorded):
    for path, before in recorded.items():
        if not path.is_file() or checksum(path) != before:
            raise IngestError("refusing to overwrite %s: checksum changed after backup" % path)


def provenance_row(entry, date):
    folder = "`%s/`" % relative_path(ROOT, entry["target"]).parent.as_posix()
    what = "`%s` from job `%s`" % (entry["target"].name, entry["job_id"])
    how = "Downloaded output, installed by `scripts/ingest_missing_20261115.py`"
    tool = "Qwen-Image-Edit on Colab"
    licence = "Owner-generated output; owner-reviewed: pending"
    return "| %s | %s | %s | %s | %s | %s |" % (folder, what, how, tool, date, licence)


def append_provenance(path, entries, date, repo_root):
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise IngestError("could not read asset provenance table: %s" % exc) from exc
    marker = "\nNotes\n"
    if marker not in text:
        raise IngestError("asset provenance table has no Notes marker")
    rows = []
    for entry in entries:
        target = entry["target"]
        folder = "`%s/`" % relative_path(repo_root, target).parent.as_posix()
        what = "`%s` from job `%s`" % (target.name, entry["job_id"])
        rows.append("| %s | %s | Downloaded output, installed by `scripts/ingest_missing_20261115.py` | Qwen-Image-Edit on Colab | %s | Owner-generated output; owner-reviewed: pending |" % (folder, what, date))
    return text.replace(marker, "\n" + "\n".join(rows) + marker, 1)


def apply_install(plan, repo_root, log_path):
    provenance = repo_root / "docs" / "ASSET_PROVENANCE.md"
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_dir = repo_root / "docs" / "audition" / ("backup_ingest_" + stamp)
    targets = [entry["target"] for entry in plan] + [provenance]
    existing = [path for path in targets if path.exists()]
    if existing:
        backup_dir.mkdir(parents=True, exist_ok=False)
        recorded = backup_targets(repo_root, existing, backup_dir)
        print("BACKUP %d file(s) -> %s" % (len(existing), backup_dir))
    else:
        recorded = {}

    try:
        provenance_text = append_provenance(provenance, plan, dt.date.today().isoformat(), repo_root)
        with tempfile.TemporaryDirectory(prefix="pk-missing-ingest-") as temporary:
            staged = stage(plan, temporary)
            provenance_stage = Path(temporary) / "ASSET_PROVENANCE.md"
            provenance_stage.write_text(provenance_text, encoding="utf-8")
            require_unchanged(recorded)
            for entry, staged_file in staged:
                entry["target"].parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(staged_file, entry["target"])
                print("WROTE %s" % relative_path(repo_root, entry["target"]))
            require_unchanged({provenance: recorded[provenance]} if provenance in recorded else {})
            shutil.copy2(provenance_stage, provenance)
    except (OSError, IngestError) as exc:
        raise IngestError("installation failed: %s" % exc) from exc

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        for entry in plan:
            handle.write("%s INSTALLED %s <- %s\n" % (
                dt.datetime.now().isoformat(timespec="seconds"),
                relative_path(repo_root, entry["target"]), entry["source"].name))


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", required=True, help="JSON job list from Colab")
    parser.add_argument("--drive-out", required=True, help="folder containing downloaded Colab PNGs")
    parser.add_argument("--apply", action="store_true", help="install validated pictures; default is dry run")
    parser.add_argument("--repo-root", default=str(ROOT), help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    try:
        jobs = json.loads(Path(args.jobs).read_text(encoding="utf-8"))["jobs"]
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        print("ERROR could not read jobs: %s" % exc, file=sys.stderr)
        return 1

    plans, problems = [], 0
    seen = set()
    for job in jobs:
        job_id = job.get("id")
        if job_id not in KNOWN_IDS or job_id in seen:
            print("ERROR unsupported or duplicate job id: %r" % job_id, file=sys.stderr)
            problems += 1
            continue
        seen.add(job_id)
        source = newest_output(args.drive_out, job_id)
        if source is None:
            print("MISSING %s" % job_id)
            problems += 1
            continue
        try:
            plans.append(prepare(job_id, source, repo_root))
        except IngestError as exc:
            print("REJECT %s" % exc)
            problems += 1

    if problems:
        print("done, %d problem(s)" % problems)
        return 1
    for entry in plans:
        action = "COPY" if entry["kind"] == "copy" else "KEY"
        candidate = " (sprite candidate; not mapped into the page)" if entry["job_id"].startswith("ghoststar_") else ""
        print("WOULD %s %s -> %s%s" % (
            action, entry["source"].name, relative_path(repo_root, entry["target"]), candidate))
    if not args.apply:
        print("dry run: no files written")
        return 0

    try:
        apply_install(plans, repo_root, repo_root / "docs" / "audition" / "ingest_missing.log")
    except IngestError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 1
    print("done, %d picture(s) installed" % len(plans))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
