#!/usr/bin/env python3
"""End-to-end local relay regression check. Requires loopback socket permission."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import e2e_local  # noqa: E402


class LocalEndToEndTest(unittest.TestCase):
    def test_three_rounds_share_hashes_and_hide_private_item_slots(self):
        result = e2e_local.run_e2e(rounds=3)
        self.assertEqual(result["rounds"], 3)
        self.assertEqual(len(result["round_hashes"]), 3)
        self.assertTrue(all(isinstance(value, str) and len(value) == 8
                            for value in result["round_hashes"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
