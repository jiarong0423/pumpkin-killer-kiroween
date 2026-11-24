# Kiro task 85 — release delivery: build the fresh public repository, then upload it (stages R1 to R6)

Owner 2026-11-11: "tell Kiro the earlier design, let him run it, write a delivery document first, then let him upload." This document is that delivery document. The design is already decided and lives in `docs/kiro_84_release_plan_claude-sonnet-5.5.md` (sections 1 to 8). Do not redesign it. Implement it, in order, one stage at a time.

## 0. Read first (in this order)
1. `docs/kiro_84_release_plan_claude-sonnet-5.5.md` (the design: manifest, privacy gate P1-P16, history option (b), root layout, clean checkout, sequence).
2. `(not published)` and `(not published)` (the contest rules).
3. `docs/KIRO_LEDGER.md`, `docs/kiro_verified.json`, `.kiro/steering/*.md`.

## 1. Fixed rules (already decided, never reopen)
- Target is a NEW repository. The old repository and its history are never touched, never rewritten, never published.
- The new repository is public and MIT. `/.kiro` sits at the root and is never in `.gitignore`.
- Commits use the GitHub noreply identity in all four fields (author name/email, committer name/email), and carry no `Co-Authored-By` line written by Claude Code. Kiro's own automatic co-author trailers are accepted (owner decision 2026-11-10). CLI work keeps a `Kiro-Task: NN` trailer.
- Never read, print or copy the value of any secret. Privacy hits are reported as `file:line` only. Nobody opens a flagged line to look at the value; fix by editing or deleting, then re-run the gate.
- Every claim in README, JUDGES.md and commit messages must be true on the day of the push and backed by a file path. Describe only what runs.
- Scripts under `scripts/release/` use only the Python standard library, take no network action, add no git remote, and never push.
- Plain English in everything that is published. Chinese working notes are excluded (gate P10), not translated by guess.
- Dry run first. Nothing is written outside `(not published)` (the export target) and the files named below. Existing files are not edited except where a stage names them.

## 2. Who does what
| Role | Does |
|---|---|
| Kiro (Terra) | R1, R2, R3, R5 scripts and their tests |
| Kiro (Sonnet) | R4 drafts, R3 review of the trailer logic |
| Main line (Claude Code) | runs every script, compares output with the plan, fixes gate hits, commits the working tree, writes the approval record for R6 |
| Owner | answers the four questions (R0), creates the empty repository, approves the upload with one word, sets visibility Public, checks About shows MIT |

Kiro's researcher agent has no shell. When a Kiro report says "not run", that is expected; the main line runs and records raw output in `(not published)`.

## R0. Owner answers (blocks R3 milestone 1-2 trailers, R5 test edits, R4 art disclosure)
Written by the main line from the owner's reply into `(not published)`. Until the file exists, use these defaults and do not edit anything they cover:
1. Were the first-commit steering and spec made in Kiro, and by whom? Default: unknown, milestones 1 and 2 carry no Kiro trailer.
2. Did any shipped picture come from a tool other than Qwen? Default: unknown, such pictures are excluded unless disclosed in `CREDITS.md`.
3. May tests become SKIP when an optional package is missing? Default: no, do not edit tests.
4. Publish `(not published)` extracts? Default: no.

## R1. Export tree (task 85a, Terra)
Deliver in `scripts/release/`:
- `export_manifest.json`: the section 1 table of the plan as data (path, decision INCLUDE/TRANSFORM/EXCLUDE, reason). Every top-level path of the repository must be covered; an uncovered path is an error.
- `check_asset_refs.py`: lists every `assets/` file referenced by `index.html`, `js/*.js`, `css/*.css` and the preload links, and every referenced file that is missing. Exit 1 if any referenced file is missing.
- `export_tree.py --source . --manifest scripts/release/export_manifest.json --out <dir> [--dry-run (default)] [--apply]`: dry run prints per path the decision, file count and size and writes nothing; `--apply` refuses a non-empty `--out`, copies INCLUDE paths, applies the TRANSFORM edits named in the manifest (root `.gitignore`, `steering/kiro_assignment.md` references, the credits sentence in `docs/kiro_queue_20261110.md`, route logs renamed `.txt` into `docs/kiro_evidence/raw/route_logs/`), and writes `docs/kiro_evidence/EXPORT_NOTES.md` listing every change (what and why, no private values).
- Tests `scripts/test_export_tree.py` and `scripts/test_check_asset_refs.py` built on a toy tree created at test time.
Done when: `python3 -B scripts/test_export_tree.py` and `python3 -B scripts/test_check_asset_refs.py` print OK, and the dry run on the real tree covers every top-level path.

## R2. Privacy gate (task 86, Terra)
Deliver `scripts/release/privacy_gate.py --tree <dir> [--check cjk|png-text|links|all] [--history <repo>]` implementing checks P1 to P16 of plan section 2 exactly, including: terms file read from `$PK_TERMS` outside the tree (fail if missing or empty), hits printed as `file:line` or `commit:file` only, BLOCK vs REVIEW classes, exit 1 on any BLOCK.
- Test `scripts/test_privacy_gate.py`: fake private strings are built at test time (for example an email assembled from parts) in a temp tree; no private string is ever stored in the repository.
- Short `scripts/release/README_gate.md`.
Done when: the test prints OK, and a run on a temp tree seeded with one hit per check reports exactly those hits and exits 1; a clean temp tree exits 0.

