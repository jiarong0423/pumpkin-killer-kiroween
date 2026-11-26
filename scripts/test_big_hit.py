#!/usr/bin/env python3
"""Rare big hits (owner 2026-11-27): one throw takes at most half of a full health bar, except one throw in ten. The page (index.html limitHit + js/determinism.js)
and the server (mcp_game_server.py _limit_hit) must give the same numbers. usage: python3 -B scripts/test_big_hit.py"""
import json
import subprocess
import unittest
from pathlib import Path

import mcp_game_server as srv
from determinism_py import BIG_HIT_ONE_IN, big_hit_pass

ROOT = Path(__file__).resolve().parent.parent
CASES = [[seed, rnd, throw, [200.0, 10.0, 80.0, 0.0, 5.5]] for seed in (1, 19, 4294967295) for rnd in (1, 7, 30) for throw in range(1, 41)]
NODE = r"""
const Determinism = require(process.argv[1]), html = require('fs').readFileSync(process.argv[2], 'utf8');
const start = html.indexOf('const BIG_HIT_SHARE'), end = html.indexOf('\n    }\n', start) + 7;
const make = new Function('Determinism', 'matchSeed', 'roundNum', html.slice(start, end) + ' return limitHit;');
const out = JSON.parse(require('fs').readFileSync(0, 'utf8')).map(([seed, round, throwId, hits]) => {
  const limit = make(Determinism, seed, round); return hits.map(raw => limit({ throwId }, { id: 'u', maxHp: 125 }, raw)); });
console.log(JSON.stringify(out));
"""


def server_numbers(seed, rnd, throw, hits):
    game = srv.GameState(mode="human_vs_agent", seed=1, units=1, hero_red="bat", hero_white="wizard")
    game.seed, game.round_num = seed, rnd
    victim = {"id": "u", "max_hp": 125}
    return [game._limit_hit(throw, victim, raw) for raw in hits]


class BigHit(unittest.TestCase):
    def test_page_and_server_agree(self):
        run = subprocess.run(["node", "-e", NODE, str(ROOT / "js" / "determinism.js"), str(ROOT / "index.html")], input=json.dumps(CASES), capture_output=True, text=True, check=True)
        for case, page in zip(CASES, json.loads(run.stdout)):
            server = server_numbers(*case)
            for a, b in zip(page, server):
                self.assertAlmostEqual(a, b, places=6, msg=str(case[:3]))

    def test_a_normal_throw_stops_at_half_and_a_passing_throw_does_not(self):
        seen = set()
        for case in CASES:
            passed = big_hit_pass(case[0], case[1], case[2])
            total = sum(server_numbers(*case))
            self.assertAlmostEqual(total, sum(case[3]) if passed else 62.5, places=6)
            seen.add(passed)
        self.assertEqual(seen, {True, False})

    def test_about_one_throw_in_ten_passes(self):
        n = 100000
        share = sum(big_hit_pass(i * 2654435761 % 4294967296, 1 + i % 30, 1 + i % 97) for i in range(n)) / n
        self.assertAlmostEqual(share, 1 / BIG_HIT_ONE_IN, delta=0.005)


if __name__ == "__main__":
    unittest.main()
