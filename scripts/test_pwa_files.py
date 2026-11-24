#!/usr/bin/env python3
"""Filesystem checks for the static PWA support files."""
import json
import re
import struct
import subprocess
import sys
import unittest
from pathlib import Path

from make_sw_precache import BEGIN, END, ROOT, cache_name, wanted_files

MANIFEST = ROOT / "manifest.webmanifest"
WORKER = ROOT / "sw.js"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
CACHE_NAME_PATTERN = re.compile(r'^const CACHE_NAME = "([^"]+)";$', re.MULTILINE)
EXPECTED_FONTS = {
    "assets/fonts/pk-body-400.woff2",
    "assets/fonts/pk-body-700.woff2",
    "assets/fonts/pk-display-cjk-900.woff2",
}


def png_size(path):
    with path.open("rb") as file:
        header = file.read(24)
    if header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise AssertionError("%s is not a PNG with an IHDR header" % path)
    return struct.unpack(">II", header[16:24])


def worker_precache_paths(source):
    start = source.index(BEGIN) + len(BEGIN)
    end = source.index(END, start)
    lines = source[start:end].splitlines()
    return [line.strip().strip(",").strip('"') for line in lines if line.strip()]


class PwaFilesTest(unittest.TestCase):
    def test_manifest_and_icons(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for key in ("name", "short_name", "lang", "start_url", "scope", "display", "orientation", "background_color", "theme_color", "icons"):
            self.assertIn(key, manifest)
        self.assertEqual(manifest["lang"], "en")
        self.assertEqual(manifest["display"], "fullscreen")
        self.assertEqual(manifest.get("display_override"), ["fullscreen", "standalone"])
        self.assertEqual(manifest["orientation"], "landscape")
        expected = {
            "icons/icon-192.png": (192, 192, None),
            "icons/icon-512.png": (512, 512, None),
            "icons/icon-maskable-512.png": (512, 512, "maskable"),
        }
        self.assertEqual(len(manifest["icons"]), len(expected))
        for icon in manifest["icons"]:
            source = icon["src"]
            self.assertIn(source, expected)
            width, height, purpose = expected[source]
            self.assertEqual(icon["sizes"], "%dx%d" % (width, height))
            self.assertEqual(icon.get("purpose"), purpose)
            self.assertEqual(png_size(ROOT / source), (width, height))

    def test_precache_matches_generator_and_files_exist(self):
        result = subprocess.run(
            [sys.executable, "-B", str(ROOT / "scripts" / "make_sw_precache.py"), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        source = WORKER.read_text(encoding="utf-8")
        actual = worker_precache_paths(source)
        self.assertEqual(actual, wanted_files())
        self.assertTrue(EXPECTED_FONTS.issubset(actual))
        match = CACHE_NAME_PATTERN.search(source)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), cache_name(actual))
        for path in actual:
            self.assertTrue((ROOT / path).is_file(), path)

    def test_worker_precaches_network_first_relay_config_only(self):
        source = WORKER.read_text(encoding="utf-8")
        self.assertIn('"relay-config.js"', source)
        self.assertIn('url.pathname === "/relay-config.js"', source)
        self.assertNotIn('ws:', source)


if __name__ == "__main__":
    unittest.main()
