#!/usr/bin/env python3
"""Shared-vector tests for the public adaptive difficulty controller."""
import json
import os
import unittest

import adaptive_level

HERE = os.path.dirname(os.path.abspath(__file__))
VECTORS = os.path.join(HERE, "adaptive_level_vectors.json")


def load_vectors():
    with open(VECTORS, "r", encoding="utf-8") as source:
        return json.load(source)


class AdaptiveLevelTests(unittest.TestCase):
    def test_shared_vectors(self):
        for vector in load_vectors():
            controller = adaptive_level.AdaptiveLevel()
            levels = [controller.record_hit(hit)["level"] for hit in vector["hits"]]
            self.assertEqual(levels, vector["levels"], vector["name"])
            self.assertEqual(controller.public_state()["last_change"], vector["last_change"], vector["name"])

    def test_public_state_exposes_only_required_values(self):
        self.assertEqual(set(adaptive_level.AdaptiveLevel().public_state()), {"level", "last_change"})

    def test_identical_inputs_are_deterministic(self):
        hits = [True, False, True, False, False, True, True]
        first = adaptive_level.AdaptiveLevel()
        second = adaptive_level.AdaptiveLevel()
        self.assertEqual([first.record_hit(hit) for hit in hits], [second.record_hit(hit) for hit in hits])


if __name__ == "__main__":
    unittest.main()
