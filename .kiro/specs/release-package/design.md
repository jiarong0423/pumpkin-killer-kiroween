# Design: Release package

Written 2026-11-11 (latest dated record in the repository; the clock was not
read). Requirements: `requirements.md` in this folder. Inputs:
`docs/kiro_task_85_release_delivery.md` (stages R1 to R6),
`docs/kiro_84_release_plan_claude-sonnet-5.5.md` (sections 1 to 8, an earlier
plan whose numbers are UNVERIFIED), `scripts/release/export_manifest.json`.

## 1. Data flow

```
pumpkin-killer (source, never written)
   |  check_asset_refs.py         which assets/ files the page names
   |  export_tree.py              manifest rules -> copy / transform / skip
   v
../pk-release (release tree, new git repo, no remote until T6)
   |  privacy_gate.py --tree      P1-P14 on files
   |  build_history.py            git archive <end_rev> per milestone, filtered
   |  privacy_gate.py --history   P15-P16 and P1-P4, P6, P7 on every commit
   |  tree-hash check             new commit 1 == real first commit
   |  clean_checkout.sh           clone to temp, serve, run all tests
   v
docs/kiro_evidence/UPLOAD_APPROVAL.md   (written by the main line only)
   |  git remote add origin <URL from the approval record>
   |  git push -u origin main            (one push, no force)
   v
new GitHub repository (Private until the owner sets Public)
```

The source repository is read only. The release tree is the only place the
scripts write, apart from result and evidence files named in `tasks.md`.

Note on `build_history.py` and `export_tree.py`: they are two ways to make the
release tree and are not run one after the other on the same `--out`. The
history builder reuses the manifest filter from `export_tree.py` for each
snapshot. `export_tree.py --apply` alone gives a plain tree with no history, which a
single commit can then wrap (plan option (a), the fallback). `build_history.py --apply` gives plan option (b),
the recommended path. Both refuse a non-empty `--out`.

## 2. Components

| Component | File | Inputs | Output | Stage |
|---|---|---|---|---|
| Export manifest | `scripts/release/export_manifest.json` | none | ordered rules, first match wins; last rule is a catch-all EXCLUDE; `new_files` lists README, JUDGES, CREDITS | R1 |
| Asset-reference check | `scripts/release/check_asset_refs.py` | `--root` source or release tree | lines `REF`, `MISSING`, `CASE`; exit 1 if any file is missing or has the wrong case | R1 |
| Export tree | `scripts/release/export_tree.py` | `--source`, `--manifest`, `--out`, `--dry-run` (default) or `--apply` | per-path decision, count, size; with `--apply` the copied tree, four named transforms, `docs/kiro_evidence/EXPORT_NOTES.md` | R1 |
| Privacy gate | `scripts/release/privacy_gate.py`, `README_gate.md` | `--tree`, `--check cjk\|png-text\|links\|all`, `--history`, `$PK_TERMS` | `file:line` or `commit:file` hits with class BLOCK or REVIEW; exit 1 on any BLOCK | R2 |
| Trailer validator | `(not published)` | `milestones.tsv`, ledger, verified.json, inventory, git | pass or refuse per milestone | R3 |
| History builder | `(not published)`, `milestones.tsv` | `--source`, `--milestones`, `--manifest`, `--out` | commits in `(not published)`; dry run prints sha, date, count, size, gate result per milestone | R3 |
| Root documents | `(not published)`, `JUDGES.md`, `CREDITS.md` | ledger, provenance, audio licences | drafts; the main line copies reviewed text to the release root | R4 |
| Clean-checkout script | `scripts/release/clean_checkout.sh` | directory to clone, `--log` | temp clone, static server, all tests, 404 count, log file | R5 |
| Upload step | none (Kiro IDE signed in as the owner, or the Kiro Agent GitHub app) | `UPLOAD_APPROVAL.md` | one push, read-back | R6 |

### Export manifest (decided, exists)
Ordered rules; the first match wins. `only_if: referenced` keeps an `assets/`
file only when the page, `js/*.js` or `css/*.css` names it. Four transforms are
named: `gitignore`, `steering_refs`, `route_log_txt`, `drop_credit_sentence`.
`README.md` is EXCLUDEd from the copy because the old text overclaims; the
reviewed draft is placed by the main line (T4).

### Privacy gate
Checks P1 to P16 are specified in plan section 2 and are not repeated here.
Design points that matter for correctness:
- The terms file is `$PK_TERMS`, outside the tree. A missing or empty file is a
  failure, so the gate cannot pass by accident.
- Output contains positions only. A test captures stdout and asserts that no
  seeded value appears in it.
- P5, P8, P9, P10 are REVIEW. A REVIEW decision is stored as
  `path|sha1-of-line` in an allowlist, so an edited line needs approval again.
- History scan walks commits and prints `commit:file` only.

### History builder
Per milestone: `git archive <end_rev>` into a temp directory, filter by the
manifest, `git add -A`, `git commit` with these set explicitly: the four
identity fields (noreply), `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` from the
real author date, `--no-gpg-sign`, `-c core.hooksPath=/dev/null`. No remote.
After the last commit, compare `git rev-parse <real1>^{tree}` with
`git rev-parse <new1>^{tree}`. `real1` comes from
`git rev-list --max-parents=0 HEAD`.

Message shape:
```
<subject>

Kiro part: <what, with file names>.
Main line (Claude Code) part: <what, with file names>.
Kiro-Task: NN (brief docs/kiro_task_NN.md; evidence level V|C|L)
```
No `Co-Authored-By`. A milestone with no Kiro work says "Main line (Claude Code)
only." Only evidence level V or C may say "Kiro wrote". Level L says "brief
written; output not verified".

