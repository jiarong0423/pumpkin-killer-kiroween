#!/usr/bin/env python3
"""Tests for the Pillow-based asset pipeline checker."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

SCRIPT = Path(__file__).with_name("check_asset_pipeline.py")


class TestAssetPipeline(unittest.TestCase):
    def make_tree(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        for directory in ("assets/avatars", "assets/portraits", "assets/poses", "assets/units", "assets/ui", "assets/fx", "assets/env", "assets/weapons", "js", "css", "shared"):
            (root / directory).mkdir(parents=True, exist_ok=True)
        (root / "shared/heroes.json").write_text('{"alpha": {}}\n', encoding="utf-8")
        (root / "index.html").write_text(
            """const imgList = {
  unit_alpha: \"assets/units/unit_alpha.png\",
  pose_alpha_windup: \"assets/poses/alpha_windup.png\",
  pose_alpha_release: \"assets/poses/alpha_release.png\",
  pose_alpha_hit: \"assets/poses/alpha_hit.png\"
};
const POSE_SETS = {
  unit_alpha: { windup: \"pose_alpha_windup\", release: \"pose_alpha_release\", hit: \"pose_alpha_hit\" }
};
const DOCK_PORTRAIT = { alpha: \"assets/ui/portrait_alpha.png\" };
""",
            encoding="utf-8",
        )
        (root / "sw.js").write_text('const x = "assets/ui/fx_ok.png";\n', encoding="utf-8")
        return temp

    def picture(self, root: Path, relative: str, *, size: tuple[int, int] = (256, 256), mode: str = "RGBA", magenta: bool = False, corner_alpha: int = 0) -> None:
        color = (255, 0, 255, 255) if magenta else (20, 40, 60, 255)
        image = Image.new("RGBA", size, color)
        if mode == "RGB":
            image = image.convert("RGB")
        elif corner_alpha == 0:
            for point in ((0, 0), (size[0] - 1, 0), (0, size[1] - 1), (size[0] - 1, size[1] - 1)):
                image.putpixel(point, (20, 40, 60, 0))
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(target)

    def good_files(self, root: Path) -> None:
        for relative in (
            "assets/avatars/avatar_alpha.png",
            "assets/ui/portrait_alpha.png",
            "assets/units/unit_alpha.png",
            "assets/poses/alpha_windup.png",
            "assets/poses/alpha_release.png",
            "assets/poses/alpha_hit.png",
            "assets/ui/fx_ok.png",
        ):
            self.picture(root, relative)

    def run_checker(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", str(root), *args], text=True, capture_output=True, check=False)

    def test_good_repository_passes_and_writes_manifest(self) -> None:
        with self.make_tree() as temp:
            root = Path(temp)
            self.good_files(root)
            result = self.run_checker(root, "--manifest")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SUMMARY checked=7 errors=0", result.stdout)
            manifest = json.loads((root / "docs/ASSET_MANIFEST.json").read_text(encoding="utf-8"))
            avatar = manifest["heroes"]["alpha"]["files"]["avatar"]
            self.assertEqual(avatar["metadata"]["size"], [256, 256])
            self.assertEqual(len(avatar["metadata"]["sha256"]), 64)
            self.assertTrue(avatar["passed"])
            self.assertEqual(manifest["heroes"]["alpha"]["files"]["portrait"]["path"], "assets/ui/portrait_alpha.png")
            self.assertIn("assets/ui/fx_ok.png", manifest["pictures"])
            self.assertEqual(self.run_checker(root, "--manifest", "--check").returncode, 0)

    def test_rejected_images_name_and_missing_pose_report_specific_rules(self) -> None:
        with self.make_tree() as temp:
            root = Path(temp)
            self.good_files(root)
            self.picture(root, "assets/avatars/avatar_alpha.png", mode="RGB")
            self.picture(root, "assets/poses/alpha_windup.png", magenta=True)
            self.picture(root, "assets/avatars/not_an_avatar.png")
            (root / "assets/poses/alpha_release.png").unlink()
            result = self.run_checker(root)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("ERROR assets/avatars/avatar_alpha.png not-rgba", result.stdout)
            self.assertIn("ERROR assets/poses/alpha_windup.png magenta-pixels-100.00-percent", result.stdout)
            self.assertIn("ERROR assets/avatars/not_an_avatar.png filename-avatar", result.stdout)
            self.assertIn("ERROR assets/poses/alpha_release.png required-hero-picture-missing", result.stdout)

    def test_path_mode_only_checks_the_saved_file(self) -> None:
        with self.make_tree() as temp:
            root = Path(temp)
            self.good_files(root)
            (root / "assets/ui/portrait_alpha.png").unlink()
            result = self.run_checker(root, "--path", "assets/avatars/avatar_alpha.png")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.strip(), "SUMMARY checked=1 errors=0")

    def test_manifest_check_detects_changed_picture(self) -> None:
        with self.make_tree() as temp:
            root = Path(temp)
            self.good_files(root)
            self.assertEqual(self.run_checker(root, "--manifest").returncode, 0)
            self.picture(root, "assets/ui/fx_ok.png", size=(257, 256))
            stale = self.run_checker(root, "--manifest", "--check")
            self.assertEqual(stale.returncode, 3, stale.stdout + stale.stderr)
            self.assertIn("ERROR docs/ASSET_MANIFEST.json manifest-stale", stale.stdout)
    def test_manifest_check_detects_added_and_removed_picture(self) -> None:
        for action in ("added", "removed"):
            with self.subTest(action=action), self.make_tree() as temp:
                root = Path(temp)
                self.good_files(root)
                self.assertEqual(self.run_checker(root, "--manifest").returncode, 0)
                if action == "added":
                    self.picture(root, "assets/fx/fx_added.png")
                else:
                    (root / "assets/ui/fx_ok.png").unlink()
                stale = self.run_checker(root, "--manifest", "--check")
                self.assertEqual(stale.returncode, 3, stale.stdout + stale.stderr)
                self.assertIn("ERROR docs/ASSET_MANIFEST.json manifest-stale", stale.stdout)

    def test_backgrounds_and_raw_sources_allow_rgb(self) -> None:
        with self.make_tree() as temp:
            root = Path(temp)
            self.good_files(root)
            self.picture(root, "assets/env/bg_night.png", mode="RGB")
            self.picture(root, "assets/units/unit_alpha_raw.png", mode="RGB")
            result = self.run_checker(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("not-rgba", result.stdout)


if __name__ == "__main__":
    unittest.main()
