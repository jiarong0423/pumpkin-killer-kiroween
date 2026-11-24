#!/usr/bin/env python3
"""Socket-free tests of the slot filler's decisions (scripts/fill_room.py; docs/ADR_unit_slot_fill_20261124.md): the subtraction, the draw, the refusal of the agent filler."""
import argparse
import asyncio
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fill_room as fr  # noqa: E402
import run_hybrid_room as hybrid  # noqa: E402

import tempfile  # noqa: E402
from unittest import mock  # noqa: E402
_LOGDIR = tempfile.mkdtemp(prefix="pk-fill-test-")
fr.LOG_PATH = os.path.join(_LOGDIR, "fill_room.log")   # red-team R1 B: the tests that call fill() on purpose with a missing room must not write ERROR lines into the real log
fr.RUN_LOG_PATH = os.path.join(_LOGDIR, "fill_room_run.log")


def seat(seat_id, team, units, ready=True):
    return {"seat_id": seat_id, "team": team, "ready": ready, "units": units}


class RemainderTests(unittest.TestCase):
    holders = {"red-1", "white-1"}

    def test_remainder_is_team_size_minus_the_units_the_humans_named(self):
        seats = [seat("red-1", "red", []), seat("white-1", "white", []), seat("red-2", "red", ["skeleton"]), seat("red-3", "red", ["wizard", "bat"])]
        self.assertEqual(fr.team_remainders(3, seats, self.holders), {"red": 0, "white": 3})

    def test_open_slots_on_both_teams(self):
        seats = [seat("red-2", "red", ["skeleton", "bat"]), seat("white-2", "white", ["wizard"])]
        self.assertEqual(fr.team_remainders(3, seats, self.holders), {"red": 1, "white": 2})

    def test_six_humans_leave_nothing_to_fill(self):
        seats = [seat("red-%d" % i, "red", ["a"]) for i in (2, 3, 4)] + [seat("white-%d" % i, "white", ["b"]) for i in (2, 3, 4)]
        self.assertEqual(fr.team_remainders(3, seats, self.holders), {"red": 0, "white": 0})

    def test_placeholders_and_spectators_are_not_humans(self):
        seats = [seat("red-1", "red", ["x", "y", "z"]), seat("spectator-1", "spectator", ["q"]), seat("white-2", "white", ["wizard"])]
        self.assertEqual(fr.team_remainders(3, seats, self.holders), {"red": 3, "white": 2})

    def test_a_ready_human_without_a_unit_list_counts_as_the_whole_team(self):
        self.assertEqual(fr.team_remainders(3, [seat("red-2", "red", [], ready=True)], self.holders), {"red": 0, "white": 3})
        self.assertEqual(fr.team_remainders(3, [seat("red-2", "red", [], ready=False)], self.holders), {"red": 3, "white": 3})

    def test_never_below_zero_and_one_unit_rooms_work(self):
        self.assertEqual(fr.team_remainders(2, [seat("red-2", "red", ["a", "b", "c"])], self.holders), {"red": 0, "white": 2})
        self.assertEqual(fr.team_remainders(1, [seat("red-2", "red", ["a"])], self.holders), {"red": 0, "white": 1})


class DrawTests(unittest.TestCase):
    def test_the_hero_list_matches_the_game_hero_list(self):
        self.assertEqual(fr.HEROES, hybrid.HEROES)

    def test_the_draw_is_reproducible_and_skips_taken_heroes(self):
        taken = ["skeleton", "wizard"]
        a = fr.draw_heroes("ABC234", "white", 3, taken, 3)
        b = fr.draw_heroes("ABC234", "white", 3, taken, 3)
        self.assertEqual(a, b, "same room code and team: same draw")
        named, full = a
        self.assertEqual(len(named), 3)
        self.assertEqual(len(set(named)), 3, "no repeated hero")
        self.assertFalse(set(named) & set(taken), "never a hero a teammate took")
        self.assertEqual(full[:3], named)
        self.assertEqual(len(full), 3)

    def test_the_draw_differs_between_rooms_and_teams(self):
        draws = {fr.draw_heroes(code, team, 3, [], 3)[0].__repr__() for code in ("AAAAAA", "BBBBBB", "CCCCCC") for team in ("red", "white")}
        self.assertGreater(len(draws), 1)

    def test_the_full_list_is_team_size_long_even_when_few_are_named(self):
        named, full = fr.draw_heroes("ABC234", "red", 1, ["skeleton", "wizard"], 3)
        self.assertEqual(len(named), 1)
        self.assertEqual(len(full), 3)
        self.assertEqual(len(set(full)), 3)

    def test_seed_is_positive_and_stable(self):
        self.assertGreater(fr.seed_from("ABC234", "red"), 0)
        self.assertEqual(fr.seed_from("ABC234", "red"), fr.seed_from("ABC234", "red"))
        self.assertNotEqual(fr.seed_from("ABC234", "red"), fr.seed_from("ABC234", "white"))


