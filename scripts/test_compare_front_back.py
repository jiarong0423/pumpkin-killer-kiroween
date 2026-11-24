#!/usr/bin/env python3
"""Socket-free tests of scripts/compare_front_back.py and the pure parts of scripts/engine_matrix.py with small fake files."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import compare_front_back as cmp  # noqa: E402
import engine_matrix as em  # noqa: E402


def match(end, hero, size, seed, rounds, winner, throws=20, hits=12, near=None, pity=None, comeback=None, errors=None,
          tier_left="hard", tier_right="easy", hero_right="bat"):
    return {"end": end, "hero": hero, "hero_right": hero_right, "size": size, "seed": seed, "tier_left": tier_left,
            "tier_right": tier_right, "winner": winner, "rounds": rounds, "hp_share_left": 0.5, "hp_share_right": 0.0,
            "units_left_alive": 1, "units_right_alive": 0, "throws": throws, "direct_hits": hits, "near_misses": near,
            "pity_triggers": pity, "comeback_hits": comeback, "ultimates_left": 0, "ultimates_right": 0, "errors": errors or []}


def write(directory, name, end, matches):
    with open(os.path.join(directory, name), "w", encoding="utf-8") as handle:
        json.dump({"end": end, "started": "2026-11-17T00:00:00+00:00", "matches": matches}, handle)


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.out = os.path.join(self.dir, "report.md")
        engine = []
        page = []
        for k in range(10):
            seed = 7000 + k
            engine.append(match("engine", "skeleton", 1, seed, 10, "left" if k < 5 else "right", near=0, pity=0, comeback=0))
            # page: much longer (x1.5), left always wins, fewer hits, null counters
            page.append(match("page", "skeleton", 1, seed, 15, "left", hits=6, near=None, pity=None, comeback=None))
        for k in range(10):
            seed = 7010 + k
            engine.append(match("engine", "wizard", 2, seed, 12, "left", near=5, pity=4, comeback=3))
            page.append(match("page", "wizard", 2, seed, 12, "left", near=5, pity=4, comeback=3))
        page[3]["errors"] = ["TypeError: undefined is not a function"]
        page[4]["tier_left"] = "easy"            # a seed whose hidden tier differs from the engine record
        write(self.dir, "matrix_engine.json", "engine", engine)
        write(self.dir, "matrix_page_vm.json", "page", page)
        with open(os.path.join(self.dir, "matrix_page_phone.json"), "w") as handle:
            handle.write("{not json")

    def tearDown(self):
        shutil.rmtree(self.dir)

    def report(self):
        text, status = cmp.compare(self.dir, self.out)
        self.assertEqual(status, 0)
        self.assertEqual(open(self.out, encoding="utf-8").read(), text)
        return text

    def test_flags_errors_files_and_hypotheses(self):
        text = self.report()
        self.assertIn("| page vm | matrix_page_vm.json | 20 | ok |", text)
        self.assertIn("| page desktop | matrix_page_desktop.json | 0 | missing |", text)
        self.assertRegex(text, r"page phone \| matrix_page_phone.json \| 0 \| unreadable")
        cell = next(line for line in text.splitlines() if line.startswith("| skeleton | 1v1 |"))
        self.assertIn("R +50%", cell)          # 15 against 10 rounds
        self.assertIn("W +50 pt", cell)        # page left wins 100 percent, engine 50
        self.assertNotIn("R", next(line for line in text.splitlines() if line.startswith("| wizard | 2v2 |")).split("|")[5])
        self.assertIn("Flagged cells: 1 of 2.", text)
        self.assertIn("| page vm | 7003 | skeleton | 1v1 | TypeError: undefined is not a function |", text)
        self.assertIn("1 disagreements", text)
        self.assertIn("first: seed 7004 field tier_left engine=hard page=easy", text)
        hypotheses = text.split("## What differs and probable cause")[1]
        self.assertIn("[hypothesis]", hypotheses)
        self.assertIn("1v1: mean rounds 15.0 against 10.0", hypotheses)
        self.assertIn("hits per throw 0.30 against 0.60", hypotheses)
        self.assertIn("left side wins 100% against 50%", hypotheses)

    def test_a_null_counter_is_reported_not_compared(self):
        text = self.report()
        row = next(line for line in text.splitlines() if line.startswith("| 1v1 | page vm |"))
        self.assertIn("n/a", row)

    def test_missing_page_files_still_give_an_engine_only_report(self):
        for name in ("matrix_page_vm.json", "matrix_page_phone.json"):
            os.remove(os.path.join(self.dir, name))
        text = self.report()
        self.assertIn("No page file exists yet", text)
        self.assertIn("1v1 rounds 10.0, left win 50%", text)

    def test_a_missing_engine_file_is_an_error(self):
        os.remove(os.path.join(self.dir, "matrix_engine.json"))
        text, status = cmp.compare(self.dir, self.out)
        self.assertEqual(status, 2)
        self.assertFalse(os.path.exists(self.out))

    def test_command_line_exit_codes(self):
        done = subprocess.run([sys.executable, "-B", os.path.join(HERE, "compare_front_back.py"), "--logs", self.dir,
                               "--out", self.out], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("page files read: vm, phone", done.stdout)
        empty = tempfile.mkdtemp()
        try:
            done = subprocess.run([sys.executable, "-B", os.path.join(HERE, "compare_front_back.py"), "--logs", empty,
                                   "--out", self.out], capture_output=True, text=True)
            self.assertEqual(done.returncode, 2)
        finally:
            shutil.rmtree(empty)

    def test_within_limits_is_not_flagged(self):
        e = cmp.summarize([match("engine", "bat", 1, 1, 10, "left")])
        self.assertEqual(cmp.differs(e, cmp.summarize([match("page", "bat", 1, 1, 12, "left")])), {})           # +20 percent
        self.assertIn("rounds", cmp.differs(e, cmp.summarize([match("page", "bat", 1, 1, 13, "left")])))        # +30 percent


class EngineMatrixPureTests(unittest.TestCase):
    def test_seeds_right_hero_and_tiers_follow_the_spec(self):
        self.assertEqual(em.cell_seed(0, 1, 0), 7010)
        self.assertEqual(em.cell_seed(7, 3, 9), 7739)
        self.assertEqual(em.right_hero(7000), em.HEROES[(7000 * 7 + 3) % 8])
        self.assertEqual(em.draw_tiers(7000), em.draw_tiers(7000))
        self.assertTrue(all(t in em.TIERS for s in range(7010, 7040) for t in em.draw_tiers(s)))

    @unittest.skipUnless(shutil.which("node"), "node is needed to cross-check mulberry32")
    def test_mulberry32_equals_the_js_generator(self):
        seeds = [7000, 7013, 7222, 7731, 0x5eed, 123456789]
        js = ("function m(seed){var a=seed|0;return function(){a=(a+0x6d2b79f5)|0;var t=Math.imul(a^(a>>>15),1|a);"
              "t=(t+Math.imul(t^(t>>>7),61|t))^t;return((t^(t>>>14))>>>0)/4294967296;};}"
              "console.log(JSON.stringify(%s.map(s=>{const r=m(s^0x5eed);return [r(),r()];})));" % json.dumps(seeds))
        want = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
        for seed, (first, second) in zip(seeds, want):
            rand = em.mulberry32(seed ^ 0x5eed)
            self.assertEqual((rand(), rand()), (first, second))

    def test_a_small_matrix_runs_and_keeps_the_record_keys(self):
        matches = em.run_matrix(["bat"], [1, 2], 1)
        keys = {"end", "hero", "hero_right", "size", "seed", "tier_left", "tier_right", "winner", "rounds", "hp_share_left",
                "hp_share_right", "units_left_alive", "units_right_alive", "throws", "direct_hits", "near_misses",
                "pity_triggers", "comeback_hits", "ultimates_left", "ultimates_right", "errors", "heroes_left", "heroes_right"}
        for record in matches:
            self.assertEqual(set(record), keys)
            self.assertEqual(record["end"], "engine")
            self.assertEqual(record["errors"], [])
            self.assertIn(record["winner"], ("left", "right", "cap_left", "cap_right", "none"))
            self.assertGreater(record["throws"], 0)
        self.assertEqual([m["seed"] for m in matches], [7000 + 100 * 2 + 10 * 1, 7000 + 100 * 2 + 10 * 2])
        self.assertEqual(matches[0]["near_misses"], 0)     # a duel has no comeback pack


if __name__ == "__main__":
    unittest.main(verbosity=2)
