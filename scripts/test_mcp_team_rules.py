#!/usr/bin/env python3
"""Team-match rules of the Python engine (2026-11-17): hp scale, late ramp, round cap, and parity with the page
(wizard blast 234 px flat, bride wave 105 px stepped, swarm, 120 px teammate gap after moves and knockback)."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import mcp_game_server as engine  # noqa: E402
import mcp_stdio_server as srv  # noqa: E402
import team_tuning_py as tuning  # noqa: E402


def game(red, white, seed=7, red_x=(500.0, 700.0, 900.0), white_x=(1300.0, 1500.0, 1700.0), wall=False):
    units = len(red)
    g = srv.TrackedGameState(mode="agent_vs_agent", seed=seed, units=units, hero_red=red, hero_white=white)
    g.wind = 0
    if not wall:
        g.central_wall_hp = 0
    for index in range(units):
        g.units["red_%d" % (index + 1)]["x"] = float(red_x[index])
        g.units["white_%d" % (index + 1)]["x"] = float(white_x[index])
    for unit in g.units.values():
        unit["hp"] = unit["max_hp"] = 500.0   # the rules below are measured in damage, not in kills (hp scale has its own test)
    return g


def shoot(g, unit, angle, power, special=None):
    g.wind = 0
    assert g.submit_throw(unit, angle, power, special=special)["success"]
    return g.resolve_round()["results"][0]


def hp_drop(g, before):
    return {uid: round(before[uid] - u["hp"], 1) for uid, u in g.units.items() if before[uid] != u["hp"]}


class HpScale(unittest.TestCase):
    def test_team_units_use_the_scaled_hp_and_one_unit_keeps_the_table(self):
        for n in (2, 3):
            heroes = ["skeleton", "wizard", "bat"][:n]
            g = srv.TrackedGameState(seed=3, units=n, hero_red=heroes, hero_white=heroes)
            for unit in g.units.values():
                want = tuning.team_max_hp(engine.HERO_TEMPLATES[unit["hero"]]["hp"],
                                          engine.HERO_TEMPLATES[unit["hero"]]["dmg"], n)
                self.assertEqual(unit["max_hp"], want)
                self.assertEqual(unit["hp"], float(want))
            self.assertEqual([g.units["red_1"]["max_hp"], g.units["red_2"]["max_hp"]][:2],
                             [tuning.team_max_hp(150, 22, n), tuning.team_max_hp(124, 33, n)])
        one = srv.TrackedGameState(seed=3, units=1, hero_red="skeleton", hero_white="wizard")
        self.assertEqual((one.units["red_1"]["max_hp"], one.units["red_1"]["hp"]), (150, 150.0))
        self.assertEqual((one.units["white_1"]["max_hp"], one.units["white_1"]["hp"]), (124, 124.0))
        self.assertEqual(tuning.ramp_multiplier(40, 1), 1.0)
        self.assertEqual(tuning.round_cap(1), 40)   # the duel limit (owner 2026-11-17)


class Ramp(unittest.TestCase):
    def hit(self, n, round_number):
        heroes = ["skeleton", "wizard", "bat"][:n]
        g = srv.TrackedGameState(seed=3, units=n, hero_red=heroes, hero_white=heroes)
        g.round_num = round_number
        attacker, target = g.units["red_1"], g.units["white_1"]
        target["hp"] = target["max_hp"] = 500.0
        return g._apply_hit(attacker, target, target["x"], target["y"] - 100, False, 1.0, True)["damage"]

    def test_ramp_starts_at_the_tuned_round_and_only_in_team_matches(self):
        start, per = tuning.RAMP_START, tuning.RAMP_PER_ROUND     # values come from shared/team_tuning.json
        def ramped(round_number):                                 # independent formula: 24 x (1 + per x (round - start + 1)) (24 = skeleton since the 2026-11-18 balanced role, 22 before)
            return round(24 * (1 + per * (round_number - start + 1)) * 10 + 1e-9) / 10
        self.assertEqual(self.hit(2, start - 1), 24.0)
        self.assertEqual(self.hit(2, start), ramped(start))
        self.assertGreater(self.hit(2, start), 24.0)
        self.assertEqual(self.hit(3, start + 3), ramped(start + 3))
        self.assertEqual(self.hit(1, start + 3), 24.0)            # one unit per team: neutral
        self.assertEqual(self.hit(1, 40), 24.0)


class RoundCap(unittest.TestCase):
    def play_idle(self, g, rounds):
        last = None
        for _ in range(rounds):
            last = g.resolve_round()
            if last["winner"] is not None:
                break
        return last

    def test_cap_ends_a_team_match_after_the_cap_round_and_names_the_reason(self):
        for n in (2, 3):
            cap = tuning.round_cap(n)                       # from shared/team_tuning.json
            g = srv.TrackedGameState(seed=5, units=n, hero_red=["knight"] * n, hero_white=["knight"] * n)
            g.units["white_1"]["hp"] -= 10
            early = self.play_idle(g, cap - 1)
            self.assertIsNone(early["winner"])
            self.assertEqual(g.round_num, cap)
            result = g.resolve_round()                      # round `cap` resolved: the counter is now cap + 1
            self.assertEqual(g.round_num, cap + 1)
            self.assertEqual((result["winner"], result["winner_reason"]), ("red", "round_cap"))

    def test_cap_winner_follows_the_hp_share_then_living_units_then_right_side(self):
        def run(red_hp, white_hp, white_alive=True):
            g = srv.TrackedGameState(seed=5, units=2, hero_red=["knight"] * 2, hero_white=["knight"] * 2)
            for uid, hp in zip(("red_1", "red_2"), red_hp):
                g.units[uid]["hp"] = hp
            for uid, hp in zip(("white_1", "white_2"), white_hp):
                g.units[uid]["hp"] = hp
            g.round_num = tuning.round_cap(2)
            return g.resolve_round()
        m = srv.TrackedGameState(seed=5, units=2, hero_red=["knight"] * 2, hero_white=["knight"] * 2).units["red_1"]["max_hp"]
        self.assertEqual(run((0.5 * m, 0.5 * m), (0.6 * m, 0.6 * m))["winner"], "white")
        self.assertEqual(run((0.6 * m, 0.6 * m), (0.5 * m, 0.5 * m))["winner"], "red")
        self.assertEqual(run((m, m), (m, m))["winner"], "white")                    # fully equal: the right side
        self.assertEqual(run((m, 0), (0.5 * m, 0.5 * m))["winner"], "white")        # equal share, more living units
        self.assertEqual(run((0.5 * m, 0.5 * m), (m, 0))["winner"], "red")

    def test_a_real_kill_wins_before_the_cap_and_has_no_reason(self):
        g = srv.TrackedGameState(seed=5, units=2, hero_red=["knight"] * 2, hero_white=["knight"] * 2)
        for uid in ("white_1", "white_2"):
            g.units[uid].update({"alive": False, "hp": 0.0})
        g.round_num = tuning.round_cap(2)
        result = g.resolve_round()
        self.assertEqual(result["winner"], "red")
        self.assertNotIn("winner_reason", result)

    def test_one_unit_per_team_has_the_duel_cap(self):   # owner 2026-11-17: a duel ends at round 40 by hp share
        g = srv.TrackedGameState(seed=5, units=1, hero_red="knight", hero_white="knight")
        result = self.play_idle(g, 39)
        self.assertIsNone(result["winner"])
        self.assertNotIn("winner_reason", result)
        result = self.play_idle(g, 5)
        self.assertIsNotNone(result["winner"])
        self.assertEqual(result["winner_reason"], "round_cap")

    def test_session_exposes_the_reason_only_for_a_cap(self):
        s = srv.Session(seed=5, units=2, clock=lambda: 0.0, turn_seconds=99, human_turn_seconds=99,
                        hero_red=["knight"] * 2, hero_white=["knight"] * 2)
        self.assertNotIn("winner_reason", s.public_state())
        s.engine.units["white_1"]["hp"] -= 10
        s.engine.round_num = tuning.round_cap(2)
        s.call("end_turn", {"phase": "human"})
        summary = s.call("end_turn", {"phase": "agent"})
        self.assertEqual((s.winner, s.winner_reason, summary["winner_reason"]), ("red", "round_cap", "round_cap"))
        self.assertEqual(s.public_state()["winner_reason"], "round_cap")
        self.assertEqual(s.phase, "over")
        one = srv.Session(seed=5, units=1, clock=lambda: 0.0, turn_seconds=99, human_turn_seconds=99,
                          hero_red="knight", hero_white="knight")
        self.assertNotIn("winner_reason", one.public_state())


def wave_centre(heroes_white, special=None, power=54):
    """x where the bride's wave first touches. The touch happens where the wave drops into the 40 px band above the
    ground; an enemy placed on that x is touched at that very step, so iterate to the fixed point."""
    x = 1250.0
    for _ in range(6):
        probe = game(["bride", "knight"], heroes_white, white_x=(x, x + 400.0))
        record = shoot(probe, "red_1", 45, power, special)
        assert record["hit_type"] == "hero", record
        if record["landing_x"] == x:
            return x
        x = record["landing_x"]
    raise AssertionError("wave centre did not settle")


class BrideWave(unittest.TestCase):
    WHITE = ["skeleton", "knight"]

    def test_steps_and_splash_follow_the_page(self):
        xc = wave_centre(self.WHITE)
        # touched unit 30 px from the centre: 100 percent (34); the other unit 90 px away: 50 percent (17).
        # Both survive and are poisoned, so each loses 2 more at the white turn start of the same round.
        g = game(["bride", "knight"], self.WHITE, white_x=(xc + 30.0, xc - 90.0))
        before = {uid: u["hp"] for uid, u in g.units.items()}
        record = shoot(g, "red_1", 45, 54)
        self.assertEqual(record["landing_x"], xc)
        self.assertEqual(hp_drop(g, before), {"white_1": 42.0, "white_2": 22.0})   # bride dmg 40 (36 before the 2026-11-18 role +10 percent): 40 + 2 poison, 20 + 2
        self.assertEqual(record["hit_target"], "white_1")
        self.assertEqual(g.units["white_2"]["statuses"].get("poison"), 1)
        # 60 px: 75 percent; 120 px away: outside the wave
        g = game(["bride", "knight"], self.WHITE, white_x=(xc + 60.0, xc - 120.0))
        before = {uid: u["hp"] for uid, u in g.units.items()}
        shoot(g, "red_1", 45, 54)
        self.assertEqual(hp_drop(g, before), {"white_1": 32.0})

    def test_the_wave_falloff_is_counted_in_cells_of_35_px(self):
        """Owner 2026-11-18: falloff by grid cell: 100 / 75 / 50 percent to 35 / 70 / 105 px (they were the invented 40 / 75 / 105)."""
        xc = wave_centre(self.WHITE)
        def other_unit(offset):
            g = game(["bride", "knight"], self.WHITE, white_x=(xc + 20.0, xc + offset))
            before = {uid: u["hp"] for uid, u in g.units.items()}
            record = shoot(g, "red_1", 45, 54)
            self.assertEqual(record["hit_target"], "white_1")
            return hp_drop(g, before).get("white_2")
        # the exact wave centre is a few hundredths of a px beyond the rounded landing_x: the probes stay a px or more away from the cell edges
        for offset, want in ((30.0, 42.0), (34.0, 42.0), (37.0, 32.0), (69.0, 32.0), (72.0, 22.0), (104.0, 22.0), (-30.0, 42.0), (-72.0, 22.0)):
            with self.subTest(offset=offset):
                self.assertEqual(other_unit(offset), want)   # 40 x (1 | 0.75 | 0.5) plus the 2 poison tick of the white turn start
        self.assertIsNone(other_unit(107.0))
        self.assertIsNone(other_unit(-107.0))

    def test_one_wave_uses_the_comeback_numbers_of_its_first_hit_for_every_victim(self):
        """Red-team R11B-2: the page fixes the shares and the pity charge at the projectile's first damage; the engine recomputed them at every hit,
        so the second victim of one wave took less than the first although both stood in the same cell. Here both victims stand 30 px from the centre."""
        xc = wave_centre(self.WHITE)
        g = game(["bride", "knight"], self.WHITE, white_x=(xc + 30.0, xc - 30.0))
        for uid in ("red_1", "red_2"):
            g.units[uid]["hp"] = 100.0   # the thrower's team is far behind (max hp 500): a big underdog bonus
        before = {uid: u["hp"] for uid, u in g.units.items()}
        shoot(g, "red_1", 45, 54)
        drop = hp_drop(g, before)
        self.assertEqual(drop["white_1"], drop["white_2"], drop)   # equal cells, equal damage (the first hit lowers the white share; a recompute would give the second victim less)
        self.assertGreater(drop["white_1"], 42.0, drop)            # and the underdog bonus is really in it

    def test_nearest_to_the_wave_centre_is_the_touched_unit_and_dead_units_are_skipped(self):
        xc = wave_centre(self.WHITE)
        g = game(["bride", "knight"], self.WHITE, white_x=(xc + 90.0, xc - 20.0))
        before = {uid: u["hp"] for uid, u in g.units.items()}
        record = shoot(g, "red_1", 45, 54)
        self.assertEqual(record["hit_target"], "white_2")
        self.assertEqual(hp_drop(g, before), {"white_2": 42.0, "white_1": 22.0})
        g = game(["bride", "knight"], self.WHITE, white_x=(xc + 90.0, xc - 20.0))
        g.units["white_1"].update({"alive": False, "hp": 0.0})
        before = {uid: u["hp"] for uid, u in g.units.items()}
        shoot(g, "red_1", 45, 54)
        self.assertEqual(hp_drop(g, before), {"white_2": 42.0})

    def test_swarm_hits_every_living_enemy_after_any_hit_of_the_armed_wave(self):
        xc = wave_centre(self.WHITE, "bride")
        # precise (30 px < 55): touched 40 (+2 poison tick), then the swarm 52.0 (40 x 1.3) on EVERY living enemy, far or near; the swarm poisons nobody
        g = game(["bride", "knight"], self.WHITE, white_x=(xc + 30.0, xc + 400.0))
        before = {uid: u["hp"] for uid, u in g.units.items()}
        record = shoot(g, "red_1", 45, 54, "bride")
        self.assertEqual(hp_drop(g, before), {"white_1": round(40.0 + 52.0 + 2.0, 1), "white_2": 52.0})
        self.assertEqual(record["damage_dealt"], round(40.0 + 52.0 + 52.0, 1))
        self.assertNotIn("poison", g.units["white_2"]["statuses"])
        # 60 px: touched at 75 percent (30 + 2 poison) and, since 2026-11-18 (owner: the bat swarm comes with the ultimate and only when it hits), the swarm on everybody too
        g = game(["bride", "knight"], self.WHITE, white_x=(xc + 60.0, xc + 400.0))
        before = {uid: u["hp"] for uid, u in g.units.items()}
        shoot(g, "red_1", 45, 54, "bride")
        self.assertEqual(hp_drop(g, before), {"white_1": round(30.0 + 52.0 + 2.0, 1), "white_2": 52.0})
        # a wave that touches nobody (300 px away): no damage, no swarm
        g = game(["bride", "knight"], self.WHITE, white_x=(xc + 300.0, xc + 600.0))
        before = {uid: u["hp"] for uid, u in g.units.items()}
        shoot(g, "red_1", 45, 54, "bride")
        self.assertEqual(hp_drop(g, before), {})
        # the touched unit dies from the wave: no swarm (page: opp.hp > 0)
        g = game(["bride", "knight"], self.WHITE, white_x=(xc + 30.0, xc + 400.0))
        g.units["white_1"]["hp"] = 20.0
        before = {uid: u["hp"] for uid, u in g.units.items()}
        shoot(g, "red_1", 45, 54, "bride")
        self.assertEqual(hp_drop(g, before), {"white_1": 20.0})
        self.assertFalse(g.units["white_1"]["alive"])


WIZ = ["wizard", "knight", "bat"]


def wizard_game(white, white_x, wall=False):
    return game(WIZ, white, white_x=white_x, wall=wall)


class WizardBlast(unittest.TestCase):
    WHITE = ["skeleton", "knight", "bat"]
    FAR = (2500.0, 2700.0, 2900.0)

    def ground_x(self):
        record = shoot(wizard_game(self.WHITE, self.FAR), "red_1", 45, 50, "wizard")
        self.assertEqual(record["hit_type"], "ground")
        return record["landing_x"]

    def test_flat_blast_inside_234_px_and_nothing_outside(self):
        gx = self.ground_x()
        # victims stand beyond the landing point (a unit on the flight path would be hit by the shell itself)
        g = wizard_game(self.WHITE, (gx + 233.9, gx + 234.5, gx + 100.0))
        before = {uid: u["hp"] for uid, u in g.units.items()}
        record = shoot(g, "red_1", 45, 50, "wizard")
        self.assertEqual(record["hit_type"], "hero")
        # 36 x 1.5 = 54.0 flat at 233.9 px and at 100 px alike (no distance steps); 234.5 px is outside; no poison
        self.assertEqual(hp_drop(g, before), {"white_1": 54.0, "white_3": 54.0})
        self.assertEqual(record["hit_target"], "white_3,white_1")     # nearest to the impact first
        self.assertEqual(record["damage_dealt"], 108.0)
        self.assertEqual(g.units["white_1"]["statuses"], {})

    def test_dead_units_are_not_listed_or_hit(self):
        gx = self.ground_x()
        g = wizard_game(self.WHITE, (gx + 150.0, gx + 100.0, gx + 2000.0))
        g.units["white_2"].update({"alive": False, "hp": 0.0})
        record = shoot(g, "red_1", 45, 50, "wizard")
        self.assertEqual(record["hit_target"], "white_1")
        self.assertEqual(g.units["white_2"]["hp"], 0.0)

    def test_every_hit_of_the_blast_is_ramped_in_team_matches(self):
        gx = self.ground_x()
        g = wizard_game(self.WHITE, (gx + 200.0, gx + 100.0, gx + 2000.0))
        g.round_num = tuning.RAMP_START + 1                # ramp factor 1 + per_round x 2, from shared/team_tuning.json
        before = {uid: u["hp"] for uid, u in g.units.items()}
        shoot(g, "red_1", 45, 50, "wizard")
        want = round(36 * 1.5 * (1 + tuning.RAMP_PER_ROUND * 2) * 10 + 1e-9) / 10
        self.assertEqual(hp_drop(g, before), {"white_1": want, "white_2": want})

    def test_shell_hit_adds_the_flat_blast_for_everyone_in_range(self):
        direct = shoot(wizard_game(self.WHITE, (1250.0, 1700.0, 2000.0)), "red_1", 45, 54, "wizard")
        self.assertEqual(direct["hit_type"], "hero")
        self.assertLess(direct["landing_y"], 860.0)      # a contact in the air, not a ground landing
        centre = direct["landing_x"]
        g = wizard_game(self.WHITE, (1250.0, centre + 200.0, centre + 400.0))
        before = {uid: u["hp"] for uid, u in g.units.items()}
        record = shoot(g, "red_1", 45, 54, "wizard")
        self.assertEqual(record["landing_x"], centre)
        # white_1: shell 36 + blast 54.0 + 2 poison tick; white_2: blast only; white_3 at 400 px: outside
        self.assertEqual(hp_drop(g, before), {"white_1": round(36.0 + 54.0 + 2.0, 1), "white_2": 54.0})

    def test_blast_also_fires_when_the_shell_stops_on_a_floating_shield(self):
        shield = {"active": True, "x": 900.0, "y": 560.0, "width": 80.0, "height": 800.0}
        probe = wizard_game(self.WHITE, self.FAR)
        probe.shields["white"].update(shield)
        record = shoot(probe, "red_1", 45, 50, "wizard")
        self.assertEqual(record["hit_type"], "shield_blocked")
        stop = record["landing_x"]
        g = wizard_game(self.WHITE, (stop + 150.0, stop + 2000.0, stop + 2200.0))
        g.shields["white"].update(shield)
        before = {uid: u["hp"] for uid, u in g.units.items()}
        record = shoot(g, "red_1", 45, 50, "wizard")
        self.assertEqual(record["hit_type"], "shield_blocked")
        self.assertEqual(hp_drop(g, before), {"white_1": 54.0})


def session3():
    return srv.Session(seed=11, units=3, clock=lambda: 0.0, turn_seconds=99, human_turn_seconds=99,
                       hero_red=["knight", "skeleton", "bat"], hero_white=["knight", "skeleton", "bat"])


class TeammateGap(unittest.TestCase):
    def move(self, s, die, direction="forward", unit="red_1"):
        s.dice.randint = lambda lo, hi: die
        return s.call("submit_action", {"unit": unit, "action": {"type": "move", "direction": direction}})

    def test_move_steps_back_until_120_px_from_every_living_teammate(self):
        s = session3()
        s.engine.units["red_1"]["x"], s.engine.units["red_2"]["x"], s.engine.units["red_3"]["x"] = 300.0, 460.0, 680.0
        result = self.move(s, 6)                       # target 516 is 56 px from red_2
        self.assertEqual(result["x_after"], 332.4)     # 300 + 216 x 3/20
        self.assertTrue(result["blocked_by_teammate"])
        self.assertFalse(result["blocked_by_edge"])
        self.assertGreaterEqual(abs(332.4 - 460.0), 120)

    def test_a_dead_teammate_does_not_block(self):
        s = session3()
        s.engine.units["red_1"]["x"], s.engine.units["red_2"]["x"], s.engine.units["red_3"]["x"] = 300.0, 460.0, 680.0
        s.engine.units["red_2"].update({"alive": False, "hp": 0.0})
        result = self.move(s, 6)
        self.assertEqual(result["x_after"], 516.0)
        self.assertNotIn("blocked_by_teammate", result)

    def test_the_unit_stays_when_no_spot_on_the_way_is_free(self):
        s = session3()
        s.engine.units["red_1"]["x"], s.engine.units["red_2"]["x"], s.engine.units["red_3"]["x"] = 300.0, 420.0, 680.0
        result = self.move(s, 1)
        self.assertEqual(result["x_after"], 300.0)
        self.assertTrue(result["blocked_by_teammate"])

    def test_one_unit_per_team_moves_exactly_as_before(self):
        s = srv.Session(seed=11, units=1, clock=lambda: 0.0, turn_seconds=99, human_turn_seconds=99)
        s.engine.units["red_1"]["x"] = 300.0
        result = self.move(s, 6)
        self.assertEqual(result["x_after"], 516.0)
        self.assertNotIn("blocked_by_teammate", result)

    def push(self, attacker_x, target_x, mate_xs, mate_alive=True):
        g = srv.TrackedGameState(seed=2, units=3, hero_red=["hunchback", "knight", "bat"],
                                 hero_white=["knight", "skeleton", "bat"])
        g.units["red_1"]["x"] = attacker_x
        white = [g.units["white_%d" % i] for i in (1, 2, 3)]
        white[0]["x"] = target_x
        for unit, x in zip(white[1:], mate_xs):
            unit["x"] = x
            unit["alive"] = mate_alive
        white[0]["hp"] = white[0]["max_hp"] = 500.0
        result = g._apply_hit(g.units["red_1"], white[0], target_x, 500.0, False, 1.0, True)
        self.assertEqual(result["knockback"], 50)
        return white[0]["x"]

    def test_knockback_stops_120_px_before_a_teammate_and_never_passes_it(self):
        # the axe pushes the target away from the attacker (+x here)
        self.assertEqual(self.push(500.0, 1400.0, (1650.0, 1240.0)), 1450.0)       # free: full 50 px
        self.assertEqual(self.push(500.0, 1400.0, (1550.0, 1240.0)), 1430.0)       # teammate at 1550: stop at 1430
        self.assertEqual(self.push(500.0, 1400.0, (1520.0, 1240.0)), 1400.0)       # exactly 120 px: no room
        self.assertEqual(self.push(500.0, 1400.0, (1480.0, 1240.0)), 1400.0)       # already inside 120: stays, never behind it
        self.assertEqual(self.push(500.0, 1400.0, (1250.0, 1680.0)), 1450.0)       # teammates behind or far: unaffected
        self.assertEqual(self.push(500.0, 1400.0, (1550.0, 1240.0), mate_alive=False), 1450.0)   # dead teammates do not block

    def test_knockback_still_respects_the_zone_edge(self):
        self.assertEqual(self.push(500.0, 1800.0, (1500.0, 1300.0)), 1810.0)   # the retreat limit is 1810 since 2026-11-17 (was 1680)


def hit_x(red_hero="skeleton", angle=45, power=54):
    """An enemy x at which the throw (angle, power) from red_1 at x 500 is a direct hit."""
    for x in range(1100, 1800, 10):
        g = game([red_hero, "knight"], ["knight", "knight"], white_x=(float(x), 2500.0))
        if shoot(g, "red_1", angle, power)["hit_type"] == "hero":
            return float(x)
    raise AssertionError("no hitting x")


def landing_x(red_hero="skeleton", angle=45, power=50):
    record = shoot(game([red_hero, "knight"], ["knight", "knight"], white_x=(2500.0, 2700.0)), "red_1", angle, power)
    assert record["hit_type"] == "ground"
    return record["landing_x"]


class Comeback(unittest.TestCase):
    """B1 near miss, B2 underdog, B3 pity (shared/comeback.json); team matches only."""

    def test_near_miss_is_off_a_ground_landing_costs_no_hp(self):
        # OFF since 2026-11-18 (owner: damage without contact is a bug); shared/comeback.json near_miss.enabled false. A landing 60 px from the nearest box edge, a unit at 5 hp that the old rule would have killed,
        # and a dead unit: nobody loses hp, no near_miss entry, the throw still counts as a miss for the pity charge.
        gx = landing_x()
        g = game(["skeleton", "knight"], ["knight", "knight"], white_x=(gx + 130.0, gx + 380.0))
        before = {uid: u["hp"] for uid, u in g.units.items()}
        record = shoot(g, "red_1", 45, 50)
        self.assertEqual(record["hit_type"], "ground")
        self.assertNotIn("near_miss", record)
        self.assertEqual(hp_drop(g, before), {})
        self.assertEqual(record["damage_dealt"], 0.0)
        self.assertEqual(g.pity["red"], 1)
        s = srv.Session(seed=11, units=2, clock=lambda: 0.0, turn_seconds=99, human_turn_seconds=99,
                        hero_red=["skeleton", "knight"], hero_white=["knight", "knight"])
        s.engine.wind = 0
        s.engine.central_wall_hp = 0
        s.engine.units["red_1"]["x"] = 500.0
        s.engine.units["white_1"]["x"] = gx + 130.0
        s.engine.units["white_2"]["x"] = gx + 2000.0
        s.engine.units["white_1"]["hp"] = 5.0
        s.call("submit_action", {"unit": "red_1", "action": {"type": "throw", "angle": 45, "power": 50}})
        s.call("end_turn", {"phase": "human"})
        summary = s.call("end_turn", {"phase": "agent"})
        self.assertTrue(s.engine.units["white_1"]["alive"])
        self.assertEqual(s.energy["red"], 0)
        self.assertNotIn("near_miss", summary["throws"][0])
        self.assertEqual(summary["pity"]["red"], {"misses": 1, "bonus": 0.4})

    def test_the_dormant_near_miss_formula_still_works_when_switched_on(self):
        # the switch is a single flag: with it on, the engine again hurts the nearest unit within reach (the old rule, reach 120 px)
        gx = landing_x()
        g = game(["skeleton", "knight"], ["knight", "knight"], white_x=(gx + 130.0, gx + 380.0))
        old = engine.comeback.NEAR_ENABLED
        engine.comeback.NEAR_ENABLED = True
        try:
            record = shoot(g, "red_1", 45, 50)
        finally:
            engine.comeback.NEAR_ENABLED = old
        self.assertEqual(record["near_miss"], {"target": "white_1", "damage": 10.8, "edge": 60.0})

    def test_no_near_miss_on_a_direct_hit(self):
        g = game(["skeleton", "knight"], ["knight", "knight"], white_x=(hit_x(), hit_x() + 150.0))
        record = shoot(g, "red_1", 45, 54)
        self.assertEqual(record["hit_type"], "hero")
        self.assertNotIn("near_miss", record)

    def test_pity_grows_per_miss_applies_to_the_next_direct_hit_and_resets(self):
        x = hit_x()
        g = game(["skeleton", "knight"], ["knight", "knight"], white_x=(2500.0, 2700.0))
        for expected in (1, 2):
            shoot(g, "red_1", 45, 50)      # lands far from everybody: a plain miss
            self.assertEqual(g.pity, {"red": expected, "white": 0})
        g.units["white_1"]["x"] = x
        record = shoot(g, "red_1", 45, 54)
        self.assertEqual(record["hit_type"], "hero")
        self.assertEqual(record["damage_dealt"], 43.2)                          # 24 x (1 + 0.4 x 2)
        self.assertEqual(g.pity["red"], 0)
        self.assertEqual(shoot(g, "red_1", 45, 54)["damage_dealt"], 24.0)       # the charge was used up

    def test_pity_bonus_is_capped_at_plus_160_percent_and_teams_count_separately(self):
        x = hit_x()
        g = game(["skeleton", "knight"], ["knight", "knight"], white_x=(2500.0, 2700.0))
        for _ in range(7):
            shoot(g, "red_1", 45, 50)
        self.assertEqual(g.pity, {"red": 7, "white": 0})
        g.units["white_1"]["x"] = x
        self.assertEqual(shoot(g, "red_1", 45, 54)["damage_dealt"], 55.2)       # 24 x min(2.3, 1 + 1.6): the owner's cap

    def test_a_blocked_throw_counts_as_a_miss(self):
        g = game(["skeleton", "knight"], ["knight", "knight"], white_x=(1300.0, 1500.0), wall=True)
        record = shoot(g, "red_1", 45, 50)
        self.assertEqual(record["hit_type"], "central_wall")
        self.assertEqual(g.pity["red"], 1)

    def test_underdog_multiplies_hits_of_the_trailing_team_and_never_goes_below_one(self):
        g = game(["skeleton", "knight"], ["skeleton", "knight"])
        attacker, target = g.units["white_1"], g.units["red_1"]
        for unit in g.units.values():
            if unit["team"] == "white":
                unit["hp"] = 300.0                                   # white share 0.6, red share 1.0
        def hit():
            g._cb_lock = None   # every call is a separate throw: the comeback numbers are fixed by the first hit of ONE throw (red-team R11B-2)
            return g._apply_hit(attacker, target, target["x"], target["y"] - 100, False, 1.0, True)["damage"]
        self.assertEqual(g.underdog_bonus("white"), 0.8)             # deficit 0.4 / 0.5 = +80 percent
        self.assertEqual(g.underdog_bonus("red"), 0.0)
        self.assertEqual(hit(), 43.2)                                # 24 x 1.8
        target["hp"] = 500.0
        attacker2, target2 = g.units["red_1"], g.units["white_1"]
        g._cb_lock = None
        self.assertEqual(g._apply_hit(attacker2, target2, target2["x"], target2["y"] - 100, False, 1.0, True)["damage"], 24.0)
        for unit in g.units.values():
            if unit["team"] == "white":
                unit["hp"] = 50.0                                    # share 0.1: capped at +100 percent
        self.assertEqual(hit(), 48.0)

    def test_area_effects_take_the_same_factors(self):
        gx = landing_x("wizard")
        g = game(["wizard", "knight"], ["knight", "knight"], white_x=(gx + 200.0, gx + 100.0))
        g.pity["red"] = 2
        g.units["red_1"]["hp"] = g.units["red_2"]["hp"] = 400.0         # red share 0.8 against 1.0: underdog +40 percent
        before = {uid: u["hp"] for uid, u in g.units.items()}
        shoot(g, "red_1", 45, 50, "wizard")
        # nearest first: white_2 takes 54.0 x min(2.3, 1.4 x 1.8 = 2.52) = 124.2; shares are read at the moment of each hit, so white_1
        # white_1 (hit second) takes the same 124.2: the page fixes the shares and the pity charge at the projectile's first damage (cbBegin), and since red-team R11B-2 the engine does too
        # (the 111.9 pinned here on 2026-11-18 was the engine's per-hit recompute, not the page's number)
        self.assertEqual(hp_drop(g, before), {"white_2": 124.2, "white_1": 124.2})

    def test_one_unit_per_team_has_no_comeback_pack(self):
        g = srv.TrackedGameState(seed=5, units=1, hero_red="skeleton", hero_white="knight")
        g.wind = 0
        g.central_wall_hp = 0
        g.units["red_1"]["x"] = 500.0
        g.units["white_1"]["x"] = landing_x() + 200.0
        record = shoot(g, "red_1", 45, 50)
        self.assertNotIn("near_miss", record)
        self.assertEqual(g.pity, {"red": 0, "white": 0})
        self.assertEqual(g.units["white_1"]["hp"], 198.0)
        s = srv.Session(seed=5, units=1, clock=lambda: 0.0, turn_seconds=99, human_turn_seconds=99)
        self.assertNotIn("pity", s.public_state())
        self.assertNotIn("underdog_bonus", s.public_state())

    def test_public_state_exposes_pity_and_underdog_in_team_matches(self):
        s = session3()
        state = s.public_state()
        self.assertEqual(state["pity"], {"red": {"misses": 0, "bonus": 0.0}, "white": {"misses": 0, "bonus": 0.0}})
        self.assertEqual(state["underdog_bonus"], {"red": 0.0, "white": 0.0})
        s.engine.pity["white"] = 9
        s.engine.units["white_1"]["hp"] = 0.0
        view = s.public_state()
        self.assertEqual(view["pity"]["white"], {"misses": 9, "bonus": 1.6})
        self.assertGreater(view["underdog_bonus"]["white"], 0.0)
        # real combined factor after the cap: underdog 1 + min(1, (1 - 0.667)/0.5) = 1.667 x (1 + 1.6) = 4.3 -> 2.3
        self.assertEqual(view["comeback_multiplier"]["white"], 2.3)
        self.assertEqual(view["comeback_multiplier"]["red"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
