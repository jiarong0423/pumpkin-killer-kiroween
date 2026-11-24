# Requirements: Release package

Written 2026-11-11, the date of the latest record in the repository
(`docs/KIRO_LEDGER.md`, generated 2026-11-11 19:04). The system clock could
not be read when this was written, so no later date is claimed.

## Introduction

Pumpkin Killer is published as a NEW public GitHub repository, built from the
working repository by scripts in `scripts/release/`. The working repository
stays untouched. The fixed rules come from `docs/kiro_task_85_release_delivery.md`
section 1; the contest rules come from `(not published)`
(public repository with a visible licence, `/.kiro` at the root and not ignored,
everything in English, built after Oct 30 2026).

Terms used below:

- **Source**: this working repository (`pumpkin-killer`).
- **Release tree**: the new repository, built in `(not published)`.
- **Gate**: a script check whose non-zero exit stops the release.
- **BLOCK / REVIEW**: privacy-gate result classes. BLOCK must be zero. A person
  decides each REVIEW hit by `file:line` and records the decision.

## Requirements

### 1. A judge can run the project from a clean clone

**User story:** As a judge, I want to clone the repository and run the game and
the tests with no extra setup, so that I can check what the write-up claims.

1. WHEN the page `index.html` is served from a fresh clone of the release tree,
   THEN THE SYSTEM SHALL find every file under `assets/` that `index.html`,
   `js/*.js` or `css/*.css` names, with the same letter case as on disk.
2. WHEN `scripts/release/clean_checkout.sh` runs on a fresh clone, THEN THE
   SYSTEM SHALL serve the page on a free local port, run every
   `node scripts/test_*.js` and `python3 -B scripts/test_*.py`, and exit non-zero
   if any of them fails or if the server log shows a 404.
3. IF a test needs an optional package that a bare Python lacks AND the owner has
   not approved turning that test into a SKIP (R0 answer 3), THEN THE SYSTEM
   SHALL leave the test unchanged and list it as a known failure in the log.
4. THE SYSTEM SHALL write the full clean-checkout log to the file named by
   `--log`, and SHALL NOT report a test as passed unless its output says so.

### 2. The old repository is never touched

**User story:** As the owner, I want the release built in a separate place, so
that the working history and its private notes are never rewritten or published.

1. THE SYSTEM SHALL write only to the release tree (`(not published)`), to
   `.kiro/specs/release-package/`, to the result files named by the delivery
   document, and to the evidence paths named in `design.md`.
2. WHEN `--apply` is given an `--out` directory that is not empty, THEN THE
   SYSTEM SHALL refuse and write nothing.
3. THE SYSTEM SHALL NOT run `git push`, `git remote add`, `git filter-repo`, or
   any history rewrite against the source repository.

### 3. The repository is public-ready: MIT, `.kiro` visible

**User story:** As a contest reviewer, I want the licence and the Kiro
directory visible at the root, so that the entry meets the rules.

1. THE SYSTEM SHALL include `LICENSE` (MIT) and `.kiro/` at the root of the
   release tree.
2. WHEN the release tree is checked, THEN THE SYSTEM SHALL fail if
   `git check-ignore -q .kiro` succeeds, or if `.gitignore` contains any line
   that names `.kiro`, or if `git ls-files .kiro` lists fewer than 73 files
   (gate P16).
3. THE SYSTEM SHALL fail if `(not published)` is present in the release tree
   (gate P16).
4. WHEN the repository is created on GitHub, THEN the owner SHALL set
   visibility to Public and confirm that About shows MIT. These are owner steps
   and no script performs them.

### 4. No private data is read, printed or published

**User story:** As the owner, I want a release that contains no secret, email,
local path or private name, so that nothing sensitive becomes public.

1. WHEN the privacy gate finds a hit, THEN THE SYSTEM SHALL print only
   `file:line` (tree) or `commit:file` (history), and SHALL NOT print the
   matched text.
2. WHEN the file named by `$PK_TERMS` is missing, empty, or inside the release
   tree, THEN THE SYSTEM SHALL fail the gate instead of passing it.
3. THE SYSTEM SHALL run checks P1 to P16 of
   `docs/kiro_84_release_plan_claude-sonnet-5.5.md` section 2 on the release
   tree and, for P1 to P4, P6, P7 and P15, on every commit of the built history.
4. IF a BLOCK hit exists, THEN THE SYSTEM SHALL exit 1, and a person SHALL fix
   the hit by editing or deleting the file and re-running the gate. Nobody
   opens a flagged line to read the value.
5. THE test suite SHALL build any fake private string at test time and SHALL
   NOT store one in the repository.

### 5. History shows real dates and true Kiro attribution

**User story:** As a judge, I want a readable history with the real dates and
only the Kiro credit that was earned, so that I can trust the timeline.

1. THE SYSTEM SHALL build the history as the milestones in
   `(not published)`, each one a snapshot of the source at its
   `end_rev`, filtered by the export manifest, in `git rev-list --first-parent
   --reverse` order.
2. THE SYSTEM SHALL set author date and committer date of each commit to the
   real author date of its `end_rev`. IF an `end_rev` is not later than the
   previous one, THEN THE SYSTEM SHALL stop with an error.
