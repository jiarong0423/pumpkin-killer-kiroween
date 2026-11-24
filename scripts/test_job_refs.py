#!/usr/bin/env python3
"""Tests for ordered Colab queue references."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "colab"))

from job_refs import resolve_refs


class ResolveRefsTests(unittest.TestCase):
    def test_ordered_refs_preserve_style_then_identity(self):
        refs = {"style": "style.png", "identity": "identity.png"}
        self.assertEqual(
            resolve_refs({"refs": ["style", "identity"]}, refs),
            ["style.png", "identity.png"],
        )

    def test_single_ref_is_resolved_as_one_item(self):
        self.assertEqual(resolve_refs({"ref": "only"}, {"only": "only.png"}), ["only.png"])

    def test_unknown_name_has_a_clear_error(self):
        with self.assertRaisesRegex(ValueError, r"^unknown reference name: 'missing'$"):
            resolve_refs({"refs": ["missing"]}, {})

    def test_queue_ordered_references_exist_in_its_ref_table(self):
        queue = json.loads((ROOT / "colab" / "jobs_missing_20261115.json").read_text(encoding="utf-8"))
        self.assertEqual(len(queue["jobs"]), 8)
        for job in queue["jobs"]:
            if "refs" not in job:
                self.assertIn("ref", job)
                continue
            self.assertTrue(all(name in queue["refs"] for name in job["refs"]))
            self.assertEqual(
                resolve_refs(job, queue["refs"]),
                [queue["refs"][name] for name in job["refs"]],
            )


if __name__ == "__main__":
    unittest.main()
