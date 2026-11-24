#!/usr/bin/env python3
"""scripts/stress_judge_relay.py counts a hash mismatch once per failed assertion, not once per traceback line (red team R1-8)."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stress_judge_relay as S  # noqa: E402

REAL_FAILURE = '''======================================================================
FAIL: test_3v3_ultimate_over_page_judge_relay (__main__.PageJudgeRoomTest.test_3v3_ultimate_over_page_judge_relay)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/x/scripts/test_page_judge_relay.py", line 196, in test_3v3_ultimate_over_page_judge_relay
    self.assertEqual(len(set(by_seat.values())), 1, "round %s hash differs: %s" % (number, by_seat))
AssertionError: 2 != 1 : round 12 hash differs: {'red-1': '5b8d6c88', 'white-1': '21cf2992'}

----------------------------------------------------------------------
Ran 4 tests in 15.154s
FAILED (failures=1)
'''


class ParseTest(unittest.TestCase):
    def test_one_failure_is_counted_once(self):
        found = S.HASH_RE.findall(REAL_FAILURE)
        self.assertEqual(len(found), 1, found)
        self.assertEqual(found[0][0], "12")
        self.assertIn("red-1", found[0][1])

    def test_traceback_source_line_alone_is_not_a_result(self):
        source_only = '    self.assertEqual(len(set(by_seat.values())), 1, "round %s hash differs: %s" % (number, by_seat))\n'
        self.assertEqual(S.HASH_RE.findall(source_only), [])

    def test_two_failed_assertions_count_twice(self):
        self.assertEqual(len(S.HASH_RE.findall(REAL_FAILURE + REAL_FAILURE.replace("round 12", "round 6"))), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
