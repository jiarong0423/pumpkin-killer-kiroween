#!/usr/bin/env python3
"""Engine parity coverage for the owner-fixed Shield Wall rule."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import mcp_game_server as engine  # noqa: E402


class ShieldWallTest(unittest.TestCase):
    def game(self, hero="skeleton"):
        game = engine.GameState(mode="human_vs_agent", seed=19, units=1,
                                hero_red=hero, hero_white="knight")
        game.central_wall_hp = 0
        game.wind = 0
        game.units["red_1"]["x"] = 500
        game.units["white_1"]["x"] = 1500
        return game

    def throw(self, game, hero=None):
        unit = game.units["red_1"]
        return game._resolve_throw(unit, {"angle": 45, "power": 50,
                                          "special": hero, "damage_scale": 1.0})

    def test_expiry_after_three_enemy_throws(self):
        game = self.game()
        game.set_knight_wall("white", [{"x": 700, "y": 100}] * 3)
        for _ in range(3):
            self.throw(game)
        self.assertEqual(game.knight_walls["white"], [])
        self.assertEqual(game.knight_wall_attacks["white"], 0)

    def test_high_shot_passes_over_the_coffin(self):
        game = self.game()
        # First integration point is inside the x range but 100 px above y=738.5.
        game.set_knight_wall("white", [{"x": 570, "y": 638.5}])
        result = self.throw(game)
        self.assertNotEqual(result["hit_type"], "ultimate_blocked")
        self.assertEqual(len(game.knight_walls["white"]), 1)

    def test_hunchback_bypasses_before_the_shield_wall_check(self):
        game = self.game("hunchback")
        game.set_knight_wall("white", [{"x": 570, "y": 738.5}])
        result = self.throw(game, "hunchback")
        self.assertNotEqual(result["hit_type"], "ultimate_blocked")
        self.assertEqual(len(game.knight_walls["white"]), 1)
        self.assertEqual(game.knight_wall_attacks["white"], 1)

    def test_two_enemy_throws_in_one_round_count_once_per_throw(self):
        game = self.game()
        game.set_knight_wall("white", [{"x": 700, "y": 100}] * 3)
        self.throw(game)
        self.throw(game)
        self.assertEqual(game.knight_wall_attacks["white"], 2)
        self.assertEqual(len(game.knight_walls["white"]), 3)

    def test_crossing_the_coffin_range_blocks_and_consumes_one_point(self):
        game = self.game()
        game.set_knight_wall("white", [{"x": 570, "y": 738.5}])
        result = self.throw(game)
        self.assertEqual(result["hit_type"], "ultimate_blocked")
        self.assertEqual(result["damage_dealt"], 0)
        self.assertEqual(game.knight_walls["white"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
