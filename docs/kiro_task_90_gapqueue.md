# Kiro task 90 — bring the gap queue up to date and add the release package

`scripts/daily_log.py` builds `docs/PROGRESS_TABLE.md` from the NEWEST `(not published)`. The newest file is still `(not published)`, so the table misses everything done since. Create `(not published)`; do not edit the 11-10 file.

Read: `(not published)` (format and rows), `.kiro/specs/release-package/tasks.md`, `docs/kiro_verified.json`, `docs/KIRO_LEDGER.md`, `docs/kiro_evidence/2026-11-15_tests.md`, `docs/kiro_85_R*_result_*.md`, `docs/kiro_85b_result_*.md`, `docs/kiro_85c_result_*.md`, `docs/PROGRESS_TABLE.md` (to see which words set which status; `scripts/daily_log.py` STATUS_RULES lines ~44 to 56 define them).

Write `(not published)` in the same format: title with the date 2026-11-15, the same section headings (零 to 六), same table columns, row IDs keep their old letters and numbers so the table's "last change" column stays meaningful. For every old row, re-check the claim against the files (an `ls`, a grep or the test table) and update its status honestly; mark a row done only if a file or command output you saw proves it. New rows get new IDs continuing the series, never reused ones.

Add a new section `## 七、發佈包（Kiro spec release-package）` with these rows (ID prefix R, status words from the existing vocabulary so the parser classifies them):
- R1 T1 export tree (scripts/release, tests): done, main line reran tests 2026-11-15.
- R2 T2 privacy gate: built, tested by the main line; not run on real content; waiting for the owner's terms file.
- R3 T3 history build: not started, needs the working tree committed first (waiting owner approval to commit).
- R4 T4 English drafts in (not published): drafts written, claims review pending; 4 path mismatches (JUDGES.md and CREDITS.md live at the release root later; `tech.md` and `rules.md` need the `.kiro/steering/` prefix).
- R5 T5 clean-checkout script: built; known limits: 404 count ignores MISSING references, and a git clone sees only committed files.
- R6 T6 upload to the owner's new repository: not started, gate preconditions all open.
- R7 owner steps: create `~/pk_privacy_terms.txt`, answer R0 questions 1 to 4, allow the commit of the working tree.
- R8 the 10 real missing assets from `python3 -B scripts/release/check_asset_refs.py` (list them): two backgrounds, `fx_feet_chain.png`, `unit_knight_unarmed.png`, three `.ogg` effects, three `.woff` CSS fallbacks.
- R9 the known failing test `test_i18n.js` (missing `assets/i18n/zh-TW.json`).
- R10 evidence: `docs/kiro_evidence/raw/hook_runs.log` exists; read it and say in one line what it proves and what it does not (do not claim IDE hooks ran unless the file shows it).

Then run `python3 -B scripts/daily_log.py --dry-run --date 2026-11-15` and paste the last 10 lines of its output into the result file (the dry run writes nothing). Do NOT run it with `--apply`.

Write `(not published)` (max 30 lines): the file created, the dry-run lines, rows whose status you changed from the 11-10 file and why, what you did not verify. Touch no other file. No network, no git.