class FormationRecheckTests(unittest.TestCase):
    holders = {"red-1", "white-1"}

    def humans(self):
        return [seat("red-2", "red", ["skeleton"]), seat("red-3", "red", ["wizard", "bat"])]

    def test_the_same_human_seats_pass(self):
        now = self.humans() + [seat("red-1", "red", [], ready=False), seat("white-1", "white", [], ready=False), seat("white-2", "white", ["a", "b", "c"])]
        self.assertEqual(fr.formation_unchanged(self.humans(), now, self.holders, {"white-2"}), (True, "unchanged"))

    def test_a_human_who_left_is_caught(self):
        ok, why = fr.formation_unchanged(self.humans(), [seat("red-2", "red", ["skeleton"])], self.holders, set())
        self.assertFalse(ok)
        self.assertIn("left=['red-3']", why)

    def test_a_late_human_is_caught(self):
        ok, why = fr.formation_unchanged(self.humans(), self.humans() + [seat("white-5", "white", ["x"])], self.holders, set())
        self.assertFalse(ok)
        self.assertIn("new=['white-5']", why)

    def test_a_changed_unit_list_is_caught(self):
        ok, why = fr.formation_unchanged(self.humans(), [seat("red-2", "red", ["skeleton", "bat"]), seat("red-3", "red", ["wizard", "bat"])], self.holders, set())
        self.assertFalse(ok)
        self.assertIn("changed=['red-2']", why)

    def test_a_human_who_is_no_longer_ready_is_caught(self):
        ok, why = fr.formation_unchanged(self.humans(), [seat("red-2", "red", ["skeleton"]), seat("red-3", "red", ["wizard", "bat"], ready=False)], self.holders, set())
        self.assertFalse(ok)
        self.assertIn("no longer ready", why)

    def test_filler_and_placeholder_seats_are_not_humans(self):
        now = self.humans() + [seat("red-1", "red", ["junk"]), seat("red-4", "red", ["hag"])]
        self.assertTrue(fr.formation_unchanged(self.humans(), now, self.holders, {"red-4"})[0])


class UsageTests(unittest.TestCase):
    def test_base_url_drops_the_path(self):
        self.assertEqual(fr.base_url("ws://localhost:8765/ws"), "ws://localhost:8765")
        self.assertEqual(fr.base_url("ws://localhost:8765/"), "ws://localhost:8765")
        self.assertEqual(fr.base_url("ws://localhost:8765"), "ws://localhost:8765")

    def test_the_agent_filler_is_refused_before_anything_is_joined(self):
        args = argparse.Namespace(relay="ws://127.0.0.1:1", code="ABC234", filler="agent", settle=1, max_wait=1, join_wait=1, level="normal", speed=0, max_seconds=1)
        self.assertEqual(asyncio.run(fr.fill(args)), fr.EXIT_AGENT)

    def test_a_missing_room_gives_a_join_error_not_a_crash(self):
        args = argparse.Namespace(relay="ws://127.0.0.1:1", code="ABC234", filler="computer", settle=1, max_wait=1, join_wait=1, level="normal", speed=0, max_seconds=1)
        self.assertEqual(asyncio.run(fr.fill(args)), fr.EXIT_JOIN)