3. THE SYSTEM SHALL set author name, author email, committer name and committer
   email on every commit to the GitHub noreply identity, explicitly, with no
   signing and no hooks.
4. THE SYSTEM SHALL NOT write a `Co-Authored-By` line written by Claude Code.
   Kiro's own automatic co-author trailers are accepted (owner decision
   2026-11-10). CLI work keeps a `Kiro-Task: NN` trailer.
5. WHEN a milestone message carries `Kiro-Task: NN`, THEN THE SYSTEM SHALL
   check that NN is a row of `docs/KIRO_LEDGER.md` with status `ok` or an entry
   in `docs/kiro_verified.json`, and that each file named under "Kiro part" is
   in the ledger, in `docs/KIRO_IMPACT_INVENTORY_20261110.md`, or in the diff of
   the real end commit. Otherwise it SHALL refuse the milestone.
6. WHILE R0 answer 1 does not exist, THE SYSTEM SHALL give milestones 1 to 3 no
   Kiro trailer.
7. WHEN the history is built, THEN THE SYSTEM SHALL compare the tree hash of
   new commit 1 with the tree hash of the real first commit (found with
   `git rev-list --max-parents=0 HEAD`, never a hash quoted in a document) and
   stop if they differ.
8. THE SYSTEM SHALL NOT move any date earlier than its real value.

### 6. Every published claim is true and backed by a path

**User story:** As a judge, I want README, JUDGES.md and commit messages to
describe what actually runs, so that nothing is oversold.

1. THE SYSTEM SHALL describe the prototype as it runs on the day of the push:
   1 vs 1 in the browser; the MCP server is a separate channel, tested by its
   own scripts; the browser game does not call it.
2. WHEN a draft names a path or a command in backticks, THEN THE SYSTEM SHALL
   find that path in the release tree.
3. THE SYSTEM SHALL NOT state that a test passed unless the main line has seen
   the command output and recorded it in `docs/kiro_verified.json`.
4. WHEN the placeholder `HOSTED_URL` remains in README.md, JUDGES.md or
   CREDITS.md, THEN gate P14 SHALL fail, unless the owner approves a private
   rehearsal push in writing.
5. THE SYSTEM SHALL list every third-party asset and its licence in
   `CREDITS.md`, and SHALL exclude a picture that came from a tool other than
   Qwen unless `CREDITS.md` discloses it (R0 answer 2).

### 7. Release scripts are small, offline and cannot publish

**User story:** As the owner, I want the release tooling to be unable to leak
or push by accident.

1. THE scripts under `scripts/release/` SHALL use only the Python standard
   library (clean_checkout.sh uses only standard shell tools, `git`, `python3`,
   `node` and `curl`).
2. THE scripts SHALL make no network request, SHALL NOT add a git remote and
   SHALL NOT push.
3. THE scripts SHALL default to dry run and SHALL write only with `--apply`.

### 8. Everything published is in plain English

**User story:** As an English-speaking judge, I want every published file in
English, as the contest rules ask.

1. WHEN a file outside `index.html`, `js/`, `css/` and
   `assets/fonts/charset.txt` contains Chinese characters, THEN gate P10 SHALL
   report it as REVIEW, and the file SHALL be translated by a person or excluded.
2. THE SYSTEM SHALL NOT machine-translate a working note to make it pass.

### 9. A dry run comes before every write

**User story:** As the owner, I want to see what a script will do before it does it.

1. WHEN `export_tree.py` runs without `--apply`, THEN THE SYSTEM SHALL print, per
   top-level path, the decision, the file count and the size, and write nothing.
2. WHEN `build_history.py` runs without `--apply`, THEN THE SYSTEM SHALL print
   for every milestone the sha, date, file count, size and gate result, and
   write nothing.
3. THE export manifest SHALL cover every top-level path of the source. A path
   that no rule matches SHALL be an error (the last rule is a catch-all EXCLUDE).

### 10. The upload happens only after the gates pass

**User story:** As the owner, I want nothing pushed until every check has
passed, so that a public repository never holds a leak.

1. THE SYSTEM SHALL NOT start the upload until `(not published)`
   exists. THE main line SHALL write that file only when all of these hold:
   1. `privacy_gate.py --tree ../pk-release --check all` exits 0 and
      `privacy_gate.py --tree ../pk-release --history ../pk-release` exits 0;
   2. `clean_checkout.sh` on `(not published)` exits 0, and its log is saved under
      `(not published)`;
   3. the tree hash of new commit 1 equals the tree hash of the real first commit;
   4. README.md has no `HOSTED_URL` placeholder, or the owner approved a private
      rehearsal push;
   5. the owner created an EMPTY repository (no README, licence or template) and
      gave its URL in chat.
2. IF any of the five conditions fails, THEN THE SYSTEM SHALL stop at that
   condition and report which one failed. It SHALL NOT work around it.
3. WHEN the approval file exists, THEN the upload SHALL be one `git push -u
   origin main` with no force and no later rewrite, followed by a read-back of
   the remote commit count and head sha against the local ones.
4. THE upload SHALL use the owner's signed-in GitHub session in the Kiro IDE, or
   the Kiro Agent GitHub app on the new repository only. No token, password or
   key SHALL be written to a file, a log or a message.
5. THE repository SHALL stay Private until the owner sets it Public.
