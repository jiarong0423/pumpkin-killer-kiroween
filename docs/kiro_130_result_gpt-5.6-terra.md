# Task 130 result

Changed `scripts/release/export_manifest.json`: directory-prefix `unpublish_refs` rules now cover nested specs, steering, and skills.
Changed `scripts/test_export_tree.py`: nested-spec toy export verifies dangling code and Markdown links become `(not published)` while an exported relative link remains; real-manifest assertions cover specs, three steering files, skills, and docs.
Cause: extension-specific transform rules allowed nested `.kiro/specs/` text to fall through to the `.kiro/` include rule without reference rewriting.
Verification: `python3 -B scripts/test_export_tree.py` last lines: `Ran 7 tests in 0.718s` / `OK`.
Verification: `python3 -B scripts/test_privacy_gate.py` last lines: `Ran 8 tests in 5.107s` / `OK` / `OK`.
Did not run `export_tree.py --apply` or touch the release tree.
The requested gate-log counting command was not run because its permission request was not answered.
