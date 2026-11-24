#!/usr/bin/env python3
"""Offline synthetic checks for score_ghost_tests.py; no Pillow, numpy, or model files."""
import os
import struct
import tempfile
import unittest
import zlib

import score_ghost_tests as scorer


def write_rgb_png(path, rows):
    height, width = len(rows), len(rows[0])
    payload = b"".join(b"\0" + bytes(channel for pixel in row for channel in pixel) for row in rows)
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    content = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    with open(path, "wb") as handle:
        handle.write(content + chunk(b"IDAT", zlib.compress(payload)) + chunk(b"IEND", b""))


def ghost(noisy=False, taller=False):
    background = scorer.MAGENTA
    rows = [[background for _ in range(64)] for _ in range(64)]
    if noisy:
        for y in range(64):
            for x in range(64):
                rows[y][x] = (210 + ((x + y) % 42), (x * 3 + y) % 46, 205 + ((x * 5 + y) % 42))
    height = 44 if taller else 28
    for y in range(18, 18 + height):
        for x in range(20, 44):
            rows[y][x] = (185, 255, 245)
    # Near-black features make the foreground palette and key unambiguous.
    rows[27][36] = (20, 25, 35)
    rows[28][36] = (20, 25, 35)
    return rows


class GhostScorerTests(unittest.TestCase):
    def test_identical_clean_ghost_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            ref = os.path.join(directory, "ref.png")
            candidate = os.path.join(directory, "candidate.png")
            write_rgb_png(ref, ghost())
            write_rgb_png(candidate, ghost())
            result = scorer.score_image(scorer.read_png(ref), scorer.read_png(candidate))
        self.assertTrue(result["pass"], result)
        self.assertEqual(result["halo_width"], 0.0)
        self.assertEqual(result["scale_ratio"], 1.0)

    def test_noisy_matte_fails_keyability_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            ref = os.path.join(directory, "ref.png")
            candidate = os.path.join(directory, "noisy.png")
            write_rgb_png(ref, ghost())
            write_rgb_png(candidate, ghost(noisy=True))
            result = scorer.score_image(scorer.read_png(ref), scorer.read_png(candidate))
        self.assertFalse(result["pass"])
        self.assertIn("background-noise", result["failures"])

    def test_scale_drift_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            ref = os.path.join(directory, "ref.png")
            candidate = os.path.join(directory, "tall.png")
            write_rgb_png(ref, ghost())
            write_rgb_png(candidate, ghost(taller=True))
            result = scorer.score_image(scorer.read_png(ref), scorer.read_png(candidate))
        self.assertFalse(result["pass"])
        self.assertIn("scale", result["failures"])


if __name__ == "__main__":
    unittest.main()
