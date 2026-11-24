# Kiro task 86 — stage R2 / spec task T2: privacy gate

You wrote the spec `.kiro/specs/release-package/` (requirements, design, tasks). Execute task T2 from its `tasks.md`. Read first: `.kiro/specs/release-package/tasks.md` (T2), `.kiro/specs/release-package/design.md` (privacy gate component), `docs/kiro_task_85_release_delivery.md` stage R2, and `docs/kiro_84_release_plan_claude-sonnet-5.5.md` section 2 (checks P1 to P16, exact patterns and classes). Do not deliberate at length: save each file as soon as it is written.

Write, in this order:
1. `scripts/release/privacy_gate.py --tree <dir> [--check cjk|png-text|links|all] [--history <repo>]` implementing P1 to P16 exactly as the plan's table (BLOCK vs REVIEW classes). Rules: stdlib only (the PNG-text check parses PNG chunks itself; no Pillow); terms file read from the environment variable `PK_TERMS`, and the gate FAILS when it is missing or empty; every hit is printed as `file:line` or `commit:file` and never the matched text, in the output and in exceptions and logs; exit 1 on any BLOCK, 0 otherwise; `.git` is skipped when scanning a tree; `--history <repo>` runs the history checks (P15, P16 and the P1 to P4, P6, P7 patterns over every commit, printing `commit:file` only).
2. `scripts/test_privacy_gate.py` — `unittest`, temp trees and a temp git repository built at test time; fake private strings are assembled from parts inside the test and never stored in a file of this repository. Cases: one seeded hit per check is reported and exit is 1; a clean tree exits 0; a missing or empty terms file fails; the matched text never appears in the output (assert the seeded value is absent from stdout and stderr).
3. `scripts/release/README_gate.md` — short: how to run, exit codes, what each class means.

Run `python3 -B scripts/test_privacy_gate.py` and `python3 -B scripts/release/privacy_gate.py --tree . --check links` (the second is read-only; its exit code is information, not a failure of yours). Do NOT run the gate with real private terms and do not create `~/pk_privacy_terms.txt`: the owner creates it.

Write `(not published)` (max 40 lines): files created, the commands run with the last output line of each, what you did not run. Update only the T2 boxes of `.kiro/specs/release-package/tasks.md` that a command output you saw proves. Touch no other file. No network, no git, no GitHub.
