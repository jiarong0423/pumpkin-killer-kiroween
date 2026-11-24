#!/usr/bin/env python3
"""The binary hit masks: the JS file (page) and the Python module (backend) hold the same data and give the same answer (owner 2026-11-17).
1. js/hit_masks.js embeds exactly shared/hit_masks.json.  2. 6000 seeded random shots (every hero, radius 0..30, both facings) give identical answers in Node and in Python.
3. The rule is the intended one: a shot on the body counts, a shot in an empty corner of the box does not, a mirrored figure mirrors the answer.
4. Negative: a mutant of the JS test (corner constant changed) is caught by check 2."""
import json, os, random, subprocess, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from hit_mask_py import HitMasks

NODE = r"""
const fs = require('fs'); const src = fs.readFileSync(process.argv[1], 'utf8'); const m = { exports: {} };
new Function('module', 'self', src)(m, undefined); const H = m.exports || {};
const shots = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(shots.map(s => H.touches(s[0], s[1], s[2], s[3], s[4], s[5]))));
"""

def shots():
    rnd = random.Random(20261117); heroes = list(HitMasks().runs)
    return [[rnd.choice(heroes), rnd.randint(-120, 120), rnd.randint(-225, 30), rnd.choice([0, 0, 5, 12, 22, 25, 30]), rnd.random() < 0.5, rnd.random() < 0.5] for _ in range(6000)]

def run_js(path, data):
    p = subprocess.run(["node", "-e", NODE, path], input=json.dumps(data), capture_output=True, text=True, timeout=60)
    if p.returncode: raise RuntimeError(p.stderr[:300])
    return json.loads(p.stdout)

