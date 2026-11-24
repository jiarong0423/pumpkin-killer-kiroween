---
inclusion: always
---
# Team plan: who does what, when, and which rules every task obeys

Kiro sessions from the CLI, the IDE and Kiro Web all load this file. Check the five files in section 5 before you trust it, because they change faster than this summary.

## 1. Three parties
- Owner: decisions and the steps only a person can do. These are GitHub visibility (Private to Public), the Devpost form, the video upload, the Kiro credit codes, own social and blog posts, and the Colab art runs.
- Main line (Claude Code): dispatches work, reruns every test itself, records results in `docs/kiro_verified.json`, writes the upload approval, and never trusts a Kiro self-report.
- Kiro: writes specs, scripts, tests and drafts. It reports honestly what it did not run.

## 2. Deadline and freeze points (Taiwan time, from `(not published)`)
- Submission closes 2026-12-05 06:00 (2026-12-04 14:00 PT).
- Scope freeze 12-02 06:00. One strong review 12-03 06:00. Fixes done 12-04 06:00.
- Video cut from 12-04 06:00. Upload and Devpost draft 12-04 18:00. Documents aligned 12-05 00:00. Read-only final check 12-05 04:00.

## 3. Work blocks (status words from `docs/WORK_QUEUE_20261115.md`)
- B01 IDE evidence: needs the project folder opened as the IDE workspace; first try failed.
- B02 Web and Crew evidence: needs the new repository and the GitHub app; else the write-up says "not used".
- B03 Public URL: deploy files exist; owner runs ingress; smoke test after.
- B04 Ultimates (spec `ultimates-v2`, then one task per hero): dispatch now; art by owner.
- B05 AI difficulty, three levels and a sweep: dispatch now.
- B06 Opening flow (start screen, coin toss, seats): waits for owner concept images.
- B07 Missing pictures: owner on Colab, or drop the reference.
- B08 Missing sounds: waits for owner to pick a source.
- B09 English interface: waits for B06; one `index.html` task.
- B10 Export and privacy gate: waits for owner terms file and answers.
- B11 History and private push, then Public: waits for B10.
- B12 Write-up `JUDGES.md`, eight topics: waits for B01 and B10.
- B13 README v2 and Devpost text: waits for B03 for the URL.
- B14 Disclosure list: dispatch now.
- B15 Known test gaps: waits for B09.
- B16 Video under 3 minutes: owner records; waits for B03 and the freeze.
- B17 Blog and Social Blitz posts: owner writes them; waits for B13.
- B18 Credits and final form: owner only.
- B19 4 vs 4: frozen; reopen only if every block above is done.

## 4. Rules every task obeys
- One `index.html` task at a time; at most 3 Kiro runs at once.
- Use real dates. Tick nothing without a command output the main line has seen.
- No push and no GitHub action, unless the task is stage R6 and `(not published)` exists.
- Never print a private value (keys, tokens, personal data, local paths).
- Pictures come only from the owner on Colab/Qwen. Never draw art with code.
- Everything published is in English. Do not add `/.kiro` to `.gitignore`.

## 5. Where the truth lives
`(not published)`, `docs/WORK_QUEUE_20261115.md`, `docs/PLAN_20261115.md`, `(not published)`, `(not published)`, and `docs/kiro_verified.json` for what the main line has verified.
