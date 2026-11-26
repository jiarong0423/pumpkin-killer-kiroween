#!/usr/bin/env python3
"""Focused deterministic coverage for MCP skills, energy, and ultimates."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from determinism_py import big_hit_pass
import mcp_game_server as engine  # noqa: E402
import mcp_stdio_server as srv  # noqa: E402
import team_tuning_py  # noqa: E402


THROW = {"type": "throw", "angle": 45, "power": 50}


def session(seed=91):
    return srv.Session(seed=seed, turn_seconds=99, human_turn_seconds=99)


def direct_fixture(hero, seed=19):
    game = engine.GameState(mode="human_vs_agent", seed=seed, units=1,
                            hero_red=hero, hero_white="wizard")
    game.central_wall_hp = 0
    game.wind = 0
    game.units["red_1"]["x"] = 500
    game.units["white_1"]["x"] = 1050
    return game


class SkillsTest(unittest.TestCase):
    def test_each_skill_has_one_side_use_and_a_clear_second_use_error(self):
        healed = session()
        # 3 units per side: the bat's max hp is team-scaled (shared/team_tuning.json), so the +52 heal is capped at max - 40
        bat_max = team_tuning_py.team_max_hp(147, 28, 3)
        self.assertEqual(healed.engine.units["red_1"]["max_hp"], bat_max)
        healed.engine.units["red_1"]["hp"] = 40
        result = healed.call("submit_action", {"unit": "red_1",
                              "action": {"type": "skill", "skill": "heal"}})
        self.assertEqual(result["healed"], min(52, bat_max - 40))
        self.assertEqual(healed.engine.units["red_1"]["hp"], min(92, bat_max))
        uncapped = session()
        uncapped.engine.units["red_1"].update({"max_hp": 147, "hp": 40})   # the hero-table value: the full +52 applies
        result = uncapped.call("submit_action", {"unit": "red_1",
                               "action": {"type": "skill", "skill": "heal"}})
        self.assertEqual(result["healed"], 52)
        self.assertEqual(uncapped.engine.units["red_1"]["hp"], 92)
        healed.active_unit_index["red"] = 1
        with self.assertRaisesRegex(srv.ToolError, "already used"):
            healed.call("submit_action", {"unit": "red_2",
                        "action": {"type": "skill", "skill": "heal"}})

        for skill in ("double", "heavy"):
            state = session()
            result = state.call("submit_action", {"unit": "red_1",
                                "action": dict(THROW, type="skill", skill=skill)})
            self.assertEqual(result["remaining"], 0)
            queued = state.engine.units["red_1"]["pending_throw"]
            if skill == "double":
                self.assertAlmostEqual(queued["second_throw"]["power"], 52)
                self.assertEqual(queued["second_throw"]["delay_seconds"], 0.26)
            else:
                self.assertEqual(queued["damage_scale"], 1.5)
            state.active_unit_index["red"] = 1
            with self.assertRaisesRegex(srv.ToolError, "already used"):
                state.call("submit_action", {"unit": "red_2",
                           "action": dict(THROW, type="skill", skill=skill)})

    def test_energy_reaches_three_from_three_direct_hits(self):
        state = session(seed=1)
        state.engine.central_wall_hp = 0
        state.engine.wind = 0
        state.engine.units["red_1"]["x"] = 500
        state.engine.units["white_1"]["x"] = 1050
        for unit in state.engine.units.values():
            if unit["team"] == "red":
                unit["x"] = 500
        for _ in range(3):
            state.engine.wind = 0
            active = state._active_unit("red")
            state.call("submit_action", {"unit": active, "action": THROW})
            state.call("end_turn", {"phase": "human"})
            state.call("end_turn", {"phase": "agent"})
        self.assertEqual(state.energy["red"], 3)
        self.assertEqual(state.call("get_public_state", {})["ultimate_energy"]["red"], 3)


class UltimateTest(unittest.TestCase):
    def test_every_projectile_ultimate_has_its_fixed_seed_damage(self):
        # These probes pin real contact damage, rather than accepting a no-op
        # ultimate that merely returns a non-negative number.
        expected = {
            "skeleton": 36.0, "bat": 43.5, "hag": 27.6,   # 2026-11-18 roles: skeleton 24 x 1.5 = 36 (22 x 1.5 = 33), reaper 22 (41.0 x 22 / 21 = 42.95, seeded contact 42.9), bride 40 (46.8 + 27 became 52 + 30 = 82.0), wizard 36 x 2.6 = 93.6
            "hunchback": 47.5, "reaper": 42.9, "bride": 82.0,
            "wizard": 93.6,   # balance of 2026-11-17: bat 29, bride 36, reaper 21 (evening), wizard 33, hunchback 19; 82.5 before the binary hit masks (the seeded shot used to count on an empty corner of the box and now flies on and hits the head: +3.3 = 10 percent crit of one 33 hit)
        }
        for hero, damage in expected.items():
            with self.subTest(hero=hero):
                game = direct_fixture(hero)
                self.assertTrue(game.submit_throw("red_1", 45, 50, special=hero)["success"])
                result = game.resolve_round()["results"][0]
                self.assertTrue(result["ultimate"])
                self.assertEqual(result["hit_type"], "hero")
                # one throw takes at most half of a full health bar unless it is one of the rare passing throws (owner 2026-11-27)
                if not big_hit_pass(19, 1, game.throw_seq):
                    damage = min(damage, game.units["white_1"]["max_hp"] * engine.BIG_HIT_SHARE)
                self.assertAlmostEqual(result["damage_dealt"], damage)

    def test_necromancer_skips_the_target_without_consuming_its_action(self):
        game = direct_fixture("reaper")
        # Queue the target's throw before the reaper marks it. The complete
        # normal resolution order is red then white; the white action is skipped.
        self.assertTrue(game.submit_throw("white_1", 45, 50)["success"])
        white_actions_before = sum(record["unit_id"] == "white_1" for record in game.history)
        game.submit_throw("red_1", 45, 50, special="reaper")
        result = game.resolve_round()["results"]
        self.assertEqual(engine.resolution_order(game.units, 1), ["red_1", "white_1"])
        self.assertEqual([record["unit_id"] for record in result], ["red_1"])
        white_actions_after = sum(record["unit_id"] == "white_1" for record in game.history)
        self.assertEqual(white_actions_after, white_actions_before)

    def test_knight_points_are_private_to_the_owning_seat(self):
        state = session()
        state.active_unit_index["red"] = 2
        state.energy["red"] = 3
        result = state.call("submit_action", {
            "unit": "red_3", "action": {"type": "ultimate", "points": [
                {"x": 800, "y": 420}, {"x": 700, "y": 430}, {"x": 600, "y": 440}
            ]}
        })
        self.assertFalse(result["turn_cost"])
        red = state.view_for(state.seats["red"])
        white = state.view_for(state.seats["white"])
        self.assertEqual(len(red["knight_walls"]["red"]["points"]), 3)
        self.assertNotIn("points", white["knight_walls"]["red"])
        self.assertEqual(white["knight_walls"]["red"]["points_left"], 3)

    def test_seeded_scripted_match_finishes(self):
        game = engine.GameState(mode="agent_vs_agent", seed=717, units=1,
                                hero_red="wizard", hero_white="wizard")
        game.central_wall_hp = 0
        game.wind = 0
        game.units["red_1"]["x"] = 500
        game.units["white_1"]["x"] = 1050
        winner = None
        for _ in range(20):
            if game.units["red_1"]["alive"]:
                game.submit_throw("red_1", 45, 50)
            if game.units["white_1"]["alive"]:
                game.submit_throw("white_1", 45, 50)
            winner = game.resolve_round()["winner"]
            if winner is not None:
                break
        self.assertIn(winner, ("red", "white", "draw"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