## R3. History build and trailer validator (task 87, Terra writes, Sonnet reviews)
Deliver:
- `(not published)`: the 22 milestones of plan section 3 (columns `id, end_rev, subject, kiro_tasks, kiro_part, mainline_part, evidence_level`). `end_rev` values are filled from `git log --reverse --format='%h %ad %s' --date=short`; where a real commit does not exist, merge rows as the plan says and keep both trailers. Find the first commit with `git rev-list --max-parents=0 HEAD`, never by a hash quoted in a document.
- `validate_trailers.py`: checks each `Kiro-Task: NN` against the ledger row and `docs/kiro_verified.json`, requires status `ok` or a verified entry, and checks that every file named under "Kiro part" appears in the ledger, in `docs/KIRO_IMPACT_INVENTORY_20261110.md`, or in the real end commit's diff. Milestones 1 to 3 get no trailer unless R0 answer 1 supports one.
- `build_history.py --source . --milestones (not published) --manifest scripts/release/export_manifest.json --out ../pk-release [--dry-run (default)] [--apply]` exactly as plan section 3: snapshots via `git archive <end_rev>`, filtered by the manifest, real author dates, noreply identity set explicitly, no remote, no push, refuses a non-empty `--out`, final tree-hash check of commit 1 against the real first commit.
- Test `(not published)` on a toy repository created at test time.
Done when: the tests print OK and `build_history.py --dry-run` on the real repository prints every milestone with sha, date, file count, size and gate result, exit 0.

## R4. Root documents (task 88, Sonnet)
Draft in English into `(not published)` (not at the repository root): `README.md` (what it is, three-command run, how to play, bring-your-own-agent idea, licence, credits, hosted URL written as the literal text `HOSTED_URL` until release day), `JUDGES.md` (one page mapped to the 8 write-up topics and 5 scoring criteria, each with a file path and a reproducing command), `CREDITS.md` (every third-party asset with its licence, from `docs/ASSET_PROVENANCE.md` and `assets/audio/_licenses`). Rules: prototype is described as it runs today (1 vs 1 in the browser, the MCP server is a separate channel tested by its own scripts), not as the 4v4 plan; every path and command must exist.
Done when: a script-free check shows every backticked path in the three drafts exists in the repository.

## R5. Clean checkout (task 89, Terra) — only after R0 answer 3 exists if tests must change
Deliver `scripts/release/clean_checkout.sh`: clones a given directory into a temp folder, starts the static server on a free port, runs every `node scripts/test_*.js` and `python3 -B scripts/test_*.py`, checks the load gate reports all pictures loaded with no missing file, and exits non-zero on any failure while writing the full log to a file named by `--log`. Without answer 3 it makes no test edits and lists the known failing tests instead.
Done when: `bash -n scripts/release/clean_checkout.sh` passes and a run on the current repository writes a log.

## R6. Upload (Kiro, but only through the gate below)
Kiro agents in this project cannot push (the `committer` agent is local-git only). The upload is done from the Kiro IDE, signed in with the owner's own GitHub account, or by the Kiro Agent GitHub app on the new repository only. No token, password or key is ever written to a file, a log or a message.

Preconditions, all required. The main line writes `(not published)` only when every one is true, and Kiro does not start R6 without that file:
1. `privacy_gate.py --tree ../pk-release --check all` exits 0 and `--history ../pk-release` exits 0 (P15 and P16 included).
2. `clean_checkout.sh` on `(not published)` exits 0, log saved under `(not published)`.
3. Commit 1's tree hash equals the real first commit's tree hash.
4. `README.md` has no `HOSTED_URL` placeholder (gate P14), or the owner explicitly approves a private rehearsal push instead.
5. The owner created an EMPTY repository on GitHub (no README, no licence, no template) and gave its URL in chat. Owner decision 2026-11-11: Kiro performs the upload itself once preconditions 1 to 4 hold, no further one-word approval is needed for the push to that repository. The approval record quotes that decision and the URL. Visibility stays Private until the owner sets it Public (owner only).

Steps once the file exists:
1. In `(not published)`: `git remote add origin <the URL from the approval record>`; `git push -u origin main`. One push, no force, no rewrite afterwards.
2. Read back the remote: the commit count and the head sha equal the local ones.
3. Report to the main line; the owner sets visibility Public and checks that About shows MIT and the page opens logged out.

If any precondition fails, stop at that point and report which one; do not work around it.

## Output and reporting
Each stage ends with one result file `(not published)` (max 80 lines): what was delivered (paths), what was not run, what could not be verified. Do not claim a test passed unless a command output you saw says so. The main line then reruns every command above and records the result in `docs/kiro_verified.json`.