### Root documents
English only. They describe the prototype as it runs: 1 vs 1 in the browser;
the MCP server (`scripts/mcp_stdio_server.py`) is a separate channel with its
own tests; the 4 vs 4 and bring-your-own-agent ideas are labelled as design.
`HOSTED_URL` stays literal until release day, and gate P14 blocks a push while
it is present. `(not published)` is not published.

## 3. Gate order

Cheap and local gates first; the expensive or irreversible ones last.

| # | Gate | Command | Stops when |
|---|---|---|---|
| G0 | Owner answers R0 | file `(not published)` exists | missing: defaults apply, covered files are not edited |
| G1 | Tests of the tooling | `python3 -B scripts/test_check_asset_refs.py`, `test_export_tree.py`, then the tests of later stages | any non-OK |
| G2 | Manifest covers source | `python3 -B scripts/release/export_tree.py --source . --manifest scripts/release/export_manifest.json` | an uncovered top-level path or a bad manifest |
| G3 | Asset references | `python3 -B scripts/release/check_asset_refs.py` (source) | exit 1: referenced file missing or wrong case |
| G4 | Privacy, tree | `python3 -B scripts/release/privacy_gate.py --tree ../pk-release --check all` | any BLOCK |
| G5 | History dry run | `build_history.py --dry-run` | a milestone with a gate hit, a bad trailer, or a non-increasing date |
| G6 | History apply | `build_history.py --apply` | non-empty `--out`, or the commit-1 tree hash differs |
| G7 | Privacy, history | `privacy_gate.py --tree ../pk-release --history ../pk-release` | identity not unique, a `Co-Authored-By` line, a term hit, a leaked path |
| G8 | Clean checkout | `bash scripts/release/clean_checkout.sh ../pk-release --log <file>` | a failing test or a 404 |
| G9 | Approval | `UPLOAD_APPROVAL.md` written by the main line | any of the five preconditions false |
| G10 | Upload | one push, then read-back | push error, or counts or head sha differ |

## 4. Failure handling

| Failure | Response |
|---|---|
| BLOCK hit | Fix by editing or deleting at `file:line`. Re-run the gate. Never open the line to read the value. A real secret is rotated by the owner. |
| REVIEW hit | A person decides and records `path|sha1`. Nothing is waved through by the script. |
| Uncovered path in the manifest | Add a rule above the catch-all with a reason. Do not widen the catch-all. |
| Missing referenced asset | Restore the file in the source or remove the reference. Do not delete the check. |
| Commit-1 tree hash differs | Stop. Print the differing files. If a gate fix caused it, write the exception into `EXPORT_NOTES.md`. Never hide it. |
| Milestone `end_rev` missing | Merge the rows as the plan says and keep both trailers. |
| Trailer refused | Fix the message or drop the trailer. Do not edit the ledger to fit. |
| Test needs an optional package | Without R0 answer 3 the test is not edited; the clean-checkout log lists it as a known failure. |
| Push rejected or counts differ | Stop. No force push, no second push, no rewrite. Report to the main line. |
| Any `--apply` on a non-empty `--out` | Refused. The operator picks a new empty directory. |
| Shell or git unavailable to Kiro | The result says "not run". The main line runs the command and records raw output in `(not published)`. |

## 5. What is verified by which command

| Claim | Command | Run by |
|---|---|---|
| asset-reference check works on a toy tree | `python3 -B scripts/test_check_asset_refs.py` | main line |
| export tree dry run and `--apply` guard work | `python3 -B scripts/test_export_tree.py` | main line |
| manifest covers the real source | `python3 -B scripts/release/export_tree.py --source . --manifest scripts/release/export_manifest.json` | main line |
| every referenced asset exists | `python3 -B scripts/release/check_asset_refs.py` | main line |
| privacy gate finds seeded hits and passes a clean tree | `python3 -B scripts/test_privacy_gate.py` | main line |
| trailers and history builder work on a toy repo | `python3 -B (not published)` | main line |
| real milestones pass | `python3 -B (not published) --source . --milestones (not published) --manifest scripts/release/export_manifest.json --out ../pk-release` | main line |
| drafts cite real paths | script-free check: each backticked path in `(not published)` exists | main line |
| shell script is valid | `bash -n scripts/release/clean_checkout.sh` | main line |
| release tree runs from a clone | `bash scripts/release/clean_checkout.sh ../pk-release --log <file>` | main line |
| remote matches local | `git ls-remote origin` head sha and `git rev-list --count main` equal the local values | upload step, then main line |
| About shows MIT, page opens logged out | browser | owner |

A Kiro result file is never counted as verification. The main line records its
own runs in `docs/kiro_verified.json` and regenerates the ledger with
`python3 -B scripts/make_kiro_ledger.py --apply`.

## 6. Decisions and open items

- History option (b), curated milestones with real dates, is the path. The
  fallback is option (a), one tree, with a dated history table in JUDGES.md.
  Full history (c) is not used.
- The upload is done from the Kiro IDE signed in as the owner, or by the Kiro
  Agent GitHub app on the new repository only, because no Kiro agent here can
  push (`committer` is local-git only). Not verified in this run.
- The target URL is recorded only in `UPLOAD_APPROVAL.md`, written by the main
  line when the owner has created an empty repository.
- Open: the real first commit and the milestone `end_rev` values are not
  checked here (no shell). The 22-milestone list in plan section 3 is a draft.
- Open: the four optional-package tests and `test_i18n.js` stay as they are
  until R0 answer 3 exists.
