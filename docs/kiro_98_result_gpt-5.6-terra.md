# Task 98 result — gpt-5.6-terra

Changed `scripts/release/export_manifest.json`: moved the three broad documentation `unpublish_refs` transforms after all document exclusions and immediately before the final `docs/` include.
Changed `scripts/test_export_tree.py`: `test_real_manifest_keeps_private_docs_excluded` loads the real manifest, checks required decisions with `choose_rule`, and reports any earlier non-exclude rule that overlaps a more-specific exclusion.

Verification run:
`python3 -B scripts/test_export_tree.py`
Last output lines:
```
Ran 6 tests in 0.628s

OK
```

Not run: `export_tree.py --apply`; `(not published)` was not touched. No network or git commands were run.
