#!/usr/bin/env python3
"""The page's hit rule and the engine's hit rule must give the same answer for the same shot (red-team R3A-1: the page picked the weapon-less mask after a unit's first
throw, the engine never did, and the test only grepped a string). Behavioural: the page's own `touches` and `projHitRadius` are cut out of index.html and run in Node over a
grid of shots; the engine's GameState.projectile_hits runs over the same grid; every cell must agree, for every hero and every non-wave weapon, on both sides of the field."""
import json, os, subprocess, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import mcp_game_server as srv

HEROES = ["skeleton", "wizard", "knight", "hunchback", "bat", "hag", "bride", "reaper"]
WEAPONS = ["cannonball", "proj_spear", "proj_shuriken", "proj_flame", "proj_cross", "proj_axe", "proj_shield"]
GRID = [(dx, up) for dx in range(-150, 151, 5) for up in range(-45, 261, 5)]

NODE = r"""
const fs = require("fs"), path = require("path");
const root = process.argv[1], input = JSON.parse(fs.readFileSync(0, "utf8"));
const page = fs.readFileSync(path.join(root, "index.html"), "utf8");
const cut = (a, b) => { const i = page.indexOf(a); if (i < 0) throw new Error("missing " + a); const j = page.indexOf(b, i); return page.slice(i, j); };
const radiusSrc = cut("function projHitRadius(p)", "\n");
const touchesSrc = cut("const touches = (opp) => {", "          };");
const HitMask = require(path.join(root, "js", "hit_masks.js"));
const factory = new Function("HitMask", "p", "WAVE_HALF_WIDTH", "hitR", "sideOfUnit", "currentHero", "ai",
  radiusSrc + ";\n" + touchesSrc.replace("const touches = (opp) => {", "return (opp) => {") + "};");
const radiusOf = new Function(radiusSrc + "; return projHitRadius;")();
const out = {};
for (const side of ["left", "right"]) for (const hero of input.heroes) for (const weapon of input.weapons) {
  const [wl, wt] = input.sizes[weapon]; const p = { weapon, wLen: wl, wThick: wt, hitCool: 0, x: 0, y: 0, team: side === "left" ? "ai" : "player" };
  const hitR = radiusOf(p);
  const touches = factory(HitMask, p, 105, hitR, () => side, hero, { profile: hero });
  const unit = { x: 1500, y: 860, hp: 100, profile: hero };
  out[side + "|" + hero + "|" + weapon] = input.grid.map(([dx, up]) => { p.x = unit.x + dx; p.y = unit.y - up; return touches(unit) ? 1 : 0; }).join("");
}
console.log(JSON.stringify(out));
"""

class ParityTests(unittest.TestCase):
    def test_page_projectile_sizes_equal_the_engine_table(self):
        import re
        with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f: src = f.read()
        pairs = [(int(a), int(b)) for a, b in re.findall(r"wLen: (\d+), wThick: (\d+)", src)]
        for weapon, size in srv.PROJECTILE_SIZE.items():
            self.assertIn(tuple(size), pairs, "the page has no projectile of size %s for %s" % (size, weapon))
    def test_page_and_engine_agree_cell_by_cell(self):
        p = subprocess.run(["node", "-e", NODE, ROOT], input=json.dumps({"heroes": HEROES, "weapons": WEAPONS, "grid": GRID, "sizes": srv.PROJECTILE_SIZE}), capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr[:400])
        page = json.loads(p.stdout)
        total = diff = hits = 0
        for key, bits in page.items():
            side, hero, weapon = key.split("|")
            attacker = {"weapon": weapon}
            target = {"hero": hero, "x": 1500.0, "y": 860.0, "facing": 1 if side == "left" else -1,
                      "hit_box": {"halfWidth": 57 if hero == "reaper" else 70, "height": 165 if hero == "reaper" else 190}}
            for (dx, up), bit in zip(GRID, bits):
                eng = 1 if srv.GameState.projectile_hits(attacker, target, 1500.0 + dx, 860.0 - up) else 0
                total += 1; hits += int(bit)
                if eng != int(bit): diff += 1
        self.assertGreater(hits, 1000, "the grid must hit something, or the comparison proves nothing")
        self.assertEqual(diff, 0, "%d of %d cells differ between the page rule and the engine rule" % (diff, total))

if __name__ == "__main__":
    unittest.main()
