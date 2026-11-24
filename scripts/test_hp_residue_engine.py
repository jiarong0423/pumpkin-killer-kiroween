#!/usr/bin/env python3
"""Ledger N7, engine side: a hit that should kill a unit must leave it dead (hp exactly 0, alive False), never alive with a floating-point residue such as 3.6e-15 (twin of the page's hpAfter, matrix scripts/test_dead_unit_hits.js RESIDUE_KILL)."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mcp_stdio_server as srv
class HpResidue(unittest.TestCase):
    def test_exact_kill_with_a_binary_residue_leaves_the_unit_dead(self):
        for units, hero in ((1, "skeleton"), (3, "wizard")):
            g = srv.TrackedGameState(mode="agent_vs_agent", seed=7, units=units, hero_red=[hero] * units, hero_white=["skeleton"] * units)
            att = g.units["red_1"]; vic = g.units["white_1"]; vic["hp"] = 24.000000000000004
            dealt = g._apply_hit(att, vic, 1100.0, 700.0, False, 1.0, True, False)["damage"]
            vic["hp"] = dealt + 3.6e-15; vic["alive"] = True
            g._apply_hit(att, vic, 1100.0, 700.0, False, 1.0, True, False)
            self.assertEqual(vic["hp"], 0.0); self.assertFalse(vic["alive"])
if __name__ == "__main__": unittest.main()
