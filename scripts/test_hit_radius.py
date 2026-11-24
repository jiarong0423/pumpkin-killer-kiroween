#!/usr/bin/env python3
"""The drawn projectile counts in the hit test (owner 2026-11-16: overlap without damage is a bug).

Checks: the engine's PROJECTILE_SIZE equals the page's HERO_PROFILES (wLen, wThick) per weapon, the page and the engine use the same
radius formula, and the data matching script (24,510 simulated throws) reports at most 3.5 percent of overlapping throws without damage
for every weapon and none for the spear and the flame.
"""
import json, os, re, subprocess, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mcp_game_server as srv  # noqa: E402


class HitRadiusTests(unittest.TestCase):
    def test_projectile_sizes_match_the_page(self):
        html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
        found = {}
        for m in re.finditer(r'weapon: "([a-z_]+)",\s*imgKey: "[a-z_]+",\s*wLen: (\d+), wThick: (\d+)', html):
            found[m.group(1)] = (int(m.group(2)), int(m.group(3)))
        self.assertEqual(found, srv.PROJECTILE_SIZE)

    def test_formula_is_the_same_in_page_and_engine(self):
        html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
        self.assertIn('Math.max(0, Math.sqrt((p.wLen || 0) * (p.wThick || 0)) / 2 - 20)', html)
        self.assertEqual(srv.GameState.projectile_radius("proj_soundwave"), 0.0)
        self.assertAlmostEqual(srv.GameState.projectile_radius("proj_axe"), 45.0)
        self.assertEqual(srv.GameState.projectile_radius("cannonball"), 0.0)

    def test_big_picture_over_the_head_now_hits(self):
        attacker = {"weapon": "proj_axe"}
        target = {"x": 1400.0, "y": 860.0, "hit_box": {"halfWidth": 70, "height": 190}}
        self.assertFalse(srv.GameState.projectile_hits({"weapon": "cannonball"}, target, 1400.0, 860.0 - 195.0))
        self.assertTrue(srv.GameState.projectile_hits(attacker, target, 1400.0, 860.0 - 195.0))
        self.assertFalse(srv.GameState.projectile_hits(attacker, target, 1400.0, 860.0 - 240.0))

    def test_overlap_without_damage_stays_rare(self):
        out = subprocess.run(["node", os.path.join(HERE, "hit_match_overlap.js"), os.path.join(os.environ.get("TMPDIR", "/tmp"), "hit_match_check.json")],
                             capture_output=True, text=True, timeout=300, cwd=ROOT)
        self.assertEqual(out.returncode, 0, out.stderr[-300:])
        data = json.load(open(os.path.join(os.environ.get("TMPDIR", "/tmp"), "hit_match_check.json")))
        for weapon, row in data["byWeapon"].items():
            share = row["overlapNoHit"] / max(1, row["overlap"])
            self.assertLessEqual(share, 0.035, "%s: %.1f%% of overlapping throws did no damage" % (weapon, 100 * share))
        for weapon in ("skeleton", "reaper"):
            self.assertEqual(data["byWeapon"][weapon]["overlapNoHit"], 0, weapon)


if __name__ == "__main__":
    unittest.main()