class HitMaskTests(unittest.TestCase):
    def test_js_embeds_the_json(self):
        with open(os.path.join(ROOT, "shared", "hit_masks.json")) as f: data = json.load(f)
        with open(os.path.join(ROOT, "js", "hit_masks.js")) as f: js = f.read()
        self.assertIn(json.dumps(data, separators=(",", ":")), js)
    def test_js_and_python_agree(self):
        S = shots(); M = HitMasks(); py = [M.touches(h, dx, dy, r, f, a) for h, dx, dy, r, f, a in S]
        js = run_js(os.path.join(ROOT, "js", "hit_masks.js"), S)
        self.assertEqual(py, js)
        self.assertTrue(any(py) and not all(py))
    def test_masks_follow_the_pictures_the_page_draws(self):
        """Red-team R1 A P1-1 and R2 A P1: the masks are built from the frames the page draws a TARGET in, read from index.html, in two states (armed: the idle frames; unarmed: the weapon-less art after the throw), never the hit frame or a base art that is never drawn. The json must equal what the generator computes now (a stale json fails)."""
        import hit_mask_py as H
        with open(os.path.join(ROOT, "shared", "hit_masks.json")) as f: data = json.load(f)
        images, sets, unarmed, xfix, foot, footfix, faces, held = H._page_tables()
        self.assertEqual(sorted(held), ["unit_bat", "unit_skeleton"], "the page holds layered weapons for the skeleton and the bat")
        sk = data["heroes"]["skeleton"]
        self.assertEqual((sk["frames"], sk["unarmed_frames"]), (["pose_skel_windup"], ["unit_skeleton_unarmed"]), "skeleton: idle is the windup pose, after the throw the weapon-less art")
        self.assertIn("rows_unarmed", sk)
        self.assertEqual(data["heroes"]["bat"]["frames"], ["unit_bat_unarmed"], "bat: the base art is never drawn (layered hands)")
        self.assertNotIn("rows_unarmed", data["heroes"]["wizard"], "a hero without weapon-less art has one state")
        self.assertAlmostEqual(footfix["unit_reaper"], 66 / 1024); self.assertIn("unit_reaper", data["heroes"]["reaper"]["frames"])
        for hero, v in data["heroes"].items():
            fr = H.frames_of(hero)
            self.assertFalse([n for n in v["frames"] + v["unarmed_frames"] if n.endswith("_hit")], hero + ": no hit frame in a mask")
            self.assertEqual((v["frames"], v["unarmed_frames"]), ([f[3] for f in fr["armed"]], [f[3] for f in fr["unarmed"]]), hero + ": the json is as fresh as index.html")
            self.assertEqual(v["faces"], "right" if faces.get("unit_" + hero) else "left", hero + ": facing equals ART_FACES_RIGHT of the page")
        self.assertEqual(sorted(data["heroes"]), sorted(h for h in H.HEROES))
    def test_armed_state_changes_the_answer_and_js_agrees(self):
        """A shot that only the weapon pose can touch hits an armed skeleton and misses an unarmed one, in Python and in the page's JS."""
        M = HitMasks(); found = None
        for dx in range(-110, 111, 2):
            for dy in range(-200, 30, 2):
                if M.touches("skeleton", dx, dy, 0, False, True) != M.touches("skeleton", dx, dy, 0, False, False): found = (dx, dy); break
            if found: break
        self.assertIsNotNone(found, "the skeleton has pixels in one state only")
        S = [["skeleton", found[0], found[1], 0, False, a] for a in (True, False)]
        js = run_js(os.path.join(ROOT, "js", "hit_masks.js"), S)
        self.assertEqual(js, [M.touches("skeleton", found[0], found[1], 0, False, a) for a in (True, False)])
        self.assertNotEqual(js[0], js[1])
    def test_page_engine_and_reference_sim_use_the_armed_mask_only(self):
        """Red-team R3A-1: a target is shot at on the other team's turn, when it is drawn armed again (the page re-arms 0.55 s after a throw), so every rule uses the ARMED mask.
        The weapon-less rows stay in the data only for the fidelity audit. The behavioural proof that page and engine agree is scripts/test_hit_rule_parity.py."""
        with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f: src = f.read()
        line = [l for l in src.split("\n") if "HitMask.touches(" in l]
        self.assertEqual(len(line), 1)
        self.assertNotIn("thrown", line[0]); self.assertNotIn("opp.armed", line[0]); self.assertIn('=== "left", true))', line[0])
        self.assertNotIn("u.thrown", src)
        with open(os.path.join(ROOT, "scripts", "mcp_game_server.py"), encoding="utf-8") as f: eng = f.read()
        self.assertNotIn("last_throw\") is None", eng)
        with open(os.path.join(ROOT, "scripts", "sim_team_headless.py"), encoding="utf-8") as f: sim = f.read()
        self.assertNotIn("last_throw", sim.split("def touches")[1] if "def touches" in sim else "")
    def test_rule_is_the_intended_one(self):
        M = HitMasks()
        self.assertTrue(M.touches("skeleton", 0, -90, 0, False), "the middle of the body is hit")
        self.assertFalse(M.touches("skeleton", 66, -185, 0, False), "an empty corner of the 70 x 190 box is not")
        for h in ("wizard", "hag", "bride"):
            a, b = M.touches(h, 40, -100, 5, False), M.touches(h, -40, -100, 5, True)
            self.assertEqual(a, b, h + ": a mirrored figure mirrors the answer")
        self.assertTrue(M.has("hunchback"))
    def test_negative_mutant_is_caught(self):
        with open(os.path.join(ROOT, "js", "hit_masks.js")) as f: js = f.read()
        self.assertEqual(js.count("(r + 0.7072) * (r + 0.7072)"), 1)
        tmp = os.path.join(os.environ.get("TMPDIR", "/tmp"), "hit_masks_mutant.js")
        with open(tmp, "w") as f: f.write(js.replace("(r + 0.7072) * (r + 0.7072)", "(r + 0.0) * (r + 0.0)"))
        S = shots(); M = HitMasks(); py = [M.touches(h, dx, dy, r, f, a) for h, dx, dy, r, f, a in S]
        self.assertNotEqual(py, run_js(tmp, S))

if __name__ == "__main__":
    unittest.main(verbosity=1)
