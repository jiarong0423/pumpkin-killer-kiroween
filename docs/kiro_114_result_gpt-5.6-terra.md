# Task 114 result

Changed `scripts/release/export_tree.py`: `unpublish_refs` now rewrites bare paths and `:line` suffixes; ordered manifest transforms let the queue remove its credit sentence before reference rewriting.
Changed `scripts/release/export_manifest.json` to apply `unpublish_refs` to steering and after the queue transform.
Changed `scripts/release/privacy_gate.py`: P7 permits only the root `LICENSE` line beginning `Copyright (c)`; `README_gate.md` documents that narrow exception.
Added toy-tree coverage in `scripts/test_export_tree.py` and a narrow P7 test in `scripts/test_privacy_gate.py`.

Verification run:
`python3 -B scripts/test_export_tree.py`
Last lines: `Ran 7 tests in 0.710s` / `OK`
`python3 -B scripts/test_privacy_gate.py`
Last lines: `OK` / `OK`

Not verified: I did not run `export_tree.py --apply` or touch the export tree, as required. The main line must re-export and rerun the gate.
