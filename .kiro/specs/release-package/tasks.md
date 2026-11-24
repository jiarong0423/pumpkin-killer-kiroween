# Tasks: Release package

Written 2026-11-11 (latest dated record in the repository; the clock was not
read). Spec: `requirements.md` and `design.md` in this folder.

Tick rule: a box is ticked only when a command output or a file listing seen in
the run that ticks it proves the item. A Kiro report is not proof. Boxes for
commands stay empty until the main line has run the command and seen its output.
Do not start a task out of order. Do not push, add a remote or touch GitHub
before T6 preconditions are met.

R0 (owner answers, `(not published)`) is written by the main
line, not by Kiro. Not checked in this run. Until it exists, the defaults in
`docs/kiro_task_85_release_delivery.md` section R0 apply.

## T1. Export tree (stage R1, task 85a) — IN PROGRESS

Requirements: 1.1, 2.1, 2.2, 7.1, 7.2, 7.3, 9.1, 9.3.

Files:
- `scripts/release/export_manifest.json`
- `scripts/release/check_asset_refs.py`
- `scripts/release/export_tree.py`
- `scripts/test_check_asset_refs.py`
- `scripts/test_export_tree.py`
- `docs/kiro_85_R1_result_gpt-5.6-terra.md` (the 85a report)

Checklist:
- [x] `scripts/release/export_manifest.json` exists (seen in a directory listing).
- [x] `scripts/release/check_asset_refs.py` exists (seen; it has a `--root` option).
- [x] `scripts/release/export_tree.py` exists (seen; it has `--source`, `--manifest`, `--out`, `--dry-run`, `--apply`).
- [x] `scripts/test_check_asset_refs.py` exists (file search).
- [x] `scripts/test_export_tree.py` exists (file search).
- [x] Manifest ends with a catch-all EXCLUDE rule (seen in the file: last rule is `"match": "*"`).
- [ ] `python3 -B scripts/test_check_asset_refs.py` prints OK. The 85a report says it did; not seen in this run.
- [ ] `python3 -B scripts/test_export_tree.py` prints OK. Same.
- [ ] Dry run on the real tree covers every top-level path: `python3 -B scripts/release/export_tree.py --source . --manifest scripts/release/export_manifest.json`. The 85a report quotes `selected=548`; not seen in this run.
- [ ] `python3 -B scripts/release/check_asset_refs.py` exits 0 on the source.
- [ ] Main line records the result of the four commands above in `docs/kiro_verified.json`.

Not in the file set yet, so not ticked: no `--apply` run, no `(not published)`
(none was looked for in this run).

## T2. Privacy gate (stage R2, task 86)

Requirements: 3.2, 3.3, 4.1, 4.2, 4.3, 4.4, 4.5, 8.1, 8.2, 6.4.

Files:
- `scripts/release/privacy_gate.py`
- `scripts/release/README_gate.md`
- `scripts/test_privacy_gate.py`
- `(not published)`

Checklist:
- [ ] `privacy_gate.py --tree <dir> [--check cjk|png-text|links|all] [--history <repo>]` implements P1 to P16.
- [x] Terms read from `$PK_TERMS`; missing or empty file fails.
- [x] Output has `file:line` or `commit:file` only; a test asserts no seeded value is printed.
- [x] `python3 -B scripts/test_privacy_gate.py` prints OK; fake private strings are built at test time.
- [x] A temp tree with one seeded hit per check reports exactly those hits and exits 1; a clean temp tree exits 0.
- [ ] Main line runs the gate on `(not published)` and records the exit code.

## T3. History build (stage R3, task 87)

Requirements: 2.2, 2.3, 4.3, 5.1 to 5.8, 9.2.

Files:
- `(not published)`
- `(not published)`
- `(not published)`
- `(not published)`
- `(not published)`

Checklist:
- [ ] `milestones.tsv` has the milestones of plan section 3, with `end_rev` filled from `git log --reverse --format='%h %ad %s' --date=short` (main line runs git).
- [ ] `validate_trailers.py` refuses a task that is not `ok` or verified, and a "Kiro part" file with no support.
- [ ] `build_history.py` refuses a non-empty `--out`, adds no remote, never pushes.
- [ ] `python3 -B (not published)` prints OK on a toy repository.
- [ ] `build_history.py --dry-run` on the real repository lists every milestone with sha, date, file count, size and gate result, exit 0.
- [ ] `--apply` into an empty `(not published)`; commit-1 tree hash equals the real first commit's tree hash.
- [ ] `git log --all --format='%an|%ae|%cn|%ce' | sort -u` shows exactly one line.

## T4. Root documents (stage R4, task 88)

Requirements: 6.1 to 6.5, 8.1, 3.1.

Files:
- `(not published)`
- `(not published)`
- `(not published)`
- `(not published)`

Checklist:
- [x] Drafts are in English and describe the 1 vs 1 prototype as it runs.
- [x] JUDGES.md maps the 8 write-up topics and 5 criteria, each with a path and a command.
- [x] CREDITS.md lists every third-party asset with its licence, from `docs/ASSET_PROVENANCE.md` and `assets/audio/_licenses`.
- [ ] Every backticked path in the three drafts exists (script-free check).
- [x] README keeps the literal `HOSTED_URL` until release day.
- [ ] Main line reviews the claims and copies the text to the release root.

## T5. Clean checkout (stage R5, task 89)

Requirements: 1.1, 1.2, 1.3, 1.4, 7.1, 7.2.

Files:
- `scripts/release/clean_checkout.sh`
- `(not published)`
- log: `(not published)` (written by the main line)

Checklist:
- [ ] `bash -n scripts/release/clean_checkout.sh` passes.
- [ ] A run on the current repository writes the file named by `--log`.
- [ ] The log reports all pictures loaded and no 404.
- [ ] Known failing tests are listed, not edited, unless R0 answer 3 exists.
- [ ] A run on `(not published)` exits 0; log saved under `(not published)`.
- [ ] A run on Linux (Docker, Codespace or Actions) repeats the 404 count. Which of these exists is not known.

## T6. Upload (stage R6)

Requirements: 2.3, 3.4, 10.1 to 10.5.

Files:
- `(not published)` (written by the main line only)
- `(not published)`

Checklist:
- [ ] `privacy_gate.py --tree ../pk-release --check all` exits 0.
- [ ] `privacy_gate.py --tree ../pk-release --history ../pk-release` exits 0 (P15, P16).
- [ ] T5 clean checkout on `(not published)` exits 0 and its log is saved.
- [ ] Commit-1 tree hash equals the real first commit's tree hash.
- [ ] `README.md` has no `HOSTED_URL`, or the owner approved a private rehearsal push.
- [ ] The owner created an EMPTY repository and gave its URL in chat.
- [ ] `UPLOAD_APPROVAL.md` exists and quotes the owner decision and the URL.
- [ ] `git remote add origin <URL>` then `git push -u origin main` (one push, no force).
- [ ] Remote commit count and head sha equal the local ones.
- [ ] Owner sets visibility Public, checks that About shows MIT, and opens the page logged out. Owner step.

If a precondition fails, stop at it and report which one. Do not work around it.
