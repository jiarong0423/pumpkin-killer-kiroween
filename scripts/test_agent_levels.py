#!/usr/bin/env python3
"""Tests for the public-information MCP agent difficulty levels."""
import inspect
import os
import tempfile
import unittest
from unittest import mock

import agent_levels
import sweep_agent_levels as sweep

# Read before any test runs; the last test compares against it.
REAL_REPORT = sweep.REPORT_PATH
with open(REAL_REPORT, "rb") as _handle:
    REPORT_BYTES_AT_IMPORT = _handle.read()


class AgentLevelsTests(unittest.TestCase):
    def test_same_seed_gives_same_measurement(self):
        first = sweep.play_match("normal", 101, "human_vs_agent", 12)
        second = sweep.play_match("normal", 101, "human_vs_agent", 12)
        self.assertEqual(first, second)

    def test_levels_differ_only_by_the_shared_knob_table(self):
        expected_keys = {
            "perception_target_px", "perception_wind", "aim_power_error", "memory", "fit_wind",
        }
        configs = [agent_levels.level_config(level) for level in agent_levels.LEVEL_NAMES]
        self.assertTrue(all(set(config) == expected_keys for config in configs))
        self.assertEqual(len({tuple(sorted(config.items())) for config in configs}), len(configs))
        self.assertNotIn("if level ==", inspect.getsource(agent_levels.LevelAgent))

    def test_small_fixed_sweep_orders_hit_rates(self):
        rows = sweep.run_sweep(total_throws=300, seeds=sweep.DEFAULT_SEEDS)   # 100 throws was too few once the wind became unequal (2026-11-16): the order is stable from 200 on
        rates = [row["hit_rate"] for row in rows]
        self.assertLess(rates[0], rates[1])
        self.assertLess(rates[1], rates[2])

    def test_agent_client_rejects_any_tool_outside_the_six(self):
        expected = {
            "get_public_state", "get_history", "submit_action", "end_turn", "set_notes", "get_notes",
        }
        self.assertEqual(agent_levels.PUBLIC_TOOLS, expected)
        with self.assertRaises(AssertionError):
            agent_levels.PublicToolClient(None).call("resolve_round", {})
        # play_match has its own assertion over the complete recorded call sequence.
        self.assertEqual(len(sweep.play_match("easy", 101, "agent_vs_agent", 2)), 2)

    def test_sweep_writes_the_table_file(self):
        # A tiny run must never replace the real report in docs/, so write to a temp file.
        rows = sweep.run_sweep(total_throws=50, seeds=sweep.DEFAULT_SEEDS)
        with tempfile.TemporaryDirectory() as folder:
            temp_report = os.path.join(folder, "sweep.md")
            with mock.patch.object(sweep, "REPORT_PATH", temp_report):
                sweep.write_report(rows, 50, sweep.DEFAULT_SEEDS)
            self.assertTrue(os.path.isfile(temp_report))
            with open(temp_report, "r", encoding="utf-8") as report:
                text = report.read()
        self.assertIn("| normal |", text)
        self.assertIn("95% hit-rate interval", text)


def _read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


class RealReportIsUntouched(unittest.TestCase):
    """docs/ai_levels_sweep_20261115.md must be byte-identical after the whole run."""

    def test_real_report_bytes_unchanged(self):
        self.assertEqual(_read_bytes(REAL_REPORT), REPORT_BYTES_AT_IMPORT)


def load_tests(loader, standard_tests, pattern):
    """Put the byte check last, so it observes the file after every other test has run."""
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(AgentLevelsTests))
    suite.addTests(loader.loadTestsFromTestCase(RealReportIsUntouched))
    return suite


if __name__ == "__main__":
    unittest.main()
