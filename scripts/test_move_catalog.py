#!/usr/bin/env python3
"""scripts/move_catalog.py: the real tree has 0 mismatches, and each static gate fails on a mutant (read() is patched, no file is changed)."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import move_catalog as mc  # noqa: E402

REAL_READ = mc.read


def with_edit(path, old, new):
    def patched(name):
        text = REAL_READ(name)
        if name == path:
            assert old in text, "mutation target missing: %s" % old
            text = text.replace(old, new)
        return text
    return patched


class CatalogTest(unittest.TestCase):
    def tearDown(self):
        mc.read = REAL_READ

    def errors(self):
        return mc.build()[1]

    def test_real_tree_has_no_mismatch(self):
        self.assertEqual(self.errors(), [])

    def test_catalog_has_all_eight_heroes_and_the_room_rule(self):
        table, _ = mc.build()
        self.assertEqual(len(table["heroes"]), 8)
        self.assertEqual(table["page_room_refused"], ["knight", "reaper"])
        self.assertEqual(table["bridge_room_refused"], ["knight", "reaper"])

    def test_m1_spec_page_damage_mismatch_is_caught(self):
        mc.read = with_edit("index.html", "        dmg: 24,\n        tipColor: \"#00cec9\"", "        dmg: 25,\n        tipColor: \"#00cec9\"")
        self.assertTrue(any(e.startswith("M1s skeleton") for e in self.errors()), self.errors())

    def test_m2_missing_throw_sound_is_caught(self):
        mc.read = with_edit("index.html", "proj_axe: \"throw_axe\", ", "")
        self.assertTrue(any(e.startswith("M2s hunchback") for e in self.errors()), self.errors())

    def test_m6_page_and_bridge_disagree_is_caught(self):
        mc.read = with_edit("scripts/mcp_stdio_server.py", 'unit["hero"] in ("knight", "reaper")', 'unit["hero"] in ("knight",)')
        self.assertTrue(any(e.startswith("M6 the page UI refuses") for e in self.errors()), self.errors())

    def test_m6_doc_without_the_refusal_is_caught(self):
        def patched(name):
            text = REAL_READ(name)
            if name == "docs/mcp_agent_protocol.md":
                text = "\n".join(line for line in text.splitlines() if "ultimate" not in line.lower())
            return text
        mc.read = patched
        self.assertTrue(any("protocol doc" in e for e in self.errors()), self.errors())

    def test_m4_unreferenced_audio_event_is_caught(self):
        def patched(name):
            text = REAL_READ(name)
            if name == "js/audio.js":
                text = text.replace('"version": 1,', '"version": 1,', 1)
                text = text.replace('"events": {', '"events": {\n      "zz_never_used_event": {"synth": "x"},', 1)
            return text
        mc.read = patched
        self.assertTrue(any("zz_never_used_event" in e for e in self.errors()), self.errors())


if __name__ == "__main__":
    unittest.main(verbosity=2)
