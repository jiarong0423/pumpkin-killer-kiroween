# Kiro task 114 — clear the last privacy-gate BLOCK hits on the export (work block B10)

Main line, 2026-11-15: after tasks 95, 96 and 98 the export `(not published)` still has 8 BLOCK hits (gate log `(not published)`, format `class check file:line`):
`P7 LICENSE:3` and seven `P13` dangling links at `.kiro/steering/kiro_assignment.md:6`, `.kiro/steering/kiro_assignment.md:9`, `docs/audio_gap_options_20261115.md:6`, `docs/kiro_queue_20261110.md:59`, `docs/kiro_queue_20261110.md:63`, `docs/kiro_evidence/IDE_SESSION_20261115.md:10`, `docs/playtest/kiro_review.md:3`.

Read: `scripts/release/privacy_gate.py` (P13 and P7), `scripts/release/export_tree.py` (the `unpublish_refs` transform and how it finds references), `scripts/release/export_manifest.json`, `scripts/test_export_tree.py`, `scripts/test_privacy_gate.py`. Open the source lines named above to see WHY the transform did not rewrite them (for example a reference with a line suffix, a path in a table cell, a path written without backticks, a `docs/kiro_queue_20261110.md` rule that runs another transform first). Never repeat a private value in any file you write.

Do, saving after each:
1. Make `unpublish_refs` handle the reference shapes that remain (add each shape with a test on a toy tree); do not edit the source files unless the reference is to a file that really does not exist in the repository (then fix the text at the source and say so). The kept rule: a reference to a path that is NOT in the export becomes `(not published)`.
2. `LICENSE:3` holds the owner's chosen GitHub account name as the copyright holder (an owner decision on 2026-11-15, not a leak). Add a narrow allowlist to `privacy_gate.py`: check P7 ignores the line in `LICENSE` that starts with `Copyright (c)`; document it in `scripts/release/README_gate.md`; add a test that the same term in `(not published)` is still reported.
3. Run `python3 -B scripts/test_export_tree.py` and `python3 -B scripts/test_privacy_gate.py`; paste the last lines. Do NOT run `export_tree.py --apply` and do not touch `(not published)`; the main line re-exports. If a shell call is refused, say so; do not invent output.

Touch only `scripts/release/export_tree.py`, `scripts/release/privacy_gate.py`, `scripts/release/README_gate.md`, `scripts/release/export_manifest.json`, `scripts/test_export_tree.py`, `scripts/test_privacy_gate.py`, and the result file exactly named `docs/kiro_114_result_gpt-5.6-terra.md` (max 20 lines). No network, no git.
