# Kiro task 130 — dead links appeared again under `.kiro/specs/` after task 114 (work block B10)

Main line, 2026-11-15: after task 114 the export `(not published)` was rebuilt and the privacy gate (`(not published)`, one line per hit: class, check, `file:line`) now reports many BLOCK `P13` hits under `.kiro/specs/` (for example `.kiro/specs/fonts/requirements.md:8`, `.kiro/specs/gameplay-experience/tasks.md:34`, `.kiro/specs/judging-fit/tasks.md:5`). Before task 114 they were handled. Count them with `grep '^BLOCK' (not published) | awk '{print $2}' | sort | uniq -c` and list the distinct files with `awk '{print $3}' | cut -d: -f1 | sort -u`.

Read: `scripts/release/export_manifest.json` (rule order; the `unpublish_refs` rules and the rules for `.kiro/specs/`), `scripts/release/export_tree.py` (`unpublish_refs`: what it rewrites), `scripts/release/privacy_gate.py` (P13), `scripts/test_export_tree.py`, and the source line of two or three hits to see what kind of reference they hold (a path in backticks, a markdown link, a relative `(not published)` path, a path with a glob). Never repeat a private value in any file you write.

Do, saving after each:
1. Find why the `.kiro/specs/` files are no longer rewritten (rule order, a glob that does not match, a reference shape not handled) and fix it in `export_manifest.json` and/or `export_tree.py`; add a regression test on a toy tree in `scripts/test_export_tree.py` that builds a toy `(not published)` with a dangling backticked path and a dangling markdown link and asserts both become `(not published)` while a link to a file that IS in the export stays.
2. Make the test that loads the REAL manifest assert that `(not published)` resolves to a rule with the `unpublish_refs` transform and that the three `.kiro/steering/` files, `(not published)` and `docs/*.md` do too (reuse the matcher of `export_tree.py`).
3. Run `python3 -B scripts/test_export_tree.py` and `python3 -B scripts/test_privacy_gate.py`; paste the last lines. Do NOT run `export_tree.py --apply` and do not touch `(not published)`; the main line re-exports.

Touch only `scripts/release/export_manifest.json`, `scripts/release/export_tree.py`, `scripts/test_export_tree.py` and the result file exactly named `docs/kiro_130_result_gpt-5.6-terra.md` (max 15 lines: cause, files changed, commands with last output lines, what you did not run). No network, no git.
