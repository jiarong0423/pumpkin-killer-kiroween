#!/usr/bin/env python3
"""Offline tests for the pending-picture ingestion command."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "ingest_missing_20261115.py"
PYTHON = sys.executable
MAGENTA = (251, 0, 247)


class IngestMissingTests(unittest.TestCase):
    def command(self, root, jobs, drive, *extra):
        return subprocess.run(
            [PYTHON, "-B", str(SCRIPT), "--jobs", str(jobs), "--drive-out", str(drive),
             "--repo-root", str(root), *map(str, extra)],
            cwd=ROOT, text=True, capture_output=True,
        )

    def make_root(self, directory):
        root = directory / "repo"
        (root / "docs").mkdir(parents=True)
        (root / "docs" / "ASSET_PROVENANCE.md").write_text(
            "# Asset provenance\n\n| Folder | What it holds | How it was made | Tool | Date | License status |\n"
            "|---|---|---|---|---|---|\n\nNotes\n", encoding="utf-8")
        return root

    def jobs_file(self, directory, ids):
        path = directory / "jobs.json"
        path.write_text(json.dumps({"jobs": [{"id": job_id} for job_id in ids]}), encoding="utf-8")
        return path

    def sprite(self, path, colour=(30, 180, 100)):
        image = Image.new("RGB", (100, 100), MAGENTA)
        ImageDraw.Draw(image).rectangle((20, 20, 80, 80), fill=colour)
        image.save(path)

    def background(self, path, size=(160, 90), colour=(30, 50, 100)):
        Image.new("RGB", size, colour).save(path)

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory(prefix="pk-missing-test-") as temporary:
            directory = Path(temporary)
            root, drive = self.make_root(directory), directory / "drive"
            drive.mkdir()
            jobs = self.jobs_file(directory, ["bg_belltower", "coin_pumpkin_head", "ghoststar_blow"])
            self.background(drive / "bg_belltower_v1_old.png", colour=(10, 10, 10))
            self.background(drive / "bg_belltower_v1_new.png", colour=(20, 20, 20))
            self.sprite(drive / "coin_pumpkin_head_v1_q3.png")
            self.sprite(drive / "ghoststar_blow_v1_q3.png")
            result = self.command(root, jobs, drive)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ghoststar_blow_v1_q3.png", result.stdout)
            self.assertIn("sprite candidate; not mapped into the page", result.stdout)
            self.assertFalse((root / "assets").exists())
            self.assertFalse((root / "docs" / "audition").exists())
            self.assertNotIn("owner-reviewed: pending", (root / "docs" / "ASSET_PROVENANCE.md").read_text(encoding="utf-8"))

    def test_apply_installs_and_backs_up(self):
        with tempfile.TemporaryDirectory(prefix="pk-missing-test-") as temporary:
            directory = Path(temporary)
            root, drive = self.make_root(directory), directory / "drive"
            drive.mkdir()
            jobs = self.jobs_file(directory, ["bg_belltower", "unit_knight_unarmed", "fx_feet_chain", "coin_pumpkin_tail"])
            self.background(drive / "bg_belltower_v1_q3.png")
            for job_id in ("unit_knight_unarmed", "fx_feet_chain", "coin_pumpkin_tail"):
                self.sprite(drive / (job_id + "_v1_q3.png"))
            old = root / "assets" / "env" / "bg_belltower.png"
            old.parent.mkdir(parents=True)
            old.write_bytes(b"old background")
            result = self.command(root, jobs, drive, "--apply")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "assets" / "units" / "unit_knight_unarmed.png").exists())
            self.assertTrue((root / "assets" / "fx" / "sprites" / "fx_feet_chain.png").exists())
            self.assertTrue((root / "assets" / "fx" / "sprites" / "coin_pumpkin_tail.png").exists())
            backups = list((root / "docs" / "audition").glob("backup_ingest_*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / "assets" / "env" / "bg_belltower.png").read_bytes(), b"old background")
            provenance = (root / "docs" / "ASSET_PROVENANCE.md").read_text(encoding="utf-8")
            self.assertIn("Qwen-Image-Edit on Colab", provenance)
            self.assertIn("owner-reviewed: pending", provenance)
            self.assertTrue((root / "docs" / "audition" / "ingest_missing.log").exists())

    def test_missing_output_exits_one(self):
        with tempfile.TemporaryDirectory(prefix="pk-missing-test-") as temporary:
            directory = Path(temporary)
            root, drive = self.make_root(directory), directory / "drive"
            drive.mkdir()
            jobs = self.jobs_file(directory, ["coin_pumpkin_head"])
            result = self.command(root, jobs, drive)
            self.assertEqual(result.returncode, 1)
            self.assertIn("MISSING coin_pumpkin_head", result.stdout)
            self.assertFalse((root / "assets").exists())

    def test_four_by_three_background_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="pk-missing-test-") as temporary:
            directory = Path(temporary)
            root, drive = self.make_root(directory), directory / "drive"
            drive.mkdir()
            jobs = self.jobs_file(directory, ["bg_pumpkin_field"])
            self.background(drive / "bg_pumpkin_field_v1_q3.png", size=(120, 90))
            result = self.command(root, jobs, drive)
            self.assertEqual(result.returncode, 1)
            self.assertIn("must be a 16:9 background", result.stdout)
            self.assertFalse((root / "assets").exists())


if __name__ == "__main__":
    unittest.main()