class PlaceholderReleaseTests(unittest.TestCase):
    """Red-team R2B-P1-1 (Option A): `finally` must NOT unconditionally call leave() on the team placeholders.
    Only after formation_unchanged passes and the release step runs may the placeholders leave (2 calls total: red + white);
    failure paths (EXIT_CHANGED, EXIT_WAIT) keep placeholders (0 calls) and log honestly about grace expiry."""

    def _make_args(self, max_wait=1.0, join_wait=1.0):
        return argparse.Namespace(
            relay="ws://127.0.0.1:1", code="ABC234", filler="computer",
            settle=0.01, max_wait=max_wait, join_wait=join_wait,
            level="normal", speed=0, max_seconds=5,
        )

    def _make_holder_factory(self, initial_seats, team_size=3, start_on_second_leave=False):
        created = []

        class FakeHolder:
            def __init__(self, url, code, team, state):
                self.url, self.code, self.team, self.state = url, code, team, state
                self.socket = None
                self.task = None
                self.seat_id = ""
                self.leave_calls = 0
                created.append(self)

            async def join(self):
                self.seat_id = "%s-1" % self.team
                self.state["team_size"] = team_size
                if not self.state["seats"]:
                    self.state["seats"] = [dict(s) for s in initial_seats]
                if self.team in fr.TEAMS:
                    self.state["seats"].append(seat(self.seat_id, self.team, [], ready=False))

            async def leave(self):
                self.leave_calls += 1
                self.state["seats"] = [s for s in self.state["seats"] if s.get("seat_id") != self.seat_id]
                if start_on_second_leave and self.team in fr.TEAMS:
                    left_placeholders = sum(h.leave_calls for h in created if h.team in fr.TEAMS)
                    if left_placeholders >= 2:
                        self.state["started"] = True

        return FakeHolder, created

    def _placeholder_leaves(self, created):
        return sum(h.leave_calls for h in created if h.team in fr.TEAMS)

    def test_exit_wait_humans_never_calls_placeholder_leave(self):
        fake_cls, created = self._make_holder_factory([seat("red-2", "red", ["skeleton"], ready=False)])
        logs = []
        with mock.patch.object(fr, "Holder", fake_cls), \
                mock.patch.object(fr, "POLL_SECONDS", 0.01), \
                mock.patch.object(fr, "log", side_effect=logs.append):
            rc = asyncio.run(fr.fill(self._make_args(max_wait=0.05)))
        self.assertEqual(rc, fr.EXIT_WAIT)
        self.assertEqual(self._placeholder_leaves(created), 0, "EXIT_WAIT (humans) must not call leave() on placeholders")
        self.assertTrue(any("placeholders kept" in line and "grace period" in line for line in logs), logs)

    def test_exit_wait_fillers_not_ready_never_calls_placeholder_leave(self):
        humans = [seat("red-2", "red", ["skeleton"]), seat("red-3", "red", ["wizard", "bat"])]
        fake_cls, created = self._make_holder_factory(humans)
        logs = []

        async def slow_filler(kind, team, command, timeout, log_path):
            await asyncio.sleep(10)

        with mock.patch.object(fr, "Holder", fake_cls), \
                mock.patch.object(fr, "POLL_SECONDS", 0.01), \
                mock.patch.object(fr, "log", side_effect=logs.append), \
                mock.patch.object(hybrid, "run_process_seat", side_effect=slow_filler):
            rc = asyncio.run(fr.fill(self._make_args(join_wait=0.05)))
        self.assertEqual(rc, fr.EXIT_WAIT)
        self.assertEqual(self._placeholder_leaves(created), 0, "EXIT_WAIT (fillers) must not call leave() on placeholders")
        self.assertTrue(any("placeholders kept" in line and "grace period" in line for line in logs), logs)

    def test_exit_changed_never_calls_placeholder_leave(self):
        humans = [seat("red-2", "red", ["skeleton"]), seat("red-3", "red", ["wizard", "bat"])]
        fake_cls, created = self._make_holder_factory(humans)
        logs = []
        expected_picks, _ = fr.draw_heroes("ABC234", "white", 3, [], 3)

        async def filler_while_human_leaves(kind, team, command, timeout, log_path):
            state = created[0].state
            state["seats"].append(seat("white-2", "white", list(expected_picks), ready=True))
            # A human seat drops after the fill was planned, triggering formation_unchanged -> False.
            state["seats"] = [s for s in state["seats"] if s.get("seat_id") != "red-3"]
            await asyncio.sleep(10)

        with mock.patch.object(fr, "Holder", fake_cls), \
                mock.patch.object(fr, "POLL_SECONDS", 0.01), \
                mock.patch.object(fr, "HOLD_ON_CHANGE_SECONDS", 0.0), \
                mock.patch.object(fr, "log", side_effect=logs.append), \
                mock.patch.object(hybrid, "run_process_seat", side_effect=filler_while_human_leaves):
            rc = asyncio.run(fr.fill(self._make_args()))
        self.assertEqual(rc, fr.EXIT_CHANGED)
        self.assertEqual(self._placeholder_leaves(created), 0, "EXIT_CHANGED must not call leave() on placeholders")
        self.assertTrue(any("placeholders kept" in line and "grace period" in line for line in logs), logs)
        self.assertFalse(any("does not start behind your back" in line for line in logs), logs)

    def test_success_path_calls_placeholder_leave_twice_total(self):
        humans = [seat("red-2", "red", ["skeleton"]), seat("red-3", "red", ["wizard", "bat"])]
        fake_cls, created = self._make_holder_factory(humans, start_on_second_leave=True)
        logs = []
        expected_picks, _ = fr.draw_heroes("ABC234", "white", 3, [], 3)

        async def happy_filler(kind, team, command, timeout, log_path):
            state = created[0].state
            state["seats"].append(seat("white-2", "white", list(expected_picks), ready=True))
            res = hybrid.SeatResult(kind, team)
            res.data = {"reason": "game_over", "winner": "red", "errors": []}
            return res

        with mock.patch.object(fr, "Holder", fake_cls), \
                mock.patch.object(fr, "POLL_SECONDS", 0.01), \
                mock.patch.object(fr, "log", side_effect=logs.append), \
                mock.patch.object(hybrid, "run_process_seat", side_effect=happy_filler):
            rc = asyncio.run(fr.fill(self._make_args()))
        self.assertEqual(rc, fr.EXIT_OK)
        self.assertEqual(self._placeholder_leaves(created), 2, "success path must call leave() once per placeholder (2 total)")


if __name__ == "__main__":
    unittest.main()
